"""admission cycles, seat configuration and the enquiry register

The first tables of Part 2 (ERP_BLUEPRINT §5.1.5). Nothing here references
`students` or `users` except optionally: an enquirer is not a user and may
never become one.

Revision ID: a1c93f7b62d4
Revises: 9b58e3d2c0f6
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c93f7b62d4"
down_revision: str | None = "9b58e3d2c0f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CYCLE_STATUS = sa.Enum(
    "planning", "open", "closed", "archived",
    name="admissioncyclestatus", native_enum=False,
)
_ENQUIRY_STATUS = sa.Enum(
    "new", "contacted", "interested", "application_form_issued", "converted",
    "not_interested", "lost_to_competitor", "invalid",
    name="enquirystatus", native_enum=False,
)
_SOURCE = sa.Enum(
    "walk_in", "phone", "website", "referral", "alumni", "hoarding",
    "digital_ad", "other",
    name="enquirysource", native_enum=False,
)
_CHANNEL = sa.Enum(
    "phone", "visit", "email", "whatsapp", "sms",
    name="enquirychannel", native_enum=False,
)


def _ts():
    return [
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "admission_cycles",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("status", _CYCLE_STATUS, nullable=False, server_default="planning"),
        sa.Column("starts_on", sa.Date()),
        sa.Column("ends_on", sa.Date()),
        sa.Column("application_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("late_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column(
            "allow_online_applications", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("admission_fee_refund_policy", sa.Text()),
        *_ts(),
        sa.UniqueConstraint("school_id", "academic_year_id", "name", name="uq_admission_cycle"),
    )
    op.create_index("ix_admission_cycles_school_id", "admission_cycles", ["school_id"])
    op.create_index(
        "ix_admission_cycles_academic_year_id", "admission_cycles", ["academic_year_id"]
    )

    op.create_table(
        "cycle_class_config",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "cycle_id", sa.BigInteger(), sa.ForeignKey("admission_cycles.id"), nullable=False
        ),
        sa.Column("class_name", sa.String(8), nullable=False),
        sa.Column("stream", sa.String(20)),
        sa.Column("total_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_seats", sa.JSON()),
        sa.Column("age_on", sa.Date()),
        sa.Column("min_age_years", sa.Numeric(4, 2)),
        sa.Column("max_age_years", sa.Numeric(4, 2)),
        sa.Column("requires_test", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_interview", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("required_document_codes", sa.JSON()),
        *_ts(),
        sa.UniqueConstraint("cycle_id", "class_name", "stream", name="uq_cycle_class"),
    )
    op.create_index("ix_cycle_class_config_school_id", "cycle_class_config", ["school_id"])
    op.create_index("ix_cycle_class_config_cycle_id", "cycle_class_config", ["cycle_id"])

    op.create_table(
        "enquiries",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "cycle_id", sa.BigInteger(), sa.ForeignKey("admission_cycles.id"), nullable=False
        ),
        sa.Column("enquirer_name", sa.String(120), nullable=False),
        sa.Column("mobile", sa.String(20), nullable=False),
        sa.Column("email", sa.String(160)),
        sa.Column("child_name", sa.String(120)),
        sa.Column("child_dob", sa.Date()),
        sa.Column("class_of_interest", sa.String(8)),
        sa.Column("source", _SOURCE, nullable=False, server_default="walk_in"),
        sa.Column("status", _ENQUIRY_STATUS, nullable=False, server_default="new"),
        sa.Column("assigned_to", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("next_follow_up_on", sa.Date()),
        sa.Column("converted_application_id", sa.BigInteger()),
        *_ts(),
    )
    op.create_index("ix_enquiries_school_id", "enquiries", ["school_id"])
    op.create_index("ix_enquiry_cycle_status", "enquiries", ["cycle_id", "status"])
    op.create_index("ix_enquiry_follow_up", "enquiries", ["school_id", "next_follow_up_on"])

    op.create_table(
        "enquiry_interactions",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("enquiry_id", sa.BigInteger(), sa.ForeignKey("enquiries.id"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", _CHANNEL, nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("outcome", _ENQUIRY_STATUS),
        sa.Column("by_user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        *_ts(),
    )
    op.create_index(
        "ix_enquiry_interactions_school_id", "enquiry_interactions", ["school_id"]
    )
    op.create_index(
        "ix_enquiry_interactions_enquiry_id", "enquiry_interactions", ["enquiry_id"]
    )


def downgrade() -> None:
    op.drop_table("enquiry_interactions")
    op.drop_table("enquiries")
    op.drop_table("cycle_class_config")
    op.drop_table("admission_cycles")
