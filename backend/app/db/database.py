"""
SQLAlchemy database engine configuration.

The engine manages connections between the FastAPI backend
and the PostgreSQL database.
"""

from sqlalchemy import create_engine

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    # Checks whether a pooled connection is still valid
    # before SQLAlchemy uses it.
    pool_pre_ping=True,
    # Display generated SQL during development.
    # We can disable this in production.
    echo=settings.app_debug,
)
