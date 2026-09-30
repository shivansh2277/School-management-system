"""remove teacher meeting requests and add user access management

Revision ID: a1b2c3d4e5f8
Revises: f6a7b8c9d0e1
Create Date: 2026-09-26
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f8"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. Drop teacher_meeting_requests table if it exists
    if "teacher_meeting_requests" in tables:
        op.drop_table("teacher_meeting_requests")

    # 2. Add app_access_blocked and token_version to users table if missing
    user_cols = [c["name"] for c in insp.get_columns("users")]
    with op.batch_alter_table("users") as batch_op:
        if "app_access_blocked" not in user_cols:
            batch_op.add_column(
                sa.Column(
                    "app_access_blocked",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("false"),
                )
            )
        if "token_version" not in user_cols:
            batch_op.add_column(
                sa.Column(
                    "token_version",
                    sa.Integer(),
                    nullable=False,
                    server_default=sa.text("1"),
                )
            )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("token_version")
        batch_op.drop_column("app_access_blocked")

    op.create_table(
        "teacher_meeting_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("slip_code", sa.String(40), nullable=False),
        sa.Column("teacher_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("teacher_name", sa.String(120), nullable=False),
        sa.Column("visitor_name", sa.String(120), nullable=False),
        sa.Column("visitor_phone", sa.String(30), nullable=False),
        sa.Column("visitor_relation", sa.String(60), nullable=True),
        sa.Column("student_name", sa.String(120), nullable=True),
        sa.Column("student_admission_no", sa.String(50), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("meeting_time", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_teacher_meetings_school_id", "teacher_meeting_requests", ["school_id"])
    op.create_index("ix_teacher_meetings_code", "teacher_meeting_requests", ["slip_code"])
    op.create_index("ix_teacher_meetings_school_status", "teacher_meeting_requests", ["school_id", "status"])
    op.create_index("ix_teacher_meetings_teacher", "teacher_meeting_requests", ["school_id", "teacher_id"])
