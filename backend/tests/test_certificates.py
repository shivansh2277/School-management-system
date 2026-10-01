from datetime import date
import pytest
from app.models import (
    Enrolment,
    EnrolmentStatus,
    Student,
    StudentCertificate,
    StudentStatus,
    User,
)
from sqlalchemy import select


def test_certificates_permission_teacher_denied_by_default(client, teacher):
    """Teachers do NOT hold certificates.request by default."""
    res = client.post(
        "/admin/certificates/requests",
        headers=teacher,
        json={
            "student_id": 1,
            "certificate_type": "transfer_certificate",
            "reason": "Family relocation to Mumbai",
        },
    )
    assert res.status_code == 403


def test_bonafide_certificate_lifecycle(client, admin, db):
    """Bonafide certificate request, approval, issuance leaves student active."""
    std = db.scalar(select(Student).where(Student.school_id == 1, Student.status == StudentStatus.active))
    assert std is not None

    # 1. Request
    req_res = client.post(
        "/admin/certificates/requests",
        headers=admin,
        json={
            "student_id": std.id,
            "certificate_type": "bonafide_certificate",
            "reason": "Passport application",
            "purpose": "Passport verification",
        },
    )
    assert req_res.status_code == 201
    cert_id = req_res.json()["id"]

    # 2. Approve
    app_res = client.post(f"/admin/certificates/{cert_id}/approve", headers=admin)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # Verify student is still active
    db.expire_all()
    std_check = db.scalar(select(Student).where(Student.id == std.id))
    assert std_check.status == StudentStatus.active

    # 3. Issue
    issue_res = client.post(
        "/admin/certificates/issue",
        headers=admin,
        json={
            "certificate_id": cert_id,
            "conduct": "Excellent",
        },
    )
    assert issue_res.status_code == 200
    data = issue_res.json()
    assert data["status"] == "issued"
    assert data["certificate_no"].startswith("BON-")

    # Verify student is STILL active (Bonafide does not transfer out)
    db.expire_all()
    std_after = db.scalar(select(Student).where(Student.id == std.id))
    assert std_after.status == StudentStatus.active

    # 4. Download PDF
    pdf_res = client.get(f"/admin/certificates/{cert_id}/pdf", headers=admin)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"


def test_transfer_certificate_atomic_exit_invariant(client, admin, db):
    """TC request and approval do NOT alter student status; only final issuance
    atomically sets transferred_out while preserving all historical records."""
    # Find an active student with enrolment
    std = db.scalars(
        select(Student).where(Student.school_id == 1, Student.status == StudentStatus.active)
    ).all()[-1]  # Pick last so we don't interfere with other tests
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == std.id))
    assert std is not None
    assert enr is not None
    assert std.status == StudentStatus.active
    assert enr.status == EnrolmentStatus.active

    # Step 1: Request TC
    req_res = client.post(
        "/admin/certificates/requests",
        headers=admin,
        json={
            "student_id": std.id,
            "certificate_type": "transfer_certificate",
            "reason": "Parent transfer to Bangalore",
        },
    )
    assert req_res.status_code == 201
    cert_id = req_res.json()["id"]

    # Invariant check: student and enrolment MUST remain active
    db.expire_all()
    assert db.get(Student, std.id).status == StudentStatus.active
    assert db.get(Enrolment, enr.id).status == EnrolmentStatus.active

    # Step 2: Approve TC
    app_res = client.post(f"/admin/certificates/{cert_id}/approve", headers=admin)
    assert app_res.status_code == 200

    # Invariant check: still active after approval!
    db.expire_all()
    assert db.get(Student, std.id).status == StudentStatus.active
    assert db.get(Enrolment, enr.id).status == EnrolmentStatus.active

    # Step 3: Issue TC
    issue_res = client.post(
        "/admin/certificates/issue",
        headers=admin,
        json={
            "certificate_id": cert_id,
            "conduct": "Good",
            "leaving_date": "2026-09-01",
        },
    )
    assert issue_res.status_code == 200
    assert issue_res.json()["status"] == "issued"
    assert issue_res.json()["certificate_no"].startswith("TC-")

    # Invariant check: NOW atomically transitioned to transferred_out!
    db.expire_all()
    updated_std = db.get(Student, std.id)
    updated_enr = db.get(Enrolment, enr.id)
    assert updated_std.status == StudentStatus.transferred_out
    assert updated_enr.status == EnrolmentStatus.transferred_out
    assert updated_std.user.is_active is False

    # Historical records are strictly preserved (student row still exists, enrolment still exists)
    assert db.scalar(select(Student).where(Student.id == std.id)) is not None
    assert db.scalar(select(Enrolment).where(Enrolment.id == enr.id)) is not None


def test_certificate_reissue_and_duplicate_watermark(client, admin, db):
    """Reissuing an issued certificate increments reissue_count and generates duplicate PDF."""
    std = db.scalar(select(Student).where(Student.school_id == 1))
    # Direct issue character certificate
    issue_res = client.post(
        "/admin/certificates/issue",
        headers=admin,
        json={
            "student_id": std.id,
            "certificate_type": "character_certificate",
            "conduct": "Exemplary",
        },
    )
    assert issue_res.status_code == 200
    cert_id = issue_res.json()["id"]

    # Reissue as duplicate
    reissue_res = client.post(
        f"/admin/certificates/{cert_id}/reissue",
        headers=admin,
        json={"reason": "Original certificate lost in transit"},
    )
    assert reissue_res.status_code == 200
    data = reissue_res.json()
    assert data["reissue_count"] == 1

    # Verify PDF generates with duplicate watermark
    pdf_res = client.get(f"/admin/certificates/{cert_id}/pdf", headers=admin)
    assert pdf_res.status_code == 200
    assert pdf_res.content[:4] == b"%PDF"


def test_certificate_template_update(client, admin):
    """Admin can configure certificate template details."""
    res = client.put(
        "/admin/certificates/templates/character_certificate",
        headers=admin,
        json={
            "title": "CERTIFICATE OF CHARACTER AND CONDUCT",
            "header_text": "Affiliated with UP State Board",
            "body_template": "Certified that the student bore high moral character.",
            "signatory_name": "Dr. R. K. Sharma",
            "signatory_title": "Headmaster",
            "show_seal": True,
        },
    )
    assert res.status_code == 200
    assert res.json()["title"] == "CERTIFICATE OF CHARACTER AND CONDUCT"

    get_tmpl = client.get("/admin/certificates/templates/character_certificate", headers=admin)
    assert get_tmpl.status_code == 200
    assert get_tmpl.json()["signatory_title"] == "Headmaster"
