from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# This creates the connection engine to PostgreSQL.
engine = create_engine(settings.DATABASE_URL)


# This creates database sessions.
# A session is used when we read or write data in the database.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)