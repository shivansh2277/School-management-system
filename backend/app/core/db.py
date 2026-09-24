from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    # Normalize postgresql:// or postgres:// to postgresql+psycopg:// for psycopg 3
    # compatibility when deploying to cloud providers like Neon Tech.
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]

    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}, "future": True}
    else:
        # Neon Tech Serverless / Cloud Postgres connection pool resilience
        kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "future": True,
        }
    return create_engine(url, **kwargs)


engine = make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
