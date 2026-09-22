from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Employee, Grievance, User
from app.schemas.grievance import (
    GrievanceAssign,
    GrievanceOut,
    GrievanceReplyCreate,
    GrievanceReplyOut,
    GrievanceStatsOut,
    GrievanceStatusUpdate,
)
from app.services import grievance as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/grievances",
    tags=["admin-grievances"],
    dependencies=[Depends(module_enabled("grievances"))],
)

reader = require_permission("grievance.read", school_wide=True)
writer = require_permission("grievance.write", school_wide=True)
assigner = require_permission("grievance.assign", school_wide=True)


@router.get("/stats", response_model=GrievanceStatsOut)
def get_stats(
    user: User = Depends(reader), db: Session = Depends(get_db)
) -> GrievanceStatsOut:
    return svc.get_stats(db, user.school_id)


@router.get("/staff")
def list_staff_assignees(
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Staff members available for grievance assignment."""
    employees = db.scalars(
        select(Employee)
        .where(Employee.school_id == user.school_id)
        .order_by(Employee.employee_code)
    ).all()
    return [
        {
            "id": e.id,
            "employee_code": e.employee_code,
            "full_name": e.user.full_name if e.user else e.employee_code,
            "employee_type": e.employee_type.value if hasattr(e.employee_type, "value") else str(e.employee_type),
        }
        for e in employees
    ]


@router.get("", response_model=list[GrievanceOut])
def list_grievances(
    status: str | None = None,
    role: str | None = None,
    category: str | None = None,
    search: str | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[GrievanceOut]:
    q = select(Grievance).where(Grievance.school_id == user.school_id)
    if status:
        q = q.where(Grievance.status == status)
    if role:
        q = q.where(Grievance.raised_by_role == role)
    if category:
        q = q.where(Grievance.category == category)
    if search:
        term = f"%{search.strip()}%"
        q = q.where(
            or_(
                Grievance.title.ilike(term),
                Grievance.description.ilike(term),
                Grievance.raised_by_name.ilike(term),
                Grievance.student_name.ilike(term),
            )
        )
    items = db.scalars(q.order_by(Grievance.created_at.desc())).all()
    return [svc.to_out(g) for g in items]


@router.get("/{id}", response_model=GrievanceOut)
def get_grievance(
    id: int,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    g = db.scalar(
        select(Grievance).where(Grievance.id == id, Grievance.school_id == user.school_id)
    )
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    return svc.to_out(g)


@router.post("/{id}/reply", response_model=GrievanceReplyOut)
def reply_grievance(
    id: int,
    body: GrievanceReplyCreate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> GrievanceReplyOut:
    g = db.scalar(
        select(Grievance).where(Grievance.id == id, Grievance.school_id == user.school_id)
    )
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    reply = svc.add_reply(db, g, user, body, role_name="admin")
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


@router.post("/{id}/assign", response_model=GrievanceOut)
def assign_grievance(
    id: int,
    body: GrievanceAssign,
    user: User = Depends(assigner),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    g = db.scalar(
        select(Grievance).where(Grievance.id == id, Grievance.school_id == user.school_id)
    )
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    updated = svc.assign_to_teacher(db, g, body.assigned_to_id)
    return svc.to_out(updated)


@router.patch("/{id}/status", response_model=GrievanceOut)
def update_grievance_status(
    id: int,
    body: GrievanceStatusUpdate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> GrievanceOut:
    g = db.scalar(
        select(Grievance).where(Grievance.id == id, Grievance.school_id == user.school_id)
    )
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    updated = svc.update_status(db, g, body.status, body.resolution_notes)
    return svc.to_out(updated)
