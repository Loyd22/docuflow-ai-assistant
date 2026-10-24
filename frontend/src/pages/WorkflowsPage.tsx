
import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";

import { getWorkflows } from "../api/workflowApi";
import { useAuth } from "../auth/useAuth";

import WorkflowDecisionPanel from "../components/workflows/WorkflowDecisionPanel";
import WorkflowDetailsPanel from "../components/workflows/WorkflowDetailsPanel";
import WorkflowInformationResponsePanel from "../components/workflows/WorkflowInformationResponsePanel";
import WorkflowManualReviewPanel from "../components/workflows/WorkflowManualReviewPanel";
import WorkflowTable from "../components/workflows/WorkflowTable";

import type {
  Workflow,
  WorkflowStatus,
  WorkflowDecisionResponse,
  WorkflowInformationResponseDecisionResponse,
  WorkflowReviewDecisionResponse,
} from "../types/workflow";

import "./WorkflowsPage.css";
import "../styles/WorkspacePages.css";
import { workflowStatusLabels } from "../utils/recentWorkflows";

function WorkflowsPage() {
  const { user } = useAuth();

  // Store workflows visible to the logged-in user.
  const [workflows, setWorkflows] = useState<Workflow[]>([]);

  // Track the workflow selected for an action.
  const [selectedWorkflowId, setSelectedWorkflowId] =
    useState<number | null>(null);

  // Track the workflow selected for viewing details.
  const [searchParams, setSearchParams] = useSearchParams();
  const statusParam = searchParams.get("status");
  const activeStatus = statusParam && Object.hasOwn(workflowStatusLabels, statusParam)
    ? statusParam as WorkflowStatus : null;
  const filteredWorkflows = activeStatus
    ? workflows.filter((workflow) => workflow.current_status === activeStatus)
    : workflows;

  function setStatusFilter(status: string) {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      if (status) next.set("status", status);
      else next.delete("status");
      return next;
    });
  }

  const workflowParam = searchParams.get("workflow");
  const parsedWorkflowId = Number(workflowParam);
  const detailsWorkflowId = workflowParam && /^\d+$/.test(workflowParam) &&
    Number.isSafeInteger(parsedWorkflowId) && parsedWorkflowId > 0
    ? parsedWorkflowId : null;
  const detailsPanelRef = useRef<HTMLDivElement>(null);

  function setDetailsWorkflowId(workflowId: number | null) {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      if (workflowId === null) next.delete("workflow");
      else next.set("workflow", String(workflowId));
      return next;
    }, { replace: true });
  }

  const [isLoading, setIsLoading] = useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  // Managers and admins can review and approve workflows.
  const canMakeDecisions =
    user?.role === "manager" ||
    user?.role === "admin";

  // Employees can answer requests for their own documents.
  const canRespondToRequests = user?.role === "employee";

  // Find the workflow selected for a review or response.
  const selectedWorkflow =
    workflows.find(
      (workflow) => workflow.id === selectedWorkflowId,
    ) ?? null;

  // Find the workflow selected for viewing details.
  const detailsWorkflow =
    workflows.find(
      (workflow) => workflow.id === detailsWorkflowId,
    ) ?? null;

  const visibleDetailsId = detailsWorkflow?.id;
  useEffect(() => {
    if (visibleDetailsId) {
      detailsPanelRef.current?.focus();
      detailsPanelRef.current?.scrollIntoView?.({ block: "start" });
    }
  }, [visibleDetailsId]);

  // Retrieve workflows visible to the current user.
  async function loadWorkflows() {
    try {
      setErrorMessage(null);

      const workflowList = await getWorkflows();

      setWorkflows(workflowList);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        setErrorMessage(
          typeof detail === "string"
            ? detail
            : "Unable to load workflows.",
        );
      } else {
        setErrorMessage("Unable to load workflows.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadWorkflows();
  }, []);

  // Open the appropriate action panel for the selected workflow.
  function handleReview(workflowId: number) {
    const workflow = workflows.find(
      (item) => item.id === workflowId,
    );

    if (!workflow) {
      return;
    }

    const canOpenReview =
      canMakeDecisions &&
      (workflow.current_status === "needs_review" ||
        workflow.current_status === "pending_approval");

    const canOpenResponse =
      canRespondToRequests &&
      workflow.current_status === "needs_information";

    if (!canOpenReview && !canOpenResponse) {
      return;
    }

    // Close details when opening a workflow action.
    setDetailsWorkflowId(null);

    setSelectedWorkflowId(workflowId);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  // Open details for a workflow visible to the current user.
  function handleViewDetails(workflowId: number) {
    const workflowExists = workflows.some(
      (workflow) => workflow.id === workflowId,
    );

    if (!workflowExists) {
      return;
    }

    // Close action panels when opening workflow details.
    setSelectedWorkflowId(null);

    setDetailsWorkflowId(workflowId);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  // Update the workflow after a successful decision or response.
  function handleDecisionComplete(
    response:
      | WorkflowDecisionResponse
      | WorkflowReviewDecisionResponse
      | WorkflowInformationResponseDecisionResponse,
  ) {
    // Update the table without reloading the page.
    setWorkflows((currentWorkflows) =>
      currentWorkflows.map((workflow) =>
        workflow.id === response.workflow.id
          ? response.workflow
          : workflow,
      ),
    );

    // Close open panels after a successful action.
    setSelectedWorkflowId(null);
    setDetailsWorkflowId(null);

    const updatedStatus =
      response.workflow.current_status.replaceAll("_", " ");

    setSuccessMessage(
      `Workflow #${response.workflow.id} updated to ${updatedStatus}.`,
    );
  }

  return (
    <section className="workflows-page">
      <div className="workflows-heading">
        <div>
          <h2>Workflows</h2>

          <p>
            View document workflows, review decisions,
            and respond to information requests.
          </p>
        </div>
      </div>

      <div className="workflow-filters">
        <label htmlFor="workflow-status-filter">Workflow status</label>
        <select id="workflow-status-filter" value={activeStatus ?? ""}
          onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(workflowStatusLabels).map(([status, label]) => (
            <option key={status} value={status}>{label}</option>
          ))}
        </select>
        {statusParam !== null && (
          <button type="button" className="workflow-history-button" onClick={() => setStatusFilter("")}>Clear filter</button>
        )}
        {!isLoading && !errorMessage && <span className="workflow-filter-count" role="status">
          Showing {filteredWorkflows.length} of {workflows.length} workflows
        </span>}
        {statusParam !== null && !activeStatus && (
          <p className="workflow-filter-note">Unknown status filter. Showing all workflows.</p>
        )}
      </div>

      {errorMessage && (
        <p
          className="workflow-message workflow-error"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      {!isLoading && !errorMessage && workflowParam !== null && !detailsWorkflow && (
        <p className="workflow-message workflow-error" role="alert">
          This workflow is unavailable or you do not have access to it.
        </p>
      )}

      {successMessage && (
        <p
          className="workflow-message workflow-success"
          role="status"
        >
          {successMessage}
        </p>
      )}

      {isLoading ? (
        <p className="workspace-loading" role="status">Loading workflows...</p>
      ) : errorMessage && workflows.length === 0 ? null : workflows.length === 0 ? (
        <div className="empty-workflows">
          <h3>No workflows yet</h3>

          <p>
            Workflows will appear after documents are analyzed.
          </p>
        </div>
      ) : (
        <>
          {filteredWorkflows.length === 0 ? (
            <div className="empty-workflows">
              <h3>No workflows match this status</h3>
              <p>Choose another status or clear the filter to see all visible workflows.</p>
            </div>
          ) : <WorkflowTable
            workflows={filteredWorkflows}
            canMakeDecisions={canMakeDecisions}
            canRespondToRequests={canRespondToRequests}
            onDecision={handleReview}
            onViewHistory={handleViewDetails}
          />}

          {/* Manager/admin: Resolve manual reviews. */}
          {canMakeDecisions &&
            selectedWorkflow?.current_status === "needs_review" && (
              <WorkflowManualReviewPanel
                workflow={selectedWorkflow}
                onClose={() => setSelectedWorkflowId(null)}
                onReviewComplete={handleDecisionComplete}
              />
            )}

          {/* Manager/admin: Make formal approval decisions. */}
          {canMakeDecisions &&
            selectedWorkflow?.current_status === "pending_approval" && (
              <WorkflowDecisionPanel
                workflow={selectedWorkflow}
                onClose={() => setSelectedWorkflowId(null)}
                onDecisionComplete={handleDecisionComplete}
              />
            )}

          {/* Employee: Answer an information request. */}
          {canRespondToRequests &&
            selectedWorkflow?.current_status === "needs_information" && (
              <WorkflowInformationResponsePanel
                workflow={selectedWorkflow}
                onClose={() => setSelectedWorkflowId(null)}
                onResponseComplete={handleDecisionComplete}
              />
            )}

          {/* Display workflow information and decision history. */}

          {/* Display document details and manage decisions in one panel. */}
        {detailsWorkflow && (
      <div ref={detailsPanelRef} tabIndex={-1} aria-label={`Workflow #${detailsWorkflow.id} details`}>
      <WorkflowDetailsPanel
        key={detailsWorkflow.id}
        workflow={detailsWorkflow}
        canMakeDecisions={canMakeDecisions}
        canRespondToRequests={canRespondToRequests}
        onDecisionComplete={handleDecisionComplete}
        onClose={() => setDetailsWorkflowId(null)}
      />
      </div>
    )}

        </>
      )}
    </section>
  );
}

export default WorkflowsPage;
