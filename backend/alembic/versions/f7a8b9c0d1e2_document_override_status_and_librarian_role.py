"""document override status, rejection_reason, and librarian role

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-10-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("application_document_overrides"):
        cols = [c["name"] for c in insp.get_columns("application_document_overrides")]
        with op.batch_alter_table("application_document_overrides") as batch_op:
            if "status" not in cols:
                batch_op.add_column(
                    sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'"))
                )
            if "rejection_reason" not in cols:
                batch_op.add_column(
                    sa.Column("rejection_reason", sa.Text(), nullable=True)
                )
            if "authorized_by_id" in cols:
                batch_op.alter_column("authorized_by_id", nullable=True)
            if "authorized_at" in cols:
                batch_op.alter_column("authorized_at", nullable=True)

        # Backfill existing rows that have an authorized_by_id to 'approved'
        bind.execute(sa.text("""
            UPDATE application_document_overrides
            SET status = 'approved'
            WHERE authorized_by_id IS NOT NULL;
        """))


def downgrade() -> None:
    pass
