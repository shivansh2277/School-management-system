"""Decisions, offers and the waitlist (§5.1.5).

The three tables that make an admission defensible. A decision without a
recorded reason, an offer without an expiry, or a waitlist that is not an
ordered queue are each the failure the blueprint calls out by name.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import DecisionOutcome, OfferStatus, WaitlistStatus


class AdmissionDecision(TenantBase):
    """Append-only. A reversal is a new row, not an edit of the old one — the
    history of who decided what, and why, is the whole point (§5.1.9(13))."""

    __tablename__ = "admission_decisions"
    __table_args__ = (Index("ix_decision_application", "application_id", "decided_at"),)

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False
    )
    decision: Mapped[DecisionOutcome] = enum_col(DecisionOutcome, nullable=False)
    decided_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Not nullable, and that is deliberate: §5.1.9(13) requires a reason for
    # every decision including the admits, because that is what makes the
    # process defensible when it is challenged.
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # Which pool the seat came out of. A General admission may not consume a
    # reserved seat (§5.1.9(12)).
    seat_category: Mapped[str | None] = mapped_column(String(20))
    conditions: Mapped[str | None] = mapped_column(Text)
    # §5.1.9(11): admitting beyond capacity is possible, never accidental.
    over_allocation_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class AdmissionOffer(TenantBase):
    __tablename__ = "admission_offers"
    __table_args__ = (Index("ix_offer_expiry", "school_id", "status", "expires_on"),)

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False, index=True
    )
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Not nullable: an offer without an expiry is a seat held forever, and the
    # waitlist behind it never moves (§5.1.9(14)).
    expires_on: Mapped[date] = mapped_column(Date, nullable=False)
    offer_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    status: Mapped[OfferStatus] = enum_col(
        OfferStatus, nullable=False, default=OfferStatus.issued
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the seat went back into the pool, whether by expiry or by decline.
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WaitlistEntry(TenantBase):
    """An ordered queue per class, not a label on an application.

    Rank is explicit rather than derived from a score, because the order is
    what the school promised the parent and it must not silently reshuffle when
    somebody's marks are corrected.
    """

    __tablename__ = "waitlist_entries"
    __table_args__ = (
        UniqueConstraint("cycle_id", "class_name", "rank", name="uq_waitlist_rank"),
        UniqueConstraint("application_id", name="uq_waitlist_application"),
        Index("ix_waitlist_queue", "cycle_id", "class_name", "status", "rank"),
    )

    cycle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("admission_cycles.id"), nullable=False
    )
    class_name: Mapped[str] = mapped_column(String(8), nullable=False)
    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[WaitlistStatus] = enum_col(
        WaitlistStatus, nullable=False, default=WaitlistStatus.waiting
    )
