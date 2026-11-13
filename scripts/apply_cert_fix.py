import re
from pathlib import Path

cert_svc_path = Path("backend/app/services/certificates.py")
code = cert_svc_path.read_text(encoding="utf-8")

if "from decimal import Decimal" not in code:
    code = "from decimal import Decimal\n" + code

dues_func = '''
def get_student_outstanding_dues(db: Session, school_id: int, student_id: int) -> Decimal:
    from app.services import fees
    from app.models.fees import FeeInvoice, InvoiceStatus
    from app.models.enrolment import Enrolment
    invoices = db.scalars(
        select(FeeInvoice)
        .join(Enrolment, Enrolment.id == FeeInvoice.enrolment_id)
        .where(
            Enrolment.student_id == student_id,
            FeeInvoice.school_id == school_id,
            FeeInvoice.status.not_in([InvoiceStatus.voided, InvoiceStatus.written_off]),
        )
    ).all()
    return sum((fees.totals(db, inv)["balance"] for inv in invoices), Decimal("0.00"))
'''

if "def get_student_outstanding_dues" not in code:
    idx = code.find("def request_certificate")
    assert idx != -1
    code = code[:idx] + dues_func + "\n\n" + code[idx:]

old_sig = """    remarks: str | None = None,
    leaving_date: date | None = None,
) -> StudentCertificate:"""

new_sig = """    remarks: str | None = None,
    leaving_date: date | None = None,
    dues_override_reason: str | None = None,
) -> StudentCertificate:"""

if old_sig in code:
    code = code.replace(old_sig, new_sig, 1)

check_marker = "    # Freeze snapshot\n    snapshot_extras = {"
new_check = '''    # FEE DUES CLEARANCE GATE FOR TRANSFER CERTIFICATES (BUG-CERT-01)
    if cert_type == "transfer_certificate":
        dues = get_student_outstanding_dues(db, school_id, student.id)
        if dues > Decimal("0.00"):
            if not dues_override_reason:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Outstanding fee dues pending: Rs. {dues:.2f}. TC cannot be issued without full dues clearance or authorized Admin override",
                )
            from app.models.enums import UserRole
            from app.models.rbac import Role, ScopeType, UserRoleAssignment
            is_super_admin = (
                issued_by.role == UserRole.admin
                or db.scalar(
                    select(UserRoleAssignment.id)
                    .join(Role, Role.id == UserRoleAssignment.role_id)
                    .where(
                        UserRoleAssignment.user_id == issued_by.id,
                        Role.code.in_(("super_admin", "principal")),
                        UserRoleAssignment.scope_type == ScopeType.school,
                    )
                ) is not None
            )
            if not is_super_admin:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Only Super Admin can authorize TC issuance with pending dues",
                )
            audit.record(
                db,
                actor=issued_by,
                school_id=school_id,
                entity_type="transfer_certificate",
                entity_id=student.id,
                action=AuditAction.status_change,
                reason=f"Fee dues override: {dues_override_reason} (Outstanding: Rs. {dues:.2f})",
            )

    # Freeze snapshot
    snapshot_extras = {'''

if check_marker in code and "BUG-CERT-01" not in code:
    code = code.replace(check_marker, new_check, 1)

extras_marker = '        "issue_date": str(date.today()),\n    }'
new_extras = '''        "issue_date": str(date.today()),
        "dues_override": dues_override_reason if (cert_type == "transfer_certificate" and dues_override_reason) else None,
    }'''
if extras_marker in code:
    code = code.replace(extras_marker, new_extras, 1)

pdf_marker = '''    if cert.status != "issued":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Certificate PDF is only available for issued certificates"
        )'''

new_pdf_check = '''    if cert.status != "issued":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Certificate PDF is only available for issued certificates"
        )

    if cert.certificate_type == "transfer_certificate":
        snapshot = cert.data_snapshot or {}
        if not snapshot.get("dues_override"):
            dues = get_student_outstanding_dues(db, school_id, cert.student_id)
            if dues > Decimal("0.00"):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Outstanding fee dues pending: Rs. {dues:.2f}. TC cannot be printed without full dues clearance or authorized Admin override",
                )'''

if pdf_marker in code and "if not snapshot.get(\"dues_override\"):" not in code:
    code = code.replace(pdf_marker, new_pdf_check, 1)

cert_svc_path.write_text(code, encoding="utf-8")
print("Successfully patched backend/app/services/certificates.py")

# Now patch backend/app/api/admin/certificates.py
cert_api_path = Path("backend/app/api/admin/certificates.py")
api_code = cert_api_path.read_text(encoding="utf-8")

old_input = """class IssueCertificateInput(BaseModel):
    model_config = {"extra": "forbid"}

    certificate_id: int | None = None
    student_id: int | None = None
    certificate_type: str | None = None
    enrolment_id: int | None = None
    conduct: str = "Good"
    reason: str | None = None
    remarks: str | None = None
    leaving_date: Date | None = None"""

new_input = """class IssueCertificateInput(BaseModel):
    model_config = {"extra": "forbid"}

    certificate_id: int | None = None
    student_id: int | None = None
    certificate_type: str | None = None
    enrolment_id: int | None = None
    conduct: str = "Good"
    reason: str | None = None
    remarks: str | None = None
    leaving_date: Date | None = None
    dues_override_reason: str | None = None"""

if old_input in api_code:
    api_code = api_code.replace(old_input, new_input, 1)

old_call = """        remarks=body.remarks,
        leaving_date=body.leaving_date,
    )"""

new_call = """        remarks=body.remarks,
        leaving_date=body.leaving_date,
        dues_override_reason=body.dues_override_reason,
    )"""

if old_call in api_code:
    api_code = api_code.replace(old_call, new_call, 1)

cert_api_path.write_text(api_code, encoding="utf-8")
print("Successfully patched backend/app/api/admin/certificates.py")
