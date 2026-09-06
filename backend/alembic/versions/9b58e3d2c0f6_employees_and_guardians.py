"""teachers -> employees, parents -> guardians

ERP_BLUEPRINT §3.4. `teachers` left the librarian, the accountant and the bus
in-charge with nowhere to live, and Part 4 builds HR, payroll and transport on
staff rather than on teachers. `parents` was likewise wrong for the child
living with a grandparent, and §0.7 settled that guardians stay their own
entity with a nullable cross-link to `employees` for the teacher whose own
child studies here.

Renames rather than recreates, so existing rows and their ids survive. The
columns that point at a teacher *in a teaching role* — `class_teacher_id`,
`class_subject_teacher.teacher_id`, `homework.teacher_id` — keep their names:
they describe the role in that context, not the entity.

Revision ID: 9b58e3d2c0f6
Revises: 8a47d2c1b9e5
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9b58e3d2c0f6"
down_revision: str | None = "8a47d2c1b9e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMPLOYEE_TYPE = sa.Enum(
    "teaching", "administrative", "support", name="employeetype", native_enum=False
)
_RELATION = sa.Enum(
    "father", "mother", "grandparent", "sibling", "legal_guardian", "other",
    name="guardianrelation", native_enum=False,
)

# What v0 stored as free text, mapped onto the closed list. Anything else
# becomes `other` rather than failing the migration: a relation nobody
# anticipated is a data-quality problem, not a reason to block an upgrade.
_KNOWN = ("father", "mother", "grandparent", "sibling", "legal_guardian", "other")


def upgrade() -> None:
    bind = op.get_bind()

    op.rename_table("teachers", "employees")
    with op.batch_alter_table("employees") as batch:
        batch.alter_column(
            "employee_id", new_column_name="employee_code", existing_type=sa.String(16)
        )
        batch.add_column(
            sa.Column(
                "employee_type",
                _EMPLOYEE_TYPE,
                nullable=False,
                server_default="teaching",
            )
        )

    op.rename_table("parents", "guardians")
    op.add_column("guardians", sa.Column("employee_id", sa.BigInteger()))

    op.rename_table("parent_student", "student_guardian")
    with op.batch_alter_table("student_guardian") as batch:
        batch.alter_column(
            "parent_id", new_column_name="guardian_id", existing_type=sa.BigInteger()
        )
        batch.add_column(
            sa.Column(
                "is_primary", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )

    bind.execute(
        sa.text(
            "UPDATE student_guardian SET relation = 'other' "
            f"WHERE relation NOT IN ({', '.join(repr(r) for r in _KNOWN)})"
        )
    )
    with op.batch_alter_table("student_guardian") as batch:
        batch.alter_column("relation", type_=_RELATION, existing_type=sa.String(20))

    # The first guardian recorded against each child becomes the one the school
    # rings, so the "who do we call" column is not empty for every existing row.
    bind.execute(
        sa.text(
            "UPDATE student_guardian SET is_primary = true WHERE id IN "
            "(SELECT MIN(id) FROM student_guardian GROUP BY student_id)"
        )
    )
    op.create_index(
        "uq_student_primary_guardian",
        "student_guardian",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
        sqlite_where=sa.text("is_primary"),
    )


def downgrade() -> None:
    op.drop_index("uq_student_primary_guardian", table_name="student_guardian")
    with op.batch_alter_table("student_guardian") as batch:
        batch.alter_column("relation", type_=sa.String(20), existing_type=_RELATION)
        batch.drop_column("is_primary")
        batch.alter_column(
            "guardian_id", new_column_name="parent_id", existing_type=sa.BigInteger()
        )
    op.rename_table("student_guardian", "parent_student")

    op.drop_column("guardians", "employee_id")
    op.rename_table("guardians", "parents")

    with op.batch_alter_table("employees") as batch:
        batch.drop_column("employee_type")
        batch.alter_column(
            "employee_code", new_column_name="employee_id", existing_type=sa.String(16)
        )
    op.rename_table("employees", "teachers")
