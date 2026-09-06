from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Enrolment, Exam, ExamSchedule, Mark, Student, User
from app.schemas.common import (
    ExamScheduleOut,
    MarksRequest,
    MarksRosterRow,
    ReportCard,
    ReportCardRow,
)
from app.services import scoping
from app.services.common import (
    current_enrolment,
    grade_for,
    require_current_enrolment,
    roster,
    section_labels,
    subject_names,
)


def schedule_out(db: Session, rows: list[ExamSchedule]) -> list[ExamScheduleOut]:
    labels = section_labels(db)
    subjects = subject_names(db)
    exams = {e.id: e.name for e in db.scalars(select(Exam))}
    with_marks = set(
        db.scalars(
            select(Mark.exam_schedule_id).where(
                Mark.exam_schedule_id.in_([r.id for r in rows] or [0])
            )
        )
    )
    return [
        ExamScheduleOut(
            id=r.id,
            exam_id=r.exam_id,
            exam_name=exams.get(r.exam_id, ""),
            class_section_id=r.class_section_id,
            class_label=labels.get(r.class_section_id, ""),
            subject_id=r.subject_id,
            subject=subjects.get(r.subject_id, ""),
            exam_date=r.exam_date,
            start_time=r.start_time,
            max_marks=r.max_marks,
            marks_entered=r.id in with_marks,
        )
        for r in rows
    ]


def _owned_schedule(db: Session, user: User, exam_schedule_id: int) -> ExamSchedule:
    sched = db.get(ExamSchedule, exam_schedule_id)
    if sched is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam paper not found")
    scoping.assert_teaches_subject_in_section(db, user, sched.class_section_id, sched.subject_id)
    return sched


def marks_roster(db: Session, user: User, exam_schedule_id: int) -> list[MarksRosterRow]:
    sched = _owned_schedule(db, user, exam_schedule_id)
    existing = {
        m.student_id: m.marks_obtained
        for m in db.scalars(select(Mark).where(Mark.exam_schedule_id == sched.id))
    }
    return [
        MarksRosterRow(
            student_id=e.student_id,
            full_name=e.student.user.full_name,
            roll_no=e.roll_no,
            marks_obtained=existing.get(e.student_id),
        )
        for e in roster(db, sched.class_section_id)
    ]


def enter_marks(db: Session, user: User, body: MarksRequest) -> list[MarksRosterRow]:
    sched = _owned_schedule(db, user, body.exam_schedule_id)
    teacher = scoping.employee_for(db, user)
    students = {e.student_id: e.student for e in roster(db, sched.class_section_id)}
    existing = {
        m.student_id: m
        for m in db.scalars(select(Mark).where(Mark.exam_schedule_id == sched.id))
    }
    for entry in body.entries:
        student = students.get(entry.student_id)
        if student is None:
            raise scoping.forbidden("Student is not in this class section")
        if entry.marks_obtained < 0 or entry.marks_obtained > sched.max_marks:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{student.user.full_name}: marks must be between 0 and {sched.max_marks}",
            )
        row = existing.get(entry.student_id)
        if row is None:
            db.add(
                Mark(
                    school_id=teacher.school_id,
                    exam_schedule_id=sched.id,
                    student_id=entry.student_id,
                    marks_obtained=entry.marks_obtained,
                    entered_by=teacher.id,
                )
            )
        else:
            row.marks_obtained = entry.marks_obtained
            row.entered_by = teacher.id
    db.commit()
    return marks_roster(db, user, sched.id)


def report_card(db: Session, student_id: int, exam_id: int) -> ReportCard:
    student = db.get(Student, student_id)
    exam = db.get(Exam, exam_id)
    if student is None or exam is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam or student not found")
    enrolment = require_current_enrolment(db, student.id)
    schedules = list(
        db.scalars(
            select(ExamSchedule).where(
                ExamSchedule.exam_id == exam_id,
                ExamSchedule.class_section_id == enrolment.class_section_id,
            )
        )
    )
    marks = {
        m.exam_schedule_id: m.marks_obtained
        for m in db.scalars(
            select(Mark).where(
                Mark.student_id == student_id,
                Mark.exam_schedule_id.in_([s.id for s in schedules] or [0]),
            )
        )
    }
    subjects = subject_names(db)
    rows, total_obtained, total_max = [], Decimal(0), Decimal(0)
    for sched in sorted(schedules, key=lambda s: s.exam_date):
        obtained = marks.get(sched.id)
        percent = None
        if obtained is not None:
            # An absent subject has no marks row; it is excluded from the
            # totals rather than counted as zero (BLUEPRINT §8).
            total_obtained += obtained
            total_max += sched.max_marks
            percent = round(float(obtained) / float(sched.max_marks) * 100, 1)
        rows.append(
            ReportCardRow(
                subject=subjects.get(sched.subject_id, ""),
                marks_obtained=obtained,
                max_marks=sched.max_marks,
                percent=percent,
                grade=grade_for(db, percent),
            )
        )
    overall = round(float(total_obtained) / float(total_max) * 100, 1) if total_max else None
    return ReportCard(
        exam_id=exam.id,
        exam_name=exam.name,
        student_id=student.id,
        student_name=student.user.full_name,
        class_label=enrolment.class_section.label,
        rows=rows,
        total_obtained=total_obtained,
        total_max=total_max,
        overall_percent=overall,
        overall_grade=grade_for(db, overall),
    )


def latest_exam_with_marks(
    db: Session, school_id: int, class_section_id: int | None = None
) -> Exam | None:
    q = (
        select(Exam)
        .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
        .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
        .where(Exam.school_id == school_id)
    )
    if class_section_id is not None:
        q = q.where(ExamSchedule.class_section_id == class_section_id)
    return db.scalars(q.order_by(Exam.end_date.desc()).limit(1)).first()


def student_average_percent(db: Session, student_id: int, exam_id: int) -> float | None:
    return report_card(db, student_id, exam_id).overall_percent
