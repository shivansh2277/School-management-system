"""Staff leave: the types a school defines, the balances, and the requests.

Leave types are rows rather than an enum. The student `LeaveType` enum
(sick/planned/emergency) is student-shaped and says nothing about entitlement;
a school's staff leave is casual/sick/earned with a quota each, and §3.15 puts
per-school configuration in tables rather than in code.
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import LeaveStatus


class LeaveTypeDef(TenantBase):
    """One kind of staff leave, with its yearly entitlement."""

    __tablename__ = "leave_types"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_leave_type_code"),
        CheckConstraint("annual_quota >= 0", name="ck_leave_type_quota"),
    )

    code: Mapped[str] = mapped_column(String(12), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    annual_quota: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    # Unpaid leave still needs a row: payroll's loss-of-pay is computed from
    # the days taken against a type that does not pay.
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class LeaveBalance(TenantBase):
    """What one employee has left of one type, this year.

    `used` is maintained by the approval path rather than recomputed on read,
    because the balance is checked on every application and a SUM over requests
    would be the same arithmetic done far more often. The two are reconciled by
    a test rather than by trust.
    """

    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "leave_type_id", "academic_year_id", name="uq_leave_balance"
        ),
        CheckConstraint("used >= 0", name="ck_leave_balance_used"),
    )

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leave_types.id"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    entitled: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    used: Mapped[Decimal] = mapped_column(
        Numeric(5, 1), nullable=False, default=Decimal(0)
    )

    leave_type = relationship("LeaveTypeDef", lazy="joined")

    @property
    def remaining(self) -> Decimal:
        return self.entitled - self.used


class StaffLeaveRequest(TenantBase):
    """One application, from draft to decision.

    Separate from `student_leave_requests` deliberately: that one writes the
    attendance register on approval, and this one creates timetable
    substitutions. The two look alike and do different work.
    """

    __tablename__ = "staff_leave_requests"
    __table_args__ = (
        Index("ix_staff_leave_employee_dates", "employee_id", "from_date", "to_date"),
        CheckConstraint("to_date >= from_date", name="ck_staff_leave_range"),
        CheckConstraint("days > 0", name="ck_staff_leave_days"),
    )

    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False, index=True
    )
    leave_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leave_types.id"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False
    )
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_half_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Working days, computed once at application time from the school calendar
    # and stored: recomputing it later would silently restate an approved
    # request when a holiday is declared after the fact.
    days: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[LeaveStatus] = enum_col(
        LeaveStatus, nullable=False, default=LeaveStatus.applied
    )
    # True when approved past the remaining balance. §5.3.9 allows that only as
    # an explicit exception, so it is a recorded fact rather than an absence of
    # one.
    balance_exception: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    decided_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)

    employee = relationship("Employee", lazy="joined")
    leave_type = relationship("LeaveTypeDef", lazy="joined")
