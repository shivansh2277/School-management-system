"""receptionist operations: found items, student passes, meeting slips, and directory contacts

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-22
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. found_items
    op.create_table(
        "found_items",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("item_name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="other"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("found_location", sa.String(150), nullable=False),
        sa.Column("found_date", sa.Date(), nullable=False),
        sa.Column("found_time", sa.String(20), nullable=True),
        sa.Column("recorded_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recorded_by_name", sa.String(120), nullable=False),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="reported"),
        sa.Column("broadcasted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_by_student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("claimed_by_student_name", sa.String(120), nullable=True),
        sa.Column("claimed_by_admission_no", sa.String(50), nullable=True),
        sa.Column("claimed_by_class_name", sa.String(50), nullable=True),
        sa.Column("handover_photo_url", sa.Text(), nullable=True),
        sa.Column("handover_notes", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_by_staff_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("collected_by_staff_name", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_found_items_school_id", "found_items", ["school_id"])
    op.create_index("ix_found_items_school_status", "found_items", ["school_id", "status"])
    op.create_index("ix_found_items_school_date", "found_items", ["school_id", "found_date"])
    op.create_index("ix_found_items_claimed_by_student_id", "found_items", ["claimed_by_student_id"])

    # 2. student_authorized_persons
    op.create_table(
        "student_authorized_persons",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("relationship", sa.String(60), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("id_proof_type", sa.String(50), nullable=True),
        sa.Column("id_proof_number", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_student_auth_persons_school_id", "student_authorized_persons", ["school_id"])
    op.create_index("ix_student_auth_persons_student", "student_authorized_persons", ["school_id", "student_id"])

    # 3. student_passes
    op.create_table(
        "student_passes",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("pass_code", sa.String(40), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("student_name", sa.String(120), nullable=False),
        sa.Column("admission_no", sa.String(50), nullable=False),
        sa.Column("class_name", sa.String(60), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("pickup_person_name", sa.String(120), nullable=False),
        sa.Column("pickup_person_relation", sa.String(60), nullable=False),
        sa.Column("pickup_person_phone", sa.String(30), nullable=False),
        sa.Column("pickup_person_id_proof", sa.String(80), nullable=True),
        sa.Column("pass_date", sa.Date(), nullable=False),
        sa.Column("pass_time", sa.String(20), nullable=False),
        sa.Column("issued_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issued_by_name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="issued"),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_student_passes_school_id", "student_passes", ["school_id"])
    op.create_index("ix_student_passes_code", "student_passes", ["pass_code"])
    op.create_index("ix_student_passes_school_date", "student_passes", ["school_id", "pass_date"])
    op.create_index("ix_student_passes_student", "student_passes", ["school_id", "student_id"])

    # 4. principal_meeting_requests
    op.create_table(
        "principal_meeting_requests",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("slip_code", sa.String(40), nullable=False),
        sa.Column("visitor_name", sa.String(120), nullable=False),
        sa.Column("visitor_phone", sa.String(30), nullable=False),
        sa.Column("visitor_organization", sa.String(120), nullable=True),
        sa.Column("student_name", sa.String(120), nullable=True),
        sa.Column("student_admission_no", sa.String(50), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("meeting_time", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("wait_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_principal_meetings_school_id", "principal_meeting_requests", ["school_id"])
    op.create_index("ix_principal_meetings_code", "principal_meeting_requests", ["slip_code"])
    op.create_index("ix_principal_meetings_school_status", "principal_meeting_requests", ["school_id", "status"])
    op.create_index("ix_principal_meetings_school_date", "principal_meeting_requests", ["school_id", "meeting_date"])

    # 5. teacher_meeting_requests
    op.create_table(
        "teacher_meeting_requests",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
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

    # 6. directory_contacts
    op.create_table(
        "directory_contacts",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("category", sa.String(60), nullable=False, server_default="Emergency"),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("designation_or_department", sa.String(120), nullable=True),
        sa.Column("phone_primary", sa.String(40), nullable=False),
        sa.Column("phone_secondary", sa.String(40), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("operating_hours", sa.String(100), nullable=True),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_directory_contacts_school_id", "directory_contacts", ["school_id"])
    op.create_index("ix_directory_contacts_school_category", "directory_contacts", ["school_id", "category"])


def downgrade() -> None:
    op.drop_table("directory_contacts")
    op.drop_table("teacher_meeting_requests")
    op.drop_table("principal_meeting_requests")
    op.drop_table("student_passes")
    op.drop_table("student_authorized_persons")
    op.drop_table("found_items")
