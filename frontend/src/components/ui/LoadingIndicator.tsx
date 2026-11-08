import ShellIcon from "../../layouts/ShellIcon";
import "./LoadingIndicator.css";

export function Spinner() {
  return <span className="docuflow-spinner" aria-hidden="true" />;
}

/** Render only while a real request is pending. No timers or simulated progress. */
export default function LoadingIndicator({ label, compact = false }: {
  label: string;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "docuflow-loading" : "docuflow-page-loading"} role="status" aria-live="polite">
      {!compact && <span className="loading-brand-mark" aria-hidden="true"><ShellIcon name="documents" /></span>}
      <div>
        {!compact && <strong className="loading-brand-name">DocuFlow AI</strong>}
        <span className="docuflow-loading"><Spinner />{label}</span>
      </div>
    </div>
  );
}
