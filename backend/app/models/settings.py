"""Per-school configuration: levels 1-3 of ERP_BLUEPRINT §3.15.

Two tables, because they answer two different questions:

* `settings` — what this school chose, for a key the software defined. Typed by
  `core/settings_registry.py`; a key that is not in the registry is rejected
  rather than stored, so a typo cannot become a silently-ignored setting.
* `custom_fields` — attributes this school invented, which the software knows
  nothing about. The definitions live here; the values live in a JSON column on
  the entity itself. That is deliberately not an EAV table: reading a student
  should not mean joining a row per attribute, and a school with fifteen custom
  fields is normal.
"""

from sqlalchemy import JSON, Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import CustomFieldType, OwnerType


class Setting(TenantBase):
    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("school_id", "key", name="uq_setting_key"),)

    key: Mapped[str] = mapped_column(String(80), nullable=False)
    # JSON rather than a text column plus a type tag: the registry already
    # states the type, and JSON round-trips a bool as a bool.
    value: Mapped[object] = mapped_column(JSON, nullable=False)


class CustomField(TenantBase):
    """One school-defined attribute on students, guardians, employees or
    applications (§3.15 level 2)."""

    __tablename__ = "custom_fields"
    __table_args__ = (
        UniqueConstraint("school_id", "entity", "key", name="uq_custom_field_key"),
    )

    entity: Mapped[OwnerType] = enum_col(OwnerType, nullable=False)
    key: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    field_type: Mapped[CustomFieldType] = enum_col(CustomFieldType, nullable=False)
    # Only for `select`; the allowed choices.
    options: Mapped[list | None] = mapped_column(JSON)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Retired rather than deleted: values already recorded against it stay
    # readable, and a school that turns one off has not lost last year's data.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=100)
