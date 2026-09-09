"""Enrolment — a student's membership of one class section for one year.

This is the entity ERP_BLUEPRINT §3.2 calls the largest structural fix in the
system. v0 put `class_section_id` and `roll_no` directly on `students`, so
promoting 10-A to 11-A overwrote them and every historical attendance, mark and
invoice row silently re-parented to the new class. There was no way to answer
"which section was this child in last year" or to print a past nominal roll.

Splitting the two apart means promotion *creates* rows instead of destroying
them: the old enrolment stays exactly as it was, marked `promoted`.

    students    — what is true for life  (admission no, name, date of birth)
    enrolments  — what is true for a year (class, section, roll no, outcome)
"""

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import EnrolmentStatus


class Enrolment(TenantBase):
    __tablename__ = "enrolments"
    __table_args__ = (
        # Roll numbers are unique within a section, and sections are already
        # year-scoped, so this is automatically per-year.
        UniqueConstraint("class_section_id", "roll_no", name="uq_enrolment_roll"),
        # A student sits in exactly one section per year. Enforced here rather
        # than in application code, because this is the invariant that keeps the
        # whole history model honest.
        Index(
            "uq_enrolment_student_year",
            "student_id",
            "academic_year_id",
            unique=True,
        ),
        Index("ix_enrolment_section_status", "class_section_id", "status"),
    )

    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False, index=True
    )
    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False, index=True
    )
    roll_no: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[EnrolmentStatus] = enum_col(
        EnrolmentStatus, nullable=False, default=EnrolmentStatus.active
    )
    joined_on: Mapped[date | None] = mapped_column(Date)
    left_on: Mapped[date | None] = mapped_column(Date)
    house: Mapped[str | None] = mapped_column(String(20))

    student = relationship("Student", lazy="joined")
    class_section = relationship("ClassSection", lazy="joined")

    @property
    def is_current(self) -> bool:
        return self.status is EnrolmentStatus.active

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Enrolment student={self.student_id} year={self.academic_year_id}>"
