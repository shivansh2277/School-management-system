"""application authorized pickup persons with photos

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-24
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add photo_url to application_guardians
    with op.batch_alter_table("application_guardians") as batch_op:
        batch_op.add_column(sa.Column("photo_url", sa.Text(), nullable=True))

    # 2. application_authorized_persons
    op.create_table(
        "application_authorized_persons",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("relationship", sa.String(60), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("id_proof_type", sa.String(50), nullable=True),
        sa.Column("id_proof_number", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_app_auth_persons_school_id", "application_authorized_persons", ["school_id"])
    op.create_index(
        "ix_app_auth_persons_app",
        "application_authorized_persons",
        ["school_id", "application_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_app_auth_persons_app", table_name="application_authorized_persons")
    op.drop_index("ix_app_auth_persons_school_id", table_name="application_authorized_persons")
    op.drop_table("application_authorized_persons")

    with op.batch_alter_table("application_guardians") as batch_op:
        batch_op.drop_column("photo_url")
