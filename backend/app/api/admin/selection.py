"""Merit view, decisions, offers and the waitlist (screens 12, 13 and 16 of
§5.1.3)."""

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AdmissionOffer,
    Application,
    DecisionOutcome,
    User,
    WaitlistEntry,
)
from app.services import admission
from app.services import applications as app_svc
from app.services import selection as svc
from app.services.common import class_sort_key
from app.services.rbac import require_permission, authz_for
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)
cycle_reader = require_permission(
    "admission.cycle.read", "admission.application.read", school_wide=True
)
decider = require_permission("admission.decision.make", school_wide=True)


class DecisionInput(BaseModel):
    model_config = {"extra": "forbid"}

    decision: DecisionOutcome
    # No default. §5.1.9(13) wants a reason for every decision, and a default
    # would quietly supply one.
    reason: str
    seat_category: str | None = None
    conditions: str | None = None
    over_allocation_approved: bool = False


class BatchDecision(BaseModel):
    model_config = {"extra": "forbid"}

    decisions: list[dict]


class OfferInput(BaseModel):
    model_config = {"extra": "forbid"}

    expires_on: Date
    offer_amount: Decimal | None = None


class OfferResponse(BaseModel):
    model_config = {"extra": "forbid"}

    accepted: bool
    reason: str | None = None


def _offer_out(o: AdmissionOffer) -> dict:
    return {
        "id": o.id,
        "application_id": o.application_id,
        "offered_at": o.offered_at,
        "expires_on": o.expires_on,
        "offer_amount": o.offer_amount,
        "status": o.status,
        "accepted_at": o.accepted_at,
        "released_at": o.released_at,
    }


