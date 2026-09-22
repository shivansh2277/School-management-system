"""The application working queue and the 360° applicant view (screens 5-7 of
ERP_BLUEPRINT §5.1.3).

Medical is not on the detail response. §15 requires it to be gated separately,
so it has its own endpoint and its own permission — a receptionist who can see
an application must not thereby learn about a child's epilepsy.
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    AdmissionCategory,
    Application,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationSibling,
    ApplicationStatus,
    Employee,
    Enrolment,
    EnrolmentStatus,
    Enquiry,
    EnquiryStatus,
    EnquirySource,
    GuardianRelation,
    Student,
    User,
)
from app.services import admission
from app.services import applications as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)
writer = Depends(require_permission("admission.application.write"))
medical_reader = require_permission("admission.medical.read", school_wide=True)


class ApplicantDetails(BaseModel):
    """Step 1 plus step 2 — everything needed to open a draft."""

    model_config = {"extra": "forbid"}

    first_name: str
    last_name: str
    date_of_birth: Date
    gender: str
    class_applying_for: str
    cycle_id: int | None = None
    middle_name: str | None = None
    nationality: str | None = None
    religion: str | None = None
    caste_category: str | None = None
    mother_tongue: str | None = None
    place_of_birth: str | None = None
    identification_marks: str | None = None
    is_single_child: bool = False
    # §0.12: the last four digits and nothing more, ever.
    aadhaar_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    stream: str | None = None
    second_language: str | None = None
    optional_subject: str | None = None
    preferred_section: str | None = None
    admission_category: AdmissionCategory = AdmissionCategory.general
    transport_required: bool = False
    source: EnquirySource = EnquirySource.walk_in
    enquiry_id: int | None = None
    previous_application_id: int | None = None


class ApplicationUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    date_of_birth: Date | None = None
    gender: str | None = None
    nationality: str | None = None
    religion: str | None = None
    caste_category: str | None = None
    mother_tongue: str | None = None
    place_of_birth: str | None = None
    identification_marks: str | None = None
    is_single_child: bool | None = None
    aadhaar_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    class_applying_for: str | None = None
    stream: str | None = None
    second_language: str | None = None
    optional_subject: str | None = None
    preferred_section: str | None = None
    admission_category: AdmissionCategory | None = None
    transport_required: bool | None = None
    # Steps 5, 6 and 9: written and read whole by the form.
    address: dict | None = None
    previous_school: dict | None = None
    declarations: dict | None = None
    age_override_reason: str | None = None


class GuardianInput(BaseModel):
    model_config = {"extra": "forbid"}

    relation: GuardianRelation
    full_name: str
    mobile: str
    date_of_birth: Date | None = None
    qualification: str | None = None
    occupation: str | None = None
    designation: str | None = None
    organisation: str | None = None
    annual_income_band: str | None = None
    office_address: str | None = None
    alternate_mobile: str | None = None
    email: str | None = None
    is_primary: bool = False
    is_emergency_contact: bool = False
    is_authorised_for_pickup: bool = False
    is_school_alumnus: bool = False
    is_school_staff: bool = False
    employee_id: int | None = None


class SiblingInput(BaseModel):
    model_config = {"extra": "forbid"}

    student_id: int | None = None
    name: str | None = None
    age: int | None = None
    school_name: str | None = None


class MedicalInput(BaseModel):
    model_config = {"extra": "forbid"}

    blood_group: str | None = None
    known_allergies: str | None = None
    chronic_conditions: str | None = None
    regular_medication: str | None = None
    physical_disability: str | None = None
    learning_needs: str | None = None
    vision_hearing_notes: str | None = None
    emergency_doctor: str | None = None
    emergency_doctor_phone: str | None = None
    consent_for_emergency_treatment: bool = False


class StatusMove(BaseModel):
    model_config = {"extra": "forbid"}

    status: ApplicationStatus
    reason: str | None = None


def _guardian_out(g: ApplicationGuardian) -> dict:
    return {
        "id": g.id,
        "relation": g.relation,
        "full_name": g.full_name,
        "date_of_birth": g.date_of_birth,
        "qualification": g.qualification,
        "occupation": g.occupation,
        "designation": g.designation,
        "organisation": g.organisation,
        "annual_income_band": g.annual_income_band,
        "office_address": g.office_address,
        "mobile": g.mobile,
        "alternate_mobile": g.alternate_mobile,
        "email": g.email,
        "is_primary": g.is_primary,
        "is_emergency_contact": g.is_emergency_contact,
        "is_authorised_for_pickup": g.is_authorised_for_pickup,
        "is_school_alumnus": g.is_school_alumnus,
        "is_school_staff": g.is_school_staff,
        "employee_id": g.employee_id,
    }


def _row(a: Application) -> dict:
    return {
        "id": a.id,
        "application_no": a.application_no,
        "cycle_id": a.cycle_id,
        "name": a.full_name,
        "date_of_birth": a.date_of_birth,
        "gender": a.gender,
        "class_applying_for": a.class_applying_for,
        "stream": a.stream,
        "status": a.status,
        "admission_category": a.admission_category,
        "sibling_verified": a.sibling_verified,
        "staff_ward_verified": a.staff_ward_verified,
        "submitted_at": a.submitted_at,
        "source": a.source,
        "student_id": a.student_id,
    }


def _detail(db: Session, a: Application) -> dict:
    enrolled_student = None
    if a.student_id:
        st = db.get(Student, a.student_id)
        if st:
            enr = db.scalar(
                select(Enrolment).where(
                    Enrolment.student_id == st.id,
                    Enrolment.status == EnrolmentStatus.active,
                )
            )
            ay_code = None
            if enr and enr.academic_year_id:
                ay = db.get(AcademicYear, enr.academic_year_id)
                ay_code = ay.code if ay else None
            elif a.cycle and getattr(a.cycle, "academic_year", None):
                ay_code = a.cycle.academic_year.code

            enrolled_student = {
                "student_id": st.id,
                "admission_no": st.admission_no,
                "class_label": enr.class_section.label if (enr and enr.class_section) else a.class_applying_for,
                "section": enr.class_section.section if (enr and enr.class_section) else None,
                "roll_no": enr.roll_no if enr else None,
                "academic_year": ay_code,
                "status": enr.status.value if enr else "active",
            }

    return {
        **_row(a),
        "first_name": a.first_name,
        "middle_name": a.middle_name,
        "last_name": a.last_name,
        "nationality": a.nationality,
        "religion": a.religion,
        "caste_category": a.caste_category,
        "mother_tongue": a.mother_tongue,
        "place_of_birth": a.place_of_birth,
        "identification_marks": a.identification_marks,
        "is_single_child": a.is_single_child,
        "aadhaar_last4": a.aadhaar_last4,
        "second_language": a.second_language,
        "optional_subject": a.optional_subject,
        "preferred_section": a.preferred_section,
        "transport_required": a.transport_required,
        "address": a.address or {},
        "previous_school": a.previous_school or {},
        "declarations": a.declarations or {},
        "age_override_reason": a.age_override_reason,
        "previous_application_id": a.previous_application_id,
        "guardians": [_guardian_out(g) for g in svc.guardians(db, a.id)],
        "siblings": [
            {
                "id": s.id,
                "student_id": s.student_id,
                "name": s.name,
                "age": s.age,
                "school_name": s.school_name,
            }
            for s in db.scalars(
                select(ApplicationSibling).where(
                    ApplicationSibling.application_id == a.id
                )
            )
        ],
        "completeness_pct": svc.completeness(db, a),
        "effective_category": svc.eligible_categories(a),
        "enrolled_student": enrolled_student,
    }


@router.get("/applications")
def list_applications(
    cycle_id: int | None = None,
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    class_applying_for: str | None = None,
    category: AdmissionCategory | None = None,
    q: str | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(Application).where(Application.school_id == user.school_id)
    if cycle_id is not None:
        stmt = stmt.where(Application.cycle_id == cycle_id)
    if status_filter is not None:
        stmt = stmt.where(Application.status == status_filter)
    if class_applying_for is not None:
        stmt = stmt.where(Application.class_applying_for == class_applying_for)
    if category is not None:
        stmt = stmt.where(Application.admission_category == category)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Application.first_name.ilike(like)
            | Application.last_name.ilike(like)
            | Application.application_no.ilike(like)
        )
    return [_row(a) for a in db.scalars(stmt.order_by(Application.id.desc()))]


@router.post("/applications", status_code=status.HTTP_201_CREATED, dependencies=[writer])
def create_application(
    body: ApplicantDetails, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Opens a draft. Nothing is validated against seats or age yet — a draft
    that refuses to save is a draft staff will keep on paper."""
    cycle = (
        admission.cycle_for(db, user.school_id, body.cycle_id)
        if body.cycle_id is not None
        else admission.open_cycle(db, user.school_id)
    )
    fields = body.model_dump(exclude={"cycle_id", "enquiry_id"})
    app = Application(school_id=user.school_id, cycle_id=cycle.id, created_by=user.id, **fields)
    db.add(app)
    db.flush()

    if body.enquiry_id is not None:
        enquiry = db.get(Enquiry, body.enquiry_id)
        if enquiry is None or enquiry.school_id != user.school_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Enquiry not found")
        # The funnel only means anything if the two ends are actually joined.
        enquiry.converted_application_id = app.id
        enquiry.status = EnquiryStatus.converted
        enquiry.next_follow_up_on = None
        if enquiry.enquirer_name and enquiry.mobile:
            db.add(
                ApplicationGuardian(
                    school_id=user.school_id,
                    application_id=app.id,
                    relation=GuardianRelation.father,
                    full_name=enquiry.enquirer_name,
                    mobile=enquiry.mobile,
                    email=enquiry.email,
                    is_primary=True,
                )
            )
    db.commit()
    return _detail(db, app)


