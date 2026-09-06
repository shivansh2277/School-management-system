"""documents and document types

Nothing in v0 modelled an uploaded file (ERP_BLUEPRINT §2.5(8)), and Admission
cannot be built without them. Seeds the CBSE-school document checklist so a new
tenant has a usable list on day one.

Revision ID: 7f38b1a9c4d2
Revises: 6e24da71c05f
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.document_types import DEFAULT_TYPES

revision: str = "7f38b1a9c4d2"
down_revision: str | None = "6e24da71c05f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OWNER = sa.Enum(
    "student", "application", "guardian", "employee", "vehicle", "school",
    name="ownertype", native_enum=False,
)
_DOC_STATUS = sa.Enum(
    "pending", "submitted", "verified", "rejected", "resubmit_required",
    name="documentstatus", native_enum=False,
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
        "document_types",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("applies_to", _OWNER, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("required_if_category", sa.String(40)),
        sa.Column("has_expiry", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        *_ts(),
        sa.UniqueConstraint("school_id", "code", name="uq_document_type"),
    )
    op.create_index("ix_document_types_school_id", "document_types", ["school_id"])

    op.create_table(
        "documents",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("owner_type", _OWNER, nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "document_type_id", sa.BigInteger(), sa.ForeignKey("document_types.id")
        ),
        sa.Column("file_key", sa.String(255), nullable=False, unique=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(64)),
        sa.Column("uploaded_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", _DOC_STATUS, nullable=False, server_default="pending"),
        sa.Column("original_seen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("expires_on", sa.Date()),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.BigInteger()),
        sa.Column("delete_reason", sa.Text()),
        *_ts(),
    )
    op.create_index("ix_documents_school_id", "documents", ["school_id"])
    op.create_index("ix_document_owner", "documents", ["owner_type", "owner_id"])
    op.create_index("ix_document_status", "documents", ["school_id", "status"])

    bind = op.get_bind()
    ins = sa.text(
        "INSERT INTO document_types (school_id, code, name, applies_to, is_mandatory,"
        " required_if_category, has_expiry, is_confidential, sort_order, created_at,"
        " updated_at) VALUES (:sid, :code, :name, :applies, :mand, :cat, :exp, :conf,"
        " :order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )
    for school_id in [r[0] for r in bind.execute(sa.text("SELECT id FROM schools"))]:
        for i, (code, name, applies, mand, cat, exp, conf) in enumerate(DEFAULT_TYPES):
            bind.execute(
                ins,
                {
                    "sid": school_id,
                    "code": code,
                    "name": name,
                    "applies": applies,
                    "mand": mand,
                    "cat": cat,
                    "exp": exp,
                    "conf": conf,
                    "order": (i + 1) * 10,
                },
            )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("document_types")
