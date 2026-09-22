from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class StockItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    location: str = Field(min_length=1, max_length=80)
    unit: str = Field(min_length=1, max_length=30)
    current_quantity: int = Field(default=0, ge=0)
    min_quantity: int = Field(default=5, ge=0)
    unit_cost: Decimal | None = None
    is_critical: bool = False


class StockItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    location: str | None = None
    unit: str | None = None
    min_quantity: int | None = None
    unit_cost: Decimal | None = None
    is_critical: bool | None = None


class StockAdjustIn(BaseModel):
    new_quantity: int = Field(ge=0)
    reason: str = Field(min_length=3)
    has_discrepancy: bool = False
    discrepancy_notes: str | None = None


class StockConsumeIn(BaseModel):
    model_config = {"extra": "forbid"}
    quantity: int = Field(gt=0, description="Quantity consumed")
    reason: str | None = Field(default=None, max_length=255)


class StockItemOut(BaseModel):
    id: int
    school_id: int
    name: str
    category: str
    location: str
    unit: str
    current_quantity: int
    min_quantity: int
    unit_cost: Decimal | None = None
    is_critical: bool
    has_discrepancy: bool
    discrepancy_notes: str | None = None
    is_low_stock: bool
    last_checked_at: datetime | None = None

    class Config:
        from_attributes = True


class StockRequestCreate(BaseModel):
    item_id: int | None = None
    item_name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    location: str = Field(min_length=1, max_length=80)
    quantity_requested: int = Field(default=1, ge=1)
    urgency: str = Field(default="normal")  # normal, urgent, critical
    flag_type: str = Field(default="diminishing")  # diminishing, purchase, issue
    reason: str = Field(min_length=3)


class StockRequestDecide(BaseModel):
    status: Literal["approved", "rejected", "fulfilled"]
    decision_note: str | None = None


class StockRequestOut(BaseModel):
    id: int
    school_id: int
    item_id: int | None
    item_name: str
    category: str
    location: str
    quantity_requested: int
    urgency: str
    status: str
    flag_type: str
    requested_by_id: int
    requested_by_name: str
    reason: str
    decided_by_id: int | None
    decided_at: datetime | None
    decision_note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CriticalAlertOut(BaseModel):
    item_id: int | None
    title: str
    subtitle: str
    level: str  # "critical", "warning"
    location: str
    category: str
    current_quantity: int
    min_quantity: int
    unit: str


class InventoryStatsOut(BaseModel):
    low_stock_count: int
    pending_approvals_count: int
    discrepancies_count: int
    total_items: int
    critical_alerts: list[CriticalAlertOut]
