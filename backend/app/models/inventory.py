"""Stock and inventory models for tracking school supplies and materials.

Covers science lab chemicals, glassware, models, mathematics kits, art materials,
chalks, dusters, stationery, and first-aid supplies with minimum threshold alerts,
discrepancies, and staff/teacher replenishment requests.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class StockItem(TenantBase):
    """An inventory item held in a school store, lab, or room."""

    __tablename__ = "stock_items"
    __table_args__ = (
        Index("ix_stock_items_school_category", "school_id", "category"),
        Index("ix_stock_items_school_location", "school_id", "location"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    location: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    is_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_discrepancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discrepancy_notes: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )

    @property
    def is_low_stock(self) -> bool:
        return self.current_quantity <= self.min_quantity


class StockRequest(TenantBase):
    """A stock replenishment request, purchase indent, or teacher diminishing-stock flag."""

    __tablename__ = "stock_requests"
    __table_args__ = (
        Index("ix_stock_requests_school_status", "school_id", "status"),
    )

    item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_items.id"), index=True
    )
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    location: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    flag_type: Mapped[str] = mapped_column(String(20), nullable=False, default="diminishing")
    requested_by_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    requested_by_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)

    item = relationship("StockItem", lazy="joined", foreign_keys=[item_id])
