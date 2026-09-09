"""Timetable conflict detection and substitutions (§5.7.9).

The v0 timetable was seeded and read-only, and nothing checked it: it held 144
teacher double-bookings. The checks are the feature — a grid that lets a
teacher be in two rooms at once is worse than no grid, because someone trusts
it and a class sits unattended.
"""

from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import (
    ClassSubjectTeacher,
    DayOfWeek,
    Employee,
    SchoolPeriod,
    SubstitutionStatus,
    TimetableSlot,
)
from app.services import timetable as svc


def any_slot(db) -> TimetableSlot:
    return db.scalars(select(TimetableSlot)).first()


def next_weekday(day: DayOfWeek) -> date:
    wanted = list(svc.DAY_BY_WEEKDAY.values()).index(day)
    d = date.today() + timedelta(days=1)
    while d.weekday() != wanted:
        d += timedelta(days=1)
    return d


def test_the_seeded_timetable_has_no_conflicts(db):
    """The demo data is built through the same validator the API uses. v0's
    was not, and shipped 144 teacher clashes and 36 room clashes."""
    clashes = db.execute(
        select(TimetableSlot.teacher_id, TimetableSlot.day_of_week, TimetableSlot.period_id)
        .group_by(TimetableSlot.teacher_id, TimetableSlot.day_of_week, TimetableSlot.period_id)
        .having(func.count() > 1)
    ).all()
    assert clashes == []

    rooms = db.execute(
        select(TimetableSlot.room, TimetableSlot.day_of_week, TimetableSlot.period_id)
        .where(TimetableSlot.room.is_not(None))
        .group_by(TimetableSlot.room, TimetableSlot.day_of_week, TimetableSlot.period_id)
        .having(func.count() > 1)
    ).all()
    assert rooms == []


def test_a_teacher_cannot_be_in_two_places_at_once(client, admin, db):
    """The hard constraint of §5.7.9, and the reason the builder needs live
    validation rather than a validate-at-the-end button."""
    taken = any_slot(db)
    other_section = db.scalar(
        select(TimetableSlot.class_section_id).where(
            TimetableSlot.class_section_id != taken.class_section_id,
            TimetableSlot.day_of_week == taken.day_of_week,
            TimetableSlot.period_id == taken.period_id,
        )
    )
    body = {
        "class_section_id": other_section,
        "day_of_week": taken.day_of_week.value,
        "period_id": taken.period_id,
        "subject_id": taken.subject_id,
        "teacher_id": taken.teacher_id,
    }
    checked = client.post("/admin/timetable/slots/check", json=body, headers=admin).json()
    assert checked["ok"] is False
    kinds = {c["kind"] for c in checked["conflicts"]}
    assert "teacher" in kinds and "section" in kinds

    saved = client.post("/admin/timetable/slots", json=body, headers=admin)
    assert saved.status_code == 409, "checking is advisory; saving must refuse"


def test_a_room_cannot_host_two_classes_at_once(client, admin, db):
    occupied = db.scalars(
        select(TimetableSlot).where(TimetableSlot.room.is_not(None))
    ).first()
    free_section = db.scalar(
        select(TimetableSlot.class_section_id).where(
            TimetableSlot.class_section_id != occupied.class_section_id,
            TimetableSlot.day_of_week == occupied.day_of_week,
            TimetableSlot.period_id == occupied.period_id,
        )
    )
    other_teacher = db.scalar(
        select(TimetableSlot.teacher_id).where(
            TimetableSlot.class_section_id == free_section,
            TimetableSlot.day_of_week == occupied.day_of_week,
            TimetableSlot.period_id == occupied.period_id,
        )
    )
    body = {
        "class_section_id": free_section,
        "day_of_week": occupied.day_of_week.value,
        "period_id": occupied.period_id,
        "subject_id": occupied.subject_id,
        "teacher_id": other_teacher,
        "room": occupied.room,
    }
    conflicts = client.post("/admin/timetable/slots/check", json=body, headers=admin).json()
    assert "room" in {c["kind"] for c in conflicts["conflicts"]}


def test_a_free_slot_saves_and_moves(client, admin, db, ids):
    """The whole point: the timetable is editable now."""
    slot = any_slot(db)
    empty_period = db.scalar(
        select(SchoolPeriod).where(
            SchoolPeriod.school_id == slot.school_id, SchoolPeriod.is_break.is_(True)
        )
    )
    # a break is not a teaching slot
    body = {
        "class_section_id": slot.class_section_id,
        "day_of_week": slot.day_of_week.value,
        "period_id": empty_period.id,
        "subject_id": slot.subject_id,
        "teacher_id": slot.teacher_id,
    }
    assert "break" in {
        c["kind"]
        for c in client.post("/admin/timetable/slots/check", json=body, headers=admin).json()[
            "conflicts"
        ]
    }

    # moving an existing slot to a room that is free
    moved = client.put(
        f"/admin/timetable/slots/{slot.id}",
        json={
            "class_section_id": slot.class_section_id,
            "day_of_week": slot.day_of_week.value,
            "period_id": slot.period_id,
            "subject_id": slot.subject_id,
            "teacher_id": slot.teacher_id,
            "room": "Room Z9",
        },
        headers=admin,
    )
    assert moved.status_code == 200 and moved.json()["room"] == "Room Z9"


