"""Reading and writing a school's settings (ERP_BLUEPRINT §3.15 levels 1 and 3).

A read never inserts. An unset key returns the registry default, so a fresh
school behaves exactly like one whose rows happen to be present, and the
defaults are not duplicated in a seed that could drift from the registry.
"""

from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.settings_registry import BY_KEY, DEFAULTS
from app.models import AuditAction, Setting, User
from app.services import audit


def _definition(key: str):
    definition = BY_KEY.get(key)
    if definition is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown setting: {key}")
    return definition


def all_for(db: Session, school_id: int) -> dict[str, Any]:
    stored = {
        row.key: row.value
        for row in db.scalars(select(Setting).where(Setting.school_id == school_id))
        # A key retired from the registry stays in the table but stops being
        # served, so removing a setting does not need a data migration.
        if row.key in BY_KEY
    }
    return {**DEFAULTS, **stored}


def get(db: Session, school_id: int, key: str) -> Any:
    _definition(key)
    row = db.scalar(
        select(Setting).where(Setting.school_id == school_id, Setting.key == key)
    )
    return DEFAULTS[key] if row is None else row.value


def enabled(db: Session, school_id: int, module_code: str) -> bool:
    """Whether a module is switched on for this school."""
    return bool(get(db, school_id, f"feature.{module_code}"))


def require_module(db: Session, school_id: int, module_code: str) -> None:
    if not enabled(db, school_id, module_code):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"The {module_code} module is not enabled for this school",
        )


def module_enabled(module_code: str):
    """Route dependency: refuse the whole module when the school has it off.

    A switch the UI honours and the API does not is not a switch. This is the
    same separation as permissions — enforced where the request lands, not
    where it is drawn.
    """

    def _dep(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        require_module(db, user.school_id, module_code)
        return user

    return _dep


def set_many(db: Session, actor: User, values: dict[str, Any]) -> dict[str, Any]:
    """Validate against the registry, then write. All or nothing: a request
    that sets four settings and gets one type wrong changes none of them."""
    school_id = actor.school_id
    for key, value in values.items():
        definition = _definition(key)
        # bool is a subclass of int, so the int check has to exclude it or
        # `feature.fees = 1` would pass as a boolean.
        ok = (
            isinstance(value, bool)
            if definition.type is bool
            else isinstance(value, definition.type) and not isinstance(value, bool)
        )
        if not ok:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{key} expects {definition.type.__name__}, got {type(value).__name__}",
            )

    before = all_for(db, school_id)
    for key, value in values.items():
        row = db.scalar(
            select(Setting).where(Setting.school_id == school_id, Setting.key == key)
        )
        if row is None:
            db.add(Setting(school_id=school_id, key=key, value=value))
        else:
            row.value = value
    db.flush()

    after = all_for(db, school_id)
    audit.record(
        db,
        actor=actor,
        school_id=school_id,
        entity_type="settings",
        action=AuditAction.update,
        before={k: before[k] for k in values},
        after={k: after[k] for k in values},
    )
    db.commit()
    return after
