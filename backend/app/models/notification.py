from datetime import UTC, datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
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


class AlertView(TenantBase):
    """Tracks viewed/dismissed status of important alerts per user, child, and alert event."""

    __tablename__ = "alert_views"
    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "user_id",
            "student_id",
            "alert_type",
            "event_key",
            name="uq_alert_views_user_student_alert",
        ),
        Index(
            "ix_alert_views_lookup",
            "user_id",
            "student_id",
            "alert_type",
            "event_key",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id"), nullable=False, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_key: Mapped[str] = mapped_column(String(100), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    user = relationship("User", lazy="joined")
    student = relationship("Student", lazy="joined")

