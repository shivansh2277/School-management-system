"""assessment schemes, so a subject can carry more than one mark a term

v0 held exactly one number per subject per exam, which cannot produce the CBSE
report card: that card prints a periodic test, a notebook mark, subject
enrichment and the term examination, and totals them. A scheme declares those
columns as data (§0.5, §0.15) and an exam cites the one it fills.

`exams.scheme_component_id` is nullable on purpose — an exam without a
component is an ordinary class test, marked and readable and simply not
printed. Requiring it would mean a school must amend its scheme before it can
hold a surprise test.

Revision ID: f2b49d71c8a6
Revises: e1a38c60b7f5
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2b49d71c8a6"
down_revision: str | None = "e1a38c60b7f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
        "assessment_schemes",
        _pk(),
        _tenant(),
        sa.Column(
            "academic_year_id",
            sa.BigInteger(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_stamps(),
        sa.UniqueConstraint("academic_year_id", "name", name="uq_assessment_scheme_name"),
    )
    op.create_index(
        "uq_assessment_scheme_active",
        "assessment_schemes",
        ["academic_year_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
        sqlite_where=sa.text("is_active"),
    )

    op.create_table(
        "scheme_components",
        _pk(),
        _tenant(),
        sa.Column(
            "scheme_id",
            sa.BigInteger(),
            sa.ForeignKey("assessment_schemes.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("term", sa.String(20), nullable=False),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("max_marks", sa.Numeric(5, 2), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        *_stamps(),
        sa.UniqueConstraint("scheme_id", "term", "code", name="uq_scheme_component"),
        sa.CheckConstraint("max_marks > 0", name="ck_scheme_component_max_marks"),
    )

    # Nullable, and added with the FK in one batch so SQLite rebuilds once.
    with op.batch_alter_table("exams") as batch:
        batch.add_column(sa.Column("scheme_component_id", sa.BigInteger()))
        batch.create_foreign_key(
            "fk_exam_scheme_component", "scheme_components", ["scheme_component_id"], ["id"]
        )
    op.create_index("ix_exams_scheme_component_id", "exams", ["scheme_component_id"])


def downgrade() -> None:
    op.drop_index("ix_exams_scheme_component_id", table_name="exams")
    with op.batch_alter_table("exams") as batch:
        batch.drop_constraint("fk_exam_scheme_component", type_="foreignkey")
        batch.drop_column("scheme_component_id")
    op.drop_table("scheme_components")
    op.drop_index("uq_assessment_scheme_active", table_name="assessment_schemes")
    op.drop_table("assessment_schemes")
