"""Payroll: the arithmetic, the immutability, and who may do what.

This is a money path, so the tests that matter most are the ones that would
catch a wrong number on a payslip: that earnings always come to exactly the
gross, that a rate lives in a row rather than in the code, that loss of pay
comes from the one definition, and that an approved run cannot move.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AttendanceStatus,
    AuditLog,
    Employee,
    PayrollRunStatus,
    Payslip,
    PayslipLine,
    SalaryComponent,
    SalaryStructure,
)
from app.services import payroll as svc
from app.services import staff_attendance, staff_leave

# Salary structures, runs and payslips sit behind module_enabled("hr"), which defaults to off for
# every new school (core/modules.py). A test buys the module, exactly as a
# school does; it does not reach around the gate.
pytestmark = pytest.mark.usefixtures("hr_enabled")

YEAR, MONTH = 2026, 8


@pytest.fixture()
def teacher_1(db, ids):
    return db.get(Employee, ids["teacher_1"])


@pytest.fixture()
def run(db, admin_user):
    return svc.open_run(db, admin_user, year=YEAR, month=MONTH)


def component(db, ids, code) -> SalaryComponent:
    return db.scalar(
        select(SalaryComponent).where(
            SalaryComponent.school_id == ids["school"], SalaryComponent.code == code
        )
    )


def lines_of(db, slip) -> dict[str, Decimal]:
    return {
        line.code: line.amount
        for line in db.scalars(
            select(PayslipLine).where(PayslipLine.payslip_id == slip.id)
        )
    }


def slip_for(db, run, employee):
    return db.scalar(
        select(Payslip).where(
            Payslip.run_id == run.id, Payslip.employee_id == employee.id
        )
    )


# --- the arithmetic ---------------------------------------------------------


def test_the_default_components_are_the_blueprint_set(db, ids):
    codes = {
        c.code: c
        for c in db.scalars(
            select(SalaryComponent).where(SalaryComponent.school_id == ids["school"])
        )
    }
    assert {"BASIC", "HRA", "CONV", "SPL", "DA", "PF", "ESI", "PT", "TDS", "LOP",
            "PF_ER"} <= set(codes)
    assert codes["BASIC"].value == 50
    assert codes["HRA"].value == 40
    assert codes["PF"].value == 12
    assert codes["ESI"].applies_below_gross == 21000
    # Both off by default: most private schools pay no DA, and Uttar Pradesh
    # levies no professional tax (§0.B, confirmed by the owner).
    assert codes["DA"].active is False
    assert codes["PT"].active is False


def test_earnings_always_come_to_exactly_the_gross(db, admin_user, run):
    """The balancing figure's whole job. If this drifts, somebody is paid the
    wrong amount and the payslip still looks arithmetically tidy."""
    result = svc.calculate(db, admin_user, run)
    assert result["payslips"]
    for slip in result["payslips"]:
        assert slip.total_earnings == slip.monthly_gross, slip.employee.employee_code


def test_a_payslip_adds_up(db, admin_user, run, teacher_1):
    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, teacher_1)
    amounts = lines_of(db, slip)

    # 42,000 gross: basic 50%, HRA 40% of basic, conveyance fixed, the rest
    # falling to the balancing figure.
    assert amounts["BASIC"] == Decimal("21000.00")
    assert amounts["HRA"] == Decimal("8400.00")
    assert amounts["CONV"] == Decimal("1600.00")
    assert amounts["SPL"] == Decimal("11000.00")
    assert amounts["PF"] == Decimal("2520.00")
    assert slip.net_pay == slip.total_earnings - slip.total_deductions
    # What the school spends is not what the employee receives.
    assert slip.employer_cost == slip.total_earnings + amounts["PF_ER"]


def test_no_rate_lives_in_the_code(db, admin_user, ids, teacher_1):
    """§3.16's whole point. A school paying HRA at 30% edits a row."""
    hra = component(db, ids, "HRA")
    hra.value = Decimal(30)
    db.flush()

    run = svc.open_run(db, admin_user, year=YEAR, month=MONTH)
    svc.calculate(db, admin_user, run)
    amounts = lines_of(db, slip_for(db, run, teacher_1))
    assert amounts["HRA"] == Decimal("6300.00"), "30% of 21,000"
    # And the balancing figure absorbs the difference, so gross is unchanged.
    assert amounts["SPL"] == Decimal("13100.00")


