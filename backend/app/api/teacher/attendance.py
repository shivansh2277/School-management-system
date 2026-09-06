from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import User, UserRole
from app.schemas.common import AttendanceMarkRequest, RollRow
from app.services import attendance as svc
from app.services import scoping

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("attendance.record.read")


@router.get("/attendance", response_model=list[RollRow])
def roll_sheet(
    class_section_id: int,
    date: Date,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> list[RollRow]:
    scoping.assert_teaches_section(db, user, class_section_id)
    return svc.roll_sheet(db, class_section_id, date)


@router.post("/attendance", response_model=list[RollRow], dependencies=[Depends(require_permission("attendance.record.mark"))])
def mark(
    body: AttendanceMarkRequest,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> list[RollRow]:
    return svc.mark(db, user, body)
