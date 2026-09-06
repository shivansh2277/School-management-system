"""Admission: cycles, seats and the enquiry register (ERP_BLUEPRINT §5.1).

Two things shape every table here.

**The applicant is not a user.** They have no login, no student row, and may
never get one, so nothing in this module may depend on `students` or `users`
(§5.1.2(2)). The links that do exist — a sibling already enrolled, a staff
parent — are nullable, and are claims until somebody verifies them.

**Enquiry is a real stage.** A school takes 800 enquiries to fill 120 seats;
most never become applications, and the funnel is what the module is measured
on. That is why the register carries its own follow-up log rather than a
`notes` column.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    AdmissionCycleStatus,
    EnquiryChannel,
    EnquirySource,
    EnquiryStatus,
)


class AdmissionCycle(TenantBase):
    """One intake season for one academic year.

    A school runs next year's cycle while this year is still in session, which
    is why this hangs off `academic_years` rather than off "the current year".
    """

    __tablename__ = "admission_cycles"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "name", name="uq_admission_cycle"
        ),
    )

    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[AdmissionCycleStatus] = enum_col(
        AdmissionCycleStatus, nullable=False, default=AdmissionCycleStatus.planning
    )
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)

    application_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    late_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    allow_online_applications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    # §5.1.9(15): the refund policy is recorded on the cycle, not decided ad
    # hoc when a parent asks for their money back.
    admission_fee_refund_policy: Mapped[str | None] = mapped_column(Text)

    academic_year = relationship("AcademicYear", lazy="joined")

    @property
    def is_open(self) -> bool:
        return self.status is AdmissionCycleStatus.open


class CycleClassConfig(TenantBase):
    """Seats and rules for one class within one cycle.

    Configured per class rather than per section because next year's sections
    often do not exist yet when applications open (§5.1.6).
    """

    __tablename__ = "cycle_class_config"
    __table_args__ = (
        UniqueConstraint("cycle_id", "class_name", "stream", name="uq_cycle_class"),
    )

    cycle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("admission_cycles.id"), nullable=False, index=True
    )
    class_name: Mapped[str] = mapped_column(String(8), nullable=False)
    stream: Mapped[str | None] = mapped_column(String(20))

    total_seats: Mapped[int] = mapped_column(nullable=False, default=0)
    # {"EWS": 12, "RTE": 10}. Reserved seats are tracked apart so a General
    # admission cannot quietly consume one (§5.1.9(12)).
    reserved_seats: Mapped[dict | None] = mapped_column(JSON)

    # Age is checked against a cut-off date, never against today (§5.1.9(1)).
    age_on: Mapped[date | None] = mapped_column(Date)
    min_age_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    max_age_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))

    requires_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_interview: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # document_type codes: the checklist this class demands, drawn from the
    # same configurable list the rest of the product already uses.
    required_document_codes: Mapped[list | None] = mapped_column(JSON)

    cycle = relationship("AdmissionCycle", lazy="joined")


class Enquiry(TenantBase):
    __tablename__ = "enquiries"
    __table_args__ = (
        Index("ix_enquiry_cycle_status", "cycle_id", "status"),
        Index("ix_enquiry_follow_up", "school_id", "next_follow_up_on"),
    )

    cycle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("admission_cycles.id"), nullable=False
    )
    enquirer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # The only contact detail that is mandatory: a receptionist on the phone
    # has sixty seconds and a mobile number (§5.1.3).
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(160))

    child_name: Mapped[str | None] = mapped_column(String(120))
    child_dob: Mapped[date | None] = mapped_column(Date)
    class_of_interest: Mapped[str | None] = mapped_column(String(8))

    source: Mapped[EnquirySource] = enum_col(
        EnquirySource, nullable=False, default=EnquirySource.walk_in
    )
    status: Mapped[EnquiryStatus] = enum_col(
        EnquiryStatus, nullable=False, default=EnquiryStatus.new
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    next_follow_up_on: Mapped[date | None] = mapped_column(Date)
    # Not a foreign key yet: `applications` arrives in the next migration, and
    # an enquiry is perfectly valid without one.
    converted_application_id: Mapped[int | None] = mapped_column(BigInteger)


class EnquiryInteraction(TenantBase):
    """One logged contact. Append-only in practice: the follow-up history is
    the evidence behind a conversion number."""

    __tablename__ = "enquiry_interactions"

    enquiry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enquiries.id"), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    channel: Mapped[EnquiryChannel] = enum_col(EnquiryChannel, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    # What the conversation changed the enquiry to, recorded on the interaction
    # so the status history is reconstructable from the log alone.
    outcome: Mapped[EnquiryStatus | None] = enum_col(EnquiryStatus)
    by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
