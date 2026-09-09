"""Scheduling applicant tests and interviews, and recording what happened
(§5.1.9(7)-(10)).

The four rules that need code rather than a column:

7. Marks cannot be entered before the paper was sat, and cannot exceed the
   maximum.
8. Absent and zero are different states.
9. A panel member sees nobody else's score until they have entered their own.
10. Changing a submitted score needs a reason, and is audited.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status as http
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Application,
    ApplicationStatus,
    Assessment,
    AssessmentStatus,
    AssessmentSubject,
    AuditAction,
    Interview,
    User,
)
from app.services import applications as app_svc
from app.services import audit


def _utc(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes even for timestamptz columns, and
    comparing one to an aware `now` raises rather than returning False."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def schedule_assessment(
    db: Session,
    app: Application,
    *,
    actor: User,
    assessment_type,
    scheduled_at: datetime,
    venue: str | None = None,
    seat_no: str | None = None,
    subjects: list[dict] | None = None,
) -> Assessment:
    row = Assessment(
        school_id=app.school_id,
        application_id=app.id,
        assessment_type=assessment_type,
        scheduled_at=scheduled_at,
        venue=venue,
        seat_no=seat_no,
    )
    db.add(row)
    db.flush()
    for s in subjects or []:
        db.add(
            AssessmentSubject(
                school_id=app.school_id,
                assessment_id=row.id,
                subject=s["subject"],
                max_marks=Decimal(str(s["max_marks"])),
            )
        )
    if app.status in (
        ApplicationStatus.documents_verified,
        ApplicationStatus.submitted,
        ApplicationStatus.under_document_verification,
    ):
        app_svc.move(
            db, app, ApplicationStatus.assessment_scheduled, actor=actor
        )
    db.commit()
    return row


def record_marks(
    db: Session,
    row: Assessment,
    *,
    actor: User,
    obtained_marks: Decimal | None = None,
    total_marks: Decimal | None = None,
    is_absent: bool = False,
    remarks: str | None = None,
    subject_marks: dict[str, Decimal] | None = None,
    reason: str | None = None,
    now: datetime | None = None,
) -> Assessment:
    now = now or datetime.now(UTC)
    if _utc(row.scheduled_at) > now:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            "Marks cannot be entered before the assessment has taken place",
        )
    if row.status is AssessmentStatus.completed and not (reason and reason.strip()):
        # §5.1.9(10): a score that has already been entered may be corrected,
        # but never quietly.
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            "Changing a recorded assessment requires a reason",
        )

    before = {
        "obtained_marks": str(row.obtained_marks),
        "is_absent": row.is_absent,
    }

    if is_absent:
        # Absent is a state, not a score of zero (§5.1.9(8)).
        row.is_absent = True
        row.status = AssessmentStatus.absent
        row.obtained_marks = None
    else:
        total = total_marks if total_marks is not None else row.total_marks
        if total is None:
            raise HTTPException(
                http.HTTP_422_UNPROCESSABLE_ENTITY,
                "The paper's total marks must be known before a score is entered",
            )
        if obtained_marks is None:
            raise HTTPException(
                http.HTTP_422_UNPROCESSABLE_ENTITY, "No marks given"
            )
        if obtained_marks > total:
            raise HTTPException(
                http.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{obtained_marks} is more than the maximum {total}",
            )
        row.total_marks = total
        row.obtained_marks = obtained_marks
        row.is_absent = False
        row.status = AssessmentStatus.completed

    for subject, mark in (subject_marks or {}).items():
        sub = db.scalar(
            select(AssessmentSubject).where(
                AssessmentSubject.assessment_id == row.id,
                AssessmentSubject.subject == subject,
            )
        )
        if sub is None:
            raise HTTPException(
                http.HTTP_404_NOT_FOUND, f"{subject} is not part of this assessment"
            )
        if mark > sub.max_marks:
            raise HTTPException(
                http.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{subject}: {mark} is more than the maximum {sub.max_marks}",
            )
        sub.obtained = mark

    row.evaluated_by = actor.id
    row.remarks = remarks if remarks is not None else row.remarks

    audit.record(
        db,
        actor=actor,
        school_id=row.school_id,
        entity_type="assessment",
        entity_id=row.id,
        action=AuditAction.update,
        before=before,
        after={"obtained_marks": str(row.obtained_marks), "is_absent": row.is_absent},
        reason=reason,
    )

    app = db.get(Application, row.application_id)
    if app.status is ApplicationStatus.assessment_scheduled:
        app_svc.move(db, app, ApplicationStatus.assessment_completed, actor=actor)
    db.commit()
    return row


def schedule_interview(
    db: Session,
    app: Application,
    *,
    actor: User,
    scheduled_at: datetime,
    venue: str | None = None,
    panel_member_ids: list[int] | None = None,
) -> Interview:
    row = Interview(
        school_id=app.school_id,
        application_id=app.id,
        scheduled_at=scheduled_at,
        venue=venue,
        panel_member_ids=panel_member_ids or [],
        structured_scores={},
    )
    db.add(row)
    if app.status in (
        ApplicationStatus.assessment_completed,
        ApplicationStatus.documents_verified,
        ApplicationStatus.submitted,
        ApplicationStatus.under_document_verification,
    ):
        app_svc.move(db, app, ApplicationStatus.interview_scheduled, actor=actor)
    db.commit()
    return row


def visible_scores(row: Interview, user: User) -> dict:
    """What this user may see of the panel's scoring (§5.1.9(9)).

    Until a panel member has entered their own score they see only their own
    slot — otherwise the second panelist simply agrees with the first, and the
    school has one opinion wearing three hats. Once they have submitted, the
    whole panel opens up.
    """
    scores = row.structured_scores or {}
    key = str(user.id)
    panel = [int(m) for m in (row.panel_member_ids or [])]
    if user.id not in panel:
        # Not on this panel: whoever is reading is doing so as an officer, and
        # the independence rule does not apply to them.
        return scores
    if key in scores:
        return scores
    return {key: scores.get(key)} if key in scores else {}


def record_panel_score(
    db: Session,
    row: Interview,
    *,
    actor: User,
    child_rating: int | None,
    parent_rating: int | None,
    recommendation,
    notes: str | None,
    reason: str | None = None,
    now: datetime | None = None,
) -> Interview:
    now = now or datetime.now(UTC)
    if _utc(row.scheduled_at) > now:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            "Feedback cannot be entered before the interview has taken place",
        )
    panel = [int(m) for m in (row.panel_member_ids or [])]
    if actor.id not in panel:
        raise HTTPException(
            http.HTTP_403_FORBIDDEN, "You are not on this interview panel"
        )

    scores = dict(row.structured_scores or {})
    key = str(actor.id)
    if key in scores and not (reason and reason.strip()):
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            "Changing submitted interview feedback requires a reason",
        )
    before = {key: scores.get(key)}
    scores[key] = {
        "child": child_rating,
        "parent": parent_rating,
        "recommendation": recommendation.value if recommendation else None,
        "notes": notes,
        "submitted_at": now.isoformat(),
    }
    row.structured_scores = scores

    # The interview's own summary is the panel's average, recomputed rather
    # than typed by whoever happens to save last.
    ratings = [s["child"] for s in scores.values() if s and s.get("child") is not None]
    row.child_rating = round(sum(ratings) / len(ratings)) if ratings else None
    parents = [s["parent"] for s in scores.values() if s and s.get("parent") is not None]
    row.parent_rating = round(sum(parents) / len(parents)) if parents else None

    if len(scores) >= len(panel) and panel:
        row.status = AssessmentStatus.completed
        app = db.get(Application, row.application_id)
        if app.status is ApplicationStatus.interview_scheduled:
            app_svc.move(db, app, ApplicationStatus.interview_completed, actor=actor)

    audit.record(
        db,
        actor=actor,
        school_id=row.school_id,
        entity_type="interview",
        entity_id=row.id,
        action=AuditAction.update,
        before=before,
        after={key: scores[key]},
        reason=reason,
    )
    db.commit()
    return row
