"""payroll: components, structures, runs and payslips

§3.16 built as components rather than rules: the code knows the methods — a
percentage of basic, a balancing figure, loss of pay — and never the numbers.
Basic at 50% and PF at 12% are seed rows a school edits.

Payroll is a **separate ledger** from fees (§5.3.6). Nothing here touches
`fee_invoices` or `fee_periods`; a run's own status is the month lock, because
closing June for fees and closing June for payroll are decisions different
people make for different reasons.

`payslip_lines` is a table rather than a frozen JSON payload — unlike a report
card, payroll is asked questions *across* documents (the PF register, cost per
department, §5.3.10), and those are queries over lines.

Revision ID: f8b05d37a1ec
Revises: e7a94c26d3fb
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f8b05d37a1ec"
down_revision: str | None = "e7a94c26d3fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TYPE = sa.Enum(
    "earning", "deduction", "employer_contribution",
    name="componenttype", native_enum=False,
)
_CALC = sa.Enum(
    "fixed", "percent_of_basic", "percent_of_gross", "balance", "loss_of_pay",
    name="calculationmethod", native_enum=False,
)
_RUN = sa.Enum(
    "draft", "calculated", "approved", "paid",
    name="payrollrunstatus", native_enum=False,
)


def _pk() -> sa.Column:
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        primary_key=True,
    )


def _stamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
        nullable=False, index=True,
    )


def upgrade() -> None:
    op.create_table(
        "salary_components",
        _pk(), _tenant(),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("type", _TYPE, nullable=False),
        sa.Column("calculation", _CALC, nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("applies_below_gross", sa.Numeric(12, 2)),
        sa.Column("taxable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("statutory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        *_stamps(),
        sa.UniqueConstraint("school_id", "code", name="uq_salary_component_code"),
        sa.CheckConstraint("value >= 0", name="ck_salary_component_value"),
    )

    op.create_table(
        "salary_structures",
        _pk(), _tenant(),
        sa.Column(
            "employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"),
            nullable=False, index=True,
        ),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("monthly_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("note", sa.Text()),
        *_stamps(),
        sa.UniqueConstraint(
            "employee_id", "effective_from", name="uq_salary_structure_from"
        ),
        sa.CheckConstraint("monthly_gross > 0", name="ck_salary_structure_gross"),
    )
    op.create_index(
        "uq_salary_structure_active",
        "salary_structures",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
        sqlite_where=sa.text("is_active"),
    )

    op.create_table(
        "salary_structure_items",
        _pk(), _tenant(),
        sa.Column(
            "structure_id", sa.BigInteger(), sa.ForeignKey("salary_structures.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "component_id", sa.BigInteger(), sa.ForeignKey("salary_components.id"),
            nullable=False,
        ),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint("structure_id", "component_id", name="uq_structure_item"),
    )

    op.create_table(
        "payroll_runs",
        _pk(), _tenant(),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("run_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "is_supplementary", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("status", _RUN, nullable=False, server_default="draft"),
        sa.Column("working_days", sa.Integer()),
        sa.Column("calculated_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.Text()),
        *_stamps(),
        sa.UniqueConstraint(
            "school_id", "year", "month", "run_no", name="uq_payroll_run"
        ),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_payroll_run_month"),
    )

    op.create_table(
        "payslips",
        _pk(), _tenant(),
        sa.Column(
            "run_id", sa.BigInteger(), sa.ForeignKey("payroll_runs.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"),
            nullable=False, index=True,
        ),
        sa.Column("payslip_no", sa.String(32), nullable=False),
        sa.Column("working_days", sa.Integer(), nullable=False),
        sa.Column("lop_days", sa.Numeric(5, 1), nullable=False, server_default="0"),
        sa.Column("monthly_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_earnings", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("employer_cost", sa.Numeric(12, 2), nullable=False),
        *_stamps(),
        sa.UniqueConstraint("run_id", "employee_id", name="uq_payslip_employee"),
        sa.UniqueConstraint("school_id", "payslip_no", name="uq_payslip_no"),
    )

    op.create_table(
        "payslip_lines",
        _pk(), _tenant(),
        sa.Column(
            "payslip_id", sa.BigInteger(), sa.ForeignKey("payslips.id"),
            nullable=False, index=True,
        ),
        # Nullable: the component may be deleted later and the line must survive.
        sa.Column(
            "component_id", sa.BigInteger(), sa.ForeignKey("salary_components.id")
        ),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("type", _TYPE, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        *_stamps(),
        sa.UniqueConstraint("payslip_id", "code", name="uq_payslip_line_code"),
    )
    op.create_index("ix_payslip_line_code", "payslip_lines", ["code"])


def downgrade() -> None:
    op.drop_index("ix_payslip_line_code", table_name="payslip_lines")
    op.drop_table("payslip_lines")
    op.drop_table("payslips")
    op.drop_table("payroll_runs")
    op.drop_table("salary_structure_items")
    op.drop_index("uq_salary_structure_active", table_name="salary_structures")
    op.drop_table("salary_structures")
    op.drop_table("salary_components")
