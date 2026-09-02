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
    ClassSection,
    FeeInvoice,
    FeePayment,
    Student,
    Teacher,
    TimetableSlot,
    User,
)
from app.services import assessment, attendance
from app.services.common import section_labels, subject_names

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", None]

BUCKETS = [
    ("excellent", 80.0),
    ("good", 60.0),
    ("average", 40.0),
    ("needs_improvement", 0.0),
]


def totals(db: Session, academic_year: str) -> dict:
    students = db.scalar(
        select(func.count()).select_from(Student).join(User, User.id == Student.user_id).where(User.is_active)
    )
    teachers = db.scalar(
        select(func.count()).select_from(Teacher).join(User, User.id == Teacher.user_id).where(User.is_active)
    )
    classes = db.scalar(
        select(func.count()).select_from(ClassSection).where(
            ClassSection.academic_year == academic_year
        )
    )
    fees = db.scalar(
        select(func.coalesce(func.sum(FeePayment.amount), 0))
        .join(FeeInvoice, FeeInvoice.id == FeePayment.invoice_id)
        .where(FeeInvoice.year.in_(_academic_years(academic_year)))
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


def performance(db: Session, class_section_id: int | None = None) -> dict:
    exam = assessment.latest_exam_with_marks(db, class_section_id)
    counts = {name: 0 for name, _ in BUCKETS}
    if exam is None:
        return counts
    q = select(Student)
    if class_section_id is not None:
        q = q.where(Student.class_section_id == class_section_id)
    for s in db.scalars(q):
        pct = assessment.student_average_percent(db, s.id, exam.id)
        if pct is None:
            continue
        for name, floor in BUCKETS:
            if pct >= floor:
                counts[name] += 1
                break
    return counts


def top_performers(db: Session, limit: int = 3) -> list[dict]:
    exam = assessment.latest_exam_with_marks(db)
    if exam is None:
        return []
    labels = section_labels(db)
    scored = []
    for s in db.scalars(select(Student)):
        pct = assessment.student_average_percent(db, s.id, exam.id)
        if pct is not None:
            scored.append(
                {
                    "student_id": s.id,
                    "name": s.user.full_name,
                    "class_label": labels.get(s.class_section_id, ""),
                    "average_percent": pct,
                }
            )
    scored.sort(key=lambda r: r["average_percent"], reverse=True)
    return scored[:limit]


def today_schedule(
    db: Session,
    class_section_ids: list[int] | None = None,
    teacher_id: int | None = None,
) -> list[dict]:
    key = DAY_KEYS[Date.today().weekday()]
    if key is None:  # Sunday
        return []
    q = select(TimetableSlot).where(TimetableSlot.day_of_week == key)
    if class_section_ids is not None:
        q = q.where(TimetableSlot.class_section_id.in_(class_section_ids))
    if teacher_id is not None:
        # A teacher is scoped to a whole section, but only takes some of its
        # periods. Filtering by section alone would show a colleague's class as
        # if it were theirs.
        q = q.where(TimetableSlot.teacher_id == teacher_id)
    labels = section_labels(db)
    subjects = subject_names(db)
    teachers = {t.id: t.user.full_name for t in db.scalars(select(Teacher))}
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


def fee_trend(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            FeeInvoice.year,
            FeeInvoice.month,
            func.sum(FeePayment.amount),
        )
        .join(FeePayment, FeePayment.invoice_id == FeeInvoice.id)
        .group_by(FeeInvoice.year, FeeInvoice.month)
        .order_by(FeeInvoice.year, FeeInvoice.month)
    ).all()
    # only months that have collections; no zero-filled placeholder points
    return [{"month": f"{y}-{m:02d}", "collected": Decimal(v)} for y, m, v in rows]


def month_attendance(db: Session, class_section_id: int | None = None) -> dict:
    today = Date.today()
    first = today.replace(day=1)
    summary = attendance.section_summary(db, class_section_id, first, today)
    return summary.model_dump()