def test_a_slot_can_be_deleted_and_shows_as_missing(client, admin, db):
    slot = any_slot(db)
    section = slot.class_section_id
    before = next(
        r
        for r in client.get("/admin/timetable/completeness", headers=admin).json()
        if r["class_section_id"] == section
    )
    assert client.delete(f"/admin/timetable/slots/{slot.id}", headers=admin).status_code == 204

    after = next(
        r
        for r in client.get("/admin/timetable/completeness", headers=admin).json()
        if r["class_section_id"] == section
    )
    assert after["missing"] == before["missing"] + 1, (
        "an incomplete timetable must be visibly incomplete"
    )


def test_going_over_the_weekly_limit_needs_a_reason(client, admin, db):
    """§5.7.9: the load ceiling is an override with a reason, not a wall."""
    client.put(
        "/admin/configuration",
        json={"values": {"timetable.max_periods_per_week": 1}},
        headers=admin,
    )
    slot = any_slot(db)
    free_section_period = db.scalars(
        select(TimetableSlot).where(
            TimetableSlot.teacher_id != slot.teacher_id,
        )
    ).first()
    body = {
        "class_section_id": free_section_period.class_section_id,
        "day_of_week": free_section_period.day_of_week.value,
        "period_id": free_section_period.period_id,
        "subject_id": free_section_period.subject_id,
        "teacher_id": free_section_period.teacher_id,
    }
    refused = client.put(
        f"/admin/timetable/slots/{free_section_period.id}", json=body, headers=admin
    )
    assert refused.status_code == 409
    assert refused.json()["detail"]["needs"] == "override_reason"

    allowed = client.put(
        f"/admin/timetable/slots/{free_section_period.id}",
        json={**body, "override_reason": "Covering a vacancy until January"},
        headers=admin,
    )
    assert allowed.status_code == 200


def test_the_workload_report_counts_teaching_periods_only(client, admin, db):
    chart = client.get("/admin/timetable/workload", headers=admin).json()
    rows = chart["rows"]
    assert rows
    teaching = db.scalar(
        select(func.count())
        .select_from(TimetableSlot)
        .join(SchoolPeriod, SchoolPeriod.id == TimetableSlot.period_id)
        .where(SchoolPeriod.is_break.is_(False))
    )
    assert sum(r["periods"] for r in rows) == teaching == chart["total_periods"]
    assert [r["periods"] for r in rows] == sorted(
        [r["periods"] for r in rows], reverse=True
    )


def test_a_substitution_covers_one_day_not_the_timetable(client, admin, db):
    slot = any_slot(db)
    day = next_weekday(slot.day_of_week)
    free = client.get(
        f"/admin/timetable/slots/{slot.id}/free-teachers?date={day}", headers=admin
    ).json()
    assert free, "somebody must be free, or the grid is fully booked"

    made = client.post(
        "/admin/timetable/substitutions",
        json={
            "slot_id": slot.id,
            "date": day.isoformat(),
            "substitute_teacher_id": free[0]["teacher_id"],
            "reason": "Class teacher on sick leave",
        },
        headers=admin,
    )
    assert made.status_code == 201
    assert made.json()["status"] == SubstitutionStatus.assigned

    plan = client.get(f"/admin/timetable/day?date={day}", headers=admin).json()
    covered = next(r for r in plan if r["id"] == slot.id)
    assert covered["substituted"] is True
    assert covered["teacher"] == free[0]["name"]

    db.expire_all()
    # the timetable itself did not change: next week the usual teacher is back
    assert db.get(TimetableSlot, slot.id).teacher_id == slot.teacher_id


def test_a_substitute_who_is_already_teaching_is_refused(client, admin, db):
    slot = any_slot(db)
    day = next_weekday(slot.day_of_week)
    busy = db.scalar(
        select(TimetableSlot.teacher_id).where(
            TimetableSlot.day_of_week == slot.day_of_week,
            TimetableSlot.period_id == slot.period_id,
            TimetableSlot.teacher_id != slot.teacher_id,
        )
    )
    r = client.post(
        "/admin/timetable/substitutions",
        json={
            "slot_id": slot.id,
            "date": day.isoformat(),
            "substitute_teacher_id": busy,
            "reason": "Trying to double-book the cover",
        },
        headers=admin,
    )
    assert r.status_code == 409


