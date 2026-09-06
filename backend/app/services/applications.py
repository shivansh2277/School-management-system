"""The application pipeline: drafts, submission and status movement (§5.1).

Three rules from §5.1.9 live here because they are the ones a route would get
subtly wrong:

* an out-of-range age is an **override with a reason**, never a validation
  error that hides the applicant;
* a duplicate is a **warning with the matching records shown**, never a block —
  genuine twins exist, and a hard block just produces a second, worse record;
* a backward status move is **allowed and audited**, because real admissions
  offices reopen decisions.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status as http
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import (
    AdmissionCategory,
    AdmissionCycle,
    Application,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationSibling,
    ApplicationStatus,
    AuditAction,
    Employee,
    Enrolment,
    Student,
    User,
)
from app.services import admission, audit

# The order the pipeline normally runs in. Anything not in this list — the
# terminal and exception states — is reachable from anywhere, which is what
# makes a withdrawal or a cancellation possible at any point.
FORWARD_ORDER = [
    ApplicationStatus.draft,
    ApplicationStatus.submitted,
    ApplicationStatus.under_document_verification,
    ApplicationStatus.documents_verified,
    ApplicationStatus.assessment_scheduled,
    ApplicationStatus.assessment_completed,
    ApplicationStatus.interview_scheduled,
    ApplicationStatus.interview_completed,
    ApplicationStatus.decision_pending,
    ApplicationStatus.admitted,
    ApplicationStatus.offer_issued,
    ApplicationStatus.offer_accepted,
    ApplicationStatus.fee_paid,
    ApplicationStatus.enrolled,
]

# Classes where "which school were you at before" has no answer.
PRE_PRIMARY = {"Nursery", "LKG", "UKG", "PP1", "PP2"}

# Once a child is a student, Admission is done with them. Undoing it is a
# withdrawal in the Student module, not an edit here (§5.1.7).
TERMINAL = {ApplicationStatus.enrolled}


def get(db: Session, school_id: int, application_id: int) -> Application:
    app = db.get(Application, application_id)
    if app is None or app.school_id != school_id:
        raise HTTPException(http.HTTP_404_NOT_FOUND, "Application not found")
    return app


def guardians(db: Session, application_id: int) -> list[ApplicationGuardian]:
    return list(
        db.scalars(
            select(ApplicationGuardian)
            .where(ApplicationGuardian.application_id == application_id)
            .order_by(ApplicationGuardian.is_primary.desc(), ApplicationGuardian.id)
        )
    )


def duplicate_warnings(db: Session, app: Application) -> list[dict]:
    """Applications that might be this same child (§5.1.9(2)).

    Same surname and date of birth, or a guardian mobile already on file. A
    soft warning with the matches shown — never a block.
    """
    matches: dict[int, dict] = {}

    def add(other: Application, reason: str) -> None:
        # One row per matching application, carrying every reason it matched:
        # "same date of birth *and* the same mobile" is a much stronger signal
        # than either alone, and the clerk deciding needs to see both.
        entry = matches.setdefault(
            other.id,
            {
                "application_id": other.id,
                "application_no": other.application_no,
                "name": other.full_name,
                "reasons": [],
            },
        )
        entry["reasons"].append(reason)

    for other in db.scalars(
        select(Application).where(
            Application.school_id == app.school_id,
            Application.id != app.id,
            Application.last_name.ilike(app.last_name),
            Application.date_of_birth == app.date_of_birth,
        )
    ):
        add(other, "Same surname and date of birth")

    mobiles = [g.mobile for g in guardians(db, app.id)]
    if mobiles:
        rows = db.execute(
            select(Application, ApplicationGuardian.mobile)
            .join(
                ApplicationGuardian,
                ApplicationGuardian.application_id == Application.id,
            )
            .where(
                Application.school_id == app.school_id,
                Application.id != app.id,
                ApplicationGuardian.mobile.in_(mobiles),
            )
        ).all()
        for other, mobile in rows:
            add(other, f"Guardian mobile {mobile} is already on another application")

    return sorted(matches.values(), key=lambda m: m["application_id"])


def _missing_for_submission(db: Session, app: Application) -> list[str]:
    """Steps 1-3 are mandatory to submit; the rest may complete later
    (§5.1.4)."""
    missing = []
    if not (app.first_name and app.last_name and app.date_of_birth and app.gender):
        missing.append("applicant details")
    if not app.class_applying_for:
        missing.append("class applied for")
    people = guardians(db, app.id)
    if not people:
        missing.append("at least one guardian")
    elif sum(1 for g in people if g.is_primary) != 1:
        missing.append("exactly one primary contact")
    return missing


def submit(db: Session, app: Application, *, actor: User | None) -> dict:
    """Draft -> submitted. Allocates the application number and returns the
    soft warnings the office needs to see, rather than refusing on them."""
    if app.status is not ApplicationStatus.draft:
        raise HTTPException(
            http.HTTP_409_CONFLICT, "This application has already been submitted"
        )
    missing = _missing_for_submission(db, app)
    if missing:
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            "Cannot submit without: " + ", ".join(missing),
        )

    cycle = db.get(AdmissionCycle, app.cycle_id)
    if not cycle.is_open:
        raise HTTPException(
            http.HTTP_409_CONFLICT, "This admission cycle is not accepting applications"
        )

    warnings = []
    config = admission.class_config(db, app.cycle_id, app.class_applying_for, app.stream)
    if config is None:
        warnings.append(
            f"Class {app.class_applying_for} is not configured in this cycle"
        )
    else:
        age_problem = admission.check_age(config, app.date_of_birth)
        if age_problem and not app.age_override_reason:
            warnings.append(age_problem)

    duplicates = duplicate_warnings(db, app)

    app.application_no = audit.next_number(
        db,
        app.school_id,
        kind="application",
        year=cycle.academic_year.start_date.year,
        prefix="APP",
        width=5,
    )
    app.status = ApplicationStatus.submitted
    app.submitted_at = datetime.now(UTC)
    audit.record(
        db,
        actor=actor,
        school_id=app.school_id,
        entity_type="application",
        entity_id=app.id,
        action=AuditAction.create,
        after={"application_no": app.application_no, "status": app.status.value},
    )
    db.commit()
    return {"warnings": warnings, "possible_duplicates": duplicates}


def move(
    db: Session,
    app: Application,
    to: ApplicationStatus,
    *,
    actor: User | None,
    reason: str | None = None,
) -> Application:
    """Move the application, demanding a reason for anything but a step
    forward (§5.1.7)."""
    if app.status in TERMINAL:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            "An enrolled application is closed; withdraw the student instead",
        )
    if to is app.status:
        return app

    forward = (
        to in FORWARD_ORDER
        and app.status in FORWARD_ORDER
        and FORWARD_ORDER.index(to) > FORWARD_ORDER.index(app.status)
    )
    if not forward and not (reason and reason.strip()):
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Moving an application back to {to.value} requires a reason",
        )

    before = {"status": app.status.value}
    app.status = to
    audit.record(
        db,
        actor=actor,
        school_id=app.school_id,
        entity_type="application",
        entity_id=app.id,
        action=AuditAction.status_change,
        before=before,
        after={"status": to.value},
        # Forward moves are routine; the audit log still records them, and
        # `record` only insists on a reason for the ones that matter.
        reason=reason or f"Advanced to {to.value}",
    )
    db.commit()
    return app


def match_sibling(db: Session, school_id: int, query: str) -> list[dict]:
    """Search enrolled students so a sibling claim links to a real record
    rather than being typed in free text (§5.1.4 step 4)."""
    like = f"%{query}%"
    rows = db.execute(
        select(Student, User.full_name)
        .join(User, User.id == Student.user_id)
        .where(
            Student.school_id == school_id,
            or_(User.full_name.ilike(like), Student.admission_no.ilike(like)),
        )
        .limit(10)
    ).all()
    out = []
    for student, name in rows:
        enrolment = db.scalar(
            select(Enrolment)
            .where(Enrolment.student_id == student.id)
            .order_by(Enrolment.id.desc())
        )
        out.append(
            {
                "student_id": student.id,
                "name": name,
                "admission_no": student.admission_no,
                "class_label": enrolment.class_section.label if enrolment else "",
            }
        )
    return out


def refresh_claims(db: Session, app: Application) -> Application:
    """Turn the sibling and staff-ward *claims* into verified facts, or leave
    them false. Nothing else in the module may set these flags."""
    app.sibling_verified = bool(
        db.scalar(
            select(ApplicationSibling.id).where(
                ApplicationSibling.application_id == app.id,
                ApplicationSibling.student_id.is_not(None),
            )
        )
    )
    app.staff_ward_verified = bool(
        db.scalar(
            select(ApplicationGuardian.id)
            .join(Employee, Employee.id == ApplicationGuardian.employee_id)
            .where(
                ApplicationGuardian.application_id == app.id,
                Employee.school_id == app.school_id,
            )
        )
    )
    # A category the school cannot stand behind is not a priority. The claim
    # stays on the record; it just stops counting until somebody links it.
    db.commit()
    return app


def completeness(db: Session, app: Application) -> int:
    """The percentage the multi-step form shows. Computed rather than stored,
    so it cannot drift from the data it describes."""
    has_siblings = bool(
        db.scalar(
            select(ApplicationSibling.id).where(
                ApplicationSibling.application_id == app.id
            )
        )
    )
    has_medical = bool(
        db.scalar(
            select(ApplicationMedical.id).where(
                ApplicationMedical.application_id == app.id
            )
        )
    )
    steps = [
        bool(app.first_name and app.last_name and app.date_of_birth and app.gender),
        bool(app.class_applying_for),
        bool(guardians(db, app.id)),
        app.is_single_child or has_siblings,
        bool(app.address),
        # A previous school is meaningless for a child starting at the bottom.
        bool(app.previous_school) or app.class_applying_for in PRE_PRIMARY,
        has_medical,
        bool((app.declarations or {}).get("information_accuracy")),
    ]
    return round(100 * sum(1 for s in steps if s) / len(steps))


def eligible_categories(app: Application) -> AdmissionCategory:
    """The category actually applicable once claims are verified."""
    if app.admission_category is AdmissionCategory.sibling and not app.sibling_verified:
        return AdmissionCategory.general
    if (
        app.admission_category is AdmissionCategory.staff_ward
        and not app.staff_ward_verified
    ):
        return AdmissionCategory.general
    return app.admission_category


