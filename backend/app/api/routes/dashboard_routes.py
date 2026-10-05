"""
Dashboard API endpoints.

These routes return summary information about
documents and workflows.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.dashboard_schema import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary(
    current_user: User = Depends(
        require_roles(
            UserRole.MANAGER,
            UserRole.ADMIN,
        )
    ),
    database_session: Session = Depends(get_db_session),
) -> DashboardSummaryResponse:
    """Return the main dashboard summary."""

    # Get the dashboard numbers from the service.
    dashboard_service = DashboardService(
        database_session=database_session,
    )

    return dashboard_service.get_summary()
