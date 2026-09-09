"""Staff leave: applying, approving, and what approval does to the timetable.

§5.3.9 names the failure this module exists to prevent, and calls it the single
most common real-world HR/timetable failure: **approving a teacher's leave that
silently leaves classes unattended.** Approval here therefore does not merely
set a status. It walks the teacher's timetable across the dates, and raises a
`pending` substitution for every period they were due to teach — so the class
appears on the arrangements queue as uncovered rather than being discovered
empty on the morning.

That reuses Part 3's `substitutions` table exactly as it stands: a row per date,
null substitute while nobody has been found, and §5.7.10's "unfilled" report
already counts them.

Two smaller rules, both §5.3.9:

- **Overlapping requests for one employee are rejected.** Two approved leaves
  covering the same Tuesday would each debit the balance for it.
- **Leave beyond the balance needs an explicit exception**, recorded on the
  request rather than inferred from the numbers not adding up.
"""

from datetime import UTC, date as Date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    DayOfWeek,
    Employee,
    LeaveBalance,
    LeaveStatus,
    LeaveTypeDef,
    StaffLeaveRequest,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import attendance as att
from app.services import audit
from app.services.timetable import DAY_BY_WEEKDAY

# A decision has been made; the request is no longer a claim on the balance.
CLOSED = (LeaveStatus.rejected, LeaveStatus.cancelled)
# Statuses that still hold days against the employee, for the overlap check.
LIVE = (LeaveStatus.applied, LeaveStatus.approved)


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


# --- leave types and balances ----------------------------------------------


def create_type(
    db: Session,
    school_id: int,
    *,
    code: str,
    name: str,
    annual_quota: Decimal,
    is_paid: bool = True,
) -> LeaveTypeDef:
    if annual_quota < 0:
        raise _bad("A leave type cannot have a negative quota")
    row = LeaveTypeDef(
        school_id=school_id,
        code=code.strip().upper(),
        name=name.strip(),
        annual_quota=Decimal(str(annual_quota)),
        is_paid=is_paid,
    )
    db.add(row)
    db.flush()
    return row


def types_for(db: Session, school_id: int) -> list[LeaveTypeDef]:
    return list(
        db.scalars(
            select(LeaveTypeDef)
            .where(LeaveTypeDef.school_id == school_id, LeaveTypeDef.active.is_(True))
            .order_by(LeaveTypeDef.code)
        )
    )


def balance(
    db: Session, employee: Employee, leave_type: LeaveTypeDef, academic_year_id: int
) -> LeaveBalance:
    """This employee's balance of this type, opened at the quota if absent.

    Opening it lazily rather than pre-creating one per employee per type per
    year means a new leave type does not need a backfill, and an employee who
    never takes casual leave carries no row.

    **Unused leave does not carry forward** (owner, 7 September 2026). The
    balance is keyed to the academic year and opens at the year's quota, so a
    new year starts fresh however much went untaken — there is deliberately no
    path that adds last year's remainder. A later session that "helpfully"
    carries a balance over is changing a decision, not fixing an omission;
    `test_unused_leave_does_not_carry_forward` fails if it does.
    """
    row = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.academic_year_id == academic_year_id,
        )
    )
    if row is None:
        row = LeaveBalance(
            school_id=employee.school_id,
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            academic_year_id=academic_year_id,
            entitled=leave_type.annual_quota,
            used=Decimal(0),
        )
        db.add(row)
        db.flush()
    return row


def balances_for(
    db: Session, employee: Employee, academic_year_id: int
) -> list[LeaveBalance]:
    return [
        balance(db, employee, t, academic_year_id)
        for t in types_for(db, employee.school_id)
    ]


# --- applying ---------------------------------------------------------------


def _days(
    db: Session, school_id: int, start: Date, end: Date, half_day: bool
) -> Decimal:
    """Working days in the range, from the same calendar attendance uses.

    A Sunday or a declared holiday is not leave — charging somebody a casual
    day for a Sunday is the kind of arithmetic staff notice immediately.
    """
    count = att.working_days(db, school_id, start, end)
    if half_day:
        if start != end:
            raise _bad("A half day covers one date")
        return Decimal("0.5") if count else Decimal(0)
    return Decimal(count)


