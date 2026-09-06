from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import AttendanceStatus, NoticeAudience


class Attendance(TenantBase):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
        Index("ix_attendance_date", "date"),
        Index("ix_attendance_student_date", "student_id", "date"),
    )

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = enum_col(AttendanceStatus, nullable=False)
    marked_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(String(200))


class Homework(TenantBase):
    __tablename__ = "homework"

    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)


class HomeworkSubmission(TenantBase):
    __tablename__ = "homework_submissions"
    __table_args__ = (UniqueConstraint("homework_id", "student_id", name="uq_submission"),)

    homework_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("homework.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Notice(TenantBase):
    __tablename__ = "notices"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[NoticeAudience] = enum_col(NoticeAudience, nullable=False)
    class_section_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("class_sections.id")
    )
    published_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
