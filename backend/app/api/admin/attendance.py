"""Absentee list, shortage view, holidays and leave approval (§5.8.3).

The roll sheet itself stays where teachers reach it; these are the office's
screens — who is missing today, who is heading for a shortage, and which leave
requests are waiting.
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    Holiday,
    LeaveStatus,
    StudentLeaveRequest,
    User,
)
from app.services import attendance as svc
from app.services import leave as leave_svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/attendance",
    tags=["attendance"],
    dependencies=[Depends(module_enabled("attendance"))],
)

reader = require_permission("attendance.record.read", school_wide=True)
corrector = require_permission("attendance.record.correct", school_wide=True)


class HolidayIn(BaseModel):
    model_config = {"extra": "forbid"}

    date: Date
    name: str
    academic_year_id: int | None = None


class LeaveDecision(BaseModel):
    model_config = {"extra": "forbid"}

    approve: bool
    note: str | None = Field(default=None, max_length=400)


@router.get("/absentees")
def absentees(
    date: Date | None = None,
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.absentees(db, user.school_id, date or Date.today(), class_section_id)


@router.get("/shortage")
def shortage(
    threshold: float = 75.0,
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.shortage(db, user.school_id, threshold, class_section_id)


@router.get("/holidays")
def holidays(
    year: int | None = None, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    q = select(Holiday).where(Holiday.school_id == user.school_id)
    if year is not None:
        q = q.where(Holiday.academic_year_id == year)
    return [
        {"id": h.id, "date": h.date, "name": h.name, "academic_year_id": h.academic_year_id}
        for h in db.scalars(q.order_by(Holiday.date))
    ]


@router.post("/holidays", status_code=201, dependencies=[Depends(corrector)])
def add_holiday(
    body: HolidayIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    year_id = body.academic_year_id
    if year_id is None:
        current = db.scalar(
            select(AcademicYear).where(
                AcademicYear.school_id == user.school_id, AcademicYear.is_current.is_(True)
            )
        )
        if current is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "No current academic year")
        year_id = current.id
    if db.scalar(
        select(Holiday).where(
            Holiday.academic_year_id == year_id, Holiday.date == body.date
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "That day is already a holiday")
    row = Holiday(
        school_id=user.school_id,
        academic_year_id=year_id,
        date=body.date,
        name=body.name,
    )
    db.add(row)
    db.commit()
    return {"id": row.id, "date": row.date, "name": row.name}


@router.get("/leave-requests")
def leave_requests(
    status_: LeaveStatus | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(StudentLeaveRequest).where(StudentLeaveRequest.school_id == user.school_id)
    if status_ is not None:
        q = q.where(StudentLeaveRequest.status == status_)
    return [
        leave_svc.to_out(db, r)
        for r in db.scalars(q.order_by(StudentLeaveRequest.from_date.desc()))
    ]


@router.post("/leave-requests/{request_id}/decide", dependencies=[Depends(corrector)])
def decide(
    request_id: int,
    body: LeaveDecision,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(StudentLeaveRequest, request_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave request not found")
    return leave_svc.to_out(db, leave_svc.decide(db, row, user, body.approve, body.note))
