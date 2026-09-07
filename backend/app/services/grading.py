"""Grading scales and the grade a percentage earns.

Two rules carry the weight here.

**A scale is a version, not a setting.** §0.8 freezes a published report card
by snapshotting the grade and the scale version behind it. That is only
possible if the bands live under a row a publication can cite. Before this,
bands hung off the school, so editing "A1 starts at 91" to "A1 starts at 90"
re-graded every card the school had ever issued — silently, at read time.

**The lowest band must start at zero.** A scale whose floors are 91/81/71 and
nothing below leaves a child on 40% with no grade at all, and the report card
prints a blank where a D should be. Cheap to check on save, invisible until a
parent asks.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GradeBand, GradingScale


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def active_scale(db: Session, school_id: int) -> GradingScale | None:
    return db.scalar(
        select(GradingScale).where(
            GradingScale.school_id == school_id, GradingScale.is_active.is_(True)
        )
    )


def bands_in(db: Session, scale_id: int) -> list[GradeBand]:
    """Bands of one scale, highest floor first — the order `grade_in` walks."""
    return list(
        db.scalars(
            select(GradeBand)
            .where(GradeBand.grading_scale_id == scale_id)
            .order_by(GradeBand.min_percent.desc())
        )
    )


def grade_in(db: Session, scale_id: int, percent: float | Decimal | None) -> str | None:
    """The grade this percentage earns on one specific scale.

    Takes a scale id rather than a school so a frozen report card can be
    re-read against the version it was issued under, years later, whatever the
    school has since changed.
    """
    if percent is None:
        return None
    value = Decimal(str(percent))
    for band in bands_in(db, scale_id):
        if value >= band.min_percent:
            return band.grade
    return None


def create(
    db: Session,
    school_id: int,
    *,
    name: str,
    bands: list[tuple[Decimal, str, str | None]],
    activate: bool = False,
) -> GradingScale:
    """A new scale at version 1, or the next version of an existing name."""
    latest = db.scalar(
        select(GradingScale)
        .where(GradingScale.school_id == school_id, GradingScale.name == name)
        .order_by(GradingScale.version.desc())
    )
    scale = GradingScale(
        school_id=school_id,
        name=name,
        version=(latest.version + 1) if latest else 1,
        is_active=False,
    )
    db.add(scale)
    db.flush()
    set_bands(db, scale, bands)
    if activate:
        activate_scale(db, scale)
    db.flush()
    return scale


def set_bands(
    db: Session, scale: GradingScale, bands: list[tuple[Decimal, str, str | None]]
) -> list[GradeBand]:
    """Replace a scale's bands wholesale.

    Refused once the scale is frozen: a cited version is a historical record,
    and the way to change the rule is a new version, which is what `create()`
    with the same name produces.
    """
    if scale.frozen_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{scale.name} v{scale.version} has been used on a published report "
            "card and can no longer be edited. Create the next version instead.",
        )
    if not bands:
        raise _bad("A grading scale needs at least one band")

    floors = [Decimal(str(f)) for f, _, _ in bands]
    if len(set(floors)) != len(floors):
        raise _bad("Two bands cannot start at the same percentage")
    if any(f < 0 or f > 100 for f in floors):
        raise _bad("A band must start between 0 and 100")
    if min(floors) != 0:
        raise _bad(
            "The lowest band must start at 0, otherwise a low mark earns no "
            "grade at all"
        )
    grades = [g for _, g, _ in bands]
    if len(set(grades)) != len(grades):
        raise _bad("Two bands cannot carry the same grade")

    for old in bands_in(db, scale.id):
        db.delete(old)
    db.flush()
    rows = [
        GradeBand(
            school_id=scale.school_id,
            grading_scale_id=scale.id,
            min_percent=Decimal(str(floor)),
            grade=grade,
            description=description,
        )
        for floor, grade, description in bands
    ]
    db.add_all(rows)
    db.flush()
    return rows


def activate_scale(db: Session, scale: GradingScale) -> GradingScale:
    """Put a scale in force, standing the previous one down.

    The database allows only one active scale per school, so the previous one
    is cleared and flushed first rather than left to collide.
    """
    current = active_scale(db, scale.school_id)
    if current is not None and current.id != scale.id:
        current.is_active = False
        db.flush()
    scale.is_active = True
    db.flush()
    return scale


def freeze(db: Session, scale: GradingScale) -> GradingScale:
    """Mark a scale as cited by a published document. Idempotent."""
    if scale.frozen_at is None:
        scale.frozen_at = datetime.now(UTC)
        db.flush()
    return scale
