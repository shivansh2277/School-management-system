"""bell timings as a table, slots that reference them, and substitutions

`timetable_slots` repeated `start_time` and `end_time` on every row, so moving
the lunch bell meant updating all 360 of them. Times move to `school_periods`
— the table behind the §5.7.3 setup screen — and a slot references a period.

Rebuilt rather than converted: the seeded v0 timetable held 144 teacher
double-bookings and 36 room clashes, so there is nothing there worth carrying
into a model that now refuses them.

Revision ID: d0f27b59a4e1
Revises: c9e16a48f0d3
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d0f27b59a4e1"
down_revision: str | None = "c9e16a48f0d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DAY = sa.Enum(
    "mon", "tue", "wed", "thu", "fri", "sat", name="dayofweek", native_enum=False
)
_SUB_STATUS = sa.Enum(
    "pending", "assigned", "unfilled", "completed",
    name="substitutionstatus", native_enum=False,
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
    op.create_table(
        "school_periods",
        _pk(),
        _tenant(),
        sa.Column("period_no", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("name", sa.String(20)),
        sa.Column("is_break", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "period_no", name="uq_school_period_no"),
    )

    op.drop_table("timetable_slots")
    op.create_table(
        "timetable_slots",
        _pk(),
        _tenant(),
        sa.Column(
            "class_section_id",
            sa.BigInteger(),
            sa.ForeignKey("class_sections.id"),
            nullable=False,
        ),
        sa.Column("day_of_week", _DAY, nullable=False),
        sa.Column(
            "period_id", sa.BigInteger(), sa.ForeignKey("school_periods.id"), nullable=False
        ),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("teacher_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("room", sa.String(20)),
        *_stamps(),
        sa.UniqueConstraint(
            "class_section_id", "day_of_week", "period_id", name="uq_timetable_slot"
        ),
    )
    op.create_index(
        "ix_slot_teacher_day_period",
        "timetable_slots",
        ["teacher_id", "day_of_week", "period_id"],
    )

    op.create_table(
        "substitutions",
        _pk(),
        _tenant(),
        sa.Column(
            "timetable_slot_id",
            sa.BigInteger(),
            sa.ForeignKey("timetable_slots.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "absent_teacher_id",
            sa.BigInteger(),
            sa.ForeignKey("employees.id"),
            nullable=False,
        ),
        sa.Column(
            "substitute_teacher_id", sa.BigInteger(), sa.ForeignKey("employees.id")
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", _SUB_STATUS, nullable=False),
        *_stamps(),
        sa.UniqueConstraint(
            "timetable_slot_id", "date", name="uq_substitution_slot_date"
        ),
    )
    op.create_index("ix_substitution_date", "substitutions", ["date"])


def downgrade() -> None:
    op.drop_index("ix_substitution_date", table_name="substitutions")
    op.drop_table("substitutions")
    op.drop_index("ix_slot_teacher_day_period", table_name="timetable_slots")
    op.drop_table("timetable_slots")
    op.drop_table("school_periods")

    op.create_table(
        "timetable_slots",
        _pk(),
        _tenant(),
        sa.Column(
            "class_section_id",
            sa.BigInteger(),
            sa.ForeignKey("class_sections.id"),
            nullable=False,
        ),
        sa.Column("day_of_week", _DAY, nullable=False),
        sa.Column("period_no", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("teacher_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("room", sa.String(20)),
        *_stamps(),
        sa.UniqueConstraint(
            "class_section_id", "day_of_week", "period_no", name="uq_timetable_slot"
        ),
    )
