import {
  type FormEvent,
  useEffect,
  useState,
} from "react";
import axios from "axios";

import { getDocumentDetails } from "../../api/documentApi";
import { submitWorkflowDecision } from "../../api/workflowApi";
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
};

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;

  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  const megabytes = kilobytes / 1024;

  return `${megabytes.toFixed(1)} MB`;
}

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
}: WorkflowDecisionPanelProps) {
  const [document, setDocument] =
    useState<DocumentDetail | null>(null);

  const [isLoadingDocument, setIsLoadingDocument] =
    useState(true);

  const [
    documentErrorMessage,
    setDocumentErrorMessage,
  ] = useState<string | null>(null);

  const [decision, setDecision] =
    useState<ApprovalDecision>("approved");

  const [comment, setComment] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [
    submitErrorMessage,
    setSubmitErrorMessage,
  ] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocument() {
      setIsLoadingDocument(true);
      setDocument(null);
      setDocumentErrorMessage(null);

      try {
        const documentDetails =
          await getDocumentDetails(
            workflow.document_id,
          );

        setDocument(documentDetails);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detail =
            error.response?.data?.detail;

          if (typeof detail === "string") {
            setDocumentErrorMessage(detail);
          } else {
            setDocumentErrorMessage(
              "Unable to load document details.",
            );
          }
        } else {
          setDocumentErrorMessage(
            "Unable to load document details.",
          );
        }
      } finally {
        setIsLoadingDocument(false);
      }
    }

    loadDocument();
  }, [workflow.document_id]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!document) {
      setSubmitErrorMessage(
        "Document details must be loaded before making a decision.",
      );

      return;
    }

    setIsSubmitting(true);
    setSubmitErrorMessage(null);

    try {
      const response =
        await submitWorkflowDecision(
          workflow.id,
          {
            decision,
            comment:
              comment.trim() || null,
          },
        );

      onDecisionComplete(response);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail =
          error.response?.data?.detail;

        if (typeof detail === "string") {
          setSubmitErrorMessage(detail);
        } else {
          setSubmitErrorMessage(
            "Unable to submit workflow decision.",
          );
        }
      } else {
        setSubmitErrorMessage(
          "Unable to submit workflow decision.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workflow-decision-panel">
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

      {isLoadingDocument && (
        <div className="workflow-document-loading">
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

      {document && (
        <div className="workflow-document-review">
          <div className="workflow-document-section">
            <h4>Document Information</h4>

            <div className="workflow-document-grid">
              <div>
                <span className="workflow-detail-label">
                  File Name
                </span>

                <span>
                  {document.original_file_name}
                </span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  Type
                </span>

                <span>
                  {formatLabel(
                    document.document_type,
                  )}
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
                  {formatFileSize(
                    document.file_size,
                  )}
                </span>
              </div>

              <div>
                <span className="workflow-detail-label">
                  Uploaded By
                </span>

                <span>
                  User #{document.uploaded_by}
                </span>
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

      <form
        className="workflow-decision-form"
        onSubmit={handleSubmit}
      >
        <h4>Decision</h4>

        <label htmlFor="workflow-decision">
          Decision
        </label>

        <select
          id="workflow-decision"
          value={decision}
          onChange={(event) =>
            setDecision(
              event.target.value as ApprovalDecision,
            )
          }
          disabled={
            isSubmitting ||
            isLoadingDocument ||
            !document
          }
        >
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
          Comment
        </label>

        <textarea
          id="workflow-comment"
          value={comment}
          onChange={(event) =>
            setComment(event.target.value)
          }
          placeholder="Optional comment..."
          rows={4}
          disabled={
            isSubmitting ||
            isLoadingDocument ||
            !document
          }
        />

        {submitErrorMessage && (
          <p
            className="workflow-decision-error"
            role="alert"
          >
            {submitErrorMessage}
          </p>
        )}

        <button
          type="submit"
          className="workflow-submit-button"
          disabled={
            isSubmitting ||
            isLoadingDocument ||
            !document
          }
        >
          {isSubmitting
            ? "Submitting..."
            : "Submit Decision"}
        </button>
      </form>
    </section>
  );
}

export default WorkflowDecisionPanel;