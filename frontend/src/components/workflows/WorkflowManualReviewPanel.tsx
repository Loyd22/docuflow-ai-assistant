
import { type FormEvent, useEffect, useState } from "react";
import axios from "axios";

import { getDocumentDetails } from "../../api/documentApi";
import { submitManualReview } from "../../api/workflowApi";

import OriginalDocumentActions from "../documents/OriginalDocumentActions";

import type { DocumentDetail } from "../../types/document";
import type {
  ReviewOutcome,
  Workflow,
  WorkflowReviewDecisionResponse,
} from "../../types/workflow";

import "./WorkflowDecisionPanel.css";

type WorkflowManualReviewPanelProps = {
  workflow: Workflow;
  onClose: () => void;
  onReviewComplete: (
    response: WorkflowReviewDecisionResponse,
  ) => void;
  documentDetails?: DocumentDetail;
  embedded?: boolean;
};

function WorkflowManualReviewPanel({
  workflow,
  onClose,
  onReviewComplete,
  documentDetails,
  embedded = false,
}: WorkflowManualReviewPanelProps) {
  // Reuse the document already loaded by Workflow Details.
  const [document, setDocument] =
    useState<DocumentDetail | null>(documentDetails ?? null);

  const [isLoadingDocument, setIsLoadingDocument] =
    useState(!documentDetails);

  const [documentError, setDocumentError] =
    useState<string | null>(null);

  // The manager must choose an outcome.
  const [outcome, setOutcome] =
    useState<ReviewOutcome | "">("");

  const [correctedTotal, setCorrectedTotal] =
    useState("");

  const [comment, setComment] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [submitError, setSubmitError] =
    useState<string | null>(null);

  // Fetch the document only if the parent hasn't supplied it.
  useEffect(() => {
    if (documentDetails) {
      setDocument(documentDetails);
      setIsLoadingDocument(false);
      setDocumentError(null);
      return;
    }

    let cancelled = false;

    async function loadDocument() {
      setIsLoadingDocument(true);
      setDocument(null);
      setDocumentError(null);

      try {
        const details = await getDocumentDetails(
          workflow.document_id,
        );

        if (!cancelled) {
          setDocument(details);
        }
      } catch (error) {
        if (!cancelled) {
          const detail = axios.isAxiosError(error)
            ? error.response?.data?.detail
            : null;

          setDocumentError(
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

  // Check whether the verified invoice total is valid.
  const verifiedAmount = Number(correctedTotal);

  const hasValidVerifiedAmount =
    correctedTotal.trim() !== "" &&
    Number.isFinite(verifiedAmount) &&
    verifiedAmount >= 0;

  const isDisabled =
    isSubmitting || isLoadingDocument || !document;

  // Prevent submitting an incomplete manual review.
  const cannotSubmit =
    isDisabled ||
    outcome === "" ||
    !comment.trim() ||
    (outcome === "resolved" &&
      (document?.document_type !== "invoice" ||
        !hasValidVerifiedAmount));

  // Submit the review after validating the inputs.
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    // Prevent the same review from being submitted twice.
    if (isSubmitting) {
      return;
    }

    setSubmitError(null);

    if (!document) {
      setSubmitError("Document details must be loaded first.");
      return;
    }

    if (outcome === "") {
      setSubmitError("Please select a review outcome.");
      return;
    }

    const cleanComment = comment.trim();

    if (!cleanComment) {
      setSubmitError("A review comment is required.");
      return;
    }

    let correctedAmount: number | undefined;

    // Invoice resolution requires a verified total.
    if (outcome === "resolved") {
      if (document.document_type !== "invoice") {
        setSubmitError(
          "Automatic resolution is currently supported only for invoices.",
        );
        return;
      }

      if (!hasValidVerifiedAmount) {
        setSubmitError(
          "Enter a valid, nonnegative invoice total.",
        );
        return;
      }

      correctedAmount = verifiedAmount;
    }

    setIsSubmitting(true);

    try {
      const response = await submitManualReview(
        workflow.id,
        {
          outcome,
          comment: cleanComment,
          corrected_total_amount:
            correctedAmount ?? null,
        },
      );

      onReviewComplete(response);
    } catch (error) {
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : null;

      setSubmitError(
        typeof detail === "string"
          ? detail
          : "Unable to submit manual review.",
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
            <h3>Manual Document Review</h3>

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
        <p className="workflow-document-loading" role="status">Loading document details...</p>
      )}

      {documentError && (
        <p
          className="workflow-decision-error"
          role="alert"
        >
          {documentError}
        </p>
      )}

      {/* Avoid repeating document information in embedded mode. */}
      {!embedded && document && (
        <div className="workflow-document-review">
          <div className="workflow-document-section">
            <h4>Document Information</h4>

            <p>
              <strong>File:</strong>{" "}
              {document.original_file_name}
            </p>

            <p>
              <strong>Type:</strong>{" "}
              {document.document_type}
            </p>

            <p>
              <strong>Status:</strong>{" "}
              {document.status}
            </p>
          </div>

          <OriginalDocumentActions
            documentId={document.id}
            originalFileName={document.original_file_name}
          />

          <div className="workflow-document-section">
            <h4>AI-Extracted Data</h4>

            {document.extracted_data ? (
              <pre className="workflow-json">
                {JSON.stringify(
                  document.extracted_data,
                  null,
                  2,
                )}
              </pre>
            ) : (
              <p>No extracted data available.</p>
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
              <p>No business-rule result available.</p>
            )}
          </div>

          <div className="workflow-document-section">
            <h4>Extracted Text</h4>

            {document.extracted_text ? (
              <pre className="workflow-extracted-text">
                {document.extracted_text}
              </pre>
            ) : (
              <p>No extracted text available.</p>
            )}
          </div>
        </div>
      )}

      {/* Manager selects an outcome and provides a reason. */}
      <form
        className="workflow-decision-form"
        onSubmit={handleSubmit}
      >
        <h4>Review Decision</h4>

        <label htmlFor="manual-review-outcome">
          Outcome
        </label>

        <select
          id="manual-review-outcome"
          value={outcome}
          onChange={(event) => {
            setOutcome(
              event.target.value as ReviewOutcome | "",
            );
            setSubmitError(null);
          }}
          disabled={isDisabled}
          required
        >
          <option value="" disabled>
            Select a review outcome
          </option>

          <option value="resolved">
            Resolved
          </option>

          <option value="rejected">
            Rejected
          </option>

          <option value="information_requested">
            Request Information
          </option>
        </select>

        {/* Request the verified amount only for resolution. */}
        {outcome === "resolved" && (
          <>
            <label htmlFor="corrected-invoice-total">
              Verified Invoice Total
            </label>

            <input
              id="corrected-invoice-total"
              aria-describedby="corrected-invoice-total-help"
              type="number"
              min="0"
              step="any"
              value={correctedTotal}
              onChange={(event) => {
                setCorrectedTotal(event.target.value);
                setSubmitError(null);
              }}
              placeholder="Enter verified amount"
              required
              disabled={
                isDisabled ||
                document?.document_type !== "invoice"
              }
            />

            <p id="corrected-invoice-total-help">
              Business rules will be rechecked using
              this amount. An invoice exceeding 20,000
              will require formal approval.
            </p>

            {document?.document_type !== "invoice" && (
              <p className="workflow-decision-error">
                Automatic resolution currently supports
                invoices only.
              </p>
            )}
          </>
        )}

        <label htmlFor="manual-review-comment">
          Review Comment
        </label>

        <textarea
          id="manual-review-comment"
          value={comment}
          onChange={(event) => {
            setComment(event.target.value);
            setSubmitError(null);
          }}
          placeholder="Explain your review decision..."
          rows={4}
          required
          disabled={isDisabled}
        />

        {submitError && (
          <p
            className="workflow-decision-error"
            role="alert"
          >
            {submitError}
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
              : "Submit Manual Review"}
          </button>

          {/* Cancel the form without closing Workflow Details. */}
          {embedded && (
            <button
              type="button"
              className="workflow-close-button"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel Review
            </button>
          )}
        </div>
      </form>
    </section>
  );
}

export default WorkflowManualReviewPanel;
