import type { Workflow, WorkflowStatus } from "../types/workflow";

export const workflowStatusLabels: Record<WorkflowStatus, string> = {
  needs_review: "Needs Manual Review",
  needs_information: "Needs Information",
  pending_approval: "Pending Approval",
  approved: "Approved",
  rejected: "Rejected",
  completed: "Completed",
};

export function workflowUpdatedTime(value: string): number {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function selectRecentWorkflows(workflows: Workflow[]): Workflow[] {
  return [...workflows]
    .sort((a, b) => workflowUpdatedTime(b.updated_at) - workflowUpdatedTime(a.updated_at) || b.id - a.id)
    .slice(0, 5);
}

export function formatWorkflowUpdatedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unavailable" : date.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}
