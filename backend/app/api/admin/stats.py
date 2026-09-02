from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import Notice, SchoolSettings, User, UserRole
from app.services import notices as notice_svc
from app.services import stats as svc

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(UserRole.admin)


@router.get("/dashboard/stats")
def dashboard_stats(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    school = db.get(SchoolSettings, 1)
    academic_year = school.academic_year if school else ""
    recent = list(db.scalars(select(Notice).order_by(Notice.published_at.desc()).limit(5)))
    return {
        "totals": svc.totals(db, academic_year),
        "attendance": svc.month_attendance(db),
        "performance": svc.performance(db),
        "top_performers": svc.top_performers(db),
        "recent_notices": notice_svc.to_out(db, recent),
        "today_schedule": svc.today_schedule(db),
        "fee_trend": svc.fee_trend(db),
    }


@router.get("/settings")
def get_settings(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    school = db.get(SchoolSettings, 1)
    return {
        "name": school.name,
        "address": school.address,
        "city": school.city,
        "phone": school.phone,
        "email": school.email,
        "logo_url": school.logo_url,
        "primary_color": school.primary_color,
        "academic_year": school.academic_year,
    }


@router.patch("/settings")
def update_settings(
    body: dict, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    school = db.get(SchoolSettings, 1)
    for field in (
        "name", "address", "city", "phone", "email", "logo_url",
        "primary_color", "academic_year",
    ):
        if field in body:
            setattr(school, field, body[field])
    db.commit()
    return get_settings(user, db)


@router.get("/grade-bands")
def grade_bands(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    from app.models import GradeBand

    return [
        {"id": g.id, "min_percent": g.min_percent, "grade": g.grade}
        for g in db.scalars(select(GradeBand).order_by(GradeBand.min_percent.desc()))
    ]
