import "./SummaryCard.css";

type SummaryCardProps = {
  label: string;
  value: number;
};

function SummaryCard({
  label,
  value,
}: SummaryCardProps) {
  return (
    <article className="summary-card">
      <p className="summary-card-label">
        {label}
      </p>

      <strong className="summary-card-value">
        {value}
      </strong>
    </article>
  );
}

export default SummaryCard;