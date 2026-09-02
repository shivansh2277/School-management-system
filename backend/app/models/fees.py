from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase, enum_col
from app.models.enums import InvoiceStatus


class FeeStructure(TimestampedBase):
    __tablename__ = "fee_structures"

    class_name: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class FeeInvoice(TimestampedBase):
    __tablename__ = "fee_invoices"
    __table_args__ = (UniqueConstraint("student_id", "month", "year", name="uq_invoice_period"),)

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = enum_col(InvoiceStatus, nullable=False)


class FeePayment(TimestampedBase):
    __tablename__ = "fee_payments"

    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_invoices.id"), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="simulated")
    txn_ref: Mapped[str] = mapped_column(String(40), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)


class SchoolSettings(TimestampedBase):
    __tablename__ = "school_settings"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    logo_url: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(9))
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
