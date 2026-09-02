from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import Notice, User, UserRole
from app.schemas.common import NoticeCreate, NoticeOut
from app.services import notices as svc

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(UserRole.admin)


@router.get("/notices", response_model=list[NoticeOut])
def list_notices(
    user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> list[NoticeOut]:
    items = list(db.scalars(select(Notice).order_by(Notice.published_at.desc())))
    return svc.to_out(db, items)


@router.post("/notices", response_model=NoticeOut, status_code=status.HTTP_201_CREATED)
def publish(
    body: NoticeCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> NoticeOut:
    return svc.publish(db, user, body)


@router.delete("/notices/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    notice_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> Response:
    svc.delete(db, notice_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
