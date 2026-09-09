"""The staff register, and the loss-of-pay days payroll is computed from.

This deliberately mirrors the student register rather than inventing a second
set of habits. The same three decisions Part 3 argued out apply unchanged, and
a test pins each:

- **A non-working day cannot be marked.** Sunday and a declared holiday come
  from the same calendar `attendance.working_days()` uses, so the staff
  register and the student one can never disagree about whether the school was
  open.
- **Correcting an earlier day needs a reason and is audited; fixing today's
  mark does not.** Somebody correcting a tap while the register is open is not
  amending a record.
- **Approving leave writes the register**, and leaves an already-marked day
  alone. Otherwise "approved leave" and what the register says disagree, and
  only whoever remembers reconciles them.

`lop_days()` is what payroll will call. It is deliberately the only place the
question "how many days is this person not being paid for" is answered.
"""

from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AttendanceStatus,
    AuditAction,
    Employee,
    EmployeeStatus,
    LeaveStatus,
    LeaveTypeDef,
    StaffAttendance,
    StaffLeaveRequest,
    User,
)
from app.services import attendance as att
from app.services import audit

def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def assert_school_open(db: Session, school_id: int, on: Date) -> None:
    holidays = att.holidays_between(db, school_id, on, on)
    if not att.is_working_day(on, holidays):
        raise _bad(f"The school is closed on {on}, so there is nothing to mark")


def roll(db: Session, school_id: int, on: Date) -> list[dict]:
    """Who is in today, in employee-code order.

    Every member of staff in service appears, marked or not — a register that
    lists only the people somebody remembered to mark is not a register.
    """
    marks = {
        m.employee_id: m
        for m in db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.school_id == school_id, StaffAttendance.date == on
            )
        )
    }
    staff = db.scalars(
        select(Employee)
        .where(
            Employee.school_id == school_id,
            Employee.status != EmployeeStatus.exited,
        )
        .order_by(Employee.employee_code)
    )
    rows = []
    for person in staff:
        mark = marks.get(person.id)
        rows.append(
            {
                "employee_id": person.id,
                "employee_code": person.employee_code,
                "full_name": person.user.full_name,
                "department": person.department.name if person.department else None,
                "status": mark.status if mark else None,
                "check_in": mark.check_in if mark else None,
                "check_out": mark.check_out if mark else None,
                "corrected": bool(mark and mark.corrected_by),
                "remarks": mark.remarks if mark else None,
            }
        )
    return rows


def mark(
    db: Session,
    user: User,
    *,
    on: Date,
    entries: list[dict],
    reason: str | None = None,
) -> list[dict]:
    """Mark or correct the register for one day.

    Correcting a day already marked *before today* requires a reason and lands
    in the audit log; today's register is still open and a fix to it is not an
    amendment.
    """
    school_id = user.school_id
    assert_school_open(db, school_id, on)
    is_past = on < datetime.now(UTC).date()

    existing = {
        m.employee_id: m
        for m in db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.school_id == school_id, StaffAttendance.date == on
            )
        )
    }
    in_service = {
        e.id: e
        for e in db.scalars(
            select(Employee).where(
                Employee.school_id == school_id,
                Employee.status != EmployeeStatus.exited,
            )
        )
    }

    corrections = [
        e
        for e in entries
        if (row := existing.get(e["employee_id"])) is not None
        and row.status != e["status"]
        and is_past
    ]
    if corrections and not (reason and reason.strip()):
        raise _bad(
            f"Changing {on}'s register is a correction to a record, and needs a "
            "reason"
        )

    for entry in entries:
        person = in_service.get(entry["employee_id"])
        if person is None:
            raise _bad("That employee is not in service at this school")
        row = existing.get(person.id)
        if row is None:
            db.add(
                StaffAttendance(
                    school_id=school_id,
                    employee_id=person.id,
                    date=on,
                    status=entry["status"],
                    check_in=entry.get("check_in"),
                    check_out=entry.get("check_out"),
                    remarks=entry.get("remarks"),
                    marked_by=user.id,
                )
            )
            continue

        before = audit.snapshot(row, ["status", "check_in", "check_out"])
        changed = row.status != entry["status"]
        row.status = entry["status"]
        if entry.get("check_in") is not None:
            row.check_in = entry["check_in"]
        if entry.get("check_out") is not None:
            row.check_out = entry["check_out"]
        if entry.get("remarks") is not None:
            row.remarks = entry["remarks"]
        if changed and is_past:
            row.corrected_by = user.id
            audit.record(
                db,
                actor=user,
                school_id=school_id,
                entity_type="staff_attendance",
                entity_id=row.id,
                action=AuditAction.status_change,
                before=before,
                after=audit.snapshot(row, ["status", "check_in", "check_out"]),
                reason=reason,
            )
    db.flush()
    return roll(db, school_id, on)


