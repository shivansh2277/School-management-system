"""Student Certificates Service.

Manages Transfer Certificates (TC), Bonafide Certificates, and Character Certificates.
Implements multi-step lifecycle: Request -> Approval -> Issuance -> Reissue.
Atomic invariant: TC request or approval DOES NOT alter student status.
Only final issuance of a Transfer Certificate atomically transitions the student
to transferred_out status while strictly preserving all historical financial, academic,
attendance, and library records.
"""

from datetime import UTC, date, datetime
import json

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    AuditAction,
    CertificateTemplate,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    Guardian,
    School,
    Student,
    StudentCertificate,
    StudentGuardian,
    StudentStatus,
    User,
)
from app.pdf import certificate as cert_pdf
from app.services import audit, tenancy
from app.services.common import current_enrolment


PREFIX_MAP = {
    "transfer_certificate": "TC",
    "bonafide_certificate": "BON",
    "character_certificate": "CHAR",
}


def get_template(
    db: Session, school_id: int, certificate_type: str
) -> CertificateTemplate | None:
    return db.scalar(
        select(CertificateTemplate).where(
            CertificateTemplate.school_id == school_id,
            CertificateTemplate.certificate_type == certificate_type,
        )
    )


def save_template(
    db: Session,
    school_id: int,
    certificate_type: str,
    title: str,
    header_text: str | None = None,
    body_template: str | None = None,
    signatory_name: str | None = None,
    signatory_title: str | None = None,
    show_seal: bool = True,
    actor: User | None = None,
) -> CertificateTemplate:
    tmpl = get_template(db, school_id, certificate_type)
    if tmpl is None:
        tmpl = CertificateTemplate(
            school_id=school_id,
            certificate_type=certificate_type,
            title=title,
            header_text=header_text,
            body_template=body_template or "This is to certify that the particulars furnished above have been verified from official records.",
            signatory_name=signatory_name,
            signatory_title=signatory_title or "Principal",
            show_seal=show_seal,
        )
        db.add(tmpl)
    else:
        tmpl.title = title
        if header_text is not None:
            tmpl.header_text = header_text
        if body_template is not None:
            tmpl.body_template = body_template
        if signatory_name is not None:
            tmpl.signatory_name = signatory_name
        if signatory_title is not None:
            tmpl.signatory_title = signatory_title
        tmpl.show_seal = show_seal

    db.commit()
    return tmpl


def _build_student_snapshot(
    db: Session, student: Student, enrolment: Enrolment, extra_fields: dict | None = None
) -> dict:
    extra = extra_fields or {}
    guardians = db.execute(
        select(Guardian, StudentGuardian.relation)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == student.id)
    ).all()

    guardian_name = None
    mother_name = None
    for g, rel in guardians:
        rel_str = str(rel.value if hasattr(rel, "value") else rel).lower()
        if "mother" in rel_str:
            mother_name = g.user.full_name
        elif not guardian_name:
            guardian_name = g.user.full_name

    ay = db.get(AcademicYear, enrolment.academic_year_id) if enrolment.academic_year_id else None
    session_code = ay.code if ay else "2026-2027"

    return {
        "student_id": student.id,
        "student_name": student.user.full_name if student.user else "",
        "admission_no": student.admission_no,
        "enrolment_id": enrolment.id,
        "enrollment_code": f"ENR-{enrolment.id}",
        "class_label": enrolment.class_section.label if enrolment.class_section else "",
        "roll_no": enrolment.roll_no,
        "session_code": session_code,
        "dob": str(student.dob) if student.dob else "N/A",
        "gender": str(student.gender.value if hasattr(student.gender, "value") else student.gender or "N/A"),
        "admission_date": str(student.admission_date) if student.admission_date else "N/A",
        "guardian_name": guardian_name or "N/A",
        "mother_name": mother_name,
        "issue_date": str(date.today()),
        "reason": extra.get("reason", "On Parent's Request"),
        "conduct": extra.get("conduct", "Good"),
        "purpose": extra.get("purpose", "Official Verification"),
        "dues_cleared": extra.get("dues_cleared", "Cleared"),
        "leaving_date": extra.get("leaving_date", str(date.today())),
        "remarks": extra.get("remarks", ""),
    }


