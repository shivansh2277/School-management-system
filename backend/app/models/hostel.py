from datetime import date, datetime, time
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import DayOfWeek, Gender


class Hostel(TenantBase):
    """A residential building / facility belonging to the school."""

    __tablename__ = "hostels"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_hostel_code"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[Gender] = enum_col(Gender, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, inactive, maintenance
    description: Mapped[str | None] = mapped_column(Text)

    floors = relationship("HostelFloor", back_populates="hostel", cascade="all, delete-orphan", order_by="HostelFloor.floor_number")
    rooms = relationship("HostelRoom", back_populates="hostel", cascade="all, delete-orphan")
    admissions = relationship("HostelAdmission", back_populates="hostel", cascade="all, delete-orphan")


class HostelFloor(TenantBase):
    """A floor within a hostel."""

    __tablename__ = "hostel_floors"
    __table_args__ = (
        UniqueConstraint("school_id", "hostel_id", "floor_number", name="uq_hostel_floor_number"),
    )

    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    floor_name: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    hostel = relationship("Hostel", back_populates="floors")
    rooms = relationship("HostelRoom", back_populates="floor", cascade="all, delete-orphan", order_by="HostelRoom.room_number")


class HostelRoom(TenantBase):
    """A room on a floor with configurable bed capacity."""

    __tablename__ = "hostel_rooms"
    __table_args__ = (
        UniqueConstraint("school_id", "hostel_id", "room_number", name="uq_hostel_room_number"),
        CheckConstraint("capacity > 0", name="ck_room_capacity_positive"),
    )

    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False, index=True)
    floor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_floors.id", ondelete="CASCADE"), nullable=False, index=True)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    room_type: Mapped[str] = mapped_column(String(30), nullable=False, default="standard")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")  # available, full, maintenance

    hostel = relationship("Hostel", back_populates="rooms")
    floor = relationship("HostelFloor", back_populates="rooms")
    beds = relationship("HostelBed", back_populates="room", cascade="all, delete-orphan", order_by="HostelBed.bed_number")


class HostelBed(TenantBase):
    """An explicit bed record inside a room."""

    __tablename__ = "hostel_beds"
    __table_args__ = (
        UniqueConstraint("school_id", "room_id", "bed_number", name="uq_hostel_bed_number"),
    )

    room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    bed_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")  # available, occupied, maintenance

    room = relationship("HostelRoom", back_populates="beds")
    allocations = relationship("BedAllocation", back_populates="bed", cascade="all, delete-orphan")