def test_switching_a_component_off_removes_its_line(db, admin_user, ids, teacher_1):
    component(db, ids, "PF").active = False
    db.flush()
    run = svc.open_run(db, admin_user, year=YEAR, month=MONTH)
    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, teacher_1)
    assert "PF" not in lines_of(db, slip)
    assert slip.total_deductions == 0
    assert slip.net_pay == slip.monthly_gross


def test_esi_applies_below_the_threshold_and_is_absent_above_it(
    db, admin_user, run, ids
):
    """A zero line invites "why is their ESI nil this month". Absent is the
    honest answer for somebody the threshold does not reach."""
    svc.calculate(db, admin_user, run)
    below = db.scalar(
        select(Employee).where(Employee.employee_code == "TCH011")
    )  # 19,500 gross
    above = db.scalar(select(Employee).where(Employee.employee_code == "TCH001"))

    assert lines_of(db, slip_for(db, run, below))["ESI"] == Decimal("146.25")
    assert "ESI" not in lines_of(db, slip_for(db, run, above))


def test_a_per_employee_override_beats_the_school_default(
    db, admin_user, teacher_1, ids
):
    """How TDS is actually entered: the accountant computes a figure and puts
    it on one person, rather than the system guessing a slab."""
    tds = component(db, ids, "TDS")
    tds.active = True
    db.flush()
    svc.set_structure(
        db,
        admin_user,
        teacher_1,
        effective_from=date(2026, 7, 1),
        monthly_gross=Decimal(42000),
        overrides={"TDS": Decimal(2500)},
    )
    run = svc.open_run(db, admin_user, year=YEAR, month=MONTH)
    svc.calculate(db, admin_user, run)
    assert lines_of(db, slip_for(db, run, teacher_1))["TDS"] == Decimal("2500.00")


# --- loss of pay ------------------------------------------------------------


def test_loss_of_pay_is_gross_over_working_days_times_days_lost(
    db, admin_user, teacher_1, run
):
    day = date(YEAR, MONTH, 3)
    while day.weekday() == 6:
        day += timedelta(days=1)
    staff_attendance.mark(
        db,
        admin_user,
        on=day,
        entries=[{"employee_id": teacher_1.id, "status": AttendanceStatus.absent}],
    )
    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, teacher_1)

    assert slip.lop_days == 1
    expected = (Decimal(42000) / Decimal(slip.working_days)).quantize(Decimal("0.01"))
    assert lines_of(db, slip)["LOP"] == expected
    assert slip.net_pay == slip.total_earnings - slip.total_deductions


def test_a_half_day_does_not_reduce_pay(db, admin_user, teacher_1, run):
    """The owner's decision of 7 September 2026, arriving on the payslip: the
    mark is recorded and it costs nothing."""
    day = date(YEAR, MONTH, 3)
    while day.weekday() == 6:
        day += timedelta(days=1)
    staff_attendance.mark(
        db,
        admin_user,
        on=day,
        entries=[{"employee_id": teacher_1.id, "status": AttendanceStatus.half_day}],
    )
    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, teacher_1)
    assert slip.lop_days == 0
    assert "LOP" not in lines_of(db, slip)
    assert slip.net_pay == Decimal("39480.00")


