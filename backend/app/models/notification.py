from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class InAppNotification(TenantBase):
    """In-app alert for staff, teachers, or admins regarding leaves, substitutions, etc."""

    __tablename__ = "in_app_notifications"
    __table_args__ = (
        Index("ix_in_app_notifications_user_read", "user_id", "is_read"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user = relationship("User", lazy="joined")
