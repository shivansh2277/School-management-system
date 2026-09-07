"""Grading scale setup (§5.4.3).

Bands are replaced wholesale rather than edited row by row: a scale is only
coherent as a set, and a partial edit is how a school ends up with a gap
between C2 and D that nobody notices until a report card prints a blank.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import GradingScale, User
from app.services import grading as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/grading-scales", tags=["admin"])
reader = require_permission("exam.definition.read", school_wide=True)
writer = require_permission("exam.definition.write", school_wide=True)


class BandIn(BaseModel):
    min_percent: Decimal = Field(ge=0, le=100)
    grade: str = Field(min_length=1, max_length=4)
    description: str | None = Field(default=None, max_length=40)


class ScaleIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    bands: list[BandIn]
    activate: bool = False


def _out(db: Session, scale: GradingScale) -> dict:
    return {
        "id": scale.id,
        "name": scale.name,
        "version": scale.version,
        "is_active": scale.is_active,
        "frozen_at": scale.frozen_at,
        "bands": [
            {
                "min_percent": b.min_percent,
                "grade": b.grade,
                "description": b.description,
            }
            for b in svc.bands_in(db, scale.id)
        ],
    }


def _owned(db: Session, user: User, scale_id: int) -> GradingScale:
    scale = db.get(GradingScale, scale_id)
    if scale is None or scale.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grading scale not found")
    return scale


@router.get("")
def list_scales(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    scales = db.scalars(
        select(GradingScale)
        .where(GradingScale.school_id == user.school_id)
        .order_by(GradingScale.name, GradingScale.version.desc())
    )
    return [_out(db, s) for s in scales]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_scale(
    body: ScaleIn, user: User = Depends(writer), db: Session = Depends(get_db)
) -> dict:
    """Create a scale, or the next version of one that already exists.

    Reusing the name is how a school revises a frozen scale: the old version
    stays readable for the report cards that cite it.
    """
    scale = svc.create(
        db,
        user.school_id,
        name=body.name,
        bands=[(b.min_percent, b.grade, b.description) for b in body.bands],
        activate=body.activate,
    )
    db.commit()
    return _out(db, scale)


@router.put("/{scale_id}/bands")
def replace_bands(
    scale_id: int,
    body: list[BandIn],
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> dict:
    scale = _owned(db, user, scale_id)
    svc.set_bands(db, scale, [(b.min_percent, b.grade, b.description) for b in body])
    db.commit()
    return _out(db, scale)


@router.post("/{scale_id}/activate")
def activate(
    scale_id: int, user: User = Depends(writer), db: Session = Depends(get_db)
) -> dict:
    scale = svc.activate_scale(db, _owned(db, user, scale_id))
    db.commit()
    return _out(db, scale)
