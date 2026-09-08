"""Payroll: what a school pays, worked out from rows rather than from code.

**Zero hardcoded rates** (§3.16). The code knows the methods — a percentage of
basic, a balancing figure, loss of pay — and never the numbers. Basic at 50% of
gross and PF at 12% are seed data a school edits on a screen, and a school that
pays differently changes rows rather than asking for a deployment.

**Payroll is a separate ledger from fees** (§5.3.6). Nothing here touches
`fee_invoices` or `fee_periods`. The run's own status is the month lock:
reusing the fee period would mean closing June for fees also closed June for
payroll, and those are decisions different people make for different reasons.

**An approved run is immutable** (§5.3.9). A correction is a supplementary run
for the same month, standing on its own, never an edit to a payslip somebody
has already been handed.

**Loss of pay is asked, not computed here.** `staff_attendance.lop_days()` is
the single definition, merging the register and unpaid leave, counting a day
that is both only once, and charging nothing for a Sunday or a half day. A
second definition would put two figures on two screens.
"""

from calendar import monthrange
from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    CalculationMethod,
    ComponentType,
    Employee,
    EmployeeStatus,
    PayrollRun,
    PayrollRunStatus,
    Payslip,
    PayslipLine,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureItem,
    User,
)
from app.services import attendance as att
from app.services import audit
from app.services import staff_attendance
from app.services.fee_setup import money

ZERO = Decimal("0.00")

# §3.16's default set for a Lucknow private CBSE school. Every one of these is
# editable and disableable; this is what the setup screen is pre-filled with,
# not what the code assumes anywhere.
# (code, name, type, calculation, value, sequence, active, statutory, taxable,
#  applies_below_gross)
DEFAULT_COMPONENTS = [
    ("BASIC", "Basic", ComponentType.earning, CalculationMethod.percent_of_gross,
     Decimal(50), 10, True, False, True, None),
    ("HRA", "House Rent Allowance", ComponentType.earning,
     CalculationMethod.percent_of_basic, Decimal(40), 20, True, False, True, None),
    ("CONV", "Conveyance", ComponentType.earning, CalculationMethod.fixed,
     Decimal(1600), 30, True, False, True, None),
    # Disabled: most private schools do not pay dearness allowance.
    ("DA", "Dearness Allowance", ComponentType.earning,
     CalculationMethod.percent_of_basic, Decimal(0), 40, False, False, True, None),
    # The balancing figure — whatever is left of gross once the rest are taken.
    ("SPL", "Special Allowance", ComponentType.earning, CalculationMethod.balance,
     Decimal(0), 90, True, False, True, None),

    ("PF", "Provident Fund", ComponentType.deduction,
     CalculationMethod.percent_of_basic, Decimal(12), 110, True, True, False, None),
    # Applies only while gross is at or below the statutory threshold.
    ("ESI", "Employee State Insurance", ComponentType.deduction,
     CalculationMethod.percent_of_gross, Decimal("0.75"), 120, True, True, False,
     Decimal(21000)),
    # Uttar Pradesh does not levy professional tax (§0.B, confirmed by the owner
    # on 7 September 2026). Shipped so a school in a state that does can switch
    # it on, and off so nobody is charged one by default.
    ("PT", "Professional Tax", ComponentType.deduction, CalculationMethod.fixed,
     Decimal(0), 130, False, True, False, None),
    # Fixed, not slab. Slab-based TDS needs an annual projection this system
    # does not hold, and inventing one would put a wrong number on a payslip.
    # Off by default; the accountant enters a monthly figure per employee as a
    # structure override.
    ("TDS", "Income Tax Deducted at Source", ComponentType.deduction,
     CalculationMethod.fixed, Decimal(0), 140, False, True, False, None),
    ("LOP", "Loss of Pay", ComponentType.deduction, CalculationMethod.loss_of_pay,
     Decimal(0), 150, True, False, False, None),

    ("PF_ER", "Provident Fund (employer)", ComponentType.employer_contribution,
     CalculationMethod.percent_of_basic, Decimal(12), 210, True, True, False, None),
]


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


# --- components -------------------------------------------------------------


