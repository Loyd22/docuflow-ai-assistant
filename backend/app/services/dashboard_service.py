"""
Application service for Phase 11 dashboard metrics.

This service combines database aggregation results into the
structured dashboard summary returned by the API.
"""

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import (
    count_documents,
    count_documents_by_status,
    count_documents_by_type,
    count_workflows,
    count_workflows_by_status,
)
from app.schemas.dashboard_schema import (
    DashboardSummaryResponse,
    DocumentStatusCounts,
    DocumentTypeCounts,
    WorkflowStatusCounts,
)


class DashboardService:
    """Coordinate dashboard summary generation."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def get_summary(self) -> DashboardSummaryResponse:
        """Return summarized document and workflow metrics."""

        document_status_counts = count_documents_by_status(
            self.database_session,
        )

        document_type_counts = count_documents_by_type(
            self.database_session,
        )

        workflow_status_counts = count_workflows_by_status(
            self.database_session,
        )

        return DashboardSummaryResponse(
            total_documents=count_documents(
                self.database_session,
            ),
            documents_by_status=DocumentStatusCounts(
                **{
                    status.value: count
                    for status, count in document_status_counts.items()
                }
            ),
            documents_by_type=DocumentTypeCounts(
                **{
                    document_type.value: count
                    for document_type, count in document_type_counts.items()
                }
            ),
            total_workflows=count_workflows(
                self.database_session,
            ),
            workflows_by_status=WorkflowStatusCounts(
                **{
                    status.value: count
                    for status, count in workflow_status_counts.items()
                }
            ),
        )
