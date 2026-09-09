"""invoices with lines, and allocation-based payments

The second half of the §3.9 rebuild, and a replacement rather than a migration
of the old rows. `fee_payments` carried `UNIQUE (invoice_id)`, so its data
cannot express a part payment or a payment spanning two months — there is no
mapping from the old shape into the new one that is not an invention. Nothing
is deployed and the only fee data that exists is the demo seed, which is
regenerated, so the tables are dropped and rebuilt.

`fee_structures` goes at the same time: `fee_plans` replaced its only reader.

Revision ID: a7c94e26d8b3
Revises: f6b83d15c7a4
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c94e26d8b3"
down_revision: str | None = "f6b83d15c7a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INVOICE_STATUS = sa.Enum(
    "draft",
    "issued",
    "partially_paid",
    "paid",
    "overdue",
    "voided",
    "written_off",
    name="invoicestatus",
    native_enum=False,
)
_PAYMENT_STATUS = sa.Enum(
    "success", "reversed", name="feepaymentstatus", native_enum=False
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
    op.drop_table("fee_payments")
    op.drop_table("fee_invoices")
    op.drop_table("fee_structures")

    op.create_table(
        "fee_invoices",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id",
            sa.BigInteger(),
            sa.ForeignKey("enrolments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("invoice_no", sa.String(24), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", _INVOICE_STATUS, nullable=False),
        sa.Column("settled_on", sa.Date()),
        sa.Column("void_reason", sa.Text()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "invoice_no", name="uq_invoice_no"),
    )
    # Partial: voiding must leave the month reissuable, which a plain unique
    # constraint would forbid.
    op.create_index(
        "uq_invoice_period",
        "fee_invoices",
        ["enrolment_id", "period_year", "period_month"],
        unique=True,
        postgresql_where=sa.text("status <> 'voided'"),
        sqlite_where=sa.text("status <> 'voided'"),
    )
    op.create_index(
        "ix_invoice_school_period",
        "fee_invoices",
        ["school_id", "period_year", "period_month"],
    )

    op.create_table(
        "fee_invoice_lines",
        _pk(),
        _tenant(),
        sa.Column(
            "invoice_id",
            sa.BigInteger(),
            sa.ForeignKey("fee_invoices.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "fee_head_id", sa.BigInteger(), sa.ForeignKey("fee_heads.id"), nullable=False
        ),
        sa.Column("description", sa.String(80), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        *_stamps(),
        sa.CheckConstraint("amount >= 0 AND discount >= 0", name="ck_invoice_line_amounts"),
        sa.CheckConstraint("discount <= amount", name="ck_invoice_line_discount"),
    )

    op.create_table(
        "fee_payments",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id",
            sa.BigInteger(),
            sa.ForeignKey("enrolments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("receipt_no", sa.String(24), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("instrument_ref", sa.String(40)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("status", _PAYMENT_STATUS, nullable=False),
        sa.Column("reverses_payment_id", sa.BigInteger(), sa.ForeignKey("fee_payments.id")),
        sa.Column("reason", sa.Text()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "receipt_no", name="uq_payment_receipt_no"),
        sa.UniqueConstraint("school_id", "idempotency_key", name="uq_payment_idempotency"),
        sa.CheckConstraint("amount <> 0", name="ck_payment_amount_nonzero"),
    )

    op.create_table(
        "payment_allocations",
        _pk(),
        _tenant(),
        sa.Column(
            "payment_id",
            sa.BigInteger(),
            sa.ForeignKey("fee_payments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "invoice_line_id",
            sa.BigInteger(),
            sa.ForeignKey("fee_invoice_lines.id"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        *_stamps(),
    )
    op.create_index("ix_allocation_line", "payment_allocations", ["invoice_line_id"])


def downgrade() -> None:
    op.drop_table("payment_allocations")
    op.drop_table("fee_payments")
    op.drop_table("fee_invoice_lines")
    op.drop_index("ix_invoice_school_period", table_name="fee_invoices")
    op.drop_index("uq_invoice_period", table_name="fee_invoices")
    op.drop_table("fee_invoices")

    op.create_table(
        "fee_structures",
        _pk(),
        _tenant(),
        sa.Column("class_name", sa.String(8), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(10, 2), nullable=False),
        *_stamps(),
        sa.UniqueConstraint("school_id", "class_name", name="uq_fee_structure_class"),
    )
    op.create_table(
        "fee_invoices",
        _pk(),
        _tenant(),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "paid", "overdue", name="invoicestatus", native_enum=False),
            nullable=False,
        ),
        *_stamps(),
        sa.UniqueConstraint("student_id", "month", "year", name="uq_invoice_period"),
    )
    op.create_table(
        "fee_payments",
        _pk(),
        _tenant(),
        sa.Column(
            "invoice_id",
            sa.BigInteger(),
            sa.ForeignKey("fee_invoices.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("txn_ref", sa.String(40), nullable=False),
        sa.Column("receipt_no", sa.String(24), nullable=False),
        *_stamps(),
        sa.UniqueConstraint("school_id", "receipt_no", name="uq_payment_receipt_no"),
    )
