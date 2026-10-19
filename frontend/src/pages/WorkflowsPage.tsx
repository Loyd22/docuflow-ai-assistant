import {
  useEffect,
  useState,
} from "react";
import axios from "axios";

import { getWorkflows } from "../api/workflowApi";
import { useAuth } from "../auth/useAuth";
import WorkflowDecisionPanel from "../components/workflows/WorkflowDecisionPanel";
import WorkflowTable from "../components/workflows/WorkflowTable";
import type {
  Workflow,
  WorkflowDecisionResponse,
} from "../types/workflow";

import "./WorkflowsPage.css";

function WorkflowsPage() {
  const { user } = useAuth();

  const [workflows, setWorkflows] =
    useState<Workflow[]>([]);

  const [
    selectedWorkflowId,
    setSelectedWorkflowId,
  ] = useState<number | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  const canMakeDecisions =
    user?.role === "manager" ||
    user?.role === "admin";

  const selectedWorkflow =
    workflows.find(
      (workflow) =>
        workflow.id === selectedWorkflowId,
    ) ?? null;

  async function loadWorkflows() {
    try {
      setErrorMessage(null);

      const workflowList =
        await getWorkflows();

      setWorkflows(workflowList);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail =
          error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to load workflows.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to load workflows.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadWorkflows();
  }, []);

  function handleReview(
    workflowId: number,
  ) {
    setSelectedWorkflowId(workflowId);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function handleDecisionComplete(
    response: WorkflowDecisionResponse,
  ) {
    setWorkflows((currentWorkflows) =>
      currentWorkflows.map((workflow) =>
        workflow.id === response.workflow.id
          ? response.workflow
          : workflow,
      ),
    );

    setSelectedWorkflowId(null);

    setSuccessMessage(
      `Workflow #${response.workflow.id} updated to ${response.workflow.current_status.replaceAll(
        "_",
        " ",
      )}.`,
    );
  }

  return (
    <section className="workflows-page">
      <div className="workflows-heading">
        <div>
          <h2>Workflows</h2>

          <p>
            Review document workflow status and approval decisions.
          </p>
        </div>
      </div>

      {errorMessage && (
        <p
          className="workflow-message workflow-error"
          role="alert"
        >
          {errorMessage}
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
        <p>Loading workflows...</p>
      ) : workflows.length === 0 ? (
        <div className="empty-workflows">
          <h3>No workflows yet</h3>

          <p>
            Workflows will appear after documents are analyzed.
          </p>
        </div>
      ) : (
        <>
          <WorkflowTable
            workflows={workflows}
            canMakeDecisions={canMakeDecisions}
            onDecision={handleReview}
          />

          {selectedWorkflow && (
            <WorkflowDecisionPanel
              workflow={selectedWorkflow}
              onClose={() =>
                setSelectedWorkflowId(null)
              }
              onDecisionComplete={
                handleDecisionComplete
              }
            />
          )}
        </>
      )}
    </section>
  );
}

export default WorkflowsPage;