"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for ORM models."""


settings = get_settings()

engine = create_engine(  # type: ignore[assignment]
    settings.sql_database_url,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session():
    """Database session dependency for FastAPI."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

