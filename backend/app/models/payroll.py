"""Payroll: components, structures, runs and payslips (§3.16, §5.3).

**Payroll is a separate ledger from fees.** §5.3.6 calls mixing staff pay into
the student fee ledger a serious modelling error, so nothing here touches
`fee_invoices` or `fee_periods`. A payroll run's own status is the month lock —
reusing `fee_periods` would mean closing June for fees also closed June for
payroll, which are decisions different people make for different reasons.

**Zero hardcoded rates.** Every percentage in §3.16 is a row a school edits.
The code knows the *methods* — a percentage of basic, a balancing figure, loss
of pay — and never the numbers.
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
from app.models.enums import CalculationMethod, ComponentType, PayrollRunStatus


class SalaryComponent(TenantBase):
    """One line a payslip can carry, and how its amount is worked out.

    §3.16 ships a default set for a Lucknow CBSE school and every one of them is
    editable and disableable. The system holds no rate of its own.
    """

    __tablename__ = "salary_components"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_salary_component_code"),
        CheckConstraint("value >= 0", name="ck_salary_component_value"),
    )

    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    type: Mapped[ComponentType] = enum_col(ComponentType, nullable=False)
    calculation: Mapped[CalculationMethod] = enum_col(
        CalculationMethod, nullable=False
    )
    # A rupee amount for `fixed`, a percentage for the percent methods, and
    # ignored for `balance` and `loss_of_pay`, which take theirs from the rest
    # of the payslip.
    value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal(0)
    )
    # ESI applies only while gross is at or below a threshold (§3.16). A real
    # statutory condition, so a column rather than a special case in code.
    applies_below_gross: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    taxable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    statutory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # DA and Professional Tax ship inactive: most private schools pay no DA, and
    # Uttar Pradesh levies no professional tax (§0.B, confirmed 7 Sep 2026).
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Order of computation, not just of printing: basic has to exist before
    # anything takes a percentage of it, and the balancing figure has to come
    # after everything it balances against.
    sequence: Mapped[int] = mapped_column(nullable=False, default=0)


class SalaryStructure(TenantBase):
    """What one employee is on, from a date.

    A new structure supersedes rather than edits, so a payslip issued last
    March can still be explained by the terms in force then.
    """

    __tablename__ = "salary_structures"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "effective_from", name="uq_salary_structure_from"
        ),
        CheckConstraint("monthly_gross > 0", name="ck_salary_structure_gross"),
        # One structure in force per employee, enforced by the database rather
        # than by whoever remembers to stand the previous one down.
        Index(
            "uq_salary_structure_active",
            "employee_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active"),
        ),
    )

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False, index=True
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text)

    employee = relationship("Employee", lazy="joined")


class SalaryStructureItem(TenantBase):
    """A per-employee override of one component's value.

    Present only where somebody differs from the school's default — a fixed TDS
    the accountant computed, a negotiated conveyance. Absent means "use the
    component as the school defined it", which is the common case and costs no
    row.
    """

    __tablename__ = "salary_structure_items"
    __table_args__ = (
        UniqueConstraint("structure_id", "component_id", name="uq_structure_item"),
    )

    structure_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("salary_structures.id"), nullable=False, index=True
    )
    component_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("salary_components.id"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Lets a school switch one component off for one person without inventing a
    # second structure.
    included: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    component = relationship("SalaryComponent", lazy="joined")


class PayrollRun(TenantBase):
    """One month's payroll, once.

    §5.3.9: **an approved run is immutable; a correction is a supplementary
    run, never an edit.** That is why `run_no` is part of the key — a month can
    have a second and third run, each standing on its own, rather than one row
    that gets quietly restated.
    """

    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("school_id", "year", "month", "run_no", name="uq_payroll_run"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_payroll_run_month"),
    )

    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    run_no: Mapped[int] = mapped_column(nullable=False, default=1)
    is_supplementary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[PayrollRunStatus] = enum_col(
        PayrollRunStatus, nullable=False, default=PayrollRunStatus.draft
    )
    # The denominator §3.16's loss-of-pay formula divides by, frozen onto the
    # run: recomputing it after a holiday is declared would restate a payslip
    # somebody has already been given.
    working_days: Mapped[int | None] = mapped_column()

    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)

    @property
    def is_open(self) -> bool:
        return self.status in (PayrollRunStatus.draft, PayrollRunStatus.calculated)


class Payslip(TenantBase):
    """One person, one run. The totals are stored, not derived on read."""

    __tablename__ = "payslips"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id", name="uq_payslip_employee"),
        UniqueConstraint("school_id", "payslip_no", name="uq_payslip_no"),
    )

    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("payroll_runs.id"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False, index=True
    )
    payslip_no: Mapped[str] = mapped_column(String(32), nullable=False)

    working_days: Mapped[int] = mapped_column(nullable=False)
    lop_days: Mapped[Decimal] = mapped_column(
        Numeric(5, 1), nullable=False, default=Decimal(0)
    )
    monthly_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # What the school spends: earnings plus its own contributions. Not the same
    # as what the employee receives, and management asks for both.
    employer_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    employee = relationship("Employee", lazy="joined")


class PayslipLine(TenantBase):
    """One component on one payslip, as it was computed.

    A table rather than a JSON payload — unlike a report card, payroll is asked
    questions *across* documents: the PF register, the TDS register, cost per
    department (§5.3.10). Those are queries over lines, and a frozen blob would
    make each of them a scan-and-parse.

    The code and name are copied onto the row so a renamed or deleted component
    cannot rewrite what an issued payslip says.
    """

    __tablename__ = "payslip_lines"
    __table_args__ = (
        UniqueConstraint("payslip_id", "code", name="uq_payslip_line_code"),
        Index("ix_payslip_line_code", "code"),
    )

    payslip_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("payslips.id"), nullable=False, index=True
    )
    # Nullable: the component may be deleted later, and the line must survive.
    component_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("salary_components.id")
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    type: Mapped[ComponentType] = enum_col(ComponentType, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sequence: Mapped[int] = mapped_column(nullable=False, default=0)
