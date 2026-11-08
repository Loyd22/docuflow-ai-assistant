import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, Route, Routes, MemoryRouter } from "react-router-dom";
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

it("keeps the shell and existing route state intact across navigation without duplicate mounts", async () => {
  const mounted = vi.fn();
  function StatefulPage() {
    useEffect(() => { mounted(); }, []);
    return <section><label>Draft<input defaultValue="" /></label><Link to="/workflows?status=needs_review">Filter</Link></section>;
  }
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, name: "Admin", email: "admin@example.com", role: "admin", is_active: true },
    logout: vi.fn(), login: vi.fn(), isLoading: false, isAuthenticated: true,
  });
  render(<MemoryRouter initialEntries={["/documents"]}>
    <Routes><Route element={<AppLayout />}><Route path="/documents" element={<StatefulPage />} /><Route path="/workflows" element={<StatefulPage />} /></Route></Routes>
  </MemoryRouter>);
  const header = screen.getByRole("banner");
  const sidebar = screen.getByRole("navigation", { name: "Main navigation" });
  const input = screen.getByLabelText("Draft");
  await userEvent.type(input, "Unsaved draft");
  await userEvent.click(screen.getByRole("link", { name: "Workflows" }));
  expect(screen.getByRole("banner")).toBe(header);
  expect(screen.getByRole("navigation", { name: "Main navigation" })).toBe(sidebar);
  expect(screen.getByLabelText("Draft")).toBe(input);
  expect(input).toHaveValue("Unsaved draft");
  await userEvent.click(screen.getByRole("link", { name: "Filter" }));
  expect(input).toHaveValue("Unsaved draft");
  expect(mounted).toHaveBeenCalledTimes(1);
  expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
});