def install_defaults(db: Session, school_id: int) -> list[SalaryComponent]:
    """Give a school §3.16's starting set, once."""
    existing = {
        c.code
        for c in db.scalars(
            select(SalaryComponent).where(SalaryComponent.school_id == school_id)
        )
    }
    made = []
    for (
        code, name, type_, calc, value, seq, active, statutory, taxable, threshold
    ) in DEFAULT_COMPONENTS:
        if code in existing:
            continue
        row = SalaryComponent(
            school_id=school_id,
            code=code,
            name=name,
            type=type_,
            calculation=calc,
            value=value,
            sequence=seq,
            active=active,
            statutory=statutory,
            taxable=taxable,
            applies_below_gross=threshold,
        )
        db.add(row)
        made.append(row)
    db.flush()
    return made


def components_for(db: Session, school_id: int) -> list[SalaryComponent]:
    """Active components in computation order.

    The order is the point, not decoration: basic has to exist before anything
    takes a percentage of it, and the balancing figure has to come after
    everything it balances against.
    """
    return list(
        db.scalars(
            select(SalaryComponent)
            .where(
                SalaryComponent.school_id == school_id,
                SalaryComponent.active.is_(True),
            )
            .order_by(SalaryComponent.sequence, SalaryComponent.code)
        )
    )


# --- structures -------------------------------------------------------------


def active_structure(db: Session, employee_id: int) -> SalaryStructure | None:
    return db.scalar(
        select(SalaryStructure).where(
            SalaryStructure.employee_id == employee_id,
            SalaryStructure.is_active.is_(True),
        )
    )


def set_structure(
    db: Session,
    user: User,
    employee: Employee,
    *,
    effective_from: Date,
    monthly_gross: Decimal,
    overrides: dict[str, Decimal] | None = None,
    note: str | None = None,
) -> SalaryStructure:
    """Put an employee on new terms.

    Supersedes rather than edits: a payslip issued last March must still be
    explicable by the terms in force then, so the old structure stays and is
    stood down.
    """
    if monthly_gross <= 0:
        raise _bad("A salary structure needs a gross above zero")

    # Checked before anything is stood down. Doing it the other way round meant
    # the unique constraint fired *after* the current structure was
    # deactivated, so the failure path left the employee on no terms at all —
    # and reported it as a 500 rather than as the ordinary mistake it is.
    clash = db.scalar(
        select(SalaryStructure).where(
            SalaryStructure.employee_id == employee.id,
            SalaryStructure.effective_from == effective_from,
        )
    )
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{employee.user.full_name} already has terms effective "
            f"{effective_from}. New terms start on a later date; the old ones "
            "stay so an old payslip can still be explained.",
        )

    current = active_structure(db, employee.id)
    if current is not None:
        current.is_active = False
        db.flush()

    row = SalaryStructure(
        school_id=employee.school_id,
        employee_id=employee.id,
        effective_from=effective_from,
        monthly_gross=money(monthly_gross),
        is_active=True,
        note=note,
    )
    db.add(row)
    db.flush()

    by_code = {c.code: c for c in components_for(db, employee.school_id)}
    for code, value in (overrides or {}).items():
        component = by_code.get(code)
        if component is None:
            raise _bad(f"{code} is not an active salary component")
        db.add(
            SalaryStructureItem(
                school_id=employee.school_id,
                structure_id=row.id,
                component_id=component.id,
                value=money(value),
            )
        )
    db.flush()

    audit.record(
        db,
        actor=user,
        school_id=employee.school_id,
        entity_type="salary_structure",
        entity_id=row.id,
        action=AuditAction.create,
        after={
            "employee_id": employee.id,
            "monthly_gross": str(row.monthly_gross),
            "effective_from": str(effective_from),
        },
    )
    return row


# --- the calculation --------------------------------------------------------


