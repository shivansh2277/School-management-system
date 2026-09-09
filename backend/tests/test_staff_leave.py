"""Staff leave, and the classes it must not leave unattended.

§5.3.9 names approving a teacher's leave that silently leaves classes
unattended as the single most common real-world HR/timetable failure. The tests
that matter are the ones that check approval raised cover for every affected
period, and that a teacher who is themselves away can no longer be given
somebody else's lesson — the question `arrange()` could not ask before this
module existed.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AuditLog,
    Employee,
    Holiday,
    LeaveStatus,
    LeaveTypeDef,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import staff_leave as svc
from app.services import timetable

# Leave and balances sit behind module_enabled("hr"), which defaults to off for
# every new school (core/modules.py). A test buys the module, exactly as a
# school does; it does not reach around the gate.
pytestmark = pytest.mark.usefixtures("hr_enabled")


def next_weekday(start: date, weekday: int) -> date:
    """The next date on or after `start` falling on `weekday` (Mon=0)."""
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def a_monday_lesson(db, teacher_id):
    """One of this teacher's Monday lessons."""
    return next(
        s
        for s in db.scalars(
            select(TimetableSlot).where(TimetableSlot.teacher_id == teacher_id)
        )
        if s.day_of_week.value == "mon"
    )


def someone_free_for(db, school_id, slot):
    """A colleague with no lesson of their own in that day and period.

    Picking merely "a different employee" is not enough — the seeded timetable
    is dense, so an arbitrary colleague is usually already teaching then, and
    the test would pass or fail on which one it happened to pick.
    """
    busy = {
        s.teacher_id
        for s in db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.day_of_week == slot.day_of_week,
                TimetableSlot.period_id == slot.period_id,
            )
        )
    }
    return db.scalar(
        select(Employee).where(
            Employee.school_id == school_id, Employee.id.not_in(busy or {0})
        )
    )


@pytest.fixture()
def casual(db, ids):
    return db.scalar(
        select(LeaveTypeDef).where(
            LeaveTypeDef.school_id == ids["school"], LeaveTypeDef.code == "CL"
        )
    )


@pytest.fixture()
def teacher_1(db, ids):
    return db.get(Employee, ids["teacher_1"])


@pytest.fixture()
def year(db, ids):
    return ids["year"]


@pytest.fixture()
def monday(db):
    """A Monday comfortably in the future, so nothing seeded collides."""
    return next_weekday(date(2027, 1, 4), 0)


def apply(db, employee, casual, year, start, end=None, **kw):
    return svc.apply_for(
        db,
        employee,
        leave_type_id=casual.id,
        academic_year_id=year,
        from_date=start,
        to_date=end or start,
        reason="Family function",
        **kw,
    )


# --- types and balances ----------------------------------------------------


def test_the_demo_school_has_a_real_entitlement_structure(client, admin):
    rows = client.get("/admin/staff-leave/types", headers=admin).json()
    by_code = {t["code"]: t for t in rows}
    assert {"CL", "SL", "EL", "LWP"} <= set(by_code)
    assert Decimal(by_code["CL"]["annual_quota"]) == 12
    assert by_code["LWP"]["is_paid"] is False, "loss of pay needs an unpaid type"


def test_a_balance_opens_at_the_quota_on_first_use(db, teacher_1, casual, year):
    bal = svc.balance(db, teacher_1, casual, year)
    assert bal.entitled == 12
    assert bal.used == 0
    assert bal.remaining == 12


# --- applying --------------------------------------------------------------


def test_days_are_counted_from_the_school_calendar_not_the_diary(
    db, teacher_1, casual, year, monday
):
    """Mon to Sun is six working days, not seven: a Sunday is not leave, and
    charging somebody a casual day for one is noticed immediately."""
    row = apply(db, teacher_1, casual, year, monday, monday + timedelta(days=6))
    assert row.days == 6


def test_a_declared_holiday_inside_the_range_is_not_charged(
    db, teacher_1, casual, year, monday, ids
):
    db.add(
        Holiday(
            school_id=ids["school"],
            academic_year_id=ids["year"],
            date=monday + timedelta(days=1),
            name="Founders Day",
        )
    )
    db.flush()
    row = apply(db, teacher_1, casual, year, monday, monday + timedelta(days=2))
    assert row.days == 2, "three days minus the holiday"


