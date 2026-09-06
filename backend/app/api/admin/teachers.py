from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.core.security import hash_password
from app.models import ClassSection, ClassSubjectTeacher, Teacher, User, UserRole
from app.services.common import section_labels, subject_names

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_permission("hr.employee.read", school_wide=True)


class TeacherCreate(BaseModel):
    full_name: str
    employee_id: str
    qualification: str | None = None
    joining_date: Date | None = None
    email: str | None = None
    phone: str | None = None
    password: str = "Teacher@123"


class TeacherUpdate(BaseModel):
    full_name: str | None = None
    qualification: str | None = None
    email: str | None = None
    phone: str | None = None


def _row(db: Session, t: Teacher) -> dict:
    labels = section_labels(db)
    subjects = subject_names(db)
    owned = db.scalars(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == t.id)
    ).all()
    class_of = db.scalars(
        select(ClassSection).where(ClassSection.class_teacher_id == t.id)
    ).all()
    return {
        "id": t.id,
        "employee_id": t.employee_id,
        "full_name": t.user.full_name,
        "qualification": t.qualification,
        "joining_date": t.joining_date,
        "email": t.user.email,
        "phone": t.user.phone,
        "is_active": t.user.is_active,
        "subjects": sorted({subjects[o.subject_id] for o in owned}),
        "sections": sorted({labels[o.class_section_id] for o in owned}),
        "class_teacher_of": [c.label for c in class_of],
    }


@router.get("/teachers")
def list_teachers(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    return [
        _row(db, t) for t in db.scalars(select(Teacher).order_by(Teacher.employee_id))
    ]


@router.post("/teachers", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("hr.employee.write"))])
def create_teacher(
    body: TeacherCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    if db.scalar(select(User).where(User.login_id == body.employee_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Employee id already exists")
    u = User(
        role=UserRole.teacher,
        school_id=user.school_id,
        login_id=body.employee_id,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
    )
    db.add(u)
    db.flush()
    t = Teacher(
        school_id=user.school_id,
        user_id=u.id,
        employee_id=body.employee_id,
        qualification=body.qualification,
        joining_date=body.joining_date or Date.today(),
    )
    db.add(t)
    db.commit()
    return _row(db, t)


@router.patch("/teachers/{teacher_id}", dependencies=[Depends(require_permission("hr.employee.write"))])
def update_teacher(
    teacher_id: int,
    body: TeacherUpdate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    t = db.get(Teacher, teacher_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    if body.qualification is not None:
        t.qualification = body.qualification
    for field in ("full_name", "email", "phone"):
        value = getattr(body, field)
        if value is not None:
            setattr(t.user, field, value)
    db.commit()
    return _row(db, t)


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("hr.employee.write"))])
def deactivate_teacher(
    teacher_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> Response:
    t = db.get(Teacher, teacher_id)
    if t is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    t.user.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