class HostelAdmission(TenantBase):
    """Lifetime stay record of a student admitted to a hostel."""

    __tablename__ = "hostel_admissions"
    __table_args__ = (
        Index("ix_hostel_admission_student", "school_id", "student_id", "status"),
        Index("ix_hostel_admission_hostel", "school_id", "hostel_id", "status"),
        Index(
            "uq_active_hostel_admission",
            "school_id",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id"), nullable=False)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, vacated, cancelled
    exit_date: Mapped[date | None] = mapped_column(Date)
    exit_reason: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    admitted_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    exited_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    student = relationship("Student", lazy="joined")
    hostel = relationship("Hostel", back_populates="admissions", lazy="joined")
    allocations = relationship("BedAllocation", back_populates="admission", cascade="all, delete-orphan")


class BedAllocation(TenantBase):
    """Historical and active bed allocations for a hostel admission."""

    __tablename__ = "bed_allocations"
    __table_args__ = (
        Index(
            "uq_active_bed_allocation",
            "bed_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
        Index(
            "uq_active_admission_allocation",
            "admission_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    admission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_admissions.id", ondelete="CASCADE"), nullable=False, index=True)
    bed_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_beds.id"), nullable=False, index=True)
    allocated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vacated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allocated_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    remarks: Mapped[str | None] = mapped_column(Text)

    admission = relationship("HostelAdmission", back_populates="allocations")
    bed = relationship("HostelBed", back_populates="allocations", lazy="joined")


class HostelAttendance(TenantBase):
    """Residential 8:00 PM evening attendance marked by Wardens."""

    __tablename__ = "hostel_attendances"
    __table_args__ = (
        UniqueConstraint("school_id", "hostel_id", "student_id", "attendance_date", name="uq_hostel_attendance"),
        Index("ix_hostel_att_date", "school_id", "hostel_id", "attendance_date"),
    )

    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    admission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_admissions.id"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # present, absent, on_leave, on_outing
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(20, 0, 0))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)

    student = relationship("Student", lazy="joined")
    recorded_by = relationship("User", lazy="joined")


class HostelLeaveRequest(TenantBase):
    """Leave and outing requests initiated by parents and approved by wardens."""

    __tablename__ = "hostel_leave_requests"
    __table_args__ = (
        Index("ix_hostel_leaves_student", "school_id", "student_id", "status"),
        Index("ix_hostel_leaves_hostel", "school_id", "hostel_id", "status"),
    )

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    admission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostel_admissions.id"), nullable=False)
    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)  # leave, outing
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    out_time: Mapped[time | None] = mapped_column(Time)
    expected_return_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_return_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    parent_guardian_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guardians.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, approved, rejected, departed, returned
    approved_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remarks: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    returned_recorded_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    student = relationship("Student", lazy="joined")
    guardian = relationship("Guardian", lazy="joined")
    approved_by = relationship("User", foreign_keys=[approved_by_id], lazy="joined")


class HostelMessMenu(TenantBase):
    """School-wide weekly mess menu managed and published by Chief Provost."""

    __tablename__ = "hostel_mess_menus"
    __table_args__ = (
        UniqueConstraint("school_id", "day_of_week", name="uq_mess_menu_day"),
    )

    day_of_week: Mapped[DayOfWeek] = enum_col(DayOfWeek, nullable=False)
    breakfast: Mapped[str] = mapped_column(Text, nullable=False)
    lunch: Mapped[str] = mapped_column(Text, nullable=False)
    snacks: Mapped[str] = mapped_column(Text, nullable=False)
    dinner: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    updated_by = relationship("User", lazy="joined")


class HostelComplaint(TenantBase):
    """Hostel maintenance, cleanliness, and facilities complaints."""

    __tablename__ = "hostel_complaints"
    __table_args__ = (
        Index("ix_hostel_complaints_hostel", "school_id", "hostel_id", "status"),
    )

    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("students.id"))
    room_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hostel_rooms.id"))
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # plumbing, electrical, cleanliness, mess_food, noise, other
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, in_progress, resolved, dismissed
    resolution_remarks: Mapped[str | None] = mapped_column(Text)
    resolved_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    hostel = relationship("Hostel", lazy="joined")
    student = relationship("Student", lazy="joined")
    room = relationship("HostelRoom", lazy="joined")


class HostelIncident(TenantBase):
    """Disciplinary and welfare incidents recorded in hostels."""

    __tablename__ = "hostel_incidents"
    __table_args__ = (
        Index("ix_hostel_incidents_hostel", "school_id", "hostel_id", "incident_date"),
    )

    hostel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hostels.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("students.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    incident_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_taken: Mapped[str | None] = mapped_column(Text)
    reported_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")  # open, investigating, resolved, closed

    hostel = relationship("Hostel", lazy="joined")
    student = relationship("Student", lazy="joined")
    reported_by = relationship("User", lazy="joined")


class HostelNotice(TenantBase):
    """Hostel-wide broadcast circulars and notices."""

    __tablename__ = "hostel_notices"
    __table_args__ = (
        Index("ix_hostel_notices_hostel", "school_id", "hostel_id", "is_active"),
    )

    hostel_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hostels.id"))  # None for school-wide hostel notice
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")  # normal, important, urgent
    posted_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    hostel = relationship("Hostel", lazy="joined")
    posted_by = relationship("User", lazy="joined")
