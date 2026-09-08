from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.core.security import hash_password
from app.models import (
    AuditAction,
    ClassSection,
    Enrolment,
    Gender,
    Guardian,
    StudentGuardian,
    GuardianRelation,
    OwnerType,
    Student,
    User,
    UserRole,
)
from app.schemas.common import Page
from app.services import assessment, attendance, audit, homework
from app.services import custom_fields as cf
from app.services.common import current_enrolment

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_permission("students.profile.read", school_wide=True)


class GuardianInput(BaseModel):
    full_name: str
    phone: str
    relation: GuardianRelation = GuardianRelation.father
    occupation: str | None = None
    password: str = "Parent@123"


class StudentCreate(BaseModel):
    # extra="forbid" because the guardian key was renamed under these tests
    # and they kept passing: a body with a key nobody reads looked identical
    # to a body that worked.
    model_config = {"extra": "forbid"}

    full_name: str
    # Omit it and the school's gapless sequence allocates one (§0.21).
    admission_no: str | None = None
    class_section_id: int
    roll_no: int
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    admission_date: Date | None = None
    phone: str | None = None
    email: str | None = None
    password: str = "Student@123"
    guardian: GuardianInput | None = None
    guardian_id: int | None = None
    # School-defined attributes (§3.15 level 2), keyed by custom field key.
    custom: dict | None = None


class StudentUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    full_name: str | None = None
    class_section_id: int | None = None
    roll_no: int | None = None
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    custom: dict | None = None


def _owned(db: Session, user: User, student_id: int) -> Student:
    """This school's student, or 404.

    `db.get()` is not tenant-aware, and three handlers here used it bare, so a
    guessed id read - and in one case edited - another customer's child.
    """
    s = db.get(Student, student_id)
    if s is None or s.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return s


def _row(db: Session, s: Student) -> dict:
    enrolment = current_enrolment(db, s.id)
    guardians = db.scalars(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == s.id)
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
        "guardian_name": guardians[0].user.full_name if guardians else None,
        "guardian_phone": guardians[0].user.phone if guardians else None,
        "custom": s.custom or {},
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
    # Carrying `school_id` is not filtering on it (CLAUDE.md, HANDOFF section
    # 4). This is the roster of every child in the school, so the omission here
    # was the widest of that family.
    stmt = (
        select(Student)
        .join(User, User.id == Student.user_id)
        .where(Student.school_id == user.school_id)
    )
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
    section = db.get(ClassSection, body.class_section_id)
    if section is None or section.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
    custom = cf.validate(db, user.school_id, OwnerType.student, body.custom)
    admission_no = body.admission_no or audit.admission_number(
        db, user.school_id, (body.admission_date or Date.today()).year
    )
    if db.scalar(select(User).where(User.login_id == admission_no)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Admission number already exists")
    # Student login + student row + (new or linked) guardian, in one transaction.
    su = User(
        school_id=user.school_id,
        role=UserRole.student,
        login_id=admission_no,
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
        admission_no=admission_no,
        dob=body.dob,
        gender=body.gender,
        address=body.address,
        admission_date=body.admission_date or Date.today(),
        custom=custom,
    )
    db.add(student)
    db.flush()
    # The class and roll number belong to a year, so creating a student also
    # creates their enrolment in the section's.
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

    guardian_row = None
    if body.guardian_id is not None:
        guardian_row = db.get(Guardian, body.guardian_id)
        if guardian_row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")
        relation = GuardianRelation.legal_guardian
    elif body.guardian is not None:
        if db.scalar(select(User).where(User.login_id == body.guardian.phone)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Guardian mobile already registered")
        pu = User(
            school_id=user.school_id,
            role=UserRole.parent,
            login_id=body.guardian.phone,
            password_hash=hash_password(body.guardian.password),
            full_name=body.guardian.full_name,
            phone=body.guardian.phone,
        )
        db.add(pu)
        db.flush()
        guardian_row = Guardian(
            school_id=user.school_id,
            user_id=pu.id,
            occupation=body.guardian.occupation,
        )
        db.add(guardian_row)
        db.flush()
        relation = body.guardian.relation
    if guardian_row is not None:
        db.add(
            StudentGuardian(
                school_id=user.school_id,
                guardian_id=guardian_row.id,
                student_id=student.id,
                relation=relation,
                is_primary=not db.scalar(
                    select(StudentGuardian.id).where(
                        StudentGuardian.student_id == student.id,
                        StudentGuardian.is_primary.is_(True),
                    )
                ),
            )
        )
    db.commit()
    return _row(db, student)


@router.get("/students/{student_id}")
def student_detail(
    student_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    s = _owned(db, user, student_id)
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
    s = _owned(db, user, student_id)
    # class_section_id and roll_no live on the enrolment now. Setting them on
    # the Student silently did nothing: SQLAlchemy accepts the attribute, the
    # column is not there, and the move was lost.
    if body.class_section_id is not None or body.roll_no is not None:
        enrolment = current_enrolment(db, s.id)
        if enrolment is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This student has no enrolment in the current academic year",
            )
        if body.class_section_id is not None:
            section = db.get(ClassSection, body.class_section_id)
            if section is None or section.school_id != user.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
            enrolment.class_section_id = section.id
        if body.roll_no is not None:
            enrolment.roll_no = body.roll_no
    for field in ("dob", "gender", "address"):
        value = getattr(body, field)
        if value is not None:
            setattr(s, field, value)
    if body.custom is not None:
        s.custom = cf.validate(
            db, user.school_id, OwnerType.student, body.custom,
            existing=s.custom, partial=True,
        )
    for field in ("full_name", "phone", "email"):
        value = getattr(body, field)
        if value is not None:
            setattr(s.user, field, value)
    db.commit()
    return _row(db, s)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("students.profile.write"))])
def deactivate_student(
    student_id: int,
    reason: str = Query(
        ...,
        min_length=3,
        description="Why this student is being deactivated. Recorded in the audit log.",
    ),
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> Response:
    s = _owned(db, user, student_id)
    before = audit.snapshot(s.user, ["is_active"])
    s.user.is_active = False  # portal access revoked; the record is retained
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="student",
        entity_id=s.id,
        action=AuditAction.status_change,
        before=before,
        after=audit.snapshot(s.user, ["is_active"]),
        reason=reason,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
