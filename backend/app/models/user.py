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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import Gender, StudentStatus, UserRole


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


class Teacher(TenantBase):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "employee_id", name="uq_teacher_employee_id"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(16), nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(120))
    joining_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(lazy="joined")


class Parent(TenantBase):
    __tablename__ = "parents"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    occupation: Mapped[str | None] = mapped_column(String(80))

    user: Mapped[User] = relationship(lazy="joined")


class ParentStudent(TenantBase):
    __tablename__ = "parent_student"
    __table_args__ = (UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),)

    parent_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("parents.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    relation: Mapped[str] = mapped_column(String(20), nullable=False)
