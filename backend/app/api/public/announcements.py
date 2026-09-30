"""Public announcements API for Sunrise School public-facing website.

Unauthenticated endpoint: prospective parents, students, and community members
can view published institutional notices and news announcements.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Notice, School, SchoolStatus
from app.schemas.common import NoticeOut
from app.services import notices as svc

router = APIRouter(prefix="/public", tags=["public-announcements"])


def _school(db: Session, school_code: str) -> School:
    school = db.scalar(select(School).where(School.code == school_code))
    if school is None or school.status is not SchoolStatus.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such school")
    return school


def _default_school(db: Session) -> School:
    school = db.scalar(select(School).where(School.code == "SPS"))
    if not school:
        school = db.scalar(select(School).where(School.status == SchoolStatus.active).order_by(School.id.asc()))
    if not school:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School not configured")
    return school


@router.get("/{school_code}/announcements", response_model=list[NoticeOut])
def list_public_announcements(
    school_code: str,
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[NoticeOut]:
    school = _school(db, school_code)
    today = date.today()
    query = (
        select(Notice)
        .where(
            Notice.school_id == school.id,
            Notice.is_public == True,  # noqa: E712
        )
    )
    if category and category.lower() != "all":
        query = query.where(Notice.category.ilike(category))

    items = list(
        db.scalars(
            query.order_by(Notice.is_pinned.desc(), Notice.published_at.desc())
        )
    )
    # Filter out expired notices
    valid_items = [
        item for item in items
        if item.expiry_date is None or item.expiry_date >= today
    ]
    return svc.to_out(db, valid_items)


@router.get("/{school_code}/announcements/{announcement_id}", response_model=NoticeOut)
def get_public_announcement(
    school_code: str,
    announcement_id: int,
    db: Session = Depends(get_db),
) -> NoticeOut:
    school = _school(db, school_code)
    notice = db.scalar(
        select(Notice).where(
            Notice.id == announcement_id,
            Notice.school_id == school.id,
            Notice.is_public == True,  # noqa: E712
        )
    )
    if not notice:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Announcement not found")
    return svc.to_out(db, [notice])[0]


@router.get("/announcements", response_model=list[NoticeOut])
def list_default_public_announcements(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[NoticeOut]:
    school = _default_school(db)
    return list_public_announcements(school.code, category=category, db=db)


@router.get("/announcements/{announcement_id}", response_model=NoticeOut)
def get_default_public_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
) -> NoticeOut:
    school = _default_school(db)
    return get_public_announcement(school.code, announcement_id=announcement_id, db=db)
