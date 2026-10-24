import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { getAuditLogs } from "../api/auditLogApi";
import AuditLogsPage from "./AuditLogsPage";

vi.mock("../api/auditLogApi", () => ({ getAuditLogs: vi.fn() }));
it("announces loading and does not describe a failed request as an empty audit log", async () => {
  vi.mocked(getAuditLogs).mockRejectedValue(new Error("Network unavailable"));
  render(<AuditLogsPage />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading audit logs");
  expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load audit logs");
  expect(screen.queryByText("No audit logs yet")).not.toBeInTheDocument();
});
