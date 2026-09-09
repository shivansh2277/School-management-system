"""The staff register (§5.3.3), and the month a payslip is computed from."""

from datetime import date as Date, time

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import AttendanceStatus, User
from app.services import hr
from app.services import staff_attendance as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/staff-attendance", tags=["admin"],
    dependencies=[Depends(module_enabled("hr"))],
)
reader = require_permission("hr.attendance.read", school_wide=True)
marker = require_permission("hr.attendance.mark", school_wide=True)


class MarkEntry(BaseModel):
    employee_id: int
    status: AttendanceStatus
    check_in: time | None = None
    check_out: time | None = None
    remarks: str | None = Field(default=None, max_length=200)


class MarkRequest(BaseModel):
    date: Date
    entries: list[MarkEntry]
    # Required only to change an earlier day's mark: that is a correction to a
    # record, not a fix to an open register.
    reason: str | None = None


@router.get("")
def roll(
    date: Date, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """Everyone in service, marked or not — a register that lists only the
    people somebody remembered to mark is not a register."""
    return svc.roll(db, user.school_id, date)


@router.post("", status_code=status.HTTP_200_OK)
def mark(
    body: MarkRequest, user: User = Depends(marker), db: Session = Depends(get_db)
) -> list[dict]:
    rows = svc.mark(
        db,
        user,
        on=body.date,
        entries=[e.model_dump() for e in body.entries],
        reason=body.reason,
    )
    db.commit()
    return rows


@router.get("/summary/{employee_id}")
def summary(
    employee_id: int,
    date_from: Date = Query(alias="from"),
    date_to: Date = Query(alias="to"),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Working days, what was marked, and the loss-of-pay days payroll uses."""
    return svc.summary(db, hr.owned(db, user, employee_id), date_from, date_to)
