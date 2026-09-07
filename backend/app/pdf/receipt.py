"""Fee receipt PDF, generated on demand from invoice + payment + school settings."""

from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Enrolment,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    PaymentAllocation,
    School,
    Student,
)

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


def build_receipt(db: Session, payment_id: int) -> bytes:
    """A receipt for one payment, showing which months it settled.

    Payment-shaped rather than invoice-shaped because that is what the ledger
    is: one payment can clear September and part of October, and a receipt that
    could only name one invoice was why v0 could not take a part payment.
    """
    payment = db.get(FeePayment, payment_id)
    enrolment = db.get(Enrolment, payment.enrolment_id)
    student = db.get(Student, enrolment.student_id)
    # The receipt belongs to the payment's school, not to a global row.
    school = db.get(School, payment.school_id)
    class_label = enrolment.class_section.label

    settled = db.execute(
        select(FeeInvoice.period_month, FeeInvoice.period_year, func.sum(PaymentAllocation.amount))
        .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
        .join(PaymentAllocation, PaymentAllocation.invoice_line_id == FeeInvoiceLine.id)
        .where(PaymentAllocation.payment_id == payment.id)
        .group_by(FeeInvoice.period_year, FeeInvoice.period_month)
        .order_by(FeeInvoice.period_year, FeeInvoice.period_month)
    ).all()
    allocated = sum((Decimal(a) for _, _, a in settled), Decimal(0))
    credit = payment.amount - allocated

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm, title=payment.receipt_no,
    )
    styles = getSampleStyleSheet()
    head = styles["Title"]
    head.textColor = colors.HexColor(school.primary_color or "#5B4BE0")

    applied = ", ".join(f"{MONTHS[m - 1]} {y}" for m, y, _ in settled) or "Advance"
    rows = [
        ["Receipt No.", payment.receipt_no],
        ["Date", f"{payment.received_at:%d %b %Y}"],
        ["Student", student.user.full_name],
        ["Admission No.", student.admission_no],
        ["Class", class_label],
        ["Applied To", applied],
        ["Amount", f"Rs. {payment.amount:,.2f}"],
        ["Amount in words", amount_in_words(payment.amount)],
        ["Payment Mode", payment.method.title()],
    ]
    if payment.instrument_ref:
        rows.append(["Instrument Ref.", payment.instrument_ref])
    if credit > 0:
        # Shown rather than silently held: a parent who paid ahead should see
        # the balance on the receipt, not discover it next month.
        rows.append(["Credit Carried", f"Rs. {credit:,.2f}"])
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
    title = "FEE RECEIPT" if payment.amount > 0 else "PAYMENT REVERSAL"
    doc.build(
        [
            Paragraph(school.name, head),
            Paragraph(address, styles["Normal"]),
            Spacer(1, 8 * mm),
            Paragraph(f"<b>{title}</b>", styles["Heading2"]),
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
