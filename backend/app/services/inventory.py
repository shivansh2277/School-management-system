from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditAction, StockItem, StockRequest, User
from app.schemas.inventory import (
    CriticalAlertOut,
    InventoryStatsOut,
    StockAdjustIn,
    StockConsumeIn,
    StockItemCreate,
    StockItemOut,
    StockItemUpdate,
    StockRequestCreate,
    StockRequestDecide,
    StockRequestOut,
)
from app.services import audit


def to_item_out(item: StockItem) -> StockItemOut:
    return StockItemOut(
        id=item.id,
        school_id=item.school_id,
        name=item.name,
        category=item.category,
        location=item.location,
        unit=item.unit,
        current_quantity=item.current_quantity,
        min_quantity=item.min_quantity,
        unit_cost=item.unit_cost,
        is_critical=item.is_critical,
        has_discrepancy=item.has_discrepancy,
        discrepancy_notes=item.discrepancy_notes,
        is_low_stock=item.is_low_stock,
        last_checked_at=item.last_checked_at,
    )


def to_request_out(req: StockRequest) -> StockRequestOut:
    return StockRequestOut(
        id=req.id,
        school_id=req.school_id,
        item_id=req.item_id,
        item_name=req.item_name,
        category=req.category,
        location=req.location,
        quantity_requested=req.quantity_requested,
        urgency=req.urgency,
        status=req.status,
        flag_type=req.flag_type,
        requested_by_id=req.requested_by_id,
        requested_by_name=req.requested_by_name,
        reason=req.reason,
        decided_by_id=req.decided_by_id,
        decided_at=req.decided_at,
        decision_note=req.decision_note,
        created_at=req.created_at,
    )


