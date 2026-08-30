"""
Database session creation and cleanup.

A session represents one unit of communication with the database.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """
    Provide one database session for a request.

    FastAPI will:
    1. Create the session.
    2. Give it to the endpoint.
    3. Close it after the request finishes.
    """

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()
