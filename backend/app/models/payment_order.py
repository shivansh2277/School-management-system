"""Payment order lifecycle tracking gateway/intent orders, UTR verification, and reconciliation."""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import PaymentMethodType, PaymentOrderStatus, PaymentProviderType


class PaymentOrder(TenantBase):
    """Tracks an intent or gateway payment attempt before it is settled into fee_payments.

    An invoice or ledger row is NEVER marked paid directly from this table. Only after
    the provider confirms payment (or accounts staff approves UTR) does svc.collect()
    execute the authoritative FIFO allocation and create a real FeePayment.
    """

    __tablename__ = "payment_orders"
    __table_args__ = (
        UniqueConstraint("school_id", "order_no", name="uq_payment_order_no"),
        UniqueConstraint("school_id", "tr_ref", name="uq_payment_order_tr"),
        UniqueConstraint("idempotency_key", name="uq_payment_order_idempotency"),
        Index("ix_payment_order_enrolment", "enrolment_id", "status"),
        Index("ix_payment_order_student", "student_id", "status"),
        Index("ix_payment_order_status_created", "status", "created_at"),
    )

    order_no: Mapped[str] = mapped_column(String(40), nullable=False)
    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False, index=True
    )
    invoice_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fee_invoices.id"), index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    provider: Mapped[PaymentProviderType] = enum_col(
        PaymentProviderType, nullable=False, default=PaymentProviderType.direct_upi
    )
    method: Mapped[PaymentMethodType] = enum_col(
        PaymentMethodType, nullable=False, default=PaymentMethodType.upi
    )
    status: Mapped[PaymentOrderStatus] = enum_col(
        PaymentOrderStatus, nullable=False, default=PaymentOrderStatus.created
    )

    # NPCI UPI Transaction Reference (tr=)
    tr_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    upi_intent_url: Mapped[str | None] = mapped_column(Text)

    # 12-digit Bank Reference Number (UTR / RRN) submitted by parent or PSP webhook
    bank_utr: Mapped[str | None] = mapped_column(String(64), index=True)
    utr_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Accounts staff manual verification
    verified_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    # Order validity window (5 minutes by default)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Populated only once settled into the fee ledger
    fee_payment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fee_payments.id"), index=True
    )

    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text)

    # Relationships
    enrolment = relationship("Enrolment", lazy="joined")
    student = relationship("Student", lazy="joined")
    invoice = relationship("FeeInvoice", lazy="joined")
    fee_payment = relationship("FeePayment", lazy="joined")
