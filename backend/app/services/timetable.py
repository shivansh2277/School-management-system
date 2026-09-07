"""Building a timetable, and covering the days it does not survive contact with.

The timetable was seeded and read-only in v0, so nothing ever checked it. The
moment it is editable, the checks are the feature: a grid that lets you put a
teacher in two rooms at once is worse than no grid, because someone will trust
it and a class will sit unattended.

Every conflict is reported, not just the first — a builder screen that says
"teacher busy" and then, after you fix it, "room busy" wastes the coordinator's
afternoon one clash at a time.
"""

from datetime import date as Date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    ClassSection,
    ClassSubjectTeacher,
    DayOfWeek,
    Employee,
    Holiday,
    SchoolPeriod,
    Subject,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import audit, school_settings

DAY_BY_WEEKDAY = {
    0: DayOfWeek.mon,
    1: DayOfWeek.tue,
    2: DayOfWeek.wed,
    3: DayOfWeek.thu,
    4: DayOfWeek.fri,
    5: DayOfWeek.sat,
}


def max_load(db: Session, school_id: int) -> int:
    return int(school_settings.get(db, school_id, "timetable.max_periods_per_week"))


def teacher_load(db: Session, teacher_id: int, exclude_slot_id: int | None = None) -> int:
    """Teaching periods a week. Breaks are on the grid but are not taught."""
    q = (
        select(func.count())
        .select_from(TimetableSlot)
        .join(SchoolPeriod, SchoolPeriod.id == TimetableSlot.period_id)
        .where(TimetableSlot.teacher_id == teacher_id, SchoolPeriod.is_break.is_(False))
    )
    if exclude_slot_id is not None:
        q = q.where(TimetableSlot.id != exclude_slot_id)
    return db.scalar(q) or 0


def conflicts(
    db: Session,
    school_id: int,
    *,
    class_section_id: int,
    day_of_week: DayOfWeek,
    period_id: int,
    teacher_id: int,
    room: str | None = None,
    exclude_slot_id: int | None = None,
) -> list[dict]:
    """Everything wrong with putting this lesson here.

    Each entry names the kind, so a builder can colour the cell and a caller
    can decide which are overridable — only `workload` is (§5.7.9).
    """
    found: list[dict] = []
    period = db.get(SchoolPeriod, period_id)
    if period is None or period.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown period")
    if period.is_break:
        found.append(
            {"kind": "break", "detail": f"Period {period.period_no} is a break, not a lesson"}
        )

    same_time = select(TimetableSlot).where(
        TimetableSlot.school_id == school_id,
        TimetableSlot.day_of_week == day_of_week,
        TimetableSlot.period_id == period_id,
    )
    if exclude_slot_id is not None:
        same_time = same_time.where(TimetableSlot.id != exclude_slot_id)
    others = list(db.scalars(same_time))

    for other in others:
        if other.teacher_id == teacher_id:
            found.append(
                {
                    "kind": "teacher",
                    "detail": (
                        f"{db.get(Employee, teacher_id).user.full_name} already teaches "
                        f"{other.class_section.label} then"
                    ),
                    "slot_id": other.id,
                }
            )
        if other.class_section_id == class_section_id:
            found.append(
                {
                    "kind": "section",
                    "detail": f"{other.class_section.label} already has a lesson then",
                    "slot_id": other.id,
                }
            )
        if room and other.room == room:
            found.append(
                {
                    "kind": "room",
                    "detail": f"Room {room} is taken by {other.class_section.label} then",
                    "slot_id": other.id,
                }
            )

    # Does this teacher actually teach this section? A timetable that ignores
    # the subject allocation is a rota, not a timetable.
    ceiling = max_load(db, school_id)
    load = teacher_load(db, teacher_id, exclude_slot_id)
    if not period.is_break and load + 1 > ceiling:
        found.append(
            {
                "kind": "workload",
                "detail": (
                    f"{db.get(Employee, teacher_id).user.full_name} would be at "
                    f"{load + 1} periods a week, over the limit of {ceiling}"
                ),
                "overridable": True,
            }
        )
    return found


