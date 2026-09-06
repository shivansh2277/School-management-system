from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import Exam, ExamSchedule, Mark, User, UserRole
from app.schemas.common import (
    AttendanceMonth,
    ExamScheduleOut,
    ReportCard,
    StudentHomeworkOut,
    SubmitRequest,
)
from app.services import assessment, attendance, homework, scoping
from app.services.common import require_current_enrolment

router = APIRouter(prefix="/student", tags=["student"])
student_only = require_permission("homework.item.read")


@router.get("/attendance", response_model=AttendanceMonth)
def my_attendance(
    month: int | None = None,
    year: int | None = None,
    user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> AttendanceMonth:
    today = Date.today()
    s = scoping.student_for(db, user)
    return attendance.student_month(db, s.id, month or today.month, year or today.year)


@router.get("/homework", response_model=list[StudentHomeworkOut])
def my_homework(
    status: str = "all", user: User = Depends(student_only), db: Session = Depends(get_db)
) -> list[StudentHomeworkOut]:
    return homework.for_student(db, scoping.student_id_for(db, user), status)


@router.post("/homework/{homework_id}/submit", response_model=StudentHomeworkOut, dependencies=[Depends(require_permission("homework.submission.submit"))])
def submit(
    homework_id: int,
    body: SubmitRequest,
    user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> StudentHomeworkOut:
    return homework.submit(db, user, homework_id, body.answer_text)


@router.get("/exams", response_model=list[ExamScheduleOut])
def upcoming_exams(
    user: User = Depends(student_only), db: Session = Depends(get_db)
) -> list[ExamScheduleOut]:
    s = scoping.student_for(db, user)
    enrolment = require_current_enrolment(db, s.id)
    rows = list(
        db.scalars(
            select(ExamSchedule)
            .where(
                ExamSchedule.class_section_id == enrolment.class_section_id,
                ExamSchedule.exam_date >= Date.today(),
            )
            .order_by(ExamSchedule.exam_date)
        )
    )
    return assessment.schedule_out(db, rows)


@router.get("/results")
def my_results(user: User = Depends(student_only), db: Session = Depends(get_db)) -> list[dict]:
    """Exams this student actually has marks for."""
    s = scoping.student_for(db, user)
    exams = db.scalars(
        select(Exam)
        .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
        .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
        .where(Mark.student_id == s.id)
        .distinct()
        .order_by(Exam.end_date.desc())
    ).all()
    return [
        {
            "exam_id": e.id,
            "name": e.name,
            "term": e.term,
            "overall_percent": assessment.report_card(db, s.id, e.id).overall_percent,
        }
        for e in exams
    ]


@router.get("/results/{exam_id}", response_model=ReportCard)
def report_card(
    exam_id: int, user: User = Depends(student_only), db: Session = Depends(get_db)
) -> ReportCard:
    return assessment.report_card(db, scoping.student_id_for(db, user), exam_id)
