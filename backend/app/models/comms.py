"""The outbox, and the evidence that something was actually sent.

ERP_BLUEPRINT §5.9.5 lists nine entities. Four are here, and the five that are
not are deliberate:

* `delivery_receipts` — a receipt is a status transition on the recipient row,
  not a second table, until a provider webhook starts reporting several events
  per recipient. It arrives with the webhook.
* `device_tokens` — push is not a channel in v1 (§0.11 is email only).
* `communication_credits` — nothing to meter. The email tier is free and has
  no per-message cost to budget against; a credits ledger that only ever reads
  zero is a screen that teaches a school to ignore it.
* `parent_queries` — two-way messaging is its own feature with its own inbox,
  and is not what "an outbox with a delivery record" means.
* `notices` — already exists. It gains one nullable column rather than a
  parallel concept beside it.

What is left is the part §5.9.1 actually asks for: the right message, to the
right people, with evidence it was delivered.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    Channel,
    DeliveryStatus,
    MessageCategory,
    MessageStatus,
)


class MessageTemplate(TenantBase):
    """Versioned, so the exact text sent stays reproducible (§5.9.9).

    The same shape `grading_scales` already uses: editing a template does not
    edit history, it supersedes a version. A message records which version it
    was built from, so "what did we actually send that parent in March" has an
    answer in September.
    """

    __tablename__ = "message_templates"
    __table_args__ = (
        UniqueConstraint("school_id", "code", "version", name="uq_message_template_version"),
        # At most one live version per code, the same partial index the fee
        # plans and salary structures use.
        Index(
            "uq_message_template_active",
            "school_id",
            "code",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active"),
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[Channel] = enum_col(Channel, nullable=False, default=Channel.email)
    category: Mapped[MessageCategory] = enum_col(MessageCategory, nullable=False)
    # `{child_name}`-style placeholders. Deliberately not a template engine:
    # see `services/comms.py::render`.
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Message(TenantBase):
    """One send: a body, an audience, and a status.

    `subject` and `body` are snapshotted here rather than left as a pointer to
    the template, because a template edited in June must not rewrite what was
    sent in March. The per-recipient merge values live on the recipient row, so
    the exact text one parent received is those two things composed — rather
    than four hundred near-identical copies of the same paragraph.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_school_status", "school_id", "status"),
    )

    category: Mapped[MessageCategory] = enum_col(MessageCategory, nullable=False)
    channel: Mapped[Channel] = enum_col(Channel, nullable=False, default=Channel.email)

    template_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("message_templates.id")
    )
    template_version: Mapped[int | None] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # What was asked for, kept beside what it resolved to. The recipient rows
    # are the resolution; this is the request, which is what an auditor asking
    # "who did you mean to write to" needs.
    audience: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    status: Mapped[MessageStatus] = enum_col(
        MessageStatus, nullable=False, default=MessageStatus.draft
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    # §5.9.9: a bulk send above the threshold needs a second person. Null on a
    # small send, which needs nobody.
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    recipients = relationship(
        "MessageRecipient", lazy="selectin", cascade="all, delete-orphan",
        back_populates="message",
    )


class MessageRecipient(TenantBase):
    """One person, one address, one delivery outcome.

    Every link to a person is nullable and `to_address` is not, which is the
    whole point: **an applicant is not a user** (CLAUDE.md), and most
    applicants never become one. A recipient model that needed a `users` row
    could not send an admission acknowledgement, which is the first message the
    system ever sends anybody.

    `context` holds this recipient's merge values **and nobody else's**. That
    is the mechanism behind §5.9.9's rule that no family's data may appear in
    another family's message: the render has nothing else to reach for.
    """

    __tablename__ = "message_recipients"
    __table_args__ = (
        Index("ix_message_recipient_status", "message_id", "status"),
    )

    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("messages.id"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    guardian_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("guardians.id"))
    student_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("students.id"))
    application_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("applications.id")
    )

    to_address: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[Channel] = enum_col(Channel, nullable=False, default=Channel.email)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    status: Mapped[DeliveryStatus] = enum_col(
        DeliveryStatus, nullable=False, default=DeliveryStatus.queued
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    # Whatever the provider called it, so a bounce reported later can be
    # matched back to the row that caused it.
    provider_ref: Mapped[str | None] = mapped_column(String(120))

    message = relationship("Message", back_populates="recipients")


class NotificationPreference(TenantBase):
    """One opt-out, per person per category per channel.

    A row means "this person has opted out of this"; no row means they have
    not. Absence as the default is what makes a new category work without a
    backfill — and `MANDATORY_CATEGORIES` means an opt-out row against
    "your child is absent" is written down and then ignored, rather than
    refused at the point somebody ticks the box.
    """

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "category", "channel", name="uq_notification_preference"
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    category: Mapped[MessageCategory] = enum_col(MessageCategory, nullable=False)
    channel: Mapped[Channel] = enum_col(Channel, nullable=False, default=Channel.email)
    opted_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