def test_payroll_does_not_keep_its_own_idea_of_absent_days(
    db, admin_user, teacher_1, run, ids
):
    """Unpaid leave costs pay even though the register says `leave`, because
    payroll asks `staff_attendance.lop_days()` rather than reading the
    register. Two definitions would put two numbers on two screens."""
    from app.models import LeaveTypeDef

    lwp = db.scalar(
        select(LeaveTypeDef).where(
            LeaveTypeDef.school_id == ids["school"], LeaveTypeDef.code == "LWP"
        )
    )
    day = date(YEAR, MONTH, 10)
    while day.weekday() == 6:
        day += timedelta(days=1)
    request = staff_leave.apply_for(
        db,
        teacher_1,
        leave_type_id=lwp.id,
        academic_year_id=ids["year"],
        from_date=day,
        to_date=day,
        reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)

    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, teacher_1)
    assert slip.lop_days == 1
    assert "LOP" in lines_of(db, slip)
    assert slip.lop_days == staff_attendance.lop_days(
        db, teacher_1, *svc.month_range(YEAR, MONTH)
    )


# --- the run, and its immutability -----------------------------------------


def test_a_run_covers_everyone_with_a_structure_and_names_everyone_without(
    db, admin_user, run, ids
):
    """A missing structure is an oversight. A zero payslip would hide it."""
    from app.models import User

    user = User(
        school_id=ids["school"], role="teacher", login_id="TCH960",
        password_hash="x", full_name="No Terms Yet",
    )
    db.add(user)
    db.flush()
    db.add(Employee(school_id=ids["school"], user_id=user.id, employee_code="TCH960"))
    db.flush()

    result = svc.calculate(db, admin_user, run)
    # Sixteen: twelve teachers plus the transport manager, two drivers and the
    # bus attendant, who are employees and are paid like anybody else.
    assert len(result["payslips"]) == 16
    assert result["without_structure"] == ["TCH960"]


def test_recalculating_an_open_run_replaces_rather_than_duplicates(
    db, admin_user, run
):
    svc.calculate(db, admin_user, run)
    svc.calculate(db, admin_user, run)
    assert len(db.scalars(select(Payslip).where(Payslip.run_id == run.id)).all()) == 16


def test_an_approved_run_cannot_be_recalculated(db, admin_user, run):
    svc.calculate(db, admin_user, run)
    svc.approve(db, admin_user, run)
    with pytest.raises(Exception) as e:
        svc.calculate(db, admin_user, run)
    assert e.value.status_code == 409
    assert "supplementary run" in str(e.value.detail)


def test_an_approved_run_cannot_be_discarded(db, admin_user, run):
    svc.calculate(db, admin_user, run)
    svc.approve(db, admin_user, run)
    with pytest.raises(Exception) as e:
        svc.discard(db, admin_user, run, reason="Mistake")
    assert e.value.status_code == 409
    assert "immutable" in str(e.value.detail)


def test_an_empty_run_cannot_be_approved(db, admin_user, run):
    with pytest.raises(Exception) as e:
        svc.approve(db, admin_user, run)
    assert e.value.status_code == 409


def test_a_second_ordinary_run_for_the_month_is_refused(db, admin_user, run):
    svc.calculate(db, admin_user, run)
    svc.approve(db, admin_user, run)
    with pytest.raises(Exception) as e:
        svc.open_run(db, admin_user, year=YEAR, month=MONTH)
    assert "supplementary" in str(e.value.detail)


def test_a_correction_is_a_supplementary_run_standing_on_its_own(
    db, admin_user, run, teacher_1
):
    """§5.3.9. The first run's payslips are untouched by the second."""
    svc.calculate(db, admin_user, run)
    svc.approve(db, admin_user, run)
    first_net = slip_for(db, run, teacher_1).net_pay

    second = svc.open_run(db, admin_user, year=YEAR, month=MONTH, supplementary=True)
    assert second.run_no == 2 and second.is_supplementary
    svc.calculate(db, admin_user, second)

    assert slip_for(db, run, teacher_1).net_pay == first_net
    assert slip_for(db, second, teacher_1) is not None


def test_two_runs_cannot_be_open_at_once(db, admin_user, run):
    with pytest.raises(Exception) as e:
        svc.open_run(db, admin_user, year=YEAR, month=MONTH, supplementary=True)
    assert "still open" in str(e.value.detail)


