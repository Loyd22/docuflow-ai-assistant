
import { useEffect, useState } from "react";
import axios from "axios";

import { getDocumentDetails } from "../../api/documentApi";

import OriginalDocumentActions from "../documents/OriginalDocumentActions";
import WorkflowHistoryPanel from "./WorkflowHistoryPanel";

import type { DocumentDetail } from "../../types/document";

import WorkflowDecisionPanel from "./WorkflowDecisionPanel";
import WorkflowManualReviewPanel from "./WorkflowManualReviewPanel";
import WorkflowInformationResponsePanel from "./WorkflowInformationResponsePanel";

import type { Workflow,WorkflowDecisionResponse,WorkflowInformationResponseDecisionResponse, WorkflowReviewDecisionResponse } from "../../types/workflow";
import WorkflowAIAnalysisPanel from "./WorkflowAIAnalysisPanel";

import "./WorkflowDetailsPanel.css";

type WorkflowDetailsPanelProps = {
  workflow: Workflow;
  onClose: () => void;
  canMakeDecisions: boolean;
  canRespondToRequests: boolean;
  onDecisionComplete: (
    response:
      | WorkflowDecisionResponse
      | WorkflowReviewDecisionResponse
      | WorkflowInformationResponseDecisionResponse,
  ) => void;
};

// Make backend values easier to read.
function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

// Display timestamps in the user's local timezone.
function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleString();
}

