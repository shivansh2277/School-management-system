from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.db import Base


def enum_col(py_enum, **kw):
    """VARCHAR-backed enum: identical constraint semantics on Postgres and SQLite."""
    return mapped_column(
        Enum(py_enum, native_enum=False, values_callable=lambda e: [m.value for m in e]), **kw
    )


class TimestampedBase(Base):
    __abstract__ = True

    # SQLite only autoincrements INTEGER; Postgres still gets BIGSERIAL.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # server_default as well as onupdate: without it the column stays NULL until
    # the row is first updated, which made "never touched" and "touched at an
    # unknown time" indistinguishable.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TenantBase(TimestampedBase):
    """Every table except `schools` carries the tenant key.

    The column is declared here rather than on each model so that a new table
    cannot silently be created without one — a missing `school_id` is a data
    leak between customers, not a style problem (ERP_BLUEPRINT §3.15).
    """

    __abstract__ = True

    @declared_attr
    def school_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(
            BigInteger, ForeignKey("schools.id"), nullable=False, index=True
        )
