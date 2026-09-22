from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.schemas.inventory import (
    StockConsumeIn,
    StockItemOut,
    StockRequestCreate,
    StockRequestOut,
)
from app.services import inventory as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/teacher/stock", tags=["teacher-stock"])

teacher_access = require_permission("inventory.request.create", "academics.class.read")


@router.get("/items", response_model=list[StockItemOut])
def get_teacher_stock_items(
    category: str | None = None,
    location: str | None = None,
    search: str | None = None,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> list[StockItemOut]:
    """Provides teaching staff with immediate visibility into lab, classroom, and teaching supplies."""
    return svc.list_items(
        db,
        user.school_id,
        category=category,
        location=location,
        low_stock_only=False,
        search=search,
    )


@router.post(
    "/flag",
    response_model=StockRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def flag_diminishing_stock(
    body: StockRequestCreate,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> StockRequestOut:
    """Allows teachers to flag diminishing supplies (e.g. chalks, chemicals, kits) directly from the classroom or lab."""
    # Ensure flag_type is marked diminishing if not set
    if not body.flag_type:
        body.flag_type = "diminishing"
    return svc.create_request(db, user, body)


@router.post(
    "/{item_id}/consume",
    response_model=StockItemOut,
    status_code=status.HTTP_200_OK,
)
def consume_teacher_stock(
    item_id: int,
    body: StockConsumeIn,
    user: User = Depends(teacher_access),
    db: Session = Depends(get_db),
) -> StockItemOut:
    """Records stock usage/consumption by teaching staff in classroom or lab."""
    return svc.consume_stock(db, user, item_id, body)