def request_certificate(
    db: Session,
    school_id: int,
    student_id: int,
    certificate_type: str,
    requested_by: User,
    reason: str,
    purpose: str | None = None,
    enrolment_id: int | None = None,
) -> StudentCertificate:
    """Submit a certificate request. Status becomes 'pending'.

    NOTE: Requesting a TC does NOT change student status!
    """
    if certificate_type not in PREFIX_MAP:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"Invalid certificate type '{certificate_type}'"
        )

    student = db.scalar(
        select(Student).where(Student.id == student_id, Student.school_id == school_id)
    )
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    if enrolment_id:
        enrolment = db.scalar(
            select(Enrolment).where(
                Enrolment.id == enrolment_id,
                Enrolment.student_id == student.id,
                Enrolment.school_id == school_id,
            )
        )
    else:
        enrolment = current_enrolment(db, student.id)

    if enrolment is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Student has no enrolment record to associate with certificate"
        )

    template = get_template(db, school_id, certificate_type)

    cert = StudentCertificate(
        school_id=school_id,
        certificate_type=certificate_type,
        student_id=student.id,
        enrolment_id=enrolment.id,
        status="requested",
        requested_by_id=requested_by.id,
        requested_at=datetime.now(UTC),
        data_snapshot={"reason": reason, "purpose": purpose} if (reason or purpose) else {},
    )
    db.add(cert)

    audit.record(
        db,
        actor=requested_by,
        school_id=school_id,
        entity_type="student_certificate",
        entity_id=student.id,
        action=AuditAction.create,
        after={
            "certificate_type": certificate_type,
            "student_id": student.id,
            "status": "requested",
        },
        reason=f"Requested {certificate_type}: {reason}",
    )
    db.commit()
    return cert


def approve_certificate(
    db: Session,
    school_id: int,
    certificate_id: int,
    approved_by: User,
) -> StudentCertificate:
    """Approve a pending certificate request. Status becomes 'approved'.

    NOTE: Approving a TC does NOT change student status!
    """
    cert = db.scalar(
        select(StudentCertificate).where(
            StudentCertificate.id == certificate_id,
            StudentCertificate.school_id == school_id,
        )
    )
    if cert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate request not found")
    if cert.status not in ("requested", "pending"):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Cannot approve certificate in '{cert.status}' state"
        )

    cert.status = "approved"
    cert.approved_by_id = approved_by.id
    cert.approved_at = datetime.now(UTC)

    audit.record(
        db,
        actor=approved_by,
        school_id=school_id,
        entity_type="student_certificate",
        entity_id=cert.id,
        action=AuditAction.status_change,
        after={"status": "approved"},
        reason="Certificate request approved",
    )
    db.commit()
    return cert


def reject_certificate(
    db: Session,
    school_id: int,
    certificate_id: int,
    rejected_by: User,
    rejection_reason: str,
) -> StudentCertificate:
    cert = db.scalar(
        select(StudentCertificate).where(
            StudentCertificate.id == certificate_id,
            StudentCertificate.school_id == school_id,
        )
    )
    if cert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate request not found")
    if cert.status not in ("requested", "pending", "approved"):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Cannot reject certificate in '{cert.status}' state"
        )

    cert.status = "rejected"
    cert.rejection_reason = rejection_reason

    audit.record(
        db,
        actor=rejected_by,
        school_id=school_id,
        entity_type="student_certificate",
        entity_id=cert.id,
        action=AuditAction.status_change,
        after={"status": "rejected", "rejection_reason": rejection_reason},
        reason=f"Certificate request rejected: {rejection_reason}",
    )
    db.commit()
    return cert