def write_leave(db: Session, request: StaffLeaveRequest) -> list[StaffAttendance]:
    """Put an approved leave into the register.

    Leaves an already-marked day alone: somebody physically present on a day
    they later got leave approved for was present, and overwriting that would
    make the register disagree with what actually happened.
    """
    from app.services.staff_leave import dates_in

    holidays = att.holidays_between(
        db, request.school_id, request.from_date, request.to_date
    )
    already = {
        m.date
        for m in db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.employee_id == request.employee_id,
                StaffAttendance.date >= request.from_date,
                StaffAttendance.date <= request.to_date,
            )
        )
    }
    written = []
    for day in dates_in(request.from_date, request.to_date):
        if not att.is_working_day(day, holidays) or day in already:
            continue
        row = StaffAttendance(
            school_id=request.school_id,
            employee_id=request.employee_id,
            date=day,
            status=AttendanceStatus.leave,
            remarks=f"{request.leave_type.name} approved",
            marked_by=None,
        )
        db.add(row)
        written.append(row)
    db.flush()
    return written


def lop_days(
    db: Session, employee: Employee, start: Date, end: Date
) -> Decimal:
    """Days in the range this person is not to be paid for.

    Two sources, and payroll must not have to know about either separately:
    a day marked `absent` in the register, and a day of approved leave against
    a type that does not pay. A day is counted once even if it is both.

    **A half day is not a deduction** (owner, 7 September 2026): somebody who
    came in for half a day is paid for the whole one. The mark is still kept —
    it is a real fact about attendance and it appears on the register and in
    the counts — it just does not reach this number.

    This is the only place the question is answered. §3.16 computes loss of pay
    as gross ÷ working days × absent days, and two definitions of "absent days"
    would put two different numbers on two different screens.
    """
    holidays = att.holidays_between(db, employee.school_id, start, end)

    unpaid_dates: set[Date] = set()
    unpaid_requests = db.scalars(
        select(StaffLeaveRequest)
        .join(LeaveTypeDef, LeaveTypeDef.id == StaffLeaveRequest.leave_type_id)
        .where(
            StaffLeaveRequest.employee_id == employee.id,
            StaffLeaveRequest.status == LeaveStatus.approved,
            LeaveTypeDef.is_paid.is_(False),
            StaffLeaveRequest.from_date <= end,
            StaffLeaveRequest.to_date >= start,
        )
    )
    from app.services.staff_leave import dates_in

    for request in unpaid_requests:
        for day in dates_in(
            max(request.from_date, start), min(request.to_date, end)
        ):
            if att.is_working_day(day, holidays):
                unpaid_dates.add(day)

    total = Decimal(len(unpaid_dates))

    marks = db.scalars(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == employee.id,
            StaffAttendance.date >= start,
            StaffAttendance.date <= end,
        )
    )
    for row in marks:
        if row.date in unpaid_dates or not att.is_working_day(row.date, holidays):
            continue
        if row.status is AttendanceStatus.absent:
            total += 1
        # A half day costs nothing. Decided by the owner on 7 September 2026:
        # somebody who came in for half a day is paid for the day. The status
        # is still recorded — it is a real fact about attendance and it shows
        # on the register and in the counts — it simply does not dock pay.
    return total


def summary(db: Session, employee: Employee, start: Date, end: Date) -> dict:
    """The month a payslip is computed from."""
    working = att.working_days(db, employee.school_id, start, end)
    marks = list(
        db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.employee_id == employee.id,
                StaffAttendance.date >= start,
                StaffAttendance.date <= end,
            )
        )
    )
    counts: dict[str, int] = {}
    for row in marks:
        counts[row.status.value] = counts.get(row.status.value, 0) + 1
    return {
        "employee_id": employee.id,
        "from": start,
        "to": end,
        "working_days": working,
        "marked_days": len(marks),
        "counts": counts,
        "lop_days": lop_days(db, employee, start, end),
    }
