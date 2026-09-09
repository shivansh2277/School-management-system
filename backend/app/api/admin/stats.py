from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from pydantic import BaseModel

from app.models import Notice, User
from app.services import notices as notice_svc
from app.services import stats as svc
from app.services import tenancy

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_permission("admin.settings.read", school_wide=True)


@router.get("/dashboard/stats")
def dashboard_stats(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    year = tenancy.current_year(db, user.school_id)
    school_id = user.school_id
    recent = list(
        db.scalars(
            select(Notice)
            .where(Notice.school_id == school_id)
            .order_by(Notice.published_at.desc())
            .limit(5)
        )
    )
    return {
        "totals": svc.totals(db, year),
        "attendance": svc.month_attendance(db, school_id),
        "performance": svc.performance(db, school_id),
        "top_performers": svc.top_performers(db, school_id),
        "recent_notices": notice_svc.to_out(db, recent),
        "today_schedule": svc.today_schedule(db, school_id),
        "fee_trend": svc.fee_trend(db, school_id),
    }


class SettingsUpdate(BaseModel):
    """Replaces the bare `dict` this endpoint used to accept: an admin write
    with no validation was a recorded defect, and settings now drive billing
    and branding for a whole tenant."""

    model_config = {"extra": "forbid"}

    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    board: str | None = None
    affiliation_no: str | None = None


@router.get("/settings")
def get_settings(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    school = tenancy.school_for(db, user)
    return {
        "name": school.name,
        "address": school.address,
        "city": school.city,
        "phone": school.phone,
        "email": school.email,
        "logo_url": school.logo_url,
        "primary_color": school.primary_color,
        "board": school.board,
        # The session is no longer a settings string; it is the school's
        # current AcademicYear row (ERP_BLUEPRINT §3.1).
        "academic_year": tenancy.current_year(db, user.school_id).code,
    }


@router.patch("/settings", dependencies=[Depends(require_permission("admin.settings.write"))])
def update_settings(
    body: SettingsUpdate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    school = tenancy.school_for(db, user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(school, field, value)
    db.commit()
    return get_settings(user, db)


@router.get("/grade-bands")
def grade_bands(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    from app.models import GradeBand

    return [
        {"id": g.id, "min_percent": g.min_percent, "grade": g.grade}
        for g in db.scalars(
            select(GradeBand)
            .where(GradeBand.school_id == user.school_id)
            .order_by(GradeBand.min_percent.desc())
        )
    ]
