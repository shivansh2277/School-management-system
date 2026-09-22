from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Grievance, User
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceOut,
    GrievanceReplyCreate,
    GrievanceReplyOut,
)
from app.services import grievance as svc
from app.services import scoping
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/teacher/grievances",
    tags=["teacher-grievances"],
    dependencies=[Depends(module_enabled("grievances"))],
)

teacher_access = require_permission("grievance.submit", "academics.class.read")


@router.get("", response_model=list[GrievanceOut])
def list_teacher_grievances(
    tab: str = Query("all", description="all, mine, assigned"),
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> list[GrievanceOut]:
    me = scoping.employee_for(db, user)
    base = select(Grievance).where(Grievance.school_id == user.school_id)

    if tab == "mine":
        base = base.where(Grievance.raised_by_id == user.id)
    elif tab == "assigned":
        base = base.where(Grievance.assigned_to_id == me.id)
    else:
        base = base.where(
            or_(
                Grievance.raised_by_id == user.id,
                Grievance.assigned_to_id == me.id,
            )
        )

    items = db.scalars(base.order_by(Grievance.created_at.desc())).all()
    return [svc.to_out(g) for g in items]


@router.post("", response_model=GrievanceOut, status_code=status.HTTP_201_CREATED)
def create_teacher_grievance(
    body: GrievanceCreate,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    created = svc.create_grievance(
        db,
        user.school_id,
        user,
        body,
        role_override="teacher",
    )
    return svc.to_out(created)


@router.get("/{id}", response_model=GrievanceOut)
def get_teacher_grievance(
    id: int,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    me = scoping.employee_for(db, user)
    g = db.scalar(
        select(Grievance).where(
            Grievance.id == id,
            Grievance.school_id == user.school_id,
            or_(
                Grievance.raised_by_id == user.id,
                Grievance.assigned_to_id == me.id,
            ),
        )
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found or not accessible",
        )
    return svc.to_out(g)


@router.post("/{id}/reply", response_model=GrievanceReplyOut)
def reply_teacher_grievance(
    id: int,
    body: GrievanceReplyCreate,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> GrievanceReplyOut:
    me = scoping.employee_for(db, user)
    g = db.scalar(
        select(Grievance).where(
            Grievance.id == id,
            Grievance.school_id == user.school_id,
            or_(
                Grievance.raised_by_id == user.id,
                Grievance.assigned_to_id == me.id,
            ),
        )
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found or not accessible",
        )
    reply = svc.add_reply(db, g, user, body, role_name="teacher")
    return GrievanceReplyOut(
        id=reply.id,
        grievance_id=reply.grievance_id,
        author_id=reply.author_id,
        author_name=reply.author_name,
        author_role=reply.author_role,
        message=reply.message,
        is_internal=reply.is_internal,
        created_at=reply.created_at,
    )
