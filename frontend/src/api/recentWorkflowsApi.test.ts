import { beforeEach, describe, expect, it, vi } from "vitest";
import { getDocuments } from "./documentApi";
import { getWorkflows } from "./workflowApi";
import { getRecentWorkflows } from "./recentWorkflowsApi";
import type { Workflow } from "../types/workflow";

vi.mock("./documentApi", () => ({ getDocuments: vi.fn() }));
vi.mock("./workflowApi", () => ({ getWorkflows: vi.fn() }));
const workflow = (id: number): Workflow => ({
  id, document_id: id, current_status: "pending_approval", priority: "normal",
  assigned_to: null, recommended_action: null,
  created_at: "2026-01-01T00:00:00Z", updated_at: `2026-01-0${id}T00:00:00Z`,
});
beforeEach(() => vi.resetAllMocks());

describe("recent workflow data", () => {
  it("selects the newest five without mutating the authorized list, using one document request", async () => {
    const workflows = [1, 3, 6, 2, 5, 4].map(workflow);
    vi.mocked(getWorkflows).mockResolvedValue(workflows);
    vi.mocked(getDocuments).mockResolvedValue([]);
    const result = await getRecentWorkflows();
    expect(result.records.map(({ workflow }) => workflow.id)).toEqual([6, 5, 4, 3, 2]);
    expect(workflows.map(({ id }) => id)).toEqual([1, 3, 6, 2, 5, 4]);
    expect(getDocuments).toHaveBeenCalledTimes(1);
    expect(result.records[0].filename).toBeNull();
  });
  it("keeps authorized workflows when document names cannot be retrieved", async () => {
    vi.mocked(getWorkflows).mockResolvedValue([workflow(1)]);
    vi.mocked(getDocuments).mockRejectedValue(new Error("Forbidden"));
    expect(await getRecentWorkflows()).toMatchObject({ documentsUnavailable: true, records: [{ filename: null }] });
  });
  it("propagates workflow failures instead of presenting an empty list", async () => {
    vi.mocked(getWorkflows).mockRejectedValue(new Error("Unauthorized"));
    vi.mocked(getDocuments).mockResolvedValue([]);
    await expect(getRecentWorkflows()).rejects.toThrow("Unauthorized");
  });
});
