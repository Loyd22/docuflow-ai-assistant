export type WorkflowStatus =
  | "needs_review"
  | "needs_information"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "completed";

export type WorkflowPriority =
  | "normal"
  | "urgent";

export type ApprovalDecision =
  | "approved"
  | "rejected"
  | "information_requested";

export type Workflow = {
  id: number;
  document_id: number;
  current_status: WorkflowStatus;
  priority: WorkflowPriority;
  recommended_action: string | null;
  assigned_to: number | null;
  created_at: string;
  updated_at: string;
};

export type ApprovalDecisionRequest = {
  decision: ApprovalDecision;
  comment: string | null;
};

export type Approval = {
  id: number;
  workflow_id: number;
  approver_id: number;
  decision: ApprovalDecision;
  comment: string | null;
  created_at: string;
};

export type WorkflowDecisionResponse = {
  workflow: Workflow;
  approval: Approval;
};