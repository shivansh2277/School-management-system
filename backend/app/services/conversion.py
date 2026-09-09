"""Applicant money, and the conversion that ends the module (§5.1.9(15)-(19)).

Conversion is the one operation in Admission that must be all-or-nothing. A
partial conversion — the student who exists with no fee account, or with no
login, or whose documents stayed behind on the application — is the failure
mode §5.1.9(16) names, and it is not recoverable by hand at 200 students a
year. Everything below happens inside the caller's transaction and commits
once.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status as http
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Application,
    ApplicationFeePurpose,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationPayment,
    ApplicationStatus,
    AuditAction,
    ClassSection,
    Document,
    Enrolment,
    EnrolmentStatus,
    Guardian,
    OwnerType,
    PaymentStatus,
    Student,
    StudentGuardian,
    StudentStatus,
    User,
    UserRole,
    WaitlistEntry,
    WaitlistStatus,
)
from app.services import audit
from app.services import applications as app_svc

# What a converted student's portal accounts start with. The school hands these
# over at the counter and the family is expected to change them; the same
# defaults the seed uses, for the same reason.
DEFAULT_STUDENT_PASSWORD = "Student@123"
DEFAULT_GUARDIAN_PASSWORD = "Parent@123"


# ------------------------------------------------------------------- payments


def collect(
    db: Session,
    app: Application,
    *,
    actor: User,
    purpose: ApplicationFeePurpose,
    amount: Decimal,
    method: str,
    reference: str | None = None,
    idempotency_key: str | None = None,
) -> ApplicationPayment:
    if amount <= 0:
        raise HTTPException(
            http.HTTP_422_UNPROCESSABLE_ENTITY, "A receipt cannot be for nothing"
        )
    if idempotency_key:
        existing = db.scalar(
            select(ApplicationPayment).where(
                ApplicationPayment.idempotency_key == idempotency_key
            )
        )
        if existing is not None:
            # Two clicks on Collect are one payment, not two receipts.
            return existing

    year = app.cycle.academic_year.start_date.year
    receipt_no = audit.next_number(
        db, app.school_id, kind="application_receipt", year=year, prefix="AR", width=5
    )
    payment = ApplicationPayment(
        school_id=app.school_id,
        application_id=app.id,
        purpose=purpose,
        amount=amount,
        method=method,
        reference=reference,
        receipt_no=receipt_no,
        paid_at=datetime.now(UTC),
        collected_by=actor.id,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    audit.record(
        db,
        actor=actor,
        school_id=app.school_id,
        entity_type="application_payment",
        entity_id=app.id,
        action=AuditAction.create,
        after={"receipt_no": receipt_no, "amount": str(amount), "purpose": purpose.value},
    )
    if purpose is ApplicationFeePurpose.admission_fee and app.status in (
        ApplicationStatus.offer_accepted,
        ApplicationStatus.offer_issued,
    ):
        app_svc.move(db, app, ApplicationStatus.fee_paid, actor=actor)
    db.commit()
    return payment


def void_payment(
    db: Session, payment: ApplicationPayment, *, actor: User, reason: str
) -> ApplicationPayment:
    """Voided, never deleted: the receipt number stays used, which is what
    makes the sequence auditable."""
    if payment.status is PaymentStatus.voided:
        return payment
    payment.status = PaymentStatus.voided
    payment.void_reason = reason
    audit.record(
        db,
        actor=actor,
        school_id=payment.school_id,
        entity_type="application_payment",
        entity_id=payment.id,
        action=AuditAction.void,
        before={"status": PaymentStatus.paid.value},
        after={"status": PaymentStatus.voided.value},
        reason=reason,
    )
    db.commit()
    return payment


def payments_for(db: Session, application_id: int) -> list[ApplicationPayment]:
    return list(
        db.scalars(
            select(ApplicationPayment)
            .where(ApplicationPayment.application_id == application_id)
            .order_by(ApplicationPayment.paid_at)
        )
    )


# ---------------------------------------------------------- section allocation


def _sections_for(db: Session, app: Application) -> list[ClassSection]:
    return list(
        db.scalars(
            select(ClassSection).where(
                ClassSection.school_id == app.school_id,
                ClassSection.academic_year_id == app.cycle.academic_year_id,
                ClassSection.class_name == app.class_applying_for,
            )
        )
    )


def allocate_section(db: Session, app: Application) -> tuple[ClassSection, str]:
    """Pick the section, and say why (§5.1.9(18)).

    Balance by headcount, honour a stated preference when that section is not
    already the fullest, and refuse rather than overfill a section with a
    capacity. Automatic, but always previewable before it is committed.
    """
    sections = _sections_for(db, app)
    if not sections:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            f"No section of class {app.class_applying_for} exists for "
            f"{app.cycle.academic_year.code}. Create next year's sections first.",
        )
    counts = {
        s.id: db.scalar(
            select(func.count())
            .select_from(Enrolment)
            .where(
                Enrolment.class_section_id == s.id,
                Enrolment.status == EnrolmentStatus.active,
            )
        )
        for s in sections
    }
    with_room = [
        s for s in sections if s.capacity is None or counts[s.id] < s.capacity
    ]
    if not with_room:
        raise HTTPException(
            http.HTTP_409_CONFLICT,
            f"Every section of class {app.class_applying_for} is at capacity",
        )

    if app.preferred_section:
        wanted = next(
            (s for s in with_room if s.section == app.preferred_section), None
        )
        if wanted is not None:
            # A request, never a guarantee: honoured only while it does not
            # unbalance the class.
            if counts[wanted.id] <= min(counts[s.id] for s in with_room):
                return wanted, f"Requested section {wanted.section} and it has room"

    chosen = min(with_room, key=lambda s: (counts[s.id], s.section))
    return chosen, (
        f"Section {chosen.section} has the fewest students "
        f"({counts[chosen.id]} enrolled)"
    )


def _next_roll_no(db: Session, section_id: int) -> int:
    last = db.scalar(
        select(func.max(Enrolment.roll_no)).where(
            Enrolment.class_section_id == section_id
        )
    )
    return (last or 0) + 1


def preview(db: Session, app: Application) -> dict:
    """Everything conversion is about to do, writing nothing."""
    blockers = []
    if app.status not in (
        ApplicationStatus.offer_accepted,
        ApplicationStatus.fee_paid,
        ApplicationStatus.admitted,
    ):
        blockers.append(
            f"An application in {app.status.value} is not ready to be enrolled"
        )
    if app.student_id is not None:
        blockers.append("This application has already been converted")

    section = None
    rationale = None
    try:
        section, rationale = allocate_section(db, app)
    except HTTPException as e:
        blockers.append(str(e.detail))

    guardians = app_svc.guardians(db, app.id)
    if not guardians:
        blockers.append("The application has no guardian to link or give a login to")

    documents = db.scalars(
        select(Document).where(
            Document.school_id == app.school_id,
            Document.owner_type == OwnerType.application,
            Document.owner_id == app.id,
            Document.deleted_at.is_(None),
        )
    ).all()

    return {
        "application_id": app.id,
        "application_no": app.application_no,
        "name": app.full_name,
        "class_applying_for": app.class_applying_for,
        "section": section.section if section else None,
        "class_label": section.label if section else None,
        "section_rationale": rationale,
        "roll_no": _next_roll_no(db, section.id) if section else None,
        "guardian_logins": [
            {"name": g.full_name, "login_id": g.mobile, "relation": g.relation}
            for g in guardians
        ],
        "documents_to_migrate": len(documents),
        "fee_class": app.class_applying_for,
        "blockers": blockers,
        "ready": not blockers,
    }


# ------------------------------------------------------------------ conversion


def convert(db: Session, app: Application, *, actor: User) -> dict:
    """Applicant -> student, in one transaction (§5.1.9(16)).

    Creates the student and their login, the enrolment in the allocated
    section, the guardians and their logins, the links between them, and moves
    the documents across. The admission number is allocated here and not before
    (§5.1.9(17)); the application keeps an immutable pointer to what it became,
    and the student keeps one back (§5.1.9(19)).
    """
    plan = preview(db, app)
    if plan["blockers"]:
        raise HTTPException(http.HTTP_409_CONFLICT, "; ".join(plan["blockers"]))

    section, _ = allocate_section(db, app)
    joining_year = app.cycle.academic_year.start_date.year
    admission_no = audit.admission_number(db, app.school_id, joining_year)

    student_user = User(
        school_id=app.school_id,
        role=UserRole.student,
        login_id=admission_no,
        password_hash=hash_password(DEFAULT_STUDENT_PASSWORD),
        full_name=app.full_name,
    )
    db.add(student_user)
    db.flush()

    student = Student(
        school_id=app.school_id,
        user_id=student_user.id,
        admission_no=admission_no,
        status=StudentStatus.active,
        dob=app.date_of_birth,
        gender=app.gender,
        address=_address_line(app.address),
        admission_date=date.today(),
    )
    db.add(student)
    db.flush()

    db.add(
        Enrolment(
            school_id=app.school_id,
            student_id=student.id,
            academic_year_id=section.academic_year_id,
            class_section_id=section.id,
            roll_no=_next_roll_no(db, section.id),
            joined_on=date.today(),
        )
    )

    for i, g in enumerate(app_svc.guardians(db, app.id)):
        guardian = _guardian_for(db, app, g)
        db.add(
            StudentGuardian(
                school_id=app.school_id,
                guardian_id=guardian.id,
                student_id=student.id,
                relation=g.relation,
                is_primary=g.is_primary,
            )
        )

    # The birth certificate the school verified belongs to the child, not to a
    # form that is now closed.
    migrated = 0
    for doc in db.scalars(
        select(Document).where(
            Document.school_id == app.school_id,
            Document.owner_type == OwnerType.application,
            Document.owner_id == app.id,
            Document.deleted_at.is_(None),
        )
    ):
        doc.owner_type = OwnerType.student
        doc.owner_id = student.id
        migrated += 1

    medical = db.scalar(
        select(ApplicationMedical).where(ApplicationMedical.application_id == app.id)
    )

    app.student_id = student.id
    app_svc.move(
        db,
        app,
        ApplicationStatus.enrolled,
        actor=actor,
        reason=f"Converted to student {admission_no}",
    )

    entry = db.scalar(
        select(WaitlistEntry).where(WaitlistEntry.application_id == app.id)
    )
    if entry is not None:
        entry.status = WaitlistStatus.converted

    audit.record(
        db,
        actor=actor,
        school_id=app.school_id,
        entity_type="student",
        entity_id=student.id,
        action=AuditAction.create,
        after={
            "admission_no": admission_no,
            "from_application": app.application_no,
            "class": section.label,
            "documents_migrated": migrated,
        },
    )
    db.commit()

    return {
        "student_id": student.id,
        "admission_no": admission_no,
        "class_label": section.label,
        "student_login": {"login_id": admission_no, "password": DEFAULT_STUDENT_PASSWORD},
        "documents_migrated": migrated,
        "medical_transferred": medical is not None,
        "application_no": app.application_no,
    }


def _address_line(address: dict | None) -> str | None:
    if not address:
        return None
    parts = [
        address.get("line1"),
        address.get("line2"),
        address.get("city"),
        address.get("state"),
        address.get("pincode"),
    ]
    return ", ".join(str(p) for p in parts if p) or None


def _guardian_for(
    db: Session, app: Application, g: ApplicationGuardian
) -> Guardian:
    """Reuse the guardian already in the school when the mobile matches.

    A second child of the same family must not produce a second login, or the
    parent ends up with two portals and sees one child in each.
    """
    existing_user = db.scalar(
        select(User).where(
            User.school_id == app.school_id,
            User.login_id == g.mobile,
            User.role == UserRole.parent,
        )
    )
    if existing_user is not None:
        guardian = db.scalar(
            select(Guardian).where(Guardian.user_id == existing_user.id)
        )
        if guardian is not None:
            return guardian

    user = User(
        school_id=app.school_id,
        role=UserRole.parent,
        login_id=g.mobile,
        password_hash=hash_password(DEFAULT_GUARDIAN_PASSWORD),
        full_name=g.full_name,
        phone=g.mobile,
        email=g.email,
    )
    db.add(user)
    db.flush()
    guardian = Guardian(
        school_id=app.school_id,
        user_id=user.id,
        occupation=g.occupation,
        employee_id=g.employee_id,
    )
    db.add(guardian)
    db.flush()
    return guardian
