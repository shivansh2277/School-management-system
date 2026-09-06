from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import ExamSchedule, Student, TimetableSlot, User, UserRole
from app.schemas.common import SlotOut
from app.services import assessment, attendance, homework, notices, scoping
from app.services.common import section_labels, subject_names
from app.services.stats import DAY_KEYS

router = APIRouter(prefix="/student", tags=["student"])
student_only = require_role(UserRole.student)


def _slots(db: Session, student: Student, day_key: str | None) -> list[SlotOut]:
    q = select(TimetableSlot).where(TimetableSlot.class_section_id == student.class_section_id)
    if day_key is not None:
        q = q.where(TimetableSlot.day_of_week == day_key)
    labels = section_labels(db)
    subjects = subject_names(db)
    from app.models import Teacher

    teachers = {t.id: t.user.full_name for t in db.scalars(select(Teacher))}
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
        for s in db.scalars(q.order_by(TimetableSlot.day_of_week, TimetableSlot.period_no))
    ]


@router.get("/dashboard")
def dashboard(user: User = Depends(student_only), db: Session = Depends(get_db)) -> dict:
    s = scoping.student_for(db, user)
    exam = assessment.latest_exam_with_marks(db, s.school_id, s.class_section_id)
    next_paper = db.scalars(
        select(ExamSchedule)
        .where(
            ExamSchedule.class_section_id == s.class_section_id,
            ExamSchedule.exam_date >= Date.today(),
        )
        .order_by(ExamSchedule.exam_date)
        .limit(1)
    ).first()
    return {
        "attendance_percent": attendance.student_percent(db, s.id),
        "homework_pending": homework.pending_count(db, s.id),
        "next_exam": (
            {
                "exam_schedule_id": next_paper.id,
                "subject": subject_names(db).get(next_paper.subject_id, ""),
                "exam_date": next_paper.exam_date,
            }
            if next_paper
            else None
        ),
        "latest_result_percent": (
            assessment.student_average_percent(db, s.id, exam.id) if exam else None
        ),
        "recent_notices": notices.visible_to(db, user)[:5],
        "today_schedule": _slots(db, s, DAY_KEYS[Date.today().weekday()]),
    }


@router.get("/timetable", response_model=list[SlotOut])
def timetable(user: User = Depends(student_only), db: Session = Depends(get_db)) -> list[SlotOut]:
    return _slots(db, scoping.student_for(db, user), None)


@router.get("/profile")
def profile(user: User = Depends(student_only), db: Session = Depends(get_db)) -> dict:
    from app.models import Parent, ParentStudent

    s = scoping.student_for(db, user)
    guardians = db.scalars(
        select(Parent).join(ParentStudent, ParentStudent.parent_id == Parent.id).where(
            ParentStudent.student_id == s.id
        )
    ).all()
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        "class_label": s.class_section.label,
        "roll_no": s.roll_no,
        "dob": s.dob,
        "gender": s.gender,
        "address": s.address,
        "admission_date": s.admission_date,
        "parents": [{"full_name": g.user.full_name, "phone": g.user.phone} for g in guardians],
    }


@router.get("/notices")
def my_notices(user: User = Depends(student_only), db: Session = Depends(get_db)) -> list:
    return notices.visible_to(db, user)
