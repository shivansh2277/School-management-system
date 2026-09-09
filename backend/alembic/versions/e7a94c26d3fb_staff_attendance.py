"""the staff register, and the loss-of-pay days payroll is computed from

Mirrors the student register rather than inventing a second set of habits: the
same calendar decides whether the school was open, and a correction to an
earlier day is an audited act while fixing today's mark is not.

`AttendanceStatus` is shared with the student register. The six states a school
records about a person being in or not are the same six, and a second
nearly-identical enum would be two lists to keep in step.

Keyed to the employee rather than to an enrolment: unlike a child, a member of
staff has no per-year membership row — the employment is the continuity.

Revision ID: e7a94c26d3fb
Revises: d6f83b15c2ea
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7a94c26d3fb"
down_revision: str | None = "d6f83b15c2ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ATTENDANCE = sa.Enum(
    "present", "absent", "late", "half_day", "leave", "excused",
    name="attendancestatus", native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "staff_attendance",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", _ATTENDANCE, nullable=False),
        sa.Column("check_in", sa.Time()),
        sa.Column("check_out", sa.Time()),
        # Nullable: a row written by an approved leave request was not marked
        # by anybody, and naming somebody who did not touch it is worse.
        sa.Column("marked_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("corrected_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("remarks", sa.String(200)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("employee_id", "date", name="uq_staff_attendance_date"),
    )
    op.create_index("ix_staff_attendance_date", "staff_attendance", ["date"])
    op.create_index(
        "ix_staff_attendance_employee_date", "staff_attendance", ["employee_id", "date"]
    )


def downgrade() -> None:
    op.drop_index("ix_staff_attendance_employee_date", table_name="staff_attendance")
    op.drop_index("ix_staff_attendance_date", table_name="staff_attendance")
    op.drop_table("staff_attendance")
