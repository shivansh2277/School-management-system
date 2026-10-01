"""Student Certificates API router.

Exposes certificate request, approval, issuance, reissue, and template configuration.
Gated with explicit permissions: certificates.read, certificates.request, certificates.approve, certificates.issue.
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.services import certificates as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled


router = APIRouter(
    prefix="/admin/certificates",
    tags=["certificates"],
    dependencies=[Depends(module_enabled("students"))],
)

reader = require_permission("certificates.read", school_wide=True)
requester = require_permission("certificates.request")
approver = require_permission("certificates.approve", school_wide=True)
issuer = require_permission("certificates.issue", school_wide=True)


class CertificateRequestInput(BaseModel):
    model_config = {"extra": "forbid"}

    student_id: int
    certificate_type: str = Field(pattern=r"^(transfer_certificate|bonafide_certificate|character_certificate)$")
    reason: str = Field(min_length=3, max_length=255)
    purpose: str | None = Field(None, max_length=255)
    enrolment_id: int | None = None


class RejectCertificateInput(BaseModel):
    model_config = {"extra": "forbid"}

    rejection_reason: str = Field(min_length=3, max_length=255)


class IssueCertificateInput(BaseModel):
    model_config = {"extra": "forbid"}

    certificate_id: int | None = None
    student_id: int | None = None
    certificate_type: str | None = None
    enrolment_id: int | None = None
    conduct: str = "Good"
    reason: str | None = None
    remarks: str | None = None
    leaving_date: Date | None = None


class ReissueCertificateInput(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(min_length=3, max_length=255)


class TemplateUpdateInput(BaseModel):
    model_config = {"extra": "ignore"}

    title: str = Field(min_length=1, max_length=120)
    header_text: str | None = None
    body_template: str | None = None
    signatory_name: str | None = None
    signatory_title: str | None = None
    show_seal: bool = True


@router.get("")
def list_certificates(
    cert_type: str | None = Query(None),
    status: str | None = Query(None),
    q: str | None = Query(None),
    student_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    items, total = svc.list_certificates(
        db,
        user.school_id,
        cert_type=cert_type,
        status_filter=status,
        search_q=q,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/requests", status_code=status.HTTP_201_CREATED)
def request_certificate(
    body: CertificateRequestInput,
    user: User = Depends(requester),
    db: Session = Depends(get_db),
) -> dict:
    cert = svc.request_certificate(
        db,
        user.school_id,
        student_id=body.student_id,
        certificate_type=body.certificate_type,
        requested_by=user,
        reason=body.reason,
        purpose=body.purpose,
        enrolment_id=body.enrolment_id,
    )
    return {
        "id": cert.id,
        "certificate_type": cert.certificate_type,
        "status": cert.status,
        "reason": body.reason,
    }


@router.post("/{certificate_id}/approve")
def approve_certificate(
    certificate_id: int,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    cert = svc.approve_certificate(db, user.school_id, certificate_id, approved_by=user)
    return {
        "id": cert.id,
        "status": cert.status,
    }


@router.post("/{certificate_id}/reject")
def reject_certificate(
    certificate_id: int,
    body: RejectCertificateInput,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    cert = svc.reject_certificate(
        db, user.school_id, certificate_id, rejected_by=user, rejection_reason=body.rejection_reason
    )
    return {
        "id": cert.id,
        "status": cert.status,
        "rejection_reason": cert.rejection_reason,
    }


@router.post("/issue")
def issue_certificate(
    body: IssueCertificateInput,
    user: User = Depends(issuer),
    db: Session = Depends(get_db),
) -> dict:
    cert = svc.issue_certificate(
        db,
        user.school_id,
        issued_by=user,
        certificate_id=body.certificate_id,
        student_id=body.student_id,
        certificate_type=body.certificate_type,
        enrolment_id=body.enrolment_id,
        conduct=body.conduct,
        reason=body.reason,
        remarks=body.remarks,
        leaving_date=body.leaving_date,
    )
    return {
        "id": cert.id,
        "certificate_no": cert.certificate_no,
        "status": cert.status,
        "student_id": cert.student_id,
        "issued_at": cert.issued_at.isoformat(),
    }


@router.post("/{certificate_id}/reissue")
def reissue_certificate(
    certificate_id: int,
    body: ReissueCertificateInput,
    user: User = Depends(issuer),
    db: Session = Depends(get_db),
) -> dict:
    cert = svc.reissue_certificate(
        db, user.school_id, certificate_id, reissued_by=user, reason=body.reason
    )
    return {
        "id": cert.id,
        "certificate_no": cert.certificate_no,
        "reissue_count": cert.reissue_count,
    }


@router.get("/{certificate_id}/pdf")
def download_certificate_pdf(
    certificate_id: int,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> Response:
    pdf_bytes = svc.get_certificate_pdf_bytes(db, user.school_id, certificate_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="certificate-{certificate_id}.pdf"'
        },
    )


@router.get("/templates/{cert_type}")
def get_template(
    cert_type: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    tmpl = svc.get_template(db, user.school_id, cert_type)
    if tmpl is None:
        title_map = {
            "transfer_certificate": "SCHOOL LEAVING / TRANSFER CERTIFICATE",
            "bonafide_certificate": "BONAFIDE CERTIFICATE",
            "character_certificate": "CHARACTER CERTIFICATE",
        }
        return {
            "certificate_type": cert_type,
            "title": title_map.get(cert_type, "STUDENT CERTIFICATE"),
            "header_text": "Recognized & Affiliated to CBSE",
            "body_template": "This is to certify that the particulars furnished above have been verified from official records.",
            "signatory_name": "Principal",
            "signatory_title": "Principal / Head of Institution",
            "show_seal": True,
        }
    return {
        "id": tmpl.id,
        "certificate_type": tmpl.certificate_type,
        "title": tmpl.title,
        "header_text": tmpl.header_text,
        "body_template": tmpl.body_template,
        "signatory_name": tmpl.signatory_name,
        "signatory_title": tmpl.signatory_title,
        "show_seal": tmpl.show_seal,
    }


@router.put("/templates/{cert_type}")
def update_template(
    cert_type: str,
    body: TemplateUpdateInput,
    user: User = Depends(issuer),
    db: Session = Depends(get_db),
) -> dict:
    tmpl = svc.save_template(
        db,
        user.school_id,
        certificate_type=cert_type,
        title=body.title,
        header_text=body.header_text,
        body_template=body.body_template,
        signatory_name=body.signatory_name,
        signatory_title=body.signatory_title,
        show_seal=body.show_seal,
        actor=user,
    )
    return {
        "id": tmpl.id,
        "certificate_type": tmpl.certificate_type,
        "title": tmpl.title,
        "header_text": tmpl.header_text,
        "body_template": tmpl.body_template,
        "signatory_name": tmpl.signatory_name,
        "signatory_title": tmpl.signatory_title,
        "show_seal": tmpl.show_seal,
    }
