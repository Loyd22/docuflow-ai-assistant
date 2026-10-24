
import type { Workflow } from "../../types/workflow";

import "./WorkflowTable.css";

type WorkflowTableProps = {
  workflows: Workflow[];
  canMakeDecisions: boolean;
  canRespondToRequests: boolean;
  onDecision: (workflowId: number) => void;
  onViewHistory: (workflowId: number) => void;
};

// Convert database values into readable labels.
function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

// Convert timestamps into readable dates.
function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleString();
}

function WorkflowTable({
  workflows,
  canMakeDecisions,
  canRespondToRequests,
  onDecision,
  onViewHistory,
}: WorkflowTableProps) {
  return (
    <div className="workflow-table-wrapper" role="region" aria-label="Workflows table" tabIndex={0}>
      <table className="workflow-table">
        <thead>
          <tr>
            <th scope="col">Workflow</th>
            <th scope="col">Document</th>
            <th scope="col">Status</th>
            <th scope="col">Priority</th>
            <th scope="col">Recommended Action</th>
            <th scope="col">Created</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>

        <tbody>
          {workflows.map((workflow) => {
            // Managers and admins handle reviews and approvals.
            const canReview =
              canMakeDecisions &&
              (workflow.current_status === "pending_approval" ||
                workflow.current_status === "needs_review");

            // Employees respond to outstanding information requests.
            const canRespond =
              canRespondToRequests &&
              workflow.current_status === "needs_information";

            // Select the action label based on workflow status.
            const actionLabel = canRespond
              ? "Respond to Request"
              : workflow.current_status === "needs_review"
                ? "Manual Review"
                : "Approval Decision";

            return (
              <tr key={workflow.id}>
                <td>#{workflow.id}</td>

                <td>#{workflow.document_id}</td>

                <td>
                  <span className={`workflow-status workflow-status-${workflow.current_status}`}>
                    {formatLabel(workflow.current_status)}
                  </span>
                </td>

                <td>
                  <span className={`workflow-priority workflow-priority-${workflow.priority}`}>{formatLabel(workflow.priority)}</span>
                </td>

                <td>
                  {workflow.recommended_action
                    ? formatLabel(workflow.recommended_action)
                    : "—"}
                </td>

                <td>{formatDate(workflow.created_at)}</td>

                <td>
                  <div className="workflow-row-actions">
                    {/* Show an action only when the user can perform it. */}
                    {(canReview || canRespond) && (
                      <button
                        type="button"
                        className="workflow-review-button"
                        onClick={() => onDecision(workflow.id)}
                      >
                        {actionLabel}
                      </button>
                    )}

                    {/* History is available for visible workflows. */}
                    <button
                      type="button"
                      className="workflow-history-button"
                      onClick={() => onViewHistory(workflow.id)}
                      aria-label={`View history for workflow #${workflow.id}`}
                    >
                      View details
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default WorkflowTable;
