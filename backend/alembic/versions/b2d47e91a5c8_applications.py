"""applications, their guardians, siblings and medical section

ERP_BLUEPRINT §5.1.4-5. Address, previous school and declarations are JSON:
a form step writes and reads each of them whole, and nothing queries inside
them. Medical is a table of its own because §15 gates it separately.

Revision ID: b2d47e91a5c8
Revises: a1c93f7b62d4
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d47e91a5c8"
down_revision: str | None = "a1c93f7b62d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUS = sa.Enum(
    "draft", "submitted", "under_document_verification", "documents_verified",
    "documents_rejected", "assessment_scheduled", "assessment_completed",
    "interview_scheduled", "interview_completed", "decision_pending", "admitted",
    "waitlisted", "rejected", "offer_issued", "offer_accepted", "offer_expired",
    "fee_paid", "enrolled", "withdrawn_by_parent", "cancelled_after_admission",
    name="applicationstatus", native_enum=False,
)
_CATEGORY = sa.Enum(
    "general", "sibling", "staff_ward", "management", "rte", "sports", "alumni_child",
    name="admissioncategory", native_enum=False,
)
_SOURCE = sa.Enum(
    "walk_in", "phone", "website", "referral", "alumni", "hoarding",
    "digital_ad", "other",
    name="enquirysource", native_enum=False,
)
_RELATION = sa.Enum(
    "father", "mother", "grandparent", "sibling", "legal_guardian", "other",
    name="guardianrelation", native_enum=False,
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
        "applications",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "cycle_id", sa.BigInteger(), sa.ForeignKey("admission_cycles.id"), nullable=False
        ),
        sa.Column("application_no", sa.String(24)),
        sa.Column("first_name", sa.String(60), nullable=False),
        sa.Column("middle_name", sa.String(60)),
        sa.Column("last_name", sa.String(60), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(12), nullable=False),
        sa.Column("nationality", sa.String(40)),
        sa.Column("religion", sa.String(40)),
        sa.Column("caste_category", sa.String(12)),
        sa.Column("mother_tongue", sa.String(40)),
        sa.Column("place_of_birth", sa.String(80)),
        sa.Column("identification_marks", sa.Text()),
        sa.Column("is_single_child", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aadhaar_last4", sa.String(4)),
        sa.Column("aadhaar_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("class_applying_for", sa.String(8), nullable=False),
        sa.Column("stream", sa.String(20)),
        sa.Column("second_language", sa.String(40)),
        sa.Column("optional_subject", sa.String(40)),
        sa.Column("preferred_section", sa.String(4)),
        sa.Column("admission_category", _CATEGORY, nullable=False, server_default="general"),
        sa.Column("transport_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", _STATUS, nullable=False, server_default="draft"),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("source", _SOURCE, nullable=False, server_default="walk_in"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("address", sa.JSON()),
        sa.Column("previous_school", sa.JSON()),
        sa.Column("declarations", sa.JSON()),
        sa.Column("sibling_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "staff_ward_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("age_override_reason", sa.Text()),
        sa.Column(
            "previous_application_id", sa.BigInteger(), sa.ForeignKey("applications.id")
        ),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id")),
        *_ts(),
        sa.UniqueConstraint("school_id", "application_no", name="uq_application_no"),
    )
    op.create_index("ix_applications_school_id", "applications", ["school_id"])
    op.create_index("ix_application_cycle_status", "applications", ["cycle_id", "status"])
    op.create_index(
        "ix_application_class", "applications", ["cycle_id", "class_applying_for"]
    )
    op.create_index(
        "ix_application_child", "applications", ["school_id", "last_name", "date_of_birth"]
    )

    op.create_table(
        "application_guardians",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("relation", _RELATION, nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("qualification", sa.String(120)),
        sa.Column("occupation", sa.String(80)),
        sa.Column("designation", sa.String(80)),
        sa.Column("organisation", sa.String(120)),
        sa.Column("annual_income_band", sa.String(40)),
        sa.Column("office_address", sa.Text()),
        sa.Column("mobile", sa.String(20), nullable=False),
        sa.Column("alternate_mobile", sa.String(20)),
        sa.Column("email", sa.String(160)),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "is_emergency_contact", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_authorised_for_pickup", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_school_alumnus", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("is_school_staff", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("employee_id", sa.BigInteger(), sa.ForeignKey("employees.id")),
        *_ts(),
    )
    op.create_index(
        "ix_application_guardians_school_id", "application_guardians", ["school_id"]
    )
    op.create_index(
        "ix_application_guardians_application_id", "application_guardians", ["application_id"]
    )
    op.create_index(
        "ix_application_guardian_mobile", "application_guardians", ["school_id", "mobile"]
    )
    # One primary contact per application, for the same reason student_guardian
    # has one: "who do we ring" must have a single answer.
    op.create_index(
        "uq_application_primary_guardian",
        "application_guardians",
        ["application_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
        sqlite_where=sa.text("is_primary"),
    )

    op.create_table(
        "application_siblings",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id")),
        sa.Column("name", sa.String(120)),
        sa.Column("age", sa.Integer()),
        sa.Column("school_name", sa.String(160)),
        *_ts(),
    )
    op.create_index(
        "ix_application_siblings_school_id", "application_siblings", ["school_id"]
    )
    op.create_index(
        "ix_application_siblings_application_id", "application_siblings", ["application_id"]
    )

    op.create_table(
        "application_medical",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("blood_group", sa.String(8)),
        sa.Column("known_allergies", sa.Text()),
        sa.Column("chronic_conditions", sa.Text()),
        sa.Column("regular_medication", sa.Text()),
        sa.Column("physical_disability", sa.Text()),
        sa.Column("learning_needs", sa.Text()),
        sa.Column("vision_hearing_notes", sa.Text()),
        sa.Column("emergency_doctor", sa.String(160)),
        sa.Column("emergency_doctor_phone", sa.String(20)),
        sa.Column(
            "consent_for_emergency_treatment",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        *_ts(),
        sa.UniqueConstraint("application_id", name="uq_application_medical"),
    )
    op.create_index(
        "ix_application_medical_school_id", "application_medical", ["school_id"]
    )

    # The enquiry register can finally point at what it converted into.
    # Batch mode because SQLite cannot ALTER a constraint into place, and the
    # migration test runs there.
    with op.batch_alter_table("enquiries") as batch:
        batch.create_foreign_key(
            "fk_enquiries_application", "applications", ["converted_application_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("enquiries") as batch:
        batch.drop_constraint("fk_enquiries_application", type_="foreignkey")
    op.drop_table("application_medical")
    op.drop_table("application_siblings")
    op.drop_table("application_guardians")
    op.drop_table("applications")
