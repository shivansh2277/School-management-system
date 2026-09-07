from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import timetable as timetable_svc
from app.services.rbac import require_permission
from app.models import ExamSchedule, Student, TimetableSlot, User, UserRole
from app.schemas.common import SlotOut
from app.services import assessment, attendance, homework, notices, scoping
from app.services.common import require_current_enrolment, section_labels, subject_names
from app.services.stats import DAY_KEYS

router = APIRouter(prefix="/student", tags=["student"])
student_only = require_permission("attendance.record.read")


def _slots(db: Session, student: Student, day_key: str | None) -> list[SlotOut]:
    enrolment = require_current_enrolment(db, student.id)
    return timetable_svc.grid(
        db,
        student.school_id,
        class_section_id=enrolment.class_section_id,
        day_of_week=day_key,
    )


@router.get("/dashboard")
def dashboard(user: User = Depends(student_only), db: Session = Depends(get_db)) -> dict:
    s = scoping.student_for(db, user)
    exam = assessment.latest_exam_with_marks(
        db, s.school_id, require_current_enrolment(db, s.id).class_section_id
    )
    next_paper = db.scalars(
        select(ExamSchedule)
        .where(
            ExamSchedule.class_section_id == require_current_enrolment(
                db, s.id
            ).class_section_id,
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
                "subject": subject_names(db, user.school_id).get(next_paper.subject_id, ""),
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
    from app.models import Guardian, StudentGuardian

    s = scoping.student_for(db, user)
    guardians = db.scalars(
        select(Guardian).join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id).where(
            StudentGuardian.student_id == s.id
        )
    ).all()
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        "class_label": enrolment.class_section.label if enrolment else "",
        "roll_no": enrolment.roll_no if enrolment else None,
        "dob": s.dob,
        "gender": s.gender,
        "address": s.address,
        "admission_date": s.admission_date,
        "parents": [{"full_name": g.user.full_name, "phone": g.user.phone} for g in guardians],
    }


@router.get("/notices")
def my_notices(user: User = Depends(student_only), db: Session = Depends(get_db)) -> list:
    return notices.visible_to(db, user)
