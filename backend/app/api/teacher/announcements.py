from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import Notice, NoticeAudience, User
from app.schemas.common import AnnouncementCreate, NoticeCreate, NoticeOut
from app.services import notices as svc

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("comms.notice.read")


@router.post("/announcements", response_model=NoticeOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("comms.notice.publish"))])
def publish(
    body: AnnouncementCreate, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> NoticeOut:
    # Audience is not forced silently: anything other than "class" is a 403, so a
    # teacher can never broadcast beyond their section (BLUEPRINT §8 Notices).
    return svc.publish(
        db,
        user,
        NoticeCreate(
            title=body.title,
            body=body.body,
            audience=body.audience or NoticeAudience.class_,
            class_section_id=body.class_section_id,
        ),
    )


@router.get("/announcements", response_model=list[NoticeOut])
def mine(user: User = Depends(teacher_only), db: Session = Depends(get_db)) -> list[NoticeOut]:
    items = list(
        db.scalars(
            select(Notice)
            .where(Notice.published_by == user.id)
            .order_by(Notice.published_at.desc())
        )
    )
    return svc.to_out(db, items)
