"""Service layer for Grievances & Feedback.

Enforces multi-tenant isolation, user scoping, teacher assignment, status transitions,
and conversation reply tracking.
"""
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employee, Grievance, GrievanceReply, Student, User
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceOut,
    GrievanceReplyCreate,
    GrievanceReplyOut,
    GrievanceStatsOut,
)


def create_grievance(
    db: Session,
    school_id: int,
    user: User,
    data: GrievanceCreate,
    role_override: str | None = None,
) -> Grievance:
    role = role_override or getattr(user.role, "value", str(user.role))
    student_name: str | None = None
    if data.student_id:
        student = db.scalar(
            select(Student).where(
                Student.id == data.student_id,
                Student.school_id == school_id,
            )
        )
        if student and student.user:
            student_name = student.user.full_name

    item = Grievance(
        school_id=school_id,
        title=data.title.strip(),
        description=data.description.strip(),
        category=data.category or "general",
        raised_by_id=user.id,
        raised_by_role=role,
        raised_by_name=user.full_name,
        student_id=data.student_id,
        student_name=student_name,
        status="open",
        priority=data.priority,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_reply(
    db: Session,
    grievance: Grievance,
    author: User,
    data: GrievanceReplyCreate,
    role_name: str | None = None,
) -> GrievanceReply:
    role = role_name or getattr(author.role, "value", str(author.role))
    reply = GrievanceReply(
        school_id=grievance.school_id,
        grievance_id=grievance.id,
        author_id=author.id,
        author_name=author.full_name,
        author_role=role,
        message=data.message.strip(),
        is_internal=data.is_internal,
    )
    db.add(reply)
    if grievance.status == "open" and role in ("admin", "super_admin", "principal", "teacher"):
        grievance.status = "in_progress"
    db.commit()
    db.refresh(reply)
    return reply


def assign_to_teacher(
    db: Session,
    grievance: Grievance,
    employee_id: int,
) -> Grievance:
    emp = db.scalar(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.school_id == grievance.school_id,
        )
    )
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found in this school",
        )

    grievance.assigned_to_id = emp.id
    grievance.assigned_to_name = emp.user.full_name
    if grievance.status == "open":
        grievance.status = "in_progress"
    db.commit()
    db.refresh(grievance)
    return grievance


def update_status(
    db: Session,
    grievance: Grievance,
    new_status: str,
    resolution_notes: str | None = None,
) -> Grievance:
    grievance.status = new_status
    if resolution_notes:
        grievance.resolution_notes = resolution_notes
    if new_status in ("resolved", "closed"):
        grievance.resolved_at = datetime.now(UTC)
    db.commit()
    db.refresh(grievance)
    return grievance


def get_stats(db: Session, school_id: int) -> GrievanceStatsOut:
    base = select(Grievance).where(Grievance.school_id == school_id)
    all_items = db.scalars(base).all()

    total_count = len(all_items)
    open_count = sum(1 for g in all_items if g.status == "open")
    in_progress_count = sum(1 for g in all_items if g.status == "in_progress")
    resolved_count = sum(1 for g in all_items if g.status in ("resolved", "closed"))
    teacher_count = sum(1 for g in all_items if g.raised_by_role == "teacher")
    parent_count = sum(1 for g in all_items if g.raised_by_role in ("parent", "guardian"))

    return GrievanceStatsOut(
        total_count=total_count,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        teacher_count=teacher_count,
        parent_count=parent_count,
    )


def to_out(g: Grievance) -> GrievanceOut:
    return GrievanceOut(
        id=g.id,
        school_id=g.school_id,
        title=g.title,
        description=g.description,
        category=g.category,
        raised_by_id=g.raised_by_id,
        raised_by_role=g.raised_by_role,
        raised_by_name=g.raised_by_name,
        student_id=g.student_id,
        student_name=g.student_name,
        status=g.status,
        priority=g.priority,
        assigned_to_id=g.assigned_to_id,
        assigned_to_name=g.assigned_to_name,
        resolution_notes=g.resolution_notes,
        resolved_at=g.resolved_at,
        created_at=g.created_at,
        replies_count=len(g.replies) if g.replies else 0,
        replies=[
            GrievanceReplyOut(
                id=r.id,
                grievance_id=r.grievance_id,
                author_id=r.author_id,
                author_name=r.author_name,
                author_role=r.author_role,
                message=r.message,
                is_internal=r.is_internal,
                created_at=r.created_at,
            )
            for r in (g.replies or [])
        ],
    )
