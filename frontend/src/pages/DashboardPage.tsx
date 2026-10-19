import {
  useEffect,
  useState,
} from "react";
import axios from "axios";

import { getDashboardSummary } from "../api/dashboardApi";
import SummaryCard from "../components/dashboard/SummaryCard";
import type { DashboardSummary } from "../types/dashboard";

import "./DashboardPage.css";

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(
    null,
  );

  const [isLoading, setIsLoading] = useState(true);

  const [errorMessage, setErrorMessage] = useState<string | null>(
    null,
  );

  useEffect(() => {
    async function loadDashboard() {
      try {
        const dashboardSummary = await getDashboardSummary();

        setSummary(dashboardSummary);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detail = error.response?.data?.detail;

          if (typeof detail === "string") {
            setErrorMessage(detail);
          } else {
            setErrorMessage("Unable to load dashboard data.");
          }
        } else {
          setErrorMessage("Unable to load dashboard data.");
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (isLoading) {
    return (
      <section>
        <h2>Dashboard</h2>
        <p>Loading dashboard...</p>
      </section>
    );
  }

  if (errorMessage) {
    return (
      <section>
        <h2>Dashboard</h2>

        <p role="alert">
          {errorMessage}
        </p>
      </section>
    );
  }

  if (!summary) {
    return (
      <section>
        <h2>Dashboard</h2>
        <p>No dashboard data is available.</p>
      </section>
    );
  }

  return (
    <section className="dashboard-page">
      <div className="dashboard-heading">
        <h2>Dashboard</h2>

        <p>
          Overview of DocuFlow documents and workflows.
        </p>
      </div>

      <div className="summary-grid">
        <SummaryCard
          label="Total Documents"
          value={summary.total_documents}
        />

        <SummaryCard
          label="Total Workflows"
          value={summary.total_workflows}
        />
      </div>

      <section className="dashboard-section">
        <h3>Documents by Status</h3>

        <div className="metric-grid">
          <SummaryCard
            label="Uploaded"
            value={summary.documents_by_status.uploaded}
          />

          <SummaryCard
            label="Processing"
            value={summary.documents_by_status.processing}
          />

          <SummaryCard
            label="Text Extracted"
            value={summary.documents_by_status.text_extracted}
          />

          <SummaryCard
            label="Processing Failed"
            value={summary.documents_by_status.processing_failed}
          />

          <SummaryCard
            label="AI Processing"
            value={summary.documents_by_status.ai_processing}
          />

          <SummaryCard
            label="Analyzed"
            value={summary.documents_by_status.analyzed}
          />

          <SummaryCard
            label="AI Processing Failed"
            value={summary.documents_by_status.ai_processing_failed}
          />
        </div>
      </section>

      <section className="dashboard-section">
        <h3>Workflows by Status</h3>

        <div className="metric-grid">
          <SummaryCard
            label="Needs Review"
            value={summary.workflows_by_status.needs_review}
          />

          <SummaryCard
            label="Needs Information"
            value={summary.workflows_by_status.needs_information}
          />

          <SummaryCard
            label="Pending Approval"
            value={summary.workflows_by_status.pending_approval}
          />

          <SummaryCard
            label="Approved"
            value={summary.workflows_by_status.approved}
          />

          <SummaryCard
            label="Rejected"
            value={summary.workflows_by_status.rejected}
          />

          <SummaryCard
            label="Completed"
            value={summary.workflows_by_status.completed}
          />
        </div>
      </section>

      <section className="dashboard-section">
        <h3>Documents by Type</h3>

        <div className="metric-grid">
          <SummaryCard
            label="Invoice"
            value={summary.documents_by_type.invoice}
          />

          <SummaryCard
            label="Contract"
            value={summary.documents_by_type.contract}
          />

          <SummaryCard
            label="SOP"
            value={summary.documents_by_type.sop}
          />

          <SummaryCard
            label="HR Form"
            value={summary.documents_by_type.hr_form}
          />

          <SummaryCard
            label="Purchase Request"
            value={summary.documents_by_type.purchase_request}
          />

          <SummaryCard
            label="Policy"
            value={summary.documents_by_type.policy}
          />

          <SummaryCard
            label="Business Report"
            value={summary.documents_by_type.business_report}
          />

          <SummaryCard
            label="Support Ticket"
            value={summary.documents_by_type.support_ticket}
          />

          <SummaryCard
            label="Digital Form"
            value={summary.documents_by_type.digital_form}
          />

          <SummaryCard
            label="Memo"
            value={summary.documents_by_type.memo}
          />

          <SummaryCard
            label="Unknown"
            value={summary.documents_by_type.unknown}
          />
        </div>
      </section>
    </section>
  );
}

export default DashboardPage;