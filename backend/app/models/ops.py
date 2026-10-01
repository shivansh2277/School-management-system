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
    select,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    AttendanceStatus,
    LeaveStatus,
    LeaveType,
    NoticeAudience,
)


class Attendance(TenantBase):
    """One day, one child, one mark.

    Keyed to the enrolment, not the student. Attendance is a fact about a
    *year* (§3.2): keyed to the student, promoting 10-A to 11-A silently
    re-parents every past mark to the new class, which is the defect the
    enrolment split exists to fix.
    """

    __tablename__ = "attendance"
    __table_args__ = (
        # §5.8.9: one record per child per date. Marking is idempotent, which
        # matters most for the mobile app resubmitting on a poor connection.
        UniqueConstraint("enrolment_id", "date", name="uq_attendance_enrolment_date"),
        Index("ix_attendance_date", "date"),
        Index("ix_attendance_enrolment_date", "enrolment_id", "date"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = enum_col(AttendanceStatus, nullable=False)
    # Nullable: a row written by an approved leave request was not marked by a
    # teacher, and naming one who did not touch it would be worse than a null.
    marked_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    remarks: Mapped[str | None] = mapped_column(String(200))
    # A correction is a different act from marking, and in a dispute about
    # where a child was, "who changed this, and when" is the question. The why
    # goes to the audit log, which already refuses to record it without one.
    corrected_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    enrolment = relationship("Enrolment", lazy="joined")


class Holiday(TenantBase):
    """A day or date-range the school or specific sections are shut.

    Attendance needs it to refuse marking, and the attendance percentage needs
    it for the denominator — counting a Diwali break as days absent is the
    reporting bug §5.8.9 warns about. Timetable will read the same rows.
    """

    __tablename__ = "holidays"
    __table_args__ = (
        Index("ix_holiday_dates", "school_id", "start_date", "end_date"),
    )

    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    # Kept for backward compatibility with existing single-day queries
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_school_wide: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default=text("'active'")
    )
    created_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    cancelled_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    academic_year = relationship("AcademicYear", lazy="joined")
    class_sections = relationship(
        "ClassSection", secondary="holiday_class_sections", lazy="selectin"
    )
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id], lazy="joined")

    def __init__(self, **kwargs):
        if "date" in kwargs and "start_date" not in kwargs:
            kwargs["start_date"] = kwargs["date"]
        if "start_date" in kwargs and "date" not in kwargs:
            kwargs["date"] = kwargs["start_date"]
        if "start_date" in kwargs and "end_date" not in kwargs:
            kwargs["end_date"] = kwargs["start_date"]
        elif "date" in kwargs and "end_date" not in kwargs:
            kwargs["end_date"] = kwargs["date"]
        super().__init__(**kwargs)


class HolidayClassSection(TenantBase):
    """Associates a holiday with specific class sections when not school-wide."""

    __tablename__ = "holiday_class_sections"
    __table_args__ = (
        UniqueConstraint("holiday_id", "class_section_id", name="uq_holiday_class_section"),
    )

    holiday_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("holidays.id", ondelete="CASCADE"), nullable=False
    )
    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False
    )

    holiday = relationship("Holiday", lazy="joined", overlaps="class_sections")
    class_section = relationship("ClassSection", lazy="joined", overlaps="class_sections")



class StudentLeaveRequest(TenantBase):
    """A guardian asking for a child to be away (§5.8.5).

    Approving it writes the attendance rows for the range, so "approved leave"
    and "what the register says" cannot disagree.
    """

    __tablename__ = "student_leave_requests"
    __table_args__ = (
        CheckConstraint("to_date >= from_date", name="ck_leave_range"),
        Index("ix_leave_enrolment_status", "enrolment_id", "status"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False
    )
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[LeaveType] = enum_col(LeaveType, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[LeaveStatus] = enum_col(
        LeaveStatus, nullable=False, default=LeaveStatus.applied
    )
    requested_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    decided_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)


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
    attachment_url: Mapped[str | None] = mapped_column(String(500))


class HomeworkSubmission(TenantBase):
    __tablename__ = "homework_submissions"
    __table_args__ = (UniqueConstraint("homework_id", "enrolment_id", name="uq_submission"),)

    homework_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("homework.id"), nullable=False)
    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(200), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    enrolment = relationship("Enrolment", lazy="joined")
    homework = relationship("Homework", lazy="joined")

    @hybrid_property
    def student_id(self) -> int | None:
        return self.enrolment.student_id if self.enrolment else None

    @student_id.inplace.expression
    @classmethod
    def _student_id_expression(cls):
        from app.models.enrolment import Enrolment
        return (
            select(Enrolment.student_id)
            .where(Enrolment.id == cls.enrolment_id)
            .correlate_except(Enrolment)
            .scalar_subquery()
        )


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
    # A notice is what appears on the board; a message is what goes out to
    # people. Publishing can do both, and this is the link — one nullable
    # column rather than a second notice-shaped concept living beside this one
    # with its own audience enum and its own delivery record.
    message_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("messages.id"))
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="General")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str | None] = mapped_column(String(300), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
