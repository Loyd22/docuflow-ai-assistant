"""
Shared pytest fixtures for backend integration tests.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app

# Integration tests must use a separate test database.
if not settings.test_database_url:
    raise RuntimeError(
        "TEST_DATABASE_URL must be configured to run backend database tests."
    )

# Read the database URLs without displaying passwords.
application_url = make_url(settings.database_url)
test_url = make_url(settings.test_database_url)

# Prevent tests from using the main application database.
if (
    application_url.host == test_url.host
    and (application_url.port or 5432) == (test_url.port or 5432)
    and application_url.database == test_url.database
):
    raise RuntimeError("TEST_DATABASE_URL must not point to the application database.")

# Create the test database engine only after validation.
test_engine = create_engine(
    settings.test_database_url,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> Generator[None, None, None]:
    """Create the database schema used by integration tests."""

    with test_engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated database session for a test."""

    connection = test_engine.connect()
    transaction = connection.begin()

    # Keep application commits and rollbacks inside a SAVEPOINT.
    session = TestSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(
    db_session: Session,
) -> Generator[TestClient, None, None]:
    """Provide a FastAPI client using the test database."""

    def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
