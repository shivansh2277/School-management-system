from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import ClassSubjectTeacher, ExamSchedule, Homework, Mark, User, UserRole
from app.services import homework as hw_svc
from app.services import scoping, stats
from app.services.common import section_labels

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("academics.class.read")


@router.get("/dashboard")
def dashboard(user: User = Depends(teacher_only), db: Session = Depends(get_db)) -> dict:
    me = scoping.employee_for(db, user)
    section_ids = scoping.class_section_ids_for(db, user)
    labels = section_labels(db, user.school_id)
    owned = {
        (r.class_section_id, r.subject_id)
        for r in db.scalars(
            select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == me.id)
        )
    }
    with_marks = set(db.scalars(select(Mark.exam_schedule_id).distinct()))
    pending_marks = [
        s
        for s in db.scalars(select(ExamSchedule))
        if (s.class_section_id, s.subject_id) in owned and s.id not in with_marks
    ]
    mine = list(db.scalars(select(Homework).where(Homework.teacher_id == me.id)))
    reviews = sum(
        1 for h in hw_svc.to_out(db, mine) if h.submitted_count < h.total_students
    )
    return {
        "today_schedule": stats.today_schedule(db, user.school_id, section_ids, teacher_id=me.id),
        "sections": [labels[i] for i in section_ids],
        "pending_marks_entry": len(pending_marks),
        "homework_awaiting_submissions": reviews,
        "attendance": stats.month_attendance(db, section_ids[0]) if section_ids else None,
    }
