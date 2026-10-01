"""Student ID Card PDF generator.

Generates single CR80 cards and bulk 8-up A4 printable sheets.
Canonical Enrollment ID (ENR-{enrolments.id}) is printed and encoded into the QR code.
Strictly excludes Admission Number, blood group, emergency contact phone, or PII from the QR payload.
"""

from io import BytesIO
import qrcode
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.models import Enrolment, School, Student


CR80_WIDTH = 85.6 * mm  # ~242.6 points
CR80_HEIGHT = 54.0 * mm  # ~153.1 points


def _generate_qr_reader(payload: str) -> ImageReader:
    """Generate in-memory QR code for ReportLab canvas."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _draw_id_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    school: School,
    student: Student,
    enrolment: Enrolment,
    session_code: str,
) -> None:
    """Draw a single CR80 ID card at (x, y) coordinates."""
    c.saveState()

    # Outer border / card outline
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(0.75)
    c.setFillColor(colors.white)
    c.roundRect(x, y, CR80_WIDTH, CR80_HEIGHT, radius=3 * mm, fill=1, stroke=1)

    # Header bar
    header_color = colors.HexColor(school.primary_color or "#5B4BE0")
    c.setFillColor(header_color)
    # Clip top rounded corners or draw rectangle
    c.rect(x + 0.5, y + CR80_HEIGHT - 13 * mm, CR80_WIDTH - 1, 12.5 * mm, fill=1, stroke=0)

    # School Name in header
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    school_name = (school.name or "Sunrise Public School").upper()
    c.drawCentredString(x + CR80_WIDTH / 2.0, y + CR80_HEIGHT - 6 * mm, school_name[:38])

    # Card Subtitle
    c.setFont("Helvetica-Bold", 5.5)
    c.setFillColor(colors.HexColor("#E0E7FF"))
    c.drawCentredString(x + CR80_WIDTH / 2.0, y + CR80_HEIGHT - 10 * mm, "STUDENT IDENTITY CARD")

    # Photo Box on left
    photo_w = 20 * mm
    photo_h = 24 * mm
    photo_x = x + 4 * mm
    photo_y = y + CR80_HEIGHT - 15 * mm - photo_h

    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(0.5)
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=1, stroke=1)

    # Photo placeholder silhouette or text
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica", 6)
    c.drawCentredString(photo_x + photo_w / 2.0, photo_y + photo_h / 2.0, "PHOTO")

    # Student Details on the right of photo
    text_x = photo_x + photo_w + 3.5 * mm
    text_y = y + CR80_HEIGHT - 16 * mm

    # Student Name
    student_name = student.user.full_name if student.user else "Student"
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(text_x, text_y, student_name[:26])

    # Enrollment ID (prominent & canonical)
    enr_id_str = f"ENR-{enrolment.id}"
    text_y -= 4.2 * mm
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(header_color)
    c.drawString(text_x, text_y, f"ID: {enr_id_str}")

    # Class & Section
    class_label = enrolment.class_section.label if enrolment.class_section else "N/A"
    text_y -= 3.8 * mm
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(text_x, text_y, f"Class: {class_label}")

    # Roll Number
    text_y -= 3.5 * mm
    c.drawString(text_x, text_y, f"Roll No: {enrolment.roll_no}")

    # Academic Session
    text_y -= 3.5 * mm
    c.drawString(text_x, text_y, f"Session: {session_code}")

    # QR Code at bottom-right (encodes canonical Enrollment ID ONLY)
    qr_size = 14 * mm
    qr_x = x + CR80_WIDTH - qr_size - 4 * mm
    qr_y = y + 4 * mm
    qr_reader = _generate_qr_reader(enr_id_str)
    c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)

    # Valid Until / Signatory footer on bottom-left
    c.setFont("Helvetica", 5)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawString(photo_x, y + 6.5 * mm, "Authorized Signatory")
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(0.5)
    c.line(photo_x, y + 6 * mm, photo_x + 22 * mm, y + 6 * mm)

    c.drawString(photo_x, y + 3 * mm, f"Valid Session: {session_code}")

    c.restoreState()


def generate_single_id_card(
    school: School,
    student: Student,
    enrolment: Enrolment,
    session_code: str,
) -> bytes:
    """Generate a single CR80 student ID card PDF."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(CR80_WIDTH, CR80_HEIGHT))
    _draw_id_card(c, 0, 0, school, student, enrolment, session_code)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def generate_bulk_id_cards(
    school: School,
    items: list[tuple[Student, Enrolment, str]],
) -> bytes:
    """Generate 8-up A4 sheet(s) of student ID cards with cut guidelines.

    2 columns x 4 rows per A4 page.
    A4 dimensions: 210mm x 297mm (595.27 pt x 841.89 pt).
    """
    buf = BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    margin_x = (page_w - (2 * CR80_WIDTH + 8 * mm)) / 2.0
    margin_y = (page_h - (4 * CR80_HEIGHT + 12 * mm)) / 2.0

    cards_per_page = 8
    col_gap = 8 * mm
    row_gap = 4 * mm

    for idx, (student, enrolment, session_code) in enumerate(items):
        page_idx = idx % cards_per_page
        if idx > 0 and page_idx == 0:
            c.showPage()

        col = page_idx % 2
        row = page_idx // 2  # 0 at top, 3 at bottom

        card_x = margin_x + col * (CR80_WIDTH + col_gap)
        # In PDF coordinates, (0,0) is bottom-left, so top row has largest y
        card_y = margin_y + (3 - row) * (CR80_HEIGHT + row_gap)

        _draw_id_card(c, card_x, card_y, school, student, enrolment, session_code)

        # Draw light cut guidelines
        c.saveState()
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.25)
        # Corner tick marks around card
        c.line(card_x - 2 * mm, card_y, card_x - 0.5 * mm, card_y)
        c.line(card_x, card_y - 2 * mm, card_x, card_y - 0.5 * mm)
        c.line(card_x + CR80_WIDTH + 0.5 * mm, card_y, card_x + CR80_WIDTH + 2 * mm, card_y)
        c.line(card_x + CR80_WIDTH, card_y - 2 * mm, card_x + CR80_WIDTH, card_y - 0.5 * mm)
        c.restoreState()

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