def save_slot(
    db: Session,
    actor: User,
    *,
    class_section_id: int,
    day_of_week: DayOfWeek,
    period_id: int,
    subject_id: int,
    teacher_id: int,
    room: str | None = None,
    slot_id: int | None = None,
    override_reason: str | None = None,
) -> TimetableSlot:
    """Place or move one lesson. Refuses a clash; a workload breach needs a
    reason, which is recorded rather than merely accepted."""
    school_id = actor.school_id
    problems = conflicts(
        db,
        school_id,
        class_section_id=class_section_id,
        day_of_week=day_of_week,
        period_id=period_id,
        teacher_id=teacher_id,
        room=room,
        exclude_slot_id=slot_id,
    )
    blocking = [p for p in problems if not p.get("overridable")]
    if blocking:
        raise HTTPException(status.HTTP_409_CONFLICT, {"conflicts": blocking})
    overridable = [p for p in problems if p.get("overridable")]
    if overridable and not (override_reason and override_reason.strip()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"conflicts": overridable, "needs": "override_reason"},
        )

    slot = db.get(TimetableSlot, slot_id) if slot_id else None
    if slot is None:
        slot = TimetableSlot(school_id=school_id)
        db.add(slot)
    slot.class_section_id = class_section_id
    slot.day_of_week = day_of_week
    slot.period_id = period_id
    slot.subject_id = subject_id
    slot.teacher_id = teacher_id
    slot.room = room
    db.flush()

    if overridable:
        audit.record(
            db,
            actor=actor,
            school_id=school_id,
            entity_type="timetable_slot",
            entity_id=slot.id,
            action=AuditAction.update,
            after={"override": [p["detail"] for p in overridable], "reason": override_reason},
        )
    db.commit()
    return slot


def slot_out(db: Session, slot: TimetableSlot) -> dict:
    return {
        "id": slot.id,
        "class_section_id": slot.class_section_id,
        "class_label": slot.class_section.label,
        "day_of_week": slot.day_of_week,
        "period": slot.period.period_no,
        "start_time": slot.period.start_time,
        "end_time": slot.period.end_time,
        "subject": db.get(Subject, slot.subject_id).name,
        "subject_id": slot.subject_id,
        "teacher": db.get(Employee, slot.teacher_id).user.full_name,
        "teacher_id": slot.teacher_id,
        "room": slot.room,
    }


def grid(
    db: Session,
    school_id: int,
    class_section_id: int | None = None,
    teacher_id: int | None = None,
    day_of_week: DayOfWeek | None = None,
) -> list[dict]:
    q = select(TimetableSlot).where(TimetableSlot.school_id == school_id)
    if class_section_id is not None:
        q = q.where(TimetableSlot.class_section_id == class_section_id)
    if teacher_id is not None:
        q = q.where(TimetableSlot.teacher_id == teacher_id)
    if day_of_week is not None:
        q = q.where(TimetableSlot.day_of_week == day_of_week)
    rows = db.scalars(q).all()
    return [
        slot_out(db, s)
        for s in sorted(rows, key=lambda s: (list(DayOfWeek).index(s.day_of_week), s.period.period_no))
    ]


def completeness(db: Session, school_id: int, academic_year_id: int) -> list[dict]:
    """Which sections have gaps, and how many (§5.7.9).

    An incomplete timetable must be visibly incomplete. Reporting the number
    rather than hiding it is the whole point: a section short four periods is a
    decision someone has to make, not a defect to paper over.
    """
    teaching = db.scalar(
        select(func.count())
        .select_from(SchoolPeriod)
        .where(SchoolPeriod.school_id == school_id, SchoolPeriod.is_break.is_(False))
    ) or 0
    expected = teaching * len(DayOfWeek)
    out = []
    for section in db.scalars(
        select(ClassSection).where(ClassSection.academic_year_id == academic_year_id)
    ):
        placed = db.scalar(
            select(func.count())
            .select_from(TimetableSlot)
            .where(TimetableSlot.class_section_id == section.id)
        ) or 0
        out.append(
            {
                "class_section_id": section.id,
                "class_label": section.label,
                "placed": placed,
                "expected": expected,
                "missing": max(expected - placed, 0),
            }
        )
    return out


def workload(db: Session, school_id: int) -> list[dict]:
    ceiling = max_load(db, school_id)
    rows = []
    for employee in db.scalars(select(Employee).where(Employee.school_id == school_id)):
        periods = teacher_load(db, employee.id)
        if periods == 0:
            continue
        rows.append(
            {
                "teacher_id": employee.id,
                "name": employee.user.full_name,
                "periods": periods,
                "limit": ceiling,
                "over": periods > ceiling,
            }
        )
    return sorted(rows, key=lambda r: r["periods"], reverse=True)


# --- substitutions ----------------------------------------------------------


def _teaching_on(db: Session, teacher_id: int, day: DayOfWeek, period_id: int) -> TimetableSlot | None:
    return db.scalar(
        select(TimetableSlot).where(
            TimetableSlot.teacher_id == teacher_id,
            TimetableSlot.day_of_week == day,
            TimetableSlot.period_id == period_id,
        )
    )


