from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import (
    AcademicYear,
    ClassSection,
    ClassSubjectTeacher,
    Homework,
    HomeworkSubmission,
    Student,
    Subject,
    Teacher,
    TimetableSlot,
    User,
    UserRole,
)
from app.schemas.common import HomeworkOut, SlotOut
from app.services import homework as homework_svc
from app.services import tenancy
from app.services.common import roster, section_labels, subject_names

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
    subjects = subject_names(db)
    owned = db.scalars(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.class_section_id == c.id)
    ).all()
    teacher = db.get(Teacher, c.class_teacher_id) if c.class_teacher_id else None
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
        for s in db.scalars(select(Subject).order_by(Subject.name))
    ]


@router.get("/timetable", response_model=list[SlotOut])
def timetable(
    class_section_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[SlotOut]:
    labels = section_labels(db)
    subjects = subject_names(db)
    teachers = {t.id: t.user.full_name for t in db.scalars(select(Teacher))}
    slots = db.scalars(
        select(TimetableSlot)
        .where(TimetableSlot.class_section_id == class_section_id)
        .order_by(TimetableSlot.day_of_week, TimetableSlot.period_no)
    )
    return [
        SlotOut(
            period=s.period_no,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            class_section_id=s.class_section_id,
            class_label=labels.get(s.class_section_id, ""),
            subject=subjects.get(s.subject_id, ""),
            teacher=teachers.get(s.teacher_id, ""),
            room=s.room,
        )
        for s in slots
    ]


@router.get("/assignments", response_model=list[HomeworkOut])
def assignments(
    class_section_id: int | None = None,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[HomeworkOut]:
    """All homework across sections, read only (BLUEPRINT section 9 matrix)."""
    q = select(Homework)
    if class_section_id is not None:
        q = q.where(Homework.class_section_id == class_section_id)
    return homework_svc.to_out(db, list(db.scalars(q.order_by(Homework.due_date.desc()))))


@router.get("/assignments/{homework_id}/submissions")
def assignment_submissions(
    homework_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[dict]:
    hw = db.get(Homework, homework_id)
    if hw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Homework not found")
    submitted = {
        s.student_id: s
        for s in db.scalars(
            select(HomeworkSubmission).where(HomeworkSubmission.homework_id == hw.id)
        )
    }
    return [
        {
            "student_id": e.student_id,
            "full_name": e.student.user.full_name,
            "roll_no": e.roll_no,
            "submitted": e.student_id in submitted,
            "submitted_at": (
                submitted[e.student_id].submitted_at
                if e.student_id in submitted
                else None
            ),
            "late": (
                e.student_id in submitted
                and submitted[e.student_id].submitted_at.date() > hw.due_date
            ),
        }
        for e in roster(db, hw.class_section_id)
    ]
