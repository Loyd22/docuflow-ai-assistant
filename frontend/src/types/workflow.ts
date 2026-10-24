
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

// Formal approval types.
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

// Manual-review types.
export type ReviewOutcome =
  | "resolved"
  | "rejected"
  | "information_requested";

export type WorkflowReviewRequest = {
  outcome: ReviewOutcome;
  comment: string;
  corrected_total_amount?: number | null;
};

export type WorkflowReview = {
  id: number;
  workflow_id: number;
  reviewer_id: number;
  outcome: ReviewOutcome;
  comment: string;
  created_at: string;
};

export type WorkflowReviewDecisionResponse = {
  workflow: Workflow;
  review: WorkflowReview;
};

// An information request created by a manager or admin.
export type WorkflowInformationRequest = {
  id: number;
  workflow_id: number;
  approval_id: number | null;
  review_id: number | null;
  requested_by: number;
  request_comment: string;
  requested_at: string;
  response_comment: string | null;
  responded_by: number | null;
  responded_at: string | null;
  return_status: WorkflowStatus;
};

// Information submitted by the document owner.
export type WorkflowInformationResponseRequest = {
  response_comment: string;
};

// Result after an employee answers a request.
export type WorkflowInformationResponseDecisionResponse = {
  workflow: Workflow;
  information_request: WorkflowInformationRequest;
};



/**
 * One decision recorded in a workflow's history.
 */

export type WorkflowHistoryItem = {
  id: number;
  action_type:
    | "approval"
    | "manual_review"
    | "information_response";
  decided_by: number;
  decision: ApprovalDecision | ReviewOutcome | "responded";
  comment: string | null;
  created_at: string;
};


/**
 * Complete approval and manual-review history for a workflow.
 */
export type WorkflowHistoryResponse = {
  workflow_id: number;
  history: WorkflowHistoryItem[];
};