def get_item(db: Session, school_id: int, item_id: int) -> StockItem:
    item = db.scalar(
        select(StockItem).where(
            StockItem.id == item_id, StockItem.school_id == school_id
        )
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stock item not found")
    return item


def get_overview_stats(db: Session, school_id: int) -> InventoryStatsOut:
    low_stock_count = (
        db.scalar(
            select(func.count(StockItem.id)).where(
                StockItem.school_id == school_id,
                StockItem.current_quantity <= StockItem.min_quantity,
            )
        )
        or 0
    )
    pending_approvals_count = (
        db.scalar(
            select(func.count(StockRequest.id)).where(
                StockRequest.school_id == school_id,
                StockRequest.status == "pending",
            )
        )
        or 0
    )
    discrepancies_count = (
        db.scalar(
            select(func.count(StockItem.id)).where(
                StockItem.school_id == school_id,
                StockItem.has_discrepancy.is_(True),
            )
        )
        or 0
    )
    total_items = (
        db.scalar(
            select(func.count(StockItem.id)).where(StockItem.school_id == school_id)
        )
        or 0
    )

    # Build critical alerts
    # Prioritize items explicitly marked is_critical or severely depleted
    critical_items = list(
        db.scalars(
            select(StockItem)
            .where(
                StockItem.school_id == school_id,
                (StockItem.is_critical.is_(True))
                | (StockItem.current_quantity <= StockItem.min_quantity),
            )
            .order_by(StockItem.is_critical.desc(), StockItem.current_quantity.asc())
            .limit(6)
        )
    )

    alerts: list[CriticalAlertOut] = []
    for it in critical_items:
        if it.current_quantity <= 0:
            subtitle = f"{it.location} • Out of stock ({it.unit})"
            level = "critical"
        elif it.current_quantity <= 2:
            subtitle = f"{it.location} • {it.current_quantity} {it.unit} remaining"
            level = "critical"
        elif it.name.lower().startswith("science") or "chemical" in it.name.lower():
            subtitle = f"{it.location} • Reorder required"
            level = "critical"
        elif "first-aid" in it.name.lower() or "medical" in it.location.lower():
            subtitle = f"{it.location} • Below minimum level"
            level = "critical"
        else:
            subtitle = f"{it.location} • {it.current_quantity} {it.unit} remaining (min {it.min_quantity})"
            level = "warning"

        alerts.append(
            CriticalAlertOut(
                item_id=it.id,
                title=it.name,
                subtitle=subtitle,
                level=level,
                location=it.location,
                category=it.category,
                current_quantity=it.current_quantity,
                min_quantity=it.min_quantity,
                unit=it.unit,
            )
        )

    return InventoryStatsOut(
        low_stock_count=low_stock_count,
        pending_approvals_count=pending_approvals_count,
        discrepancies_count=discrepancies_count,
        total_items=total_items,
        critical_alerts=alerts,
    )


def list_items(
    db: Session,
    school_id: int,
    category: str | None = None,
    location: str | None = None,
    low_stock_only: bool = False,
    has_discrepancy_only: bool = False,
    search: str | None = None,
) -> list[StockItemOut]:
    q = select(StockItem).where(StockItem.school_id == school_id)

    if category and category.lower() != "all":
        q = q.where(StockItem.category.ilike(f"%{category}%"))
    if location and location.lower() != "all":
        q = q.where(StockItem.location.ilike(f"%{location}%"))
    if low_stock_only:
        q = q.where(StockItem.current_quantity <= StockItem.min_quantity)
    if has_discrepancy_only:
        q = q.where(StockItem.has_discrepancy.is_(True))
    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.where(
            (StockItem.name.ilike(term))
            | (StockItem.category.ilike(term))
            | (StockItem.location.ilike(term))
        )

    q = q.order_by(StockItem.category, StockItem.name)
    return [to_item_out(it) for it in db.scalars(q)]


def create_item(db: Session, user: User, data: StockItemCreate) -> StockItemOut:
    item = StockItem(
        school_id=user.school_id,
        name=data.name.strip(),
        category=data.category.strip(),
        location=data.location.strip(),
        unit=data.unit.strip(),
        current_quantity=data.current_quantity,
        min_quantity=data.min_quantity,
        unit_cost=data.unit_cost,
        is_critical=data.is_critical,
        last_checked_at=datetime.now(UTC),
        last_checked_by_id=user.id,
    )
    db.add(item)
    db.flush()

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_item",
        entity_id=item.id,
        action=AuditAction.create,
        after={
            "name": item.name,
            "category": item.category,
            "location": item.location,
            "current_quantity": item.current_quantity,
            "min_quantity": item.min_quantity,
        },
    )
    db.commit()
    db.refresh(item)
    return to_item_out(item)


def update_item(
    db: Session, user: User, item_id: int, data: StockItemUpdate
) -> StockItemOut:
    item = get_item(db, user.school_id, item_id)
    before = {
        "name": item.name,
        "category": item.category,
        "location": item.location,
        "min_quantity": item.min_quantity,
        "unit_cost": str(item.unit_cost) if item.unit_cost is not None else None,
        "is_critical": item.is_critical,
    }

    if data.name is not None:
        item.name = data.name.strip()
    if data.category is not None:
        item.category = data.category.strip()
    if data.location is not None:
        item.location = data.location.strip()
    if data.unit is not None:
        item.unit = data.unit.strip()
    if data.min_quantity is not None:
        item.min_quantity = data.min_quantity
    if data.unit_cost is not None:
        item.unit_cost = data.unit_cost
    if data.is_critical is not None:
        item.is_critical = data.is_critical

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_item",
        entity_id=item.id,
        action=AuditAction.update,
        before=before,
        after={
            "name": item.name,
            "category": item.category,
            "location": item.location,
            "min_quantity": item.min_quantity,
            "unit_cost": str(item.unit_cost) if item.unit_cost is not None else None,
            "is_critical": item.is_critical,
        },
    )
    db.commit()
    db.refresh(item)
    return to_item_out(item)


