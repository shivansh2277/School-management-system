"""Admission cycles, seat configuration and the enquiry register (§5.1).

The rules that live here rather than in a route: which cycle is the one being
worked on, whether a class in it still has seats, and how an enquiry moves
through the funnel without losing the reason it moved.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AdmissionCycle,
    AdmissionCycleStatus,
    CycleClassConfig,
    Enquiry,
    EnquiryInteraction,
    EnquiryStatus,
    User,
)

# Statuses that mean this enquiry will never become an application. Kept as a
# set so the funnel report and the follow-up list agree on what "closed" means.
CLOSED_ENQUIRY_STATUSES = {
    EnquiryStatus.converted,
    EnquiryStatus.not_interested,
    EnquiryStatus.lost_to_competitor,
    EnquiryStatus.invalid,
}


def cycle_for(db: Session, school_id: int, cycle_id: int) -> AdmissionCycle:
    cycle = db.get(AdmissionCycle, cycle_id)
    if cycle is None or cycle.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Admission cycle not found")
    return cycle


def open_cycle(db: Session, school_id: int) -> AdmissionCycle:
    """The cycle a walk-in enquiry or an online application belongs to.

    A school may have several cycles on the books — last year's, closed; next
    year's, still in planning — but only one taking applications at a time.
    """
    cycles = list(
        db.scalars(
            select(AdmissionCycle).where(
                AdmissionCycle.school_id == school_id,
                AdmissionCycle.status == AdmissionCycleStatus.open,
            )
        )
    )
    if not cycles:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This school has no open admission cycle"
        )
    if len(cycles) > 1:
        # Not a database constraint, because two cycles open at once is a
        # legitimate transitional state for staff — it is only ambiguous when
        # something has to *pick* one.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "More than one admission cycle is open; name the one you mean",
        )
    return cycles[0]


def class_config(
    db: Session, cycle_id: int, class_name: str, stream: str | None = None
) -> CycleClassConfig | None:
    return db.scalar(
        select(CycleClassConfig).where(
            CycleClassConfig.cycle_id == cycle_id,
            CycleClassConfig.class_name == class_name,
            CycleClassConfig.stream.is_(stream) if stream is None
            else CycleClassConfig.stream == stream,
        )
    )


def age_years_on(dob: date, on: date) -> Decimal:
    """Whole years plus the fraction, so a 5.5-year cut-off means what it says.

    Computed against the cycle's cut-off date rather than today (§5.1.9(1)):
    a child who is too young in April is still too young when the office
    finally opens the file in June.
    """
    days = (on - dob).days
    return (Decimal(days) / Decimal("365.25")).quantize(Decimal("0.01"))


def check_age(config: CycleClassConfig, dob: date | None) -> str | None:
    """Returns why the age is out of range, or None. Never raises: an
    out-of-range age is an override decision for a human, not a validation
    error that hides the applicant (§5.1.9(1))."""
    if dob is None or config.age_on is None:
        return None
    age = age_years_on(dob, config.age_on)
    if config.min_age_years is not None and age < config.min_age_years:
        return (
            f"Age {age} on {config.age_on} is below the minimum "
            f"{config.min_age_years} for class {config.class_name}"
        )
    if config.max_age_years is not None and age > config.max_age_years:
        return (
            f"Age {age} on {config.age_on} is above the maximum "
            f"{config.max_age_years} for class {config.class_name}"
        )
    return None


# ----------------------------------------------------------------- enquiries


def log_interaction(
    db: Session,
    enquiry: Enquiry,
    *,
    actor: User | None,
    channel,
    notes: str | None = None,
    outcome: EnquiryStatus | None = None,
    next_follow_up_on: date | None = None,
) -> EnquiryInteraction:
    """Record a contact and, if it changed anything, move the enquiry with it.

    Status and history move together on purpose: a register where someone can
    change the status without saying why is a register nobody trusts.
    """
    interaction = EnquiryInteraction(
        school_id=enquiry.school_id,
        enquiry_id=enquiry.id,
        occurred_at=datetime.now(UTC),
        channel=channel,
        notes=notes,
        outcome=outcome,
        by_user_id=actor.id if actor else None,
    )
    db.add(interaction)
    if outcome is not None:
        if enquiry.status is EnquiryStatus.converted:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This enquiry has already become an application",
            )
        enquiry.status = outcome
    if next_follow_up_on is not None:
        enquiry.next_follow_up_on = next_follow_up_on
    if outcome in CLOSED_ENQUIRY_STATUSES:
        # Nothing left to chase; leaving the date set would keep it on
        # somebody's list forever.
        enquiry.next_follow_up_on = None
    db.commit()
    return interaction


def funnel(db: Session, school_id: int, cycle_id: int) -> dict[str, int]:
    """Enquiry counts by status — the first half of the funnel report
    (§5.1.10). Applications add their own stages in the next unit."""
    counts = {s.value: 0 for s in EnquiryStatus}
    for enquiry in db.scalars(
        select(Enquiry).where(
            Enquiry.school_id == school_id, Enquiry.cycle_id == cycle_id
        )
    ):
        counts[enquiry.status.value] += 1
    return counts
