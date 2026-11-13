"""Public payment webhooks for acquiring bank / PSP real-time notifications."""

from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import PaymentProviderType
from app.services.payments import get_payment_provider

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/direct-upi/webhook", status_code=status.HTTP_200_OK)
async def direct_upi_webhook(
    request: Request,
    x_psp_signature: str | None = Header(None, alias="X-PSP-Signature"),
    x_signature: str | None = Header(None, alias="X-Signature"),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Acquiring bank / PSP webhook endpoint for Direct UPI Intent transaction reconciliation.

    Verifies HMAC-SHA256 signature using the school's configured webhook secret.
    Atomically settles confirmed transactions into the fee ledger.
    """
    signature = x_psp_signature or x_signature or x_webhook_signature
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature header (expected X-PSP-Signature)",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON body")

    school_id = payload.get("school_id")
    if not school_id:
        # Default to 1 if not passed in multi-tenant payload
        school_id = 1
    else:
        try:
            school_id = int(school_id)
        except (ValueError, TypeError):
            school_id = 1

    provider = get_payment_provider(PaymentProviderType.direct_upi)
    order = provider.verify_webhook(
        db=db,
        school_id=school_id,
        payload=payload,
        signature=signature,
    )

    return {
        "status": "success",
        "order_no": order.order_no,
        "order_status": order.status.value,
        "receipt_no": order.fee_payment.receipt_no if order.fee_payment else None,
    }
