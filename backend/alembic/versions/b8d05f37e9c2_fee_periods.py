"""fee periods, so a month's books can be closed

Checkpoint 3 (§12) requires that a closed period refuses further writes. Absent
means open — a school should not have to open January before billing it — so
this table holds only the months someone has actually acted on.

Revision ID: b8d05f37e9c2
Revises: a7c94e26d8b3
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d05f37e9c2"
down_revision: str | None = "a7c94e26d8b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUS = sa.Enum("open", "closed", name="feeperiodstatus", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "fee_periods",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "school_id",
            sa.BigInteger(),
            sa.ForeignKey("schools.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("status", _STATUS, nullable=False),
        sa.Column("closed_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text()),
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
        sa.UniqueConstraint("school_id", "period_year", "period_month", name="uq_fee_period"),
    )


def downgrade() -> None:
    op.drop_table("fee_periods")
