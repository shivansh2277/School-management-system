"""marks: a lock on the paper, and absent/exempted as their own states

§5.4.9 wants three distinguishable states and a single non-null number cannot
carry them: a zero is a mark — the child sat the paper and scored nothing —
while an absence and an exemption are not marks at all, and a child excused
from a paper must not be averaged against it.

The lock goes on `exam_schedule` rather than on each mark because §5.4.7 closes
marks entry *per subject*; a per-mark lock would let a paper be half shut.

There is no `mark_change_log` table. `audit_log` is already append-only, already
refuses a `status_change` without a reason, and is already indexed on
(entity_type, entity_id) — its own docstring names "changing a published mark"
as the case it exists for. A second log would be a second thing to keep honest.

Revision ID: a3c50e82d9b7
Revises: f2b49d71c8a6
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3c50e82d9b7"
down_revision: str | None = "f2b49d71c8a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("exam_schedule") as batch:
        batch.add_column(sa.Column("room", sa.String(20)))
        batch.add_column(sa.Column("marks_locked_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("marks_locked_by", sa.BigInteger()))
        batch.create_foreign_key(
            "fk_exam_schedule_locked_by", "users", ["marks_locked_by"], ["id"]
        )

    # `marks.entered_by` pointed at `employees`, which made the exam
    # controller's override path impossible: the person §5.4.8 puts in charge of
    # moderation may hold no teaching post, and every other actor in this
    # codebase — the audit log included — is identified by user. Re-pointed at
    # `users`, mapping the existing employee ids through `employees.user_id`.
    # The column is written and never read, so nothing else moves.
    marks = sa.table(
        "marks",
        sa.column("entered_by", sa.BigInteger),
    )
    employees = sa.table(
        "employees",
        sa.column("id", sa.BigInteger),
        sa.column("user_id", sa.BigInteger),
    )
    conn = op.get_bind()
    for employee_id, user_id in conn.execute(
        sa.select(employees.c.id, employees.c.user_id)
    ).all():
        conn.execute(
            marks.update()
            .where(marks.c.entered_by == employee_id)
            .values(entered_by=user_id)
        )
    # The original foreign key was never named, so the two engines disagree
    # about what to call it: Postgres auto-named it `marks_entered_by_fkey`,
    # while SQLite reflects it with no name at all and batch mode needs a
    # convention before it can be addressed. Hence the branch — the alternative
    # is a migration that passes on SQLite and fails on the engine that matters.
    sqlite = op.get_bind().dialect.name == "sqlite"
    naming = {"fk": "fk_%(table_name)s_%(column_0_name)s"} if sqlite else None
    old_fk = "fk_marks_entered_by" if sqlite else "marks_entered_by_fkey"
    with op.batch_alter_table("marks", naming_convention=naming) as batch:
        batch.drop_constraint(old_fk, type_="foreignkey")
        batch.create_foreign_key(
            "fk_marks_entered_by_user", "users", ["entered_by"], ["id"]
        )

    # Existing marks are all real scores, so both flags default false and
    # `marks_obtained` stays populated — the constraints below hold for every
    # row already there.
    with op.batch_alter_table("marks") as batch:
        batch.add_column(
            sa.Column("is_absent", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column(
                "is_exempted", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch.add_column(sa.Column("remarks", sa.String(200)))
        batch.alter_column(
            "marks_obtained", existing_type=sa.Numeric(5, 2), nullable=True
        )
        batch.create_check_constraint(
            "ck_mark_absent_xor_exempted", "NOT (is_absent AND is_exempted)"
        )
        batch.create_check_constraint(
            "ck_mark_score_matches_state",
            "(is_absent OR is_exempted) = (marks_obtained IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("marks") as batch:
        batch.drop_constraint("ck_mark_score_matches_state", type_="check")
        batch.drop_constraint("ck_mark_absent_xor_exempted", type_="check")
        batch.drop_column("remarks")
        batch.drop_column("is_exempted")
        batch.drop_column("is_absent")
    op.execute("DELETE FROM marks WHERE marks_obtained IS NULL")
    with op.batch_alter_table("marks") as batch:
        batch.alter_column(
            "marks_obtained", existing_type=sa.Numeric(5, 2), nullable=False
        )
    with op.batch_alter_table("exam_schedule") as batch:
        batch.drop_constraint("fk_exam_schedule_locked_by", type_="foreignkey")
        batch.drop_column("marks_locked_by")
        batch.drop_column("marks_locked_at")
        batch.drop_column("room")