def adjust_quantity(
    db: Session, user: User, item_id: int, data: StockAdjustIn
) -> StockItemOut:
    item = get_item(db, user.school_id, item_id)
    old_qty = item.current_quantity

    item.current_quantity = data.new_quantity
    item.has_discrepancy = data.has_discrepancy
    if data.has_discrepancy:
        item.discrepancy_notes = data.discrepancy_notes or data.reason
    else:
        item.discrepancy_notes = None
    item.last_checked_at = datetime.now(UTC)
    item.last_checked_by_id = user.id

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_item",
        entity_id=item.id,
        action=AuditAction.status_change,
        reason=data.reason,
        before={"current_quantity": old_qty},
        after={
            "current_quantity": item.current_quantity,
            "has_discrepancy": item.has_discrepancy,
            "discrepancy_notes": item.discrepancy_notes,
        },
    )
    db.commit()
    db.refresh(item)
    return to_item_out(item)


def consume_stock(
    db: Session, user: User, item_id: int, data: StockConsumeIn
) -> StockItemOut:
    item = get_item(db, user.school_id, item_id)
    if data.quantity <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Quantity consumed must be greater than zero"
        )
    if data.quantity > item.current_quantity:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot consume {data.quantity} units; only {item.current_quantity} available in stock",
        )

    old_qty = item.current_quantity
    item.current_quantity -= data.quantity
    item.last_checked_at = datetime.now(UTC)
    item.last_checked_by_id = user.id

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_item",
        entity_id=item.id,
        action=AuditAction.update,
        before={"current_quantity": old_qty},
        after={"current_quantity": item.current_quantity, "consumed": data.quantity},
        reason=data.reason or "Stock consumed by teacher",
    )
    db.commit()
    db.refresh(item)
    return to_item_out(item)


def create_request(
    db: Session, user: User, data: StockRequestCreate
) -> StockRequestOut:
    # If item_id provided, verify school ownership
    if data.item_id:
        get_item(db, user.school_id, data.item_id)

    req = StockRequest(
        school_id=user.school_id,
        item_id=data.item_id,
        item_name=data.item_name.strip(),
        category=data.category.strip(),
        location=data.location.strip(),
        quantity_requested=data.quantity_requested,
        urgency=data.urgency,
        status="pending",
        flag_type=data.flag_type,
        requested_by_id=user.id,
        requested_by_name=user.full_name,
        reason=data.reason.strip(),
    )
    db.add(req)
    db.flush()

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_request",
        entity_id=req.id,
        action=AuditAction.create,
        after={
            "item_name": req.item_name,
            "quantity_requested": req.quantity_requested,
            "urgency": req.urgency,
            "flag_type": req.flag_type,
            "reason": req.reason,
        },
    )
    db.commit()
    db.refresh(req)
    return to_request_out(req)


def list_requests(
    db: Session, school_id: int, status_filter: str | None = None
) -> list[StockRequestOut]:
    q = select(StockRequest).where(StockRequest.school_id == school_id)
    if status_filter and status_filter.lower() != "all":
        q = q.where(StockRequest.status == status_filter.lower())
    q = q.order_by(StockRequest.created_at.desc())
    return [to_request_out(r) for r in db.scalars(q)]


def decide_request(
    db: Session, user: User, request_id: int, data: StockRequestDecide
) -> StockRequestOut:
    req = db.scalar(
        select(StockRequest).where(
            StockRequest.id == request_id, StockRequest.school_id == user.school_id
        )
    )
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stock request not found")

    old_status = req.status
    req.status = data.status
    req.decided_by_id = user.id
    req.decided_at = datetime.now(UTC)
    req.decision_note = data.decision_note

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="stock_request",
        entity_id=req.id,
        action=AuditAction.status_change,
        reason=data.decision_note or f"Stock request marked {data.status}",
        before={"status": old_status},
        after={"status": req.status, "decision_note": req.decision_note},
    )
    db.commit()
    db.refresh(req)
    return to_request_out(req)
