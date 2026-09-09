"""attendance keyed to the enrolment, plus holidays and leave requests

`attendance` was keyed to the student, so promoting 10-A to 11-A silently
re-parented every past mark to the new class — the defect the enrolment split
exists to fix, still present in one table (§3.2, §5.8.5).

Rebuilt rather than converted. Mapping a student's old rows onto the right
enrolment means guessing which year each date belonged to, and the only
attendance data that exists is the demo seed, which is regenerated.

`marked_by` becomes nullable: a row written by an approved leave request was
not marked by a teacher, and naming one who did not touch it is worse than a
null.

Revision ID: c9e16a48f0d3
Revises: b8d05f37e9c2
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9e16a48f0d3"
down_revision: str | None = "b8d05f37e9c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUS = sa.Enum(
    "present",
    "absent",
    "late",
    "half_day",
    "leave",
    "excused",
    name="attendancestatus",
    native_enum=False,
)
_LEAVE_TYPE = sa.Enum("sick", "planned", "emergency", name="leavetype", native_enum=False)
_LEAVE_STATUS = sa.Enum(
    "applied", "approved", "rejected", "cancelled", name="leavestatus", native_enum=False
)


def _pk() -> sa.Column:
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        primary_key=True,
    )


def _stamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False, index=True
    )


def upgrade() -> None:
    op.drop_table("attendance")
    op.create_table(
        "attendance",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", _STATUS, nullable=False),
        sa.Column("marked_by", sa.BigInteger(), sa.ForeignKey("employees.id")),
        sa.Column("remarks", sa.String(200)),
        sa.Column("corrected_by", sa.BigInteger(), sa.ForeignKey("employees.id")),
        sa.Column("corrected_at", sa.DateTime(timezone=True)),
        *_stamps(),
        sa.UniqueConstraint("enrolment_id", "date", name="uq_attendance_enrolment_date"),
    )
    op.create_index("ix_attendance_date", "attendance", ["date"])
    op.create_index(
        "ix_attendance_enrolment_date", "attendance", ["enrolment_id", "date"]
    )

    op.create_table(
        "holidays",
        _pk(),
        _tenant(),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        *_stamps(),
        sa.UniqueConstraint("academic_year_id", "date", name="uq_holiday_date"),
    )

    op.create_table(
        "student_leave_requests",
        _pk(),
        _tenant(),
        sa.Column(
            "enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"), nullable=False
        ),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("type", _LEAVE_TYPE, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", _LEAVE_STATUS, nullable=False),
        sa.Column("requested_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("decided_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decision_note", sa.Text()),
        *_stamps(),
        sa.CheckConstraint("to_date >= from_date", name="ck_leave_range"),
    )
    op.create_index(
        "ix_leave_enrolment_status", "student_leave_requests", ["enrolment_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_leave_enrolment_status", table_name="student_leave_requests")
    op.drop_table("student_leave_requests")
    op.drop_table("holidays")
    op.drop_index("ix_attendance_enrolment_date", table_name="attendance")
    op.drop_index("ix_attendance_date", table_name="attendance")
    op.drop_table("attendance")

    op.create_table(
        "attendance",
        _pk(),
        _tenant(),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("present", "absent", "leave", name="attendancestatus", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "marked_by", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column("remarks", sa.String(200)),
        *_stamps(),
        sa.UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
    )
