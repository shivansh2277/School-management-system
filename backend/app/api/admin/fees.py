"""Invoices, the collection counter and the fee dashboard (§5.5.3).

Catalogue setup lives in `fee_setup.py`; this is the money itself.
"""

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Enrolment,
    FeeInvoice,
    FeePayment,
    FeePeriod,
    InvoiceStatus,
    Student,
    User,
)
from app.services import fees as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(module_enabled("fees"))],
)

admin_only = require_permission("fees.invoice.read", school_wide=True)
collector = require_permission("fees.payment.collect", school_wide=True)
voider = require_permission("fees.payment.void", school_wide=True)


class GenerateIn(BaseModel):
    model_config = {"extra": "forbid"}

    month: int
    year: int


class CollectIn(BaseModel):
    model_config = {"extra": "forbid"}

    enrolment_id: int
    amount: Decimal
    method: str = "cash"
    instrument_ref: str | None = None
    # Required, not optional: without it a retried request at the counter takes
    # the money twice (§3.9 rule 4).
    idempotency_key: str = Field(min_length=8, max_length=64)


class ReasonIn(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(min_length=3)


def _payment_out(p: FeePayment) -> dict:
    return {
        "id": p.id,
        "receipt_no": p.receipt_no,
        "enrolment_id": p.enrolment_id,
        "amount": p.amount,
        "method": p.method,
        "instrument_ref": p.instrument_ref,
        "received_at": p.received_at,
        "status": p.status,
        "reverses_payment_id": p.reverses_payment_id,
        "allocations": [
            {"invoice_line_id": a.invoice_line_id, "amount": a.amount} for a in p.allocations
        ],
    }


@router.get("/fees/invoices")
def invoices(
    month: int | None = None,
    year: int | None = None,
    status_: InvoiceStatus | None = None,
    class_section_id: int | None = None,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(FeeInvoice).where(FeeInvoice.school_id == user.school_id)
    if month is not None:
        q = q.where(FeeInvoice.period_month == month)
    if year is not None:
        q = q.where(FeeInvoice.period_year == year)
    if class_section_id is not None:
        q = q.where(
            FeeInvoice.enrolment_id.in_(
                select(Enrolment.id).where(Enrolment.class_section_id == class_section_id)
            )
        )
    rows = list(
        db.scalars(q.order_by(FeeInvoice.period_year.desc(), FeeInvoice.period_month.desc()))
    )
    out = svc.list_invoices(db, rows)
    # Filtered after the presented status is computed, so the filter matches
    # what the screen shows rather than what the sweep last stored.
    return [i for i in out if status_ is None or i["status"] == status_]


@router.post(
    "/fees/invoices/generate",
    dependencies=[Depends(require_permission("fees.invoice.generate"))],
)
def generate(
    body: GenerateIn, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    return svc.generate(db, body.month, body.year, user.school_id, actor=user)


@router.post("/fees/invoices/{invoice_id}/void")
def void_invoice(
    invoice_id: int,
    body: ReasonIn,
    user: User = Depends(voider),
    db: Session = Depends(get_db),
) -> dict:
    invoice = db.get(FeeInvoice, invoice_id)
    if invoice is None or invoice.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    return svc.invoice_out(db, svc.void(db, invoice, body.reason, user))


@router.get("/fees/ledger/{student_id}")
def ledger(
    student_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    student = db.get(Student, student_id)
    if student is None or student.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    enrolment = svc.enrolment_for_student(db, student_id)
    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This student has no active enrolment")
    return {"student_id": student_id, **svc.ledger(db, enrolment.id)}


@router.post("/fees/payments", status_code=201)
def collect(
    body: CollectIn, user: User = Depends(collector), db: Session = Depends(get_db)
) -> dict:
    enrolment = db.get(Enrolment, body.enrolment_id)
    if enrolment is None or enrolment.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
    payment = svc.collect(
        db,
        enrolment.id,
        body.amount,
        idempotency_key=body.idempotency_key,
        method=body.method,
        instrument_ref=body.instrument_ref,
        actor=user,
    )
    return _payment_out(payment)


@router.post("/fees/payments/{payment_id}/reverse")
def reverse(
    payment_id: int,
    body: ReasonIn,
    user: User = Depends(voider),
    db: Session = Depends(get_db),
) -> dict:
    payment = db.get(FeePayment, payment_id)
    if payment is None or payment.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    if payment.received_by == user.id:
        # §5.5.9: taking the money and cancelling the record of it are not the
        # same pair of hands.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "A payment must be reversed by someone other than whoever collected it",
        )
    return _payment_out(svc.reverse(db, payment, body.reason, user))


@router.get("/fees/defaulters")
def defaulters(
    min_amount: Decimal = Decimal("0"),
    class_section_id: int | None = None,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Who owes what, worst first, with a phone number to ring (§5.5.3).

    Thin, like the rest of this router. The list itself moved into
    `services/fees.py` when the defaulter chase in Communication needed the
    same one — two queries would drift, and §5.10.9 names that as the way a
    number stops meaning anything.
    """
    return svc.defaulters(
        db,
        user.school_id,
        min_amount=min_amount,
        class_section_id=class_section_id,
    )


@router.get("/fees/daybook")
def daybook(
    on: Date | None = None, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    """The day's collection register, by mode and by cashier (§5.5.10)."""
    return svc.daybook(db, user.school_id, on or Date.today())


@router.get("/fees/periods")
def periods(
    year: int | None = None, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[dict]:
    q = select(FeePeriod).where(FeePeriod.school_id == user.school_id)
    if year is not None:
        q = q.where(FeePeriod.period_year == year)
    return [
        {
            "year": p.period_year,
            "month": p.period_month,
            "status": p.status,
            "closed_at": p.closed_at,
            "note": p.note,
        }
        for p in db.scalars(q.order_by(FeePeriod.period_year, FeePeriod.period_month))
    ]


@router.post("/fees/periods/{year}/{month}/close", dependencies=[Depends(voider)])
def close_period(
    year: int,
    month: int,
    body: ReasonIn,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.close_period(db, user.school_id, year, month, user, body.reason)
    return {"year": row.period_year, "month": row.period_month, "status": row.status}


@router.post("/fees/periods/{year}/{month}/reopen", dependencies=[Depends(voider)])
def reopen_period(
    year: int,
    month: int,
    body: ReasonIn,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.reopen_period(db, user.school_id, year, month, user, body.reason)
    return {"year": row.period_year, "month": row.period_month, "status": row.status}


@router.get("/fees/collection")
def collection(
    year: int | None = None, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    return svc.collection(db, year or Date.today().year, user.school_id)
