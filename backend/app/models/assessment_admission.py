"""Applicant assessment and interview (§5.1.5).

Deliberately not the same tables as `exams` and `marks`. Those hang off an
enrolment — a student who exists, in a class, in a year. An applicant has none
of those, and forcing them into the exam model is how the applicant ends up
needing a student record before anyone has decided to admit them.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    AssessmentStatus,
    AssessmentType,
    InterviewRecommendation,
)


class Assessment(TenantBase):
    """One test or observation for one applicant."""

    __tablename__ = "assessments"
    __table_args__ = (Index("ix_assessment_slot", "school_id", "scheduled_at"),)

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False, index=True
    )
    assessment_type: Mapped[AssessmentType] = enum_col(AssessmentType, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    venue: Mapped[str | None] = mapped_column(String(80))
    # Printed on the hall ticket; unique within a slot so two children are not
    # sent to the same desk.
    seat_no: Mapped[str | None] = mapped_column(String(16))

    status: Mapped[AssessmentStatus] = enum_col(
        AssessmentStatus, nullable=False, default=AssessmentStatus.scheduled
    )
    total_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    obtained_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    # Absent is not zero (§5.1.9(8)). A child who did not sit the paper has not
    # scored badly, and averaging the two together is a lie about the cohort.
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    remarks: Mapped[str | None] = mapped_column(Text)

    @property
    def percent(self) -> Decimal | None:
        if self.is_absent or not self.total_marks or self.obtained_marks is None:
            return None
        return (self.obtained_marks / self.total_marks * 100).quantize(Decimal("0.01"))


class AssessmentSubject(TenantBase):
    """Subject-wise marks, for the assessments that have subjects at all."""

    __tablename__ = "assessment_subjects"
    __table_args__ = (
        UniqueConstraint("assessment_id", "subject", name="uq_assessment_subject"),
    )

    assessment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assessments.id"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(60), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    obtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))


class Interview(TenantBase):
    __tablename__ = "interviews"
    __table_args__ = (Index("ix_interview_slot", "school_id", "scheduled_at"),)

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    venue: Mapped[str | None] = mapped_column(String(80))
    # User ids of the panel. A list rather than a join table because a panel is
    # two or three people, read whole, and never queried across interviews.
    panel_member_ids: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[AssessmentStatus] = enum_col(
        AssessmentStatus, nullable=False, default=AssessmentStatus.scheduled
    )

    # {"<user_id>": {"child": 4, "parent": 5, "notes": "...",
    #                "recommendation": "admit", "submitted_at": "..."}}
    # Kept per panel member, because §5.1.9(9) requires each to score
    # independently: nobody sees another's numbers until they have entered
    # their own.
    structured_scores: Mapped[dict | None] = mapped_column(JSON)

    child_rating: Mapped[int | None] = mapped_column()
    parent_rating: Mapped[int | None] = mapped_column()
    recommendation: Mapped[InterviewRecommendation | None] = enum_col(
        InterviewRecommendation
    )
    notes: Mapped[str | None] = mapped_column(Text)
    conducted_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
