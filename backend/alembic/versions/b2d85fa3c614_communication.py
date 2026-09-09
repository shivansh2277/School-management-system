"""communication: templates, the outbox, delivery records and opt-outs

Four tables where ERP_BLUEPRINT §5.9.5 lists nine. `delivery_receipts` is a
status transition on the recipient row until a provider webhook reports several
events per recipient; `device_tokens` needs push, which is not a v1 channel;
`communication_credits` would meter a free email tier and always read zero;
`parent_queries` is two-way messaging, which is a different feature. `notices`
already exists and gains one nullable column rather than a parallel concept.

`messages.subject`/`body` are a snapshot rather than a pointer at the template:
a template edited in June must not rewrite what was sent in March. The
per-recipient merge values sit on the recipient row instead, so the exact text
one parent received is those two composed rather than four hundred copies of
the same paragraph.

Every person link on `message_recipients` is nullable and `to_address` is not.
That is the applicant rule of CLAUDE.md in the schema: an applicant is not a
user and most never become one, and a recipient model needing a `users` row
could not send an admission acknowledgement — the first message the system
ever sends anybody.

Revision ID: b2d85fa3c614
Revises: a1c74e92b5d3
Create Date: 2026-09-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d85fa3c614"
down_revision: str | None = "a1c74e92b5d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHANNEL = sa.Enum("email", "sms", "whatsapp", name="channel", native_enum=False)
_CATEGORY = sa.Enum(
    "emergency", "attendance", "fees", "examination", "transport", "admission",
    "hr", "general",
    name="messagecategory", native_enum=False,
)
_MESSAGE = sa.Enum(
    "draft", "scheduled", "sending", "completed", "failed", "cancelled",
    name="messagestatus", native_enum=False,
)
_DELIVERY = sa.Enum(
    "queued", "sent", "failed", "opted_out", name="deliverystatus", native_enum=False,
)


def _pk() -> sa.Column:
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        primary_key=True,
    )


def _stamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
        nullable=False, index=True,
    )


def upgrade() -> None:
    op.create_table(
        "message_templates",
        _pk(), _tenant(),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("channel", _CHANNEL, nullable=False, server_default="email"),
        sa.Column("category", _CATEGORY, nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint(
            "school_id", "code", "version", name="uq_message_template_version"
        ),
    )
    op.create_index(
        "uq_message_template_active",
        "message_templates",
        ["school_id", "code"],
        unique=True,
        postgresql_where=sa.text("is_active"),
        sqlite_where=sa.text("is_active"),
    )

    op.create_table(
        "messages",
        _pk(), _tenant(),
        sa.Column("category", _CATEGORY, nullable=False),
        sa.Column("channel", _CHANNEL, nullable=False, server_default="email"),
        sa.Column(
            "template_id", sa.BigInteger(), sa.ForeignKey("message_templates.id")
        ),
        sa.Column("template_version", sa.Integer()),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("audience", sa.JSON(), nullable=False),
        sa.Column("status", _MESSAGE, nullable=False, server_default="draft"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("approved_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        *_stamps(),
    )
    op.create_index("ix_message_school_status", "messages", ["school_id", "status"])

    op.create_table(
        "message_recipients",
        _pk(), _tenant(),
        sa.Column(
            "message_id", sa.BigInteger(), sa.ForeignKey("messages.id"),
            nullable=False, index=True,
        ),
        # All four nullable on purpose: see the module docstring.
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("guardian_id", sa.BigInteger(), sa.ForeignKey("guardians.id")),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id")),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("applications.id")),
        sa.Column("to_address", sa.String(200), nullable=False),
        sa.Column("channel", _CHANNEL, nullable=False, server_default="email"),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("status", _DELIVERY, nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("provider_ref", sa.String(120)),
        *_stamps(),
    )
    op.create_index(
        "ix_message_recipient_status", "message_recipients", ["message_id", "status"]
    )

    op.create_table(
        "notification_preferences",
        _pk(), _tenant(),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id"),
            nullable=False, index=True,
        ),
        sa.Column("category", _CATEGORY, nullable=False),
        sa.Column("channel", _CHANNEL, nullable=False, server_default="email"),
        sa.Column("opted_out", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint(
            "user_id", "category", "channel", name="uq_notification_preference"
        ),
    )

    # `notices` becomes the board entry that a message can have been sent for,
    # rather than a second concept beside the outbox. Batch mode because SQLite
    # rebuilds the table to add a foreign key — and §4 of the handoff records
    # what a rebuild once cost, so the Postgres side is checked afterwards
    # rather than assumed.
    with op.batch_alter_table("notices") as batch:
        batch.add_column(sa.Column("message_id", sa.BigInteger()))
        batch.create_foreign_key(
            "fk_notice_message", "messages", ["message_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("notices") as batch:
        batch.drop_constraint("fk_notice_message", type_="foreignkey")
        batch.drop_column("message_id")
    op.drop_table("notification_preferences")
    op.drop_index("ix_message_recipient_status", table_name="message_recipients")
    op.drop_table("message_recipients")
    op.drop_index("ix_message_school_status", table_name="messages")
    op.drop_table("messages")
    op.drop_index("uq_message_template_active", table_name="message_templates")
    op.drop_table("message_templates")
