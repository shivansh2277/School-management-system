"""Selection against seats, decisions, offers and the waitlist (§5.1.9(11)-(14)).

Decisions are made in batches against capacity, not one application at a time
(§5.1.2(5)), so the merit list is the primary object here and the decision is
what falls out of it.

Four rules carry the module's weight:

11. Admitting past capacity requires an explicit approval with a reason.
12. A General admission may not consume a reserved seat.
13. Every decision carries a reason, including the admits.
14. Every offer has an expiry; on lapse the seat returns and the next
    waitlisted applicant is offered it.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status as http
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AdmissionCategory,
    AdmissionDecision,
    AdmissionOffer,
    Application,
    ApplicationStatus,
    Assessment,
    AssessmentStatus,
    AuditAction,
    DecisionOutcome,
    Interview,
    OfferStatus,
    User,
    WaitlistEntry,
    WaitlistStatus,
)
from app.services import admission, audit
from app.services import applications as app_svc

# Statuses that mean this applicant is holding a seat. An offer that has been
# issued holds one just as firmly as an enrolment does — that is the entire
# reason offers expire.
HOLDING_A_SEAT = {
    ApplicationStatus.admitted,
    ApplicationStatus.offer_issued,
    ApplicationStatus.offer_accepted,
    ApplicationStatus.fee_paid,
    ApplicationStatus.enrolled,
}

# How strongly an interview panel's verdict counts, on the same 0-100 scale as
# an assessment percentage, so the two can be combined without a magic weight.
RECOMMENDATION_SCORE = {
    "strong_admit": 100,
    "admit": 75,
    "waitlist": 40,
    "reject": 0,
}


def seat_usage(db: Session, cycle_id: int, class_name: str, stream: str | None = None) -> dict:
    config = admission.class_config(db, cycle_id, class_name, stream)
    if config is None:
        raise HTTPException(
            http.HTTP_404_NOT_FOUND,
            f"Class {class_name} is not configured in this cycle",
        )
    holders = list(
        db.scalars(
            select(Application).where(
                Application.cycle_id == cycle_id,
                Application.class_applying_for == class_name,
                Application.status.in_(HOLDING_A_SEAT),
            )
        )
    )
    reserved = {k.upper(): v for k, v in (config.reserved_seats or {}).items()}
    by_category: dict[str, int] = {}
    for app in holders:
        seat = _seat_category_of(db, app)
        by_category[seat] = by_category.get(seat, 0) + 1

    reserved_total = sum(reserved.values())
    general_taken = sum(v for k, v in by_category.items() if k not in reserved)
    return {
        "class_name": class_name,
        "stream": stream,
        "total_seats": config.total_seats,
        "reserved": reserved,
        "taken": len(holders),
        "taken_by_category": by_category,
        # What a General applicant can still be given without eating into a
        # reserved pool (§5.1.9(12)).
        "general_seats": max(config.total_seats - reserved_total, 0),
        "general_available": max(config.total_seats - reserved_total - general_taken, 0),
        "available": max(config.total_seats - len(holders), 0),
    }


def _seat_category_of(db: Session, app: Application) -> str:
    """Which pool this applicant's seat comes from.

    The *claimed* category is irrelevant here; only what was verified counts,
    which is why an unverified sibling claim cannot quietly take a reserved
    seat (§5.1.9(6)).
    """
    decision = latest_decision(db, app.id)
    if decision is not None and decision.seat_category:
        return decision.seat_category.upper()
    if app.caste_category:
        return app.caste_category.upper()
    return app_svc.eligible_categories(app).value.upper()


def latest_decision(db: Session, application_id: int) -> AdmissionDecision | None:
    return db.scalar(
        select(AdmissionDecision)
        .where(AdmissionDecision.application_id == application_id)
        .order_by(AdmissionDecision.decided_at.desc(), AdmissionDecision.id.desc())
    )


def _score(db: Session, app: Application) -> dict:
    """The comparable numbers behind one applicant, kept separate rather than
    fused into a single opaque total: the officer ranking a class has to be
    able to say why one child is above another."""
    assessments = list(
        db.scalars(select(Assessment).where(Assessment.application_id == app.id))
    )
    scored = [a for a in assessments if a.percent is not None]
    assessment_pct = (
        (sum(a.percent for a in scored) / len(scored)).quantize(Decimal("0.01"))
        if scored
        else None
    )
    absent = any(a.status is AssessmentStatus.absent for a in assessments)

    interviews = list(
        db.scalars(select(Interview).where(Interview.application_id == app.id))
    )
    recommendations = [
        s.get("recommendation")
        for i in interviews
        for s in (i.structured_scores or {}).values()
        if s and s.get("recommendation")
    ]
    interview_score = (
        Decimal(
            sum(RECOMMENDATION_SCORE.get(r, 0) for r in recommendations)
            / len(recommendations)
        ).quantize(Decimal("0.01"))
        if recommendations
        else None
    )

    category = app_svc.eligible_categories(app)
    # Verified priority, in the order a school actually applies it.
    priority = {
        AdmissionCategory.staff_ward: 0,
        AdmissionCategory.sibling: 1,
        AdmissionCategory.alumni_child: 2,
        AdmissionCategory.management: 3,
    }.get(category, 9)

    parts = [p for p in (assessment_pct, interview_score) if p is not None]
    composite = (sum(parts) / len(parts)).quantize(Decimal("0.01")) if parts else None

    return {
        "application_id": app.id,
        "application_no": app.application_no,
        "name": app.full_name,
        "status": app.status.value,
        "category": category.value,
        "priority": priority,
        "assessment_percent": assessment_pct,
        "was_absent": absent,
        "interview_score": interview_score,
        "composite": composite,
        "documents_outstanding": app_svc.outstanding_documents(db, app),
        "submitted_at": app.submitted_at,
    }


def merit_list(
    db: Session, school_id: int, cycle_id: int, class_name: str
) -> list[dict]:
    """The ranked comparison of screen 12, with the components visible.

    Ordered by verified priority, then by the composite score, then by who
    applied first. An applicant with no score yet sorts last rather than
    first — an unassessed child must never outrank an assessed one by accident.
    """
    apps = db.scalars(
        select(Application).where(
            Application.school_id == school_id,
            Application.cycle_id == cycle_id,
            Application.class_applying_for == class_name,
            Application.status.not_in(
                [
                    ApplicationStatus.draft,
                    ApplicationStatus.rejected,
                    ApplicationStatus.withdrawn_by_parent,
                ]
            ),
        )
    )
    rows = [_score(db, a) for a in apps]
    rows.sort(
        key=lambda r: (
            r["priority"],
            -(r["composite"] or Decimal("-1")),
            r["submitted_at"] or datetime.max.replace(tzinfo=UTC),
        )
    )
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


def decide(
    db: Session,
    app: Application,
    *,
    actor: User,
    decision: DecisionOutcome,
    reason: str,
    seat_category: str | None = None,
    conditions: str | None = None,
    over_allocation_approved: bool = False,
    may_over_allocate: bool = False,
) -> AdmissionDecision:
    if not (reason and reason.strip()):
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            "Every admission decision needs a reason, including an admit",
        )

    if decision is DecisionOutcome.admitted:
        usage = seat_usage(db, app.cycle_id, app.class_applying_for, app.stream)
        pool = (seat_category or _seat_category_of(db, app)).upper()
        reserved = usage["reserved"]

        if pool in reserved:
            taken = usage["taken_by_category"].get(pool, 0)
            if taken >= reserved[pool] and not over_allocation_approved:
                raise HTTPException(
                    http.HTTP_409_CONFLICT,
                    f"The {pool} pool is full ({taken}/{reserved[pool]})",
                )
        elif usage["general_available"] <= 0 and not over_allocation_approved:
            # Silent over-admission is one of the more damaging failures
            # possible here (§5.1.9(11)).
            raise HTTPException(
                http.HTTP_409_CONFLICT,
                f"Class {app.class_applying_for} is full "
                f"({usage['taken']}/{usage['total_seats']} seats). "
                "An over-allocation must be approved explicitly.",
            )

        if over_allocation_approved and not may_over_allocate:
            raise HTTPException(
                http.HTTP_403_FORBIDDEN,
                "Approving an over-allocation needs admission.decision.override",
            )
        seat_category = pool

    row = AdmissionDecision(
        school_id=app.school_id,
        application_id=app.id,
        decision=decision,
        decided_by=actor.id,
        decided_at=datetime.now(UTC),
        reason=reason,
        seat_category=seat_category,
        conditions=conditions,
        over_allocation_approved=over_allocation_approved,
    )
    db.add(row)

    target = {
        DecisionOutcome.admitted: ApplicationStatus.admitted,
        DecisionOutcome.waitlisted: ApplicationStatus.waitlisted,
        DecisionOutcome.rejected: ApplicationStatus.rejected,
    }[decision]
    app_svc.move(db, app, target, actor=actor, reason=reason)

    if decision is DecisionOutcome.waitlisted:
        add_to_waitlist(db, app)
    db.commit()
    return row


def add_to_waitlist(db: Session, app: Application) -> WaitlistEntry:
    existing = db.scalar(
        select(WaitlistEntry).where(WaitlistEntry.application_id == app.id)
    )
    if existing is not None:
        existing.status = WaitlistStatus.waiting
        return existing
    last = db.scalar(
        select(WaitlistEntry.rank)
        .where(
            WaitlistEntry.cycle_id == app.cycle_id,
            WaitlistEntry.class_name == app.class_applying_for,
        )
        .order_by(WaitlistEntry.rank.desc())
    )
    entry = WaitlistEntry(
        school_id=app.school_id,
        cycle_id=app.cycle_id,
        class_name=app.class_applying_for,
        application_id=app.id,
        rank=(last or 0) + 1,
    )
    db.add(entry)
    db.flush()
    return entry


def issue_offer(
    db: Session,
    app: Application,
    *,
    actor: User | None,
    expires_on: date,
    offer_amount: Decimal | None = None,
) -> AdmissionOffer:
    if app.status is not ApplicationStatus.admitted:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            "An offer can only be issued to an admitted applicant",
        )
    if expires_on <= date.today():
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            "An offer must expire in the future",
        )
    offer = AdmissionOffer(
        school_id=app.school_id,
        application_id=app.id,
        offered_at=datetime.now(UTC),
        expires_on=expires_on,
        offer_amount=offer_amount,
    )
    db.add(offer)
    app_svc.move(db, app, ApplicationStatus.offer_issued, actor=actor)
    db.commit()
    return offer


def current_offer(db: Session, application_id: int) -> AdmissionOffer | None:
    return db.scalar(
        select(AdmissionOffer)
        .where(
            AdmissionOffer.application_id == application_id,
            AdmissionOffer.status == OfferStatus.issued,
        )
        .order_by(AdmissionOffer.id.desc())
    )


def respond_to_offer(
    db: Session, app: Application, *, actor: User | None, accepted: bool, reason: str | None = None
) -> AdmissionOffer:
    offer = current_offer(db, app.id)
    if offer is None:
        raise HTTPException(http.HTTP_404_NOT_FOUND, "No open offer on this application")
    now = datetime.now(UTC)
    if accepted:
        offer.status = OfferStatus.accepted
        offer.accepted_at = now
        app_svc.move(db, app, ApplicationStatus.offer_accepted, actor=actor)
    else:
        offer.status = OfferStatus.declined
        offer.released_at = now
        app_svc.move(
            db,
            app,
            ApplicationStatus.withdrawn_by_parent,
            actor=actor,
            reason=reason or "The family declined the offer",
        )
        promote_next(db, app.cycle_id, app.class_applying_for, actor=actor)
    db.commit()
    return offer


def promote_next(
    db: Session, cycle_id: int, class_name: str, *, actor: User | None
) -> Application | None:
    """Offer the released seat to the head of the queue (§5.1.9(14)).

    Returns the applicant promoted, or None when the queue is empty. Whether
    this runs automatically or waits for a human is the school's call; the job
    calls it, and an officer can call it from the waitlist screen.
    """
    entry = db.scalar(
        select(WaitlistEntry)
        .where(
            WaitlistEntry.cycle_id == cycle_id,
            WaitlistEntry.class_name == class_name,
            WaitlistEntry.status == WaitlistStatus.waiting,
        )
        .order_by(WaitlistEntry.rank)
    )
    if entry is None:
        return None
    app = db.get(Application, entry.application_id)
    usage = seat_usage(db, cycle_id, class_name)
    if usage["available"] <= 0:
        return None

    db.add(
        AdmissionDecision(
            school_id=app.school_id,
            application_id=app.id,
            decision=DecisionOutcome.admitted,
            decided_by=actor.id if actor else None,
            decided_at=datetime.now(UTC),
            reason=f"Promoted from waitlist rank {entry.rank} as a seat was released",
            seat_category=_seat_category_of(db, app),
        )
    )
    app_svc.move(
        db,
        app,
        ApplicationStatus.admitted,
        actor=actor,
        reason="Promoted from the waitlist",
    )
    entry.status = WaitlistStatus.offered
    db.flush()
    return app


def expire_offers(db: Session, school_id: int, *, today: date | None = None) -> dict:
    """Lapse every offer past its expiry, release the seat, and offer it on.

    This is the automation §5.1.2(6) calls a large part of the module's value:
    without it a seat sits behind a family who stopped answering the phone in
    March and the waitlist never moves.
    """
    today = today or date.today()
    lapsed = list(
        db.scalars(
            select(AdmissionOffer).where(
                AdmissionOffer.school_id == school_id,
                AdmissionOffer.status == OfferStatus.issued,
                AdmissionOffer.expires_on < today,
            )
        )
    )
    promoted = []
    for offer in lapsed:
        app = db.get(Application, offer.application_id)
        offer.status = OfferStatus.expired
        offer.released_at = datetime.now(UTC)
        app_svc.move(
            db,
            app,
            ApplicationStatus.offer_expired,
            actor=None,
            reason=f"The offer expired on {offer.expires_on}",
        )
        audit.record(
            db,
            actor=None,
            school_id=school_id,
            entity_type="admission_offer",
            entity_id=offer.id,
            action=AuditAction.status_change,
            before={"status": OfferStatus.issued.value},
            after={"status": OfferStatus.expired.value},
            reason=f"Expired on {offer.expires_on}; the seat returns to the pool",
        )
        next_app = promote_next(db, app.cycle_id, app.class_applying_for, actor=None)
        if next_app is not None:
            promoted.append(next_app.application_no)
    db.flush()
    return {"expired": len(lapsed), "promoted": promoted}