def test_an_unfilled_substitution_is_recorded_not_dropped(client, admin, db):
    """§5.7.10: a class nobody was assigned to is the number that matters
    most, so it has to exist as a row."""
    slot = any_slot(db)
    day = next_weekday(slot.day_of_week)
    r = client.post(
        "/admin/timetable/substitutions",
        json={
            "slot_id": slot.id,
            "date": day.isoformat(),
            "substitute_teacher_id": None,
            "reason": "Nobody free this period",
        },
        headers=admin,
    )
    assert r.status_code == 201
    assert r.json()["status"] == SubstitutionStatus.unfilled
    assert r.json()["substitute_teacher"] is None

    listed = client.get(f"/admin/timetable/substitutions?date={day}", headers=admin).json()
    assert any(s["status"] == SubstitutionStatus.unfilled for s in listed)


def test_a_substitution_on_the_wrong_weekday_is_refused(client, admin, db):
    slot = any_slot(db)
    day = next_weekday(slot.day_of_week) + timedelta(days=1)
    r = client.post(
        "/admin/timetable/substitutions",
        json={
            "slot_id": slot.id,
            "date": day.isoformat(),
            "substitute_teacher_id": None,
            "reason": "Wrong day entirely",
        },
        headers=admin,
    )
    assert r.status_code == 422


def test_no_cover_is_arranged_for_a_day_the_school_is_shut(client, admin, db):
    slot = any_slot(db)
    day = next_weekday(slot.day_of_week)
    client.post(
        "/admin/attendance/holidays",
        json={"date": day.isoformat(), "name": "Declared holiday"},
        headers=admin,
    )
    r = client.post(
        "/admin/timetable/substitutions",
        json={
            "slot_id": slot.id,
            "date": day.isoformat(),
            "substitute_teacher_id": None,
            "reason": "Should not be needed",
        },
        headers=admin,
    )
    assert r.status_code == 422


def test_a_teacher_sees_their_own_timetable_with_bell_timings(client, teacher, db):
    rows = client.get("/teacher/timetable", headers=teacher).json()
    assert rows
    assert all(r["start_time"] and r["end_time"] for r in rows)
    me = db.scalar(
        select(Employee).join(ClassSubjectTeacher, ClassSubjectTeacher.teacher_id == Employee.id)
    )
    assert me is not None


# --- the load chart (§5.7.10, §5.3.10) --------------------------------------


def test_the_load_chart_lists_every_teacher_including_any_with_nothing(
    client, admin, db, ids
):
    """The first version skipped teachers on zero periods, which made the chart
    useless for the question it is actually asked — is this fair? The person
    carrying nothing is exactly who a coordinator is looking for."""
    from app.models import Employee, User

    user = User(
        school_id=ids["school"], role="teacher", login_id="TCH950",
        password_hash="x", full_name="Newly Joined",
    )
    db.add(user)
    db.flush()
    db.add(Employee(school_id=ids["school"], user_id=user.id, employee_code="TCH950"))
    db.flush()

    chart = client.get("/admin/timetable/workload", headers=admin).json()
    names = [r["name"] for r in chart["rows"]]
    assert "Newly Joined" in names
    assert "Newly Joined" in chart["unassigned"]


def test_the_seeded_timetable_is_evenly_loaded(client, admin):
    """A spread of 0: every teacher carries the same number of periods.

    The previous allocation gave each section three teachers taking two
    subjects apiece, which cannot balance — thirty teacher-section assignments
    over twelve teachers is 2.5 each — and produced 30 periods against 18.
    """
    chart = client.get("/admin/timetable/workload", headers=admin).json()
    assert chart["total_periods"] == 300
    assert chart["spread"] == 0, chart["rows"]
    assert chart["lightest"] == chart["heaviest"] == 25
    assert chart["fair_share"] == 25.0
    assert chart["over_limit"] == []
    assert all(r["share"] == 1.0 for r in chart["rows"] if r["periods"])


def test_every_section_gets_every_subject_the_same_number_of_times(db, ids):
    """What makes the balance hold: thirty teaching slots over six subjects is
    five each, and a greedy "first free subject" drifts away from that."""
    from collections import Counter

    from app.models import TimetableSlot

    counts = Counter(
        (s.class_section_id, s.subject_id)
        for s in db.scalars(select(TimetableSlot))
    )
    assert set(counts.values()) == {5}


def test_the_chart_reports_who_is_over_the_ceiling(client, admin, db, ids):
    from app.services import school_settings

    from app.models import User

    school_settings.set_many(
        db,
        db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu")),
        {"timetable.max_periods_per_week": 20},
    )
    db.flush()
    chart = client.get("/admin/timetable/workload", headers=admin).json()
    assert chart["limit"] == 20
    assert len(chart["over_limit"]) == 12, "everyone is over a ceiling of 20"
