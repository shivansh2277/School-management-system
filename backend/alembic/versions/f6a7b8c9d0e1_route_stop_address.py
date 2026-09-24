"""add address to route_stops

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-24
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("route_stops") as batch_op:
        batch_op.add_column(sa.Column("address", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("route_stops") as batch_op:
        batch_op.drop_column("address")
