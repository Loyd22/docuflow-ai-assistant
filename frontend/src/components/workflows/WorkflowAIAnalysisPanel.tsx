
import type { DocumentDetail } from "../../types/document";

type WorkflowAIAnalysisPanelProps = {
  document: DocumentDetail;
};

// Read string values safely from AI-generated data.
function readString(
  data: Record<string, unknown>,
  key: string,
): string | null {
  const value = data[key];

  return typeof value === "string" && value.trim()
    ? value
    : null;
}

// Read numeric values safely from AI-generated data.
function readNumber(
  data: Record<string, unknown>,
  key: string,
): number | null {
  const value = data[key];

  return typeof value === "number" &&
    Number.isFinite(value)
    ? value
    : null;
}

// Convert technical values into readable labels.
function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

// Format an amount using the extracted currency.
function formatAmount(
  amount: number | null,
  currency: string | null,
): string {
  if (amount === null) {
    return "Not available";
  }

  if (currency) {
    try {
      return new Intl.NumberFormat("en-PH", {
        style: "currency",
        currency,
      }).format(amount);
    } catch {
      // Show the amount without a currency if the code is invalid.
    }
  }

  return new Intl.NumberFormat("en-PH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function WorkflowAIAnalysisPanel({
  document,
}: WorkflowAIAnalysisPanelProps) {
  const extractedData = document.extracted_data;
  const businessRules = document.business_rule_result;

  const invoiceNumber = extractedData
    ? readString(extractedData, "invoice_number")
    : null;

  const supplier = extractedData
    ? readString(extractedData, "supplier")
    : null;

  const invoiceDate = extractedData
    ? readString(extractedData, "invoice_date")
    : null;

  const dueDate = extractedData
    ? readString(extractedData, "due_date")
    : null;

  const currency = extractedData
    ? readString(extractedData, "currency")
    : null;

  const subtotal = extractedData
    ? readNumber(extractedData, "subtotal")
    : null;

  const tax = extractedData
    ? readNumber(extractedData, "tax")
    : null;

  const totalAmount = extractedData
    ? readNumber(extractedData, "total_amount")
    : null;

  const nextAction = businessRules
    ? readString(businessRules, "next_action")
    : null;

  const reason = businessRules
    ? readString(businessRules, "reason")
    : null;

  const approvalRole = businessRules
    ? readString(businessRules, "approval_role")
    : null;

  const requiresApproval =
    businessRules?.requires_approval === true;

  const requiresManualReview =
    businessRules?.requires_manual_review === true;

  return (
    <section className="workflow-document-review">
      <div className="workflow-document-section">
        <h3>AI Analysis</h3>

        {document.document_type === "invoice" &&
        extractedData ? (
          <div className="workflow-document-grid">
            <div>
              <span className="workflow-detail-label">
                Invoice Number
              </span>
              <span>{invoiceNumber ?? "Not available"}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Supplier
              </span>
              <span>{supplier ?? "Not available"}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Invoice Date
              </span>
              <span>{invoiceDate ?? "Not available"}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Due Date
              </span>
              <span>{dueDate ?? "Not available"}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Subtotal
              </span>
              <span>{formatAmount(subtotal, currency)}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Tax
              </span>
              <span>{formatAmount(tax, currency)}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Total Amount
              </span>
              <strong>
                {formatAmount(totalAmount, currency)}
              </strong>
            </div>
          </div>
        ) : (
          <p className="workflow-empty-value">
            No structured invoice extraction is available
            for this document.
          </p>
        )}
      </div>

      <div className="workflow-document-section">
        <h3>Business Rule Evaluation</h3>

        {businessRules ? (
          <div className="workflow-document-grid">
            <div>
              <span className="workflow-detail-label">
                Recommended Action
              </span>
              <strong>
                {nextAction
                  ? formatLabel(nextAction)
                  : "Not available"}
              </strong>
            </div>

            <div>
              <span className="workflow-detail-label">
                Requires Approval
              </span>
              <span>{requiresApproval ? "Yes" : "No"}</span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Requires Manual Review
              </span>
              <span>
                {requiresManualReview ? "Yes" : "No"}
              </span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Approval Role
              </span>
              <span>
                {approvalRole
                  ? formatLabel(approvalRole)
                  : "Not required"}
              </span>
            </div>

            <div>
              <span className="workflow-detail-label">
                Reason
              </span>
              <span>{reason ?? "Not provided"}</span>
            </div>
          </div>
        ) : (
          <p className="workflow-empty-value">
            No business-rule evaluation is available.
          </p>
        )}
      </div>

      <p className="workflow-empty-value">
        AI-extracted information should be verified against
        the original document before making a decision.
      </p>
    </section>
  );
}

export default WorkflowAIAnalysisPanel;
