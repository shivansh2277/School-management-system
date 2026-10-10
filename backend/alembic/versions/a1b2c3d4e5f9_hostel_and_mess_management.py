"""hostel and mess management module

Revision ID: a1b2c3d4e5f9
Revises: f7a8b9c0d1e2
Create Date: 2026-10-08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f9"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. Add hostel_required to applications
    if insp.has_table("applications"):
        cols = [c["name"] for c in insp.get_columns("applications")]
        if "hostel_required" not in cols:
            with op.batch_alter_table("applications") as batch_op:
                batch_op.add_column(
                    sa.Column("hostel_required", sa.Boolean(), nullable=False, server_default=sa.text("false"))
                )

    # 2. Hostels
    if not insp.has_table("hostels"):
        op.create_table(
            "hostels",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("gender", sa.String(12), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "code", name="uq_hostel_code"),
        )

    # 3. Hostel Floors
    if not insp.has_table("hostel_floors"):
        op.create_table(
            "hostel_floors",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("floor_number", sa.Integer(), nullable=False),
            sa.Column("floor_name", sa.String(60), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "hostel_id", "floor_number", name="uq_hostel_floor_number"),
        )

    # 4. Hostel Rooms
    if not insp.has_table("hostel_rooms"):
        op.create_table(
            "hostel_rooms",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("floor_id", sa.BigInteger(), sa.ForeignKey("hostel_floors.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("room_number", sa.String(20), nullable=False),
            sa.Column("capacity", sa.Integer(), nullable=False, server_default=sa.text("2")),
            sa.Column("room_type", sa.String(30), nullable=False, server_default=sa.text("'standard'")),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'available'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "hostel_id", "room_number", name="uq_hostel_room_number"),
            sa.CheckConstraint("capacity > 0", name="ck_room_capacity_positive"),
        )

    # 5. Hostel Beds
    if not insp.has_table("hostel_beds"):
        op.create_table(
            "hostel_beds",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("hostel_rooms.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("bed_number", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'available'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "room_id", "bed_number", name="uq_hostel_bed_number"),
        )

    # 6. Hostel Admissions
    if not insp.has_table("hostel_admissions"):
        op.create_table(
            "hostel_admissions",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=False, index=True),
            sa.Column("admission_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
            sa.Column("exit_date", sa.Date(), nullable=True),
            sa.Column("exit_reason", sa.Text(), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("admitted_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("exited_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "ix_hostel_admission_student",
            "hostel_admissions",
            ["school_id", "student_id", "status"],
        )
        op.create_index(
            "ix_hostel_admission_hostel",
            "hostel_admissions",
            ["school_id", "hostel_id", "status"],
        )
        op.create_index(
            "uq_active_hostel_admission",
            "hostel_admissions",
            ["school_id", "student_id"],
            unique=True,
            postgresql_where=sa.text("status = 'active'"),
            sqlite_where=sa.text("status = 'active'"),
        )

    # 7. Bed Allocations
    if not insp.has_table("bed_allocations"):
        op.create_table(
            "bed_allocations",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("admission_id", sa.BigInteger(), sa.ForeignKey("hostel_admissions.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("bed_id", sa.BigInteger(), sa.ForeignKey("hostel_beds.id"), nullable=False, index=True),
            sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("vacated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("allocated_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "uq_active_bed_allocation",
            "bed_allocations",
            ["bed_id"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
            sqlite_where=sa.text("is_active = 1"),
        )
        op.create_index(
            "uq_active_admission_allocation",
            "bed_allocations",
            ["admission_id"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
            sqlite_where=sa.text("is_active = 1"),
        )

    # 8. Hostel Attendances
    if not insp.has_table("hostel_attendances"):
        op.create_table(
            "hostel_attendances",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=False, index=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False, index=True),
            sa.Column("admission_id", sa.BigInteger(), sa.ForeignKey("hostel_admissions.id"), nullable=False),
            sa.Column("attendance_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("scheduled_time", sa.Time(), nullable=False, server_default=sa.text("'20:00:00'")),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recorded_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "hostel_id", "student_id", "attendance_date", name="uq_hostel_attendance"),
        )
        op.create_index(
            "ix_hostel_att_date",
            "hostel_attendances",
            ["school_id", "hostel_id", "attendance_date"],
        )

    # 9. Hostel Leave Requests
    if not insp.has_table("hostel_leave_requests"):
        op.create_table(
            "hostel_leave_requests",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False, index=True),
            sa.Column("admission_id", sa.BigInteger(), sa.ForeignKey("hostel_admissions.id"), nullable=False),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=False, index=True),
            sa.Column("request_type", sa.String(20), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("out_time", sa.Time(), nullable=True),
            sa.Column("expected_return_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actual_return_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("purpose", sa.Text(), nullable=False),
            sa.Column("parent_guardian_id", sa.BigInteger(), sa.ForeignKey("guardians.id"), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
            sa.Column("approved_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("returned_recorded_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "ix_hostel_leaves_student",
            "hostel_leave_requests",
            ["school_id", "student_id", "status"],
        )
        op.create_index(
            "ix_hostel_leaves_hostel",
            "hostel_leave_requests",
            ["school_id", "hostel_id", "status"],
        )

    # 10. Hostel Mess Menus (School-wide)
    if not insp.has_table("hostel_mess_menus"):
        op.create_table(
            "hostel_mess_menus",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("day_of_week", sa.String(10), nullable=False),
            sa.Column("breakfast", sa.Text(), nullable=False),
            sa.Column("lunch", sa.Text(), nullable=False),
            sa.Column("snacks", sa.Text(), nullable=False),
            sa.Column("dinner", sa.Text(), nullable=False),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("updated_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("school_id", "day_of_week", name="uq_mess_menu_day"),
        )

    # 11. Hostel Complaints
    if not insp.has_table("hostel_complaints"):
        op.create_table(
            "hostel_complaints",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=False, index=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=True),
            sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("hostel_rooms.id"), nullable=True),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
            sa.Column("resolution_remarks", sa.Text(), nullable=True),
            sa.Column("resolved_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "ix_hostel_complaints_hostel",
            "hostel_complaints",
            ["school_id", "hostel_id", "status"],
        )

    # 12. Hostel Incidents
    if not insp.has_table("hostel_incidents"):
        op.create_table(
            "hostel_incidents",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=False, index=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False, server_default=sa.text("'medium'")),
            sa.Column("incident_date", sa.Date(), nullable=False),
            sa.Column("action_taken", sa.Text(), nullable=True),
            sa.Column("reported_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'open'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "ix_hostel_incidents_hostel",
            "hostel_incidents",
            ["school_id", "hostel_id", "incident_date"],
        )

    # 13. Hostel Notices
    if not insp.has_table("hostel_notices"):
        op.create_table(
            "hostel_notices",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True),
            sa.Column("hostel_id", sa.BigInteger(), sa.ForeignKey("hostels.id"), nullable=True, index=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("priority", sa.String(20), nullable=False, server_default=sa.text("'normal'")),
            sa.Column("posted_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index(
            "ix_hostel_notices_hostel",
            "hostel_notices",
            ["school_id", "hostel_id", "is_active"],
        )


def downgrade() -> None:
    pass
