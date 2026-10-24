import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getRecentWorkflows, type RecentWorkflowRecord } from "../../api/recentWorkflowsApi";
import { formatWorkflowUpdatedAt, workflowStatusLabels } from "../../utils/recentWorkflows";
import "./RecentWorkflows.css";

export default function RecentWorkflows() {
  const [records, setRecords] = useState<RecentWorkflowRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [documentsUnavailable, setDocumentsUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    getRecentWorkflows().then((result) => {
      if (!active) return;
      setRecords(result.records);
      setDocumentsUnavailable(result.documentsUnavailable);
    }).catch(() => {
      if (active) setError(true);
    }).finally(() => {
      if (active) setIsLoading(false);
    });
    return () => { active = false; };
  }, []);

  return (
    <section className="recent-workflows" aria-labelledby="recent-workflows-title">
      <div className="recent-workflows-heading">
        <div>
          <h3 id="recent-workflows-title">Recent Workflows</h3>
          <p>The five most recently updated workflows visible to you.</p>
        </div>
        <Link className="dashboard-text-link" to="/workflows">View All →</Link>
      </div>
      {isLoading ? <p className="recent-workflows-message" role="status">Loading recent workflows...</p>
        : error ? <p className="recent-workflows-message" role="alert">Unable to load recent workflows. Open View All to try the workflow list.</p>
        : records.length === 0 ? <p className="recent-workflows-message">No workflows yet. Workflows appear after documents are analyzed.</p>
        : <>
          {documentsUnavailable && <p className="recent-workflows-message" role="status">Document names are unavailable. Document IDs are shown instead.</p>}
          <div className="recent-workflows-scroll" role="region" aria-label="Recent workflows table" tabIndex={0}>
            <table>
              <thead><tr>
                <th scope="col">Workflow ID</th><th scope="col">Document</th>
                <th scope="col">Status</th><th scope="col">Priority</th>
                <th scope="col">Last Updated</th><th scope="col">Action</th>
              </tr></thead>
              <tbody>{records.map(({ workflow, filename }) => (
                <tr key={workflow.id}>
                  <th scope="row">#{workflow.id}</th>
                  <td className="recent-workflows-document">{filename ?? `Document #${workflow.document_id} (filename unavailable)`}</td>
                  <td><span className={`recent-workflows-status recent-workflows-status-${workflow.current_status}`}>
                    {workflowStatusLabels[workflow.current_status] ?? "Unknown status"}
                  </span></td>
                  <td><span className={`recent-workflows-priority recent-workflows-priority-${workflow.priority}`}>
                    {workflow.priority === "urgent" ? "Urgent" : workflow.priority === "normal" ? "Normal" : "Unavailable"}
                  </span></td>
                  <td className="recent-workflows-date">{formatWorkflowUpdatedAt(workflow.updated_at)}</td>
                  <td><Link className="recent-workflows-open" to={`/workflows?workflow=${workflow.id}`} aria-label={`Open workflow #${workflow.id}`}>Open →</Link></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>}
    </section>
  );
}
