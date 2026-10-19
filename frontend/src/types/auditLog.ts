export type AuditEntityType =
  | "user"
  | "document"
  | "workflow"
  | "approval"
  | "system";

export type AuditAction =
  | "user_registered"
  | "user_logged_in"
  | "document_uploaded"
  | "document_text_extracted"
  | "document_classified"
  | "document_fields_extracted"
  | "rule_check_completed"
  | "workflow_created"
  | "workflow_approved"
  | "workflow_rejected"
  | "workflow_information_requested";

export type AuditLog = {
  id: number;
  user_id: number | null;
  action: AuditAction;
  entity_type: AuditEntityType;
  entity_id: number | null;
  event_metadata: Record<string, unknown> | null;
  created_at: string;
};