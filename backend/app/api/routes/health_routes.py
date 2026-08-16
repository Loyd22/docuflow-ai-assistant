"""
Health-check API endpoints.

Health checks help developers, Docker, and hosting platforms
determine whether the application and database are working.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db_session


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def check_application_health() -> dict[str, str]:
    """Confirm that the FastAPI application is running."""

    return {
        "status": "healthy",
        "service": "docuflow-backend",
    }


@router.get("/database")
def check_database_health(
    database_session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Confirm that the backend can communicate with PostgreSQL."""

    try:
        # SELECT 1 is a lightweight database connectivity test.
        database_session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError as error:
        # Return a proper service error instead of exposing
        # sensitive database details to the client.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        ) from error