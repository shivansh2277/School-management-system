"""Receptionist operational models: Found & Lost, Student Passes, Meeting Slips, and Directory."""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class FoundItem(TenantBase):
    """Items found on school premises and managed by the receptionist."""

    __tablename__ = "found_items"
    __table_args__ = (
        Index("ix_found_items_school_status", "school_id", "status"),
        Index("ix_found_items_school_date", "school_id", "found_date"),
    )

    item_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    found_location: Mapped[str] = mapped_column(String(150), nullable=False)
    found_date: Mapped[date] = mapped_column(Date, nullable=False)
    found_time: Mapped[str | None] = mapped_column(String(20), nullable=True)

    recorded_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    recorded_by_name: Mapped[str] = mapped_column(String(120), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="reported")  # reported, broadcasted, collected
    broadcasted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Handover / collection details
    claimed_by_student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=True, index=True
    )
    claimed_by_student_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    claimed_by_admission_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    claimed_by_class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    handover_photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    handover_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_by_staff_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    collected_by_staff_name: Mapped[str | None] = mapped_column(String(120), nullable=True)


class StudentAuthorizedPerson(TenantBase):
    """Permanent authorized pickup roster on the student master record."""

    __tablename__ = "student_authorized_persons"
    __table_args__ = (
        Index("ix_student_auth_persons_student", "school_id", "student_id"),
    )

    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship: Mapped[str] = mapped_column(String(60), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    id_proof_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_proof_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudentPass(TenantBase):
    """One-time student gate pass generated on behalf of a parent."""

    __tablename__ = "student_passes"
    __table_args__ = (
        Index("ix_student_passes_school_date", "school_id", "pass_date"),
        Index("ix_student_passes_student", "school_id", "student_id"),
    )

    pass_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False, index=True
    )
    student_name: Mapped[str] = mapped_column(String(120), nullable=False)
    admission_no: Mapped[str] = mapped_column(String(50), nullable=False)
    class_name: Mapped[str | None] = mapped_column(String(60), nullable=True)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_person_name: Mapped[str] = mapped_column(String(120), nullable=False)
    pickup_person_relation: Mapped[str] = mapped_column(String(60), nullable=False)
    pickup_person_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    pickup_person_id_proof: Mapped[str | None] = mapped_column(String(80), nullable=True)

    pass_date: Mapped[date] = mapped_column(Date, nullable=False)
    pass_time: Mapped[str] = mapped_column(String(20), nullable=False)

    issued_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    issued_by_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="issued")  # issued, departed, cancelled
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class PrincipalMeetingRequest(TenantBase):
    """Visitor meeting slips/requests for the Principal."""

    __tablename__ = "principal_meeting_requests"
    __table_args__ = (
        Index("ix_principal_meetings_school_status", "school_id", "status"),
        Index("ix_principal_meetings_school_date", "school_id", "meeting_date"),
    )

    slip_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    visitor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    visitor_organization: Mapped[str | None] = mapped_column(String(120), nullable=True)
    student_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    student_admission_no: Mapped[str | None] = mapped_column(String(50), nullable=True)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")  # pending, accepted, declined, waiting, completed, cancelled
    wait_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(120), nullable=False)


class TeacherMeetingRequest(TenantBase):
    """Visitor meeting slips/requests for any School Teacher."""

    __tablename__ = "teacher_meeting_requests"
    __table_args__ = (
        Index("ix_teacher_meetings_school_status", "school_id", "status"),
        Index("ix_teacher_meetings_teacher", "school_id", "teacher_id"),
    )

    slip_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False, index=True
    )
    teacher_name: Mapped[str] = mapped_column(String(120), nullable=False)

    visitor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    visitor_relation: Mapped[str | None] = mapped_column(String(60), nullable=True)
    student_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    student_admission_no: Mapped[str | None] = mapped_column(String(50), nullable=True)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")  # pending, accepted, declined, completed, cancelled
    response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(120), nullable=False)


class DirectoryContact(TenantBase):
    """Important emergency and administrative contacts for the school."""

    __tablename__ = "directory_contacts"
    __table_args__ = (
        Index("ix_directory_contacts_school_category", "school_id", "category"),
    )

    category: Mapped[str] = mapped_column(String(60), nullable=False, default="Emergency")
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    designation_or_department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone_primary: Mapped[str] = mapped_column(String(40), nullable=False)
    phone_secondary: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    operating_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_emergency: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