def test_leave_across_a_shut_week_is_refused_rather_than_recorded_as_zero(
    db, teacher_1, casual, year
):
    sunday = next_weekday(date(2027, 1, 4), 6)
    with pytest.raises(Exception) as e:
        apply(db, teacher_1, casual, year, sunday, sunday)
    assert "no working days" in str(e.value.detail)


def test_a_half_day_is_half_a_day_and_covers_one_date(
    db, teacher_1, casual, year, monday
):
    row = apply(db, teacher_1, casual, year, monday, is_half_day=True)
    assert row.days == Decimal("0.5")
    with pytest.raises(Exception) as e:
        apply(db, teacher_1, casual, year, monday + timedelta(days=7),
              monday + timedelta(days=8), is_half_day=True)
    assert "covers one date" in str(e.value.detail)


def test_overlapping_requests_are_rejected(db, teacher_1, casual, year, monday):
    """Two approved leaves over the same Tuesday would each debit for it."""
    apply(db, teacher_1, casual, year, monday, monday + timedelta(days=2))
    with pytest.raises(Exception) as e:
        apply(db, teacher_1, casual, year, monday + timedelta(days=2),
              monday + timedelta(days=3))
    assert e.value.status_code == 409
    assert "overlaps" in str(e.value.detail)


def test_a_rejected_request_stops_blocking_the_dates(
    db, admin_user, teacher_1, casual, year, monday
):
    first = apply(db, teacher_1, casual, year, monday)
    svc.reject(db, admin_user, first, reason="Exam week")
    again = apply(db, teacher_1, casual, year, monday)
    assert again.id != first.id


def test_somebody_who_has_left_cannot_apply(db, admin_user, teacher_1, casual, year, monday):
    from app.models import EmployeeStatus

    teacher_1.status = EmployeeStatus.exited
    db.flush()
    with pytest.raises(Exception) as e:
        apply(db, teacher_1, casual, year, monday)
    assert "no longer in service" in str(e.value.detail)


# --- approval, and the rule with teeth -------------------------------------


def test_approving_a_teachers_leave_raises_cover_for_every_affected_period(
    db, admin_user, teacher_1, casual, year, monday
):
    """§5.3.9's headline. Approval must not merely set a status."""
    expected = db.scalar(
        select(TimetableSlot).where(TimetableSlot.teacher_id == teacher_1.id)
    )
    assert expected is not None, "TCH001 teaches"

    row = apply(db, teacher_1, casual, year, monday)
    result = svc.approve(db, admin_user, row)

    assert result["substitutions"], "a lesson was left uncovered and unrecorded"
    for cover in result["substitutions"]:
        assert cover.date == monday
        assert cover.absent_teacher_id == teacher_1.id
        assert cover.substitute_teacher_id is None
        assert cover.status is SubstitutionStatus.pending

    # Every Monday lesson of theirs, and nothing else.
    mondays = [
        s
        for s in db.scalars(
            select(TimetableSlot).where(TimetableSlot.teacher_id == teacher_1.id)
        )
        if s.day_of_week.value == "mon"
    ]
    assert len(result["substitutions"]) == len(mondays)


def test_cover_is_not_raised_for_a_day_the_school_is_shut(
    db, admin_user, teacher_1, casual, year, monday, ids
):
    db.add(
        Holiday(
            school_id=ids["school"],
            academic_year_id=ids["year"],
            date=monday,
            name="Founders Day",
        )
    )
    db.flush()
    row = apply(db, teacher_1, casual, year, monday, monday + timedelta(days=1))
    result = svc.approve(db, admin_user, row)
    assert all(c.date != monday for c in result["substitutions"])


def test_a_non_teaching_employee_leaves_no_class_uncovered(
    db, admin_user, casual, year, monday, ids
):
    user = User(
        school_id=ids["school"], role="teacher", login_id="ACC001",
        password_hash="x", full_name="Accounts Clerk",
    )
    db.add(user)
    db.flush()
    clerk = Employee(school_id=ids["school"], user_id=user.id, employee_code="ACC001")
    db.add(clerk)
    db.flush()
    row = apply(db, clerk, casual, year, monday)
    result = svc.approve(db, admin_user, row)
    assert result["substitutions"] == []


