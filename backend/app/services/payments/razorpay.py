"""Razorpay payment gateway provider stub / architectural blueprint.

Prepared for future Razorpay integration (Cards, Netbanking, Wallets, and Razorpay UPI).
Direct UPI is the currently active payment rail.
"""

from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import PaymentOrder, PaymentProviderType, User
from app.services.payments.base import PaymentGatewayProvider


class RazorpayProvider(PaymentGatewayProvider):
    """Razorpay Gateway Provider (Architecture Ready for V2).

    Integrates with Razorpay Standard Orders API and Webhook Events:
    - payment.authorized
    - payment.captured
    - payment.failed
    """

    def __init__(self, key_id: str | None = None, key_secret: str | None = None) -> None:
        self.key_id = key_id
        self.key_secret = key_secret

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def create_order(
        self,
        db: Session,
        school_id: int,
        enrolment_id: int,
        student_id: int,
        amount: Decimal,
        invoice_id: int | None,
        idempotency_key: str,
        note: str | None = None,
    ) -> PaymentOrder:
        """Create Razorpay order via Razorpay Orders API.

        Raises 501 until Razorpay API credentials are configured.
        """
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Razorpay gateway is not configured for this school. Use Direct UPI payments.",
            )
        # Future implementation will call:
        # client = razorpay.Client(auth=(self.key_id, self.key_secret))
        # rzp_order = client.order.create({"amount": int(amount * 100), "currency": "INR", "receipt": ...})
        raise NotImplementedError("Razorpay order creation will be activated in V2.")

    def verify_webhook(
        self,
        db: Session,
        school_id: int,
        payload: dict[str, Any],
        signature: str | None,
    ) -> PaymentOrder:
        """Verify Razorpay payment signature or webhook signature."""
        if not self.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Razorpay webhook handling is not configured.",
            )
        raise NotImplementedError("Razorpay webhook verification will be activated in V2.")

    def submit_utr(
        self,
        db: Session,
        order: PaymentOrder,
        bank_utr: str,
    ) -> PaymentOrder:
        """Razorpay reconciles automatically via payment gateway webhooks.

        Manual UTR submission is specific to Direct UPI Intent transfers.
        """
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual UTR submission is not supported for Razorpay gateway orders.",
        )

    def verify_utr(
        self,
        db: Session,
        order: PaymentOrder,
        approved: bool,
        actor: User,
        notes: str | None = None,
    ) -> PaymentOrder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual UTR verification is not supported for Razorpay gateway orders.",
        )

    def cancel_order(
        self,
        db: Session,
        order: PaymentOrder,
        reason: str | None = None,
    ) -> PaymentOrder:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Razorpay order cancellation will be activated in V2.",
        )

    def check_status(
        self,
        db: Session,
        order: PaymentOrder,
    ) -> PaymentOrder:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Razorpay status check will be activated in V2.",
        )