@router.get("/applications/{application_id}")
def application_detail(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    return _detail(db, svc.get(db, user.school_id, application_id))


@router.patch("/applications/{application_id}", dependencies=[writer])
def update_application(
    application_id: int,
    body: ApplicationUpdate,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    db.commit()
    return _detail(db, app)


@router.put("/applications/{application_id}/guardians", dependencies=[writer])
def set_guardians(
    application_id: int,
    body: list[GuardianInput],
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Replaces the whole set: step 3 is one form, edited as a whole, and
    reconciling a partial list is how a duplicate father appears."""
    app = svc.get(db, user.school_id, application_id)
    if not body:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one guardian is required"
        )
    if sum(1 for g in body if g.is_primary) != 1:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Exactly one guardian must be the primary contact",
        )
    for existing in svc.guardians(db, app.id):
        db.delete(existing)
    db.flush()
    for g in body:
        if g.employee_id is not None:
            employee = db.get(Employee, g.employee_id)
            if employee is None or employee.school_id != user.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        db.add(
            ApplicationGuardian(
                school_id=user.school_id, application_id=app.id, **g.model_dump()
            )
        )
    db.flush()
    svc.refresh_claims(db, app)
    return _detail(db, app)


@router.put("/applications/{application_id}/siblings", dependencies=[writer])
def set_siblings(
    application_id: int,
    body: list[SiblingInput],
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    for existing in db.scalars(
        select(ApplicationSibling).where(ApplicationSibling.application_id == app.id)
    ):
        db.delete(existing)
    db.flush()
    for s in body:
        if s.student_id is not None:
            student = db.get(Student, s.student_id)
            if student is None or student.school_id != user.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Sibling student not found")
        db.add(
            ApplicationSibling(
                school_id=user.school_id, application_id=app.id, **s.model_dump()
            )
        )
    db.flush()
    svc.refresh_claims(db, app)
    return _detail(db, app)


@router.get("/sibling-search")
def sibling_search(
    q: str = Query(..., min_length=2),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Step 4 searches real students rather than accepting a typed name: the
    link is what triggers the sibling concession later."""
    return svc.match_sibling(db, user.school_id, q)


@router.get("/applications/{application_id}/medical")
def read_medical(
    application_id: int,
    user: User = Depends(medical_reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    row = db.scalar(
        select(ApplicationMedical).where(ApplicationMedical.application_id == app.id)
    )
    if row is None:
        return {}
    return {
        c.name: getattr(row, c.name)
        for c in ApplicationMedical.__table__.columns
        if c.name not in ("school_id", "created_at", "updated_at")
    }


@router.put(
    "/applications/{application_id}/medical",
    dependencies=[Depends(require_permission("admission.medical.read"))],
)
def set_medical(
    application_id: int,
    body: MedicalInput,
    user: User = Depends(medical_reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    row = db.scalar(
        select(ApplicationMedical).where(ApplicationMedical.application_id == app.id)
    )
    if row is None:
        row = ApplicationMedical(
            school_id=user.school_id, application_id=app.id, **body.model_dump()
        )
        db.add(row)
    else:
        for field, value in body.model_dump().items():
            setattr(row, field, value)
    db.commit()
    return read_medical(application_id, user, db)


@router.post("/applications/{application_id}/submit", dependencies=[writer])
def submit_application(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Returns warnings rather than refusing on them: an out-of-range age or a
    possible duplicate is for a human to weigh (§5.1.9(1), (2))."""
    app = svc.get(db, user.school_id, application_id)
    result = svc.submit(db, app, actor=user)
    return {**_detail(db, app), **result}


@router.post("/applications/{application_id}/status", dependencies=[writer])
def move_status(
    application_id: int,
    body: StatusMove,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    svc.move(db, app, body.status, actor=user, reason=body.reason)
    return _detail(db, app)


@router.post("/applications/{application_id}/verify-claims", dependencies=[writer])
def verify_claims(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Re-check the sibling and staff-ward claims. An unverified claim never
    counts at selection time (§5.1.9(6))."""
    app = svc.get(db, user.school_id, application_id)
    svc.refresh_claims(db, app)
    return _detail(db, app)
