"""Teacher In-App Notifications API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.services import notifications as notif_svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/teacher", tags=["teacher"])

can_view = require_permission("teacher.leave.view")


@router.get("/notifications", dependencies=[Depends(can_view)])
def list_notifications(
    unread_only: bool = False,
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> list[dict]:
    items = notif_svc.get_user_notifications(
        db, user.id, unread_only=unread_only, limit=50
    )
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "link_url": n.link_url,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]


@router.patch("/notifications/{notification_id}/read", dependencies=[Depends(can_view)])
def mark_notification_read(
    notification_id: int,
    user: User = Depends(can_view),
    db: Session = Depends(get_db),
) -> dict:
    n = notif_svc.mark_as_read(db, notification_id, user.id)
    return {"status": "ok", "is_read": n.is_read if n else True}
