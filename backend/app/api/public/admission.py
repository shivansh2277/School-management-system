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

import base64
import hashlib
import hmac
import json
import re
import uuid
from datetime import UTC, date as Date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.common import class_sort_key
from app.models import (
    AdmissionCategory,
    AdmissionDecision,
    AdmissionOffer,
    Application,
    ApplicationAuthorizedPerson,
    ApplicationDocumentOverride,
    ApplicationFeePurpose,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationPayment,
    ApplicationSibling,
    ApplicationStatus,
    AuditAction,
    AuditLog,
    ClassSection,
    CycleClassConfig,
    Document,
    DocumentStatus,
    DocumentType,
    Enrolment,
    EnrolmentStatus,
    Enquiry,
    EnquiryChannel,
    EnquiryInteraction,
    EnquirySource,
    EnquiryStatus,
    FeeHead,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeePaymentStatus,
    GuardianRelation,
    InvoiceStatus,
    OfferStatus,
    OwnerType,
    PaymentAllocation,
    PaymentStatus,
    School,
    SchoolStatus,
    Student,
    StudentAuthorizedPerson,
    StudentGuardian,
    StudentStatus,
    User,
    UserRole,
)
from app.services import admission, audit, conversion, fees
from app.services import applications as svc
from app.services import school_settings

router = APIRouter(prefix="/public/{school_code}/admission", tags=["public"])

# Five applications an hour from one address is far more than a family needs
# and far less than a script wants.
MAX_APPLICATIONS_PER_IP_PER_HOUR = 5


def _school(db: Session, school_code: str) -> School:
    school = db.scalar(
        select(School).where(func.lower(School.code) == school_code.lower())
    )
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


