import calendar
import uuid
from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ClassSection,
    FeeInvoice,
    FeePayment,
    FeeStructure,
    InvoiceStatus,
    Student,
)
from app.schemas.common import (
    CollectionMonth,
    CollectionSummary,
    GenerateInvoicesResult,
    InvoiceOut,
    PaymentResult,
)


def _payments(db: Session, invoice_ids: list[int]) -> dict[int, FeePayment]:
    if not invoice_ids:
        return {}
    return {
        p.invoice_id: p
        for p in db.scalars(select(FeePayment).where(FeePayment.invoice_id.in_(invoice_ids)))
    }


def refresh_overdue(db: Session, invoices: list[FeeInvoice]) -> None:
    """Persist pending -> overdue once the due date has passed (BLUEPRINT §8 Fees)."""
    today = Date.today()
    changed = False
    for inv in invoices:
        if inv.status == InvoiceStatus.pending and inv.due_date < today:
            inv.status = InvoiceStatus.overdue
            changed = True
    if changed:
        db.commit()


def to_out(db: Session, invoices: list[FeeInvoice]) -> list[InvoiceOut]:
    refresh_overdue(db, invoices)
    pays = _payments(db, [i.id for i in invoices])
    students = {
        s.id: s
        for s in db.scalars(select(Student).where(Student.id.in_([i.student_id for i in invoices] or [0])))
    }
    return [
        InvoiceOut(
            id=i.id,
            student_id=i.student_id,
            student_name=students[i.student_id].user.full_name,
            admission_no=students[i.student_id].admission_no,
            class_label=students[i.student_id].class_section.label,
            month=i.month,
            year=i.year,
            amount=i.amount,
            due_date=i.due_date,
            status=i.status,
            receipt_no=pays[i.id].receipt_no if i.id in pays else None,
            paid_at=pays[i.id].paid_at if i.id in pays else None,
        )
        for i in invoices
    ]


def generate(
    db: Session, month: int, year: int, school_id: int
) -> GenerateInvoicesResult:
    if not 1 <= month <= 12:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be 1-12")
    structures = {
        f.class_name: f.monthly_amount
        for f in db.scalars(
            select(FeeStructure).where(FeeStructure.school_id == school_id)
        )
    }
    labels = {
        c.id: c.class_name
        for c in db.scalars(
            select(ClassSection).where(ClassSection.school_id == school_id)
        )
    }
    existing = set(
        db.scalars(
            select(FeeInvoice.student_id).where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.month == month,
                FeeInvoice.year == year,
            )
        )
    )
    due = Date(year, month, min(10, calendar.monthrange(year, month)[1]))
    created = skipped = 0
    for s in db.scalars(select(Student).where(Student.school_id == school_id)):
        if not s.user.is_active:
            continue
        if s.id in existing:  # idempotent: rely on the unique key, skip existing
            skipped += 1
            continue
        amount = structures.get(labels.get(s.class_section_id, ""))
        if amount is None:
            skipped += 1
            continue
        db.add(
            FeeInvoice(
                school_id=school_id,
                student_id=s.id,
                month=month,
                year=year,
                amount=amount,
                due_date=due,
                status=InvoiceStatus.overdue if due < Date.today() else InvoiceStatus.pending,
            )
        )
        created += 1
    db.commit()
    return GenerateInvoicesResult(created=created, skipped=skipped)


def _next_receipt_no(db: Session, year: int, school_id: int) -> str:
    prefix = f"SPS/RCP/{year}/"
    used = db.scalars(
        select(FeePayment.receipt_no).where(
            FeePayment.school_id == school_id,
            FeePayment.receipt_no.like(f"{prefix}%"),
        )
    ).all()
    seq = max((int(r.rsplit("/", 1)[1]) for r in used), default=0) + 1
    return f"{prefix}{seq:06d}"


def pay(db: Session, invoice_id: int) -> PaymentResult:
    invoice = db.get(FeeInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    if invoice.status == InvoiceStatus.paid:
        raise HTTPException(status.HTTP_409_CONFLICT, "This invoice is already paid")
    now = datetime.now(UTC)
    payment = FeePayment(
        school_id=invoice.school_id,
        invoice_id=invoice.id,
        amount=invoice.amount,
        paid_at=now,
        method="simulated",
        txn_ref=f"SIM-{uuid.uuid4().hex[:12].upper()}",
        receipt_no=_next_receipt_no(db, now.year, invoice.school_id),
    )
    db.add(payment)
    invoice.status = InvoiceStatus.paid
    db.commit()
    return PaymentResult(
        invoice_id=invoice.id,
        receipt_no=payment.receipt_no,
        txn_ref=payment.txn_ref,
        amount=payment.amount,
        paid_at=payment.paid_at,
    )


def collection(db: Session, year: int) -> CollectionSummary:
    billed_rows = db.execute(
        select(FeeInvoice.month, func.sum(FeeInvoice.amount))
        .where(FeeInvoice.year == year)
        .group_by(FeeInvoice.month)
    ).all()
    paid_rows = db.execute(
        select(FeeInvoice.month, func.sum(FeePayment.amount))
        .join(FeePayment, FeePayment.invoice_id == FeeInvoice.id)
        .where(FeeInvoice.year == year)
        .group_by(FeeInvoice.month)
    ).all()
    billed = {m: Decimal(v) for m, v in billed_rows}
    collected = {m: Decimal(v) for m, v in paid_rows}
    months = [
        CollectionMonth(month=m, billed=billed[m], collected=collected.get(m, Decimal(0)))
        # only months that actually have invoices — no fabricated zero bars (§8)
        for m in sorted(billed)
    ]
    total_billed = sum(billed.values(), Decimal(0))
    total_collected = sum(collected.values(), Decimal(0))
    return CollectionSummary(
        year=year,
        billed=total_billed,
        collected=total_collected,
        outstanding=total_billed - total_collected,
        months=months,
    )
