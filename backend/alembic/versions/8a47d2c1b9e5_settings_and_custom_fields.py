"""settings, feature flags and custom fields

Levels 1-3 of the customization ladder in ERP_BLUEPRINT §3.15. No rows are
seeded: an unset setting reads as the registry default, so a school that has
never opened the settings screen behaves identically to one that has.

`students.custom` is created NOT NULL with a server_default of '{}' — the
tenancy migration already taught this codebase that a NOT NULL column added
without one leaves existing rows unfillable.

Revision ID: 8a47d2c1b9e5
Revises: 7f38b1a9c4d2
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8a47d2c1b9e5"
down_revision: str | None = "7f38b1a9c4d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OWNER = sa.Enum(
    "student", "application", "guardian", "employee", "vehicle", "school",
    name="ownertype", native_enum=False,
)
_FIELD_TYPE = sa.Enum(
    "text", "number", "date", "boolean", "select",
    name="customfieldtype", native_enum=False,
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
        "settings",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        *_ts(),
        sa.UniqueConstraint("school_id", "key", name="uq_setting_key"),
    )
    op.create_index("ix_settings_school_id", "settings", ["school_id"])

    op.create_table(
        "custom_fields",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("entity", _OWNER, nullable=False),
        sa.Column("key", sa.String(40), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("field_type", _FIELD_TYPE, nullable=False),
        sa.Column("options", sa.JSON()),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        *_ts(),
        sa.UniqueConstraint("school_id", "entity", "key", name="uq_custom_field_key"),
    )
    op.create_index("ix_custom_fields_school_id", "custom_fields", ["school_id"])

    op.add_column(
        "students",
        sa.Column("custom", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("students", "custom")
    op.drop_table("custom_fields")
    op.drop_table("settings")
