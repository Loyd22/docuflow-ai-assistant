
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { Workflow } from "../../types/workflow";
import WorkflowTable from "./WorkflowTable";

// Create a sample workflow for testing.
function createWorkflow(
  overrides: Partial<Workflow> = {},
): Workflow {
  return {
    id: 1,
    document_id: 10,
    current_status: "needs_review",
    priority: "normal",
    recommended_action: "manual_review",
    assigned_to: null,
    created_at: "2026-10-20T08:00:00Z",
    updated_at: "2026-10-20T08:00:00Z",
    ...overrides,
  };
}

describe("WorkflowTable", () => {
  it("shows Manual Review for workflows needing review", () => {
    render(
      <WorkflowTable
        workflows={[createWorkflow()]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={vi.fn()}
        onViewHistory={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Manual Review",
      }),
    ).toBeInTheDocument();
  });

  it("shows Approval Decision for pending approvals", () => {
    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            current_status: "pending_approval",
          }),
        ]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={vi.fn()}
        onViewHistory={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Approval Decision",
      }),
    ).toBeInTheDocument();
  });

  it("hides manager decision buttons from employees", () => {
    render(
      <WorkflowTable
        workflows={[
          createWorkflow(),
          createWorkflow({
            id: 2,
            current_status: "pending_approval",
          }),
        ]}
        canMakeDecisions={false}
        canRespondToRequests={true}
        onDecision={vi.fn()}
        onViewHistory={vi.fn()}
      />,
    );

    // Employees cannot perform manager approval or review actions.
    expect(
      screen.queryByRole("button", {
        name: "Manual Review",
      }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", {
        name: "Approval Decision",
      }),
    ).not.toBeInTheDocument();

    // History remains available for visible workflows.
    expect(
      screen.getAllByRole("button", {
        name: /View history for workflow/i,
      }),
    ).toHaveLength(2);
  });

  it("shows Respond to Request for employees", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();

    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            id: 12,
            current_status: "needs_information",
          }),
        ]}
        canMakeDecisions={false}
        canRespondToRequests={true}
        onDecision={onDecision}
        onViewHistory={vi.fn()}
      />,
    );

    const respondButton = screen.getByRole("button", {
      name: "Respond to Request",
    });

    expect(respondButton).toBeInTheDocument();

    // Clicking the button sends the workflow ID to the parent.
    await user.click(respondButton);

    expect(onDecision).toHaveBeenCalledExactlyOnceWith(12);
  });

  it("hides decision buttons for completed or rejected workflows", () => {
    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            id: 1,
            current_status: "completed",
          }),
          createWorkflow({
            id: 2,
            current_status: "rejected",
          }),
        ]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={vi.fn()}
        onViewHistory={vi.fn()}
      />,
    );

    // Finished workflows should not allow further decisions.
    expect(
      screen.queryByRole("button", {
        name: "Manual Review",
      }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", {
        name: "Approval Decision",
      }),
    ).not.toBeInTheDocument();

    // Their decision history should still be accessible.
    expect(
      screen.getAllByRole("button", {
        name: /View history for workflow/i,
      }),
    ).toHaveLength(2);
  });

  it("passes the correct workflow ID when clicked", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();

    render(
      <WorkflowTable
        workflows={[createWorkflow({ id: 15 })]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={onDecision}
        onViewHistory={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Manual Review",
      }),
    );

    expect(onDecision).toHaveBeenCalledExactlyOnceWith(15);
  });

  it("displays workflow information correctly", () => {
    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            id: 5,
            document_id: 25,
            priority: "urgent",
          }),
        ]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={vi.fn()}
        onViewHistory={vi.fn()}
      />,
    );

    expect(screen.getByText("#5")).toBeInTheDocument();
    expect(screen.getByText("#25")).toBeInTheDocument();

    expect(
      screen.getByText("Needs Review"),
    ).toBeInTheDocument();

    expect(screen.getByText("Urgent")).toBeInTheDocument();
  });

  it("calls onViewHistory with the correct workflow ID", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();
    const onViewHistory = vi.fn();

    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            id: 12,
            current_status: "approved",
          }),
        ]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={onDecision}
        onViewHistory={onViewHistory}
      />,
    );

    // Open history for a workflow that is already approved.
    await user.click(
      screen.getByRole("button", {
        name: "View history for workflow #12",
      }),
    );

    expect(onViewHistory).toHaveBeenCalledExactlyOnceWith(12);

    // Viewing history must not trigger another decision.
    expect(onDecision).not.toHaveBeenCalled();
  });

  it("keeps history and decision actions independent", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();
    const onViewHistory = vi.fn();

    render(
      <WorkflowTable
        workflows={[
          createWorkflow({
            id: 20,
            current_status: "needs_review",
          }),
        ]}
        canMakeDecisions={true}
        canRespondToRequests={false}
        onDecision={onDecision}
        onViewHistory={onViewHistory}
      />,
    );

    // Viewing history only invokes the history callback.
    await user.click(
      screen.getByRole("button", {
        name: "View history for workflow #20",
      }),
    );

    expect(onViewHistory).toHaveBeenCalledExactlyOnceWith(20);
    expect(onDecision).not.toHaveBeenCalled();

    // Performing a review only invokes the decision callback.
    await user.click(
      screen.getByRole("button", {
        name: "Manual Review",
      }),
    );

    expect(onDecision).toHaveBeenCalledExactlyOnceWith(20);
    expect(onViewHistory).toHaveBeenCalledTimes(1);
  });
});
