"""Dashboard aggregates. Every figure here is a live query.

BLUEPRINT §0: if a statistic cannot be computed from real data the response
omits it (null) rather than inventing one. Trend series carry only periods that
actually have data.
"""

from datetime import date as Date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ClassSection,
    ExamSchedule,
    FeeInvoice,
    FeePayment,
    Mark,
    Student,
    Teacher,
    TimetableSlot,
    User,
)
from app.services import assessment, attendance
from app.services.common import class_label_map, section_labels, subject_names

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", None]

BUCKETS = [
    ("excellent", 80.0),
    ("good", 60.0),
    ("average", 40.0),
    ("needs_improvement", 0.0),
]


def totals(db: Session, year: AcademicYear) -> dict:
    school_id = year.school_id
    students = db.scalar(
        select(func.count())
        .select_from(Student)
        .join(User, User.id == Student.user_id)
        .where(Student.school_id == school_id, User.is_active)
    )
    teachers = db.scalar(
        select(func.count())
        .select_from(Teacher)
        .join(User, User.id == Teacher.user_id)
        .where(Teacher.school_id == school_id, User.is_active)
    )
    classes = db.scalar(
        select(func.count())
        .select_from(ClassSection)
        .where(ClassSection.academic_year_id == year.id)
    )
    fees = db.scalar(
        select(func.coalesce(func.sum(FeePayment.amount), 0))
        .join(FeeInvoice, FeeInvoice.id == FeePayment.invoice_id)
        .where(
            FeeInvoice.school_id == school_id,
            FeeInvoice.year.in_(_academic_years(year.code)),
        )
    )
    return {
        "students": students,
        "teachers": teachers,
        "classes": classes,
        "fees_collected": Decimal(fees),
    }


def _academic_years(academic_year: str) -> list[int]:
    """'2025-26' -> [2025, 2026]."""
    start = int(academic_year.split("-")[0])
    return [start, start + 1]


def exam_percentages(
    db: Session, exam_id: int, class_section_id: int | None = None
) -> dict[int, float]:
    """Every student's overall percentage in one exam, as a single aggregate query.

    Building this per student through `report_card()` meant one round trip per
    student per subject, which was imperceptible against a local database and
    took 8.5 s against a hosted one. The arithmetic is identical: a subject with
    no `marks` row contributes to neither the numerator nor the denominator, so
    an absent subject stays excluded from the total rather than counting as zero.
    """
    q = (
        select(
            Mark.student_id,
            func.sum(Mark.marks_obtained),
            func.sum(ExamSchedule.max_marks),
        )
        .join(ExamSchedule, ExamSchedule.id == Mark.exam_schedule_id)
        .where(ExamSchedule.exam_id == exam_id)
        .group_by(Mark.student_id)
    )
    if class_section_id is not None:
        q = q.where(ExamSchedule.class_section_id == class_section_id)
    return {
        student_id: round(float(obtained) / float(out_of) * 100, 1)
        for student_id, obtained, out_of in db.execute(q).all()
        if out_of
    }


def performance(
    db: Session, school_id: int, class_section_id: int | None = None
) -> dict:
    exam = assessment.latest_exam_with_marks(db, school_id, class_section_id)
    counts = {name: 0 for name, _ in BUCKETS}
    if exam is None:
        return counts
    for pct in exam_percentages(db, exam.id, class_section_id).values():
        for name, floor in BUCKETS:
            if pct >= floor:
                counts[name] += 1
                break
    return counts


def top_performers(db: Session, school_id: int, limit: int = 3) -> list[dict]:
    exam = assessment.latest_exam_with_marks(db, school_id)
    if exam is None:
        return []
    percentages = exam_percentages(db, exam.id)
    if not percentages:
        return []
    labels = section_labels(db)
    students = {
        s.id: s
        for s in db.scalars(
            select(Student).where(
                Student.school_id == school_id, Student.id.in_(percentages)
            )
        )
    }
    sections = class_label_map(db, list(percentages))
    scored = [
        {
            "student_id": sid,
            "name": students[sid].user.full_name,
            "class_label": sections.get(sid, ""),
            "average_percent": pct,
        }
        for sid, pct in percentages.items()
        if sid in students
    ]
    scored.sort(key=lambda r: r["average_percent"], reverse=True)
    return scored[:limit]


def today_schedule(
    db: Session,
    school_id: int,
    class_section_ids: list[int] | None = None,
    teacher_id: int | None = None,
) -> list[dict]:
    key = DAY_KEYS[Date.today().weekday()]
    if key is None:  # Sunday
        return []
    q = select(TimetableSlot).where(
        TimetableSlot.school_id == school_id, TimetableSlot.day_of_week == key
    )
    if class_section_ids is not None:
        q = q.where(TimetableSlot.class_section_id.in_(class_section_ids))
    if teacher_id is not None:
        # A teacher is scoped to a whole section, but only takes some of its
        # periods. Filtering by section alone would show a colleague's class as
        # if it were theirs.
        q = q.where(TimetableSlot.teacher_id == teacher_id)
    labels = section_labels(db)
    subjects = subject_names(db)
    teachers = {
        t.id: t.user.full_name
        for t in db.scalars(select(Teacher).where(Teacher.school_id == school_id))
    }
    return [
        {
            "period": slot.period_no,
            "time": f"{slot.start_time:%H:%M}-{slot.end_time:%H:%M}",
            "class_label": labels.get(slot.class_section_id, ""),
            "subject": subjects.get(slot.subject_id, ""),
            "teacher": teachers.get(slot.teacher_id, ""),
            "room": slot.room,
        }
        for slot in db.scalars(q.order_by(TimetableSlot.period_no))
    ]


def fee_trend(db: Session, school_id: int) -> list[dict]:
    rows = db.execute(
        select(
            FeeInvoice.year,
            FeeInvoice.month,
            func.sum(FeePayment.amount),
        )
        .join(FeePayment, FeePayment.invoice_id == FeeInvoice.id)
        .where(FeeInvoice.school_id == school_id)
        .group_by(FeeInvoice.year, FeeInvoice.month)
        .order_by(FeeInvoice.year, FeeInvoice.month)
    ).all()
    # only months that have collections; no zero-filled placeholder points
    return [{"month": f"{y}-{m:02d}", "collected": Decimal(v)} for y, m, v in rows]


def month_attendance(
    db: Session, school_id: int, class_section_id: int | None = None
) -> dict:
    today = Date.today()
    first = today.replace(day=1)
    summary = attendance.section_summary(db, school_id, class_section_id, first, today)
    return summary.model_dump()
