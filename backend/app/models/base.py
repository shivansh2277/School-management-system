from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

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
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
