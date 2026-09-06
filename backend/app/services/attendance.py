from datetime import date as Date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Attendance, AttendanceStatus, Enrolment, Student, User
from app.schemas.common import (
    AttendanceDay,
    AttendanceMarkRequest,
    AttendanceMonth,
    AttendanceSummary,
    RollRow,
)
from app.services import scoping
from app.services.common import roster


def summarise(counts: dict[AttendanceStatus, int]) -> AttendanceSummary:
    present = counts.get(AttendanceStatus.present, 0)
    absent = counts.get(AttendanceStatus.absent, 0)
    leave = counts.get(AttendanceStatus.leave, 0)
    total = present + absent + leave
    # Leave counts against presence (BLUEPRINT §8). No marks at all -> no percentage.
    percent = round(present / total * 100, 1) if total else None
    return AttendanceSummary(present=present, absent=absent, leave=leave, percent=percent)


def _counts(db: Session, where) -> dict[AttendanceStatus, int]:
    rows = db.execute(
        select(Attendance.status, func.count()).where(*where).group_by(Attendance.status)
    ).all()
    return {status_: n for status_, n in rows}


def roll_sheet(db: Session, class_section_id: int, day: Date) -> list[RollRow]:
    marked = {
        a.student_id: a
        for a in db.scalars(
            select(Attendance)
            .join(Enrolment, Enrolment.student_id == Attendance.student_id)
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
            status=marked[e.student_id].status if e.student_id in marked else None,
            remarks=marked[e.student_id].remarks if e.student_id in marked else None,
        )
        for e in roster(db, class_section_id)
    ]


def mark(db: Session, user: User, body: AttendanceMarkRequest) -> list[RollRow]:
    scoping.assert_teaches_section(db, user, body.class_section_id)
    if body.date > Date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot mark attendance for a future date")

    teacher = scoping.teacher_for(db, user)
    section_students = {e.student_id for e in roster(db, body.class_section_id)}
    existing = {
        a.student_id: a
        for a in db.scalars(
            select(Attendance).where(
                Attendance.student_id.in_(section_students), Attendance.date == body.date
            )
        )
    }
    for entry in body.entries:
        if entry.student_id not in section_students:
            raise scoping.forbidden("Student is not in this class section")
        row = existing.get(entry.student_id)
        if row is None:  # upsert on (student_id, date) — D2
            db.add(
                Attendance(
                    school_id=teacher.school_id,
                    student_id=entry.student_id,
                    date=body.date,
                    status=entry.status,
                    marked_by=teacher.id,
                    remarks=entry.remarks,
                )
            )
        else:
            row.status = entry.status
            row.remarks = entry.remarks
            row.marked_by = teacher.id
    db.commit()
    return roll_sheet(db, body.class_section_id, body.date)


def student_month(db: Session, student_id: int, month: int, year: int) -> AttendanceMonth:
    rows = db.scalars(
        select(Attendance)
        .where(
            Attendance.student_id == student_id,
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
        summary=summarise(counts),
    )


def student_percent(db: Session, student_id: int) -> float | None:
    return summarise(_counts(db, [Attendance.student_id == student_id])).percent


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
            Attendance.student_id.in_(
                select(Enrolment.student_id).where(
                    Enrolment.class_section_id == class_section_id
                )
            )
        )
    if date_from:
        where.append(Attendance.date >= date_from)
    if date_to:
        where.append(Attendance.date <= date_to)
    return summarise(_counts(db, where))
