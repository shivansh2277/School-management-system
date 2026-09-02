"""Fee receipt PDF, generated on demand from invoice + payment + school settings."""

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FeeInvoice, FeePayment, SchoolSettings, Student

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
    "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _under_hundred(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (f" {_ONES[ones]}" if ones else "")


def amount_in_words(amount: Decimal) -> str:
    """Indian numbering: crore / lakh / thousand / hundred."""
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    if rupees == 0:
        words = "Zero"
    else:
        parts = []
        for divisor, name in ((10_000_000, "Crore"), (100_000, "Lakh"), (1_000, "Thousand")):
            chunk, rupees = divmod(rupees, divisor)
            if chunk:
                parts.append(f"{_under_hundred(chunk)} {name}")
        hundreds, rest = divmod(rupees, 100)
        if hundreds:
            parts.append(f"{_ONES[hundreds]} Hundred")
        if rest:
            parts.append(_under_hundred(rest))
        words = " ".join(parts)
    out = f"Rupees {words}"
    if paise:
        out += f" and {_under_hundred(paise)} Paise"
    return out + " Only"


def build_receipt(db: Session, invoice_id: int) -> bytes:
    invoice = db.get(FeeInvoice, invoice_id)
    payment = db.scalar(select(FeePayment).where(FeePayment.invoice_id == invoice_id))
    student = db.get(Student, invoice.student_id)
    school = db.get(SchoolSettings, 1)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm, title=payment.receipt_no,
    )
    styles = getSampleStyleSheet()
    head = styles["Title"]
    head.textColor = colors.HexColor(school.primary_color or "#5B4BE0")

    rows = [
        ["Receipt No.", payment.receipt_no],
        ["Date", f"{payment.paid_at:%d %b %Y}"],
        ["Student", student.user.full_name],
        ["Admission No.", student.admission_no],
        ["Class", student.class_section.label],
        ["Billing Month", f"{MONTHS[invoice.month - 1]} {invoice.year}"],
        ["Amount", f"Rs. {invoice.amount:,.2f}"],
        ["Amount in words", amount_in_words(invoice.amount)],
        ["Payment Mode", payment.method.title()],
        ["Transaction Ref.", payment.txn_ref],
    ]
    table = Table(rows, colWidths=[45 * mm, 105 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E4E7EF")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEEBFC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    address = ", ".join(x for x in [school.address, school.city] if x)
    doc.build(
        [
            Paragraph(school.name, head),
            Paragraph(address, styles["Normal"]),
            Spacer(1, 8 * mm),
            Paragraph("<b>FEE RECEIPT</b>", styles["Heading2"]),
            Spacer(1, 4 * mm),
            table,
            Spacer(1, 10 * mm),
            Paragraph(
                "<font size=8 color='#8A93A6'>This is a system generated receipt "
                "and does not require a signature.</font>",
                styles["Normal"],
            ),
        ]
    )
    return buf.getvalue()
