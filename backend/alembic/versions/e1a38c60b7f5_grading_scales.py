"""grading scales, so a published grade can be frozen against a version

`grade_bands` hung directly off the school, so editing "A1 starts at 91" to
"A1 starts at 90" re-graded every report card the school had ever issued —
at read time, silently. §0.8 requires a published card to snapshot the grade
*and the scale version*, which needs a row a publication can cite.

Existing bands are moved onto a "CBSE" scale at version 1, made active. The
check constraint and the two uniques are new: nothing stopped two bands from
both claiming 91 before.

Revision ID: e1a38c60b7f5
Revises: d0f27b59a4e1
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a38c60b7f5"
down_revision: str | None = "d0f27b59a4e1"
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
        "grading_scales",
        _pk(),
        _tenant(),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("frozen_at", sa.DateTime(timezone=True)),
        *_stamps(),
        sa.UniqueConstraint("school_id", "name", "version", name="uq_grading_scale_version"),
    )
    op.create_index(
        "uq_grading_scale_active",
        "grading_scales",
        ["school_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
        sqlite_where=sa.text("is_active"),
    )

    # One scale per school that already has bands, and point its bands at it.
    op.add_column("grade_bands", sa.Column("grading_scale_id", sa.BigInteger()))
    op.add_column("grade_bands", sa.Column("description", sa.String(40)))

    # Built through Core rather than raw SQL: `now()` and `true` are Postgres
    # spellings and the migration test runs this on SQLite, where both are a
    # syntax error. Timestamps come from the columns' own server defaults.
    scales = sa.table(
        "grading_scales",
        sa.column("id", sa.BigInteger),
        sa.column("school_id", sa.BigInteger),
        sa.column("name", sa.String),
        sa.column("version", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    bands = sa.table(
        "grade_bands",
        sa.column("school_id", sa.BigInteger),
        sa.column("grading_scale_id", sa.BigInteger),
    )
    conn = op.get_bind()
    for (school_id,) in conn.execute(sa.select(bands.c.school_id).distinct()).all():
        conn.execute(
            scales.insert().values(
                school_id=school_id, name="CBSE", version=1, is_active=True
            )
        )
        scale_id = conn.execute(
            sa.select(scales.c.id).where(
                scales.c.school_id == school_id, scales.c.name == "CBSE"
            )
        ).scalar_one()
        conn.execute(
            bands.update()
            .where(bands.c.school_id == school_id)
            .values(grading_scale_id=scale_id)
        )

    # Only now can it be NOT NULL: the backfill had to run against a nullable
    # column first. Batch mode because SQLite has no ALTER COLUMN and no ADD
    # CONSTRAINT — it rebuilds the table. That rebuild is what once dropped a
    # server_default silently (HANDOFF §4), so `test_migrations.py` checks the
    # timestamps still default after this runs.
    with op.batch_alter_table("grade_bands") as batch:
        batch.alter_column(
            "grading_scale_id", existing_type=sa.BigInteger(), nullable=False
        )
        batch.create_foreign_key(
            "fk_grade_band_scale", "grading_scales", ["grading_scale_id"], ["id"]
        )
        batch.create_unique_constraint(
            "uq_grade_band_grade", ["grading_scale_id", "grade"]
        )
        batch.create_unique_constraint(
            "uq_grade_band_floor", ["grading_scale_id", "min_percent"]
        )
        batch.create_check_constraint(
            "ck_grade_band_percent", "min_percent >= 0 AND min_percent <= 100"
        )
    op.create_index("ix_grade_bands_grading_scale_id", "grade_bands", ["grading_scale_id"])


def downgrade() -> None:
    op.drop_index("ix_grade_bands_grading_scale_id", table_name="grade_bands")
    with op.batch_alter_table("grade_bands") as batch:
        batch.drop_constraint("ck_grade_band_percent", type_="check")
        batch.drop_constraint("uq_grade_band_floor", type_="unique")
        batch.drop_constraint("uq_grade_band_grade", type_="unique")
        batch.drop_constraint("fk_grade_band_scale", type_="foreignkey")
        batch.drop_column("description")
        batch.drop_column("grading_scale_id")
    op.drop_index("uq_grading_scale_active", table_name="grading_scales")
    op.drop_table("grading_scales")
