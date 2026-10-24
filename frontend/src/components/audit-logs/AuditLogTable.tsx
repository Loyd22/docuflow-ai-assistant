import type { AuditLog } from "../../types/auditLog";

import "./AuditLogTable.css";

type AuditLogTableProps = {
  auditLogs: AuditLog[];
};

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function formatMetadata(
  metadata: Record<string, unknown> | null,
): string {
  if (!metadata) {
    return "—";
  }

  return Object.entries(metadata)
    .map(([key, value]) => {
      const label = formatLabel(key);

      return `${label}: ${String(value)}`;
    })
    .join(" · ");
}

function AuditLogTable({
  auditLogs,
}: AuditLogTableProps) {
  return (
    <div className="audit-table-wrapper" role="region" aria-label="Audit logs table" tabIndex={0}>
      <table className="audit-table">
        <thead>
          <tr>
            <th scope="col">Time</th>
            <th scope="col">Action</th>
            <th scope="col">Entity</th>
            <th scope="col">Entity ID</th>
            <th scope="col">User ID</th>
            <th scope="col">Metadata</th>
          </tr>
        </thead>

        <tbody>
          {auditLogs.map((auditLog) => (
            <tr key={auditLog.id}>
              <td>
                {formatDate(auditLog.created_at)}
              </td>

              <td>
                <span className="audit-action">
                  {formatLabel(auditLog.action)}
                </span>
              </td>

              <td>
                {formatLabel(
                  auditLog.entity_type,
                )}
              </td>

              <td>
                {auditLog.entity_id ?? "—"}
              </td>

              <td>
                {auditLog.user_id ?? "System"}
              </td>

              <td className="audit-metadata">
                {formatMetadata(
                  auditLog.event_metadata,
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AuditLogTable;