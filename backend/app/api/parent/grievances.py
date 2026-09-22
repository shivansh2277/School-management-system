from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
    prefix="/parent/grievances",
    tags=["parent-grievances"],
    dependencies=[Depends(module_enabled("grievances"))],
)

parent_only = require_permission("grievance.submit", "students.profile.read")


@router.get("", response_model=list[GrievanceOut])
def list_parent_grievances(
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> list[GrievanceOut]:
    items = db.scalars(
        select(Grievance)
        .where(
            Grievance.school_id == user.school_id,
            Grievance.raised_by_id == user.id,
        )
        .order_by(Grievance.created_at.desc())
    ).all()
    return [svc.to_out(g) for g in items]


@router.post("", response_model=GrievanceOut, status_code=status.HTTP_201_CREATED)
def create_parent_grievance(
    body: GrievanceCreate,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    if body.student_id:
        child_ids = scoping.child_ids_for(db, user)
        if body.student_id not in child_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student is not a recognized child of this guardian",
            )

    created = svc.create_grievance(
        db,
        user.school_id,
        user,
        body,
        role_override="parent",
    )
    return svc.to_out(created)


@router.get("/{id}", response_model=GrievanceOut)
def get_parent_grievance(
    id: int,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    g = db.scalar(
        select(Grievance).where(
            Grievance.id == id,
            Grievance.school_id == user.school_id,
            Grievance.raised_by_id == user.id,
        )
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found or not accessible",
        )
    return svc.to_out(g)


@router.post("/{id}/reply", response_model=GrievanceReplyOut)
def reply_parent_grievance(
    id: int,
    body: GrievanceReplyCreate,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> GrievanceReplyOut:
    g = db.scalar(
        select(Grievance).where(
            Grievance.id == id,
            Grievance.school_id == user.school_id,
            Grievance.raised_by_id == user.id,
        )
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found or not accessible",
        )
    reply = svc.add_reply(db, g, user, body, role_name="parent")
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
