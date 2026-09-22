"""enrolment_id refactor: marks, homework_submissions, grievances

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-18
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    sqlite = conn.dialect.name == "sqlite"
    naming = {
        "fk": "fk_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
    } if sqlite else None

    # ==========================================
    # 1. TABLE: marks
    # ==========================================
    with op.batch_alter_table("marks", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("enrolment_id", sa.BigInteger(), nullable=True))

    # Backfill marks.enrolment_id
    if sqlite:
        conn.execute(sa.text("""
            UPDATE marks
            SET enrolment_id = (
                SELECT e.id
                FROM enrolments e
                JOIN exam_schedule es ON es.id = marks.exam_schedule_id
                WHERE e.student_id = marks.student_id
                  AND e.class_section_id = es.class_section_id
                LIMIT 1
            )
            WHERE enrolment_id IS NULL;
        """))
    else:
        conn.execute(sa.text("""
            UPDATE marks m
            SET enrolment_id = e.id
            FROM enrolments e, exam_schedule es
            WHERE es.id = m.exam_schedule_id
              AND e.student_id = m.student_id
              AND e.class_section_id = es.class_section_id;
        """))

    # If any mark rows exist without an enrolment (e.g. orphan records), clean or bind
    if sqlite:
        conn.execute(sa.text("""
            UPDATE marks
            SET enrolment_id = (
                SELECT e.id FROM enrolments e WHERE e.student_id = marks.student_id LIMIT 1
            )
            WHERE enrolment_id IS NULL;
        """))
    else:
        conn.execute(sa.text("""
            UPDATE marks m
            SET enrolment_id = e.id
            FROM enrolments e
            WHERE m.enrolment_id IS NULL
              AND e.student_id = m.student_id;
        """))

    with op.batch_alter_table("marks", naming_convention=naming) as batch_op:
        batch_op.alter_column("enrolment_id", existing_type=sa.BigInteger(), nullable=False)
        batch_op.create_foreign_key(
            "fk_marks_enrolment_id",
            "enrolments",
            ["enrolment_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        try:
            batch_op.drop_constraint("uq_mark", type_="unique")
        except Exception:
            pass
        batch_op.create_unique_constraint("uq_mark", ["exam_schedule_id", "enrolment_id"])
        batch_op.create_index("ix_marks_enrolment_id", ["enrolment_id"])
        try:
            batch_op.drop_column("student_id")
        except Exception:
            pass

    # ==========================================
    # 2. TABLE: homework & homework_submissions
    # ==========================================
    # Add attachment_url to homework
    with op.batch_alter_table("homework", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("attachment_url", sa.String(500), nullable=True))

    with op.batch_alter_table("homework_submissions", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("enrolment_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("marks", sa.Numeric(5, 2), nullable=True))
        batch_op.add_column(sa.Column("remarks", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("attachment_url", sa.String(500), nullable=True))

    # Backfill homework_submissions.enrolment_id
    if sqlite:
        conn.execute(sa.text("""
            UPDATE homework_submissions
            SET enrolment_id = (
                SELECT e.id
                FROM enrolments e
                JOIN homework h ON h.id = homework_submissions.homework_id
                WHERE e.student_id = homework_submissions.student_id
                  AND e.class_section_id = h.class_section_id
                LIMIT 1
            )
            WHERE enrolment_id IS NULL;
        """))
        conn.execute(sa.text("""
            UPDATE homework_submissions
            SET enrolment_id = (
                SELECT e.id FROM enrolments e WHERE e.student_id = homework_submissions.student_id LIMIT 1
            )
            WHERE enrolment_id IS NULL;
        """))
    else:
        conn.execute(sa.text("""
            UPDATE homework_submissions hs
            SET enrolment_id = e.id
            FROM enrolments e, homework h
            WHERE h.id = hs.homework_id
              AND e.student_id = hs.student_id
              AND e.class_section_id = h.class_section_id;
        """))
        conn.execute(sa.text("""
            UPDATE homework_submissions hs
            SET enrolment_id = e.id
            FROM enrolments e
            WHERE hs.enrolment_id IS NULL
              AND e.student_id = hs.student_id;
        """))

    with op.batch_alter_table("homework_submissions", naming_convention=naming) as batch_op:
        batch_op.alter_column("enrolment_id", existing_type=sa.BigInteger(), nullable=False)
        batch_op.create_foreign_key(
            "fk_homework_submissions_enrolment_id",
            "enrolments",
            ["enrolment_id"],
            ["id"],
            ondelete="CASCADE",
        )
        try:
            batch_op.drop_constraint("uq_submission", type_="unique")
        except Exception:
            pass
        batch_op.create_unique_constraint("uq_submission", ["homework_id", "enrolment_id"])
        batch_op.create_index("ix_homework_submissions_enrolment_id", ["enrolment_id"])
        try:
            batch_op.drop_column("student_id")
        except Exception:
            pass

    # ==========================================
    # 3. TABLE: grievances
    # ==========================================
    with op.batch_alter_table("grievances", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("enrolment_id", sa.BigInteger(), nullable=True))
        batch_op.create_foreign_key(
            "fk_grievances_enrolment_id",
            "enrolments",
            ["enrolment_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_grievances_enrolment_id", ["enrolment_id"])

    # Backfill grievances.enrolment_id
    if sqlite:
        conn.execute(sa.text("""
            UPDATE grievances
            SET enrolment_id = (
                SELECT e.id
                FROM enrolments e
                WHERE e.student_id = grievances.student_id
                  AND e.status = 'active'
                LIMIT 1
            )
            WHERE enrolment_id IS NULL AND student_id IS NOT NULL;
        """))
    else:
        conn.execute(sa.text("""
            UPDATE grievances g
            SET enrolment_id = e.id
            FROM enrolments e
            WHERE e.student_id = g.student_id
              AND e.status = 'active';
        """))


def downgrade() -> None:
    conn = op.get_bind()
    sqlite = conn.dialect.name == "sqlite"
    naming = {
        "fk": "fk_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
    } if sqlite else None

    # Revert grievances
    with op.batch_alter_table("grievances", naming_convention=naming) as batch_op:
        batch_op.drop_index("ix_grievances_enrolment_id")
        batch_op.drop_constraint("fk_grievances_enrolment_id", type_="foreignkey")
        batch_op.drop_column("enrolment_id")

    # Revert homework & submissions
    with op.batch_alter_table("homework", naming_convention=naming) as batch_op:
        batch_op.drop_column("attachment_url")

    with op.batch_alter_table("homework_submissions", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("student_id", sa.BigInteger(), nullable=True))

    if sqlite:
        conn.execute(sa.text("""
            UPDATE homework_submissions
            SET student_id = (SELECT e.student_id FROM enrolments e WHERE e.id = homework_submissions.enrolment_id)
        """))
    else:
        conn.execute(sa.text("""
            UPDATE homework_submissions hs
            SET student_id = e.student_id
            FROM enrolments e
            WHERE e.id = hs.enrolment_id
        """))

    with op.batch_alter_table("homework_submissions", naming_convention=naming) as batch_op:
        batch_op.alter_column("student_id", existing_type=sa.BigInteger(), nullable=False)
        batch_op.drop_constraint("uq_submission", type_="unique")
        batch_op.create_unique_constraint("uq_submission", ["homework_id", "student_id"])
        batch_op.drop_index("ix_homework_submissions_enrolment_id")
        batch_op.drop_constraint("fk_homework_submissions_enrolment_id", type_="foreignkey")
        batch_op.drop_column("attachment_url")
        batch_op.drop_column("graded_at")
        batch_op.drop_column("remarks")
        batch_op.drop_column("marks")
        batch_op.drop_column("enrolment_id")

    # Revert marks
    with op.batch_alter_table("marks", naming_convention=naming) as batch_op:
        batch_op.add_column(sa.Column("student_id", sa.BigInteger(), nullable=True))

    if sqlite:
        conn.execute(sa.text("""
            UPDATE marks
            SET student_id = (SELECT e.student_id FROM enrolments e WHERE e.id = marks.enrolment_id)
        """))
    else:
        conn.execute(sa.text("""
            UPDATE marks m
            SET student_id = e.student_id
            FROM enrolments e
            WHERE e.id = m.enrolment_id
        """))

    with op.batch_alter_table("marks", naming_convention=naming) as batch_op:
        batch_op.alter_column("student_id", existing_type=sa.BigInteger(), nullable=False)
        batch_op.drop_constraint("uq_mark", type_="unique")
        batch_op.create_unique_constraint("uq_mark", ["exam_schedule_id", "student_id"])
        batch_op.drop_index("ix_marks_enrolment_id")
        batch_op.drop_constraint("fk_marks_enrolment_id", type_="foreignkey")
        batch_op.drop_column("enrolment_id")
