from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import ExamSchedule, User, UserRole
from app.schemas.common import ExamScheduleOut, MarksRequest, MarksRosterRow
from app.services import assessment as svc
from app.services import scoping

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("exam.marks.read")


@router.get("/exams", response_model=list[ExamScheduleOut])
def my_papers(
    user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> list[ExamScheduleOut]:
    """Papers for the (section, subject) pairs this teacher owns."""
    me = scoping.employee_for(db, user)
    from app.models import ClassSubjectTeacher

    owned = {
        (r.class_section_id, r.subject_id)
        for r in db.scalars(
            select(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == me.id)
        )
    }
    rows = [
        r
        for r in db.scalars(select(ExamSchedule).order_by(ExamSchedule.exam_date))
        if (r.class_section_id, r.subject_id) in owned
    ]
    return svc.schedule_out(db, rows)


@router.get("/marks", response_model=list[MarksRosterRow])
def roster(
    exam_schedule_id: int, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> list[MarksRosterRow]:
    return svc.marks_roster(db, user, exam_schedule_id)


@router.post("/marks", response_model=list[MarksRosterRow], dependencies=[Depends(require_permission("exam.marks.enter"))])
def enter(
    body: MarksRequest, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> list[MarksRosterRow]:
    return svc.enter_marks(db, user, body)
