"""The admission dashboard and its reports (§5.1.3 screen 1, §5.1.10).

Every number here is computed on read. None of it is stored, because a stored
funnel is a funnel that disagrees with the register the first time somebody
corrects a status — and the number management actually asks for is "how are we
doing versus last year", which only means anything if both sides are computed
the same way.
"""

from datetime import UTC, date, datetime, timedelta
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AdmissionDecision,
    Application,
    ApplicationStatus,
    Assessment,
    AssessmentStatus,
    CycleClassConfig,
    DecisionOutcome,
    Enquiry,
    EnquiryStatus,
    Interview,
)
from app.services import selection
from app.services.common import class_sort_key

# The stages the funnel actually reports, in order. Statuses beyond a stage
# count towards it: an enrolled child was, at some point, tested.
FUNNEL_STAGES: list[tuple[str, set[ApplicationStatus]]] = [
    (
        "applied",
        set(ApplicationStatus) - {ApplicationStatus.draft},
    ),
    (
        "documents_verified",
        {
            ApplicationStatus.documents_verified,
            ApplicationStatus.assessment_scheduled,
            ApplicationStatus.assessment_completed,
            ApplicationStatus.interview_scheduled,
            ApplicationStatus.interview_completed,
            ApplicationStatus.decision_pending,
            ApplicationStatus.admitted,
            ApplicationStatus.waitlisted,
            ApplicationStatus.offer_issued,
            ApplicationStatus.offer_accepted,
            ApplicationStatus.fee_paid,
            ApplicationStatus.enrolled,
        },
    ),
    (
        "decided",
        {
            ApplicationStatus.admitted,
            ApplicationStatus.waitlisted,
            ApplicationStatus.rejected,
            ApplicationStatus.offer_issued,
            ApplicationStatus.offer_accepted,
            ApplicationStatus.offer_expired,
            ApplicationStatus.fee_paid,
            ApplicationStatus.enrolled,
        },
    ),
    (
        "admitted",
        {
            ApplicationStatus.admitted,
            ApplicationStatus.offer_issued,
            ApplicationStatus.offer_accepted,
            ApplicationStatus.fee_paid,
            ApplicationStatus.enrolled,
        },
    ),
    ("enrolled", {ApplicationStatus.enrolled}),
]


def _applications(db: Session, school_id: int, cycle_id: int) -> list[Application]:
    return list(
        db.scalars(
            select(Application).where(
                Application.school_id == school_id, Application.cycle_id == cycle_id
            )
        )
    )


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def funnel(db: Session, school_id: int, cycle_id: int) -> dict:
    """Enquiries through to enrolments, with the drop-off at each step.

    Enquiries lead the funnel because most of them never become anything, and
    that ratio is the number the module exists to improve (§5.1.2(1)).
    """
    enquiries = db.scalar(
        select(func.count())
        .select_from(Enquiry)
        .where(Enquiry.school_id == school_id, Enquiry.cycle_id == cycle_id)
    )
    apps = _applications(db, school_id, cycle_id)

    stages = [{"stage": "enquiries", "count": enquiries, "of_previous": None}]
    previous = enquiries
    for name, statuses in FUNNEL_STAGES:
        count = sum(1 for a in apps if a.status in statuses)
        stages.append(
            {"stage": name, "count": count, "of_previous": _pct(count, previous)}
        )
        previous = count

    tested = sum(
        1
        for a in apps
        if db.scalar(
            select(Assessment.id).where(
                Assessment.application_id == a.id,
                Assessment.status == AssessmentStatus.completed,
            )
        )
    )
    interviewed = sum(
        1
        for a in apps
        if db.scalar(
            select(Interview.id).where(
                Interview.application_id == a.id,
                Interview.status == AssessmentStatus.completed,
            )
        )
    )
    return {
        "stages": stages,
        "tested": tested,
        "interviewed": interviewed,
        "overall_conversion_pct": _pct(
            sum(1 for a in apps if a.status is ApplicationStatus.enrolled), enquiries
        ),
    }


