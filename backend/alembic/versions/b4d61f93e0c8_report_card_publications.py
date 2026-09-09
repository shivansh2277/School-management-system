"""report cards frozen at publication

§0.8 makes a published report card a document rather than a view: reopening it
months later must show exactly what was issued, even if a grade band has moved
since. So the whole rendered card is stored, and the grading scale and
assessment scheme it was computed against are cited by id rather than
re-resolved on read. Live screens keep computing from `grade_bands` — this
supersedes BLUEPRINT §7.5 for published documents only.

One card per child per term, enforced by a unique constraint: a correction is a
new document, not an edit to this row.

Revision ID: b4d61f93e0c8
Revises: a3c50e82d9b7
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b4d61f93e0c8"
down_revision: str | None = "a3c50e82d9b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_card_publications",
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
            "enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"),
            nullable=False, index=True,
        ),
        sa.Column("term", sa.String(20), nullable=False),
        sa.Column(
            "scheme_id", sa.BigInteger(), sa.ForeignKey("assessment_schemes.id"),
            nullable=False,
        ),
        sa.Column(
            "grading_scale_id", sa.BigInteger(), sa.ForeignKey("grading_scales.id"),
            nullable=False,
        ),
        sa.Column("document_no", sa.String(32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("result_status", sa.String(20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("enrolment_id", "term", name="uq_report_card_term"),
    )


def downgrade() -> None:
    op.drop_table("report_card_publications")