def compute(
    db: Session,
    structure: SalaryStructure,
    *,
    working_days: int,
    lop_days: Decimal,
) -> dict:
    """One payslip's lines and totals. Pure arithmetic — writes nothing.

    Kept separate from the run so a preview and the real thing cannot drift,
    and so the arithmetic can be tested without a payroll run existing.
    """
    gross = structure.monthly_gross
    overrides = {
        item.component_id: item
        for item in db.scalars(
            select(SalaryStructureItem).where(
                SalaryStructureItem.structure_id == structure.id
            )
        )
    }

    lines: list[dict] = []
    basic = ZERO
    earned = ZERO          # earnings settled so far, for the balancing figure
    deductions = ZERO
    employer = ZERO

    for component in components_for(db, structure.school_id):
        override = overrides.get(component.id)
        if override is not None and not override.included:
            continue
        rate = override.value if override is not None else component.value

        if (
            component.applies_below_gross is not None
            and gross > component.applies_below_gross
        ):
            # ESI above the threshold: not zero, absent. A zero line invites the
            # question "why is their ESI nil this month".
            continue

        match component.calculation:
            case CalculationMethod.fixed:
                amount = money(rate)
            case CalculationMethod.percent_of_basic:
                amount = money(basic * rate / 100)
            case CalculationMethod.percent_of_gross:
                amount = money(gross * rate / 100)
            case CalculationMethod.balance:
                # Whatever is left of gross. Never negative: a school whose
                # fixed components already exceed gross has a configuration
                # problem, and a negative allowance would hide it.
                amount = max(ZERO, money(gross - earned))
            case CalculationMethod.loss_of_pay:
                if not working_days or lop_days <= 0:
                    continue
                amount = money(gross / Decimal(working_days) * lop_days)
            case _:  # pragma: no cover - the enum is closed
                raise _bad(f"Unknown calculation method {component.calculation}")

        if amount <= 0 and component.calculation is not CalculationMethod.balance:
            continue

        if component.code == "BASIC":
            basic = amount
        if component.type is ComponentType.earning:
            earned += amount
        elif component.type is ComponentType.deduction:
            deductions += amount
        else:
            employer += amount

        lines.append(
            {
                "component_id": component.id,
                "code": component.code,
                "name": component.name,
                "type": component.type,
                "amount": amount,
                "sequence": component.sequence,
            }
        )

    net = money(earned - deductions)
    return {
        "lines": lines,
        "monthly_gross": gross,
        "total_earnings": money(earned),
        "total_deductions": money(deductions),
        "net_pay": net,
        # What the school spends, which is not what the employee receives.
        "employer_cost": money(earned + employer),
        "working_days": working_days,
        "lop_days": lop_days,
    }


# --- runs -------------------------------------------------------------------


def month_range(year: int, month: int) -> tuple[Date, Date]:
    return Date(year, month, 1), Date(year, month, monthrange(year, month)[1])


def open_run(
    db: Session, user: User, *, year: int, month: int, supplementary: bool = False
) -> PayrollRun:
    """Start a month's payroll, or a supplementary run for a month already
    approved."""
    if not 1 <= month <= 12:
        raise _bad("Month must be between 1 and 12")

    previous = list(
        db.scalars(
            select(PayrollRun)
            .where(
                PayrollRun.school_id == user.school_id,
                PayrollRun.year == year,
                PayrollRun.month == month,
            )
            .order_by(PayrollRun.run_no)
        )
    )
    open_already = [r for r in previous if r.is_open]
    if open_already:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Run {open_already[0].run_no} for {month}/{year} is still open. "
            "Approve or discard it before starting another.",
        )
    if previous and not supplementary:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{month}/{year} has already been run. A correction is a "
            "supplementary run, not a second ordinary one.",
        )

    start, end = month_range(year, month)
    row = PayrollRun(
        school_id=user.school_id,
        year=year,
        month=month,
        run_no=len(previous) + 1,
        is_supplementary=supplementary,
        status=PayrollRunStatus.draft,
        working_days=att.working_days(db, user.school_id, start, end),
    )
    db.add(row)
    db.flush()
    return row


def payable_staff(db: Session, school_id: int) -> list[Employee]:
    """Everyone in service with a salary structure in force.

    Somebody without one is not paid nothing — they are left off the run, and
    `calculate()` reports them, because a missing structure is an oversight and
    a zero payslip would hide it.
    """
    return [
        e
        for e in db.scalars(
            select(Employee)
            .where(
                Employee.school_id == school_id,
                Employee.status != EmployeeStatus.exited,
            )
            .order_by(Employee.employee_code)
        )
        if active_structure(db, e.id) is not None
    ]