def by_source(db: Session, school_id: int, cycle_id: int) -> list[dict]:
    """Which channels actually produce students, not just enquiries."""
    apps = _applications(db, school_id, cycle_id)
    rows: dict[str, dict] = {}
    for enquiry in db.scalars(
        select(Enquiry).where(
            Enquiry.school_id == school_id, Enquiry.cycle_id == cycle_id
        )
    ):
        row = rows.setdefault(
            enquiry.source.value,
            {"source": enquiry.source.value, "enquiries": 0, "applications": 0, "enrolled": 0},
        )
        row["enquiries"] += 1
    for app in apps:
        row = rows.setdefault(
            app.source.value,
            {"source": app.source.value, "enquiries": 0, "applications": 0, "enrolled": 0},
        )
        row["applications"] += 1
        if app.status is ApplicationStatus.enrolled:
            row["enrolled"] += 1
    for row in rows.values():
        row["conversion_pct"] = _pct(
            row["enrolled"], row["enquiries"] or row["applications"]
        )
    return sorted(rows.values(), key=lambda r: -r["enrolled"])


def seat_utilisation(db: Session, school_id: int, cycle_id: int) -> list[dict]:
    out = []
    for config in sorted(
        db.scalars(
            select(CycleClassConfig).where(CycleClassConfig.cycle_id == cycle_id)
        ),
        key=lambda c: class_sort_key(c.class_name),
    ):
        usage = selection.seat_usage(db, cycle_id, config.class_name, config.stream)
        waiting = db.scalar(
            select(func.count())
            .select_from(Application)
            .where(
                Application.cycle_id == cycle_id,
                Application.class_applying_for == config.class_name,
                Application.status == ApplicationStatus.waitlisted,
            )
        )
        offers = [
            a.status
            for a in db.scalars(
                select(Application).where(
                    Application.cycle_id == cycle_id,
                    Application.class_applying_for == config.class_name,
                    Application.status.in_(
                        [
                            ApplicationStatus.offer_issued,
                            ApplicationStatus.offer_accepted,
                            ApplicationStatus.offer_expired,
                            ApplicationStatus.fee_paid,
                            ApplicationStatus.enrolled,
                        ]
                    ),
                )
            )
        ]
        accepted = sum(
            1
            for s in offers
            if s
            in (
                ApplicationStatus.offer_accepted,
                ApplicationStatus.fee_paid,
                ApplicationStatus.enrolled,
            )
        )
        expired = sum(1 for s in offers if s is ApplicationStatus.offer_expired)
        out.append(
            {
                **usage,
                "filled_pct": _pct(usage["taken"], usage["total_seats"]),
                "waitlist_depth": waiting,
                "offers_made": len(offers),
                "offer_acceptance_pct": _pct(accepted, len(offers)),
                "offer_expiry_pct": _pct(expired, len(offers)),
            }
        )
    return out


def demographics(db: Session, school_id: int, cycle_id: int) -> dict:
    apps = [
        a
        for a in _applications(db, school_id, cycle_id)
        if a.status is not ApplicationStatus.draft
    ]
    admitted = [
        a
        for a in apps
        if a.status
        in (
            ApplicationStatus.admitted,
            ApplicationStatus.offer_issued,
            ApplicationStatus.offer_accepted,
            ApplicationStatus.fee_paid,
            ApplicationStatus.enrolled,
        )
    ]

    def tally(rows, key):
        out: dict[str, int] = {}
        for r in rows:
            value = getattr(r, key)
            label = (value.value if hasattr(value, "value") else value) or "unstated"
            out[label] = out.get(label, 0) + 1
        return out

    return {
        "applied": {
            "gender": tally(apps, "gender"),
            "category": tally(apps, "admission_category"),
            "caste_category": tally(apps, "caste_category"),
        },
        "admitted": {
            "gender": tally(admitted, "gender"),
            "category": tally(admitted, "admission_category"),
        },
        # The share of intake §5.1.10 asks for by name.
        "sibling_share_pct": _pct(
            sum(1 for a in admitted if a.sibling_verified), len(admitted)
        ),
        "staff_ward_share_pct": _pct(
            sum(1 for a in admitted if a.staff_ward_verified), len(admitted)
        ),
    }


