"""add public announcements fields to notices table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-29
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("notices")]

    if "category" not in cols:
        op.add_column(
            "notices",
            sa.Column("category", sa.String(50), nullable=False, server_default="General"),
        )
    if "is_public" not in cols:
        op.add_column(
            "notices",
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if "is_pinned" not in cols:
        op.add_column(
            "notices",
            sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if "summary" not in cols:
        op.add_column(
            "notices",
            sa.Column("summary", sa.String(300), nullable=True),
        )
    if "expiry_date" not in cols:
        op.add_column(
            "notices",
            sa.Column("expiry_date", sa.Date(), nullable=True),
        )
    if "attachment_url" not in cols:
        op.add_column(
            "notices",
            sa.Column("attachment_url", sa.String(255), nullable=True),
        )

    indexes = [ix["name"] for ix in insp.get_indexes("notices")]
    if "ix_notices_is_public" not in indexes:
        op.create_index("ix_notices_is_public", "notices", ["is_public"])
    if "ix_notices_category" not in indexes:
        op.create_index("ix_notices_category", "notices", ["category"])


def downgrade() -> None:
    op.drop_index("ix_notices_category", table_name="notices")
    op.drop_index("ix_notices_is_public", table_name="notices")
    op.drop_column("notices", "attachment_url")
    op.drop_column("notices", "expiry_date")
    op.drop_column("notices", "summary")
    op.drop_column("notices", "is_pinned")
    op.drop_column("notices", "is_public")
    op.drop_column("notices", "category")
