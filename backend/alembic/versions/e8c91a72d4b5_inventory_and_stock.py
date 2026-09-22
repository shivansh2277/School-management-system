"""inventory and stock management

Adds stock_items and stock_requests tables for tracking laboratory chemicals,
glassware, mathematics kits, art materials, chalks, dusters, and stationery,
as well as low-stock alerts, discrepancy audits, and staff replenishment requests.

Revision ID: e8c91a72d4b5
Revises: c3f61e0a77d2
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8c91a72d4b5"
down_revision: str | None = "c3f61e0a77d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_items",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("location", sa.String(80), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("current_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_quantity", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_critical", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_discrepancy", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("discrepancy_notes", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_stock_items_school_id", "stock_items", ["school_id"])
    op.create_index("ix_stock_items_school_category", "stock_items", ["school_id", "category"])
    op.create_index("ix_stock_items_school_location", "stock_items", ["school_id", "location"])

    op.create_table(
        "stock_requests",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("stock_items.id"), nullable=True),
        sa.Column("item_name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("location", sa.String(80), nullable=False),
        sa.Column("quantity_requested", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("urgency", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("flag_type", sa.String(20), nullable=False, server_default="diminishing"),
        sa.Column("requested_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_by_name", sa.String(120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decided_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_stock_requests_school_id", "stock_requests", ["school_id"])
    op.create_index("ix_stock_requests_item_id", "stock_requests", ["item_id"])
    op.create_index("ix_stock_requests_school_status", "stock_requests", ["school_id", "status"])


def downgrade() -> None:
    op.drop_table("stock_requests")
    op.drop_table("stock_items")
