"""School-defined attributes: ERP_BLUEPRINT §3.15 level 2.

Definitions are rows; values are a JSON dict on the entity. This module is the
only place that reconciles the two, so a retired definition disappears from
every read at once and a value cannot be stored against a field the school
never defined.
"""

from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CustomField, CustomFieldType, OwnerType


def definitions(
    db: Session, school_id: int, entity: OwnerType, *, include_inactive: bool = False
) -> list[CustomField]:
    stmt = select(CustomField).where(
        CustomField.school_id == school_id, CustomField.entity == entity
    )
    if not include_inactive:
        stmt = stmt.where(CustomField.is_active.is_(True))
    return list(db.scalars(stmt.order_by(CustomField.sort_order, CustomField.key)))


def _coerce(field: CustomField, value: Any) -> Any:
    """Return the value in the field's type, or raise 422.

    Kept strict rather than forgiving: a "number" field that quietly accepts
    "twelve thousand" is worse than one that refuses it, because the refusal
    happens in front of the clerk who can fix it.
    """
    t = field.field_type
    if t is CustomFieldType.text:
        if not isinstance(value, str):
            raise _bad(field, "text")
        return value.strip()
    if t is CustomFieldType.number:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _bad(field, "a number")
        return value
    if t is CustomFieldType.boolean:
        if not isinstance(value, bool):
            raise _bad(field, "true or false")
        return value
    if t is CustomFieldType.date:
        if not isinstance(value, str):
            raise _bad(field, "a date as YYYY-MM-DD")
        try:
            date.fromisoformat(value)
        except ValueError:
            raise _bad(field, "a date as YYYY-MM-DD") from None
        return value
    # select
    if value not in (field.options or []):
        raise _bad(field, "one of: " + ", ".join(field.options or []))
    return value


def _bad(field: CustomField, expected: str) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        f"{field.label} expects {expected}",
    )


def validate(
    db: Session,
    school_id: int,
    entity: OwnerType,
    submitted: dict[str, Any] | None,
    *,
    existing: dict[str, Any] | None = None,
    partial: bool = False,
) -> dict[str, Any]:
    """Merge submitted values onto the existing ones and return the new bag.

    `partial=True` (a PATCH) leaves untouched keys alone and skips the required
    check for them; a full write demands every required field. Unknown keys are
    refused rather than dropped — a mistyped key that vanishes silently is how
    a school ends up believing data was saved.
    """
    values = dict(existing or {})
    submitted = submitted or {}
    by_key = {f.key: f for f in definitions(db, school_id, entity)}

    unknown = sorted(set(submitted) - set(by_key))
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"No such custom field: {', '.join(unknown)}",
        )

    for key, value in submitted.items():
        field = by_key[key]
        if value is None or value == "":
            if field.is_required:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"{field.label} is required",
                )
            values.pop(key, None)
            continue
        values[key] = _coerce(field, value)

    if not partial:
        missing = [
            f.label for f in by_key.values() if f.is_required and values.get(f.key) in (None, "")
        ]
        if missing:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Required: {', '.join(missing)}",
            )

    # Values recorded against a since-retired field stay in the column but are
    # not re-saved, so the bag does not grow a tail of dead keys forever.
    return {k: v for k, v in values.items() if k in by_key}


def create(db: Session, school_id: int, body) -> CustomField:
    if body.field_type is CustomFieldType.select and not body.options:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A select field needs at least one option",
        )
    if db.scalar(
        select(CustomField).where(
            CustomField.school_id == school_id,
            CustomField.entity == body.entity,
            CustomField.key == body.key,
        )
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"{body.key} is already defined on {body.entity}"
        )
    field = CustomField(school_id=school_id, **body.model_dump())
    db.add(field)
    db.commit()
    return field


def retire(db: Session, school_id: int, field_id: int) -> None:
    field = db.get(CustomField, field_id)
    if field is None or field.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Custom field not found")
    field.is_active = False
    db.commit()
