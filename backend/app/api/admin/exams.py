from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import Exam, ExamSchedule, User, UserRole
from app.schemas.common import (
    AttendanceSummary,
    ExamCreate,
    ExamScheduleCreate,
    ExamScheduleOut,
    ExamOut,
    RollRow,
)
from app.services import assessment
from app.services import attendance as attendance_svc

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(UserRole.admin)


@router.get("/exams", response_model=list[ExamOut])
def list_exams(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[Exam]:
    return list(db.scalars(select(Exam).order_by(Exam.start_date.desc())))


@router.post("/exams", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    body: ExamCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> Exam:
    if body.end_date < body.start_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_date must not precede start_date")
    exam = Exam(school_id=user.school_id, **body.model_dump())
    db.add(exam)
    db.commit()
    return exam


@router.post(
    "/exams/{exam_id}/schedule",
    response_model=ExamScheduleOut,
    status_code=status.HTTP_201_CREATED,
)
def add_paper(
    exam_id: int,
    body: ExamScheduleCreate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> ExamScheduleOut:
    if db.get(Exam, exam_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found")
    duplicate = db.scalar(
        select(ExamSchedule).where(
            ExamSchedule.exam_id == exam_id,
            ExamSchedule.class_section_id == body.class_section_id,
            ExamSchedule.subject_id == body.subject_id,
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "This paper is already scheduled")
    if body.max_marks <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "max_marks must be positive")
    sched = ExamSchedule(
        school_id=user.school_id, exam_id=exam_id, **body.model_dump()
    )
    db.add(sched)
    db.commit()
    return assessment.schedule_out(db, [sched])[0]


@router.get("/exams/{exam_id}/schedule", response_model=list[ExamScheduleOut])
def exam_schedule(
    exam_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[ExamScheduleOut]:
    rows = list(
        db.scalars(
            select(ExamSchedule)
            .where(ExamSchedule.exam_id == exam_id)
            .order_by(ExamSchedule.exam_date)
        )
    )
    return assessment.schedule_out(db, rows)


@router.get("/attendance", response_model=list[RollRow])
def attendance_roll(
    class_section_id: int,
    date: Date,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[RollRow]:
    """Read-only: admins do not mark attendance (BLUEPRINT §9 matrix)."""
    return attendance_svc.roll_sheet(db, class_section_id, date)


@router.get("/attendance/summary", response_model=AttendanceSummary)
def attendance_summary(
    date_from: Date | None = Query(None, alias="from"),
    date_to: Date | None = Query(None, alias="to"),
    class_section_id: int | None = None,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> AttendanceSummary:
    return attendance_svc.section_summary(
        db, user.school_id, class_section_id, date_from, date_to
    )