def _number_to_words_inr(amount_num: float) -> str:
    if amount_num <= 0:
        return "Zero Rupees Only"
    a = [
        "", "One ", "Two ", "Three ", "Four ", "Five ", "Six ", "Seven ", "Eight ", "Nine ",
        "Ten ", "Eleven ", "Twelve ", "Thirteen ", "Fourteen ", "Fifteen ", "Sixteen ",
        "Seventeen ", "Eighteen ", "Nineteen ",
    ]
    b = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _in_words(n: int) -> str:
        if n == 0:
            return ""
        out = ""
        if n >= 10000000:
            out += _in_words(n // 10000000) + "Crore "
            n %= 10000000
        if n >= 100000:
            out += _in_words(n // 100000) + "Lakh "
            n %= 100000
        if n >= 1000:
            out += _in_words(n // 1000) + "Thousand "
            n %= 1000
        if n >= 100:
            out += _in_words(n // 100) + "Hundred "
            n %= 100
        if n > 0:
            if n < 20:
                out += a[n]
            else:
                out += b[n // 10] + (" " + a[n % 10] if (n % 10 != 0) else " ")
        return out

    words = _in_words(int(amount_num)).strip()
    return f"{words} Rupees Only" if words else "Zero Rupees Only"


def _create_order_token(school_id: int, app_id: int, amount: str, order_id: str, expires_at: int) -> str:
    payload = {
        "school_id": school_id,
        "app_id": app_id,
        "amount": amount,
        "order_id": order_id,
        "exp": expires_at,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    packed = base64.urlsafe_b64encode(raw).decode("utf-8")
    return f"{packed}.{sig}"


def _verify_order_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 2:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid payment order token format")
    packed, sig = parts
    try:
        raw = base64.urlsafe_b64decode(packed.encode("utf-8"))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Malformed payment token")
    expected_sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid or tampered payment token")
    data = json.loads(raw.decode("utf-8"))
    now_ts = int(datetime.now(UTC).timestamp())
    if data.get("exp", 0) < now_ts:
        raise HTTPException(status.HTTP_410_GONE, "Payment order has expired. Please initiate a new payment.")
    return data


class PublicGuardian(BaseModel):
    model_config = {"extra": "forbid"}

    relation: GuardianRelation
    full_name: str
    mobile: str = Field(pattern=r"^\d{10}$")
    email: str | None = None
    qualification: str | None = None
    occupation: str | None = None
    designation: str | None = None
    organisation: str | None = None
    annual_income_band: str | None = None
    office_address: str | None = None
    alternate_mobile: str | None = None
    is_primary: bool = False
    is_emergency_contact: bool = False
    is_authorised_for_pickup: bool = True
    photo_url: str | None = None
    is_school_alumnus: bool = False
    is_school_staff: bool = False


class PublicAuthorizedPickupPerson(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1, max_length=120)
    relationship: str = Field(min_length=1, max_length=60)
    phone: str = Field(min_length=10, max_length=30)
    id_proof_type: str | None = None
    id_proof_number: str | None = None
    photo_url: str | None = None
    notes: str | None = None


class PublicSibling(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1, max_length=120)
    age: int | None = None
    school_name: str | None = None
    student_id: int | None = None


class PublicMedical(BaseModel):
    model_config = {"extra": "forbid"}

    blood_group: str | None = None
    known_allergies: str | None = None
    chronic_conditions: str | None = None
    regular_medication: str | None = None
    physical_disability: str | None = None
    learning_needs: str | None = None
    emergency_doctor: str | None = None
    emergency_doctor_phone: str | None = None
    consent_for_emergency_treatment: bool = True


class PublicDocumentInput(BaseModel):
    model_config = {"extra": "forbid"}

    code: str
    filename: str
    url: str
    size: int | None = None


class PublicApplication(BaseModel):
    model_config = {"extra": "forbid"}

    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    middle_name: str | None = None
    date_of_birth: Date
    gender: str
    class_applying_for: str
    stream: str | None = None
    nationality: str | None = None
    religion: str | None = None
    caste_category: str | None = None
    mother_tongue: str | None = None
    place_of_birth: str | None = None
    identification_marks: str | None = None
    is_single_child: bool = False
    aadhaar_last4: str | None = None
    second_language: str | None = None
    optional_subject: str | None = None
    preferred_section: str | None = None
    photo_url: str | None = None
    admission_category: AdmissionCategory = AdmissionCategory.general
    transport_required: bool = False
    address: dict | None = None
    previous_school: dict | None = None
    guardians: list[PublicGuardian]
    authorized_pickup_persons: list[PublicAuthorizedPickupPerson] = []
    siblings: list[PublicSibling] = []
    medical: PublicMedical | None = None
    documents: list[PublicDocumentInput] = []
    heard_about_us: EnquirySource = EnquirySource.website
    # §5.1.4 step 9. Consent is explicit and never pre-ticked; the two the
    # school cannot proceed without are checked below rather than by a default.
    information_accuracy: bool = False
    school_rules_accepted: bool = False
    data_processing_consent: bool = False
    photo_media_consent: bool | None = None
    # Draft and APAAR fields
    draft_id: int | None = None
    apaar_id: str | None = None
    apaar_consent: bool = False
    apaar_consent_guardian_name: str | None = None
    apaar_consent_guardian_relation: str | None = None
    # Honeypot. A real form renders this hidden and empty; a bot fills every
    # field it finds. Named as something a scraper would want to complete.
    website: str | None = None


class PublicDraftApplication(BaseModel):
    model_config = {"extra": "ignore"}

    draft_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    date_of_birth: Date | None = None
    gender: str | None = None
    class_applying_for: str | None = None
    stream: str | None = None
    apaar_id: str | None = None
    apaar_consent: bool = False
    apaar_consent_guardian_name: str | None = None
    apaar_consent_guardian_relation: str | None = None
    guardians: list[PublicGuardian] = []
    documents: list[PublicDocumentInput] = []


class PaymentInitiateInput(BaseModel):
    model_config = {"extra": "forbid"}

    application_no: str
    mobile: str
    idempotency_key: str | None = None


class PaymentProcessInput(BaseModel):
    model_config = {"extra": "forbid"}

    order_token: str
    scenario: str = "success"  # "success" | "failure" | "cancel"
    idempotency_key: str | None = None


ALLOWED_IMAGE_MIMES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
def upload_admission_photo(
    school_code: str,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> dict:
    """Public upload for admission applications (applicant photo, escorts, and documents).
    Files are stored in local storage and served statically under /documents.
    """
    school = _school(db, school_code)
    if request:
        ip = _client_ip(request)
        _rate_limit(db, school.id, ip)

    content_type = (file.content_type or "").lower()
    ext = ALLOWED_IMAGE_MIMES.get(content_type)
    if not ext:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            ext = ".jpg"
        elif suffix == ".png":
            ext = ".png"
        elif suffix == ".webp":
            ext = ".webp"
        elif suffix == ".pdf":
            ext = ".pdf"
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Only document and image files (.jpg, .jpeg, .png, .webp, .pdf) are accepted",
            )

    data = file.file.read()
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "File exceeds maximum allowed size of 10MB",
        )

    target_dir = Path(settings.STORAGE_LOCAL_PATH) / str(school.id) / "admission"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = target_dir / filename
    file_path.write_bytes(data)

    rel_url = f"/documents/{school.id}/admission/{filename}"
    return {
        "url": rel_url,
        "filename": file.filename,
        "size": len(data),
    }


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
    classes = sorted(
        db.scalars(
            select(CycleClassConfig).where(CycleClassConfig.cycle_id == cycle.id)
        ),
        key=lambda c: class_sort_key(c.class_name),
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


@router.post("/draft")
def save_draft(
    school_code: str,
    body: PublicDraftApplication,
    db: Session = Depends(get_db),
) -> dict:
    """Save an application draft so public applicants missing documents can obtain
    a persistent reference (DFT-{id}) and request an administrative exception."""
    school = _school(db, school_code)
    cycle = admission.open_cycle(db, school.id)

    app = None
    if body.draft_id:
        app = db.scalar(
            select(Application).where(
                Application.id == body.draft_id,
                Application.school_id == school.id,
            )
        )
    if app is None:
        app = Application(
            school_id=school.id,
            cycle_id=cycle.id,
            status=ApplicationStatus.draft,
            first_name=body.first_name or "Draft",
            last_name=body.last_name or "Applicant",
            date_of_birth=body.date_of_birth or Date.today(),
            gender=body.gender or "other",
            class_applying_for=body.class_applying_for or "1",
            stream=body.stream,
        )
        db.add(app)
        db.flush()
    else:
        if app.status != ApplicationStatus.draft:
            raise HTTPException(status.HTTP_409_CONFLICT, "This application has already been submitted")
        if body.first_name:
            app.first_name = body.first_name
        if body.last_name:
            app.last_name = body.last_name
        if body.date_of_birth:
            app.date_of_birth = body.date_of_birth
        if body.gender:
            app.gender = body.gender
        if body.class_applying_for:
            app.class_applying_for = body.class_applying_for
        if body.stream:
            app.stream = body.stream

    clean_apaar = (body.apaar_id or "").strip().replace(" ", "").replace("-", "")
    if clean_apaar:
        app.apaar_id = clean_apaar
    if body.apaar_consent:
        app.apaar_consent = True
        app.apaar_consent_guardian_name = body.apaar_consent_guardian_name
        app.apaar_consent_guardian_relation = body.apaar_consent_guardian_relation
        app.apaar_consent_at = datetime.now(UTC)

    db.commit()
    return {
        "draft_id": app.id,
        "reference_code": f"DFT-{app.id}",
        "reference_number": f"DFT-{app.id}",
        "status": "draft",
        "message": f"Draft saved. Use reference code DFT-{app.id} for inquiries or document exception requests.",
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

    app_fields = body.model_dump(
        exclude={
            "draft_id",
            "guardians",
            "authorized_pickup_persons",
            "siblings",
            "medical",
            "documents",
            "heard_about_us",
            "information_accuracy",
            "school_rules_accepted",
            "data_processing_consent",
            "photo_media_consent",
            "website",
            "photo_url",
            "apaar_id",
            "apaar_consent",
            "apaar_consent_guardian_name",
            "apaar_consent_guardian_relation",
        }
    )

    app = None
    if body.draft_id:
        app = db.scalar(
            select(Application).where(
                Application.id == body.draft_id,
                Application.school_id == school.id,
            )
        )
        if app is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Draft application {body.draft_id} not found")
        if app.status != ApplicationStatus.draft:
            raise HTTPException(status.HTTP_409_CONFLICT, "This application has already been submitted")
        for field, value in app_fields.items():
            setattr(app, field, value)
        app.source = body.heard_about_us
        app.declarations = {
            "information_accuracy": body.information_accuracy,
            "school_rules_accepted": body.school_rules_accepted,
            "data_processing_consent": body.data_processing_consent,
            "photo_media_consent": body.photo_media_consent,
            "submitted_from": "public_portal",
            "declared_on": str(Date.today()),
            "photo_url": body.photo_url,
        }
    else:
        app = Application(
            school_id=school.id,
            cycle_id=cycle.id,
            created_by=None,  # nobody at the school typed this
            source=body.heard_about_us,
            **app_fields,
            declarations={
                "information_accuracy": body.information_accuracy,
                "school_rules_accepted": body.school_rules_accepted,
                "data_processing_consent": body.data_processing_consent,
                "photo_media_consent": body.photo_media_consent,
                "submitted_from": "public_portal",
                "declared_on": str(Date.today()),
                "photo_url": body.photo_url,
            },
        )
        db.add(app)
        db.flush()

    # Check conditional birth certificate rule
    if svc.is_birth_certificate_mandatory(db, school.id, body.class_applying_for, body.date_of_birth, cycle.id):
        has_uploaded_bc = any(d.code == "birth_certificate" for d in body.documents)
        has_override_bc = svc.has_override(db, app.id, "birth_certificate") if app.id else False
        if not (has_uploaded_bc or has_override_bc):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "A birth certificate is mandatory for junior section through UKG or applicants younger than 5 years old on the admission cutoff date.",
            )

    # Check APAAR ID section
    clean_apaar = (body.apaar_id or "").strip().replace(" ", "").replace("-", "")
    if clean_apaar:
        if not re.match(r"^\d{12}$", clean_apaar):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "APAAR ID must be exactly 12 digits.",
            )
        app.apaar_id = clean_apaar
        app.apaar_consent = False
    elif body.apaar_consent:
        primary_g = next((g for g in body.guardians if g.is_primary), None)
        g_name = (body.apaar_consent_guardian_name or (primary_g.full_name if primary_g else "")).strip()
        if not g_name:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Consenting parent or guardian name is required for APAAR consent.",
            )
        g_rel = body.apaar_consent_guardian_relation or (
            str(primary_g.relation.value if hasattr(primary_g.relation, "value") else primary_g.relation)
            if primary_g
            else None
        )
        app.apaar_id = None
        app.apaar_consent = True
        app.apaar_consent_guardian_name = g_name
        app.apaar_consent_guardian_relation = g_rel
        app.apaar_consent_at = datetime.now(UTC)
    else:
        has_apaar_override = svc.has_override(db, app.id, "apaar") if app.id else False
        if not has_apaar_override:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "APAAR ID section is required: please provide an existing 12-digit APAAR ID, record parental consent, or obtain an authorized exception.",
            )

    for g in body.guardians:
        db.add(
            ApplicationGuardian(
                school_id=school.id, application_id=app.id, **g.model_dump()
            )
        )

    for p in body.authorized_pickup_persons:
        db.add(
            ApplicationAuthorizedPerson(
                school_id=school.id,
                application_id=app.id,
                **p.model_dump(),
            )
        )

    for s in body.siblings:
        db.add(
            ApplicationSibling(
                school_id=school.id,
                application_id=app.id,
                name=s.name,
                age=s.age,
                school_name=s.school_name,
                student_id=s.student_id,
            )
        )

    if body.medical:
        db.add(
            ApplicationMedical(
                school_id=school.id,
                application_id=app.id,
                **body.medical.model_dump(),
            )
        )

    # Attach uploaded documents to Application owner so ERP document verification picks them up
    for doc_in in body.documents:
        dt = db.scalar(
            select(DocumentType).where(
                DocumentType.school_id == school.id,
                DocumentType.code == doc_in.code,
                DocumentType.applies_to == OwnerType.application,
            )
        )
        file_key = doc_in.url.replace(f"/documents/{school.id}/", "")
        suffix = Path(doc_in.filename or "").suffix.lower()
        mime = "application/pdf" if suffix == ".pdf" else "image/jpeg"
        db.add(
            Document(
                school_id=school.id,
                owner_type=OwnerType.application,
                owner_id=app.id,
                document_type_id=dt.id if dt else None,
                file_key=file_key,
                file_name=doc_in.filename,
                mime_type=mime,
                size_bytes=doc_in.size or 2048,
                uploaded_at=datetime.now(UTC),
                status=DocumentStatus.pending,
            )
        )

    if body.photo_url and not any(d.code == "photo" for d in body.documents):
        dt_photo = db.scalar(
            select(DocumentType).where(
                DocumentType.school_id == school.id,
                DocumentType.code == "photo",
                DocumentType.applies_to == OwnerType.application,
            )
        )
        file_key = body.photo_url.replace(f"/documents/{school.id}/", "")
        db.add(
            Document(
                school_id=school.id,
                owner_type=OwnerType.application,
                owner_id=app.id,
                document_type_id=dt_photo.id if dt_photo else None,
                file_key=file_key,
                file_name="student_photograph.jpg",
                mime_type="image/jpeg",
                size_bytes=4096,
                uploaded_at=datetime.now(UTC),
                status=DocumentStatus.pending,
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
            "Keep this application reference number safe. The admissions committee will verify your "
            "details and notify you on your registered mobile number for subsequent stages."
        ),
    }


@router.get("/status")
def application_status(
    school_code: str,
    application_no: str,
    date_of_birth: Date | None = None,
    mobile: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """Check application status requiring application_no AND either date_of_birth
    OR registered mobile number. Answers 404 identically on any mismatch to prevent enumeration."""
    school = _school(db, school_code)
    app = db.scalar(
        select(Application).where(
            Application.school_id == school.id,
            Application.application_no == application_no,
        )
    )
    if app is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No application matches that reference and verification detail",
        )

    authorized = False
    if mobile:
        guardians = db.scalars(
            select(ApplicationGuardian).where(
                ApplicationGuardian.application_id == app.id,
                ApplicationGuardian.school_id == school.id,
            )
        ).all()
        clean_target = "".join(filter(str.isdigit, mobile))[-10:]
        for g in guardians:
            clean_g = "".join(filter(str.isdigit, g.mobile or ""))[-10:]
            if clean_g and clean_g == clean_target:
                authorized = True
                break

    if date_of_birth and app.date_of_birth == date_of_birth:
        authorized = True

    if not authorized:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No application matches that reference and verification detail",
        )

    # Determine user-facing journey stage
    if app.status in (ApplicationStatus.draft, ApplicationStatus.submitted):
        stage = "submitted"
        stage_label = "Application Submitted"
        stage_desc = "Your application has been received and is registered in the admissions queue."
    elif app.status in (
        ApplicationStatus.under_document_verification,
        ApplicationStatus.documents_verified,
        ApplicationStatus.assessment_scheduled,
        ApplicationStatus.assessment_completed,
        ApplicationStatus.interview_scheduled,
        ApplicationStatus.interview_completed,
        ApplicationStatus.decision_pending,
    ):
        stage = "under_review"
        stage_label = "Under Review & Verification"
        stage_desc = "The admissions office is currently reviewing submitted documentation and eligibility."
    elif app.status in (ApplicationStatus.admitted, ApplicationStatus.offer_issued, ApplicationStatus.offer_accepted):
        stage = "offer_issued"
        stage_label = "Offer Issued • Fee Payment Pending"
        stage_desc = "Congratulations! Provisional admission has been offered. Please complete the admission fee payment to confirm enrollment."
    elif app.status in (ApplicationStatus.fee_paid, ApplicationStatus.enrolled):
        stage = "enrolled"
        stage_label = "Admission Confirmed & Enrolled"
        stage_desc = "Admission fee has been verified. The student is officially enrolled for the upcoming academic session."
    else:
        stage = "rejected"
        stage_label = "Application Closed"
        stage_desc = f"Application status: {app.status.value.replace('_', ' ').capitalize()}."

    # Look up offer details if applicable
    offer = db.scalar(
        select(AdmissionOffer)
        .where(
            AdmissionOffer.application_id == app.id,
            AdmissionOffer.school_id == school.id,
        )
        .order_by(AdmissionOffer.id.desc())
    )

    is_payable = app.status in (
        ApplicationStatus.admitted,
        ApplicationStatus.offer_issued,
        ApplicationStatus.offer_accepted,
    )
    if is_payable:
        if offer and offer.offer_amount:
            payable_amount = str(offer.offer_amount)
        elif app.cycle.application_fee and app.cycle.application_fee > 0:
            payable_amount = str(app.cycle.application_fee)
        else:
            payable_amount = "25000.00"
    else:
        payable_amount = None

    # Student and enrollment info if enrolled
    student_data = None
    if app.student_id:
        student = db.get(Student, app.student_id)
        if student:
            enrolment = db.scalar(
                select(Enrolment).where(
                    Enrolment.student_id == student.id,
                    Enrolment.status == EnrolmentStatus.active,
                )
            )
            student_data = {
                "id": student.id,
                "admission_no": student.admission_no,
                "class_label": enrolment.class_section.label if enrolment and enrolment.class_section else app.class_applying_for,
                "roll_no": enrolment.roll_no if enrolment else None,
            }

    # Latest payment receipt
    last_payment = db.scalar(
        select(ApplicationPayment)
        .where(
            ApplicationPayment.application_id == app.id,
            ApplicationPayment.status == PaymentStatus.paid,
        )
        .order_by(ApplicationPayment.id.desc())
    )

    is_enrolled = app.status in (ApplicationStatus.fee_paid, ApplicationStatus.enrolled) and app.student_id is not None

    return {
        "application_no": app.application_no,
        "name": app.full_name,
        "class_applying_for": app.class_applying_for,
        "status": app.status.value,
        "submitted_at": app.submitted_at,
        "action_needed": app.status in (
            ApplicationStatus.documents_rejected,
            ApplicationStatus.offer_issued,
        ),
        "stage": stage,
        "stage_label": stage_label,
        "stage_description": stage_desc,
        "is_payable": is_payable,
        "payable_amount": payable_amount,
        "offer": {
            "expires_on": str(offer.expires_on) if offer else None,
            "offer_amount": str(offer.offer_amount) if offer and offer.offer_amount else None,
            "status": offer.status.value if offer else None,
        } if offer else None,
        "student": student_data,
        "receipt": {
            "receipt_no": last_payment.receipt_no,
            "amount": str(last_payment.amount),
            "paid_at": str(last_payment.paid_at),
        } if last_payment else None,
        "documents_available": is_enrolled,
    }


# ------------------------------------------------------------------- Mock Payment Gateway


@router.post("/payments/initiate")
def initiate_payment(
    school_code: str,
    body: PaymentInitiateInput,
    db: Session = Depends(get_db),
) -> dict:
    """Initiates a mock payment order for an admission application with an open offer."""
    school = _school(db, school_code)
    app = db.scalar(
        select(Application).where(
            Application.school_id == school.id,
            Application.application_no == body.application_no,
        )
    )
    if app is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No application matches that reference"
        )

    # Authorization verification
    guardians = db.scalars(
        select(ApplicationGuardian).where(
            ApplicationGuardian.application_id == app.id,
            ApplicationGuardian.school_id == school.id,
        )
    ).all()
    clean_target = "".join(filter(str.isdigit, body.mobile))[-10:]
    authorized = any(
        "".join(filter(str.isdigit, g.mobile or ""))[-10:] == clean_target
        for g in guardians
    )
    if not authorized:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Mobile number does not match registered applicant guardians"
        )

    # Check if already enrolled
    if app.status == ApplicationStatus.enrolled or app.student_id is not None:
        student = db.get(Student, app.student_id)
        return {
            "status": "already_enrolled",
            "message": "This applicant is already enrolled.",
            "application_no": app.application_no,
            "admission_no": student.admission_no if student else None,
            "enrolled": True,
        }

    # Verify state eligibility
    if app.status not in (
        ApplicationStatus.admitted,
        ApplicationStatus.offer_issued,
        ApplicationStatus.offer_accepted,
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Application is in '{app.status.value}' stage and is not awaiting fee payment.",
        )

    # Look up offer
    offer = db.scalar(
        select(AdmissionOffer)
        .where(
            AdmissionOffer.application_id == app.id,
            AdmissionOffer.school_id == school.id,
            AdmissionOffer.status.in_([OfferStatus.issued, OfferStatus.accepted]),
        )
        .order_by(AdmissionOffer.id.desc())
    )

    if offer and offer.expires_on and offer.expires_on < Date.today():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"The admission offer expired on {offer.expires_on}. Please contact the school office.",
        )

    if offer and offer.offer_amount:
        amount = offer.offer_amount
    elif app.cycle.application_fee and app.cycle.application_fee > 0:
        amount = app.cycle.application_fee
    else:
        amount = Decimal("25000.00")

    order_id = f"ORD-MOCK-{school.code}-{app.id}-{uuid.uuid4().hex[:8].upper()}"
    expires_at = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    order_token = _create_order_token(school.id, app.id, str(amount), order_id, expires_at)

    return {
        "order_id": order_id,
        "order_token": order_token,
        "application_no": app.application_no,
        "student_name": app.full_name,
        "class_applying_for": app.class_applying_for,
        "amount": str(amount),
        "currency": "INR",
        "offer_expires_on": str(offer.expires_on) if offer else None,
        "status": "initiated",
        "gateway": "Sunrise School Test Gateway (Mock)",
        "supported_scenarios": ["success", "failure", "cancel"],
    }


