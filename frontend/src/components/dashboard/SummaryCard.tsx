import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import "./SummaryCard.css";

type SummaryCardProps = {
  label: string;
  value: number;
  icon?: ReactNode;
  tone?: "blue" | "amber" | "violet";
  description?: string;
  emphasis?: boolean;
  href?: string;
};

function SummaryCard({ label, value, icon, tone = "blue", description, emphasis = false, href }: SummaryCardProps) {
  return (
    <article className={`summary-card${emphasis ? " summary-card-emphasis" : ""}`}>
      <div className="summary-card-heading">
        <h4 className="summary-card-label">{label}</h4>
        {icon && <span className={`summary-card-icon summary-card-icon-${tone}`}>{icon}</span>}
      </div>
      <strong className="summary-card-value">{value.toLocaleString()}</strong>
      {description && <p className="summary-card-description">{description}</p>}
      {href && <Link className="summary-card-link" to={href} aria-label={`View ${label.toLowerCase()} workflows`}>View workflows →</Link>}
    </article>
  );
}

export default SummaryCard;