def issue_certificate(
    db: Session,
    school_id: int,
    issued_by: User,
    certificate_id: int | None = None,
    student_id: int | None = None,
    certificate_type: str | None = None,
    enrolment_id: int | None = None,
    conduct: str = "Good",
    reason: str | None = None,
    remarks: str | None = None,
    leaving_date: date | None = None,
) -> StudentCertificate:
    """Issue a certificate (directly or from an existing request).

    CRITICAL ATOMIC INVARIANT:
    If certificate_type == 'transfer_certificate', this issuance atomically updates:
      - student.status = StudentStatus.transferred_out
      - enrolment.status = EnrolmentStatus.transferred_out
      - student.user.is_active = False
    Preserving ALL historical student, fee, mark, attendance, and library records.
    Bonafide and Character certificates do NOT alter student status.
    """
    cert: StudentCertificate | None = None

    if certificate_id:
        cert = db.scalar(
            select(StudentCertificate).where(
                StudentCertificate.id == certificate_id,
                StudentCertificate.school_id == school_id,
            )
        )
        if cert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate request not found")
        if cert.status == "issued":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "This certificate has already been issued"
            )
        if cert.status in ("rejected", "cancelled"):
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Cannot issue a certificate in '{cert.status}' state"
            )
        student = cert.student
        enrolment = cert.enrolment
        cert_type = cert.certificate_type
    else:
        if not student_id or not certificate_type:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "student_id and certificate_type required"
            )
        cert_type = certificate_type
        student = db.scalar(
            select(Student).where(Student.id == student_id, Student.school_id == school_id)
        )
        if student is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

        if enrolment_id:
            enrolment = db.scalar(
                select(Enrolment).where(
                    Enrolment.id == enrolment_id,
                    Enrolment.student_id == student.id,
                    Enrolment.school_id == school_id,
                )
            )
        else:
            enrolment = current_enrolment(db, student.id)

        if enrolment is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Active enrolment required to issue certificate"
            )

        cert = StudentCertificate(
            school_id=school_id,
            certificate_type=cert_type,
            student_id=student.id,
            enrolment_id=enrolment.id,
            status="requested",
            requested_by_id=issued_by.id,
            requested_at=datetime.now(UTC),
            data_snapshot={"reason": reason} if reason else {},
        )
        db.add(cert)
        db.flush()

    # Concurrency-safe certificate numbering
    current_yr = tenancy.current_year(db, school_id)
    year_val = current_yr.start_date.year if current_yr and current_yr.start_date else date.today().year
    prefix = PREFIX_MAP.get(cert_type, "CERT")
    cert_no = audit.next_number(
        db,
        school_id,
        kind=f"cert_{prefix.lower()}",
        year=year_val,
        prefix=f"{prefix}-{year_val}",
        width=4,
    )

    # Freeze snapshot
    snapshot_extras = {
        "conduct": conduct,
        "reason": reason or (cert.data_snapshot or {}).get("reason") or "Completed Course / Relocation",
        "remarks": remarks or "",
        "leaving_date": str(leaving_date or date.today()),
        "issue_date": str(date.today()),
    }
    snapshot = _build_student_snapshot(db, student, enrolment, snapshot_extras)

    cert.certificate_no = cert_no
    cert.issue_date = date.today()
    cert.status = "issued"
    cert.issued_by_id = issued_by.id
    cert.issued_at = datetime.now(UTC)
    cert.data_snapshot = snapshot

    # ATOMIC STATUS CHANGE FOR TRANSFER CERTIFICATE ONLY
    if cert_type == "transfer_certificate":
        student.status = StudentStatus.transferred_out
        enrolment.status = EnrolmentStatus.transferred_out
        if student.user:
            student.user.is_active = False

        audit.record(
            db,
            actor=issued_by,
            school_id=school_id,
            entity_type="student",
            entity_id=student.id,
            action=AuditAction.status_change,
            after={
                "status": StudentStatus.transferred_out.value,
                "reason": f"Issued Transfer Certificate {cert_no}",
            },
            reason=f"Transfer Certificate {cert_no} issued",
        )

    audit.record(
        db,
        actor=issued_by,
        school_id=school_id,
        entity_type="student_certificate",
        entity_id=cert.id,
        action=AuditAction.publish,
        after={
            "certificate_no": cert_no,
            "status": "issued",
            "certificate_type": cert_type,
            "student_id": student.id,
        },
        reason=f"Issued certificate {cert_no}",
    )
    db.commit()
    return cert


