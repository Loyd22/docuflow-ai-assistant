import {
  useEffect,
  useState,
} from "react";
import axios from "axios";

import { getAuditLogs } from "../api/auditLogApi";
import AuditLogTable from "../components/audit-logs/AuditLogTable";
import type { AuditLog } from "../types/auditLog";

import "./AuditLogsPage.css";

function AuditLogsPage() {
  const [auditLogs, setAuditLogs] =
    useState<AuditLog[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadAuditLogs() {
      try {
        setErrorMessage(null);

        const logs = await getAuditLogs();

        setAuditLogs(logs);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detail =
            error.response?.data?.detail;

          if (typeof detail === "string") {
            setErrorMessage(detail);
          } else {
            setErrorMessage(
              "Unable to load audit logs.",
            );
          }
        } else {
          setErrorMessage(
            "Unable to load audit logs.",
          );
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadAuditLogs();
  }, []);

  return (
    <section className="audit-logs-page">
      <div className="audit-logs-heading">
        <h2>Audit Logs</h2>

        <p>
          Review important document, workflow,
          approval, and system activity.
        </p>
      </div>

      {errorMessage && (
        <p
          className="audit-error"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      {isLoading ? (
        <p>Loading audit logs...</p>
      ) : auditLogs.length === 0 ? (
        <div className="empty-audit-logs">
          <h3>No audit logs yet</h3>

          <p>
            Recorded system activity will appear here.
          </p>
        </div>
      ) : (
        <AuditLogTable
          auditLogs={auditLogs}
        />
      )}
    </section>
  );
}

export default AuditLogsPage;