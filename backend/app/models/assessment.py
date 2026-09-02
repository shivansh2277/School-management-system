from datetime import date, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase


class Exam(TimestampedBase):
    __tablename__ = "exams"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class ExamSchedule(TimestampedBase):
    __tablename__ = "exam_schedule"
    __table_args__ = (
        UniqueConstraint("exam_id", "class_section_id", "subject_id", name="uq_exam_schedule"),
    )

    exam_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exams.id"), nullable=False)
    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class Mark(TimestampedBase):
    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("exam_schedule_id", "student_id", name="uq_mark"),
        CheckConstraint("marks_obtained >= 0", name="ck_marks_non_negative"),
    )

    exam_schedule_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exam_schedule.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    entered_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("teachers.id"), nullable=False)


class GradeBand(TimestampedBase):
    __tablename__ = "grade_bands"

    min_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(4), nullable=False)
