"""API dependencies for FastAPI routers."""

from sqlalchemy.orm import Session

from app.database import get_db_session


def get_db() -> Session:
    """Provide a database session dependency."""

    yield from get_db_session()

