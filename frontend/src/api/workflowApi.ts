import { apiClient } from "./client";

import type {
  ApprovalDecisionRequest,
  Workflow,
  WorkflowDecisionResponse,
} from "../types/workflow";

export async function getWorkflows(): Promise<Workflow[]> {
  const response =
    await apiClient.get<Workflow[]>("/workflows");

  return response.data;
}

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