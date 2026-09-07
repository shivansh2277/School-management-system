"""Marking, correcting and counting attendance.

Two things here are easy to get wrong and expensive to get wrong.

**The denominator.** A percentage over "days someone happened to mark" flatters
a section nobody marks and punishes a child who joined in November. It is
computed over *working days* — Sundays and holidays removed — from the day the
child joined. §5.8.9 calls this the most common attendance-reporting bug.

**Correction versus marking.** Changing today's roll is fixing a typo. Changing
last week's is altering a record the school may later rely on to say where a
child was, so it takes a reason and lands in the audit log.
"""

from datetime import UTC, date as Date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Attendance,
    AttendanceStatus,
    AuditAction,
    Enrolment,
    EnrolmentStatus,
    Holiday,
    Student,
    User,
)
from app.schemas.common import (
    AttendanceDay,
    AttendanceMarkRequest,
    AttendanceMonth,
    AttendanceSummary,
    RollRow,
)
from app.services import audit, scoping
from app.services.common import roster

# What each mark is worth when counting attendance. Late is still a child in
# the room; leave and excused are absences the school agreed to, and are
# reported separately rather than quietly counted as presence.
CREDIT = {
    AttendanceStatus.present: 1.0,
    AttendanceStatus.late: 1.0,
    AttendanceStatus.half_day: 0.5,
}
SUNDAY = 6


def holidays_between(db: Session, school_id: int, start: Date, end: Date) -> set[Date]:
    return set(
        db.scalars(
            select(Holiday.date).where(
                Holiday.school_id == school_id,
                Holiday.date >= start,
                Holiday.date <= end,
            )
        )
    )


def is_working_day(day: Date, holidays: set[Date]) -> bool:
    return day.weekday() != SUNDAY and day not in holidays


def working_days(db: Session, school_id: int, start: Date, end: Date) -> int:
    """School days in a range: six-day week, minus declared holidays."""
    if end < start:
        return 0
    holidays = holidays_between(db, school_id, start, end)
    days = (end - start).days + 1
    return sum(
        1 for n in range(days) if is_working_day(start + timedelta(days=n), holidays)
    )


def summarise(
    counts: dict[AttendanceStatus, int], denominator: int | None = None
) -> AttendanceSummary:
    """Turn a tally into the numbers a report shows.

    `denominator` is the working days the child could have attended. Without
    one, the marks themselves are the denominator — honest only for a range
    where everything was marked, which is why every caller that can compute
    working days passes them.
    """
    present = counts.get(AttendanceStatus.present, 0)
    late = counts.get(AttendanceStatus.late, 0)
    half = counts.get(AttendanceStatus.half_day, 0)
    absent = counts.get(AttendanceStatus.absent, 0)
    leave = counts.get(AttendanceStatus.leave, 0) + counts.get(AttendanceStatus.excused, 0)

    credited = present + late + half * 0.5
    total = denominator if denominator is not None else sum(counts.values())
    percent = round(credited / total * 100, 1) if total else None
    return AttendanceSummary(
        present=present + late,
        absent=absent,
        leave=leave,
        percent=percent,
    )


def _counts(db: Session, where) -> dict[AttendanceStatus, int]:
    rows = db.execute(
        select(Attendance.status, func.count()).where(*where).group_by(Attendance.status)
    ).all()
    return {status_: n for status_, n in rows}


def enrolment_of(db: Session, student_id: int) -> Enrolment | None:
    """The current enrolment. The API speaks in students because that is what
    a parent and the mobile app know; the table is keyed by enrolment."""
    return db.scalar(
        select(Enrolment)
        .where(Enrolment.student_id == student_id, Enrolment.status == EnrolmentStatus.active)
        .order_by(Enrolment.academic_year_id.desc())
    )