def calculate(db: Session, user: User, run: PayrollRun) -> dict:
    """Work out every payslip in the run. Repeatable while the run is open."""
    if not run.is_open:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This run is {run.status.value} and can no longer be recalculated. "
            "A correction is a supplementary run.",
        )

    for old in db.scalars(select(Payslip).where(Payslip.run_id == run.id)):
        for line in db.scalars(
            select(PayslipLine).where(PayslipLine.payslip_id == old.id)
        ):
            db.delete(line)
        db.delete(old)
    db.flush()

    start, end = month_range(run.year, run.month)
    staff = payable_staff(db, run.school_id)
    made = []
    for employee in staff:
        structure = active_structure(db, employee.id)
        lop = staff_attendance.lop_days(db, employee, start, end)
        result = compute(
            db, structure, working_days=run.working_days or 0, lop_days=lop
        )
        slip = Payslip(
            school_id=run.school_id,
            run_id=run.id,
            employee_id=employee.id,
            payslip_no=audit.next_number(
                db, run.school_id, kind="payslip", year=run.year, prefix="PS"
            ),
            working_days=run.working_days or 0,
            lop_days=lop,
            monthly_gross=result["monthly_gross"],
            total_earnings=result["total_earnings"],
            total_deductions=result["total_deductions"],
            net_pay=result["net_pay"],
            employer_cost=result["employer_cost"],
        )
        db.add(slip)
        db.flush()
        for line in result["lines"]:
            db.add(
                PayslipLine(
                    school_id=run.school_id,
                    payslip_id=slip.id,
                    component_id=line["component_id"],
                    code=line["code"],
                    name=line["name"],
                    type=line["type"],
                    amount=line["amount"],
                    sequence=line["sequence"],
                )
            )
        made.append(slip)

    run.status = PayrollRunStatus.calculated
    run.calculated_at = datetime.now(UTC)
    db.flush()

    unpaid = [
        e.employee_code
        for e in db.scalars(
            select(Employee).where(
                Employee.school_id == run.school_id,
                Employee.status != EmployeeStatus.exited,
            )
        )
        if active_structure(db, e.id) is None
    ]
    return {"run": run, "payslips": made, "without_structure": sorted(unpaid)}


def approve(db: Session, user: User, run: PayrollRun, *, note: str | None = None) -> PayrollRun:
    """Freeze the run. After this nothing in it moves, ever."""
    if run.status is not PayrollRunStatus.calculated:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"A {run.status.value} run cannot be approved; calculate it first",
        )
    if not db.scalar(select(func.count(Payslip.id)).where(Payslip.run_id == run.id)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This run has no payslips to approve"
        )
    run.status = PayrollRunStatus.approved
    run.approved_at = datetime.now(UTC)
    run.approved_by = user.id
    run.note = note
    audit.record(
        db,
        actor=user,
        school_id=run.school_id,
        entity_type="payroll_run",
        entity_id=run.id,
        action=AuditAction.publish,
        after={
            "month": f"{run.month}/{run.year}",
            "run_no": run.run_no,
            "net_total": str(totals(db, run)["net_pay"]),
        },
    )
    db.flush()
    return run


def mark_paid(db: Session, user: User, run: PayrollRun) -> PayrollRun:
    if run.status is not PayrollRunStatus.approved:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"A {run.status.value} run cannot be marked paid",
        )
    run.status = PayrollRunStatus.paid
    run.paid_at = datetime.now(UTC)
    db.flush()
    return run


def discard(db: Session, user: User, run: PayrollRun, *, reason: str) -> None:
    """Throw away an unapproved run. Approved ones are never deleted."""
    if not run.is_open:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "An approved run is immutable. A correction is a supplementary run.",
        )
    audit.record(
        db,
        actor=user,
        school_id=run.school_id,
        entity_type="payroll_run",
        entity_id=run.id,
        action=AuditAction.delete,
        before={"month": f"{run.month}/{run.year}", "run_no": run.run_no},
        reason=reason,
    )
    for slip in db.scalars(select(Payslip).where(Payslip.run_id == run.id)):
        for line in db.scalars(
            select(PayslipLine).where(PayslipLine.payslip_id == slip.id)
        ):
            db.delete(line)
        db.delete(slip)
    db.delete(run)
    db.flush()


# --- reading ----------------------------------------------------------------


def totals(db: Session, run: PayrollRun) -> dict:
    row = db.execute(
        select(
            func.count(Payslip.id),
            func.coalesce(func.sum(Payslip.total_earnings), 0),
            func.coalesce(func.sum(Payslip.total_deductions), 0),
            func.coalesce(func.sum(Payslip.net_pay), 0),
            func.coalesce(func.sum(Payslip.employer_cost), 0),
        ).where(Payslip.run_id == run.id)
    ).first()
    count, earnings, deductions, net, cost = row
    return {
        "payslips": count,
        "total_earnings": money(Decimal(earnings)),
        "total_deductions": money(Decimal(deductions)),
        "net_pay": money(Decimal(net)),
        "employer_cost": money(Decimal(cost)),
    }