@router.post("/payments/process")
def process_payment(
    school_code: str,
    body: PaymentProcessInput,
    db: Session = Depends(get_db),
) -> dict:
    """Processes mock payment and triggers sole, atomic enrollment upon success."""
    data = _verify_order_token(body.order_token)
    school_id = data["school_id"]
    app_id = data["app_id"]
    amount = Decimal(data["amount"])
    order_id = data["order_id"]

    school = db.get(School, school_id)
    app = db.get(Application, app_id)
    if school is None or app is None or school.code != school_code:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application or school not found")

    # Idempotency check: if already enrolled, return existing enrollment safely
    if app.status == ApplicationStatus.enrolled and app.student_id is not None:
        student = db.get(Student, app.student_id)
        enrolment = db.scalar(
            select(Enrolment).where(
                Enrolment.student_id == student.id,
                Enrolment.status == EnrolmentStatus.active,
            )
        )
        existing_payment = db.scalar(
            select(ApplicationPayment)
            .where(
                ApplicationPayment.application_id == app.id,
                ApplicationPayment.status == PaymentStatus.paid,
            )
            .order_by(ApplicationPayment.id.desc())
        )
        return {
            "status": "success",
            "order_id": order_id,
            "receipt_no": existing_payment.receipt_no if existing_payment else "AR-EXISTING",
            "amount": str(amount),
            "student": {
                "id": student.id,
                "admission_no": student.admission_no,
                "class_label": enrolment.class_section.label if enrolment and enrolment.class_section else app.class_applying_for,
                "roll_no": enrolment.roll_no if enrolment else None,
            },
            "application_no": app.application_no,
            "message": "Payment verified and student enrollment confirmed successfully.",
        }

    # Handle negative scenarios
    if body.scenario == "failure":
        return {
            "status": "failed",
            "order_id": order_id,
            "error": "Payment declined by simulated issuing bank (Simulated Failure).",
            "can_retry": True,
        }

    if body.scenario == "cancel":
        return {
            "status": "cancelled",
            "order_id": order_id,
            "message": "Payment was cancelled by the user.",
            "can_retry": True,
        }

    # Handle success: ATOMIC ENROLLMENT TRIGGER
    try:
        # 1. Execute atomic conversion into student, enrolment, user, guardians, and documents
        conversion_res = conversion._do_conversion(db, app, actor=None)
        student_id = conversion_res["student_id"]
        admission_no = conversion_res["admission_no"]
        class_label = conversion_res["class_label"]
        roll_no = conversion_res["roll_no"]
        student = db.get(Student, student_id)

        # 2. Record ApplicationPayment receipt
        year = app.cycle.academic_year.start_date.year
        receipt_no = audit.next_number(
            db, app.school_id, kind="application_receipt", year=year, prefix="AR", width=5
        )
        app_payment = ApplicationPayment(
            school_id=app.school_id,
            application_id=app.id,
            purpose=ApplicationFeePurpose.admission_fee,
            amount=amount,
            method="mock_gateway",
            reference=order_id,
            receipt_no=receipt_no,
            paid_at=datetime.now(UTC),
            collected_by=None,
            idempotency_key=body.idempotency_key or order_id,
            status=PaymentStatus.paid,
        )
        db.add(app_payment)
        db.flush()

        # 3. Create fee invoice and allocate payment via existing fees service
        enrolment = db.scalar(
            select(Enrolment).where(
                Enrolment.student_id == student.id,
                Enrolment.status == EnrolmentStatus.active,
            )
        )
        if enrolment:
            head = db.scalar(
                select(FeeHead).where(
                    FeeHead.school_id == app.school_id,
                    FeeHead.code == "ADMISSION",
                )
            ) or db.scalar(select(FeeHead).where(FeeHead.school_id == app.school_id))

            if head:
                today = Date.today()
                invoice = FeeInvoice(
                    school_id=app.school_id,
                    enrolment_id=enrolment.id,
                    academic_year_id=enrolment.academic_year_id,
                    invoice_no=audit.next_number(
                        db, app.school_id, kind="invoice", year=today.year, prefix="INV", width=6
                    ),
                    period_month=today.month,
                    period_year=today.year,
                    issued_on=today,
                    due_date=today,
                    status=InvoiceStatus.issued,
                )
                db.add(invoice)
                db.flush()

                line = FeeInvoiceLine(
                    school_id=app.school_id,
                    invoice_id=invoice.id,
                    fee_head_id=head.id,
                    description=f"Admission Fee - Class {app.class_applying_for}",
                    amount=amount,
                    discount=Decimal("0.00"),
                )
                db.add(line)
                db.flush()

                fee_payment = FeePayment(
                    school_id=app.school_id,
                    enrolment_id=enrolment.id,
                    receipt_no=receipt_no,
                    amount=amount,
                    method="mock_gateway",
                    instrument_ref=order_id,
                    received_at=datetime.now(UTC),
                    received_by=None,
                    idempotency_key=f"FEE-{order_id}",
                    status=FeePaymentStatus.success,
                )
                db.add(fee_payment)
                db.flush()

                fees._allocate(db, fee_payment, amount, today)

        # 4. Update offer status to accepted
        offer = db.scalar(
            select(AdmissionOffer)
            .where(
                AdmissionOffer.application_id == app.id,
                AdmissionOffer.school_id == app.school_id,
            )
            .order_by(AdmissionOffer.id.desc())
        )
        if offer and offer.status == OfferStatus.issued:
            offer.status = OfferStatus.accepted
            offer.accepted_at = datetime.now(UTC)

        audit.record(
            db,
            actor=None,
            school_id=app.school_id,
            entity_type="application_payment",
            entity_id=app.id,
            action=AuditAction.create,
            after={
                "receipt_no": receipt_no,
                "amount": str(amount),
                "order_id": order_id,
                "status": "paid",
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "success",
        "order_id": order_id,
        "receipt_no": receipt_no,
        "amount": str(amount),
        "student": {
            "id": student.id,
            "admission_no": admission_no,
            "class_label": class_label,
            "roll_no": roll_no,
        },
        "application_no": app.application_no,
        "message": "Payment verified and student enrollment confirmed successfully.",
    }


# ------------------------------------------------------------------- Gated Document Download


@router.get("/documents/{doc_type}")
def get_public_admission_document(
    school_code: str,
    doc_type: str,
    application_no: str,
    mobile: str,
    db: Session = Depends(get_db),
) -> dict:
    """Provides canonical printable document data (dossier, receipt, admission letter)
    strictly gated behind successful admission payment and enrollment."""
    if doc_type not in ("dossier", "receipt", "admission_letter"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid document type")

    school = _school(db, school_code)
    app = db.scalar(
        select(Application).where(
            Application.school_id == school.id,
            Application.application_no == application_no,
        )
    )
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No application matches that reference")

    # Authorize guardian mobile
    guardians = db.scalars(
        select(ApplicationGuardian).where(
            ApplicationGuardian.application_id == app.id,
            ApplicationGuardian.school_id == school.id,
        )
    ).all()
    clean_target = "".join(filter(str.isdigit, mobile))[-10:]
    authorized = any(
        "".join(filter(str.isdigit, g.mobile or ""))[-10:] == clean_target
        for g in guardians
    )
    if not authorized:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Mobile number does not match registered applicant guardians"
        )

    # Strictly verify enrollment
    if not (app.status == ApplicationStatus.enrolled and app.student_id is not None):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Official admission documents are only downloadable after admission fee payment and enrollment confirmation.",
        )

    student = db.get(Student, app.student_id)
    enrolment = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == student.id,
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    payment = db.scalar(
        select(ApplicationPayment)
        .where(
            ApplicationPayment.application_id == app.id,
            ApplicationPayment.status == PaymentStatus.paid,
        )
        .order_by(ApplicationPayment.id.desc())
    )

    class_label = (
        enrolment.class_section.label
        if enrolment and enrolment.class_section
        else app.class_applying_for
    )

    amount_words = _number_to_words_inr(float(payment.amount)) if payment else "Zero Rupees Only"

    return {
        "doc_type": doc_type,
        "school": {
            "name": school.name,
            "code": school.code,
            "city": school.city,
            "affiliation": "CBSE Affiliated • K-12",
            "address": "Sector 4, Gomti Nagar, Lucknow, Uttar Pradesh 226010",
            "email": "admissions@sunrisepublic.edu",
            "phone": "+91 522 261 1101",
        },
        "application": {
            "id": app.id,
            "application_no": app.application_no,
            "first_name": app.first_name,
            "middle_name": app.middle_name,
            "last_name": app.last_name,
            "full_name": app.full_name,
            "date_of_birth": str(app.date_of_birth),
            "gender": app.gender,
            "class_applying_for": app.class_applying_for,
            "stream": app.stream,
            "mother_tongue": app.mother_tongue,
            "caste_category": app.caste_category,
            "admission_category": app.admission_category.value,
            "transport_required": app.transport_required,
            "address": app.address,
            "previous_school": app.previous_school,
            "submitted_at": str(app.submitted_at),
            "status": app.status.value,
        },
        "student": {
            "id": student.id,
            "admission_no": student.admission_no,
            "class_label": class_label,
            "roll_no": enrolment.roll_no if enrolment else None,
            "admission_date": str(student.admission_date),
            "status": student.status.value,
        },
        "payment": {
            "receipt_no": payment.receipt_no if payment else None,
            "amount": str(payment.amount) if payment else None,
            "amount_in_words": amount_words,
            "method": payment.method if payment else None,
            "reference": payment.reference if payment else None,
            "paid_at": str(payment.paid_at) if payment else None,
        } if payment else None,
        "guardians": [
            {
                "relation": g.relation.value if hasattr(g.relation, "value") else str(g.relation),
                "full_name": g.full_name,
                "mobile": g.mobile,
                "email": g.email,
                "qualification": g.qualification,
                "occupation": g.occupation,
                "designation": g.designation,
                "organisation": g.organisation,
                "annual_income_band": g.annual_income_band,
                "office_address": g.office_address,
                "is_primary": g.is_primary,
            }
            for g in guardians
        ],
    }


