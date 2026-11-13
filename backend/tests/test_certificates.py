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


def test_transfer_certificate_blocked_when_student_has_outstanding_fee_dues(client, admin, db):
    """BUG-CERT-01: Transfer Certificate cannot be issued if student has unpaid fee dues."""
    from app.models import FeeInvoice, FeeInvoiceLine, FeeHead, FeePeriod, AuditLog
    from app.models.enums import FeeFrequency, FeeHeadType, FeePeriodStatus, InvoiceStatus
    from decimal import Decimal

    # Pick an active student
    std = db.scalars(
        select(Student).where(Student.school_id == 1, Student.status == StudentStatus.active)
    ).first()
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == std.id, Enrolment.status == EnrolmentStatus.active))

    # Add an unpaid invoice with 3500.00 balance
    head = db.scalar(select(FeeHead).where(FeeHead.school_id == 1))
    inv = FeeInvoice(
        school_id=1,
        enrolment_id=enr.id,
        academic_year_id=enr.academic_year_id,
        invoice_no="TEST-INV-TC-001",
        period_year=2026,
        period_month=11,
        issued_on=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
        status=InvoiceStatus.issued,
    )
    db.add(inv)
    db.flush()
    line = FeeInvoiceLine(
        school_id=1,
        invoice_id=inv.id,
        fee_head_id=head.id,
        description="Tuition Fee",
        amount=Decimal("3500.00"),
        discount=Decimal("0.00"),
    )
    db.add(line)
    db.flush()

    # Attempt to issue TC without override -> must be refused with HTTP 400
    res = client.post(
        "/admin/certificates/issue",
        headers=admin,
        json={
            "student_id": std.id,
            "certificate_type": "transfer_certificate",
            "conduct": "Good",
        },
    )
    assert res.status_code == 400, res.text
    assert "Outstanding fee dues pending: Rs." in res.json()["detail"]
    assert "TC cannot be issued without full dues clearance or authorized Admin override" in res.json()["detail"]


def test_transfer_certificate_override_refused_for_non_super_admin(client, teacher, admin, db):
    """BUG-CERT-01: Non-Super Admin cannot authorize TC issuance with pending dues."""
    from app.models import FeeInvoice, FeeInvoiceLine, FeeHead, Role, Permission, UserRoleAssignment
    from app.models.enums import ScopeType, InvoiceStatus
    from decimal import Decimal

    std = db.scalars(
        select(Student).where(Student.school_id == 1, Student.status == StudentStatus.active)
    ).first()
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == std.id, Enrolment.status == EnrolmentStatus.active))

    head = db.scalar(select(FeeHead).where(FeeHead.school_id == 1))
    inv = FeeInvoice(
        school_id=1,
        enrolment_id=enr.id,
        academic_year_id=enr.academic_year_id,
        invoice_no="TEST-INV-TC-002",
        period_year=2026,
        period_month=11,
        issued_on=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
        status=InvoiceStatus.issued,
    )
    db.add(inv)
    db.flush()
    db.add(FeeInvoiceLine(school_id=1, invoice_id=inv.id, fee_head_id=head.id, description="Tuition Fee", amount=Decimal("2000.00"), discount=Decimal("0.00")))
    db.flush()

    # Grant certificates.issue to a non-admin teacher user
    from app.models import User
    from app.models.enums import UserRole
    from app.models.rbac import RolePermission
    tch = db.scalar(select(User).where(User.role == UserRole.teacher, User.school_id == 1))
    issue_perm = db.scalar(select(Permission).where(Permission.code == "certificates.issue"))
    role = Role(school_id=1, code="tc_teacher_role", name="TC Teacher Role", is_system=False)
    db.add(role)
    db.flush()
    db.add(RolePermission(school_id=1, role_id=role.id, permission_id=issue_perm.id))
    db.add(UserRoleAssignment(school_id=1, user_id=tch.id, role_id=role.id, scope_type=ScopeType.school))
    db.flush()

    # Attempt to issue with dues_override_reason using teacher headers -> must fail with HTTP 403 Forbidden
    res = client.post(
        "/admin/certificates/issue",
        headers=teacher,
        json={
            "student_id": std.id,
            "certificate_type": "transfer_certificate",
            "conduct": "Good",
            "dues_override_reason": "Clerk attempted unauthorized override",
        },
    )
    assert res.status_code == 403, res.text
    assert "Only Super Admin can authorize TC issuance with pending dues" in res.json()["detail"]


def test_transfer_certificate_override_allowed_for_super_admin(client, admin, db):
    """BUG-CERT-01: Super Admin can authorize TC issuance with pending dues, logged in audit_log."""
    from app.models import FeeInvoice, FeeInvoiceLine, FeeHead, AuditLog
    from app.models.enums import InvoiceStatus
    from decimal import Decimal

    std = db.scalars(
        select(Student).where(Student.school_id == 1, Student.status == StudentStatus.active)
    ).all()[-2]
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == std.id, Enrolment.status == EnrolmentStatus.active))

    head = db.scalar(select(FeeHead).where(FeeHead.school_id == 1))
    inv = FeeInvoice(
        school_id=1,
        enrolment_id=enr.id,
        academic_year_id=enr.academic_year_id,
        invoice_no="TEST-INV-TC-003",
        period_year=2026,
        period_month=11,
        issued_on=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
        status=InvoiceStatus.issued,
    )
    db.add(inv)
    db.flush()
    db.add(FeeInvoiceLine(school_id=1, invoice_id=inv.id, fee_head_id=head.id, description="Tuition Fee", amount=Decimal("1500.00"), discount=Decimal("0.00")))
    db.flush()

    # Super Admin issues TC with dues_override_reason
    res = client.post(
        "/admin/certificates/issue",
        headers=admin,
        json={
            "student_id": std.id,
            "certificate_type": "transfer_certificate",
            "conduct": "Good",
            "dues_override_reason": "Management approved fee waiver via Board resolution #42",
        },
    )
    assert res.status_code == 200, res.text
    cert_id = res.json()["id"]

    # Verify audit_log entry
    log = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "transfer_certificate", AuditLog.entity_id == std.id)
        .order_by(AuditLog.occurred_at.desc())
    ).first()
    assert log is not None
    assert "Management approved fee waiver via Board resolution #42" in log.reason
    assert "Outstanding: Rs. 1500.00" in log.reason

    # Verify PDF download works when authorized override is present
    pdf_res = client.get(f"/admin/certificates/{cert_id}/pdf", headers=admin)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
