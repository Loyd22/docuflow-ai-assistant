import type { Workflow } from "../../types/workflow";

import "./WorkflowTable.css";

type WorkflowTableProps = {
  workflows: Workflow[];
  canMakeDecisions: boolean;
  onDecision: (workflowId: number) => void;
};

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function WorkflowTable({
  workflows,
  canMakeDecisions,
  onDecision,
}: WorkflowTableProps) {
  return (
    <div className="workflow-table-wrapper">
      <table className="workflow-table">
        <thead>
          <tr>
            <th>Workflow</th>
            <th>Document</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Recommended Action</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {workflows.map((workflow) => {
            const canReview =
              canMakeDecisions &&
              workflow.current_status ===
                "pending_approval";

            return (
              <tr key={workflow.id}>
                <td>#{workflow.id}</td>
                <td>#{workflow.document_id}</td>

                <td>
                  <span className="workflow-status">
                    {formatLabel(
                      workflow.current_status,
                    )}
                  </span>
                </td>

                <td>
                  {formatLabel(workflow.priority)}
                </td>

                <td>
                  {workflow.recommended_action
                    ? formatLabel(
                        workflow.recommended_action,
                      )
                    : "—"}
                </td>

                <td>
                  {formatDate(workflow.created_at)}
                </td>

                <td>
                  {canReview ? (
                    <button
                      type="button"
                      className="workflow-review-button"
                      onClick={() =>
                        onDecision(workflow.id)
                      }
                    >
                      Review
                    </button>
                  ) : (
                    <span className="workflow-no-action">
                      —
                    </span>
                  )}
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