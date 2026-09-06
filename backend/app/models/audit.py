"""Audit log and number sequences.

v0's TimestampedBase gave `created_at` and `updated_at` and nothing else: marks
could be edited, invoice status mutated, students deactivated and settings
PATCHed, and none of it left a trace of who or why. For a system holding
children's academic and financial records that is the most serious governance
gap in the codebase (ERP_BLUEPRINT §3.6).
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import AuditAction


class AuditLog(TenantBase):
    """Append-only. No update path, no delete path, never truncated.

    Written by services rather than by database triggers, because the actor is
    an application concept. A direct SQL edit therefore bypasses this — accepted,
    and mitigated by not handing out production database access.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor_time", "actor_user_id", "occurred_at"),
        Index("ix_audit_school_time", "school_id", "occurred_at"),
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    actor_label: Mapped[str | None] = mapped_column(String(120))

    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[AuditAction] = enum_col(AuditAction, nullable=False)

    # Only the fields that changed, not whole rows: a diff is what anyone
    # reading this actually wants, and whole rows would store a lot of noise.
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)

    # Required for the actions where "what happened" is less useful than "why":
    # voiding an invoice, changing a published mark, striking off a student.
    reason: Mapped[str | None] = mapped_column(Text)

    academic_year_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("academic_years.id")
    )
    ip: Mapped[str | None] = mapped_column(String(45))


class NumberSequence(TenantBase):
    """A gapless counter per school, per type, per year.

    v0 computed the next receipt number as `max(seq) + 1` in Python with no
    lock, so two concurrent payments raced and the unique constraint turned the
    loser into a 500 rather than a retry. Financial document numbers must also
    be gapless — an auditor asks about gaps — which rules out a database
    sequence, since those skip on rollback.
    """

    __tablename__ = "number_sequences"
    __table_args__ = (
        UniqueConstraint("school_id", "kind", "year", name="uq_sequence_period"),
    )

    kind: Mapped[str] = mapped_column(String(24), nullable=False)  # admission, receipt…
    year: Mapped[int] = mapped_column(nullable=False)
    prefix: Mapped[str | None] = mapped_column(String(24))
    width: Mapped[int] = mapped_column(nullable=False, default=6)
    next_value: Mapped[int] = mapped_column(nullable=False, default=1)
