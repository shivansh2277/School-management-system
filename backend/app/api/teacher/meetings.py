"""Teacher Mobile API: Visitor meeting slips addressed to the teacher."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Employee, User
from app.schemas.reception import TeacherMeetingOut, TeacherMeetingRespond
from app.services import reception as svc
from app.services import scoping
from app.services.rbac import require_permission

router = APIRouter(prefix="/teacher", tags=["teacher"])

can_view = require_permission("reception.meetings.respond_teacher")


@router.get("/meetings", response_model=list[TeacherMeetingOut], dependencies=[Depends(can_view)])
def list_my_meetings(
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[TeacherMeetingOut]:
    me: Employee = scoping.employee_for(db, user)
    return svc.list_teacher_meetings(db, user.school_id, teacher_id=me.id)


@router.post("/meetings/{meeting_id}/respond", response_model=TeacherMeetingOut, dependencies=[Depends(can_view)])
def respond_my_meeting(
    meeting_id: int,
    payload: TeacherMeetingRespond,
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> TeacherMeetingOut:
    me: Employee = scoping.employee_for(db, user)
    meeting = svc.get_teacher_meeting(db, user.school_id, meeting_id)
    if meeting.teacher_id != me.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot respond to meeting slips for other teachers")
    return svc.respond_teacher_meeting(db, user.school_id, user, meeting_id, payload.model_dump())
