from dataclasses import asdict
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    ClassSection,
    User,
)
from app.models.enums import AuditAction
from app.services import audit, promotion, tenancy
from app.services.common import class_sort_key, roster
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/promotion", tags=["admin-promotion"])

promoter = require_permission("students.enrolment.promote", school_wide=True)


class PromotionRequest(BaseModel):
    class_section_id: int
    to_year_id: int
    outcomes: dict[int, str] | None = None
    final_class: str = "12"
    reason: str | None = None


class AcademicYearOut(BaseModel):
    id: int
    code: str
    start_date: date
    end_date: date
    status: str
    is_current: bool
    is_writable: bool


class SectionSummaryOut(BaseModel):
    id: int
    class_name: str
    section: str
    label: str
    academic_year_id: int
    academic_year_code: str
    student_count: int


@router.get("/years", response_model=list[AcademicYearOut])
def list_academic_years(
    user: User = Depends(promoter),
    db: Session = Depends(get_db),
) -> list[dict]:
    years = db.scalars(
        select(AcademicYear)
        .where(AcademicYear.school_id == user.school_id)
        .order_by(AcademicYear.start_date.desc())
    ).all()
    return [
        {
            "id": y.id,
            "code": y.code,
            "start_date": y.start_date,
            "end_date": y.end_date,
            "status": y.status.value if hasattr(y.status, "value") else str(y.status),
            "is_current": y.is_current,
            "is_writable": y.is_writable,
        }
        for y in years
    ]


@router.get("/sections", response_model=list[SectionSummaryOut])
def list_sections(
    academic_year_id: int | None = Query(None),
    user: User = Depends(promoter),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(ClassSection).where(ClassSection.school_id == user.school_id)
    if academic_year_id is not None:
        query = query.where(ClassSection.academic_year_id == academic_year_id)
    sections = db.scalars(query).all()

    years_map = {
        y.id: y.code
        for y in db.scalars(
            select(AcademicYear).where(AcademicYear.school_id == user.school_id)
        ).all()
    }

    sorted_sections = sorted(
        sections,
        key=lambda s: (*class_sort_key(s.class_name), s.section),
    )
    return [
        {
            "id": s.id,
            "class_name": s.class_name,
            "section": s.section,
            "label": s.label,
            "academic_year_id": s.academic_year_id,
            "academic_year_code": years_map.get(s.academic_year_id, ""),
            "student_count": len(roster(db, s.id)),
        }
        for s in sorted_sections
    ]


@router.post("/preview")
def preview_promotion(
    body: PromotionRequest,
    user: User = Depends(promoter),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    section = tenancy.get_owned(db, ClassSection, body.class_section_id, user, what="Class section")
    to_year = tenancy.get_owned(db, AcademicYear, body.to_year_id, user, what="Academic year")

    plan = promotion.preview(
        db=db,
        class_section_id=section.id,
        to_year_id=to_year.id,
        outcomes=body.outcomes,
        final_class=body.final_class,
    )
    res = asdict(plan)
    res["can_commit"] = plan.can_commit
    return res


@router.post("/commit")
def commit_promotion(
    body: PromotionRequest,
    user: User = Depends(promoter),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    section = tenancy.get_owned(db, ClassSection, body.class_section_id, user, what="Class section")
    to_year = tenancy.get_owned(db, AcademicYear, body.to_year_id, user, what="Academic year")

    plan = promotion.commit(
        db=db,
        class_section_id=section.id,
        to_year_id=to_year.id,
        outcomes=body.outcomes,
        final_class=body.final_class,
    )

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="enrolment",
        entity_id=section.id,
        action=AuditAction.update,
        reason=body.reason or f"Promoted section {plan.from_section} to {plan.to_year}",
    )
    db.commit()

    res = asdict(plan)
    res["can_commit"] = plan.can_commit
    return res
