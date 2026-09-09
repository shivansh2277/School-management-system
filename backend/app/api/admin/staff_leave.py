"""Staff leave: types, balances, applications and the approval queue (§5.3.3).

Approval returns the substitutions it raised rather than a bare status. §5.3.9
wants approving leave to *surface* the affected periods, and a response that
says "approved" and nothing else is exactly the silence the rule is about.
"""

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LeaveStatus, StaffLeaveRequest, User
from app.core.db import get_db
from app.services import hr
from app.services import staff_leave as svc
from app.services import tenancy
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled
from app.services.timetable import slot_out

router = APIRouter(
    prefix="/admin/staff-leave", tags=["admin"],
    dependencies=[Depends(module_enabled("hr"))],
)
reader = require_permission("hr.leave.read", school_wide=True)
applier = require_permission("hr.leave.apply", school_wide=True)
approver = require_permission("hr.leave.approve", school_wide=True)
type_writer = require_permission("hr.leave.configure", school_wide=True)


class LeaveTypeIn(BaseModel):
    code: str = Field(min_length=1, max_length=12)
    name: str = Field(min_length=1, max_length=60)
    annual_quota: Decimal = Field(ge=0)
    is_paid: bool = True


class ApplyIn(BaseModel):
    employee_id: int
    leave_type_id: int
    from_date: Date
    to_date: Date
    reason: str = Field(min_length=3, max_length=1000)
    is_half_day: bool = False


class DecisionIn(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
    # §5.3.9 allows approving past the balance only as an explicit exception.
    allow_exception: bool = False


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


def _owned(db: Session, user: User, request_id: int) -> StaffLeaveRequest:
    row = db.get(StaffLeaveRequest, request_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave request not found")
    return row


# --- configuration ---------------------------------------------------------


@router.get("/types")
def list_types(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "annual_quota": t.annual_quota,
            "is_paid": t.is_paid,
        }
        for t in svc.types_for(db, user.school_id)
    ]


@router.post("/types", status_code=status.HTTP_201_CREATED)
def create_type(
    body: LeaveTypeIn, user: User = Depends(type_writer), db: Session = Depends(get_db)
) -> dict:
    row = svc.create_type(
        db,
        user.school_id,
        code=body.code,
        name=body.name,
        annual_quota=body.annual_quota,
        is_paid=body.is_paid,
    )
    db.commit()
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "annual_quota": row.annual_quota,
        "is_paid": row.is_paid,
    }


@router.get("/balances/{employee_id}")
def balances(
    employee_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    employee = hr.owned(db, user, employee_id)
    year = tenancy.current_year(db, user.school_id)
    rows = svc.balances_for(db, employee, year.id)
    db.commit()
    return [
        {
            "leave_type": b.leave_type.code,
            "leave_type_name": b.leave_type.name,
            "entitled": b.entitled,
            "used": b.used,
            "remaining": b.remaining,
        }
        for b in rows
    ]


# --- requests --------------------------------------------------------------


@router.get("")
def list_requests(
    employee_id: int | None = None,
    request_status: LeaveStatus | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(StaffLeaveRequest).where(StaffLeaveRequest.school_id == user.school_id)
    if employee_id is not None:
        q = q.where(StaffLeaveRequest.employee_id == employee_id)
    if request_status is not None:
        q = q.where(StaffLeaveRequest.status == request_status)
    return [
        svc.to_out(db, r)
        for r in db.scalars(q.order_by(StaffLeaveRequest.from_date.desc()))
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def apply(
    body: ApplyIn, user: User = Depends(applier), db: Session = Depends(get_db)
) -> dict:
    employee = hr.owned(db, user, body.employee_id)
    year = tenancy.current_year(db, user.school_id)
    row = svc.apply_for(
        db,
        employee,
        leave_type_id=body.leave_type_id,
        academic_year_id=year.id,
        from_date=body.from_date,
        to_date=body.to_date,
        reason=body.reason,
        is_half_day=body.is_half_day,
    )
    db.commit()
    return svc.to_out(db, row)


@router.get("/{request_id}/affected-periods")
def affected(
    request_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """What this leave would leave uncovered, before it is approved."""
    row = _owned(db, user, request_id)
    return [
        {"date": day, **slot_out(db, slot)} for day, slot in svc.affected_periods(db, row)
    ]


@router.post("/{request_id}/approve")
def approve(
    request_id: int,
    body: DecisionIn,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    result = svc.approve(
        db,
        user,
        _owned(db, user, request_id),
        note=body.note,
        allow_exception=body.allow_exception,
    )
    db.commit()
    return {
        **svc.to_out(db, result["request"]),
        # The point of §5.3.9: approval surfaces the classes now uncovered.
        "substitutions_raised": [
            {
                "id": s.id,
                "date": s.date,
                "class_label": s.slot.class_section.label,
                "period": s.slot.period.period_no,
                "substitute_teacher_id": s.substitute_teacher_id,
                "status": s.status,
            }
            for s in result["substitutions"]
        ],
    }


@router.post("/{request_id}/reject")
def reject(
    request_id: int,
    body: ReasonIn,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.reject(db, user, _owned(db, user, request_id), reason=body.reason)
    db.commit()
    return svc.to_out(db, row)


@router.post("/{request_id}/cancel")
def cancel(
    request_id: int,
    body: ReasonIn,
    user: User = Depends(applier),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.cancel(db, user, _owned(db, user, request_id), reason=body.reason)
    db.commit()
    return svc.to_out(db, row)
