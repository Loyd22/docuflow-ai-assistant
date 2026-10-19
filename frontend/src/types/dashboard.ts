export type DocumentStatusCounts = {
  uploaded: number;
  processing: number;
  text_extracted: number;
  processing_failed: number;
  ai_processing: number;
  analyzed: number;
  ai_processing_failed: number;
};

export type DocumentTypeCounts = {
  invoice: number;
  contract: number;
  sop: number;
  hr_form: number;
  purchase_request: number;
  policy: number;
  business_report: number;
  support_ticket: number;
  digital_form: number;
  memo: number;
  unknown: number;
};

export type WorkflowStatusCounts = {
  needs_review: number;
  needs_information: number;
  pending_approval: number;
  approved: number;
  rejected: number;
  completed: number;
};

export type DashboardSummary = {
  total_documents: number;
  documents_by_status: DocumentStatusCounts;
  documents_by_type: DocumentTypeCounts;
  total_workflows: number;
  workflows_by_status: WorkflowStatusCounts;
};