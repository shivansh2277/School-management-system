"""Money taken before there is a fee account (§5.1.5, §5.1.9(15)).

An applicant has no student record and no ledger, so the application and
admission fees cannot be invoices. They are receipts against the application,
carried into the student's history at conversion.

No gateway: §0.10 defers that to V2. What is recorded here is cash, a cheque or
a UPI reference that somebody at the counter actually saw.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import ApplicationFeePurpose, PaymentStatus


class ApplicationPayment(TenantBase):
    __tablename__ = "application_payments"
    __table_args__ = (
        UniqueConstraint("school_id", "receipt_no", name="uq_application_receipt"),
        # Two clicks on Collect must not become two receipts.
        UniqueConstraint("idempotency_key", name="uq_application_payment_key"),
        Index("ix_application_payment", "application_id", "purpose"),
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False
    )
    purpose: Mapped[ApplicationFeePurpose] = enum_col(
        ApplicationFeePurpose, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    # Cheque number, UPI reference, the counter's own note — whatever proves
    # the money moved, since there is no gateway to ask.
    reference: Mapped[str | None] = mapped_column(String(80))
    receipt_no: Mapped[str] = mapped_column(String(24), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collected_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    status: Mapped[PaymentStatus] = enum_col(
        PaymentStatus, nullable=False, default=PaymentStatus.paid
    )
    # Voided, never deleted or edited — the same rule the fee counter follows.
    void_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
