from datetime import time

from sqlalchemy import BigInteger, ForeignKey, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import DayOfWeek


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


class TimetableSlot(TenantBase):
    __tablename__ = "timetable_slots"
    __table_args__ = (
        UniqueConstraint("class_section_id", "day_of_week", "period_no", name="uq_timetable_slot"),
    )

    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    day_of_week: Mapped[DayOfWeek] = enum_col(DayOfWeek, nullable=False)
    period_no: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)
    room: Mapped[str | None] = mapped_column(String(20))
