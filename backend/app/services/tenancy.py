"""Tenant and academic-year lookups.

Every request belongs to exactly one school, taken from the authenticated
user's `school_id` and never from a client-supplied parameter — a tenant id
that a caller can choose is not a tenant boundary.
"""

from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicYear, AcademicYearStatus, School, SchoolStatus, User
from app.models.base import TenantBase

T = TypeVar("T", bound=TenantBase)


def get_owned(
    db: Session, model: type[T], row_id: int | None, user: User, *, what: str | None = None
) -> T:
    """One row of `model`, by id, proven to belong to the caller's school.

    Use this wherever an id arrives from outside — a path parameter, a query
    string, a request body. `db.get(Model, id)` on its own answers "does this
    row exist anywhere in the product", which is a different and much larger
    question than "may this customer touch it". Ids are sequential integers, so
    the difference is one `curl` away.

    Missing and not-yours are deliberately the same 404. Which schools exist,
    and which ids they own, is not something to confirm to a caller — the same
    choice `module_enabled` and `/public/{school_code}` already make.

    A row reached *through* an already-owned parent does not need this: if the
    exam paper was fetched with `get_owned`, its marks are its own. Checking
    again is harmless but adds noise; checking at the boundary is what matters.
    """
    row = db.get(model, row_id) if row_id is not None else None
    if row is None or row.school_id != user.school_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"{what or model.__name__} not found"
        )
    return row


def school_for(db: Session, user: User) -> School:
    school = db.get(School, user.school_id)
    if school is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No school for this user")
    if school.status is SchoolStatus.suspended:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This school is suspended")
    return school


def current_year(db: Session, school_id: int) -> AcademicYear:
    """The one year flagged current for this school.

    A partial unique index guarantees at most one, so this cannot silently pick
    an arbitrary row when the data is inconsistent.
    """
    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    )
    if year is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This school has no current academic year",
        )
    return year


def assert_writable(year: AcademicYear) -> None:
    """Closed and archived years reject writes (ERP_BLUEPRINT §3.1)."""
    if not year.is_writable:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Academic year {year.code} is {year.status} and cannot be modified",
        )


def set_current_year(db: Session, school_id: int, year_id: int) -> AcademicYear:
    """Move the current flag. Clears the old one first: the partial unique
    index would otherwise reject the second row mid-transaction.
    """
    for existing in db.scalars(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
        )
    ):
        existing.is_current = False
    db.flush()

    year = db.get(AcademicYear, year_id)
    if year is None or year.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    if year.status in (AcademicYearStatus.closed, AcademicYearStatus.archived):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A closed year cannot be made current"
        )
    year.is_current = True
    db.commit()
    return year
