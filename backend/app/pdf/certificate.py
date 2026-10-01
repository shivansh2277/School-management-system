"""Student Certificate PDF Generator.

Generates official Transfer, Bonafide, and Character certificates using configurable
institutional details, school branding, signatory, and customizable certificate wording.
Does NOT hardcode CBSE-only assumptions.
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.models import School


def generate_certificate_pdf(
    school: School,
    cert_type: str,  # "transfer_certificate" | "bonafide_certificate" | "character_certificate"
    cert_no: str,
    student_snapshot: dict,
    template_config: dict | None = None,
    is_duplicate: bool = False,
) -> bytes:
    """Generate professional printable certificate PDF on A4."""
    buf = BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    config = template_config or {}
    primary_color = colors.HexColor(school.primary_color or "#5B4BE0")

    # Double decorative border
    margin = 15 * mm
    c.saveState()
    c.setStrokeColor(primary_color)
    c.setLineWidth(2.5)
    c.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin)

    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(0.75)
    c.rect(margin + 2.5 * mm, margin + 2.5 * mm, page_w - 2 * margin - 5 * mm, page_h - 2 * margin - 5 * mm)

    # Watermark if duplicate
    if is_duplicate:
        c.saveState()
        c.setFont("Helvetica-Bold", 60)
        c.setFillColor(colors.HexColor("#F1F5F9"))
        c.translate(page_w / 2.0, page_h / 2.0)
        c.rotate(45)
        c.drawCentredString(0, 0, "DUPLICATE")
        c.restoreState()

    y = page_h - margin - 15 * mm

    # School Header
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(page_w / 2.0, y, (school.name or "Sunrise Public School").upper())

    y -= 5 * mm
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 9)
    affiliation = config.get("header_text") or config.get("affiliation_info") or f"Recognized & Affiliated to {school.board or 'State Education Board'}"
    c.drawCentredString(page_w / 2.0, y, affiliation)

    y -= 4 * mm
    address_line = f"{school.address or ''}, {school.city or ''}, {school.state or ''}".strip(", ")
    c.drawCentredString(page_w / 2.0, y, address_line)

    if school.phone or school.email:
        y -= 4 * mm
        contact_line = f"Phone: {school.phone or 'N/A'} | Email: {school.email or 'N/A'}"
        c.drawCentredString(page_w / 2.0, y, contact_line)

    # Decorative separator line
    y -= 5 * mm
    c.setStrokeColor(primary_color)
    c.setLineWidth(1.0)
    c.line(margin + 20 * mm, y, page_w - margin - 20 * mm, y)

    # Certificate Title
    y -= 12 * mm
    title_map = {
        "transfer_certificate": "SCHOOL LEAVING / TRANSFER CERTIFICATE",
        "bonafide_certificate": "BONAFIDE CERTIFICATE",
        "character_certificate": "CHARACTER CERTIFICATE",
    }
    cert_title = config.get("title") or title_map.get(cert_type, "STUDENT CERTIFICATE")

    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_w / 2.0, y, cert_title)

    # Certificate Number & Date header
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(margin + 12 * mm, y, f"Certificate No: {cert_no}")
    issue_date_str = student_snapshot.get("issue_date") or ""
    c.drawRightString(page_w - margin - 12 * mm, y, f"Date of Issue: {issue_date_str}")

    # Horizontal divider
    y -= 4 * mm
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(0.5)
    c.line(margin + 10 * mm, y, page_w - margin - 10 * mm, y)

    # Particulars table / details
    y -= 10 * mm
    left_x = margin + 14 * mm
    val_x = left_x + 55 * mm

    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#1E293B"))

    def draw_row(label: str, val: str, cur_y: float) -> float:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_x, cur_y, label)
        c.drawString(left_x + 50 * mm, cur_y, ":")
        c.setFont("Helvetica", 9)
        c.drawString(val_x, cur_y, str(val or "N/A"))
        return cur_y - 7.5 * mm

    y = draw_row("1. Name of Student", student_snapshot.get("student_name", ""), y)
    y = draw_row("2. Father's / Guardian's Name", student_snapshot.get("guardian_name", ""), y)
    if student_snapshot.get("mother_name"):
        y = draw_row("3. Mother's Name", student_snapshot.get("mother_name", ""), y)
    y = draw_row("4. Admission Number", student_snapshot.get("admission_no", ""), y)
    y = draw_row("5. Enrollment ID", student_snapshot.get("enrollment_code", f"ENR-{student_snapshot.get('enrolment_id', '')}"), y)
    y = draw_row("6. Class & Section", student_snapshot.get("class_label", ""), y)
    y = draw_row("7. Roll Number", str(student_snapshot.get("roll_no", "")), y)
    y = draw_row("8. Date of Birth", student_snapshot.get("dob", ""), y)

    if cert_type == "transfer_certificate":
        y = draw_row("9. Date of Admission", student_snapshot.get("admission_date", ""), y)
        y = draw_row("10. Date of Leaving", student_snapshot.get("leaving_date", student_snapshot.get("issue_date", "")), y)
        y = draw_row("11. Reason for Leaving", student_snapshot.get("reason", "On Parent's Request"), y)
        y = draw_row("12. Conduct and Character", student_snapshot.get("conduct", "Good"), y)
        y = draw_row("13. School Dues Status", student_snapshot.get("dues_cleared", "Cleared"), y)
    elif cert_type == "bonafide_certificate":
        y = draw_row("9. Academic Session", student_snapshot.get("session_code", ""), y)
        y = draw_row("10. Purpose of Certificate", student_snapshot.get("purpose", "General Verification"), y)
        y = draw_row("11. Conduct and Character", student_snapshot.get("conduct", "Good"), y)
    elif cert_type == "character_certificate":
        y = draw_row("9. Period of Study", f"{student_snapshot.get('admission_date', '')} to {student_snapshot.get('issue_date', '')}", y)
        y = draw_row("10. General Conduct", student_snapshot.get("conduct", "Exemplary and Good"), y)
        y = draw_row("11. Remarks", student_snapshot.get("remarks", "Bearing moral character and conduct."), y)

    # Certification declaration text
    y -= 6 * mm
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#334155"))
    declaration = config.get("body_template") or config.get("declaration_text") or (
        "This is to certify that the particulars furnished above have been verified from the official "
        "records and registers maintained by the institution."
    )
    # Wrap text if long
    c.drawCentredString(page_w / 2.0, y, declaration[:95])

    # Signatories at bottom
    sig_y = margin + 18 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#0F172A"))

    # Left: Class Teacher / Prepared by
    c.drawString(margin + 15 * mm, sig_y + 12 * mm, "Prepared & Verified By")
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(0.5)
    c.line(margin + 15 * mm, sig_y + 10 * mm, margin + 55 * mm, sig_y + 10 * mm)

    # Center: School Seal
    if config.get("show_seal", True):
        c.drawCentredString(page_w / 2.0, sig_y + 12 * mm, "School Seal / Stamp")
        c.roundRect(page_w / 2.0 - 15 * mm, sig_y - 2 * mm, 30 * mm, 16 * mm, radius=2 * mm, fill=0, stroke=1)

    # Right: Principal / Head of Institution
    signatory_title = config.get("signatory_title") or "Principal / Head of Institution"
    signatory_name = config.get("signatory_name")
    if signatory_name:
        c.drawRightString(page_w - margin - 15 * mm, sig_y + 16 * mm, signatory_name)
    c.drawRightString(page_w - margin - 15 * mm, sig_y + 12 * mm, signatory_title)
    c.line(page_w - margin - 60 * mm, sig_y + 10 * mm, page_w - margin - 15 * mm, sig_y + 10 * mm)

    c.restoreState()
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
