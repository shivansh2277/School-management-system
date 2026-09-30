"""Teacher Mobile API: Personal leave applications, leave status history, and assigned substitution duties."""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Employee,
    LeaveStatus,
    StaffLeaveRequest,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import scoping
from app.services import staff_leave as svc
from app.services.notifications import notify_user
from app.services.rbac import require_permission

router = APIRouter(prefix="/teacher", tags=["teacher"])

can_apply = require_permission("teacher.leave.apply")
can_view = require_permission("teacher.leave.view")


class PeriodSubstitutionItem(BaseModel):
    slot_id: int
    date: Date
    substitute_teacher_id: int


class TeacherLeaveApplyRequest(BaseModel):
    leave_type_id: int | None = None
    from_date: Date
    to_date: Date
    reason: str = Field(..., min_length=1)
    is_half_day: bool = False
    half_day_period: str | None = None
    substitutions: list[PeriodSubstitutionItem] = Field(default_factory=list)


class LeaveInspectRequest(BaseModel):
    from_date: Date
    to_date: Date
    is_half_day: bool = False
    half_day_period: str | None = None


from typing import Literal


class SubstitutionRespondRequest(BaseModel):
    action: Literal["accept", "reject"]
    reason: str | None = None


class SubstitutionReassignRequest(BaseModel):
    slot_id: int
    date: Date
    new_substitute_teacher_id: int


