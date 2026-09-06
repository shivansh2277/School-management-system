"""Admission dashboard and reports (screens 1 and 18 of §5.1.3)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.services import admission
from app.services import admission_reports as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)


@router.get("/cycles/{cycle_id}/dashboard")
def dashboard(
    cycle_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    admission.cycle_for(db, user.school_id, cycle_id)
    return svc.dashboard(db, user.school_id, cycle_id)


@router.get("/cycles/{cycle_id}/reports")
def reports(
    cycle_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """§5.1.10, computed on read. A stored funnel disagrees with the register
    the first time somebody corrects a status."""
    admission.cycle_for(db, user.school_id, cycle_id)
    return {
        "funnel": svc.funnel(db, user.school_id, cycle_id),
        "by_source": svc.by_source(db, user.school_id, cycle_id),
        "seat_utilisation": svc.seat_utilisation(db, user.school_id, cycle_id),
        "demographics": svc.demographics(db, user.school_id, cycle_id),
        "rejections": svc.rejections(db, user.school_id, cycle_id),
        "cycle_time": svc.cycle_time(db, user.school_id, cycle_id),
    }
