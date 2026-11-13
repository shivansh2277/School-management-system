from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import Enrolment, FeeInvoice, FeeInvoiceLine, FeePayment, PaymentAllocation, User
from app.pdf.receipt import build_receipt
from app.services import fees as svc
from app.services import scoping
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/parent",
    tags=["parent"],
    dependencies=[Depends(module_enabled("fees"))],
)
parent_only = require_permission("fees.invoice.read")


class PayIn(BaseModel):
    model_config = {"extra": "forbid"}

    student_id: int
    amount: Decimal
    idempotency_key: str = Field(min_length=8, max_length=64)


def _enrolment_of(db: Session, user: User, student_id: int):
    scoping.assert_can_read_student(db, user, student_id)
    enrolment = svc.enrolment_for_student(db, student_id)
    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active enrolment")
    return enrolment


@router.get("/fees")
def invoices(
    student_id: int | None = None,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    ids = (
        [student_id]
        if student_id is not None
        else scoping.child_ids_for(db, user)
    )
    if student_id is not None:
        scoping.assert_can_read_student(db, user, student_id)
    enrolment_ids = [
        e.id for e in (svc.enrolment_for_student(db, sid) for sid in ids) if e is not None
    ]
    rows = list(
        db.scalars(
            select(FeeInvoice)
            .where(FeeInvoice.enrolment_id.in_(enrolment_ids or [0]))
            .order_by(FeeInvoice.period_year.desc(), FeeInvoice.period_month.desc())
        )
    )
    return svc.list_invoices(db, rows)


@router.get("/fees/ledger")
def ledger(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> dict:
    return svc.ledger(db, _enrolment_of(db, user, student_id).id)


@router.post(
    "/fees/pay",
    status_code=201,
    dependencies=[Depends(require_permission("fees.payment.pay_own"))],
)
def pay(body: PayIn, user: User = Depends(parent_only), db: Session = Depends(get_db)) -> dict:
    """Record a payment against the child's account.

    Not "pay invoice 12": §0.10 defers the gateway, and even offline a parent
    hands over an amount, not a row. It settles the oldest dues first, which is
    both what a school does and what keeps the late-fee clock shortest.
    """
    enrolment = _enrolment_of(db, user, body.student_id)
    payment = svc.collect(
        db,
        enrolment.id,
        body.amount,
        idempotency_key=body.idempotency_key,
        method="online",
        actor=user,
    )
    return {
        "id": payment.id,
        "receipt_no": payment.receipt_no,
        "amount": payment.amount,
        "received_at": payment.received_at,
        "credit": svc.credit_balance(db, enrolment.id),
    }


@router.get("/fees/receipt/{payment_id}")
@router.get("/fees/receipts/{payment_id}")
@router.get("/fees/receipts/{payment_id}.pdf")
def receipt(
    payment_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> Response:
    payment = db.get(FeePayment, payment_id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    owner = db.get(Enrolment, payment.enrolment_id)
    scoping.assert_can_read_student(db, user, owner.student_id)
    return Response(
        content=build_receipt(db, payment.id),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=receipt-{payment.receipt_no.replace('/', '-')}.pdf"
        },
    )


@router.get("/fees/{invoice_id}/receipt.pdf")
@router.get("/fees/invoices/{invoice_id}/receipt.pdf")
def invoice_receipt(
    invoice_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> Response:
    payment = db.scalar(
        select(FeePayment)
        .join(PaymentAllocation, PaymentAllocation.payment_id == FeePayment.id)
        .join(FeeInvoiceLine, FeeInvoiceLine.id == PaymentAllocation.invoice_line_id)
        .where(FeeInvoiceLine.invoice_id == invoice_id)
        .order_by(FeePayment.id.desc())
    )
    if not payment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No payment found for this invoice")
    return receipt(payment.id, user, db)



from datetime import UTC, datetime
import uuid
from app.models import InvoiceStatus, PaymentOrder, PaymentOrderStatus, PaymentProviderType
from app.services.payments import get_payment_provider


class CreatePaymentOrderIn(BaseModel):
    model_config = {"extra": "forbid"}

    student_id: int
    invoice_id: int
    provider: PaymentProviderType = PaymentProviderType.direct_upi
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=64)


class SubmitUTRIn(BaseModel):
    model_config = {"extra": "forbid"}

    bank_utr: str = Field(min_length=8, max_length=30)


class CancelOrderIn(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str | None = Field(default=None, max_length=200)


def _order_out(order: PaymentOrder) -> dict:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "school_id": order.school_id,
        "enrolment_id": order.enrolment_id,
        "student_id": order.student_id,
        "invoice_id": order.invoice_id,
        "amount": str(order.amount),
        "currency": order.currency,
        "provider": order.provider.value if hasattr(order.provider, "value") else str(order.provider),
        "method": order.method.value if hasattr(order.method, "value") else str(order.method),
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "tr_ref": order.tr_ref,
        "upi_intent_url": order.upi_intent_url,
        "bank_utr": order.bank_utr,
        "utr_submitted_at": order.utr_submitted_at.isoformat() if order.utr_submitted_at else None,
        "expires_at": order.expires_at.isoformat() if order.expires_at else None,
        "fee_payment_id": order.fee_payment_id,
        "receipt_no": order.fee_payment.receipt_no if order.fee_payment else None,
        "verified_at": order.verified_at.isoformat() if order.verified_at else None,
        "verification_notes": order.verification_notes,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@router.post(
    "/fees/orders",
    status_code=201,
    dependencies=[Depends(require_permission("fees.payment.pay_own"))],
)
def create_payment_order(
    body: CreatePaymentOrderIn,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> dict:
    enrolment = _enrolment_of(db, user, body.student_id)
    invoice = db.get(FeeInvoice, body.invoice_id)
    if invoice is None or invoice.enrolment_id != enrolment.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found for this student")
    if invoice.status == InvoiceStatus.voided:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot pay a voided invoice")

    inv_totals = svc.totals(db, invoice)
    balance = inv_totals["balance"]
    if balance <= Decimal("0.00"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invoice is already fully paid")

    now = datetime.now(UTC)
    existing_order = db.scalar(
        select(PaymentOrder).where(
            PaymentOrder.school_id == user.school_id,
            PaymentOrder.invoice_id == invoice.id,
            PaymentOrder.status.in_([PaymentOrderStatus.created, PaymentOrderStatus.pending]),
            PaymentOrder.expires_at > now,
        )
    )
    if existing_order:
        return _order_out(existing_order)

    idempotency_key = body.idempotency_key or f"order-{user.school_id}-{invoice.id}-{uuid.uuid4().hex[:12]}"
    provider = get_payment_provider(body.provider)
    order = provider.create_order(
        db,
        school_id=user.school_id,
        enrolment_id=enrolment.id,
        student_id=body.student_id,
        amount=balance,
        invoice_id=invoice.id,
        idempotency_key=idempotency_key,
        note=f"Fee Inv {invoice.invoice_no}",
    )
    return _order_out(order)


@router.get("/fees/orders")
def list_payment_orders(
    student_id: int,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    scoping.assert_can_read_student(db, user, student_id)
    enrolment = _enrolment_of(db, user, student_id)
    provider = get_payment_provider(PaymentProviderType.direct_upi)
    orders = list(
        db.scalars(
            select(PaymentOrder)
            .where(
                PaymentOrder.school_id == user.school_id,
                PaymentOrder.enrolment_id == enrolment.id,
            )
            .order_by(PaymentOrder.id.desc())
            .limit(20)
        )
    )
    for o in orders:
        provider.check_status(db, o)
    return [_order_out(o) for o in orders]


@router.get("/fees/orders/{order_id}")
def get_payment_order(
    order_id: int,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> dict:
    order = db.get(PaymentOrder, order_id)
    if order is None or order.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment order not found")
    scoping.assert_can_read_student(db, user, order.student_id)
    provider = get_payment_provider(order.provider)
    order = provider.check_status(db, order)
    return _order_out(order)


@router.post("/fees/orders/{order_id}/cancel")
def cancel_payment_order(
    order_id: int,
    body: CancelOrderIn | None = None,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> dict:
    order = db.get(PaymentOrder, order_id)
    if order is None or order.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment order not found")
    scoping.assert_can_read_student(db, user, order.student_id)
    provider = get_payment_provider(order.provider)
    reason = body.reason if body else "Cancelled by parent"
    order = provider.cancel_order(db, order, reason=reason)
    return _order_out(order)


@router.post("/fees/orders/{order_id}/submit-utr")
def submit_utr(
    order_id: int,
    body: SubmitUTRIn,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> dict:
    order = db.get(PaymentOrder, order_id)
    if order is None or order.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment order not found")
    scoping.assert_can_read_student(db, user, order.student_id)
    provider = get_payment_provider(order.provider)
    order = provider.submit_utr(db, order, body.bank_utr)
    return _order_out(order)
