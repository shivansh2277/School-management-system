"""Assessment and interview scheduling, marks and panel feedback (screens 9-11
of §5.1.3)."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Assessment,
    AssessmentSubject,
    AssessmentType,
    Interview,
    InterviewRecommendation,
    User,
)
from app.services import admission_assessment as svc
from app.services import applications as app_svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)
scheduler = Depends(require_permission("admission.application.write"))
# An assessor is a teacher marking papers for a slot they were given; they do
# not otherwise work the pipeline (§5.1.8).
assessor = require_permission("admission.assessment.enter")
panelist = require_permission("admission.interview.enter")


class SubjectInput(BaseModel):
    model_config = {"extra": "forbid"}

    subject: str
    max_marks: Decimal


class AssessmentSchedule(BaseModel):
    model_config = {"extra": "forbid"}

    assessment_type: AssessmentType
    scheduled_at: datetime
    venue: str | None = None
    seat_no: str | None = None
    subjects: list[SubjectInput] = []


class MarksInput(BaseModel):
    model_config = {"extra": "forbid"}

    obtained_marks: Decimal | None = None
    total_marks: Decimal | None = None
    # Absent is its own state, never a score of zero (§5.1.9(8)).
    is_absent: bool = False
    remarks: str | None = None
    subject_marks: dict[str, Decimal] = {}
    reason: str | None = None


class InterviewSchedule(BaseModel):
    model_config = {"extra": "forbid"}

    scheduled_at: datetime
    venue: str | None = None
    panel_member_ids: list[int] = []


class PanelFeedback(BaseModel):
    model_config = {"extra": "forbid"}

    child_rating: int | None = None
    parent_rating: int | None = None
    recommendation: InterviewRecommendation | None = None
    notes: str | None = None
    reason: str | None = None


def _assessment_out(db: Session, row: Assessment) -> dict:
    subjects = db.scalars(
        select(AssessmentSubject).where(AssessmentSubject.assessment_id == row.id)
    )
    return {
        "id": row.id,
        "application_id": row.application_id,
        "assessment_type": row.assessment_type,
        "scheduled_at": row.scheduled_at,
        "venue": row.venue,
        "seat_no": row.seat_no,
        "status": row.status,
        "total_marks": row.total_marks,
        "obtained_marks": row.obtained_marks,
        "percent": row.percent,
        "is_absent": row.is_absent,
        "remarks": row.remarks,
        "subjects": [
            {"subject": s.subject, "max_marks": s.max_marks, "obtained": s.obtained}
            for s in subjects
        ],
    }


def _interview_out(row: Interview, user: User) -> dict:
    return {
        "id": row.id,
        "application_id": row.application_id,
        "scheduled_at": row.scheduled_at,
        "venue": row.venue,
        "panel_member_ids": row.panel_member_ids or [],
        "status": row.status,
        "child_rating": row.child_rating,
        "parent_rating": row.parent_rating,
        "recommendation": row.recommendation,
        # Filtered: a panel member sees nobody else's scoring until they have
        # entered their own (§5.1.9(9)).
        "scores": svc.visible_scores(row, user),
    }


@router.post(
    "/applications/{application_id}/assessments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[scheduler],
)
def schedule_assessment(
    application_id: int,
    body: AssessmentSchedule,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = app_svc.get(db, user.school_id, application_id)
    row = svc.schedule_assessment(
        db,
        app,
        actor=user,
        assessment_type=body.assessment_type,
        scheduled_at=body.scheduled_at,
        venue=body.venue,
        seat_no=body.seat_no,
        subjects=[s.model_dump() for s in body.subjects],
    )
    return _assessment_out(db, row)


@router.get("/assessments")
def assessment_slot(
    on: datetime | None = Query(
        None, description="Everything scheduled at or after this moment"
    ),
    user: User = Depends(assessor),
    db: Session = Depends(get_db),
) -> list[dict]:
    """The roster an assessor marks from."""
    stmt = select(Assessment).where(Assessment.school_id == user.school_id)
    if on is not None:
        stmt = stmt.where(Assessment.scheduled_at >= on)
    return [
        _assessment_out(db, row)
        for row in db.scalars(stmt.order_by(Assessment.scheduled_at, Assessment.seat_no))
    ]


@router.post("/assessments/{assessment_id}/marks")
def record_marks(
    assessment_id: int,
    body: MarksInput,
    user: User = Depends(assessor),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Assessment, assessment_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment not found")
    svc.record_marks(
        db,
        row,
        actor=user,
        obtained_marks=body.obtained_marks,
        total_marks=body.total_marks,
        is_absent=body.is_absent,
        remarks=body.remarks,
        subject_marks=body.subject_marks,
        reason=body.reason,
    )
    return _assessment_out(db, row)


@router.post(
    "/applications/{application_id}/interviews",
    status_code=status.HTTP_201_CREATED,
    dependencies=[scheduler],
)
def schedule_interview(
    application_id: int,
    body: InterviewSchedule,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = app_svc.get(db, user.school_id, application_id)
    row = svc.schedule_interview(
        db,
        app,
        actor=user,
        scheduled_at=body.scheduled_at,
        venue=body.venue,
        panel_member_ids=body.panel_member_ids,
    )
    return _interview_out(row, user)


@router.get("/interviews/{interview_id}")
def read_interview(
    interview_id: int, user: User = Depends(panelist), db: Session = Depends(get_db)
) -> dict:
    row = db.get(Interview, interview_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    return _interview_out(row, user)


@router.post("/interviews/{interview_id}/feedback")
def record_feedback(
    interview_id: int,
    body: PanelFeedback,
    user: User = Depends(panelist),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Interview, interview_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    svc.record_panel_score(
        db,
        row,
        actor=user,
        child_rating=body.child_rating,
        parent_rating=body.parent_rating,
        recommendation=body.recommendation,
        notes=body.notes,
        reason=body.reason,
    )
    return _interview_out(row, user)


@router.get("/applications/{application_id}/evaluation")
def evaluation(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Everything scored about one applicant, for the 360° view."""
    app = app_svc.get(db, user.school_id, application_id)
    assessments = db.scalars(
        select(Assessment).where(Assessment.application_id == app.id)
    )
    interviews = db.scalars(
        select(Interview).where(Interview.application_id == app.id)
    )
    return {
        "assessments": [_assessment_out(db, a) for a in assessments],
        "interviews": [_interview_out(i, user) for i in interviews],
    }
