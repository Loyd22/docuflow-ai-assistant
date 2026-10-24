
import { apiClient } from "./client";


import type {
  ApprovalDecisionRequest,
  Workflow,
  WorkflowDecisionResponse,
  WorkflowHistoryResponse,
  WorkflowInformationRequest,
  WorkflowInformationResponseDecisionResponse,
  WorkflowInformationResponseRequest,
  WorkflowReviewDecisionResponse,
  WorkflowReviewRequest,
} from "../types/workflow";


// Retrieve workflows visible to the current user.
export async function getWorkflows(): Promise<Workflow[]> {
  const response =
    await apiClient.get<Workflow[]>("/workflows");

  return response.data;
}

// Submit a formal approval decision.
export async function submitWorkflowDecision(
  workflowId: number,
  request: ApprovalDecisionRequest,
): Promise<WorkflowDecisionResponse> {
  const response =
    await apiClient.post<WorkflowDecisionResponse>(
      `/workflows/${workflowId}/decision`,
      request,
    );

  return response.data;
}

// Submit a manual-review decision.
export async function submitManualReview(
  workflowId: number,
  request: WorkflowReviewRequest,
): Promise<WorkflowReviewDecisionResponse> {
  const response =
    await apiClient.post<WorkflowReviewDecisionResponse>(
      `/workflows/${workflowId}/review`,
      request,
    );

  return response.data;
}

// Retrieve the manager's unanswered information request.
export async function getWorkflowInformationRequest(
  workflowId: number,
): Promise<WorkflowInformationRequest> {
  const response =
    await apiClient.get<WorkflowInformationRequest>(
      `/workflows/${workflowId}/information-request`,
    );

  return response.data;
}

// Submit the employee's response to an information request.
export async function submitWorkflowInformationResponse(
  workflowId: number,
  request: WorkflowInformationResponseRequest,
): Promise<WorkflowInformationResponseDecisionResponse> {
  const response =
    await apiClient.post<WorkflowInformationResponseDecisionResponse>(
      `/workflows/${workflowId}/information-response`,
      request,
    );

  return response.data;
}



// Retrieve approval and manual-review history for one workflow.
export async function getWorkflowHistory(
  workflowId: number,
): Promise<WorkflowHistoryResponse> {
  const response = await apiClient.get<WorkflowHistoryResponse>(
    `/workflows/${workflowId}/history`,
  );

  return response.data;
}