def cost_by_month(db: Session, school_id: int) -> list[dict]:
    """What staff actually cost the school, by month.

    Written here rather than in the report that wanted it, because payroll owns
    what a month's wage bill is and section 5.10.9 wants one definition rather
    than two queries that drift. The expense side of "revenue versus expense"
    (section 5.10.10) is this function, called.

    Only approved and paid runs count. A draft run is an arithmetic exercise
    somebody is still editing, and putting it on a management chart would show
    a cost the school has not committed to. A supplementary run adds to its
    month rather than replacing it, which is the whole reason `run_no` is part
    of the key.

    `employer_cost`, not `net_pay`: the employer's PF and ESI contributions are
    money the school spends and no payslip pays out.

    Months with no committed run are absent, not zero (section 5.10.9). A
    school that has not run March's payroll yet has an unknown March, not a
    free one.
    """
    rows = db.execute(
        select(
            PayrollRun.year,
            PayrollRun.month,
            func.sum(Payslip.employer_cost),
            func.count(Payslip.id),
        )
        .join(Payslip, Payslip.run_id == PayrollRun.id)
        .where(
            PayrollRun.school_id == school_id,
            PayrollRun.status.in_(
                (PayrollRunStatus.approved, PayrollRunStatus.paid)
            ),
        )
        .group_by(PayrollRun.year, PayrollRun.month)
        .order_by(PayrollRun.year, PayrollRun.month)
    ).all()
    return [
        {
            "month": f"{year:04d}-{month:02d}",
            "employer_cost": money(Decimal(cost)),
            "payslips": count,
        }
        for year, month, cost, count in rows
    ]


def register(db: Session, run: PayrollRun, code: str) -> list[dict]:
    """A statutory register: every payslip carrying one component (§5.3.10).

    This is why lines are a table and not a frozen blob — PF, ESI and TDS
    registers are queries *across* documents, and a JSON payload would make
    each of them a scan.
    """
    rows = db.execute(
        select(PayslipLine, Payslip, Employee)
        .join(Payslip, Payslip.id == PayslipLine.payslip_id)
        .join(Employee, Employee.id == Payslip.employee_id)
        .where(Payslip.run_id == run.id, PayslipLine.code == code)
        .order_by(Employee.employee_code)
    ).all()
    return [
        {
            "employee_code": employee.employee_code,
            "name": employee.user.full_name,
            "payslip_no": slip.payslip_no,
            "amount": line.amount,
        }
        for line, slip, employee in rows
    ]


def cost_by_department(db: Session, run: PayrollRun) -> list[dict]:
    """§5.3.10's payroll cost per department."""
    from app.models import Department

    rows = db.execute(
        select(
            Department.name,
            func.count(Payslip.id),
            func.coalesce(func.sum(Payslip.employer_cost), 0),
        )
        .select_from(Payslip)
        .join(Employee, Employee.id == Payslip.employee_id)
        .outerjoin(Department, Department.id == Employee.department_id)
        .where(Payslip.run_id == run.id)
        .group_by(Department.name)
        .order_by(Department.name)
    ).all()
    return [
        {"department": name, "staff": count, "cost": money(Decimal(cost))}
        for name, count, cost in rows
    ]


def payslip_out(db: Session, slip: Payslip) -> dict:
    lines = db.scalars(
        select(PayslipLine)
        .where(PayslipLine.payslip_id == slip.id)
        .order_by(PayslipLine.sequence)
    )
    run = db.get(PayrollRun, slip.run_id)
    return {
        "id": slip.id,
        "payslip_no": slip.payslip_no,
        "month": f"{run.month:02d}/{run.year}",
        "run_no": run.run_no,
        "status": run.status,
        "employee_id": slip.employee_id,
        "employee_code": slip.employee.employee_code,
        "name": slip.employee.user.full_name,
        "working_days": slip.working_days,
        "lop_days": slip.lop_days,
        "monthly_gross": slip.monthly_gross,
        "total_earnings": slip.total_earnings,
        "total_deductions": slip.total_deductions,
        "net_pay": slip.net_pay,
        "employer_cost": slip.employer_cost,
        "lines": [
            {
                "code": line.code,
                "name": line.name,
                "type": line.type,
                "amount": line.amount,
            }
            for line in lines
        ],
    }
