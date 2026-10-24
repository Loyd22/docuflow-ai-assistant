
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DocumentDetail } from "../../types/document";
import type { Workflow } from "../../types/workflow";

import WorkflowManualReviewPanel from "./WorkflowManualReviewPanel";
import { getDocumentDetails } from "../../api/documentApi";
import { submitManualReview } from "../../api/workflowApi";

// Replace real API requests with controlled test responses.
vi.mock("../../api/documentApi", () => ({
  getDocumentDetails: vi.fn(),
}));

vi.mock("../../api/workflowApi", () => ({
  submitManualReview: vi.fn(),
}));

const mockGetDocument = vi.mocked(getDocumentDetails);
const mockSubmitReview = vi.mocked(submitManualReview);

const workflow: Workflow = {
  id: 1,
  document_id: 10,
  current_status: "needs_review",
  priority: "normal",
  recommended_action: "manual_review",
  assigned_to: null,
  created_at: "2026-10-20T08:00:00Z",
  updated_at: "2026-10-20T08:00:00Z",
};

const document: DocumentDetail = {
  id: 10,
  uploaded_by: 2,
  original_file_name: "invoice.txt",
  mime_type: "text/plain",
  file_size: 128,
  document_type: "invoice",
  status: "analyzed",
  is_indexed: false,
  created_at: "2026-10-20T08:00:00Z",
  updated_at: "2026-10-20T08:00:00Z",
  extracted_text: "Invoice total pending verification",
  summary: "Invoice requiring manual review",
  classification_confidence: 0.95,
  extracted_data: {
    invoice_number: "INV-001",
    total_amount: null,
  },
  business_rule_result: {
    next_action: "manual_review",
  },
};

function renderPanel() {
  const onReviewComplete = vi.fn();

  render(
    <WorkflowManualReviewPanel
      workflow={workflow}
      onClose={vi.fn()}
      onReviewComplete={onReviewComplete}
    />,
  );

  return { onReviewComplete };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockGetDocument.mockResolvedValue(document);
});

describe("WorkflowManualReviewPanel", () => {
  it("loads document details before allowing review", async () => {
    renderPanel();

    expect(
      await screen.findByText("invoice.txt"),
    ).toBeInTheDocument();

    expect(mockGetDocument).toHaveBeenCalledWith(10);
  });

  it("requires a verified amount and comment for resolution", async () => {
    const user = userEvent.setup();
    renderPanel();

    await screen.findByText("invoice.txt");

    const submitButton = screen.getByRole("button", {
      name: "Submit Manual Review",
    });

    await user.click(submitButton);

    // A deliberate outcome is required before the amount field is shown.
    expect(submitButton).toBeDisabled();
    expect(screen.queryByLabelText("Verified Invoice Total")).not.toBeInTheDocument();
    expect(mockSubmitReview).not.toHaveBeenCalled();

    await user.selectOptions(screen.getByLabelText("Outcome"), "resolved");
    await user.type(
      screen.getByLabelText("Verified Invoice Total"),
      "25000",
    );

    await user.click(submitButton);

    // The comment is also required.
    expect(mockSubmitReview).not.toHaveBeenCalled();
  });

  it("submits a verified invoice and returns the updated workflow", async () => {
    const user = userEvent.setup();
    const { onReviewComplete } = renderPanel();

    await screen.findByText("invoice.txt");

    const updatedWorkflow: Workflow = {
      ...workflow,
      current_status: "pending_approval",
    };

    const response = {
      workflow: updatedWorkflow,
      review: {
        id: 5,
        workflow_id: 1,
        reviewer_id: 3,
        outcome: "resolved" as const,
        comment: "Verified against source document.",
        created_at: "2026-10-20T09:00:00Z",
      },
    };

    mockSubmitReview.mockResolvedValue(response);

    await user.selectOptions(screen.getByLabelText("Outcome"), "resolved");
    await user.type(
      screen.getByLabelText("Verified Invoice Total"),
      "25000",
    );

    await user.type(
      screen.getByLabelText("Review Comment"),
      "Verified against source document.",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Submit Manual Review",
      }),
    );

    expect(mockSubmitReview).toHaveBeenCalledWith(1, {
      outcome: "resolved",
      comment: "Verified against source document.",
      corrected_total_amount: 25000,
    });

    expect(onReviewComplete).toHaveBeenCalledWith(response);
  });

  it("shows an error when submission fails", async () => {
    const user = userEvent.setup();
    renderPanel();

    await screen.findByText("invoice.txt");

    mockSubmitReview.mockRejectedValue(
      new Error("Network unavailable"),
    );

    await user.selectOptions(screen.getByLabelText("Outcome"), "resolved");
    await user.type(
      screen.getByLabelText("Verified Invoice Total"),
      "25000",
    );

    await user.type(
      screen.getByLabelText("Review Comment"),
      "Verified amount.",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Submit Manual Review",
      }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Unable to submit manual review.",
    );
  });
});
