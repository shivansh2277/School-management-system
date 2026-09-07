"""staff leave, and the substitutions approving it must raise

§5.3.9 calls approving a teacher's leave that silently leaves classes
unattended the single most common real-world HR/timetable failure. Approval
therefore raises a `pending` substitution for every period the teacher was due
to teach, reusing the table Part 3 already built — an unfilled row is the
honest state and §5.7.10 already counts it; what must not happen is no row.

Leave types are rows, not an enum. The student `LeaveType` enum is
student-shaped and carries no entitlement, and §3.15 puts per-school
configuration in tables.

Revision ID: d6f83b15c2ea
Revises: c5e72a04f1d9
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d6f83b15c2ea"
down_revision: str | None = "c5e72a04f1d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEAVE_STATUS = sa.Enum(
    "applied", "approved", "rejected", "cancelled",
    name="leavestatus", native_enum=False,
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
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
        nullable=False, index=True,
    )


def upgrade() -> None:
    op.create_table(
        "leave_types",
        _pk(),
        _tenant(),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("annual_quota", sa.Numeric(5, 1), nullable=False),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "code", name="uq_leave_type_code"),
        sa.CheckConstraint("annual_quota >= 0", name="ck_leave_type_quota"),
    )

    op.create_table(
        "leave_balances",
        _pk(),
        _tenant(),
        sa.Column(
            "employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "leave_type_id", sa.BigInteger(), sa.ForeignKey("leave_types.id"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id", sa.BigInteger(), sa.ForeignKey("academic_years.id"),
            nullable=False, index=True,
        ),
        sa.Column("entitled", sa.Numeric(5, 1), nullable=False),
        sa.Column("used", sa.Numeric(5, 1), nullable=False, server_default="0"),
        *_stamps(),
        sa.UniqueConstraint(
            "employee_id", "leave_type_id", "academic_year_id", name="uq_leave_balance"
        ),
        sa.CheckConstraint("used >= 0", name="ck_leave_balance_used"),
    )

    op.create_table(
        "staff_leave_requests",
        _pk(),
        _tenant(),
        sa.Column(
            "employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "leave_type_id", sa.BigInteger(), sa.ForeignKey("leave_types.id"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id", sa.BigInteger(), sa.ForeignKey("academic_years.id"),
            nullable=False,
        ),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column(
            "is_half_day", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        # Stored, not recomputed: a holiday declared after the fact would
        # otherwise silently restate an approved request.
        sa.Column("days", sa.Numeric(5, 1), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status", _LEAVE_STATUS, nullable=False, server_default="applied"
        ),
        sa.Column(
            "balance_exception", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("decided_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decision_note", sa.Text()),
        *_stamps(),
        sa.CheckConstraint("to_date >= from_date", name="ck_staff_leave_range"),
        sa.CheckConstraint("days > 0", name="ck_staff_leave_days"),
    )
    op.create_index(
        "ix_staff_leave_employee_dates",
        "staff_leave_requests",
        ["employee_id", "from_date", "to_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_staff_leave_employee_dates", table_name="staff_leave_requests")
    op.drop_table("staff_leave_requests")
    op.drop_table("leave_balances")
    op.drop_table("leave_types")
