from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import timetable as timetable_svc
from app.services.rbac import require_permission
from app.models import (
    AcademicYear,
    ClassSection,
    ClassSubjectTeacher,
    Subject,
    Employee,
    User,
)
from app.schemas.common import SlotOut
from app.services import tenancy
from app.services.common import roster, subject_names

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_permission("academics.class.read", school_wide=True)


class ClassCreate(BaseModel):
    class_name: str
    section: str
    class_teacher_id: int | None = None
    capacity: int | None = None
    stream: str | None = None
    room: str | None = None
    # The session is no longer a free string on the request: a section is
    # created inside an academic year, defaulting to the school's current
    # one (ERP_BLUEPRINT §3.1).
    academic_year_id: int | None = None


class ClassUpdate(BaseModel):
    class_teacher_id: int | None = None


def _row(db: Session, c: ClassSection) -> dict:
    subjects = subject_names(db, c.school_id)
    owned = db.scalars(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.class_section_id == c.id)
    ).all()
    teacher = db.get(Employee, c.class_teacher_id) if c.class_teacher_id else None
    return {
        "id": c.id,
        "class_name": c.class_name,
        "section": c.section,
        "class_label": c.label,
        "academic_year": year.code if (year := db.get(AcademicYear, c.academic_year_id)) else "",
        "class_teacher_id": c.class_teacher_id,
        "class_teacher": teacher.user.full_name if teacher else None,
        "student_count": len(roster(db, c.id)),
        "subjects": sorted(subjects[o.subject_id] for o in owned),
    }


@router.get("/classes")
def list_classes(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    return [
        _row(db, c)
        for c in db.scalars(
            select(ClassSection)
            .where(ClassSection.school_id == user.school_id)
            .order_by(ClassSection.class_name, ClassSection.section)
        )
    ]


@router.post("/classes", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("academics.class.write"))])
def create_class(
    body: ClassCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    year = (
        db.get(AcademicYear, body.academic_year_id)
        if body.academic_year_id is not None
        else tenancy.current_year(db, user.school_id)
    )
    if year is None or year.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    tenancy.assert_writable(year)
    exists = db.scalar(
        select(ClassSection).where(
            ClassSection.school_id == user.school_id,
            ClassSection.class_name == body.class_name,
            ClassSection.section == body.section,
            ClassSection.academic_year_id == year.id,
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "This class section already exists")
    c = ClassSection(
        school_id=user.school_id,
        academic_year_id=year.id,
        **body.model_dump(exclude={"academic_year_id"}),
    )
    db.add(c)
    db.commit()
    return _row(db, c)


@router.patch("/classes/{class_id}", dependencies=[Depends(require_permission("academics.class.write"))])
def update_class(
    class_id: int,
    body: ClassUpdate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    c = db.get(ClassSection, class_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
    if body.class_teacher_id is not None:
        c.class_teacher_id = body.class_teacher_id
    db.commit()
    return _row(db, c)


@router.get("/classes/{class_id}/students")
def class_roster(
    class_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[dict]:
    return [
        {
            "id": e.student_id,
            "full_name": e.student.user.full_name,
            "roll_no": e.roll_no,
            "admission_no": e.student.admission_no,
        }
        for e in roster(db, class_id)
    ]


@router.get("/subjects")
def list_subjects(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": s.id, "name": s.name, "code": s.code}
        for s in db.scalars(
            select(Subject).where(Subject.school_id == user.school_id).order_by(Subject.name)
        )
    ]


@router.get("/timetable", response_model=list[SlotOut])
def timetable(
    class_section_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[SlotOut]:
    return timetable_svc.grid(db, user.school_id, class_section_id=class_section_id)