def rejections(db: Session, school_id: int, cycle_id: int) -> list[dict]:
    """Reasons grouped, to expose whether the criteria are being applied
    consistently — which is the whole point of insisting on a reason."""
    rows = db.execute(
        select(AdmissionDecision.reason, func.count())
        .join(Application, Application.id == AdmissionDecision.application_id)
        .where(
            Application.cycle_id == cycle_id,
            AdmissionDecision.school_id == school_id,
            AdmissionDecision.decision == DecisionOutcome.rejected,
        )
        .group_by(AdmissionDecision.reason)
        .order_by(func.count().desc())
    ).all()
    return [{"reason": reason, "count": count} for reason, count in rows]


def cycle_time(db: Session, school_id: int, cycle_id: int) -> dict:
    """Median days from submission to decision, and to enrolment.

    Reported as a median rather than a mean: one application that sat over the
    summer holidays would drag an average into meaninglessness.
    """
    to_decision = []
    to_enrolment = []
    for app in _applications(db, school_id, cycle_id):
        if app.submitted_at is None:
            continue
        submitted = app.submitted_at
        if submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=UTC)
        decision = selection.latest_decision(db, app.id)
        if decision is not None:
            decided = decision.decided_at
            if decided.tzinfo is None:
                decided = decided.replace(tzinfo=UTC)
            to_decision.append((decided - submitted).days)
        if app.status is ApplicationStatus.enrolled:
            to_enrolment.append((datetime.now(UTC) - submitted).days)
    return {
        "median_days_to_decision": median(to_decision) if to_decision else None,
        "median_days_to_enrolment": median(to_enrolment) if to_enrolment else None,
        "decided": len(to_decision),
    }


def dashboard(db: Session, school_id: int, cycle_id: int, *, today: date | None = None) -> dict:
    """Screen 1: what the admission office needs on opening the laptop."""
    today = today or date.today()
    # The school's day, not UTC's. Comparing a local `today` against UTC
    # midnight put a 1:40 a.m. test on the wrong side of the boundary — the
    # office in Lucknow is five and a half hours ahead of the column.
    # ponytail: the server's local zone stands in for the school's; give
    # `schools` a timezone when the product is sold outside one country.
    start = datetime.combine(today, datetime.min.time()).astimezone(UTC)
    end = start + timedelta(days=1)

    awaiting = {}
    for app in _applications(db, school_id, cycle_id):
        if app.status in (ApplicationStatus.draft, ApplicationStatus.enrolled):
            continue
        awaiting[app.status.value] = awaiting.get(app.status.value, 0) + 1

    tests_today = db.scalars(
        select(Assessment).where(
            Assessment.school_id == school_id,
            Assessment.scheduled_at >= start,
            Assessment.scheduled_at < end,
        )
    ).all()
    interviews_today = db.scalars(
        select(Interview).where(
            Interview.school_id == school_id,
            Interview.scheduled_at >= start,
            Interview.scheduled_at < end,
        )
    ).all()
    follow_ups_due = db.scalar(
        select(func.count())
        .select_from(Enquiry)
        .where(
            Enquiry.school_id == school_id,
            Enquiry.cycle_id == cycle_id,
            Enquiry.next_follow_up_on.is_not(None),
            Enquiry.next_follow_up_on <= today,
            Enquiry.status.not_in(
                [
                    EnquiryStatus.converted,
                    EnquiryStatus.not_interested,
                    EnquiryStatus.lost_to_competitor,
                    EnquiryStatus.invalid,
                ]
            ),
        )
    )
    return {
        "funnel": funnel(db, school_id, cycle_id),
        "seats": seat_utilisation(db, school_id, cycle_id),
        "awaiting_action": awaiting,
        "today": {
            "tests": [
                {
                    "assessment_id": a.id,
                    "application_id": a.application_id,
                    "scheduled_at": a.scheduled_at,
                    "venue": a.venue,
                    "seat_no": a.seat_no,
                }
                for a in tests_today
            ],
            "interviews": [
                {
                    "interview_id": i.id,
                    "application_id": i.application_id,
                    "scheduled_at": i.scheduled_at,
                    "venue": i.venue,
                }
                for i in interviews_today
            ],
            "follow_ups_due": follow_ups_due,
        },
        "by_source": by_source(db, school_id, cycle_id),
    }