def test_approval_is_audited_with_the_total(db, admin_user, run):
    svc.calculate(db, admin_user, run)
    svc.approve(db, admin_user, run)
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "payroll_run", AuditLog.entity_id == run.id
        )
    )
    assert entry is not None
    assert Decimal(entry.after["net_total"]) == svc.totals(db, run)["net_pay"]


def test_the_status_walks_forward_only(db, admin_user, run):
    with pytest.raises(Exception):
        svc.approve(db, admin_user, run)  # still draft
    svc.calculate(db, admin_user, run)
    with pytest.raises(Exception):
        svc.mark_paid(db, admin_user, run)  # not approved yet
    svc.approve(db, admin_user, run)
    svc.mark_paid(db, admin_user, run)
    assert run.status is PayrollRunStatus.paid


def test_payslip_numbers_come_from_the_gapless_sequence(db, admin_user, run):
    result = svc.calculate(db, admin_user, run)
    numbers = sorted(s.payslip_no for s in result["payslips"])
    assert all(n.startswith("PS") for n in numbers)
    assert len(set(numbers)) == len(numbers)


# --- reporting --------------------------------------------------------------


def test_a_statutory_register_is_a_query_across_payslips(db, admin_user, run):
    """Why lines are a table and not a frozen blob."""
    svc.calculate(db, admin_user, run)
    pf = svc.register(db, run, "PF")
    assert len(pf) == 16
    assert sum(r["amount"] for r in pf) > 0

    # ESI applies below a gross threshold, so the register is a subset rather
    # than a headcount. Asserted as the rule: everyone on it earns under the
    # threshold and somebody above it is absent, which stays true whoever the
    # demo school hires next. It was one PRT until the school gained two
    # drivers and a bus attendant.
    esi = svc.register(db, run, "ESI")
    threshold = db.scalar(
        select(SalaryComponent.applies_below_gross).where(
            SalaryComponent.school_id == run.school_id, SalaryComponent.code == "ESI"
        )
    )
    on_esi = {r["employee_code"] for r in esi}
    everyone = {r["employee_code"] for r in svc.register(db, run, "PF")}
    assert 0 < len(on_esi) < len(everyone)
    grosses = dict(
        db.execute(
            select(Employee.employee_code, SalaryStructure.monthly_gross)
            .join(SalaryStructure, SalaryStructure.employee_id == Employee.id)
            .where(
                SalaryStructure.school_id == run.school_id,
                SalaryStructure.is_active.is_(True),
            )
        ).all()
    )
    assert all(grosses[code] < threshold for code in on_esi)
    assert all(grosses[code] >= threshold for code in everyone - on_esi)


def test_cost_by_department_adds_up_to_the_run(db, admin_user, run):
    svc.calculate(db, admin_user, run)
    by_dept = svc.cost_by_department(db, run)
    assert sum(d["cost"] for d in by_dept) == svc.totals(db, run)["employer_cost"]
    assert {d["department"] for d in by_dept} >= {"Science and Mathematics"}


# --- who may do what --------------------------------------------------------


def test_whoever_prepares_the_payroll_does_not_sign_it_off():
    """The same segregation the fee counter already has (§5.3.8)."""
    from app.core.permissions import SYSTEM_ROLES

    roles = {code: set(perms) for code, _, perms in SYSTEM_ROLES}
    assert "payroll.run.manage" in roles["accountant"]
    assert "payroll.run.approve" not in roles["accountant"]
    assert "payroll.run.approve" in roles["principal"]
    assert "payroll.run.manage" not in roles["principal"]


def test_a_records_clerk_cannot_read_the_payroll():
    """`payroll.run.read` ends in `.read`, so without the exclusion the blanket
    read set would have handed the Admin Officer every salary in the school."""
    from app.core.permissions import NOT_BLANKET_READ, READ_ONLY, SYSTEM_ROLES

    assert "payroll.run.read" in NOT_BLANKET_READ
    assert "payroll.run.read" not in READ_ONLY
    roles = {code: set(perms) for code, _, perms in SYSTEM_ROLES}
    assert "payroll.run.read" not in roles["admin_officer"]
    assert "payroll.run.read" not in roles["teacher"]
    # Whoever signs a run off must be able to see what they are signing.
    assert "payroll.run.read" in roles["principal"]


