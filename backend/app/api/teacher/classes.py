from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import (
    ClassSection,
    ClassSubjectTeacher,
    Enrolment,
    Student,
    TimetableSlot,
    User,
    UserRole,
)
from app.schemas.common import SlotOut
from app.services import scoping
from app.services.common import roster, section_labels, subject_names

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("academics.class.read")


@router.get("/classes")
def my_classes(user: User = Depends(teacher_only), db: Session = Depends(get_db)) -> list[dict]:
    me = scoping.employee_for(db, user)
    labels = section_labels(db)
    subjects = subject_names(db)
    owned: dict[int, list[str]] = {}
    for row in db.scalars(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == me.id)
    ):
        owned.setdefault(row.class_section_id, []).append(subjects[row.subject_id])
    out = []
    for section_id in scoping.class_section_ids_for(db, user):
        section = db.get(ClassSection, section_id)
        out.append(
            {
                "class_section_id": section_id,
                "class_label": labels.get(section_id, ""),
                "is_class_teacher": section.class_teacher_id == me.id,
                "subjects": sorted(owned.get(section_id, [])),
                "student_count": db.query(Student)
                .filter(Enrolment.class_section_id == section_id)
                .count(),
            }
        )
    return out


@router.get("/classes/{class_section_id}/students")
def class_roster(
    class_section_id: int,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    scoping.assert_teaches_section(db, user, class_section_id)
    return [
        {
            "id": s.id,
            "full_name": s.user.full_name,
            "roll_no": e.roll_no,
            "admission_no": s.admission_no,
        }
        for s in roster(db, class_section_id)
    ]


@router.get("/timetable", response_model=list[SlotOut])
def my_timetable(
    user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> list[SlotOut]:
    me = scoping.employee_for(db, user)
    labels = section_labels(db)
    subjects = subject_names(db)
    slots = db.scalars(
        select(TimetableSlot)
        .where(TimetableSlot.teacher_id == me.id)
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
            teacher=user.full_name,
            room=s.room,
        )
        for s in slots
    ]


@router.get("/profile")
def my_profile(user: User = Depends(teacher_only), db: Session = Depends(get_db)) -> dict:
    me = scoping.employee_for(db, user)
    subjects = subject_names(db)
    labels = section_labels(db)
    owned = db.scalars(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == me.id)
    ).all()
    class_of = db.scalars(select(ClassSection).where(ClassSection.class_teacher_id == me.id)).all()
    return {
        "id": me.id,
        "full_name": user.full_name,
        "employee_id": me.employee_id,
        "qualification": me.qualification,
        "joining_date": me.joining_date,
        "email": user.email,
        "phone": user.phone,
        "subjects": ", ".join(sorted({subjects[o.subject_id] for o in owned})),
        "sections": ", ".join(sorted({labels[o.class_section_id] for o in owned})),
        "class_teacher_of": ", ".join(c.label for c in class_of),
    }


@router.get("/subjects")
def my_subjects(
    class_section_id: int | None = None,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Subjects this teacher owns, optionally within one section."""
    me = scoping.employee_for(db, user)
    subjects = subject_names(db)
    q = select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == me.id)
    if class_section_id is not None:
        scoping.assert_teaches_section(db, user, class_section_id)
        q = q.where(ClassSubjectTeacher.class_section_id == class_section_id)
    seen: dict[int, str] = {row.subject_id: subjects[row.subject_id] for row in db.scalars(q)}
    return [{"id": k, "name": v} for k, v in sorted(seen.items(), key=lambda kv: kv[1])]
