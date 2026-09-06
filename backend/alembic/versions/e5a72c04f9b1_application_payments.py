"""application and admission fee receipts

Money taken before there is a fee account (§5.1.5). Not invoices: an applicant
has no ledger, and may never have one.

Revision ID: e5a72c04f9b1
Revises: d4f61b8c93e2
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5a72c04f9b1"
down_revision: str | None = "d4f61b8c93e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PURPOSE = sa.Enum(
    "application_fee", "admission_fee",
    name="applicationfeepurpose", native_enum=False,
)
_STATUS = sa.Enum(
    "paid", "voided", "refunded", name="paymentstatus", native_enum=False
)


def upgrade() -> None:
    op.create_table(
        "application_payments",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("purpose", _PURPOSE, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(80)),
        sa.Column("receipt_no", sa.String(24), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("status", _STATUS, nullable=False, server_default="paid"),
        sa.Column("void_reason", sa.Text()),
        sa.Column("idempotency_key", sa.String(120)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("school_id", "receipt_no", name="uq_application_receipt"),
        sa.UniqueConstraint("idempotency_key", name="uq_application_payment_key"),
    )
    op.create_index(
        "ix_application_payments_school_id", "application_payments", ["school_id"]
    )
    op.create_index(
        "ix_application_payment", "application_payments", ["application_id", "purpose"]
    )


def downgrade() -> None:
    op.drop_table("application_payments")
