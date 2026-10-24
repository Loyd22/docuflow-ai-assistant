
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import {
  getWorkflowInformationRequest,
  submitWorkflowInformationResponse,
} from "../../api/workflowApi";

import type {
  Workflow,
  WorkflowInformationRequest,
  WorkflowInformationResponseDecisionResponse,
} from "../../types/workflow";

import "./WorkflowDecisionPanel.css";

type WorkflowInformationResponsePanelProps = {
  workflow: Workflow;
  onClose: () => void;
  onResponseComplete: (
    response: WorkflowInformationResponseDecisionResponse,
  ) => void;
};

function WorkflowInformationResponsePanel({
  workflow,
  onClose,
  onResponseComplete,
}: WorkflowInformationResponsePanelProps) {
  const [informationRequest, setInformationRequest] =
    useState<WorkflowInformationRequest | null>(null);

  const [responseComment, setResponseComment] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [submitError, setSubmitError] =
    useState<string | null>(null);

  // Load the manager's unanswered request.
  useEffect(() => {
    let cancelled = false;

    async function loadInformationRequest() {
      setIsLoading(true);
      setInformationRequest(null);
      setErrorMessage(null);

      try {
        const result = await getWorkflowInformationRequest(
          workflow.id,
        );

        if (!cancelled) {
          setInformationRequest(result);
        }
      } catch (error) {
        if (!cancelled) {
          const detail = axios.isAxiosError(error)
            ? error.response?.data?.detail
            : null;

          setErrorMessage(
            typeof detail === "string"
              ? detail
              : "Unable to load the information request.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadInformationRequest();

    return () => {
      cancelled = true;
    };
  }, [workflow.id]);

  // Submit the employee's response to FastAPI.
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setSubmitError(null);

    if (!informationRequest) {
      setSubmitError(
        "The information request must be loaded first.",
      );
      return;
    }

    const cleanResponse = responseComment.trim();

    if (!cleanResponse) {
      setSubmitError("A response is required.");
      return;
    }

    if (cleanResponse.length > 5000) {
      setSubmitError(
        "Your response must not exceed 5000 characters.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await submitWorkflowInformationResponse(
        workflow.id,
        {
          response_comment: cleanResponse,
        },
      );

      onResponseComplete(result);
    } catch (error) {
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : null;

      setSubmitError(
        typeof detail === "string"
          ? detail
          : "Unable to submit your response.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="workflow-decision-panel">
      <div className="workflow-decision-header">
        <div>
          <h3>Respond to Information Request</h3>
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

      {isLoading && (
        <p className="workflow-document-loading" role="status">Loading information request...</p>
      )}

      {errorMessage && (
        <p
          className="workflow-decision-error"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      {informationRequest && (
        <>
          <div className="workflow-document-section">
            <h4>Information Requested</h4>

            <p>{informationRequest.request_comment}</p>

            <p>
              <strong>Requested on:</strong>{" "}
              {new Date(
                informationRequest.requested_at,
              ).toLocaleString()}
            </p>
          </div>

          <form
            className="workflow-decision-form"
            onSubmit={handleSubmit}
          >
            <h4>Your Response</h4>

            <label htmlFor="information-response-comment">
              Response
            </label>

            <textarea
              id="information-response-comment"
              value={responseComment}
              onChange={(event) =>
                setResponseComment(event.target.value)
              }
              placeholder="Provide the information requested by your manager..."
              rows={5}
              maxLength={5000}
              required
              disabled={isSubmitting}
            />

            <p>
              Your response will be sent back for
              manager review. It will not automatically
              approve the document.
            </p>

            {submitError && (
              <p
                className="workflow-decision-error"
                role="alert"
              >
                {submitError}
              </p>
            )}

            <button
              type="submit"
              className="workflow-submit-button"
              disabled={
                isSubmitting || !responseComment.trim()
              }
            >
              {isSubmitting
                ? "Submitting..."
                : "Submit Response"}
            </button>
          </form>
        </>
      )}
    </section>
  );
}

export default WorkflowInformationResponsePanel;
