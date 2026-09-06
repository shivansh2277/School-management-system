"""The public admission portal (§0.13, §5.1.3 screen 6).

Everything here is unauthenticated, which makes it the only part of the product
a stranger can reach. Three consequences run through the whole file:

* **The school comes from the URL, not from a session.** `/public/{school_code}`
  identifies the tenant; nothing else may.
* **Nothing is disclosed that was not already known to the asker.** The status
  endpoint takes an application number *and* the child's date of birth, and
  answers the same way whether the number is wrong or the date is — otherwise
  it is an enumeration oracle for other people's children.
* **A submission here is a claim, not a decision.** It lands as `submitted` and
  waits for staff, per §0.13's "admin login gate before an application is
  acted on".

Spam protection is a honeypot plus a per-address rate limit counted from the
audit log, which already records the IP of every write. That is deliberately
not a CAPTCHA: a school in Lucknow with intermittent connectivity should not
have a Google widget between a parent and their child's admission.
"""

from datetime import UTC, date as Date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AdmissionCategory,
    Application,
    ApplicationGuardian,
    ApplicationStatus,
    AuditAction,
    AuditLog,
    CycleClassConfig,
    EnquirySource,
    GuardianRelation,
    School,
    SchoolStatus,
)
from app.services import admission, audit
from app.services import applications as svc
from app.services import school_settings

router = APIRouter(prefix="/public/{school_code}/admission", tags=["public"])

# Five applications an hour from one address is far more than a family needs
# and far less than a script wants.
MAX_APPLICATIONS_PER_IP_PER_HOUR = 5


def _school(db: Session, school_code: str) -> School:
    school = db.scalar(select(School).where(School.code == school_code))
    # A closed or suspended school is indistinguishable from one that never
    # existed: the portal must not confirm which schools are customers.
    if school is None or school.status is not SchoolStatus.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such school")
    if not school_settings.enabled(db, school.id, "admission"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such school")
    return school


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _rate_limit(db: Session, school_id: int, ip: str | None) -> None:
    if ip is None:
        return
    since = datetime.now(UTC) - timedelta(hours=1)
    recent = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(
            AuditLog.school_id == school_id,
            AuditLog.entity_type == "application",
            AuditLog.ip == ip,
            AuditLog.occurred_at >= since,
        )
    )
    if recent >= MAX_APPLICATIONS_PER_IP_PER_HOUR:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many applications from this connection. Please try again later, "
            "or call the school office.",
        )


class PublicGuardian(BaseModel):
    model_config = {"extra": "forbid"}

    relation: GuardianRelation
    full_name: str
    mobile: str = Field(pattern=r"^\d{10}$")
    email: str | None = None
    occupation: str | None = None
    is_primary: bool = False


class PublicApplication(BaseModel):
    model_config = {"extra": "forbid"}

    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    middle_name: str | None = None
    date_of_birth: Date
    gender: str
    class_applying_for: str
    stream: str | None = None
    mother_tongue: str | None = None
    caste_category: str | None = None
    admission_category: AdmissionCategory = AdmissionCategory.general
    transport_required: bool = False
    address: dict | None = None
    previous_school: dict | None = None
    guardians: list[PublicGuardian]
    heard_about_us: EnquirySource = EnquirySource.website
    # §5.1.4 step 9. Consent is explicit and never pre-ticked; the two the
    # school cannot proceed without are checked below rather than by a default.
    information_accuracy: bool = False
    school_rules_accepted: bool = False
    data_processing_consent: bool = False
    photo_media_consent: bool | None = None
    # Honeypot. A real form renders this hidden and empty; a bot fills every
    # field it finds. Named as something a scraper would want to complete.
    website: str | None = None


