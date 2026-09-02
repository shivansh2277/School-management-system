from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedBase, enum_col
from app.models.enums import Gender, UserRole


class User(TimestampedBase):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role_login_id", "role", "login_id"),)

    role: Mapped[UserRole] = enum_col(UserRole, nullable=False)
    login_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(20))
    photo_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Student(TimestampedBase):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("class_section_id", "roll_no", name="uq_student_roll"),)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    admission_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    roll_no: Mapped[int] = mapped_column(nullable=False)
    dob: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender | None] = enum_col(Gender)
    address: Mapped[str | None] = mapped_column(Text)
    admission_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(lazy="joined")
    class_section = relationship("ClassSection", lazy="joined")


class Teacher(TimestampedBase):
    __tablename__ = "teachers"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(120))
    joining_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped[User] = relationship(lazy="joined")


class Parent(TimestampedBase):
    __tablename__ = "parents"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    occupation: Mapped[str | None] = mapped_column(String(80))

    user: Mapped[User] = relationship(lazy="joined")


class ParentStudent(TimestampedBase):
    __tablename__ = "parent_student"
    __table_args__ = (UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),)

    parent_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("parents.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    relation: Mapped[str] = mapped_column(String(20), nullable=False)
