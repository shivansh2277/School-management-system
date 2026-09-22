"""Grievances and feedback models for staff, teachers, parents, and students.

Supports submitting issues, multi-tenant scoping, delegation/assignment to teachers,
status workflows (open, in_progress, resolved, closed), and conversational reply threads.
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class Grievance(TenantBase):
    """A formal grievance or issue raised by a teacher, parent, or student."""

    __tablename__ = "grievances"
    __table_args__ = (
        Index("ix_grievances_school_status", "school_id", "status"),
        Index("ix_grievances_school_raised_by", "school_id", "raised_by_id"),
        Index("ix_grievances_school_assigned_to", "school_id", "assigned_to_id"),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="general")
    raised_by_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    raised_by_role: Mapped[str] = mapped_column(String(30), nullable=False)
    raised_by_name: Mapped[str] = mapped_column(String(120), nullable=False)

    student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=True, index=True
    )
    student_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    enrolment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("enrolments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    assigned_to_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=True, index=True
    )
    assigned_to_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    replies: Mapped[list["GrievanceReply"]] = relationship(
        "GrievanceReply",
        back_populates="grievance",
        cascade="all, delete-orphan",
        order_by="GrievanceReply.created_at.asc()",
    )
    assigned_employee = relationship("Employee", foreign_keys=[assigned_to_id], lazy="joined")
    student = relationship("Student", foreign_keys=[student_id], lazy="joined")
    enrolment = relationship("Enrolment", foreign_keys=[enrolment_id], lazy="joined")
    raised_by_user = relationship("User", foreign_keys=[raised_by_id], lazy="joined")


class GrievanceReply(TenantBase):
    """A response or progress note on a grievance thread."""

    __tablename__ = "grievance_replies"
    __table_args__ = (
        Index("ix_grievance_replies_grievance", "school_id", "grievance_id"),
    )

    grievance_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("grievances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    author_role: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="replies")
    author = relationship("User", foreign_keys=[author_id], lazy="joined")