def overlapping(
    db: Session, employee: Employee, start: Date, end: Date, exclude_id: int | None = None
) -> StaffLeaveRequest | None:
    q = select(StaffLeaveRequest).where(
        StaffLeaveRequest.employee_id == employee.id,
        StaffLeaveRequest.status.in_(LIVE),
        StaffLeaveRequest.from_date <= end,
        StaffLeaveRequest.to_date >= start,
    )
    if exclude_id is not None:
        q = q.where(StaffLeaveRequest.id != exclude_id)
    return db.scalar(q)


def apply_for(
    db: Session,
    employee: Employee,
    *,
    leave_type_id: int,
    academic_year_id: int,
    from_date: Date,
    to_date: Date,
    reason: str,
    is_half_day: bool = False,
) -> StaffLeaveRequest:
    if to_date < from_date:
        raise _bad("The last day cannot precede the first")
    if not employee.in_service:
        raise _bad(f"{employee.user.full_name} is no longer in service")

    leave_type = db.get(LeaveTypeDef, leave_type_id)
    if leave_type is None or leave_type.school_id != employee.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave type not found")

    clash = overlapping(db, employee, from_date, to_date)
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This overlaps an existing request from {clash.from_date} to "
            f"{clash.to_date}",
        )

    days = _days(db, employee.school_id, from_date, to_date, is_half_day)
    if days <= 0:
        raise _bad(
            "Those dates contain no working days — the school is closed "
            "throughout"
        )

    row = StaffLeaveRequest(
        school_id=employee.school_id,
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        academic_year_id=academic_year_id,
        from_date=from_date,
        to_date=to_date,
        is_half_day=is_half_day,
        days=days,
        reason=reason,
        status=LeaveStatus.applied,
    )
    db.add(row)
    db.flush()
    return row


# --- what a teacher was due to teach ---------------------------------------


def dates_in(start: Date, end: Date) -> list[Date]:
    return [start + timedelta(days=n) for n in range((end - start).days + 1)]


def affected_periods(
    db: Session, request: StaffLeaveRequest
) -> list[tuple[Date, TimetableSlot]]:
    """Every lesson this teacher would have taught across the leave.

    Empty for a non-teaching employee, which is correct rather than a special
    case: the accountant's leave leaves no class unattended.
    """
    slots = list(
        db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.teacher_id == request.employee_id
            )
        )
    )
    if not slots:
        return []
    by_day: dict[DayOfWeek, list[TimetableSlot]] = {}
    for slot in slots:
        by_day.setdefault(slot.day_of_week, []).append(slot)

    holidays = att.holidays_between(
        db, request.school_id, request.from_date, request.to_date
    )
    out = []
    for day in dates_in(request.from_date, request.to_date):
        if not att.is_working_day(day, holidays):
            continue
        for slot in by_day.get(DAY_BY_WEEKDAY.get(day.weekday()), []):
            out.append((day, slot))
    return out


def on_leave(db: Session, employee_id: int, on: Date) -> StaffLeaveRequest | None:
    """Is this member of staff on approved leave that day?

    The question `timetable.arrange()` could not ask before this module existed,
    and the reason a substitute could be assigned to cover a lesson on a day
    they were themselves away.
    """
    return db.scalar(
        select(StaffLeaveRequest).where(
            StaffLeaveRequest.employee_id == employee_id,
            StaffLeaveRequest.status == LeaveStatus.approved,
            StaffLeaveRequest.from_date <= on,
            StaffLeaveRequest.to_date >= on,
        )
    )


# --- deciding ---------------------------------------------------------------


