"""
Base class for future SQLAlchemy database models.

Models such as User and Document will inherit from this class.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class shared by every database model."""
