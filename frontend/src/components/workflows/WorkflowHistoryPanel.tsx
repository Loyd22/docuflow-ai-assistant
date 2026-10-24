
import { useEffect, useState } from "react";
import axios from "axios";

import { getWorkflowHistory } from "../../api/workflowApi";

import type {
  WorkflowHistoryItem,
} from "../../types/workflow";

import "./WorkflowHistoryPanel.css";

type WorkflowHistoryPanelProps = {
  workflowId: number;
  onClose: () => void;
};

// Convert backend action names into readable labels.

// Convert workflow events into readable descriptions.
function formatAction(item: WorkflowHistoryItem): string {
  if (item.action_type === "information_response") {
    return "Employee responded";
  }

  if (item.action_type === "manual_review") {
    return `Manual review: ${item.decision.replaceAll("_", " ")}`;
  }

  return `Approval: ${item.decision.replaceAll("_", " ")}`;
}


// Display a timestamp in the user's local timezone.
function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleString();
}

export default function WorkflowHistoryPanel({
  workflowId,
  onClose,
}: WorkflowHistoryPanelProps) {
  const [history, setHistory] = useState<WorkflowHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadHistory() {
      setIsLoading(true);
      setErrorMessage(null);
      setHistory([]);

      try {
        const response = await getWorkflowHistory(workflowId);

        if (isActive) {
          setHistory(response.history);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }

        const detail = axios.isAxiosError(error)
          ? error.response?.data?.detail
          : null;

        setErrorMessage(
          typeof detail === "string"
            ? detail
            : "Unable to load workflow history.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadHistory();

    // Ignore responses from workflows that are no longer selected.
    return () => {
      isActive = false;
    };
  }, [workflowId]);

  return (
    <section
      className="workflow-history-panel"
      aria-label="Workflow decision history"
    >
      <div className="workflow-history-header">
        <div>
          <h3>Decision History</h3>
          <p>Workflow #{workflowId}</p>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close decision history"
        >
          Close
        </button>
      </div>

      {isLoading && (
        <p role="status">Loading decision history...</p>
      )}

      {errorMessage && (
        <p role="alert">{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && history.length === 0 && (
        <p>No decisions have been recorded for this workflow.</p>
      )}

      {!isLoading && !errorMessage && history.length > 0 && (
        <ol className="workflow-history-list">
          {history.map((item) => (
            <li
              key={`${item.action_type}-${item.id}`}
              className="workflow-history-item"
            >
              <div className="workflow-history-item-heading">
                <strong>{formatAction(item)}</strong>
                <time dateTime={item.created_at}>
                  {formatDate(item.created_at)}
                </time>
              </div>

              <p>
              {item.action_type === "information_response"
                ? `Responded by user #${item.decided_by}`
                : `Reviewed by user #${item.decided_by}`}
            </p>

              {item.comment && (
                <p className="workflow-history-comment">
                  {item.comment}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
