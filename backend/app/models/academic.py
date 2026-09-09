from datetime import date, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import DayOfWeek, SubstitutionStatus


class ClassSection(TenantBase):
    __tablename__ = "class_sections"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id", "class_name", "section", name="uq_class_section"
        ),
    )

    class_name: Mapped[str] = mapped_column(String(8), nullable=False)
    section: Mapped[str] = mapped_column(String(4), nullable=False)
    class_teacher_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    capacity: Mapped[int | None] = mapped_column()
    stream: Mapped[str | None] = mapped_column(String(20))  # classes 11-12
    room: Mapped[str | None] = mapped_column(String(20))

    @property
    def label(self) -> str:
        return f"{self.class_name}-{self.section}"


class Subject(TenantBase):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_subject_code"),)

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    code: Mapped[str] = mapped_column(String(12), nullable=False)


class ClassSubjectTeacher(TenantBase):
    __tablename__ = "class_subject_teacher"
    __table_args__ = (UniqueConstraint("class_section_id", "subject_id", name="uq_cst"),)

    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)


class SchoolPeriod(TenantBase):
    """Bell timings, once per school instead of once per slot.

    v0 repeated `start_time` and `end_time` on all 360 slots, so moving the
    lunch bell by ten minutes meant updating every row that happened to be at
    that period. §5.7.3 calls this a setup screen; this is the table behind it.
    """

    __tablename__ = "school_periods"
    __table_args__ = (
        UniqueConstraint("school_id", "period_no", name="uq_school_period_no"),
    )

    period_no: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    name: Mapped[str | None] = mapped_column(String(20))
    # A break is on the grid but nothing is taught in it, so it is never a
    # clash and never counts towards a teacher's load.
    is_break: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TimetableSlot(TenantBase):
    __tablename__ = "timetable_slots"
    __table_args__ = (
        # A section cannot be taught two things at once. v0 had this and it is
        # kept deliberately (§5.7.9).
        UniqueConstraint(
            "class_section_id", "day_of_week", "period_id", name="uq_timetable_slot"
        ),
        # The access path for "is this teacher free then?", which is now asked
        # on every save rather than never.
        Index("ix_slot_teacher_day_period", "teacher_id", "day_of_week", "period_id"),
    )

    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    day_of_week: Mapped[DayOfWeek] = enum_col(DayOfWeek, nullable=False)
    period_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("school_periods.id"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)
    room: Mapped[str | None] = mapped_column(String(20))

    period = relationship("SchoolPeriod", lazy="joined")
    class_section = relationship("ClassSection", lazy="joined")


class Substitution(TenantBase):
    """One period, one day, covered by somebody else (§5.7.9).

    A row per date rather than an edit to the slot: the timetable did not
    change, one lesson did, and next Tuesday the usual teacher is back.
    """

    __tablename__ = "substitutions"
    __table_args__ = (
        UniqueConstraint("timetable_slot_id", "date", name="uq_substitution_slot_date"),
        Index("ix_substitution_date", "date"),
    )

    timetable_slot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("timetable_slots.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    absent_teacher_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id"), nullable=False
    )
    # Null while nobody has been found. That is the state worth reporting:
    # §5.7.10 calls unfilled substitutions the operational number that matters
    # most, because it means a class sat unattended.
    substitute_teacher_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("employees.id")
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubstitutionStatus] = enum_col(
        SubstitutionStatus, nullable=False, default=SubstitutionStatus.pending
    )

    slot = relationship("TimetableSlot", lazy="joined")
