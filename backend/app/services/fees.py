"""Billing and collection.

Everything here obeys three rules from ERP_BLUEPRINT §3.9:

1. Payments allocate to invoice *lines*; an invoice balance is a SUM over
   allocations, never a stored column that could drift from them.
2. Nothing financial is edited. An invoice is voided and reissued; a payment is
   reversed by a contra entry that keeps both rows.
3. Reads never write. `presented_status()` says how an invoice reads today; the
   scheduled sweep is what moves the stored value.
"""

import calendar
import uuid
from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    FeeFrequency,
    FeeHead,
    FeeHeadType,
    Guardian,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeePaymentStatus,
    InvoiceStatus,
    PaymentAllocation,
    School,
    Student,
    StudentGuardian,
    User,
)
from app.services import audit, fee_setup, school_settings
from app.services.fee_setup import money

ZERO = Decimal("0.00")
# Statuses that no longer represent money anyone expects to receive.
DEAD = (InvoiceStatus.voided, InvoiceStatus.written_off)
# The late fee is an ordinary line against an ordinary head, so head-wise
# reporting, part payment and receipts all handle it without a special case.
LATE_FEE_CODE = "LATE"


# --- derived amounts --------------------------------------------------------


def allocated_by_line(db: Session, line_ids: list[int]) -> dict[int, Decimal]:
    """How much has been allocated to each line, reversals included.

    A reversal is a negative allocation, so summing is all that is needed —
    there is no "except the cancelled ones" clause to forget somewhere.
    """
    if not line_ids:
        return {}
    rows = db.execute(
        select(PaymentAllocation.invoice_line_id, func.sum(PaymentAllocation.amount))
        .where(PaymentAllocation.invoice_line_id.in_(line_ids))
        .group_by(PaymentAllocation.invoice_line_id)
    ).all()
    return {line_id: Decimal(total) for line_id, total in rows}


def totals(db: Session, invoice: FeeInvoice) -> dict:
    paid_by_line = allocated_by_line(db, [line.id for line in invoice.lines])
    charged = sum((line.amount for line in invoice.lines), ZERO)
    discount = sum((line.discount for line in invoice.lines), ZERO)
    paid = sum((paid_by_line.get(line.id, ZERO) for line in invoice.lines), ZERO)
    net = charged - discount
    return {
        "charged": money(charged),
        "discount": money(discount),
        "payable": money(net),
        "paid": money(paid),
        "balance": money(net - paid),
    }


def presented_status(invoice: FeeInvoice, balance: Decimal, today: Date | None = None) -> InvoiceStatus:
    """How an invoice reads right now, without writing anything.

    v0 persisted pending -> overdue from inside `to_out()`, so a GET wrote and
    committed. The stored status is moved by `fees.overdue_sweep` instead.
    """
    if invoice.status in DEAD:
        return invoice.status
    today = today or Date.today()
    if balance <= ZERO:
        return InvoiceStatus.paid
    if invoice.due_date < today:
        return InvoiceStatus.overdue
    if balance < totals_payable(invoice):
        return InvoiceStatus.partially_paid
    return invoice.status


def totals_payable(invoice: FeeInvoice) -> Decimal:
    return money(sum((line.net for line in invoice.lines), ZERO))


def _restate(db: Session, invoice: FeeInvoice, on: Date) -> None:
    """Move an invoice's stored status to match its allocations.

    Called only from write paths — collection, reversal, the sweep. Whoever
    changed the money is the one who owes the status update.
    """
    balance = totals(db, invoice)["balance"]
    if invoice.status in DEAD:
        return
    if balance <= ZERO:
        invoice.status = InvoiceStatus.paid
        invoice.settled_on = invoice.settled_on or on
    else:
        invoice.settled_on = None
        paid_anything = balance < totals_payable(invoice)
        if invoice.due_date < on:
            invoice.status = InvoiceStatus.overdue
        elif paid_anything:
            invoice.status = InvoiceStatus.partially_paid
        else:
            invoice.status = InvoiceStatus.issued


# --- the late fee (§0.6, and §8 item C answered 7 September 2026) -----------


