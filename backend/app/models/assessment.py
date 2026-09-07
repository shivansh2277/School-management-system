from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class Exam(TenantBase):
    __tablename__ = "exams"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class ExamSchedule(TenantBase):
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


class Mark(TenantBase):
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
    entered_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)


class GradeBand(TenantBase):
    """One row of a grading scale: "91 and above is an A1"."""

    __tablename__ = "grade_bands"
    __table_args__ = (
        UniqueConstraint("grading_scale_id", "grade", name="uq_grade_band_grade"),
        UniqueConstraint("grading_scale_id", "min_percent", name="uq_grade_band_floor"),
        CheckConstraint(
            "min_percent >= 0 AND min_percent <= 100", name="ck_grade_band_percent"
        ),
    )

    grading_scale_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("grading_scales.id"), nullable=False, index=True
    )
    min_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(4), nullable=False)
    # "Outstanding", "Needs improvement" — CBSE prints the word, not the code.
    description: Mapped[str | None] = mapped_column(String(40))

    scale = relationship("GradingScale", lazy="joined")


class GradingScale(TenantBase):
    """A named set of grade bands, versioned.

    §0.8 freezes a published report card by snapshotting the grade *and the
    scale version used*. That is only expressible if the scale is a row a
    publication can point at: with bands hanging directly off the school, an
    edit to a band silently re-graded every card ever issued.

    A school edits bands freely until a card is published against the scale;
    after that the edit becomes a new version, and the old one stays readable
    for the documents that cite it.
    """

    __tablename__ = "grading_scales"
    __table_args__ = (
        UniqueConstraint("school_id", "name", "version", name="uq_grading_scale_version"),
        # One scale in force per school, enforced by the database rather than
        # by whoever remembers to deactivate the previous one.
        Index(
            "uq_grading_scale_active",
            "school_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active"),
        ),
    )

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Set when the first report card cites this version. From then on the bands
    # are history, not configuration.
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