def test_a_teacher_cannot_reach_payroll_at_all(client, teacher):
    assert client.get("/admin/payroll/components", headers=teacher).status_code == 403
    assert client.get("/admin/payroll/runs", headers=teacher).status_code == 403


def test_a_run_of_another_school_is_not_found(client, admin):
    assert client.post(
        "/admin/payroll/runs/999999/calculate", headers=admin
    ).status_code == 404


# --- the API, end to end ----------------------------------------------------


def test_a_payroll_run_completes_for_the_demo_school(client, admin, db):
    """Checkpoint 4's payroll half, as a test rather than a claim."""
    opened = client.post(
        "/admin/payroll/runs",
        headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert opened.status_code == 201, opened.text
    run_id = opened.json()["id"]
    assert opened.json()["working_days"] == 25

    calculated = client.post(f"/admin/payroll/runs/{run_id}/calculate", headers=admin)
    assert calculated.status_code == 200, calculated.text
    body = calculated.json()
    assert body["payslips"] == 16
    assert body["without_structure"] == []
    assert Decimal(body["net_pay"]) > 0

    approved = client.post(
        f"/admin/payroll/runs/{run_id}/approve", headers=admin, json={}
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    paid = client.post(f"/admin/payroll/runs/{run_id}/paid", headers=admin, json={})
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    slips = client.get(f"/admin/payroll/runs/{run_id}/payslips", headers=admin).json()
    assert len(slips) == 16
    one = slips[0]
    assert Decimal(one["total_earnings"]) == Decimal(one["monthly_gross"])
    assert {line["code"] for line in one["lines"]} >= {"BASIC", "HRA", "CONV", "SPL"}


def test_the_preview_and_the_run_cannot_drift(client, admin, db, ids, run, admin_user):
    """Both go through `compute()`, so a preview is the payslip in advance."""
    preview = client.get(
        f"/admin/payroll/preview/{ids['teacher_1']}",
        headers=admin,
        params={"year": YEAR, "month": MONTH},
    ).json()
    svc.calculate(db, admin_user, run)
    slip = slip_for(db, run, db.get(Employee, ids["teacher_1"]))
    assert Decimal(preview["net_pay"]) == slip.net_pay
    assert Decimal(preview["employer_cost"]) == slip.employer_cost


def test_new_terms_cannot_start_the_same_day_as_the_old_ones(
    db, admin_user, teacher_1
):
    """Two structures effective the same date is ambiguous, and the check runs
    before the current one is stood down — otherwise the failure path left the
    employee on no terms at all."""

    before = svc.active_structure(db, teacher_1.id)
    with pytest.raises(Exception) as e:
        svc.set_structure(
            db,
            admin_user,
            teacher_1,
            effective_from=before.effective_from,
            monthly_gross=Decimal(50000),
        )
    assert e.value.status_code == 409
    assert "later date" in str(e.value.detail)
    assert svc.active_structure(db, teacher_1.id).id == before.id


def test_new_terms_supersede_and_the_old_ones_survive(db, admin_user, teacher_1):
    """A payslip issued last March has to stay explicable by the terms in force
    then, so the old structure is stood down rather than edited."""
    from app.models import SalaryStructure

    old = svc.active_structure(db, teacher_1.id)
    new = svc.set_structure(
        db,
        admin_user,
        teacher_1,
        effective_from=date(2026, 10, 1),
        monthly_gross=Decimal(50000),
    )
    db.refresh(old)
    assert old.is_active is False
    assert old.monthly_gross == Decimal("42000.00"), "unchanged"
    assert svc.active_structure(db, teacher_1.id).id == new.id
    assert len(
        db.scalars(
            select(SalaryStructure).where(
                SalaryStructure.employee_id == teacher_1.id
            )
        ).all()
    ) == 2
