from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    ConcessionStatus,
    ConcessionType,
    FeeFrequency,
    FeeHeadType,
    InvoiceStatus,
)


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


# --- the fee catalogue (ERP_BLUEPRINT §3.9, §5.5) ---------------------------
# `fee_structures` above holds one flat monthly amount per class and has
# nowhere to put a transport charge, an admission fee or a concession. These
# four tables replace it; the invoice rebuild that consumes them follows.


class FeeHead(TenantBase):
    __tablename__ = "fee_heads"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_fee_head_code"),)

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[FeeHeadType] = enum_col(FeeHeadType, nullable=False)
    is_refundable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gl_code: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FeePlan(TenantBase):
    """What a class is charged for a year.

    `class_name` is the default applicability — every enrolment in class 8 bills
    from the class 8 plan unless a `student_fee_plans` row says otherwise. Two
    levels rather than one because most children are on the standard plan and
    the exceptions are individual.
    """

    __tablename__ = "fee_plans"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "name", name="uq_fee_plan_name"),
        # At most one default plan per class per year: two would make invoice
        # generation depend on row order.
        Index(
            "uq_fee_plan_class",
            "academic_year_id",
            "class_name",
            unique=True,
            postgresql_where=text("class_name IS NOT NULL"),
            sqlite_where=text("class_name IS NOT NULL"),
        ),
    )

    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    class_name: Mapped[str | None] = mapped_column(String(8))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    items = relationship(
        "FeePlanItem", lazy="selectin", cascade="all, delete-orphan", back_populates="plan"
    )


class FeePlanItem(TenantBase):
    __tablename__ = "fee_plan_items"
    __table_args__ = (
        UniqueConstraint("fee_plan_id", "fee_head_id", name="uq_fee_plan_item"),
        CheckConstraint("amount >= 0", name="ck_fee_plan_item_amount"),
    )

    fee_plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_plans.id"), nullable=False, index=True
    )
    fee_head_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_heads.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    frequency: Mapped[FeeFrequency] = enum_col(FeeFrequency, nullable=False)

    plan = relationship("FeePlan", back_populates="items")
    head = relationship("FeeHead", lazy="joined")


class StudentFeePlan(TenantBase):
    """An individual override of the class default. Keyed to the enrolment, not
    the student: what a child is charged is a fact about a year (§3.2)."""

    __tablename__ = "student_fee_plans"
    __table_args__ = (UniqueConstraint("enrolment_id", name="uq_student_fee_plan"),)

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False
    )
    fee_plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_plans.id"), nullable=False
    )
    assigned_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))


class FeeConcession(TenantBase):
    """A discount that someone approved.

    Percent or amount, never both, and either against one head or against the
    whole invoice. Only `approved` rows reduce money; a requested one is a
    request (§5.5.9).
    """

    __tablename__ = "fee_concessions"
    __table_args__ = (
        CheckConstraint(
            "(percent IS NULL) <> (amount IS NULL)", name="ck_concession_percent_xor_amount"
        ),
        # One live concession of a kind per enrolment. Without this, running
        # the sibling sweep twice would stack two 10% discounts.
        Index(
            "uq_concession_live",
            "enrolment_id",
            "type",
            unique=True,
            postgresql_where=text("status = 'approved'"),
            sqlite_where=text("status = 'approved'"),
        ),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    type: Mapped[ConcessionType] = enum_col(ConcessionType, nullable=False)
    fee_head_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("fee_heads.id"))
    percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConcessionStatus] = enum_col(
        ConcessionStatus, nullable=False, default=ConcessionStatus.requested
    )
    requested_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
