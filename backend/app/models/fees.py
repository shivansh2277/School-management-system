from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import InvoiceStatus


class FeeStructure(TenantBase):
    __tablename__ = "fee_structures"
    __table_args__ = (
        UniqueConstraint("school_id", "class_name", name="uq_fee_structure_class"),
    )

    class_name: Mapped[str] = mapped_column(String(8), nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class FeeInvoice(TenantBase):
    __tablename__ = "fee_invoices"
    __table_args__ = (UniqueConstraint("student_id", "month", "year", name="uq_invoice_period"),)

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = enum_col(InvoiceStatus, nullable=False)


class FeePayment(TenantBase):
    __tablename__ = "fee_payments"
    __table_args__ = (
        UniqueConstraint("school_id", "receipt_no", name="uq_payment_receipt_no"),
    )

    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_invoices.id"), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="simulated")
    txn_ref: Mapped[str] = mapped_column(String(40), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(24), nullable=False)
