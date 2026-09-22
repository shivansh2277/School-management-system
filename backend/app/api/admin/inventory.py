from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.schemas.inventory import (
    InventoryStatsOut,
    StockAdjustIn,
    StockItemCreate,
    StockItemOut,
    StockItemUpdate,
    StockRequestCreate,
    StockRequestDecide,
    StockRequestOut,
)
from app.services import inventory as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/inventory",
    tags=["admin-inventory"],
    dependencies=[Depends(module_enabled("inventory"))],
)

reader = require_permission("inventory.item.read", school_wide=True)
writer = require_permission("inventory.item.write", school_wide=True)
requester = require_permission("inventory.request.create", school_wide=True)
approver = require_permission("inventory.request.approve", school_wide=True)


@router.get("/stats", response_model=InventoryStatsOut)
def get_stats(
    user: User = Depends(reader), db: Session = Depends(get_db)
) -> InventoryStatsOut:
    return svc.get_overview_stats(db, user.school_id)


@router.get("/items", response_model=list[StockItemOut])
def list_items(
    category: str | None = None,
    location: str | None = None,
    low_stock_only: bool = False,
    has_discrepancy_only: bool = False,
    search: str | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[StockItemOut]:
    return svc.list_items(
        db,
        user.school_id,
        category=category,
        location=location,
        low_stock_only=low_stock_only,
        has_discrepancy_only=has_discrepancy_only,
        search=search,
    )


@router.post(
    "/items",
    response_model=StockItemOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(writer)],
)
def create_item(
    body: StockItemCreate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> StockItemOut:
    return svc.create_item(db, user, body)


@router.patch(
    "/items/{item_id}",
    response_model=StockItemOut,
    dependencies=[Depends(writer)],
)
def update_item(
    item_id: int,
    body: StockItemUpdate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> StockItemOut:
    return svc.update_item(db, user, item_id, body)


@router.patch(
    "/items/{item_id}/adjust",
    response_model=StockItemOut,
    dependencies=[Depends(writer)],
)
def adjust_stock(
    item_id: int,
    body: StockAdjustIn,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> StockItemOut:
    return svc.adjust_quantity(db, user, item_id, body)


@router.get("/requests", response_model=list[StockRequestOut])
def list_requests(
    status: str | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[StockRequestOut]:
    return svc.list_requests(db, user.school_id, status_filter=status)


@router.post(
    "/requests",
    response_model=StockRequestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requester)],
)
def create_request(
    body: StockRequestCreate,
    user: User = Depends(requester),
    db: Session = Depends(get_db),
) -> StockRequestOut:
    return svc.create_request(db, user, body)


@router.post(
    "/requests/{request_id}/decide",
    response_model=StockRequestOut,
    dependencies=[Depends(approver)],
)
def decide_request(
    request_id: int,
    body: StockRequestDecide,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> StockRequestOut:
    return svc.decide_request(db, user, request_id, body)
