"""Admission fee collection and enrolment conversion (screens 14 and 15 of
§5.1.3) — the last two steps of the module."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import ApplicationFeePurpose, ApplicationPayment, User
from app.services import applications as app_svc
from app.services import conversion as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)
collector = Depends(require_permission("fees.payment.collect"))
converter = Depends(require_permission("admission.application.convert"))


class PaymentInput(BaseModel):
    model_config = {"extra": "forbid"}

    purpose: ApplicationFeePurpose
    amount: Decimal
    method: str = "cash"
    reference: str | None = None
    # The counter sends the same key on a retry; two clicks are one receipt.
    idempotency_key: str | None = None


def _payment_out(p: ApplicationPayment) -> dict:
    return {
        "id": p.id,
        "receipt_no": p.receipt_no,
        "purpose": p.purpose,
        "amount": p.amount,
        "method": p.method,
        "reference": p.reference,
        "paid_at": p.paid_at,
        "status": p.status,
        "void_reason": p.void_reason,
    }


@router.get("/applications/{application_id}/payments")
def list_payments(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    app = app_svc.get(db, user.school_id, application_id)
    return [_payment_out(p) for p in svc.payments_for(db, app.id)]


@router.post(
    "/applications/{application_id}/payments",
    status_code=status.HTTP_201_CREATED,
    dependencies=[collector],
)
def collect_payment(
    application_id: int,
    body: PaymentInput,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """Offline collection only — §0.10 defers the gateway to V2 — so what is
    recorded is cash, a cheque or a UPI reference somebody actually saw."""
    app = app_svc.get(db, user.school_id, application_id)
    payment = svc.collect(
        db,
        app,
        actor=user,
        purpose=body.purpose,
        amount=body.amount,
        method=body.method,
        reference=body.reference,
        idempotency_key=body.idempotency_key,
    )
    return {**_payment_out(payment), "application_status": app.status}


@router.delete(
    "/payments/{payment_id}",
    dependencies=[Depends(require_permission("fees.payment.void"))],
)
def void_payment(
    payment_id: int,
    reason: str = Query(..., min_length=3),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    payment = db.get(ApplicationPayment, payment_id)
    if payment is None or payment.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    svc.void_payment(db, payment, actor=user, reason=reason)
    return _payment_out(payment)


@router.get("/applications/{application_id}/conversion-preview")
def conversion_preview(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Everything conversion would do, writing nothing (§5.1.9(18))."""
    app = app_svc.get(db, user.school_id, application_id)
    return svc.preview(db, app)


@router.post("/applications/{application_id}/convert", dependencies=[converter])
def convert(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """One transaction: student, login, enrolment, guardians, links and
    documents (§5.1.9(16)). A partial conversion is the failure this exists to
    make impossible."""
    app = app_svc.get(db, user.school_id, application_id)
    return svc.convert(db, app, actor=user)
