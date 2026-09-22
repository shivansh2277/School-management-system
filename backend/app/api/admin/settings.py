"""Configuration screens for the records clerk (§0.18): settings, module
switches and custom fields.

`/admin/settings` is already taken by the school's profile — name, address,
branding — which is a different thing from the setting store, so these live
under `/admin/configuration`.
"""

from typing import Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.modules import MODULES
from app.core.settings_registry import SETTINGS
from app.models import CustomFieldType, OwnerType, User
from app.services import custom_fields as cf
from app.services import school_settings as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])
reader = require_permission("admin.settings.read", school_wide=True)
writer = Depends(require_permission("admin.settings.write"))


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


class CustomFieldCreate(BaseModel):
    entity: OwnerType
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,39}$")
    label: str
    field_type: CustomFieldType
    options: list[str] | None = None
    is_required: bool = False
    sort_order: int = 100


def _field_out(f) -> dict:
    return {
        "id": f.id,
        "entity": f.entity,
        "key": f.key,
        "label": f.label,
        "field_type": f.field_type,
        "options": f.options,
        "is_required": f.is_required,
        "is_active": f.is_active,
        "sort_order": f.sort_order,
    }


@router.get("/configuration")
def read_settings(user: User = Depends(reader), db: Session = Depends(get_db)) -> dict:
    """Values plus the vocabulary, so the screen can render controls it was not
    written against — the point of a registry."""
    return {
        "values": svc.all_for(db, user.school_id),
        "definitions": [
            {"key": s.key, "type": s.type.__name__, "default": s.default,
             "description": s.description}
            for s in SETTINGS
        ],
        "modules": [
            {"code": m.code, "name": m.name, "built": m.built} for m in MODULES
        ],
    }


@router.put("/configuration", dependencies=[writer])
def write_settings(
    body: SettingsUpdate, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    result = svc.set_many(db, user, body.values)
    db.commit()
    return {"values": result}


@router.get("/custom-fields")
def list_custom_fields(
    entity: OwnerType = OwnerType.student,
    include_inactive: bool = False,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        _field_out(f)
        for f in cf.definitions(
            db, user.school_id, entity, include_inactive=include_inactive
        )
    ]


@router.post("/custom-fields", status_code=status.HTTP_201_CREATED, dependencies=[writer])
def create_custom_field(
    body: CustomFieldCreate, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    return _field_out(cf.create(db, user.school_id, body))


@router.delete(
    "/custom-fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[writer],
)
def retire_custom_field(
    field_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> Response:
    """Retires the definition. Values already recorded are kept."""
    cf.retire(db, user.school_id, field_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
