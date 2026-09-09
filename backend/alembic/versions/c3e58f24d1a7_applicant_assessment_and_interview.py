"""applicant assessments and interviews

Separate from `exams` and `marks` on purpose: those hang off an enrolment, and
an applicant has none. See app/models/assessment_admission.py.

Revision ID: c3e58f24d1a7
Revises: b2d47e91a5c8
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3e58f24d1a7"
down_revision: str | None = "b2d47e91a5c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TYPE = sa.Enum(
    "written_test", "readiness_observation", "previous_result_review",
    name="assessmenttype", native_enum=False,
)
_STATUS = sa.Enum(
    "scheduled", "completed", "absent", "cancelled",
    name="assessmentstatus", native_enum=False,
)
_RECOMMENDATION = sa.Enum(
    "strong_admit", "admit", "waitlist", "reject",
    name="interviewrecommendation", native_enum=False,
)


def _ts():
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("assessment_type", _TYPE, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(80)),
        sa.Column("seat_no", sa.String(16)),
        sa.Column("status", _STATUS, nullable=False, server_default="scheduled"),
        sa.Column("total_marks", sa.Numeric(6, 2)),
        sa.Column("obtained_marks", sa.Numeric(6, 2)),
        sa.Column("is_absent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evaluated_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("remarks", sa.Text()),
        *_ts(),
    )
    op.create_index("ix_assessments_school_id", "assessments", ["school_id"])
    op.create_index("ix_assessments_application_id", "assessments", ["application_id"])
    op.create_index("ix_assessment_slot", "assessments", ["school_id", "scheduled_at"])

    op.create_table(
        "assessment_subjects",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "assessment_id", sa.BigInteger(), sa.ForeignKey("assessments.id"), nullable=False
        ),
        sa.Column("subject", sa.String(60), nullable=False),
        sa.Column("max_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("obtained", sa.Numeric(6, 2)),
        *_ts(),
        sa.UniqueConstraint("assessment_id", "subject", name="uq_assessment_subject"),
    )
    op.create_index(
        "ix_assessment_subjects_school_id", "assessment_subjects", ["school_id"]
    )
    op.create_index(
        "ix_assessment_subjects_assessment_id", "assessment_subjects", ["assessment_id"]
    )

    op.create_table(
        "interviews",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(80)),
        sa.Column("panel_member_ids", sa.JSON()),
        sa.Column("status", _STATUS, nullable=False, server_default="scheduled"),
        sa.Column("structured_scores", sa.JSON()),
        sa.Column("child_rating", sa.Integer()),
        sa.Column("parent_rating", sa.Integer()),
        sa.Column("recommendation", _RECOMMENDATION),
        sa.Column("notes", sa.Text()),
        sa.Column("conducted_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        *_ts(),
    )
    op.create_index("ix_interviews_school_id", "interviews", ["school_id"])
    op.create_index("ix_interviews_application_id", "interviews", ["application_id"])
    op.create_index("ix_interview_slot", "interviews", ["school_id", "scheduled_at"])


def downgrade() -> None:
    op.drop_table("interviews")
    op.drop_table("assessment_subjects")
    op.drop_table("assessments")