class PublicEnquiryCreate(BaseModel):
    enquirer_name: str = Field(..., min_length=2, max_length=120)
    mobile: str = Field(..., min_length=10, max_length=20)
    email: str | None = Field(None, max_length=160)
    child_name: str | None = Field(None, max_length=120)
    child_dob: Date | None = None
    class_of_interest: str | None = Field(None, max_length=20)
    notes: str | None = Field(None, max_length=1000)


@router.post("/enquiry")
def submit_public_enquiry(
    school_code: str,
    body: PublicEnquiryCreate,
    req: Request,
    db: Session = Depends(get_db),
):
    """Public admission enquiry registration (§5.1.3).
    Inserts directly into the ERP Enquiry register for front desk receptionist processing.
    """
    school = _school(db, school_code)
    try:
        cycle = admission.open_cycle(db, school.id)
    except HTTPException:
        cycle = None

    if cycle is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Admissions are currently closed for this school."
        )

    # Check for existing active enquiry for this mobile number in current cycle
    existing = db.scalar(
        select(Enquiry).where(
            Enquiry.school_id == school.id,
            Enquiry.cycle_id == cycle.id,
            Enquiry.mobile == body.mobile,
            Enquiry.status != EnquiryStatus.invalid,
        )
    )

    if existing is not None:
        # Append web follow-up note to existing enquiry timeline
        interaction = EnquiryInteraction(
            school_id=school.id,
            enquiry_id=existing.id,
            channel=EnquiryChannel.email,
            occurred_at=datetime.now(UTC),
            notes=body.notes or "Follow-up enquiry received from public website.",
        )
        db.add(interaction)
        db.commit()
        return {
            "status": "success",
            "enquiry_id": existing.id,
            "enquiry_no": f"ENQ-{existing.id:04d}",
            "message": "We have received your update. Our admissions desk will contact you shortly.",
        }

    enquiry = Enquiry(
        school_id=school.id,
        cycle_id=cycle.id,
        enquirer_name=body.enquirer_name,
        mobile=body.mobile,
        email=body.email,
        child_name=body.child_name,
        child_dob=body.child_dob,
        class_of_interest=body.class_of_interest or "Class 1",
        source=EnquirySource.website,
        status=EnquiryStatus.new,
    )
    db.add(enquiry)
    db.flush()

    if body.notes:
        interaction = EnquiryInteraction(
            school_id=school.id,
            enquiry_id=enquiry.id,
            channel=EnquiryChannel.email,
            occurred_at=datetime.now(UTC),
            notes=body.notes,
        )
        db.add(interaction)

    db.commit()

    return {
        "status": "success",
        "enquiry_id": enquiry.id,
        "enquiry_no": f"ENQ-{enquiry.id:04d}",
        "message": "Enquiry registered successfully! Our admissions desk will get in touch with you shortly.",
    }

