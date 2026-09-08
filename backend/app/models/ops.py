from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
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
    """A day the school is shut.

    Attendance needs it to refuse marking, and the attendance percentage needs
    it for the denominator — counting a Diwali break as days absent is the
    reporting bug §5.8.9 warns about. Timetable will read the same rows.
    """

    __tablename__ = "holidays"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "date", name="uq_holiday_date"),
    )

    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)


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
    # A notice is what appears on the board; a message is what goes out to
    # people. Publishing can do both, and this is the link — one nullable
    # column rather than a second notice-shaped concept living beside this one
    # with its own audience enum and its own delivery record.
    message_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("messages.id"))
