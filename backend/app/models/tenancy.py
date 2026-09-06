"""Tenancy and session: the two entities every other table hangs off.

A `School` is one independent customer, not a branch (ERP_BLUEPRINT §0.2b).
An `AcademicYear` is a real session with a lifecycle, not the `String(9)` that
v0 denormalised onto `class_sections` and `school_settings` (§3.1).
"""

from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedBase, enum_col
from app.models.enums import AcademicYearStatus, SchoolStatus


class School(TimestampedBase):
    """One customer. The only table without a `school_id` of its own."""

    __tablename__ = "schools"

    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[SchoolStatus] = enum_col(
        SchoolStatus, nullable=False, default=SchoolStatus.active
    )

    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(80))
    pincode: Mapped[str | None] = mapped_column(String(10))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))
    website: Mapped[str | None] = mapped_column(String(200))

    # Branding — level 1 customisation (§3.15).
    logo_url: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(9))

    board: Mapped[str | None] = mapped_column(String(20))  # CBSE for now (§0.5)
    affiliation_no: Mapped[str | None] = mapped_column(String(40))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<School {self.code}>"


class AcademicYear(TimestampedBase):
    """A session. Several may be open at once — 2026-27 active while 2027-28
    takes admissions and 2025-26 is closing is the normal state of a school in
    January, which the v0 string could not express.
    """

    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_academic_year_code"),
        # Exactly one current year per school, enforced by the database rather
        # than by application code that can be forgotten (§3.1). A partial
        # unique index works on both Postgres and SQLite.
        Index(
            "uq_academic_year_current",
            "school_id",
            unique=True,
            postgresql_where=text("is_current"),
            sqlite_where=text("is_current"),
        ),
    )

    school_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("schools.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(9), nullable=False)  # "2026-27"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AcademicYearStatus] = enum_col(
        AcademicYearStatus, nullable=False, default=AcademicYearStatus.planning
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    promotion_completed_at: Mapped[date | None] = mapped_column(Date)
    result_published_at: Mapped[date | None] = mapped_column(Date)
    closed_at: Mapped[date | None] = mapped_column(Date)

    @property
    def is_writable(self) -> bool:
        """Closed and archived years reject writes (§3.1)."""
        return self.status not in (
            AcademicYearStatus.closed,
            AcademicYearStatus.archived,
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AcademicYear {self.code}>"