@router.get("/open")
def open_cycle(school_code: str, db: Session = Depends(get_db)) -> dict:
    """What a parent needs before starting: is the school taking applications,
    for which classes, and what should they bring."""
    school = _school(db, school_code)
    cycle = admission.open_cycle(db, school.id)
    if not cycle.allow_online_applications:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This school is not accepting online applications. Please contact the office.",
        )
    classes = db.scalars(
        select(CycleClassConfig)
        .where(CycleClassConfig.cycle_id == cycle.id)
        .order_by(CycleClassConfig.class_name)
    )
    return {
        "school": {"code": school.code, "name": school.name, "city": school.city},
        "cycle": {
            "name": cycle.name,
            "academic_year": cycle.academic_year.code,
            "starts_on": cycle.starts_on,
            "ends_on": cycle.ends_on,
            "application_fee": cycle.application_fee,
            "refund_policy": cycle.admission_fee_refund_policy,
        },
        "classes": [
            {
                "class_name": c.class_name,
                "stream": c.stream,
                # Seat *counts* are published; how many are already taken is
                # not — that is the school's business, and publishing it
                # invites gaming.
                "total_seats": c.total_seats,
                "age_on": c.age_on,
                "min_age_years": c.min_age_years,
                "max_age_years": c.max_age_years,
                "requires_test": c.requires_test,
                "requires_interview": c.requires_interview,
                "required_documents": c.required_document_codes or [],
            }
            for c in classes
        ],
    }


@router.post("/apply", status_code=status.HTTP_201_CREATED)
def apply(
    school_code: str,
    body: PublicApplication,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    school = _school(db, school_code)
    cycle = admission.open_cycle(db, school.id)
    if not cycle.allow_online_applications:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This school is not accepting online applications"
        )

    if body.website:
        # A filled honeypot gets the same 201 a real submission gets: telling a
        # bot it was detected only teaches it to try again differently.
        return {"application_no": None, "status": "submitted"}

    ip = _client_ip(request)
    _rate_limit(db, school.id, ip)

    missing_consent = [
        label
        for label, given in (
            ("the declaration that the information is accurate", body.information_accuracy),
            ("acceptance of the school rules", body.school_rules_accepted),
            ("consent to process this data", body.data_processing_consent),
        )
        if not given
    ]
    if missing_consent:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "This form cannot be submitted without " + ", and ".join(missing_consent),
        )
    if sum(1 for g in body.guardians if g.is_primary) != 1:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Please mark exactly one parent or guardian as the main contact",
        )

    app = Application(
        school_id=school.id,
        cycle_id=cycle.id,
        created_by=None,  # nobody at the school typed this
        source=body.heard_about_us,
        **body.model_dump(
            exclude={
                "guardians",
                "heard_about_us",
                "information_accuracy",
                "school_rules_accepted",
                "data_processing_consent",
                "photo_media_consent",
                "website",
            }
        ),
        declarations={
            "information_accuracy": body.information_accuracy,
            "school_rules_accepted": body.school_rules_accepted,
            "data_processing_consent": body.data_processing_consent,
            "photo_media_consent": body.photo_media_consent,
            "submitted_from": "public_portal",
            "declared_on": str(Date.today()),
        },
    )
    db.add(app)
    db.flush()
    for g in body.guardians:
        db.add(
            ApplicationGuardian(
                school_id=school.id, application_id=app.id, **g.model_dump()
            )
        )
    db.flush()

    # The same submission path staff use, so the portal cannot drift into a
    # second set of rules: it warns about age and duplicates rather than
    # refusing, and the office sees both when it opens the file.
    svc.submit(db, app, actor=None)
    audit.record(
        db,
        actor=None,
        school_id=school.id,
        entity_type="application",
        entity_id=app.id,
        action=AuditAction.create,
        after={"application_no": app.application_no, "channel": "public_portal"},
        ip=ip,
    )
    db.commit()
    return {
        "application_no": app.application_no,
        "status": app.status,
        "next_step": (
            "Keep this application number safe. The school will verify your "
            "documents and contact you on the mobile number you gave."
        ),
    }


@router.get("/status")
def application_status(
    school_code: str,
    application_no: str,
    date_of_birth: Date,
    db: Session = Depends(get_db),
) -> dict:
    """Both the number and the child's date of birth, and one answer for every
    kind of miss: without that this endpoint enumerates other people's
    children."""
    school = _school(db, school_code)
    app = db.scalar(
        select(Application).where(
            Application.school_id == school.id,
            Application.application_no == application_no,
            Application.date_of_birth == date_of_birth,
        )
    )
    if app is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No application matches that number and date of birth",
        )
    return {
        "application_no": app.application_no,
        "name": app.full_name,
        "class_applying_for": app.class_applying_for,
        "status": app.status,
        "submitted_at": app.submitted_at,
        # Deliberately not the internal pipeline detail: a parent needs to know
        # whether to do something, not which staff queue they are sitting in.
        "action_needed": app.status
        in (
            ApplicationStatus.documents_rejected,
            ApplicationStatus.offer_issued,
        ),
    }
