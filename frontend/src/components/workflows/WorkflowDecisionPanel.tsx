
import { type FormEvent, useEffect, useState } from "react";
import axios from "axios";

import { getDocumentDetails } from "../../api/documentApi";
import { submitWorkflowDecision } from "../../api/workflowApi";

import OriginalDocumentActions from "../documents/OriginalDocumentActions";

import type { DocumentDetail } from "../../types/document";
import type {
  ApprovalDecision,
  Workflow,
  WorkflowDecisionResponse,
} from "../../types/workflow";

import "./WorkflowDecisionPanel.css";

type WorkflowDecisionPanelProps = {
  workflow: Workflow;
  onClose: () => void;
  onDecisionComplete: (
    response: WorkflowDecisionResponse,
  ) => void;
  documentDetails?: DocumentDetail;
  embedded?: boolean;
};

// Convert database values into readable labels.
function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

// Display file sizes in readable units.
function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;

  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  return `${(kilobytes / 1024).toFixed(1)} MB`;
}

// Display AI confidence as a percentage.
function formatConfidence(
  confidence: number | null,
): string {
  if (confidence === null) {
    return "—";
  }

  return `${(confidence * 100).toFixed(1)}%`;
}

function WorkflowDecisionPanel({
  workflow,
  onClose,
  onDecisionComplete,
  documentDetails,
  embedded = false,
}: WorkflowDecisionPanelProps) {
  // Reuse document data if the parent already loaded it.
  const [document, setDocument] =
    useState<DocumentDetail | null>(documentDetails ?? null);

  const [isLoadingDocument, setIsLoadingDocument] =
    useState(!documentDetails);

  const [documentErrorMessage, setDocumentErrorMessage] =
    useState<string | null>(null);

  // No decision is selected by default.
  const [decision, setDecision] =
    useState<ApprovalDecision | "">("");

  const [comment, setComment] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [submitErrorMessage, setSubmitErrorMessage] =
    useState<string | null>(null);

  // Load the document only when the parent has not provided it.
  useEffect(() => {
    if (documentDetails) {
      setDocument(documentDetails);
      setIsLoadingDocument(false);
      setDocumentErrorMessage(null);
      return;
    }

    let cancelled = false;

    async function loadDocument() {
      setIsLoadingDocument(true);
      setDocument(null);
      setDocumentErrorMessage(null);

      try {
        const result = await getDocumentDetails(
          workflow.document_id,
        );

        if (!cancelled) {
          setDocument(result);
        }
      } catch (error) {
        if (!cancelled) {
          const detail = axios.isAxiosError(error)
            ? error.response?.data?.detail
            : null;

          setDocumentErrorMessage(
            typeof detail === "string"
              ? detail
              : "Unable to load document details.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoadingDocument(false);
        }
      }
    }

    void loadDocument();

    return () => {
      cancelled = true;
    };
  }, [workflow.document_id, documentDetails]);

  // Rejection and information requests need an explanation.
  const requiresComment =
    decision === "rejected" ||
    decision === "information_requested";

  const trimmedComment = comment.trim();

  const hasValidDecision = decision !== "";

  const hasValidComment =
    !requiresComment || trimmedComment.length > 0;

  const isDisabled =
    isSubmitting ||
    isLoadingDocument ||
    !document;

  const cannotSubmit =
    isDisabled ||
    !hasValidDecision ||
    !hasValidComment;

  // Change the comment label depending on the decision.
  const commentLabel =
    decision === "rejected"
      ? "Reason for Rejection"
      : decision === "information_requested"
        ? "Information Needed"
        : "Comment (Optional)";

  const commentPlaceholder =
    decision === "rejected"
      ? "Explain why this document is rejected..."
      : decision === "information_requested"
        ? "Explain what information the employee must provide..."
        : "Add an optional comment...";

  // Send the manager's decision to FastAPI.
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    if (!document) {
      setSubmitErrorMessage(
        "Document details must be loaded before making a decision.",
      );
      return;
    }

    // Ensure the manager deliberately selects a decision.
    if (!decision) {
      setSubmitErrorMessage(
        "Please select an approval decision.",
      );
      return;
    }

    // Require explanations for rejection and information requests.
    if (requiresComment && !trimmedComment) {
      setSubmitErrorMessage(
        decision === "rejected"
          ? "Please provide a reason for rejecting this document."
          : "Please explain what information is needed.",
      );
      return;
    }

    setIsSubmitting(true);
    setSubmitErrorMessage(null);

    try {
      const response = await submitWorkflowDecision(
        workflow.id,
        {
          decision,
          comment: trimmedComment || null,
        },
      );

      onDecisionComplete(response);
    } catch (error) {
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : null;

      setSubmitErrorMessage(
        typeof detail === "string"
          ? detail
          : "Unable to submit workflow decision.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workflow-decision-panel">
      {/* Standalone mode displays its own header. */}
      {!embedded && (
        <div className="workflow-decision-header">
          <div>
            <h3>Review Workflow</h3>
            <p>
              Workflow #{workflow.id} · Document #
              {workflow.document_id}
            </p>
          </div>

          <button
            type="button"
            className="workflow-close-button"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Close
          </button>
        </div>
      )}

      {isLoadingDocument && (
        <div className="workflow-document-loading" role="status">
          Loading document details...
        </div>
      )}

      {documentErrorMessage && (
        <p
          className="workflow-decision-error"
          role="alert"
        >
          {documentErrorMessage}
        </p>
      )}

      {/* Show document information only in standalone mode. */}
      {!embedded && document && (
        <div className="workflow-document-review">
          <div className="workflow-document-section">
            <h4>Document Information</h4>

            <div className="workflow-document-grid">
              <div>
                <span className="workflow-detail-label">
                  File Name
                </span>
                <span>{document.original_file_name}</span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  Type
                </span>
                <span>
                  {formatLabel(document.document_type)}
                </span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  Status
                </span>
                <span>
                  {formatLabel(document.status)}
                </span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  File Size
                </span>
                <span>
                  {formatFileSize(document.file_size)}
                </span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  Uploaded By
                </span>
                <span>User #{document.uploaded_by}</span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  AI Confidence
                </span>
                <span>
                  {formatConfidence(
                    document.classification_confidence,
                  )}
                </span>
              </div>
            </div>
          </div>

          <OriginalDocumentActions
            documentId={document.id}
            originalFileName={document.original_file_name}
          />

          {document.summary && (
            <div className="workflow-document-section">
              <h4>Summary</h4>
              <p className="workflow-document-text">
                {document.summary}
              </p>
            </div>
          )}

          <div className="workflow-document-section">
            <h4>Extracted Data</h4>
            {document.extracted_data ? (
              <pre className="workflow-json">
                {JSON.stringify(
                  document.extracted_data,
                  null,
                  2,
                )}
              </pre>
            ) : (
              <p className="workflow-empty-value">
                No extracted data available.
              </p>
            )}
          </div>

          <div className="workflow-document-section">
            <h4>Business Rule Result</h4>
            {document.business_rule_result ? (
              <pre className="workflow-json">
                {JSON.stringify(
                  document.business_rule_result,
                  null,
                  2,
                )}
              </pre>
            ) : (
              <p className="workflow-empty-value">
                No business-rule result available.
              </p>
            )}
          </div>

          <div className="workflow-document-section">
            <h4>Extracted Text</h4>
            {document.extracted_text ? (
              <pre className="workflow-extracted-text">
                {document.extracted_text}
              </pre>
            ) : (
              <p className="workflow-empty-value">
                No extracted text available.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Manager approval decision form. */}
      <form
        className="workflow-decision-form"
        onSubmit={handleSubmit}
      >
        <h4>Approval Decision</h4>

        <label htmlFor="workflow-decision">
          Decision
        </label>

        <select
          id="workflow-decision"
          value={decision}
          onChange={(event) => {
            setDecision(
              event.target.value as ApprovalDecision | "",
            );
            setSubmitErrorMessage(null);
          }}
          disabled={isDisabled}
          required
        >
          <option value="" disabled>
            Select a decision
          </option>

          <option value="approved">
            Approve
          </option>

          <option value="rejected">
            Reject
          </option>

          <option value="information_requested">
            Request Information
          </option>
        </select>

        <label htmlFor="workflow-comment">
          {commentLabel}
          {requiresComment ? " *" : ""}
        </label>

        <textarea
          id="workflow-comment"
          value={comment}
          onChange={(event) => {
            setComment(event.target.value);
            setSubmitErrorMessage(null);
          }}
          placeholder={commentPlaceholder}
          rows={4}
          disabled={isDisabled}
          required={requiresComment}
        />

        {requiresComment && !trimmedComment && (
          <p className="workflow-empty-value">
            {decision === "rejected"
              ? "A rejection reason is required."
              : "Explain what information the employee needs to provide."}
          </p>
        )}

        {submitErrorMessage && (
          <p
            className="workflow-decision-error"
            role="alert"
          >
            {submitErrorMessage}
          </p>
        )}

        <div className="workflow-decision-form-actions">
          <button
            type="submit"
            className="workflow-submit-button"
            disabled={cannotSubmit}
          >
            {isSubmitting
              ? "Submitting..."
              : "Submit Decision"}
          </button>

          {/* Cancel only the form when embedded. */}
          {embedded && (
            <button
              type="button"
              className="workflow-close-button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel Decision
            </button>
          )}
        </div>
      </form>
    </section>
  );
}

export default WorkflowDecisionPanel;
