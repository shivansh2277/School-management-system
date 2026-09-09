"""The fee ledger.

Two halves. The catalogue — heads, plans, assignments, concessions — says what
a child is charged. The ledger — invoices, lines, payments, allocations — is
what actually happened.

The ledger is a rebuild, not an extension (ERP_BLUEPRINT §3.9). v0 had one
amount per invoice and a `UNIQUE` on `fee_payments.invoice_id`, so a part
payment, a payment spanning two months and a head-wise collection report were
each impossible without breaking the other two. Payments now allocate to
invoice *lines*, and one mechanism gives all three.

Nothing here is ever edited to correct it: an invoice is voided and reissued, a
payment is reversed by a contra entry. Balances are derived from allocations
rather than stored, so no projection can drift from the ledger it summarises.
"""

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
    FeePaymentStatus,
    FeePeriodStatus,
    InvoiceStatus,
)

# --- the catalogue ----------------------------------------------------------


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


# --- the ledger -------------------------------------------------------------


class FeeInvoice(TenantBase):
    """One month's bill for one enrolment (§0.6: monthly, per student).

    Billed against the enrolment rather than the student, so a child who leaves
    in October stops being billed in November without anyone remembering to
    stop it.
    """

    __tablename__ = "fee_invoices"
    __table_args__ = (
        UniqueConstraint("school_id", "invoice_no", name="uq_invoice_no"),
        # One live invoice per enrolment per month. Partial, because a voided
        # invoice must be reissuable for the same month — the whole point of
        # voiding instead of editing.
        Index(
            "uq_invoice_period",
            "enrolment_id",
            "period_year",
            "period_month",
            unique=True,
            postgresql_where=text("status <> 'voided'"),
            sqlite_where=text("status <> 'voided'"),
        ),
        Index("ix_invoice_school_period", "school_id", "period_year", "period_month"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    invoice_no: Mapped[str] = mapped_column(String(24), nullable=False)
    period_month: Mapped[int] = mapped_column(nullable=False)
    period_year: Mapped[int] = mapped_column(nullable=False)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = enum_col(InvoiceStatus, nullable=False)
    # The day the balance first reached zero. §8C, answered 7 September 2026:
    # the late-fee clock runs until the invoice is *paid*, so this is what
    # stops it — and it makes the fine recomputable from the row alone rather
    # than dependent on when a job happened to run.
    settled_on: Mapped[date | None] = mapped_column(Date)
    void_reason: Mapped[str | None] = mapped_column(Text)

    lines = relationship(
        "FeeInvoiceLine", lazy="selectin", cascade="all, delete-orphan", back_populates="invoice"
    )
    enrolment = relationship("Enrolment", lazy="joined")


class FeeInvoiceLine(TenantBase):
    """One head on one invoice. The unit a payment allocates against.

    `discount` is the concession as it stood when the invoice was raised.
    Snapshotted rather than recomputed, because an invoice a parent has already
    been shown must not change when someone edits a concession next term.
    """

    __tablename__ = "fee_invoice_lines"
    __table_args__ = (
        CheckConstraint("amount >= 0 AND discount >= 0", name="ck_invoice_line_amounts"),
        CheckConstraint("discount <= amount", name="ck_invoice_line_discount"),
    )

    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_invoices.id"), nullable=False, index=True
    )
    fee_head_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_heads.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )

    invoice = relationship("FeeInvoice", back_populates="lines")
    head = relationship("FeeHead", lazy="joined")

    @property
    def net(self) -> Decimal:
        return self.amount - self.discount


class FeePayment(TenantBase):
    """Money received. Against an enrolment, not against an invoice.

    A parent hands over ₹5,000 at the counter; which months that settles is an
    allocation decision, and often spans two of them. The v0 model made the
    invoice the payment's identity and could express none of that.
    """

    __tablename__ = "fee_payments"
    __table_args__ = (
        UniqueConstraint("school_id", "receipt_no", name="uq_payment_receipt_no"),
        # §3.9 rule 4. A retried request returns the original receipt instead
        # of taking the money twice; the constraint is what makes that true
        # even when two requests arrive at once.
        UniqueConstraint("school_id", "idempotency_key", name="uq_payment_idempotency"),
        CheckConstraint("amount <> 0", name="ck_payment_amount_nonzero"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    receipt_no: Mapped[str] = mapped_column(String(24), nullable=False)
    # Negative on a contra entry: a reversal is a row, never an UPDATE, so the
    # ledger still sums correctly with a plain SUM (§3.9 rule 3).
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")
    instrument_ref: Mapped[str | None] = mapped_column(String(40))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[FeePaymentStatus] = enum_col(
        FeePaymentStatus, nullable=False, default=FeePaymentStatus.success
    )
    reverses_payment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fee_payments.id")
    )
    reason: Mapped[str | None] = mapped_column(Text)

    allocations = relationship(
        "PaymentAllocation", lazy="selectin", cascade="all, delete-orphan", back_populates="payment"
    )


class PaymentAllocation(TenantBase):
    """How much of a payment settled which line. The ledger's only truth about
    what is paid — every balance in the system is a SUM over this table."""

    __tablename__ = "payment_allocations"
    __table_args__ = (
        Index("ix_allocation_line", "invoice_line_id"),
    )

    payment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_payments.id"), nullable=False, index=True
    )
    invoice_line_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fee_invoice_lines.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    payment = relationship("FeePayment", back_populates="allocations")


class FeePeriod(TenantBase):
    """One billing month's books, open or closed.

    Closing is what makes a collection figure quotable: once the month is
    closed nothing can be billed into it, no money can be received dated inside
    it, and no invoice of that month can be voided. Money taken today against
    an old invoice still lands in today's period — a receipt is dated when it
    was issued, not when the bill was raised (§5.5.9).
    """

    __tablename__ = "fee_periods"
    __table_args__ = (
        UniqueConstraint("school_id", "period_year", "period_month", name="uq_fee_period"),
    )

    period_year: Mapped[int] = mapped_column(nullable=False)
    period_month: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[FeePeriodStatus] = enum_col(
        FeePeriodStatus, nullable=False, default=FeePeriodStatus.open
    )
    closed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
