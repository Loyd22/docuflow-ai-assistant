
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getWorkflowHistory } from "../../api/workflowApi";
import WorkflowHistoryPanel from "./WorkflowHistoryPanel";

// Replace real API requests with test responses.
vi.mock("../../api/workflowApi", () => ({
  getWorkflowHistory: vi.fn(),
}));

const mockGetWorkflowHistory = vi.mocked(getWorkflowHistory);

describe("WorkflowHistoryPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading message while retrieving history", () => {
    // Keep the API request pending.
    mockGetWorkflowHistory.mockImplementation(
      () => new Promise(() => {}),
    );

    render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByText("Loading decision history..."),
    ).toBeInTheDocument();
  });

  it("displays approval and manual-review history", async () => {
    mockGetWorkflowHistory.mockResolvedValue({
      workflow_id: 5,
      history: [
        {
          id: 10,
          action_type: "manual_review",
          decided_by: 2,
          decision: "resolved",
          comment: "Invoice verified.",
          created_at: "2026-10-22T08:00:00Z",
        },
        {
          id: 11,
          action_type: "approval",
          decided_by: 3,
          decision: "approved",
          comment: "Approved for payment.",
          created_at: "2026-10-22T09:00:00Z",
        },
      ],
    });

    render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={vi.fn()}
      />,
    );

    // Confirm both decisions appear after loading.
    expect(
      await screen.findByText("Manual review: resolved"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Approval: approved"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Invoice verified."),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Approved for payment."),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Reviewed by user #2"),
    ).toBeInTheDocument();

    // Confirm the correct workflow was requested.
    expect(mockGetWorkflowHistory).toHaveBeenCalledWith(5);
  });

  it("shows an empty message when no decisions exist", async () => {
    mockGetWorkflowHistory.mockResolvedValue({
      workflow_id: 5,
      history: [],
    });

    render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={vi.fn()}
      />,
    );

    expect(
      await screen.findByText(
        "No decisions have been recorded for this workflow.",
      ),
    ).toBeInTheDocument();
  });

  it("shows an error when history cannot be loaded", async () => {
    // Simulate a failed API request.
    mockGetWorkflowHistory.mockRejectedValue(
      new Error("Network error"),
    );

    render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={vi.fn()}
      />,
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Unable to load workflow history.",
    );
  });

  it("calls onClose when the Close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mockGetWorkflowHistory.mockResolvedValue({
      workflow_id: 5,
      history: [],
    });

    render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={onClose}
      />,
    );

    // Click the Close button.
    await user.click(
      screen.getByRole("button", {
        name: "Close decision history",
      }),
    );

    // Verify the close function runs exactly once.
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("reloads history when the selected workflow changes", async () => {
    mockGetWorkflowHistory
      .mockResolvedValueOnce({
        workflow_id: 5,
        history: [],
      })
      .mockResolvedValueOnce({
        workflow_id: 8,
        history: [],
      });

    const { rerender } = render(
      <WorkflowHistoryPanel
        workflowId={5}
        onClose={vi.fn()}
      />,
    );

    // Confirm the first workflow was requested.
    await waitFor(() => {
      expect(mockGetWorkflowHistory).toHaveBeenCalledWith(5);
    });

    // Select a different workflow.
    rerender(
      <WorkflowHistoryPanel
        workflowId={8}
        onClose={vi.fn()}
      />,
    );

    // Confirm the new workflow was requested.
    await waitFor(() => {
      expect(mockGetWorkflowHistory).toHaveBeenCalledWith(8);
    });

    expect(
      screen.getByText("Workflow #8"),
    ).toBeInTheDocument();
  });
});
