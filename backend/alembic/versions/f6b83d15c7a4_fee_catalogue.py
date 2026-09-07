"""fee heads, plans, assignments and concessions

The first half of the §3.9 fee rebuild. `fee_structures` — one flat monthly
amount per class, with nowhere to put a transport charge or a discount — stays
in place until the invoice rebuild that follows replaces its only reader.

Revision ID: f6b83d15c7a4
Revises: e5a72c04f9b1
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6b83d15c7a4"
down_revision: str | None = "e5a72c04f9b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HEAD_TYPE = sa.Enum(
    "recurring", "one_time", "optional", name="feeheadtype", native_enum=False
)
_FREQUENCY = sa.Enum("monthly", "one_time", name="feefrequency", native_enum=False)
_CONCESSION_TYPE = sa.Enum(
    "sibling",
    "staff_ward",
    "rte",
    "management",
    "scholarship",
    "other",
    name="concessiontype",
    native_enum=False,
)
_CONCESSION_STATUS = sa.Enum(
    "requested",
    "approved",
    "rejected",
    "expired",
    name="concessionstatus",
    native_enum=False,
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
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True
    )


def upgrade() -> None:
    op.create_table(
        "fee_heads",
        _pk(),
        _tenant(),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("type", _HEAD_TYPE, nullable=False),
        sa.Column("is_refundable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("gl_code", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "code", name="uq_fee_head_code"),
    )

    op.create_table(
        "fee_plans",
        _pk(),
        _tenant(),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("class_name", sa.String(8)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint("academic_year_id", "name", name="uq_fee_plan_name"),
    )
    # Partial: a plan with no class is an individual plan, and a year may hold
    # any number of those.
    op.create_index(
        "uq_fee_plan_class",
        "fee_plans",
        ["academic_year_id", "class_name"],
        unique=True,
        postgresql_where=sa.text("class_name IS NOT NULL"),
        sqlite_where=sa.text("class_name IS NOT NULL"),
    )

    op.create_table(
        "fee_plan_items",
        _pk(),
        _tenant(),
        sa.Column(
            "fee_plan_id",
            sa.BigInteger(),
            sa.ForeignKey("fee_plans.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "fee_head_id", sa.BigInteger(), sa.ForeignKey("fee_heads.id"), nullable=False
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("frequency", _FREQUENCY, nullable=False),
        *_stamps(),
        sa.UniqueConstraint("fee_plan_id", "fee_head_id", name="uq_fee_plan_item"),
        sa.CheckConstraint("amount >= 0", name="ck_fee_plan_item_amount"),
    )

    op.create_table(
        "student_fee_plans",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"), nullable=False
        ),
        sa.Column(
            "fee_plan_id", sa.BigInteger(), sa.ForeignKey("fee_plans.id"), nullable=False
        ),
        sa.Column("assigned_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        *_stamps(),
        sa.UniqueConstraint("enrolment_id", name="uq_student_fee_plan"),
    )

    op.create_table(
        "fee_concessions",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id",
            sa.BigInteger(),
            sa.ForeignKey("enrolments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", _CONCESSION_TYPE, nullable=False),
        sa.Column("fee_head_id", sa.BigInteger(), sa.ForeignKey("fee_heads.id")),
        sa.Column("percent", sa.Numeric(5, 2)),
        sa.Column("amount", sa.Numeric(10, 2)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", _CONCESSION_STATUS, nullable=False),
        sa.Column("requested_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("approved_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
        *_stamps(),
        sa.CheckConstraint(
            "(percent IS NULL) <> (amount IS NULL)", name="ck_concession_percent_xor_amount"
        ),
    )
    # Re-running the sibling sweep must not stack a second 10% on the same
    # child; the constraint is what makes that safe rather than careful code.
    op.create_index(
        "uq_concession_live",
        "fee_concessions",
        ["enrolment_id", "type"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
        sqlite_where=sa.text("status = 'approved'"),
    )


def downgrade() -> None:
    op.drop_index("uq_concession_live", table_name="fee_concessions")
    op.drop_table("fee_concessions")
    op.drop_table("student_fee_plans")
    op.drop_table("fee_plan_items")
    op.drop_index("uq_fee_plan_class", table_name="fee_plans")
    op.drop_table("fee_plans")
    op.drop_table("fee_heads")
