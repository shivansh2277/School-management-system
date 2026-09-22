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

