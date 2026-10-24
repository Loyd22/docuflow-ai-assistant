
import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

import { getDashboardSummary } from "../api/dashboardApi";
import { useAuth } from "../auth/useAuth";
import RecentWorkflows from "../components/dashboard/RecentWorkflows";
import SummaryCard from "../components/dashboard/SummaryCard";
import ShellIcon from "../layouts/ShellIcon";

import type { DashboardSummary } from "../types/dashboard";

import "./DashboardPage.css";

// Convert technical status names into readable labels.
function formatLabel(value: string): string {
  const labels: Record<string, string> = {
    ai_processing: "AI Processing",
    ai_processing_failed: "AI Processing Failed",
    sop: "Standard Operating Procedure (SOP)",
    hr_form: "HR Form",
  };
  if (labels[value]) return labels[value];

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function DashboardPage() {
  const { user } = useAuth();

  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  // Determine which dashboard experience to display.
  const role = String(user?.role ?? "").toLowerCase();

  const isManagerOrAdmin =
    role === "manager" || role === "admin";

  // Retrieve dashboard metrics from FastAPI.
  useEffect(() => {
    let isActive = true;

    async function loadDashboard() {
      try {
        const result = await getDashboardSummary();

        if (isActive) {
          setSummary(result);
          setErrorMessage(null);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }

        const detail = axios.isAxiosError(error)
          ? error.response?.data?.detail
          : null;

        setErrorMessage(
          typeof detail === "string"
            ? detail
            : "Unable to load dashboard data.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      isActive = false;
    };
  }, []);

  if (isLoading) {
    return (
      <section className="dashboard-page">
        <h2>Dashboard</h2>
        <p className="dashboard-state" role="status">Loading dashboard...</p>
      </section>
    );
  }

  if (errorMessage) {
    return (
      <section className="dashboard-page">
        <h2>Dashboard</h2>
        <p className="dashboard-state dashboard-state-error" role="alert">{errorMessage}</p>
      </section>
    );
  }

  if (!summary) {
    return (
      <section className="dashboard-page">
        <h2>Dashboard</h2>
        <p className="dashboard-state">No dashboard data is available.</p>
      </section>
    );
  }

  const workflowCounts = summary.workflows_by_status;
  const documentCounts = summary.documents_by_status;

  // These are summary totals, not necessarily assigned-user counts.
  const requiresManagerAction =
    workflowCounts.needs_review +
    workflowCounts.pending_approval;

  const documentsByStatus = Object.entries(
    documentCounts,
  );

  const documentsByType = Object.entries(
    summary.documents_by_type,
  );

  return (
    <section className="dashboard-page">
      <div className="dashboard-heading">
        <div>
          <h2>
            {isManagerOrAdmin
              ? "Manager Dashboard"
              : "Document Dashboard"}
          </h2>

          <p>
            {isManagerOrAdmin
              ? "Monitor document approvals, manual reviews, and workflow progress."
              : "Monitor your document processing and workflow progress."}
          </p>
        </div>

        <div className="dashboard-heading-actions">
          <Link
            to="/workflows"
            className="dashboard-primary-link"
          >
            View Workflows
          </Link>

          <Link
            to="/documents"
            className="dashboard-secondary-link"
          >
            View Documents
          </Link>
        </div>
      </div>

      {isManagerOrAdmin && (
        <section className="dashboard-section">
          <div className="dashboard-section-heading">
            <h3>Workflow Priorities</h3>
            <p className="dashboard-section-note">
              Overall workflow counts, not assignments to you.
            </p>
          </div>
          <div className="dashboard-priority-grid">
            <SummaryCard label="Pending Approval" value={workflowCounts.pending_approval} href="/workflows?status=pending_approval"
              icon={<ShellIcon name="audit" />} tone="blue"
              description="Awaiting an approval decision." />
            <SummaryCard label="Needs Manual Review" value={workflowCounts.needs_review} href="/workflows?status=needs_review"
              icon={<ShellIcon name="documents" />} tone="amber"
              description="Requiring human verification." />
            <SummaryCard label="Needs Information" value={workflowCounts.needs_information} href="/workflows?status=needs_information"
              icon={<ShellIcon name="workflows" />} tone="violet"
              description="Awaiting additional information; excluded from the action total." />
            <SummaryCard label="Total Requiring Action" value={requiresManagerAction}
              icon={<ShellIcon name="dashboard" />} tone="blue" emphasis
              description="Pending approvals + manual reviews." />
          </div>
        </section>
      )}

      {summary.total_documents === 0 && summary.total_workflows === 0 && (
        <p className="dashboard-state" role="status">
          No documents or workflows yet. Counts will appear here as documents are processed.
        </p>
      )}

      {/* Summary metrics for all authenticated roles. */}
      <section className="dashboard-section">
        <h3>Overall Summary</h3>

        <div className="summary-grid">
          <SummaryCard
            label="Total Documents"
            value={summary.total_documents}
            icon={<ShellIcon name="documents" />}
          />

          <SummaryCard
            label="Total Workflows"
            value={summary.total_workflows}
            icon={<ShellIcon name="workflows" />}
          />

        </div>
      </section>

      {/* Employees can also monitor workflow statuses. */}
      {!isManagerOrAdmin && (
        <section className="dashboard-section">
          <h3>Workflow Progress</h3>

          <div className="metric-grid">
            <SummaryCard
              label="Needs Manual Review"
              value={workflowCounts.needs_review} href="/workflows?status=needs_review"
            />

            <SummaryCard
              label="Needs Information"
              value={workflowCounts.needs_information} href="/workflows?status=needs_information"
            />

            <SummaryCard
              label="Pending Approval"
              value={workflowCounts.pending_approval} href="/workflows?status=pending_approval"
            />

          </div>

          <p className="dashboard-section-note">
            Open Workflows to check the details and
            respond to information requests.
          </p>

          <Link
            to="/workflows"
            className="dashboard-text-link"
          >
            View Workflow Details →
          </Link>
        </section>
      )}

      {isManagerOrAdmin && <RecentWorkflows />}

      {/* Display final workflow outcomes. */}
      <section className="dashboard-section">
        <h3>Workflow Outcomes</h3>

        <div className="metric-grid">
          <SummaryCard
            label="Approved"
            value={workflowCounts.approved}
          />

          <SummaryCard
            label="Rejected"
            value={workflowCounts.rejected}
          />

          <SummaryCard
            label="Completed"
            value={workflowCounts.completed}
          />
        </div>
      </section>

      {/* Keep the existing processing metrics. */}
      <section className="dashboard-section">
        <h3>Document Processing</h3>

        <p className="dashboard-section-note">
          Monitor documents through extraction and AI
          analysis.
        </p>

        <div className="metric-grid">
          {documentsByStatus.map(([status, count]) => (
            <SummaryCard
              key={status}
              label={formatLabel(status)}
              value={count}
            />
          ))}
        </div>
      </section>

      {/* Display all supported document types. */}
      <section className="dashboard-section">
        <h3>Documents by Type</h3>

        <div className="metric-grid">
          {documentsByType.map(([type, count]) => (
            <SummaryCard
              key={type}
              label={formatLabel(type)}
              value={count}
            />
          ))}
        </div>
      </section>
    </section>
  );
}

export default DashboardPage;
