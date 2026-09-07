"""Assessment scheme setup (§5.4.3).

Components are replaced wholesale rather than edited one at a time: a term's
components are only meaningful as a set — they are what a subject is out of —
and a partial edit is how a school ends up marking out of 105.
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import AssessmentScheme, User
from app.services import schemes as svc
from app.services import tenancy
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/assessment-schemes", tags=["admin"])
reader = require_permission("exam.definition.read", school_wide=True)
writer = require_permission("exam.definition.write", school_wide=True)


class ComponentIn(BaseModel):
    code: str = Field(min_length=1, max_length=12)
    name: str = Field(min_length=1, max_length=60)
    term: str = Field(min_length=1, max_length=20)
    max_marks: Decimal = Field(gt=0)


class SchemeIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    components: list[ComponentIn] | None = None
    academic_year_id: int | None = None
    activate: bool = False


def _out(db: Session, scheme: AssessmentScheme) -> dict:
    rows = svc.components(db, scheme.id)
    return {
        "id": scheme.id,
        "name": scheme.name,
        "academic_year_id": scheme.academic_year_id,
        "is_active": scheme.is_active,
        "terms": [
            {"term": t, "total": svc.term_total(db, scheme.id, t)}
            for t in svc.terms(db, scheme.id)
        ],
        "components": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "term": c.term,
                "max_marks": c.max_marks,
                "sequence": c.sequence,
            }
            for c in rows
        ],
    }


def _owned(db: Session, user: User, scheme_id: int) -> AssessmentScheme:
    scheme = db.get(AssessmentScheme, scheme_id)
    if scheme is None or scheme.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment scheme not found")
    return scheme


@router.get("")
def list_schemes(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(AssessmentScheme)
        .where(AssessmentScheme.school_id == user.school_id)
        .order_by(AssessmentScheme.academic_year_id.desc(), AssessmentScheme.name)
    )
    return [_out(db, s) for s in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_scheme(
    body: SchemeIn, user: User = Depends(writer), db: Session = Depends(get_db)
) -> dict:
    """Create a scheme. With no components given, the CBSE default is used —
    which is a pre-filled form, not an assumption the code makes elsewhere."""
    year_id = body.academic_year_id or tenancy.current_year(db, user.school_id).id
    rows = (
        [(c.code, c.name, c.term, c.max_marks) for c in body.components]
        if body.components
        else svc.CBSE_DEFAULT
    )
    scheme = svc.create(
        db, user.school_id, year_id, name=body.name, rows=rows, activate=body.activate
    )
    db.commit()
    return _out(db, scheme)


@router.put("/{scheme_id}/components")
def replace_components(
    scheme_id: int,
    body: list[ComponentIn],
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> dict:
    scheme = _owned(db, user, scheme_id)
    svc.set_components(
        db, scheme, [(c.code, c.name, c.term, c.max_marks) for c in body]
    )
    db.commit()
    return _out(db, scheme)


@router.post("/{scheme_id}/activate")
def activate(
    scheme_id: int, user: User = Depends(writer), db: Session = Depends(get_db)
) -> dict:
    scheme = svc.activate_scheme(db, _owned(db, user, scheme_id))
    db.commit()
    return _out(db, scheme)