def late_fee_rules(db: Session, school_id: int) -> dict:
    """The four numbers behind the rule, per school (§3.15)."""
    return {
        key: int(school_settings.get(db, school_id, f"fees.late_fee.{key}"))
        for key in ("grace_days", "initial", "per_day", "cap_percent")
    }


def late_fee_due(payable: Decimal, due_date: Date, on: Date, rules: dict) -> Decimal:
    """₹300 once 5 days overdue, then +₹100 per further day, capped at 50%.

    A pure function of the due date, the amount and one other date — no reading
    of when a job last ran. That is what makes the fine defensible at the
    counter: it can be recomputed in front of the parent.

    The clock runs until the invoice is *paid*, not until the next invoice is
    generated (the product owner's answer to §8 item C, 7 September 2026). So
    the caller passes `settled_on` for a settled invoice and today for a live
    one, and nothing else changes the answer.
    """
    days_overdue = (on - due_date).days
    if days_overdue < rules["grace_days"]:
        return ZERO
    fee = Decimal(rules["initial"]) + Decimal(rules["per_day"]) * (
        days_overdue - rules["grace_days"]
    )
    cap = payable * Decimal(rules["cap_percent"]) / 100
    return money(min(fee, cap))


def late_fee_head(db: Session, school_id: int) -> FeeHead:
    head = db.scalar(
        select(FeeHead).where(
            FeeHead.school_id == school_id, FeeHead.code == LATE_FEE_CODE
        )
    )
    if head is None:
        head = FeeHead(
            school_id=school_id,
            name="Late Fee",
            code=LATE_FEE_CODE,
            type=FeeHeadType.one_time,
        )
        db.add(head)
        db.flush()
    return head


def assess_late_fee(db: Session, invoice: FeeInvoice, on: Date | None = None) -> Decimal:
    """Bring an invoice's late-fee line up to date. A write path, never a read.

    Called by the daily sweep and again at the counter before money is taken,
    so what a parent is asked for is the fine as of today rather than as of
    whenever the job last ran.
    """
    on = on or Date.today()
    if invoice.status in DEAD:
        return ZERO
    head = late_fee_head(db, invoice.school_id)
    existing = next((line for line in invoice.lines if line.fee_head_id == head.id), None)
    if invoice.settled_on is not None:
        # Paid. The clock stopped on the day the balance reached zero.
        return existing.amount if existing else ZERO

    base = money(
        sum((line.net for line in invoice.lines if line.fee_head_id != head.id), ZERO)
    )
    fee = late_fee_due(base, invoice.due_date, on, late_fee_rules(db, invoice.school_id))
    if fee <= ZERO:
        return ZERO
    if existing is None:
        db.add(
            FeeInvoiceLine(
                school_id=invoice.school_id,
                invoice_id=invoice.id,
                fee_head_id=head.id,
                description=f"Late fee ({(on - invoice.due_date).days} days overdue)",
                amount=fee,
            )
        )
    elif fee > existing.amount:
        # Only ever upward. Lowering the rule must not refund a fine already
        # charged — that is a waiver, which is a concession and needs approval.
        existing.amount = fee
        existing.description = f"Late fee ({(on - invoice.due_date).days} days overdue)"
    else:
        return existing.amount
    db.flush()
    db.refresh(invoice)
    _restate(db, invoice, on)
    return fee


# --- billing ----------------------------------------------------------------


def _school_code(db: Session, school_id: int) -> str:
    school = db.get(School, school_id)
    return school.code if school else "SCH"


def outstanding_invoices(db: Session, enrolment_id: int) -> list[FeeInvoice]:
    """Unsettled invoices, oldest first — the order money is applied in."""
    invoices = db.scalars(
        select(FeeInvoice)
        .where(
            FeeInvoice.enrolment_id == enrolment_id,
            FeeInvoice.status.not_in(DEAD),
        )
        .order_by(FeeInvoice.due_date, FeeInvoice.id)
    ).all()
    return [i for i in invoices if totals(db, i)["balance"] > ZERO]


