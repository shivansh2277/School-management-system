"""add alert_views table for important alerts persistence

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f8
Create Date: 2026-09-27
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: str | None = "a1b2c3d4e5f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "alert_views" in insp.get_table_names():
        return

    op.create_table(
        "alert_views",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("event_key", sa.String(100), nullable=False),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "school_id",
            "user_id",
            "student_id",
            "alert_type",
            "event_key",
            name="uq_alert_views_user_student_alert",
        ),
    )
    op.create_index("ix_alert_views_user_id", "alert_views", ["user_id"])
    op.create_index("ix_alert_views_student_id", "alert_views", ["student_id"])
    op.create_index(
        "ix_alert_views_lookup",
        "alert_views",
        ["user_id", "student_id", "alert_type", "event_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_alert_views_lookup", table_name="alert_views")
    op.drop_index("ix_alert_views_student_id", table_name="alert_views")
    op.drop_index("ix_alert_views_user_id", table_name="alert_views")
    op.drop_table("alert_views")
