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
    AuditAction,
    InvoiceStatus,
    Student,
)
from app.services import audit
from app.services.common import class_label_map, enrolment_sections
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


def presented_status(invoice: FeeInvoice, today: Date | None = None) -> InvoiceStatus:
    """How an invoice reads right now, without writing anything.

    v0 persisted pending -> overdue from inside `to_out()`, so a GET wrote and
    committed. Reads do not have side effects here; the stored status is moved
    by the scheduled `fees.overdue_sweep` job instead (ERP_BLUEPRINT §2.5(7)).
    """
    today = today or Date.today()
    if invoice.status == InvoiceStatus.pending and invoice.due_date < today:
        return InvoiceStatus.overdue
    return invoice.status


def to_out(db: Session, invoices: list[FeeInvoice]) -> list[InvoiceOut]:
    pays = _payments(db, [i.id for i in invoices])
    students = {
        s.id: s
        for s in db.scalars(select(Student).where(Student.id.in_([i.student_id for i in invoices] or [0])))
    }
    labels = class_label_map(db, list(students))
    return [
        InvoiceOut(
            id=i.id,
            student_id=i.student_id,
            student_name=students[i.student_id].user.full_name,
            admission_no=students[i.student_id].admission_no,
            class_label=labels.get(i.student_id, ""),
            month=i.month,
            year=i.year,
            amount=i.amount,
            due_date=i.due_date,
            status=presented_status(i),
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
    sections = enrolment_sections(
        db,
        [
            sid
            for sid in db.scalars(
                select(Student.id).where(Student.school_id == school_id)
            )
        ],
    )
    for s in db.scalars(select(Student).where(Student.school_id == school_id)):
        if not s.user.is_active:
            continue
        if s.id in existing:  # idempotent: rely on the unique key, skip existing
            skipped += 1
            continue
        amount = structures.get(labels.get(sections.get(s.id, 0), ""))
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
    """Gapless per school, per financial year.

    v0 computed max(seq) + 1 in Python with no lock: two concurrent payments
    raced, and the unique constraint turned the loser into a 500 rather than a
    retry. Receipt numbers are also what an auditor checks for gaps.
    """
    return audit.next_number(
        db, school_id, kind="receipt", year=year, prefix=f"SPS/RCP/{year}/", width=6
    )


def pay(db: Session, invoice_id: int, actor=None) -> PaymentResult:
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
    audit.record(
        db,
        actor=actor,
        school_id=invoice.school_id,
        entity_type="fee_payment",
        entity_id=invoice.id,
        action=AuditAction.create,
        after={
            "receipt_no": payment.receipt_no,
            "amount": str(payment.amount),
            "method": payment.method,
        },
    )
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