def generate(db: Session, month: int, year: int, school_id: int, actor: User | None = None) -> dict:
    """Bill one month for a whole school.

    Idempotent through the partial unique index on (enrolment, period): a
    second run creates nothing and reports what it skipped, which is what makes
    it safe to retry a half-finished batch job.
    """
    if not 1 <= month <= 12:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be 1-12")

    due_day = int(school_settings.get(db, school_id, "fees.due_day"))
    due = Date(year, month, min(due_day, calendar.monthrange(year, month)[1]))
    issued_on = Date(year, month, 1)

    enrolments = db.scalars(
        select(Enrolment).where(
            Enrolment.school_id == school_id,
            Enrolment.status == EnrolmentStatus.active,
        )
    ).all()
    already = set(
        db.scalars(
            select(FeeInvoice.enrolment_id).where(
                FeeInvoice.school_id == school_id,
                FeeInvoice.period_month == month,
                FeeInvoice.period_year == year,
                FeeInvoice.status.not_in((InvoiceStatus.voided,)),
            )
        )
    )
    concessions = fee_setup.concessions_for(db, [e.id for e in enrolments], due)

    created = skipped = 0
    billed = ZERO
    prefix = f"{_school_code(db, school_id)}/INV/{year}/"
    for enrolment in enrolments:
        if enrolment.id in already:
            skipped += 1
            continue
        plan = fee_setup.plan_for(db, enrolment)
        if plan is None:  # no plan is not an error: a class may not be billed
            skipped += 1
            continue
        items = [i for i in plan.items if i.frequency is FeeFrequency.monthly]
        if not items:
            skipped += 1
            continue

        invoice = FeeInvoice(
            school_id=school_id,
            enrolment_id=enrolment.id,
            academic_year_id=enrolment.academic_year_id,
            invoice_no=audit.next_number(
                db, school_id, kind="invoice", year=year, prefix=prefix, width=6
            ),
            period_month=month,
            period_year=year,
            issued_on=issued_on,
            due_date=due,
            status=InvoiceStatus.overdue if due < Date.today() else InvoiceStatus.issued,
            lines=[
                FeeInvoiceLine(
                    school_id=school_id,
                    fee_head_id=item.fee_head_id,
                    description=item.head.name,
                    amount=item.amount,
                    # Snapshotted, not recomputed: an invoice already shown to a
                    # parent must not change when a concession is edited later.
                    discount=fee_setup.discount_on(
                        item.amount, item.fee_head_id, concessions.get(enrolment.id, [])
                    ),
                )
                for item in items
            ],
        )
        db.add(invoice)
        created += 1
        billed += totals_payable(invoice)

    db.flush()
    # Anyone who paid in advance has that money applied to what was just
    # billed, rather than sitting as a credit next to a fresh due invoice.
    for enrolment in enrolments:
        settle_from_credit(db, enrolment.id)
    if actor is not None:
        audit.record(
            db,
            actor=actor,
            school_id=school_id,
            entity_type="fee_invoice_run",
            action=AuditAction.create,
            after={"month": month, "year": year, "created": created},
        )
    db.commit()
    return {"created": created, "skipped": skipped, "billed": money(billed)}


def void(db: Session, invoice: FeeInvoice, reason: str, actor: User) -> FeeInvoice:
    """A wrong invoice is cancelled and reissued, never edited (§3.9 rule 3)."""
    if invoice.status in DEAD:
        raise HTTPException(status.HTTP_409_CONFLICT, "This invoice is already closed")
    if totals(db, invoice)["paid"] > ZERO:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Money has been received against this invoice; reverse the payment first",
        )
    before = invoice.status.value
    invoice.status = InvoiceStatus.voided
    invoice.void_reason = reason
    audit.record(
        db,
        actor=actor,
        school_id=invoice.school_id,
        entity_type="fee_invoice",
        entity_id=invoice.id,
        action=AuditAction.void,
        before={"status": before},
        after={"status": invoice.status.value},
        reason=reason,
    )
    db.commit()
    return invoice


# --- collection -------------------------------------------------------------