@router.get("/leave/types", dependencies=[Depends(can_view)])
def leave_types(
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Active staff leave types configured for the school."""
    types = svc.types_for(db, user.school_id)
    return [
        {
            "id": t.id,
            "code": t.code,
            "name": t.name,
            "annual_quota": float(t.annual_quota),
            "is_paid": t.is_paid,
            "is_casual": svc.is_casual_leave(t),
        }
        for t in types
    ]


@router.post("/leave/inspect", dependencies=[Depends(can_apply)])
def inspect_leave(
    body: LeaveInspectRequest,
    user: User = Depends(can_apply),
    db: Session = Depends(get_db),
) -> dict:
    """Inspects affected timetable periods across dates and suggests ranked substitutes."""
    me: Employee = scoping.employee_for(db, user)
    return svc.inspect_affected_periods(
        db,
        me,
        from_date=body.from_date,
        to_date=body.to_date,
        is_half_day=body.is_half_day,
        half_day_period=body.half_day_period,
    )


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
    sub_dicts = [s.model_dump() for s in body.substitutions]
    request = svc.apply_teacher_leave(
        db,
        me,
        from_date=body.from_date,
        to_date=body.to_date,
        reason=body.reason,
        is_half_day=body.is_half_day,
        half_day_period=body.half_day_period,
        leave_type_id=body.leave_type_id,
        substitutions=sub_dicts,
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


@router.get("/leave/applications/{application_id}/substitutions", dependencies=[Depends(can_view)])
def leave_application_substitutions(
    application_id: int,
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> dict:
    """Returns substitution status for every period in a leave application."""
    me: Employee = scoping.employee_for(db, user)
    req = db.get(StaffLeaveRequest, application_id)
    if req is None or req.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")
    if req.employee_id != me.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to view this leave application")

    periods = svc.affected_periods(db, req)
    out_periods = []
    for day, slot in periods:
        sub = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id,
                Substitution.date == day,
                Substitution.leave_request_id == req.id,
            )
        )
        if sub is None:
            sub = db.scalar(
                select(Substitution).where(
                    Substitution.timetable_slot_id == slot.id,
                    Substitution.date == day,
                )
            )

        sub_status = sub.status.value if sub else "unassigned"
        ranked = []
        if sub is None or sub.status == SubstitutionStatus.rejected:
            ranked = svc.ranked_substitutes_for_slot(db, user.school_id, slot, day, me.id)

        out_periods.append(
            {
                "date": str(day),
                "slot_id": slot.id,
                "period_id": slot.period_id,
                "period_no": slot.period.period_no,
                "time": f"{slot.period.start_time:%H:%M} - {slot.period.end_time:%H:%M}",
                "class_section_id": slot.class_section_id,
                "class_label": slot.class_section.label if slot.class_section else "",
                "subject_id": slot.subject_id,
                "subject_name": slot.subject.name if slot.subject else "",
                "room": slot.room,
                "substitution_id": sub.id if sub else None,
                "substitute_teacher_id": sub.substitute_teacher_id if sub else None,
                "substitute_teacher_name": (
                    sub.substitute_teacher.user.full_name
                    if sub and sub.substitute_teacher and sub.substitute_teacher.user
                    else None
                ),
                "status": sub_status,
                "can_reassign": (
                    req.status == LeaveStatus.applied
                    and (sub is None or sub.status in (SubstitutionStatus.pending, SubstitutionStatus.rejected))
                ),
                "ranked_substitutes": ranked,
            }
        )

    is_fully_accepted = (
        len(out_periods) > 0
        and all(p["status"] in ("assigned", "completed") for p in out_periods)
    )

    return {
        "leave_request_id": req.id,
        "status": req.status.value,
        "leave_type_name": req.leave_type.name if req.leave_type else "Teacher Leave",
        "from_date": str(req.from_date),
        "to_date": str(req.to_date),
        "days": float(req.days),
        "is_fully_accepted": is_fully_accepted,
        "total_periods": len(out_periods),
        "periods": out_periods,
    }


@router.post("/leave/applications/{application_id}/reassign", dependencies=[Depends(can_apply)])
def reassign_substitute(
    application_id: int,
    body: SubstitutionReassignRequest,
    user: User = Depends(can_apply),
    db: Session = Depends(get_db),
) -> dict:
    """Reassigns a rejected or pending period to another substitute teacher."""
    me: Employee = scoping.employee_for(db, user)
    req = db.get(StaffLeaveRequest, application_id)
    if req is None or req.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")
    if req.employee_id != me.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to modify this leave application")
    if req.status != LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot reassign substitutions for a leave in {req.status.value} status",
        )

    if body.new_substitute_teacher_id == me.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cannot assign yourself as substitute")

    new_sub_emp = db.get(Employee, body.new_substitute_teacher_id)
    if new_sub_emp is None or new_sub_emp.school_id != user.school_id or not new_sub_emp.in_service:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Substitute teacher not found or not in service")

    slot = db.get(TimetableSlot, body.slot_id)
    if slot is None or slot.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")

    sub = db.scalar(
        select(Substitution).where(
            Substitution.timetable_slot_id == slot.id,
            Substitution.date == body.date,
            Substitution.leave_request_id == req.id,
        )
    )
    if sub is None:
        sub = Substitution(
            school_id=user.school_id,
            timetable_slot_id=slot.id,
            date=body.date,
            absent_teacher_id=me.id,
            substitute_teacher_id=new_sub_emp.id,
            leave_request_id=req.id,
            reason=f"Cover for {user.full_name} (Reassigned)",
            status=SubstitutionStatus.pending,
        )
        db.add(sub)
    else:
        sub.substitute_teacher_id = new_sub_emp.id
        sub.status = SubstitutionStatus.pending
        sub.reason = f"Cover for {user.full_name} (Reassigned)"

    if new_sub_emp.user_id:
        notify_user(
            db,
            school_id=user.school_id,
            user_id=new_sub_emp.user_id,
            title="Substitution Request",
            message=(
                f"{user.full_name} has requested you to cover "
                f"{slot.class_section.label if slot.class_section else ''} "
                f"(Period {slot.period.period_no}, {slot.period.start_time:%H:%M}-{slot.period.end_time:%H:%M}) "
                f"on {body.date}."
            ),
            category="substitution_request",
        )

    db.commit()
    return {
        "id": sub.id,
        "slot_id": slot.id,
        "date": str(body.date),
        "substitute_teacher_id": new_sub_emp.id,
        "status": sub.status.value,
    }


@router.get("/substitutions/requests", dependencies=[Depends(can_view)])
@router.get("/substitutions/pending", dependencies=[Depends(can_view)])
def pending_substitution_requests(
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Pending substitution requests awaiting current teacher's accept or reject."""
    me: Employee = scoping.employee_for(db, user)
    today = Date.today()
    q = (
        select(Substitution)
        .where(
            Substitution.substitute_teacher_id == me.id,
            Substitution.date >= today,
            Substitution.status == SubstitutionStatus.pending,
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
                "slot_id": slot.id,
                "period_no": slot.period.period_no,
                "start_time": f"{slot.period.start_time:%H:%M}",
                "end_time": f"{slot.period.end_time:%H:%M}",
                "time": f"{slot.period.start_time:%H:%M} - {slot.period.end_time:%H:%M}",
                "class_section_id": slot.class_section_id,
                "class_label": slot.class_section.label if slot.class_section else "",
                "subject_name": slot.subject.name if slot.subject else "",
                "room": slot.room,
                "absent_teacher_id": sub.absent_teacher_id,
                "absent_teacher_name": (
                    sub.absent_teacher.user.full_name
                    if sub.absent_teacher and sub.absent_teacher.user
                    else ""
                ),
                "leave_request_id": sub.leave_request_id,
                "reason": sub.reason,
                "status": sub.status.value,
            }
        )
    return items


@router.post("/substitutions/{substitution_id}/respond", dependencies=[Depends(can_view)])
def respond_substitution(
    substitution_id: int,
    body: SubstitutionRespondRequest,
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> dict:
    """Accept or reject a pending substitution request."""
    me: Employee = scoping.employee_for(db, user)
    sub = db.get(Substitution, substitution_id)
    if sub is None or sub.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Substitution not found")
    if sub.substitute_teacher_id != me.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This substitution request is not addressed to you")
    if sub.status != SubstitutionStatus.pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Substitution request has already been {sub.status.value}",
        )

    slot = sub.slot
    absent_user_id = sub.absent_teacher.user_id if sub.absent_teacher else None

    if body.action == "accept":
        sub.status = SubstitutionStatus.assigned
        if absent_user_id:
            notify_user(
                db,
                school_id=user.school_id,
                user_id=absent_user_id,
                title="Substitution Accepted",
                message=(
                    f"{user.full_name} accepted your substitution request for "
                    f"{slot.class_section.label if slot.class_section else ''} "
                    f"(Period {slot.period.period_no}) on {sub.date}."
                ),
                category="substitution_update",
            )
    else:
        sub.status = SubstitutionStatus.rejected
        if absent_user_id:
            rej_reason = f" Reason: {body.reason.strip()}." if body.reason and body.reason.strip() else ""
            notify_user(
                db,
                school_id=user.school_id,
                user_id=absent_user_id,
                title="Substitution Declined",
                message=(
                    f"{user.full_name} declined your substitution request for "
                    f"{slot.class_section.label if slot.class_section else ''} "
                    f"(Period {slot.period.period_no}) on {sub.date}.{rej_reason} "
                    f"Please select another substitute."
                ),
                category="substitution_update",
            )

    db.commit()
    return {"id": sub.id, "status": sub.status.value}


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

