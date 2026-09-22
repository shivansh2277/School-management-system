"""drop recruitment tables (candidates, candidate_offers)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-21
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    sqlite = conn.dialect.name == "sqlite"
    naming = {
        "fk": "fk_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
    } if sqlite else None

    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # Drop candidate_offers first to satisfy foreign key constraints to candidates
    if "candidate_offers" in existing_tables:
        op.drop_table("candidate_offers")
    if "candidates" in existing_tables:
        op.drop_table("candidates")


def downgrade() -> None:
    # Recruitment is permanently decommissioned from the ERP product
    raise NotImplementedError("Recruitment module is permanently decommissioned.")