@router.get("/cycles/{cycle_id}/seats")
def seats(
    cycle_id: int,
    class_name: str | None = None,
    user: User = Depends(cycle_reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Filled against capacity per class — the top half of screen 1."""
    admission.cycle_for(db, user.school_id, cycle_id)
    from app.models import CycleClassConfig

    stmt = select(CycleClassConfig).where(CycleClassConfig.cycle_id == cycle_id)
    if class_name is not None:
        stmt = stmt.where(CycleClassConfig.class_name == class_name)
    rows = sorted(db.scalars(stmt), key=lambda c: class_sort_key(c.class_name))
    return [svc.seat_usage(db, cycle_id, c.class_name, c.stream) for c in rows]


@router.get("/cycles/{cycle_id}/merit")
def merit(
    cycle_id: int,
    class_name: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Screen 12. Decisions are made against a ranked class, not one
    application at a time (§5.1.2(5))."""
    admission.cycle_for(db, user.school_id, cycle_id)
    return {
        "seats": svc.seat_usage(db, cycle_id, class_name),
        "applicants": svc.merit_list(db, user.school_id, cycle_id, class_name),
    }


@router.post("/applications/{application_id}/decision")
def decide(
    application_id: int,
    body: DecisionInput,
    user: User = Depends(decider),
    db: Session = Depends(get_db),
) -> dict:
    app = app_svc.get(db, user.school_id, application_id)
    row = svc.decide(
        db,
        app,
        actor=user,
        decision=body.decision,
        reason=body.reason,
        seat_category=body.seat_category,
        conditions=body.conditions,
        over_allocation_approved=body.over_allocation_approved,
        may_over_allocate=authz_for(db, user).can("admission.decision.override"),
    )
    return {
        "application_id": app.id,
        "decision": row.decision,
        "status": app.status,
        "seat_category": row.seat_category,
        "over_allocation_approved": row.over_allocation_approved,
    }


@router.post("/cycles/{cycle_id}/decisions")
def decide_batch(
    cycle_id: int,
    body: BatchDecision,
    user: User = Depends(decider),
    db: Session = Depends(get_db),
) -> dict:
    """A batch from the merit view. Each row still carries its own reason —
    "top 40 by merit" is a reason, and it is recorded against every one of the
    forty."""
    admission.cycle_for(db, user.school_id, cycle_id)
    may_override = authz_for(db, user).can("admission.decision.override")
    results = []
    for item in body.decisions:
        app = app_svc.get(db, user.school_id, int(item["application_id"]))
        try:
            row = svc.decide(
                db,
                app,
                actor=user,
                decision=DecisionOutcome(item["decision"]),
                reason=item.get("reason", ""),
                seat_category=item.get("seat_category"),
                over_allocation_approved=bool(item.get("over_allocation_approved")),
                may_over_allocate=may_override,
            )
            results.append(
                {"application_id": app.id, "decision": row.decision, "ok": True}
            )
        except HTTPException as e:
            # One refusal does not abandon the other thirty-nine; the officer
            # gets a line per applicant saying what happened.
            results.append(
                {"application_id": app.id, "ok": False, "detail": e.detail}
            )
    return {"results": results}


@router.post(
    "/applications/{application_id}/offer",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admission.decision.make"))],
)
def issue_offer(
    application_id: int,
    body: OfferInput,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = app_svc.get(db, user.school_id, application_id)
    offer = svc.issue_offer(
        db,
        app,
        actor=user,
        expires_on=body.expires_on,
        offer_amount=body.offer_amount,
    )
    return _offer_out(offer)


@router.post(
    "/applications/{application_id}/offer/response",
    dependencies=[Depends(require_permission("admission.application.write"))],
)
def respond(
    application_id: int,
    body: OfferResponse,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Recorded by the office when the family answers. Declining releases the
    seat immediately and offers it to the next in the queue."""
    app = app_svc.get(db, user.school_id, application_id)
    offer = svc.respond_to_offer(
        db, app, actor=user, accepted=body.accepted, reason=body.reason
    )
    return {**_offer_out(offer), "application_status": app.status}


@router.get("/cycles/{cycle_id}/waitlist")
def waitlist(
    cycle_id: int,
    class_name: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    admission.cycle_for(db, user.school_id, cycle_id)
    rows = db.execute(
        select(WaitlistEntry, Application)
        .join(Application, Application.id == WaitlistEntry.application_id)
        .where(
            WaitlistEntry.cycle_id == cycle_id,
            WaitlistEntry.class_name == class_name,
        )
        .order_by(WaitlistEntry.rank)
    ).all()
    return [
        {
            "rank": entry.rank,
            "status": entry.status,
            "application_id": app.id,
            "application_no": app.application_no,
            "name": app.full_name,
            "application_status": app.status,
        }
        for entry, app in rows
    ]


@router.post(
    "/cycles/{cycle_id}/waitlist/promote",
    dependencies=[Depends(require_permission("admission.decision.make"))],
)
def promote(
    cycle_id: int,
    class_name: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Manual promotion, for the school that would rather confirm each one
    than have the job do it."""
    admission.cycle_for(db, user.school_id, cycle_id)
    app = svc.promote_next(db, cycle_id, class_name, actor=user)
    db.commit()
    if app is None:
        return {"promoted": None, "detail": "Nobody is waiting, or no seat is free"}
    return {"promoted": app.id, "application_no": app.application_no}


@router.get("/applications/{application_id}/decisions")
def decision_history(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """Append-only: a reversal is a new row, so this is the whole story."""
    from app.models import AdmissionDecision

    app = app_svc.get(db, user.school_id, application_id)
    rows = db.scalars(
        select(AdmissionDecision)
        .where(AdmissionDecision.application_id == app.id)
        .order_by(AdmissionDecision.decided_at)
    )
    return [
        {
            "decision": r.decision,
            "reason": r.reason,
            "seat_category": r.seat_category,
            "conditions": r.conditions,
            "over_allocation_approved": r.over_allocation_approved,
            "decided_by": r.decided_by,
            "decided_at": r.decided_at,
        }
        for r in rows
    ]