def roll_sheet(db: Session, class_section_id: int, day: Date) -> list[RollRow]:
    marked = {
        a.enrolment_id: a
        for a in db.scalars(
            select(Attendance)
            .join(Enrolment, Enrolment.id == Attendance.enrolment_id)
            .where(
                Enrolment.class_section_id == class_section_id,
                Attendance.date == day,
            )
        )
    }
    return [
        RollRow(
            student_id=e.student_id,
            full_name=e.student.user.full_name,
            roll_no=e.roll_no,
            status=marked[e.id].status if e.id in marked else None,
            remarks=marked[e.id].remarks if e.id in marked else None,
            corrected=e.id in marked and marked[e.id].corrected_at is not None,
        )
        for e in roster(db, class_section_id)
    ]


def mark(db: Session, user: User, body: AttendanceMarkRequest) -> list[RollRow]:
    """Mark or correct a section's roll for one day.

    Changing a mark for an earlier day is a *correction*: §5.8.9 requires a
    reason, and it is audited. Same-day changes are not — a class teacher
    fixing a tap while the register is still open is not amending a record.
    """
    scoping.assert_teaches_section(db, user, body.class_section_id)
    today = Date.today()
    if body.date > today:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot mark attendance for a future date")

    teacher = scoping.employee_for(db, user)
    holidays = holidays_between(db, teacher.school_id, body.date, body.date)
    if not is_working_day(body.date, holidays):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "That day is not a working day for this school",
        )

    by_student = {e.student_id: e for e in roster(db, body.class_section_id)}
    existing = {
        a.enrolment_id: a
        for a in db.scalars(
            select(Attendance).where(
                Attendance.enrolment_id.in_([e.id for e in by_student.values()] or [0]),
                Attendance.date == body.date,
            )
        )
    }
    now = datetime.now(UTC)
    for entry in body.entries:
        enrolment = by_student.get(entry.student_id)
        if enrolment is None:
            raise scoping.forbidden("Student is not in this class section")
        row = existing.get(enrolment.id)
        if row is None:  # idempotent upsert on (enrolment, date)
            db.add(
                Attendance(
                    school_id=teacher.school_id,
                    enrolment_id=enrolment.id,
                    date=body.date,
                    status=entry.status,
                    marked_by=teacher.id,
                    remarks=entry.remarks,
                )
            )
            continue
        if row.status == entry.status and row.remarks == entry.remarks:
            continue  # resubmitting the same roster changes nothing
        if body.date < today:
            if not (body.reason and body.reason.strip()):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Correcting attendance for an earlier day requires a reason",
                )
            audit.record(
                db,
                actor=user,
                school_id=teacher.school_id,
                entity_type="attendance",
                entity_id=row.id,
                action=AuditAction.status_change,
                before={"status": row.status.value, "date": str(row.date)},
                after={"status": entry.status.value, "date": str(row.date)},
                reason=body.reason,
            )
            row.corrected_by = teacher.id
            row.corrected_at = now
        row.status = entry.status
        row.remarks = entry.remarks
        row.marked_by = teacher.id
    db.commit()
    return roll_sheet(db, body.class_section_id, body.date)


def absentees(db: Session, school_id: int, day: Date, class_section_id: int | None = None):
    """Who is not in school today, with someone to ring (§5.8.3)."""
    from app.services.fees import primary_contact

    q = (
        select(Attendance)
        .join(Enrolment, Enrolment.id == Attendance.enrolment_id)
        .where(
            Attendance.school_id == school_id,
            Attendance.date == day,
            Attendance.status.in_(
                (AttendanceStatus.absent, AttendanceStatus.leave, AttendanceStatus.excused)
            ),
        )
    )
    if class_section_id is not None:
        q = q.where(Enrolment.class_section_id == class_section_id)
    out = []
    for row in db.scalars(q):
        student = row.enrolment.student
        out.append(
            {
                "student_id": student.id,
                "full_name": student.user.full_name,
                "admission_no": student.admission_no,
                "roll_no": row.enrolment.roll_no,
                "class_label": row.enrolment.class_section.label,
                "status": row.status,
                "remarks": row.remarks,
                # Approved leave is not an absence to chase, and a list that
                # mixes them wastes the office's morning.
                "expected": row.status is not AttendanceStatus.absent,
                "contact": primary_contact(db, student.id),
            }
        )
    return sorted(out, key=lambda r: (r["class_label"], r["roll_no"]))


