"""Teacher Mobile API: Personal leave applications, leave status history, and assigned substitution duties."""

from datetime import date as Date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Employee,
    StaffLeaveRequest,
    Substitution,
    SubstitutionStatus,
    User,
)
from app.services import scoping
from app.services import staff_leave as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/teacher", tags=["teacher"])

can_apply = require_permission("teacher.leave.apply")
can_view = require_permission("teacher.leave.view")


class TeacherLeaveApplyRequest(BaseModel):
    from_date: Date
    to_date: Date
    reason: str = Field(..., min_length=1)
    is_half_day: bool = False


@router.post(
    "/leave/apply",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(can_apply)],
)
def apply_leave(
    body: TeacherLeaveApplyRequest,
    user: User = Depends(can_apply),
    db: Session = Depends(get_db),
) -> dict:
    me: Employee = scoping.employee_for(db, user)
    request = svc.apply_teacher_leave(
        db,
        me,
        from_date=body.from_date,
        to_date=body.to_date,
        reason=body.reason,
        is_half_day=body.is_half_day,
    )
    db.commit()
    return svc.to_out(db, request)


@router.get("/leave/history", dependencies=[Depends(can_view)])
def leave_history(
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[dict]:
    me: Employee = scoping.employee_for(db, user)
    rows = list(
        db.scalars(
            select(StaffLeaveRequest)
            .where(StaffLeaveRequest.employee_id == me.id)
            .order_by(StaffLeaveRequest.created_at.desc())
        )
    )
    return [svc.to_out(db, r) for r in rows]


@router.get("/substitutions/duties", dependencies=[Depends(can_view)])
def substitution_duties(
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[dict]:
    me: Employee = scoping.employee_for(db, user)
    today = Date.today()
    q = (
        select(Substitution)
        .where(
            Substitution.substitute_teacher_id == me.id,
            Substitution.date >= today,
            Substitution.status.in_((SubstitutionStatus.assigned, SubstitutionStatus.completed)),
        )
        .order_by(Substitution.date.asc())
    )
    items = []
    for sub in db.scalars(q):
        slot = sub.slot
        items.append(
            {
                "id": sub.id,
                "date": str(sub.date),
                "is_today": sub.date == today,
                "period_no": slot.period.period_no,
                "time": f"{slot.period.start_time:%H:%M} - {slot.period.end_time:%H:%M}",
                "class_section_id": slot.class_section_id,
                "class_label": slot.class_section.label,
                "subject_name": slot.subject.name if slot.subject else "",
                "room": slot.room,
                "absent_teacher_name": (
                    sub.absent_teacher.user.full_name
                    if sub.absent_teacher and sub.absent_teacher.user
                    else ""
                ),
                "reason": sub.reason,
                "status": sub.status.value,
            }
        )
    return items
