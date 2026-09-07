"""The staff register, and the loss-of-pay days payroll will be computed from.

`lop_days()` is the number that will multiply against somebody's salary, so the
tests that matter are the ones that stop it double-counting a day that is both
marked absent and covered by unpaid leave, and the ones that stop it charging
anybody for a Sunday.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AttendanceStatus,
    AuditLog,
    Employee,
    Holiday,
    LeaveTypeDef,
    StaffAttendance,
)
from app.services import staff_attendance as svc
from app.services import staff_leave


def next_weekday(start: date, weekday: int) -> date:
    return start + timedelta(days=(weekday - start.weekday()) % 7)


@pytest.fixture()
def monday(db):
    return next_weekday(date(2027, 2, 1), 0)


@pytest.fixture()
def teacher_1(db, ids):
    return db.get(Employee, ids["teacher_1"])


@pytest.fixture()
def lwp(db, ids):
    """The unpaid type: the reason loss of pay has a source other than the
    register."""
    return db.scalar(
        select(LeaveTypeDef).where(
            LeaveTypeDef.school_id == ids["school"], LeaveTypeDef.code == "LWP"
        )
    )


def mark(db, user, on, employee, status, **kw):
    return svc.mark(
        db,
        user,
        on=on,
        entries=[{"employee_id": employee.id, "status": status, **kw}],
        reason=kw.pop("reason", None),
    )


# --- the register ----------------------------------------------------------


def test_the_roll_lists_everyone_in_service_marked_or_not(
    client, admin, db, ids, monday
):
    rows = client.get(
        "/admin/staff-attendance", headers=admin, params={"date": str(monday)}
    ).json()
    assert len(rows) == 12, "twelve staff, none marked yet"
    assert all(r["status"] is None for r in rows)
    assert rows[0]["employee_code"] == "TCH001"
    assert rows[0]["department"] == "Science and Mathematics"


def test_a_day_the_school_is_shut_cannot_be_marked(db, admin_user, teacher_1):
    sunday = next_weekday(date(2027, 2, 1), 6)
    with pytest.raises(Exception) as e:
        mark(db, admin_user, sunday, teacher_1, AttendanceStatus.present)
    assert "closed" in str(e.value.detail)


def test_a_declared_holiday_cannot_be_marked_either(
    db, admin_user, teacher_1, monday, ids
):
    """The same calendar the student register uses, so the two can never
    disagree about whether the school was open."""
    db.add(
        Holiday(
            school_id=ids["school"],
            academic_year_id=ids["year"],
            date=monday,
            name="Founders Day",
        )
    )
    db.flush()
    with pytest.raises(Exception) as e:
        mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    assert "closed" in str(e.value.detail)


def test_marking_is_idempotent(db, admin_user, teacher_1, monday):
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    rows = db.scalars(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id, StaffAttendance.date == monday
        )
    ).all()
    assert len(rows) == 1


def test_somebody_who_has_left_cannot_be_marked(db, admin_user, teacher_1, monday):
    from app.models import EmployeeStatus

    teacher_1.status = EmployeeStatus.exited
    db.flush()
    with pytest.raises(Exception) as e:
        mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    assert "not in service" in str(e.value.detail)


# --- correcting, which is a different act from marking ---------------------


def test_fixing_todays_register_is_not_a_correction(db, admin_user, teacher_1):
    """Somebody fixing a tap while the register is open is not amending a
    record — the same distinction the student register draws."""
    from datetime import UTC, datetime

    today = datetime.now(UTC).date()
    holidays = svc.att.holidays_between(db, teacher_1.school_id, today, today)
    if not svc.att.is_working_day(today, holidays):
        pytest.skip("today is not a working day")

    mark(db, admin_user, today, teacher_1, AttendanceStatus.absent)
    mark(db, admin_user, today, teacher_1, AttendanceStatus.present)
    row = db.scalar(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id, StaffAttendance.date == today
        )
    )
    assert row.status is AttendanceStatus.present
    assert row.corrected_by is None


def test_changing_an_earlier_day_needs_a_reason(db, admin_user, teacher_1):
    past = next_weekday(date(2026, 8, 3), 0)
    mark(db, admin_user, past, teacher_1, AttendanceStatus.absent)
    with pytest.raises(Exception) as e:
        mark(db, admin_user, past, teacher_1, AttendanceStatus.present)
    assert "needs a reason" in str(e.value.detail)


def test_a_correction_is_audited_with_both_marks(db, admin_user, teacher_1):
    past = next_weekday(date(2026, 8, 3), 0)
    mark(db, admin_user, past, teacher_1, AttendanceStatus.absent)
    svc.mark(
        db,
        admin_user,
        on=past,
        entries=[{"employee_id": teacher_1.id, "status": AttendanceStatus.present}],
        reason="Signed the muster; the register was marked in error",
    )
    row = db.scalar(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id, StaffAttendance.date == past
        )
    )
    assert row.corrected_by == admin_user.id
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "staff_attendance", AuditLog.entity_id == row.id
        )
    )
    assert entry.before["status"] == "absent"
    assert entry.after["status"] == "present"
    assert "marked in error" in entry.reason


# --- approved leave writes the register ------------------------------------


def test_approving_leave_writes_the_register(
    db, admin_user, teacher_1, lwp, ids, monday
):
    """Otherwise "approved leave" is in one table and `absent` in another, and
    only whoever remembers reconciles them."""
    request = staff_leave.apply_for(
        db,
        teacher_1,
        leave_type_id=lwp.id,
        academic_year_id=ids["year"],
        from_date=monday,
        to_date=monday + timedelta(days=1),
        reason="Personal",
    )
    result = staff_leave.approve(db, admin_user, request, allow_exception=True)
    assert len(result["register_days"]) == 2
    rows = db.scalars(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id,
            StaffAttendance.date >= monday,
        )
    ).all()
    assert {r.status for r in rows} == {AttendanceStatus.leave}
    assert all(r.marked_by is None for r in rows), "nobody marked these"


def test_approving_leave_leaves_an_already_marked_day_alone(
    db, admin_user, teacher_1, lwp, ids, monday
):
    """Somebody physically present on a day they later got leave approved for
    was present, and overwriting that makes the register lie."""
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    request = staff_leave.apply_for(
        db, teacher_1, leave_type_id=lwp.id, academic_year_id=ids["year"],
        from_date=monday, to_date=monday + timedelta(days=1), reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)
    row = db.scalar(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id, StaffAttendance.date == monday
        )
    )
    assert row.status is AttendanceStatus.present


def test_cancelling_leave_removes_the_rows_it_wrote_and_no_others(
    db, admin_user, teacher_1, lwp, ids, monday
):
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.present)
    request = staff_leave.apply_for(
        db, teacher_1, leave_type_id=lwp.id, academic_year_id=ids["year"],
        from_date=monday, to_date=monday + timedelta(days=1), reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)
    staff_leave.cancel(db, admin_user, request, reason="Plans changed")
    db.flush()

    rows = db.scalars(
        select(StaffAttendance).where(
            StaffAttendance.employee_id == teacher_1.id,
            StaffAttendance.date >= monday,
            StaffAttendance.date <= monday + timedelta(days=1),
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].status is AttendanceStatus.present, "the marked day survived"


# --- loss of pay, which is what payroll multiplies against -----------------


def test_a_day_marked_absent_is_a_day_not_paid(db, admin_user, teacher_1, monday):
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.absent)
    assert svc.lop_days(db, teacher_1, monday, monday) == 1


def test_a_half_day_costs_half(db, admin_user, teacher_1, monday):
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.half_day)
    assert svc.lop_days(db, teacher_1, monday, monday) == Decimal("0.5")


def test_present_late_and_paid_leave_cost_nothing(
    db, admin_user, teacher_1, monday
):
    for offset, state in enumerate(
        (AttendanceStatus.present, AttendanceStatus.late, AttendanceStatus.leave)
    ):
        mark(db, admin_user, monday + timedelta(days=offset), teacher_1, state)
    assert svc.lop_days(db, teacher_1, monday, monday + timedelta(days=2)) == 0


def test_unpaid_leave_costs_even_though_the_register_says_leave(
    db, admin_user, teacher_1, lwp, ids, monday
):
    """The second source. The register says `leave` for both paid and unpaid,
    so reading it alone would pay somebody for leave without pay."""
    request = staff_leave.apply_for(
        db, teacher_1, leave_type_id=lwp.id, academic_year_id=ids["year"],
        from_date=monday, to_date=monday + timedelta(days=1), reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)
    assert svc.lop_days(db, teacher_1, monday, monday + timedelta(days=1)) == 2


def test_a_day_that_is_both_absent_and_unpaid_leave_is_counted_once(
    db, admin_user, teacher_1, lwp, ids, monday
):
    """The double-count that would quietly dock somebody twice."""
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.absent)
    request = staff_leave.apply_for(
        db, teacher_1, leave_type_id=lwp.id, academic_year_id=ids["year"],
        from_date=monday, to_date=monday, reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)
    assert svc.lop_days(db, teacher_1, monday, monday) == 1


def test_nobody_is_docked_for_a_sunday_or_a_holiday(
    db, admin_user, teacher_1, lwp, ids, monday
):
    """Unpaid leave spanning a week must not charge for the Sunday inside it."""
    request = staff_leave.apply_for(
        db, teacher_1, leave_type_id=lwp.id, academic_year_id=ids["year"],
        from_date=monday, to_date=monday + timedelta(days=6), reason="Personal",
    )
    staff_leave.approve(db, admin_user, request, allow_exception=True)
    assert svc.lop_days(db, teacher_1, monday, monday + timedelta(days=6)) == 6


def test_the_summary_is_the_month_a_payslip_is_computed_from(
    client, admin, db, admin_user, teacher_1, monday
):
    mark(db, admin_user, monday, teacher_1, AttendanceStatus.absent)
    db.flush()
    r = client.get(
        f"/admin/staff-attendance/summary/{teacher_1.id}",
        headers=admin,
        params={"from": str(monday), "to": str(monday + timedelta(days=5))},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["working_days"] == 6
    assert Decimal(body["lop_days"]) == 1
    assert body["counts"]["absent"] == 1
