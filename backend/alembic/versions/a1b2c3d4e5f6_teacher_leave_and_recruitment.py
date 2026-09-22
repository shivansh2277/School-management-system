"""teacher leave and recruitment

Revision ID: a1b2c3d4e5f6
Revises: f4d82b1c99e1
Create Date: 2026-09-17
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f4d82b1c99e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    sqlite = op.get_bind().dialect.name == "sqlite"
    naming = {"fk": "fk_%(table_name)s_%(column_0_name)s"} if sqlite else None

    # 1. Update staff_leave_requests (make leave_type_id nullable)
    with op.batch_alter_table("staff_leave_requests", naming_convention=naming) as batch_op:
        batch_op.alter_column("leave_type_id", existing_type=sa.BigInteger(), nullable=True)

    # 2. Update substitutions (add leave_request_id and index)
    with op.batch_alter_table("substitutions", naming_convention=naming) as batch_op:
        batch_op.add_column(
            sa.Column(
                "leave_request_id",
                sa.BigInteger(),
                sa.ForeignKey(
                    "staff_leave_requests.id",
                    name="fk_substitutions_leave_request_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )
        batch_op.create_index("ix_substitutions_leave_request_id", ["leave_request_id"])

    # 3. Create candidates table
    op.create_table(
        "candidates",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("application_no", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("post_applied_for", sa.String(100), nullable=False),
        sa.Column("qualification", sa.String(200), nullable=False),
        sa.Column("specialization", sa.String(100), nullable=True),
        sa.Column("experience_years", sa.Numeric(4, 1), server_default="0.0", nullable=False),
        sa.Column("previous_school", sa.String(200), nullable=True),
        sa.Column("expected_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("resume_file_key", sa.String(500), nullable=True),
        sa.Column("photo_file_key", sa.String(500), nullable=True),
        sa.Column("status", sa.String(30), server_default="applied", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("school_id", "application_no", name="uq_candidate_app_no"),
        sa.UniqueConstraint("employee_id", name="uq_candidate_employee_id"),
    )
    op.create_index("ix_candidates_school_id", "candidates", ["school_id"])
    op.create_index("ix_candidates_application_no", "candidates", ["application_no"])
    op.create_index("ix_candidates_school_status", "candidates", ["school_id", "status"])

    # 4. Create candidate_offers table
    op.create_table(
        "candidate_offers",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("candidate_id", sa.BigInteger(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("offered_designation", sa.String(100), nullable=False),
        sa.Column("offered_department_id", sa.BigInteger(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("offered_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column("offer_notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("candidate_id", name="uq_candidate_offer_candidate"),
    )
    op.create_index("ix_candidate_offers_school_id", "candidate_offers", ["school_id"])
    op.create_index("ix_candidate_offers_candidate_id", "candidate_offers", ["candidate_id"])

    # 5. Create in_app_notifications table
    op.create_table(
        "in_app_notifications",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("link_url", sa.String(255), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_in_app_notifications_school_id", "in_app_notifications", ["school_id"])
    op.create_index("ix_in_app_notifications_user_id", "in_app_notifications", ["user_id"])
    op.create_index(
        "ix_in_app_notifications_user_read", "in_app_notifications", ["user_id", "is_read"]
    )


def downgrade() -> None:
    sqlite = op.get_bind().dialect.name == "sqlite"
    naming = {"fk": "fk_%(table_name)s_%(column_0_name)s"} if sqlite else None

    op.drop_table("in_app_notifications")
    op.drop_table("candidate_offers")
    op.drop_table("candidates")
    with op.batch_alter_table("substitutions", naming_convention=naming) as batch_op:
        batch_op.drop_index("ix_substitutions_leave_request_id")
        batch_op.drop_column("leave_request_id")
    with op.batch_alter_table("staff_leave_requests", naming_convention=naming) as batch_op:
        batch_op.alter_column("leave_type_id", existing_type=sa.BigInteger(), nullable=False)
