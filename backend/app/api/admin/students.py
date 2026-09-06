from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.core.security import hash_password
from app.models import (
    Gender,
    Parent,
    ParentStudent,
    Student,
    User,
    UserRole,
)
from app.schemas.common import Page
from app.services import assessment, attendance, homework
from app.services.common import current_enrolment

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_permission("students.profile.read", school_wide=True)


class ParentInput(BaseModel):
    full_name: str
    phone: str
    relation: str = "father"
    occupation: str | None = None
    password: str = "Parent@123"


class StudentCreate(BaseModel):
    full_name: str
    admission_no: str
    class_section_id: int
    roll_no: int
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    admission_date: Date | None = None
    phone: str | None = None
    email: str | None = None
    password: str = "Student@123"
    parent: ParentInput | None = None
    parent_id: int | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = None
    class_section_id: int | None = None
    roll_no: int | None = None
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


def _row(db: Session, s: Student) -> dict:
    enrolment = current_enrolment(db, s.id)
    guardians = db.scalars(
        select(Parent)
        .join(ParentStudent, ParentStudent.parent_id == Parent.id)
        .where(ParentStudent.student_id == s.id)
    ).all()
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        "class_section_id": enrolment.class_section_id if enrolment else None,
        "class_label": enrolment.class_section.label if enrolment else "",
        "roll_no": enrolment.roll_no if enrolment else None,
        "photo_url": s.user.photo_url,
        "is_active": s.user.is_active,
        "parent_name": guardians[0].user.full_name if guardians else None,
        "parent_phone": guardians[0].user.phone if guardians else None,
    }


@router.get("/students", response_model=Page)
def list_students(
    class_section_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> Page:
    stmt = select(Student).join(User, User.id == Student.user_id)
    if class_section_id is not None:
        stmt = stmt.where(
            Student.id.in_(
                select(Enrolment.student_id).where(
                    Enrolment.class_section_id == class_section_id
                )
            )
        )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(like), Student.admission_no.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Student.admission_no).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return Page(items=[_row(db, s) for s in rows], total=total, page=page, page_size=page_size)


@router.post("/students", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("students.profile.write"))])
def create_student(
    body: StudentCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    if db.scalar(select(User).where(User.login_id == body.admission_no)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Admission number already exists")
    # Student login + student row + (new or linked) parent, in one transaction.
    su = User(
        school_id=user.school_id,
        role=UserRole.student,
        login_id=body.admission_no,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
    )
    db.add(su)
    db.flush()
    student = Student(
        school_id=user.school_id,
        user_id=su.id,
        admission_no=body.admission_no,
        dob=body.dob,
        gender=body.gender,
        address=body.address,
        admission_date=body.admission_date or Date.today(),
    )
    db.add(student)
    db.flush()
    # The class and roll number belong to a year, so creating a student also
    # creates their enrolment in the school's current one.
    section = db.get(ClassSection, body.class_section_id)
    if section is None or section.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
    db.add(
        Enrolment(
            school_id=user.school_id,
            student_id=student.id,
            academic_year_id=section.academic_year_id,
            class_section_id=section.id,
            roll_no=body.roll_no,
            joined_on=body.admission_date or Date.today(),
        )
    )
    db.flush()

    parent = None
    if body.parent_id is not None:
        parent = db.get(Parent, body.parent_id)
        if parent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent not found")
        relation = "guardian"
    elif body.parent is not None:
        if db.scalar(select(User).where(User.login_id == body.parent.phone)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Parent mobile already registered")
        pu = User(
            school_id=user.school_id,
            role=UserRole.parent,
            login_id=body.parent.phone,
            password_hash=hash_password(body.parent.password),
            full_name=body.parent.full_name,
            phone=body.parent.phone,
        )
        db.add(pu)
        db.flush()
        parent = Parent(
            school_id=user.school_id,
            user_id=pu.id,
            occupation=body.parent.occupation,
        )
        db.add(parent)
        db.flush()
        relation = body.parent.relation
    if parent is not None:
        db.add(
            ParentStudent(
                school_id=user.school_id,
                parent_id=parent.id,
                student_id=student.id,
                relation=relation,
            )
        )
    db.commit()
    return _row(db, student)


@router.get("/students/{student_id}")
def student_detail(
    student_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    enrolment = current_enrolment(db, s.id)
    exam = assessment.latest_exam_with_marks(
        db, s.school_id, enrolment.class_section_id if enrolment else None
    )
    hw = homework.for_student(db, s.id)
    return {
        **_row(db, s),
        "dob": s.dob,
        "gender": s.gender,
        "address": s.address,
        "admission_date": s.admission_date,
        "attendance_percent": attendance.student_percent(db, s.id),
        "latest_result_percent": (
            assessment.student_average_percent(db, s.id, exam.id) if exam else None
        ),
        "homework_pending": sum(1 for h in hw if not h.submitted),
    }


@router.patch("/students/{student_id}", dependencies=[Depends(require_permission("students.profile.write"))])
def update_student(
    student_id: int,
    body: StudentUpdate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    for field in ("class_section_id", "roll_no", "dob", "gender", "address"):
        value = getattr(body, field)
        if value is not None:
            setattr(s, field, value)
    for field in ("full_name", "phone", "email"):
        value = getattr(body, field)
        if value is not None:
            setattr(s.user, field, value)
    db.commit()
    return _row(db, s)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("students.profile.write"))])
def deactivate_student(
    student_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> Response:
    s = db.get(Student, student_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    s.user.is_active = False  # soft delete
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
