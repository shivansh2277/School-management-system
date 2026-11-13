"""Abstract interface for payment gateway and intent providers."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models import PaymentOrder, User


class PaymentGatewayProvider(ABC):
    """Unified interface for all payment rails (Direct UPI Intent, Razorpay, etc.)."""

    @abstractmethod
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
        """Create a trackable payment order with intent parameters and expiry."""
        ...

    @abstractmethod
    def verify_webhook(
        self,
        db: Session,
        school_id: int,
        payload: dict[str, Any],
        signature: str | None,
    ) -> PaymentOrder:
        """Process an authorized provider/acquirer webhook and settle funds into ledger."""
        ...

    @abstractmethod
    def submit_utr(
        self,
        db: Session,
        order: PaymentOrder,
        bank_utr: str,
    ) -> PaymentOrder:
        """Record a payer-submitted bank UTR / RRN for reconciliation."""
        ...

    @abstractmethod
    def verify_utr(
        self,
        db: Session,
        order: PaymentOrder,
        approved: bool,
        actor: User,
        notes: str | None = None,
    ) -> PaymentOrder:
        """Accounts desk manual verification of submitted bank UTR."""
        ...

    @abstractmethod
    def cancel_order(
        self,
        db: Session,
        order: PaymentOrder,
        reason: str | None = None,
    ) -> PaymentOrder:
        """Cancel an open payment order before expiry."""
        ...

    @abstractmethod
    def check_status(
        self,
        db: Session,
        order: PaymentOrder,
    ) -> PaymentOrder:
        """Check status and handle automatic expiry after the 5-minute window."""
        ...