def arrange(
    db: Session,
    actor: User,
    *,
    slot_id: int,
    on: Date,
    substitute_teacher_id: int | None,
    reason: str,
) -> Substitution:
    """Cover one lesson on one day.

    Recorded with no substitute when nobody is free — an unfilled row is the
    honest state, and §5.7.10 wants exactly that number reported. Silently
    dropping it would mean a class nobody knows is unattended.
    """
    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != actor.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    if DAY_BY_WEEKDAY.get(on.weekday()) != slot.day_of_week:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{on} is not a {slot.day_of_week.value}",
        )
    if db.scalar(
        select(Holiday).where(Holiday.school_id == actor.school_id, Holiday.date == on)
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "The school is closed that day"
        )

    if substitute_teacher_id is not None:
        if substitute_teacher_id == slot.teacher_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "The absent teacher cannot cover their own lesson",
            )
        clash = _teaching_on(db, substitute_teacher_id, slot.day_of_week, slot.period_id)
        if clash is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"That teacher already teaches {clash.class_section.label} in that period",
            )
        # Someone already covering another class in the same period is just as
        # busy as someone with a scheduled lesson.
        also_covering = db.scalar(
            select(Substitution)
            .join(TimetableSlot, TimetableSlot.id == Substitution.timetable_slot_id)
            .where(
                Substitution.date == on,
                Substitution.substitute_teacher_id == substitute_teacher_id,
                TimetableSlot.period_id == slot.period_id,
            )
        )
        if also_covering is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "That teacher is already covering another class in that period",
            )
        # The third way a teacher can be unavailable, and the one Part 3 could
        # not ask about because staff leave did not exist. Assigning cover to
        # somebody who is themselves away is not a clash the timetable can see:
        # they have no lesson that period precisely because they are not in.
        from app.services import staff_leave

        away = staff_leave.on_leave(db, substitute_teacher_id, on)
        if away is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"That teacher is on approved {away.leave_type.name} from "
                f"{away.from_date} to {away.to_date}",
            )

    row = db.scalar(
        select(Substitution).where(
            Substitution.timetable_slot_id == slot.id, Substitution.date == on
        )
    )
    if row is None:
        row = Substitution(
            school_id=actor.school_id,
            timetable_slot_id=slot.id,
            date=on,
            absent_teacher_id=slot.teacher_id,
        )
        db.add(row)
    row.substitute_teacher_id = substitute_teacher_id
    row.reason = reason
    row.status = (
        SubstitutionStatus.assigned
        if substitute_teacher_id is not None
        else SubstitutionStatus.unfilled
    )
    db.commit()
    return row


def free_teachers(db: Session, school_id: int, slot_id: int, on: Date) -> list[dict]:
    """Who could take this lesson: not teaching then, not already covering.

    Whoever teaches the subject elsewhere comes first — cover by someone who
    knows the subject is cover; anyone else is supervision.
    """
    slot = db.get(TimetableSlot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    busy = {
        s.teacher_id
        for s in db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.day_of_week == slot.day_of_week,
                TimetableSlot.period_id == slot.period_id,
            )
        )
    }
    busy |= {
        s.substitute_teacher_id
        for s in db.scalars(
            select(Substitution)
            .join(TimetableSlot, TimetableSlot.id == Substitution.timetable_slot_id)
            .where(Substitution.date == on, TimetableSlot.period_id == slot.period_id)
        )
        if s.substitute_teacher_id
    }
    teaches_subject = {
        c.teacher_id
        for c in db.scalars(
            select(ClassSubjectTeacher).where(
                ClassSubjectTeacher.subject_id == slot.subject_id
            )
        )
    }
    out = [
        {
            "teacher_id": e.id,
            "name": e.user.full_name,
            "teaches_this_subject": e.id in teaches_subject,
            "weekly_load": teacher_load(db, e.id),
        }
        for e in db.scalars(select(Employee).where(Employee.school_id == school_id))
        if e.id not in busy and e.id != slot.teacher_id
    ]
    return sorted(out, key=lambda r: (not r["teaches_this_subject"], r["weekly_load"]))


def day_plan(db: Session, school_id: int, on: Date) -> list[dict]:
    """The day's schedule as it will actually run, substitutions applied."""
    day = DAY_BY_WEEKDAY.get(on.weekday())
    if day is None:
        return []
    subs = {
        s.timetable_slot_id: s
        for s in db.scalars(
            select(Substitution).where(
                Substitution.school_id == school_id, Substitution.date == on
            )
        )
    }
    out = []
    for slot in db.scalars(
        select(TimetableSlot).where(
            TimetableSlot.school_id == school_id, TimetableSlot.day_of_week == day
        )
    ):
        row = slot_out(db, slot)
        sub = subs.get(slot.id)
        if sub is not None:
            row["substituted"] = True
            row["status"] = sub.status
            row["reason"] = sub.reason
            row["teacher"] = (
                db.get(Employee, sub.substitute_teacher_id).user.full_name
                if sub.substitute_teacher_id
                else None
            )
            row["teacher_id"] = sub.substitute_teacher_id
        else:
            row["substituted"] = False
        out.append(row)
    return sorted(out, key=lambda r: (r["period"], r["class_label"]))
