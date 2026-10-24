import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { getWorkflows } from "../api/workflowApi";
import WorkflowsPage from "./WorkflowsPage";

vi.mock("../api/workflowApi", () => ({ getWorkflows: vi.fn() }));
vi.mock("../auth/useAuth", () => ({ useAuth: () => ({ user: { role: "manager" } }) }));
vi.mock("../components/workflows/WorkflowTable", () => ({ default: ({ workflows }: { workflows: { id: number }[] }) => <div>{workflows.map(({ id }) => <span key={id}>Listed workflow {id}</span>)}</div> }));
vi.mock("../components/workflows/WorkflowDetailsPanel", () => ({
  default: ({ workflow, onClose }: { workflow: { id: number }; onClose: () => void }) =>
    <div>Details for {workflow.id}<button onClick={onClose}>Close details</button></div>,
}));

beforeEach(() => {
  vi.mocked(getWorkflows).mockResolvedValue([{
    id: 12, document_id: 4, current_status: "approved", priority: "normal",
    assigned_to: null, recommended_action: null,
    created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-02T00:00:00Z",
  }]);
});

it("opens an authorized workflow from the URL and allows closing it", async () => {
  render(<MemoryRouter initialEntries={["/workflows?workflow=12"]}><WorkflowsPage /></MemoryRouter>);
  expect(await screen.findByText("Details for 12")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Close details" }));
  expect(screen.queryByText("Details for 12")).not.toBeInTheDocument();
});

it("does not open details for an ID absent from the authorized list", async () => {
  render(<MemoryRouter initialEntries={["/workflows?workflow=99"]}><WorkflowsPage /></MemoryRouter>);
  expect(await screen.findByRole("alert")).toHaveTextContent("unavailable or you do not have access");
  expect(screen.queryByText("Details for 99")).not.toBeInTheDocument();
});

it.each(["pending_approval", "needs_review", "needs_information"] as const)(
  "filters %s from the URL and restores all records when cleared", async (status) => {
    vi.mocked(getWorkflows).mockResolvedValue([
      { id: 1, document_id: 1, current_status: status, priority: "normal", assigned_to: null,
        recommended_action: null, created_at: "2026-01-01", updated_at: "2026-01-01" },
      { id: 2, document_id: 2, current_status: "completed", priority: "normal", assigned_to: null,
        recommended_action: null, created_at: "2026-01-01", updated_at: "2026-01-01" },
    ]);
    render(<MemoryRouter initialEntries={[`/workflows?status=${status}`]}><WorkflowsPage /></MemoryRouter>);
    expect(await screen.findByText("Listed workflow 1")).toBeInTheDocument();
    expect(screen.queryByText("Listed workflow 2")).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Workflow status" })).toHaveValue(status);
    await userEvent.click(screen.getByRole("button", { name: "Clear filter" }));
    expect(screen.getByText("Listed workflow 2")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toHaveValue("");
  },
);

it("keeps an explicitly opened workflow available even when the table filter has no matches", async () => {
  render(<MemoryRouter initialEntries={["/workflows?workflow=12&status=needs_review"]}><WorkflowsPage /></MemoryRouter>);
  expect(await screen.findByText("No workflows match this status")).toBeInTheDocument();
  expect(screen.getByText("Details for 12")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Clear filter" }));
  expect(screen.getByText("Listed workflow 12")).toBeInTheDocument();
  expect(screen.getByText("Details for 12")).toBeInTheDocument();
});

it("shows all authorized records for an unsupported status", async () => {
  render(<MemoryRouter initialEntries={["/workflows?status=unsupported"]}><WorkflowsPage /></MemoryRouter>);
  expect(await screen.findByText("Listed workflow 12")).toBeInTheDocument();
  expect(screen.getByText("Unknown status filter. Showing all workflows.")).toBeInTheDocument();
});

it("does not show an empty workflow state when loading fails", async () => {
  vi.mocked(getWorkflows).mockRejectedValue(new Error("Network unavailable"));
  render(<MemoryRouter><WorkflowsPage /></MemoryRouter>);
  expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load workflows");
  expect(screen.queryByText("No workflows yet")).not.toBeInTheDocument();
});