def test_approval_debits_the_balance(db, admin_user, teacher_1, casual, year, monday):
    before = svc.balance(db, teacher_1, casual, year).remaining
    row = apply(db, teacher_1, casual, year, monday, monday + timedelta(days=2))
    svc.approve(db, admin_user, row)
    assert svc.balance(db, teacher_1, casual, year).remaining == before - 3


def test_the_maintained_balance_agrees_with_the_requests(
    db, admin_user, teacher_1, casual, year, monday
):
    """`used` is incremented rather than recomputed because it is read on every
    application. This holds the fast number to the slow one."""
    for offset in (0, 7, 14):
        svc.approve(
            db, admin_user, apply(db, teacher_1, casual, year, monday + timedelta(days=offset))
        )
    bal = svc.balance(db, teacher_1, casual, year)
    assert bal.used == svc.used_from_requests(db, teacher_1.id, casual.id, year)


def test_leave_beyond_the_balance_needs_an_explicit_exception(
    db, admin_user, teacher_1, casual, year, monday
):
    row = apply(db, teacher_1, casual, year, monday, monday + timedelta(days=20))
    assert row.days > 12
    with pytest.raises(Exception) as e:
        svc.approve(db, admin_user, row)
    assert e.value.status_code == 409
    assert "explicit exception" in str(e.value.detail)

    result = svc.approve(db, admin_user, row, allow_exception=True)
    assert result["request"].balance_exception is True, "recorded, not inferred"


def test_a_decision_is_audited(db, admin_user, teacher_1, casual, year, monday):
    row = apply(db, teacher_1, casual, year, monday)
    svc.approve(db, admin_user, row, note="Approved by the principal")
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "staff_leave_request", AuditLog.entity_id == row.id
        )
    )
    assert entry is not None
    assert entry.after["substitutions_raised"] >= 1
    assert entry.reason == "Approved by the principal"


def test_a_request_cannot_be_decided_twice(
    db, admin_user, teacher_1, casual, year, monday
):
    row = apply(db, teacher_1, casual, year, monday)
    svc.approve(db, admin_user, row)
    with pytest.raises(Exception) as e:
        svc.approve(db, admin_user, row)
    assert e.value.status_code == 409


# --- cancelling ------------------------------------------------------------


def test_cancelling_credits_the_balance_back(
    db, admin_user, teacher_1, casual, year, monday
):
    before = svc.balance(db, teacher_1, casual, year).remaining
    row = apply(db, teacher_1, casual, year, monday)
    svc.approve(db, admin_user, row)
    svc.cancel(db, admin_user, row, reason="Plans changed")
    assert svc.balance(db, teacher_1, casual, year).remaining == before


def test_cancelling_drops_unfilled_cover_but_keeps_what_somebody_agreed_to(
    db, admin_user, teacher_1, casual, year, monday, ids
):
    """Deleting a filled substitution would be the system forgetting a
    conversation that actually happened with a colleague."""
    row = apply(db, teacher_1, casual, year, monday)
    result = svc.approve(db, admin_user, row)
    assert len(result["substitutions"]) >= 1

    filled = result["substitutions"][0]
    stand_in = db.scalar(
        select(Employee).where(Employee.id != teacher_1.id, Employee.school_id == ids["school"])
    )
    filled.substitute_teacher_id = stand_in.id
    filled.status = SubstitutionStatus.assigned
    db.flush()

    svc.cancel(db, admin_user, row, reason="Plans changed")
    db.flush()
    remaining = db.scalars(
        select(Substitution).where(
            Substitution.absent_teacher_id == teacher_1.id, Substitution.date == monday
        )
    ).all()
    assert [s.id for s in remaining] == [filled.id]


# --- the check the timetable could not make before -------------------------


def test_a_teacher_on_leave_cannot_be_given_somebody_elses_lesson(
    db, admin_user, teacher_1, casual, year, monday, ids
):
    """The gap Part 3 recorded and could not close. Being on leave is not a
    clash the timetable can see — they have no lesson that period precisely
    because they are not in."""
    slot = a_monday_lesson(db, teacher_1.id)
    stand_in = someone_free_for(db, ids["school"], slot)
    assert stand_in is not None
    svc.approve(db, admin_user, apply(db, stand_in, casual, year, monday))

    with pytest.raises(Exception) as e:
        timetable.arrange(
            db,
            admin_user,
            slot_id=slot.id,
            on=monday,
            substitute_teacher_id=stand_in.id,
            reason="Covering",
        )
    assert e.value.status_code == 409
    assert "on approved" in str(e.value.detail)


