import { getDocuments } from "./documentApi";
import { getWorkflows } from "./workflowApi";
import { selectRecentWorkflows } from "../utils/recentWorkflows";
import type { Workflow } from "../types/workflow";

export type RecentWorkflowRecord = {
  workflow: Workflow;
  filename: string | null;
};

export async function getRecentWorkflows(): Promise<{
  records: RecentWorkflowRecord[];
  documentsUnavailable: boolean;
}> {
  // Both list endpoints enforce visibility using the existing authenticated client.
  const [workflows, documents] = await Promise.allSettled([getWorkflows(), getDocuments()]);
  if (workflows.status === "rejected") throw workflows.reason;

  const filenames = new Map(
    documents.status === "fulfilled"
      ? documents.value.map((document) => [document.id, document.original_file_name])
      : [],
  );
  return {
    records: selectRecentWorkflows(workflows.value).map((workflow) => ({
      workflow,
      filename: filenames.get(workflow.document_id)?.trim() || null,
    })),
    documentsUnavailable: documents.status === "rejected",
  };
}