def reissue_certificate(
    db: Session,
    school_id: int,
    certificate_id: int,
    reissued_by: User,
    reason: str,
) -> StudentCertificate:
    """Mark certificate as reissued/duplicate and record in audit log."""
    cert = db.scalar(
        select(StudentCertificate).where(
            StudentCertificate.id == certificate_id,
            StudentCertificate.school_id == school_id,
        )
    )
    if cert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate not found")
    if cert.status != "issued":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only issued certificates can be reissued"
        )

    cert.is_reissue = True
    cert.reissue_count += 1
    cert.reissue_reason = reason
    extra = dict(cert.data_snapshot or {})
    extra["last_reissued_at"] = datetime.now(UTC).isoformat()
    extra["reissue_reason"] = reason
    extra["reissue_count"] = cert.reissue_count
    cert.data_snapshot = extra

    audit.record(
        db,
        actor=reissued_by,
        school_id=school_id,
        entity_type="student_certificate",
        entity_id=cert.id,
        action=AuditAction.print,
        after={"reissue_count": cert.reissue_count, "reason": reason},
        reason=f"Certificate {cert.certificate_no} re-issued (Duplicate #{cert.reissue_count}): {reason}",
    )
    db.commit()
    return cert


def get_certificate_pdf_bytes(
    db: Session,
    school_id: int,
    certificate_id: int,
) -> bytes:
    cert = db.scalar(
        select(StudentCertificate).where(
            StudentCertificate.id == certificate_id,
            StudentCertificate.school_id == school_id,
        )
    )
    if cert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate not found")
    if cert.status != "issued":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Certificate PDF is only available for issued certificates"
        )

    school = db.get(School, school_id)
    template = get_template(db, school_id, cert.certificate_type)
    template_config = {
        "title": template.title if template else None,
        "header_text": template.header_text if template else None,
        "body_template": template.body_template if template else None,
        "signatory_name": template.signatory_name if template else None,
        "signatory_title": template.signatory_title if template else None,
        "show_seal": template.show_seal if template else True,
    }
    is_dup = cert.is_reissue or (cert.reissue_count > 0)

    return cert_pdf.generate_certificate_pdf(
        school=school,
        cert_type=cert.certificate_type,
        cert_no=cert.certificate_no or f"CERT-{cert.id}",
        student_snapshot=cert.data_snapshot or {},
        template_config=template_config,
        is_duplicate=is_dup,
    )


def list_certificates(
    db: Session,
    school_id: int,
    cert_type: str | None = None,
    status_filter: str | None = None,
    search_q: str | None = None,
    student_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    stmt = (
        select(StudentCertificate)
        .join(Student, Student.id == StudentCertificate.student_id)
        .join(User, User.id == Student.user_id)
        .where(StudentCertificate.school_id == school_id)
    )
    if cert_type:
        stmt = stmt.where(StudentCertificate.certificate_type == cert_type)
    if status_filter:
        stmt = stmt.where(StudentCertificate.status == status_filter)
    if student_id:
        stmt = stmt.where(StudentCertificate.student_id == student_id)
    if search_q:
        clean = f"%{search_q.strip()}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(clean),
                Student.admission_no.ilike(clean),
                StudentCertificate.certificate_no.ilike(clean),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(StudentCertificate.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.scalars(stmt).all())

    out = []
    for c in rows:
        student = c.student
        enrolment = c.enrolment
        out.append(
            {
                "id": c.id,
                "certificate_type": c.certificate_type,
                "certificate_no": c.certificate_no,
                "status": c.status,
                "student_id": c.student_id,
                "student_name": student.user.full_name if student and student.user else "",
                "admission_no": student.admission_no if student else "",
                "enrolment_id": c.enrolment_id,
                "enrollment_code": f"ENR-{c.enrolment_id}" if c.enrolment_id else "",
                "class_label": enrolment.class_section.label if enrolment and enrolment.class_section else "",
                "reason": (c.data_snapshot or {}).get("reason", ""),
                "rejection_reason": c.rejection_reason,
                "is_reissue": c.is_reissue,
                "reissue_count": c.reissue_count,
                "reissue_reason": c.reissue_reason,
                "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                "requested_by_name": c.requested_by.full_name if c.requested_by else None,
                "requested_at": c.requested_at.isoformat() if c.requested_at else None,
                "approved_by_name": c.approved_by.full_name if c.approved_by else None,
                "approved_at": c.approved_at.isoformat() if c.approved_at else None,
                "issued_by_name": c.issued_by.full_name if c.issued_by else None,
                "issued_at": c.issued_at.isoformat() if c.issued_at else None,
            }
        )
    return out, total