export default function WorkflowDetailsPanel({
  workflow,
  onClose,
  canMakeDecisions,
  canRespondToRequests,
  onDecisionComplete,
}: WorkflowDetailsPanelProps) {
  const [document, setDocument] =
    useState<DocumentDetail | null>(null);

  const [isDocumentLoading, setIsDocumentLoading] =
    useState(true);

  const [documentError, setDocumentError] =
    useState<string | null>(null);

  // Track whether the manager has opened a decision form.
  const [showDecisionForm, setShowDecisionForm] = useState(false);  

  // Load the document belonging to the selected workflow.
  useEffect(() => {
    let isActive = true;

    async function loadDocument() {
      setIsDocumentLoading(true);
      setDocument(null);
      setDocumentError(null);

      try {
        const result = await getDocumentDetails(
          workflow.document_id,
        );

        if (isActive) {
          setDocument(result);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }

        const detail = axios.isAxiosError(error)
          ? error.response?.data?.detail
          : null;

        setDocumentError(
          typeof detail === "string"
            ? detail
            : "Unable to load document information.",
        );
      } finally {
        if (isActive) {
          setIsDocumentLoading(false);
        }
      }
    }

    void loadDocument();

    // Ignore old requests when switching documents.
    return () => {
      isActive = false;
    };
  }, [workflow.document_id]);

 
  // Check the workflow's current status.
  const isManualReview =
    workflow.current_status === "needs_review";

  const isPendingApproval =
    workflow.current_status === "pending_approval";

  const needsInformation =
    workflow.current_status === "needs_information";

  // Determine which action the user's role can perform.
  const canStartManagerAction =
    canMakeDecisions && (isManualReview || isPendingApproval);

  const canStartEmployeeAction =
    canRespondToRequests && needsInformation;

  const canStartAction =
    canStartManagerAction || canStartEmployeeAction;

  // Display the correct button text.
  const actionLabel = canStartEmployeeAction
    ? "Respond to Information Request"
    : isManualReview
      ? "Start Manual Review"
      : "Make Approval Decision";

  return (
    <section
      className="workflow-details-panel"
      aria-label={`Workflow #${workflow.id} details`}
    >
      <div className="workflow-details-header">
        <div>
          <h3>Workflow #{workflow.id}</h3>
          <p>Document #{workflow.document_id}</p>
        </div>

        <button
          type="button"
          className="workflow-details-close"
          onClick={() => onClose()}
        >
          Close Details
        </button>
      </div>

      {/* Display workflow information. */}
      <div className="workflow-details-grid">
        <div className="workflow-detail-field">
          <span>Current Status</span>
          <strong>
            {formatLabel(workflow.current_status)}
          </strong>
        </div>

        <div className="workflow-detail-field">
          <span>Priority</span>
          <strong>{formatLabel(workflow.priority)}</strong>
        </div>

        <div className="workflow-detail-field">
          <span>Assigned Reviewer</span>
          <strong>
            {workflow.assigned_to === null
              ? "Unassigned"
              : `User #${workflow.assigned_to}`}
          </strong>
        </div>

        <div className="workflow-detail-field">
          <span>Recommended Action</span>
          <strong>
            {workflow.recommended_action
              ? formatLabel(workflow.recommended_action)
              : "None"}
          </strong>
        </div>

        <div className="workflow-detail-field">
          <span>Created</span>
          <strong>{formatDate(workflow.created_at)}</strong>
        </div>

        <div className="workflow-detail-field">
          <span>Last Updated</span>
          <strong>{formatDate(workflow.updated_at)}</strong>
        </div>
      </div>

      {/* Retrieve and display the related document. */}
      <div className="workflow-document-details">
        <h4>Document Information</h4>

        {isDocumentLoading && (
          <p role="status">
            Loading document information...
          </p>
        )}

        {documentError && (
          <p
            role="alert"
            className="workflow-error-message"
          >
            {documentError}
          </p>
        )}

        {!isDocumentLoading && document && (
          <>
            <div className="workflow-details-grid">
              <div className="workflow-detail-field">
                <span>File Name</span>
                <strong>
                  {document.original_file_name}
                </strong>
              </div>

              <div className="workflow-detail-field">
                <span>Document Type</span>
                <strong>
                  {formatLabel(document.document_type)}
                </strong>
              </div>

              <div className="workflow-detail-field">
                <span>Processing Status</span>
                <strong>
                  {formatLabel(document.status)}
                </strong>
              </div>

              <div className="workflow-detail-field">
                <span>Uploaded By</span>
                <strong>
                  User #{document.uploaded_by}
                </strong>
              </div>

              <div className="workflow-detail-field">
                <span>File Size</span>
                <strong>
                  {(document.file_size / 1024).toFixed(1)} KB
                </strong>
              </div>

              <div className="workflow-detail-field">
                <span>AI Confidence</span>
                <strong>
                  {document.classification_confidence === null
                    ? "Not available"
                    : `${(
                        document.classification_confidence * 100
                      ).toFixed(1)}%`}
                </strong>
              </div>
            </div>

            {/* Display the AI summary when available. */}
            {document.summary && (
              <div className="workflow-document-summary">
                <h5>AI Summary</h5>
                <p>{document.summary}</p>
              </div>
            )}

            {/* Reuse existing authorized file actions. */}
            <OriginalDocumentActions
              documentId={document.id}
              originalFileName={document.original_file_name}
            />
          </>
        )}
      </div>
      {/* Show AI-extracted fields and business-rule results. */}
      {!isDocumentLoading && document && (
        <WorkflowAIAnalysisPanel document={document} />
      )}

      
    {/* Let managers open the decision form inside the details panel. */}
    {canStartAction && (
      <div className="workflow-details-actions">
        <h4>Next Action</h4>

        <p>
          Review the document information before making
          your decision.
        </p>

        {!showDecisionForm && (
          <button
            type="button"
            className="workflow-review-button"
            onClick={() => setShowDecisionForm(true)}
          >
            {actionLabel}
          </button>
        )}
      </div>
    )}

    {/* Show the appropriate decision form within Workflow Details. */}
    
      {/* Show the approval form inside Workflow Details. */}
      {canStartAction &&
        showDecisionForm &&
        workflow.current_status === "pending_approval" && (
          <WorkflowDecisionPanel
            workflow={workflow}
            documentDetails={document ?? undefined}
            embedded
            onClose={() => setShowDecisionForm(false)}
            onDecisionComplete={onDecisionComplete}
          />
        )}


    {canStartAction &&
      showDecisionForm &&
      workflow.current_status === "needs_review" && (
       
    <WorkflowManualReviewPanel
      workflow={workflow}
      documentDetails={document ?? undefined}
      embedded
      onClose={() => setShowDecisionForm(false)}
      onReviewComplete={onDecisionComplete}
    />

      )}

      
      {/* Allow employees to answer a manager's information request. */}
      {canStartEmployeeAction && showDecisionForm && (
        <WorkflowInformationResponsePanel
          workflow={workflow}
          onClose={() => setShowDecisionForm(false)}
          onResponseComplete={onDecisionComplete}
        />
      )}



      {/* Display previous decisions for the workflow. */}
      <WorkflowHistoryPanel
        key={workflow.id}
        workflowId={workflow.id}
        onClose={onClose}
      />
    </section>
  );
}
