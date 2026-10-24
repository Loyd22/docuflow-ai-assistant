import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { expect, it, vi } from "vitest";
import { useAuth } from "../auth/useAuth";
import type { AuthContextValue } from "../auth/AuthContext";
import AppLayout from "./AppLayout";

vi.mock("../auth/useAuth", () => ({ useAuth: vi.fn() }));

it.each(["employee", "manager", "admin"] as const)("preserves %s navigation and authenticated account actions", async (role) => {
  const logout = vi.fn();
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, name: "Test User", email: "test@example.com", role, is_active: true },
    logout, login: vi.fn(), isLoading: false, isAuthenticated: true,
  } satisfies AuthContextValue);
  render(<MemoryRouter initialEntries={["/workflows?status=needs_review"]}><AppLayout /></MemoryRouter>);
  expect(screen.getByText("Test User")).toBeInTheDocument();
  expect(screen.getByText(role)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Workflows" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Documents" })).not.toHaveAttribute("aria-current");
  for (const name of ["Dashboard", "Audit Logs"]) {
    if (role === "employee") expect(screen.queryByRole("link", { name })).not.toBeInTheDocument();
    else expect(screen.getByRole("link", { name })).toBeInTheDocument();
  }
  expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main-content");
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(logout).toHaveBeenCalledOnce();
});
