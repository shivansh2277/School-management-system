"""grievances and feedback

Adds grievances and grievance_replies tables for tracking teacher and parent complaints,
support issues, assignments to teachers, resolution notes, and conversational reply threads.

Revision ID: f4d82b1c99e1
Revises: e8c91a72d4b5
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4d82b1c99e1"
down_revision: str | None = "e8c91a72d4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grievances",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, server_default="general"),
        sa.Column("raised_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raised_by_role", sa.String(30), nullable=False),
        sa.Column("raised_by_name", sa.String(120), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("student_name", sa.String(120), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("assigned_to_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("assigned_to_name", sa.String(120), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_grievances_school_id", "grievances", ["school_id"])
    op.create_index("ix_grievances_school_status", "grievances", ["school_id", "status"])
    op.create_index("ix_grievances_school_raised_by", "grievances", ["school_id", "raised_by_id"])
    op.create_index("ix_grievances_school_assigned_to", "grievances", ["school_id", "assigned_to_id"])
    op.create_index("ix_grievances_student_id", "grievances", ["student_id"])

    op.create_table(
        "grievance_replies",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "grievance_id",
            sa.BigInteger(),
            sa.ForeignKey("grievances.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_name", sa.String(120), nullable=False),
        sa.Column("author_role", sa.String(30), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_grievance_replies_school_id", "grievance_replies", ["school_id"])
    op.create_index(
        "ix_grievance_replies_grievance",
        "grievance_replies",
        ["school_id", "grievance_id"],
    )


def downgrade() -> None:
    op.drop_table("grievance_replies")
    op.drop_table("grievances")
