"""Report card preview, publication and release (§5.4.3, §0.8, §0.6b).

Preview and issued card are deliberately different endpoints returning
different things. A preview recomputes; an issued card is read back byte for
byte. Collapsing them into one route with a flag is how a frozen document
quietly starts moving again.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Enrolment, ReportCardPublication, User
from app.services import report_cards as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/report-cards", tags=["admin"],
    dependencies=[Depends(module_enabled("examinations"))],
)
reader = require_permission("exam.marks.read", school_wide=True)
publisher = require_permission("exam.result.publish", school_wide=True)


class ReleaseRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


def _enrolment(db: Session, user: User, enrolment_id: int) -> Enrolment:
    row = db.get(Enrolment, enrolment_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
    return row


def _publication(db: Session, user: User, publication_id: int) -> ReportCardPublication:
    row = db.get(ReportCardPublication, publication_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report card not found")
    return row


@router.get("/preview")
def preview(
    enrolment_id: int,
    term: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """The live card. Moves when a mark is corrected — it is a screen."""
    return svc.preview(db, _enrolment(db, user, enrolment_id), term)


@router.get("/readiness")
def readiness(
    enrolment_id: int,
    term: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """What stands between this child and a published card.

    Answered before publication is attempted rather than as a 409 afterwards:
    an exam controller working through a section wants the list, not a refusal
    per student.
    """
    enrolment = _enrolment(db, user, enrolment_id)
    unlocked = svc.unlocked_papers(db, enrolment, term)
    return {
        "enrolment_id": enrolment.id,
        "term": term,
        "unlocked_papers": [
            {"exam_schedule_id": p.id, "subject_id": p.subject_id} for p in unlocked
        ],
        "outstanding": svc.outstanding_for(db, enrolment),
        "already_published": svc.published(db, enrolment.id, term) is not None,
    }


@router.post("/publish", status_code=status.HTTP_201_CREATED)
def publish(
    enrolment_id: int,
    term: str,
    user: User = Depends(publisher),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.publish(db, user, _enrolment(db, user, enrolment_id), term)
    return svc.issued(db, row)


@router.get("/{publication_id}")
def issued(
    publication_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """The card exactly as it was handed over. Never recomputed."""
    return svc.issued(db, _publication(db, user, publication_id))


@router.get("")
def list_published(
    term: str | None = None,
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = (
        select(ReportCardPublication)
        .join(Enrolment, Enrolment.id == ReportCardPublication.enrolment_id)
        .where(ReportCardPublication.school_id == user.school_id)
    )
    if term is not None:
        q = q.where(ReportCardPublication.term == term)
    if class_section_id is not None:
        q = q.where(Enrolment.class_section_id == class_section_id)
    return [
        {
            "id": r.id,
            "document_no": r.document_no,
            "enrolment_id": r.enrolment_id,
            "term": r.term,
            "result_status": r.result_status,
            "published_at": r.published_at,
        }
        for r in db.scalars(q.order_by(ReportCardPublication.published_at.desc()))
    ]


@router.post("/{publication_id}/release")
def release(
    publication_id: int,
    body: ReleaseRequest,
    user: User = Depends(publisher),
    db: Session = Depends(get_db),
) -> dict:
    """Lift a withholding once the dues are cleared. The marks do not move."""
    row = svc.release_withheld(db, user, _publication(db, user, publication_id), body.reason)
    return svc.issued(db, row)