def approve(
    db: Session,
    user: User,
    request: StaffLeaveRequest,
    *,
    note: str | None = None,
    allow_exception: bool = False,
) -> dict:
    """Approve, debit the balance, and raise cover for every affected lesson.

    Returns the request with the substitutions it created, because §5.3.9 wants
    approval to *surface* the affected periods rather than leave them to be
    discovered. An unfilled row is the honest state and §5.7.10 already counts
    it; what must not happen is no row at all.
    """
    if request.status is not LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )

    employee = db.get(Employee, request.employee_id)
    bal = balance(db, employee, request.leave_type, request.academic_year_id)
    if request.days > bal.remaining and not allow_exception:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{employee.user.full_name} has {bal.remaining} day(s) of "
            f"{request.leave_type.name} left and this request is "
            f"{request.days}. Approving it anyway is an explicit exception.",
        )

    request.balance_exception = request.days > bal.remaining
    bal.used = bal.used + request.days
    request.status = LeaveStatus.approved
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = note

    # Approving leave writes the register, exactly as student leave does. Any
    # other arrangement leaves "approved leave" in one table and `absent` in
    # another, reconciled only by whoever remembers.
    from app.services import staff_attendance

    register = staff_attendance.write_leave(db, request)

    created = []
    for day, slot in affected_periods(db, request):
        existing = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id, Substitution.date == day
            )
        )
        if existing is not None:
            continue
        cover = Substitution(
            school_id=request.school_id,
            timetable_slot_id=slot.id,
            date=day,
            absent_teacher_id=request.employee_id,
            substitute_teacher_id=None,
            reason=f"{request.leave_type.name} approved for "
            f"{employee.user.full_name}",
            status=SubstitutionStatus.pending,
        )
        db.add(cover)
        created.append(cover)
    db.flush()

    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={
            "status": LeaveStatus.approved.value,
            "days": str(request.days),
            "balance_exception": request.balance_exception,
            "substitutions_raised": len(created),
            "register_days_written": len(register),
        },
        reason=note or "Leave approved",
        academic_year_id=request.academic_year_id,
    )
    return {
        "request": request,
        "substitutions": created,
        "register_days": register,
    }


def reject(
    db: Session, user: User, request: StaffLeaveRequest, *, reason: str
) -> StaffLeaveRequest:
    if request.status is not LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )
    request.status = LeaveStatus.rejected
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = reason
    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={"status": LeaveStatus.rejected.value},
        reason=reason,
        academic_year_id=request.academic_year_id,
    )
    db.flush()
    return request


def cancel(
    db: Session, user: User, request: StaffLeaveRequest, *, reason: str
) -> StaffLeaveRequest:
    """Withdraw a request, crediting the balance back if it was approved.

    The substitutions raised for it are dropped only where nobody has been
    found yet: a colleague who already agreed to cover has been told, and
    deleting the row would be the system forgetting a conversation that
    happened.
    """
    if request.status in CLOSED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )
    if request.status is LeaveStatus.approved:
        employee = db.get(Employee, request.employee_id)
        bal = balance(db, employee, request.leave_type, request.academic_year_id)
        bal.used = max(Decimal(0), bal.used - request.days)
        # The register rows this leave wrote go with it; a day somebody was
        # actually marked present on is left alone, because `write_leave` never
        # touched it.
        from app.models import AttendanceStatus, StaffAttendance

        for row in db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.employee_id == request.employee_id,
                StaffAttendance.date >= request.from_date,
                StaffAttendance.date <= request.to_date,
                StaffAttendance.status == AttendanceStatus.leave,
                StaffAttendance.marked_by.is_(None),
            )
        ):
            db.delete(row)
        for cover in db.scalars(
            select(Substitution).where(
                Substitution.absent_teacher_id == request.employee_id,
                Substitution.date >= request.from_date,
                Substitution.date <= request.to_date,
                Substitution.substitute_teacher_id.is_(None),
            )
        ):
            db.delete(cover)

    request.status = LeaveStatus.cancelled
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = reason
    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.approved.value},
        after={"status": LeaveStatus.cancelled.value},
        reason=reason,
        academic_year_id=request.academic_year_id,
    )
    db.flush()
    return request


def to_out(db: Session, row: StaffLeaveRequest) -> dict:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "employee": row.employee.user.full_name,
        "employee_code": row.employee.employee_code,
        "leave_type": row.leave_type.code,
        "leave_type_name": row.leave_type.name,
        "from_date": row.from_date,
        "to_date": row.to_date,
        "is_half_day": row.is_half_day,
        "days": row.days,
        "reason": row.reason,
        "status": row.status,
        "balance_exception": row.balance_exception,
        "decided_at": row.decided_at,
        "decision_note": row.decision_note,
    }


def used_from_requests(
    db: Session, employee_id: int, leave_type_id: int, academic_year_id: int
) -> Decimal:
    """What the approved requests add up to.

    `LeaveBalance.used` is maintained incrementally because it is read on every
    application; this is the same number derived the slow way, and a test holds
    the two together.
    """
    total = db.scalar(
        select(func.sum(StaffLeaveRequest.days)).where(
            StaffLeaveRequest.employee_id == employee_id,
            StaffLeaveRequest.leave_type_id == leave_type_id,
            StaffLeaveRequest.academic_year_id == academic_year_id,
            StaffLeaveRequest.status == LeaveStatus.approved,
        )
    )
    return Decimal(total or 0)
