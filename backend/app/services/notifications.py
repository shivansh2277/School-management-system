"""In-app notifications for users across mobile and web interfaces."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import InAppNotification


def notify_user(
    db: Session,
    school_id: int,
    user_id: int,
    title: str,
    message: str,
    category: str,
    link_url: str | None = None,
) -> InAppNotification:
    notification = InAppNotification(
        school_id=school_id,
        user_id=user_id,
        title=title.strip(),
        message=message.strip(),
        category=category.strip(),
        link_url=link_url.strip() if link_url else None,
        is_read=False,
    )
    db.add(notification)
    db.flush()
    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
) -> list[InAppNotification]:
    q = (
        select(InAppNotification)
        .where(InAppNotification.user_id == user_id)
        .order_by(InAppNotification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        q = q.where(InAppNotification.is_read.is_(False))
    return list(db.scalars(q))


def mark_as_read(db: Session, notification_id: int, user_id: int) -> InAppNotification | None:
    row = db.scalar(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id,
        )
    )
    if row is not None:
        row.is_read = True
        db.flush()
    return row