def _allocate(db: Session, payment: FeePayment, available: Decimal, on: Date) -> Decimal:
    """Spend `available` against this enrolment's outstanding lines, oldest
    invoice first. Returns what is left over — the credit balance."""
    for invoice in outstanding_invoices(db, payment.enrolment_id):
        paid_by_line = allocated_by_line(db, [line.id for line in invoice.lines])
        for line in invoice.lines:
            if available <= ZERO:
                break
            owing = line.net - paid_by_line.get(line.id, ZERO)
            if owing <= ZERO:
                continue
            part = min(available, owing)
            db.add(
                PaymentAllocation(
                    school_id=payment.school_id,
                    payment_id=payment.id,
                    invoice_line_id=line.id,
                    amount=part,
                )
            )
            available -= part
        db.flush()
        _restate(db, invoice, on)
        if available <= ZERO:
            break
    return available


def credit_balance(db: Session, enrolment_id: int) -> Decimal:
    """Money received that no line has claimed — an advance, or a parent
    rounding up. §5.5.9 says over-payment becomes a credit, not an error."""
    received = db.scalar(
        select(func.coalesce(func.sum(FeePayment.amount), 0)).where(
            FeePayment.enrolment_id == enrolment_id
        )
    )
    spent = db.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
        .join(FeePayment, FeePayment.id == PaymentAllocation.payment_id)
        .where(FeePayment.enrolment_id == enrolment_id)
    )
    return money(Decimal(received) - Decimal(spent))


def _unspent(db: Session, enrolment_id: int) -> list[tuple[FeePayment, Decimal]]:
    """Payments with money still unallocated, oldest first.

    Per payment rather than one pooled figure: an allocation names the payment
    it came from, and a receipt that funded nothing it can point at is not a
    ledger, it is a plausible total.
    """
    payments = db.scalars(
        select(FeePayment)
        .where(
            FeePayment.enrolment_id == enrolment_id,
            FeePayment.status == FeePaymentStatus.success,
            FeePayment.amount > 0,
        )
        .order_by(FeePayment.received_at, FeePayment.id)
    ).all()
    out = []
    for payment in payments:
        spent = sum((a.amount for a in payment.allocations), ZERO)
        if payment.amount - spent > ZERO:
            out.append((payment, payment.amount - spent))
    return out


def settle_from_credit(db: Session, enrolment_id: int, on: Date | None = None) -> Decimal:
    """Apply any credit balance to outstanding invoices. Run after billing, so
    an advance paid in March settles April the moment April is raised."""
    on = on or Date.today()
    applied = ZERO
    for payment, spare in _unspent(db, enrolment_id):
        left = _allocate(db, payment, spare, on)
        applied += spare - left
    db.flush()
    return money(applied)