def test_a_teacher_not_on_leave_may_still_be_assigned(
    db, admin_user, teacher_1, monday, ids
):
    """The guard must refuse the away teacher and nobody else."""
    slot = a_monday_lesson(db, teacher_1.id)
    stand_in = someone_free_for(db, ids["school"], slot)
    row = timetable.arrange(
        db,
        admin_user,
        slot_id=slot.id,
        on=monday,
        substitute_teacher_id=stand_in.id,
        reason="Covering",
    )
    assert row.substitute_teacher_id == stand_in.id


def test_leave_on_another_date_does_not_block_the_substitute(
    db, admin_user, teacher_1, casual, year, monday, ids
):
    slot = a_monday_lesson(db, teacher_1.id)
    stand_in = someone_free_for(db, ids["school"], slot)
    svc.approve(
        db, admin_user, apply(db, stand_in, casual, year, monday + timedelta(days=7))
    )
    row = timetable.arrange(
        db, admin_user, slot_id=slot.id, on=monday,
        substitute_teacher_id=stand_in.id, reason="Covering",
    )
    assert row.substitute_teacher_id == stand_in.id


def test_an_applied_but_unapproved_leave_does_not_block(
    db, teacher_1, casual, year, monday, admin_user, ids
):
    """Only approved leave means somebody is actually away."""
    stand_in = someone_free_for(db, ids["school"], a_monday_lesson(db, teacher_1.id))
    apply(db, stand_in, casual, year, monday)
    assert svc.on_leave(db, stand_in.id, monday) is None


# --- the API ---------------------------------------------------------------


def test_the_api_surfaces_the_uncovered_classes_on_approval(
    client, admin, db, ids, monday, casual
):
    r = client.post(
        "/admin/staff-leave",
        headers=admin,
        json={
            "employee_id": ids["teacher_1"],
            "leave_type_id": casual.id,
            "from_date": str(monday),
            "to_date": str(monday),
            "reason": "Family function",
        },
    )
    assert r.status_code == 201, r.text
    request_id = r.json()["id"]

    preview = client.get(
        f"/admin/staff-leave/{request_id}/affected-periods", headers=admin
    ).json()
    assert preview, "the office should see this before deciding"

    approved = client.post(
        f"/admin/staff-leave/{request_id}/approve", headers=admin, json={}
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == LeaveStatus.approved.value
    assert len(body["substitutions_raised"]) == len(preview)
    assert all(s["substitute_teacher_id"] is None for s in body["substitutions_raised"])


def test_a_leave_request_of_another_school_is_not_found(client, admin):
    assert client.post(
        "/admin/staff-leave/999999/approve", headers=admin, json={}
    ).status_code == 404


def test_unused_leave_does_not_carry_forward(db, admin_user, teacher_1, casual, ids):
    """Owner's decision, 7 September 2026. A balance is keyed to the academic
    year and opens at that year's quota, so a new year starts fresh however
    much went untaken — there is deliberately no path that adds a remainder.

    This test exists to fail if a later session adds one, because carry-forward
    looks like a helpful omission and is a reversed decision.
    """
    from app.models import AcademicYear, AcademicYearStatus

    this_year = svc.balance(db, teacher_1, casual, ids["year"])
    this_year.used = Decimal(2)
    db.flush()
    assert this_year.remaining == 10, "ten days untaken"

    next_year = AcademicYear(
        school_id=ids["school"],
        code="2027-28",
        start_date="2027-04-01",
        end_date="2028-03-31",
        status=AcademicYearStatus.planning,
        is_current=False,
    )
    db.add(next_year)
    db.flush()

    opened = svc.balance(db, teacher_1, casual, next_year.id)
    assert opened.entitled == casual.annual_quota == 12
    assert opened.used == 0
    assert opened.remaining == 12, "the quota, not the quota plus last year's 10"
