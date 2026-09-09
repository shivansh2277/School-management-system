"""departments, and the employee profile HR and payroll need

`employees` carried four fields. §5.3 builds hiring, leave, attendance and
payroll on top of it, and §3.16 attaches a salary structure to an employee, so
the record has to say which department they sit in, who they report to, whether
they are still in service, and how they are paid.

There is no `designations` table. A designation has no attributes and no
relationships here — salary structures attach to the employee, not to the grade
— so it is a string until the day it carries a pay band.

The statutory and bank columns land on `employees` but are deliberately not
returned by anything that returns a profile: §5.3.9 keeps salary information
behind its own permission, and `/admin/employees/{id}/statutory` is the only
route that serves them.

Revision ID: c5e72a04f1d9
Revises: b4d61f93e0c8
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5e72a04f1d9"
down_revision: str | None = "b4d61f93e0c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUS = sa.Enum(
    "active", "on_leave", "notice_period", "exited",
    name="employeestatus", native_enum=False,
)

_NEW_COLUMNS = [
    ("designation", sa.String(60)),
    ("emergency_contact_name", sa.String(120)),
    ("emergency_contact_phone", sa.String(20)),
    ("pan", sa.String(10)),
    ("uan", sa.String(12)),
    ("esi_number", sa.String(20)),
    ("bank_account_no", sa.String(20)),
    ("bank_ifsc", sa.String(11)),
    ("bank_name", sa.String(80)),
]


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
            nullable=False, index=True,
        ),
        sa.Column("code", sa.String(12), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        # Nullable: a department exists before anyone is put in charge of it.
        sa.Column("head_employee_id", sa.BigInteger(), sa.ForeignKey("employees.id")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("school_id", "code", name="uq_department_code"),
    )

    with op.batch_alter_table("employees") as batch:
        batch.add_column(sa.Column("department_id", sa.BigInteger()))
        batch.add_column(sa.Column("reporting_to_id", sa.BigInteger()))
        # Everyone already on the books is in service.
        batch.add_column(
            sa.Column("status", _STATUS, nullable=False, server_default="active")
        )
        batch.add_column(sa.Column("exited_on", sa.Date()))
        for name, type_ in _NEW_COLUMNS:
            batch.add_column(sa.Column(name, type_))
        batch.create_foreign_key(
            "fk_employee_department", "departments", ["department_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_employee_reports_to", "employees", ["reporting_to_id"], ["id"]
        )
    op.create_index("ix_employees_department_id", "employees", ["department_id"])


def downgrade() -> None:
    op.drop_index("ix_employees_department_id", table_name="employees")
    with op.batch_alter_table("employees") as batch:
        batch.drop_constraint("fk_employee_reports_to", type_="foreignkey")
        batch.drop_constraint("fk_employee_department", type_="foreignkey")
        for name, _ in reversed(_NEW_COLUMNS):
            batch.drop_column(name)
        batch.drop_column("exited_on")
        batch.drop_column("status")
        batch.drop_column("reporting_to_id")
        batch.drop_column("department_id")
    op.drop_table("departments")