def student_month(db: Session, student_id: int, month: int, year: int) -> AttendanceMonth:
    enrolment = enrolment_of(db, student_id)
    if enrolment is None:
        return AttendanceMonth(days=[], summary=summarise({}))
    rows = db.scalars(
        select(Attendance)
        .where(
            Attendance.enrolment_id == enrolment.id,
            func.extract("month", Attendance.date) == month,
            func.extract("year", Attendance.date) == year,
        )
        .order_by(Attendance.date)
    ).all()
    counts: dict[AttendanceStatus, int] = {}
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
    return AttendanceMonth(
        days=[AttendanceDay(date=r.date, status=r.status) for r in rows],
        summary=summarise(counts, _denominator_for(db, enrolment, month, year)),
    )


def _denominator_for(db: Session, enrolment: Enrolment, month: int, year: int) -> int:
    """Working days this child could have attended in that month.

    Bounded by the day they joined and the day they left, so a student admitted
    in November is not measured against September.
    """
    first = Date(year, month, 1)
    last = Date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)
    start = max(first, enrolment.joined_on or first)
    end = min(last, enrolment.left_on or last, Date.today())
    return working_days(db, enrolment.school_id, start, end)


def student_percent(db: Session, student_id: int) -> float | None:
    """Attendance to date, over working days since the child joined."""
    enrolment = enrolment_of(db, student_id)
    if enrolment is None:
        return None
    counts = _counts(db, [Attendance.enrolment_id == enrolment.id])
    if not counts:
        return None
    marked = db.execute(
        select(func.min(Attendance.date), func.max(Attendance.date)).where(
            Attendance.enrolment_id == enrolment.id
        )
    ).one()
    start = max(marked[0], enrolment.joined_on or marked[0])
    end = min(marked[1], enrolment.left_on or marked[1])
    return summarise(counts, working_days(db, enrolment.school_id, start, end)).percent


def section_summary(
    db: Session,
    school_id: int,
    class_section_id: int | None = None,
    date_from: Date | None = None,
    date_to: Date | None = None,
) -> AttendanceSummary:
    where = [Attendance.school_id == school_id]
    if class_section_id is not None:
        where.append(
            Attendance.enrolment_id.in_(
                select(Enrolment.id).where(Enrolment.class_section_id == class_section_id)
            )
        )
    if date_from:
        where.append(Attendance.date >= date_from)
    if date_to:
        where.append(Attendance.date <= date_to)
    counts = _counts(db, where)
    if date_from and date_to and class_section_id is not None:
        heads = db.scalar(
            select(func.count())
            .select_from(Enrolment)
            .where(
                Enrolment.class_section_id == class_section_id,
                Enrolment.status == EnrolmentStatus.active,
            )
        )
        denominator = heads * working_days(db, school_id, date_from, date_to)
        return summarise(counts, denominator or None)
    return summarise(counts)


def shortage(
    db: Session, school_id: int, threshold: float = 75.0, class_section_id: int | None = None
) -> list[dict]:
    """Children below the attendance threshold, worst first.

    §5.8.10 wants this "early enough to act" — the value is in seeing it in
    November, not in the week before the exam.
    """
    q = select(Enrolment).where(
        Enrolment.school_id == school_id, Enrolment.status == EnrolmentStatus.active
    )
    if class_section_id is not None:
        q = q.where(Enrolment.class_section_id == class_section_id)
    out = []
    for enrolment in db.scalars(q):
        percent = student_percent(db, enrolment.student_id)
        if percent is None or percent >= threshold:
            continue
        student = db.get(Student, enrolment.student_id)
        out.append(
            {
                "student_id": student.id,
                "full_name": student.user.full_name,
                "admission_no": student.admission_no,
                "class_label": enrolment.class_section.label,
                "percent": percent,
            }
        )
    return sorted(out, key=lambda r: r["percent"])
