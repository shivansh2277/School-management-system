import re
from pathlib import Path

test_path = Path("backend/tests/test_certificates.py")
code = test_path.read_text(encoding="utf-8")

idx = code.find("def test_transfer_certificate_blocked_when_student_has_outstanding_fee_dues")
if idx != -1:
    code = code[:idx].rstrip() + "\n"

new_tests = '''

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

    # Create a non-super-admin user who has certificates.issue permission
    from app.models import User
    from app.models.enums import UserRole
    issuer_user = User(
        school_id=1,
        login_id="tc_clerk@sunrisepublic.edu",
        role=UserRole.staff,
        full_name="TC Issuing Clerk",
        is_active=True,
    )
    issuer_user.set_password("Clerk@123")
    db.add(issuer_user)
    db.flush()

    # Grant certificates.issue to this user
    issue_perm = db.scalar(select(Permission).where(Permission.code == "certificates.issue"))
    role = Role(school_id=1, code="tc_clerk_role", name="TC Clerk Role", is_system=False)
    db.add(role)
    db.flush()
    from app.models.rbac import RolePermission
    db.add(RolePermission(school_id=1, role_id=role.id, permission_id=issue_perm.id))
    db.add(UserRoleAssignment(school_id=1, user_id=issuer_user.id, role_id=role.id, scope_type=ScopeType.school))
    db.flush()

    # Login as tc_clerk
    login_res = client.post("/auth/login", json={"login_id": "tc_clerk@sunrisepublic.edu", "password": "Clerk@123"})
    assert login_res.status_code == 200, login_res.text
    clerk_headers = {"Authorization": f"Bearer {login_res.json()['token']}"}

    # Attempt to issue with dues_override_reason -> must fail with HTTP 403 Forbidden
    res = client.post(
        "/admin/certificates/issue",
        headers=clerk_headers,
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
'''

code += new_tests
test_path.write_text(code, encoding="utf-8")
print("Updated test_certificates.py with fee_head_id and description")
