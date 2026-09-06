from datetime import date

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    EmployeeType,
    Gender,
    GuardianRelation,
    StudentStatus,
    UserRole,
)


class User(TenantBase):
    __tablename__ = "users"
    __table_args__ = (
        # Two schools will both have an "admin" and both may issue
        # SPS2024001, so the login namespace is per school, not global.
        UniqueConstraint("school_id", "login_id", name="uq_user_login"),
        Index("ix_users_school_role_login", "school_id", "role", "login_id"),
    )

    role: Mapped[UserRole] = enum_col(UserRole, nullable=False)
    login_id: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(20))
    photo_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Student(TenantBase):
    """What is true about a student for life. Which class they sit in is a fact
    about a *year* and lives on `enrolments` (ERP_BLUEPRINT §3.2)."""

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("school_id", "admission_no", name="uq_student_admission_no"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    admission_no: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[StudentStatus] = enum_col(
        StudentStatus, nullable=False, default=StudentStatus.active
    )
    dob: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender | None] = enum_col(Gender)
    address: Mapped[str | None] = mapped_column(Text)
    admission_date: Mapped[date | None] = mapped_column(Date)

    # School-defined attributes (§3.15 level 2). Validated against
    # `custom_fields` on write; never read without going through
    # services/custom_fields.py, which drops definitions that were retired.
    custom: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user: Mapped[User] = relationship(lazy="joined")


class Employee(TenantBase):
    """Any member of staff, teaching or not (ERP_BLUEPRINT §3.4).

    v0 called this `teachers`, which meant the librarian, the accountant and
    the bus in-charge had nowhere to live — and HR, payroll and transport in
    Part 4 are all built on staff, not on teachers. Renaming it before that
    happens is cheap; renaming it afterwards is not.

    `class_sections.class_teacher_id` and `class_subject_teacher.teacher_id`
    keep their names deliberately: they mean "the employee who teaches here",
    which is a role in a context, not the entity.
    """

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("school_id", "employee_code", name="uq_employee_code"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    # The staff number the school prints and says out loud, e.g. TCH001.
    employee_code: Mapped[str] = mapped_column(String(16), nullable=False)
    employee_type: Mapped[EmployeeType] = enum_col(
        EmployeeType, nullable=False, default=EmployeeType.teaching
    )
    qualification: Mapped[str | None] = mapped_column(String(120))
    joining_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(lazy="joined")


class Guardian(TenantBase):
    """Whoever is responsible for a child — not necessarily a parent (§3.4)."""

    __tablename__ = "guardians"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    occupation: Mapped[str | None] = mapped_column(String(80))
    # §0.7: no shared `persons` supertype, just this cross-link for the
    # teacher whose own child studies here. Nullable, and almost always null.
    employee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("employees.id")
    )

    user: Mapped[User] = relationship(lazy="joined")


class StudentGuardian(TenantBase):
    """The link, with the structure §3.4 asks for: which relation, and which
    one of them the school actually rings."""

    __tablename__ = "student_guardian"
    __table_args__ = (
        UniqueConstraint("guardian_id", "student_id", name="uq_student_guardian"),
        # At most one primary contact per child. A partial index rather than a
        # convention: "who do we call" must not have two answers.
        Index(
            "uq_student_primary_guardian",
            "student_id",
            unique=True,
            sqlite_where=text("is_primary"),
            postgresql_where=text("is_primary"),
        ),
    )

    guardian_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("guardians.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False
    )
    relation: Mapped[GuardianRelation] = enum_col(GuardianRelation, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