def collect(
    db: Session,
    enrolment_id: int,
    amount: Decimal,
    *,
    idempotency_key: str,
    method: str = "cash",
    instrument_ref: str | None = None,
    actor: User | None = None,
    received_at: datetime | None = None,
) -> FeePayment:
    """Take money at the counter and allocate it, oldest invoice first.

    The idempotency key is required, not optional: a retried request must
    return the original receipt rather than take the money a second time
    (§3.9 rule 4). It is the whole reason a duplicate tap at the counter is a
    non-event.
    """
    enrolment = db.get(Enrolment, enrolment_id)
    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
    if amount <= ZERO:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Amount must be positive")

    existing = db.scalar(
        select(FeePayment).where(
            FeePayment.school_id == enrolment.school_id,
            FeePayment.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing

    now = received_at or datetime.now(UTC)
    payment = FeePayment(
        school_id=enrolment.school_id,
        enrolment_id=enrolment.id,
        receipt_no=audit.next_number(
            db,
            enrolment.school_id,
            kind="receipt",
            year=now.year,
            prefix=f"{_school_code(db, enrolment.school_id)}/RCP/{now.year}/",
            width=6,
        ),
        amount=money(amount),
        method=method,
        instrument_ref=instrument_ref,
        received_at=now,
        received_by=actor.id if actor else None,
        idempotency_key=idempotency_key,
        status=FeePaymentStatus.success,
    )
    db.add(payment)
    db.flush()
    # Bring every outstanding fine up to date before the money lands: what is
    # collected must be what is owed today, not what the last sweep stored.
    today = Date.today()
    for invoice in outstanding_invoices(db, enrolment.id):
        assess_late_fee(db, invoice, today)
    _allocate(db, payment, payment.amount, today)
    audit.record(
        db,
        actor=actor,
        school_id=payment.school_id,
        entity_type="fee_payment",
        entity_id=payment.id,
        action=AuditAction.create,
        after={
            "receipt_no": payment.receipt_no,
            "amount": str(payment.amount),
            "method": payment.method,
        },
    )
    db.commit()
    return payment


def reverse(db: Session, payment: FeePayment, reason: str, actor: User) -> FeePayment:
    """Cancel a payment with a contra entry (§3.9 rule 3).

    Both rows stay and both keep their receipt numbers, because a gap in the
    receipt sequence is exactly what an auditor asks about. A cashier may not
    do this — §5.5.9 keeps taking money and cancelling it in different hands.
    """
    if payment.status is FeePaymentStatus.reversed:
        raise HTTPException(status.HTTP_409_CONFLICT, "This payment is already reversed")
    if payment.amount < ZERO:
        raise HTTPException(status.HTTP_409_CONFLICT, "A reversal cannot itself be reversed")

    now = datetime.now(UTC)
    contra = FeePayment(
        school_id=payment.school_id,
        enrolment_id=payment.enrolment_id,
        receipt_no=audit.next_number(
            db,
            payment.school_id,
            kind="receipt",
            year=now.year,
            prefix=f"{_school_code(db, payment.school_id)}/RCP/{now.year}/",
            width=6,
        ),
        amount=-payment.amount,
        method=payment.method,
        instrument_ref=payment.instrument_ref,
        received_at=now,
        received_by=actor.id,
        idempotency_key=f"reversal-{payment.id}",
        status=FeePaymentStatus.success,
        reverses_payment_id=payment.id,
        reason=reason,
    )
    db.add(contra)
    db.flush()
    touched = set()
    for allocation in payment.allocations:
        db.add(
            PaymentAllocation(
                school_id=payment.school_id,
                payment_id=contra.id,
                invoice_line_id=allocation.invoice_line_id,
                amount=-allocation.amount,
            )
        )
        touched.add(db.get(FeeInvoiceLine, allocation.invoice_line_id).invoice_id)
    payment.status = FeePaymentStatus.reversed
    db.flush()
    for invoice_id in touched:
        _restate(db, db.get(FeeInvoice, invoice_id), now.date())
    audit.record(
        db,
        actor=actor,
        school_id=payment.school_id,
        entity_type="fee_payment",
        entity_id=payment.id,
        action=AuditAction.void,
        before={"status": FeePaymentStatus.success.value},
        after={"status": payment.status.value, "contra_receipt_no": contra.receipt_no},
        reason=reason,
    )
    db.commit()
    return contra


# --- views ------------------------------------------------------------------


def invoice_out(db: Session, invoice: FeeInvoice, today: Date | None = None) -> dict:
    amounts = totals(db, invoice)
    student = invoice.enrolment.student
    return {
        "id": invoice.id,
        "invoice_no": invoice.invoice_no,
        "enrolment_id": invoice.enrolment_id,
        "student_id": student.id,
        "student_name": student.user.full_name,
        "admission_no": student.admission_no,
        "class_label": invoice.enrolment.class_section.label,
        "month": invoice.period_month,
        "year": invoice.period_year,
        "due_date": invoice.due_date,
        "status": presented_status(invoice, amounts["balance"], today),
        "settled_on": invoice.settled_on,
        "lines": [
            {
                "id": line.id,
                "fee_head_id": line.fee_head_id,
                "description": line.description,
                "amount": line.amount,
                "discount": line.discount,
                "net": line.net,
            }
            for line in invoice.lines
        ],
        **amounts,
    }


def list_invoices(db: Session, invoices: list[FeeInvoice]) -> list[dict]:
    today = Date.today()
    return [invoice_out(db, i, today) for i in invoices]


def ledger(db: Session, enrolment_id: int) -> dict:
    """One student's fee account: every invoice, every receipt, one balance."""
    invoices = db.scalars(
        select(FeeInvoice)
        .where(FeeInvoice.enrolment_id == enrolment_id)
        .order_by(FeeInvoice.period_year.desc(), FeeInvoice.period_month.desc())
    ).all()
    payments = db.scalars(
        select(FeePayment)
        .where(FeePayment.enrolment_id == enrolment_id)
        .order_by(FeePayment.received_at.desc())
    ).all()
    rows = list_invoices(db, invoices)
    return {
        "invoices": rows,
        "payments": [
            {
                "id": p.id,
                "receipt_no": p.receipt_no,
                "amount": p.amount,
                "method": p.method,
                "received_at": p.received_at,
                "status": p.status,
                "reverses_payment_id": p.reverses_payment_id,
            }
            for p in payments
        ],
        "outstanding": money(
            sum((r["balance"] for r in rows if r["status"] not in DEAD), ZERO)
        ),
        "credit": credit_balance(db, enrolment_id),
    }


def collection(db: Session, year: int, school_id: int) -> dict:
    """Billed against collected, by month. Demand is net of concessions —
    a school cannot collect a discount it granted."""
    billed_rows = db.execute(
        select(
            FeeInvoice.period_month,
            func.sum(FeeInvoiceLine.amount - FeeInvoiceLine.discount),
        )
        .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
        .where(
            FeeInvoice.school_id == school_id,
            FeeInvoice.period_year == year,
            FeeInvoice.status.not_in(DEAD),
        )
        .group_by(FeeInvoice.period_month)
    ).all()
    paid_rows = db.execute(
        select(FeeInvoice.period_month, func.sum(PaymentAllocation.amount))
        .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
        .join(PaymentAllocation, PaymentAllocation.invoice_line_id == FeeInvoiceLine.id)
        .where(FeeInvoice.school_id == school_id, FeeInvoice.period_year == year)
        .group_by(FeeInvoice.period_month)
    ).all()

    billed = {m: Decimal(v) for m, v in billed_rows}
    collected = {m: Decimal(v) for m, v in paid_rows}
    months = [
        {
            "month": m,
            "billed": money(billed[m]),
            "collected": money(collected.get(m, ZERO)),
        }
        # only months that actually have invoices — no fabricated zero bars
        for m in sorted(billed)
    ]
    total_billed = money(sum(billed.values(), ZERO))
    total_collected = money(sum(collected.values(), ZERO))
    return {
        "year": year,
        "billed": total_billed,
        "collected": total_collected,
        "outstanding": money(total_billed - total_collected),
        "months": months,
    }


def late_fee_charged(db: Session, invoice: FeeInvoice) -> Decimal:
    """What fine currently stands on this invoice. A read: it never assesses."""
    head = db.scalar(
        select(FeeHead).where(
            FeeHead.school_id == invoice.school_id, FeeHead.code == LATE_FEE_CODE
        )
    )
    if head is None:
        return ZERO
    return money(
        sum((line.net for line in invoice.lines if line.fee_head_id == head.id), ZERO)
    )


def primary_contact(db: Session, student_id: int) -> dict | None:
    """Who the office rings about this child. A defaulter list without a phone
    number is a report rather than a chase (§5.5.3)."""
    row = db.scalar(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(
            StudentGuardian.student_id == student_id,
            StudentGuardian.is_primary.is_(True),
        )
    )
    if row is None:
        return None
    return {"name": row.user.full_name, "phone": row.user.phone, "email": row.user.email}


def enrolment_for_student(db: Session, student_id: int) -> Enrolment | None:
    return db.scalar(
        select(Enrolment)
        .where(Enrolment.student_id == student_id, Enrolment.status == EnrolmentStatus.active)
        .order_by(Enrolment.academic_year_id.desc())
    )


def new_idempotency_key() -> str:
    """For a caller with no natural key of its own — a counter clerk clicking
    Collect. The client should send its own where it can."""
    return uuid.uuid4().hex
