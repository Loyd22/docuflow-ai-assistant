"""Build workflow history from decisions and employee responses."""

from sqlalchemy.orm import Session

from app.db.enums import AuditEntityType
from app.repositories.approval_repository import get_approvals_by_workflow_id
from app.repositories.audit_log_repository import get_audit_logs_by_entity
from app.repositories.workflow_information_request_repository import (
    get_information_requests_by_workflow_id,
)
from app.repositories.workflow_review_repository import get_reviews_by_workflow_id
from app.schemas.workflow_schema import (
    WorkflowHistoryItemResponse,
    WorkflowHistoryResponse,
)


class WorkflowHistoryService:
    """Combine manager decisions and employee responses."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_history(self, *, workflow_id: int) -> WorkflowHistoryResponse:
        """Return the workflow's recorded events."""

        approvals = get_approvals_by_workflow_id(
            database_session=self.database_session,
            workflow_id=workflow_id,
        )

        reviews = get_reviews_by_workflow_id(
            database_session=self.database_session,
            workflow_id=workflow_id,
        )

        # Retrieve both answered and unanswered information requests.
        information_requests = get_information_requests_by_workflow_id(
            database_session=self.database_session,
            workflow_id=workflow_id,
        )

        audit_logs = get_audit_logs_by_entity(
            database_session=self.database_session,
            entity_type=AuditEntityType.WORKFLOW,
            entity_id=workflow_id,
        )

        decisions: dict[tuple[str, int], WorkflowHistoryItemResponse] = {}

        # Convert approval records into history items.
        for approval in approvals:
            decisions[("approval", approval.id)] = WorkflowHistoryItemResponse(
                id=approval.id,
                action_type="approval",
                decided_by=approval.approver_id,
                decision=approval.decision.value,
                comment=approval.comment,
                created_at=approval.created_at,
            )

        # Convert manual-review records into history items.
        for review in reviews:
            decisions[("manual_review", review.id)] = WorkflowHistoryItemResponse(
                id=review.id,
                action_type="manual_review",
                decided_by=review.reviewer_id,
                decision=review.outcome.value,
                comment=review.comment,
                created_at=review.created_at,
            )

        ordered_history: list[WorkflowHistoryItemResponse] = []
        included_decisions: set[tuple[str, int]] = set()

        # Keep decisions in audit-event order.
        for audit_log in sorted(audit_logs, key=lambda log: log.id):
            metadata = audit_log.event_metadata or {}

            for metadata_key, action_type in (
                ("review_id", "manual_review"),
                ("approval_id", "approval"),
            ):
                decision_id = metadata.get(metadata_key)

                if decision_id is None:
                    continue

                decision_key = (action_type, decision_id)

                if decision_key in decisions and decision_key not in included_decisions:
                    ordered_history.append(decisions[decision_key])
                    included_decisions.add(decision_key)

        # Preserve older decisions without audit events.
        unmatched_decisions = [
            item for key, item in decisions.items() if key not in included_decisions
        ]

        unmatched_decisions.sort(
            key=lambda item: (
                item.created_at.isoformat(),
                item.action_type,
                item.id,
            )
        )

        ordered_history.extend(unmatched_decisions)

        # Add each employee response after its manager request.
        for request in information_requests:
            if (
                request.responded_at is None
                or request.responded_by is None
                or request.response_comment is None
            ):
                continue

            response_item = WorkflowHistoryItemResponse(
                id=request.id,
                action_type="information_response",
                decided_by=request.responded_by,
                decision="responded",
                comment=request.response_comment,
                created_at=request.responded_at,
            )

            # Identify the decision that requested the information.
            parent_type = None
            parent_id = None

            if request.approval_id is not None:
                parent_type = "approval"
                parent_id = request.approval_id
            elif request.review_id is not None:
                parent_type = "manual_review"
                parent_id = request.review_id

            # Place the employee reply after the related request.
            parent_index = next(
                (
                    index
                    for index, item in enumerate(ordered_history)
                    if item.action_type == parent_type and item.id == parent_id
                ),
                None,
            )

            if parent_index is not None:
                insert_index = parent_index + 1

                # Keep multiple replies in their response-time order.
                while (
                    insert_index < len(ordered_history)
                    and ordered_history[insert_index].action_type
                    == "information_response"
                    and ordered_history[insert_index].created_at
                    <= response_item.created_at
                ):
                    insert_index += 1

                ordered_history.insert(insert_index, response_item)
            else:
                # For older unlinked requests, use response timestamps.
                insert_index = next(
                    (
                        index
                        for index, item in enumerate(ordered_history)
                        if item.created_at > response_item.created_at
                    ),
                    len(ordered_history),
                )

                ordered_history.insert(insert_index, response_item)

        return WorkflowHistoryResponse(
            workflow_id=workflow_id,
            history=ordered_history,
        )
