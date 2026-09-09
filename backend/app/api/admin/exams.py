from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from app.core.db import get_db
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled
from app.models import Exam, ExamSchedule, User
from app.schemas.common import (
    MarksRequest,
    MarksRosterRow,
    ExamCreate,
    ExamScheduleCreate,
    ExamScheduleOut,
    ExamOut,
)
from app.services import assessment, schemes

router = APIRouter(
    prefix="/admin", tags=["admin"],
    dependencies=[Depends(module_enabled("examinations"))],
)
admin_only = require_permission("exam.definition.read", school_wide=True)


@router.get("/exams", response_model=list[ExamOut])
def list_exams(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[Exam]:
    return list(
        db.scalars(
            select(Exam)
            .where(Exam.school_id == user.school_id)
            .order_by(Exam.start_date.desc())
        )
    )


@router.post("/exams", response_model=ExamOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.definition.write"))])
def create_exam(
    body: ExamCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> Exam:
    if body.end_date < body.start_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_date must not precede start_date")
    fields = body.model_dump()
    component_id = fields.pop("scheme_component_id")
    exam = Exam(school_id=user.school_id, **fields)
    db.add(exam)
    db.flush()
    # Takes the term from the component when there is one: two places naming
    # the term is two places to disagree, and the report card groups by it.
    schemes.attach_component(db, exam, component_id)
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


class UnlockRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


@router.post(
    "/exams/papers/{exam_schedule_id}/lock",
    response_model=ExamScheduleOut,
    dependencies=[Depends(require_permission("exam.marks.lock"))],
)
def lock_paper(
    exam_schedule_id: int,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> ExamScheduleOut:
    """Close marks entry. After this a change needs an override and a reason."""
    sched = assessment.lock_marks(db, user, exam_schedule_id)
    return assessment.schedule_out(db, [sched])[0]


@router.post(
    "/exams/papers/{exam_schedule_id}/unlock",
    response_model=ExamScheduleOut,
    dependencies=[Depends(require_permission("exam.marks.lock"))],
)
def unlock_paper(
    exam_schedule_id: int,
    body: UnlockRequest,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> ExamScheduleOut:
    sched = assessment.unlock_marks(db, user, exam_schedule_id, body.reason)
    return assessment.schedule_out(db, [sched])[0]


@router.get("/exams/papers/{exam_schedule_id}/marks", response_model=list[MarksRosterRow])
def paper_marks(
    exam_schedule_id: int,
    user: User = Depends(require_permission("exam.marks.manage_any", school_wide=True)),
    db: Session = Depends(get_db),
) -> list[MarksRosterRow]:
    return assessment.marks_roster(db, user, exam_schedule_id, school_wide=True)


@router.post("/exams/papers/{exam_schedule_id}/marks", response_model=list[MarksRosterRow])
def enter_paper_marks(
    exam_schedule_id: int,
    body: MarksRequest,
    user: User = Depends(require_permission("exam.marks.manage_any", school_wide=True)),
    db: Session = Depends(get_db),
) -> list[MarksRosterRow]:
    """The exam controller's way in.

    `/teacher/marks` reaches only the papers a teacher owns, which is right for
    a subject teacher and wrong for the person §5.4.8 puts in charge of
    moderation: an override on a locked paper is exactly the case where the
    actor does not teach the subject. The lock and the audit rules are the same
    either way — they live in the service, not in the route.

    Gated on its own permission rather than on `exam.marks.enter`, because a
    teacher holds that one *unscoped* — the "own subjects only" restriction is
    enforced in the service, not by the grant. Reusing it here would have let
    any teacher mark any section in the school.
    """
    body.exam_schedule_id = exam_schedule_id
    return assessment.enter_marks(db, user, body, school_wide=True)
