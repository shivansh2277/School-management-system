"""enrolments: a student's class is a fact about a year

Moves `class_section_id` and `roll_no` off `students` and onto a new
`enrolments` table (ERP_BLUEPRINT §3.2). Existing students are given one
enrolment in the academic year their section already belongs to, so no history
is invented and none is lost.

Revision ID: 3a91c6d40e12
Revises: 2170fa7c7d81
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a91c6d40e12"
down_revision: str | None = "2170fa7c7d81"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENROLMENT_STATUS = sa.Enum(
    "active",
    "promoted",
    "detained",
    "transferred_out",
    "struck_off",
    "passed_out",
    name="enrolmentstatus",
    native_enum=False,
)
_STUDENT_STATUS = sa.Enum(
    "enrolled",
    "active",
    "suspended",
    "transferred_out",
    "struck_off",
    "passed_out",
    "alumni",
    name="studentstatus",
    native_enum=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "enrolments",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
        ),
        sa.Column(
            "class_section_id",
            sa.BigInteger(),
            sa.ForeignKey("class_sections.id"),
            nullable=False,
        ),
        sa.Column("roll_no", sa.Integer(), nullable=False),
        sa.Column("status", _ENROLMENT_STATUS, nullable=False, server_default="active"),
        sa.Column("joined_on", sa.Date()),
        sa.Column("left_on", sa.Date()),
        sa.Column("house", sa.String(20)),
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("class_section_id", "roll_no", name="uq_enrolment_roll"),
    )
    op.create_index("ix_enrolments_school_id", "enrolments", ["school_id"])
    op.create_index("ix_enrolments_student_id", "enrolments", ["student_id"])
    op.create_index("ix_enrolments_academic_year_id", "enrolments", ["academic_year_id"])
    op.create_index("ix_enrolments_class_section_id", "enrolments", ["class_section_id"])
    op.create_index("ix_enrolment_section_status", "enrolments", ["class_section_id", "status"])
    # One enrolment per student per year — the invariant that keeps the history
    # model honest.
    op.create_index(
        "uq_enrolment_student_year",
        "enrolments",
        ["student_id", "academic_year_id"],
        unique=True,
    )

    # Each existing student gets one enrolment, in the year their section
    # already belongs to. The section carries the year, so nothing is guessed.
    bind.execute(
        sa.text(
            "INSERT INTO enrolments (school_id, student_id, academic_year_id,"
            " class_section_id, roll_no, status, joined_on, created_at, updated_at)"
            " SELECT s.school_id, s.id, cs.academic_year_id, s.class_section_id,"
            " s.roll_no, 'active', s.admission_date, CURRENT_TIMESTAMP,"
            " CURRENT_TIMESTAMP"
            " FROM students s"
            " JOIN class_sections cs ON cs.id = s.class_section_id"
        )
    )

    op.add_column(
        "students",
        sa.Column("status", _STUDENT_STATUS, nullable=False, server_default="active"),
    )
    with op.batch_alter_table("students") as batch:
        batch.drop_constraint("uq_student_roll", type_="unique")
        batch.drop_column("class_section_id")
        batch.drop_column("roll_no")


def downgrade() -> None:
    raise NotImplementedError(
        "Irreversible: a student may have several enrolments and only one could "
        "be folded back onto the students row, discarding the rest. Restore "
        "from backup instead."
    )
