
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { User, UserRole } from "../types/auth";
import { AuthContext } from "./AuthContext";
import type { AuthContextValue } from "./AuthContext";
import { RoleProtectedRoute } from "./RoleProtectedRoute";

// Create a user with the requested role.
function createTestUser(role: UserRole): User {
  return {
    id: 1,
    name: "Test User",
    email: "test@example.com",
    role,
    is_active: true,
  };
}

// Render a page with controlled user permissions.
function renderRoleProtectedRoute(
  overrides: Partial<AuthContextValue> = {},
  allowedRoles: UserRole[] = ["manager", "admin"],
) {
  const auth: AuthContextValue = {
    user: null,
    isLoading: false,
    isAuthenticated: false,
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
    ...overrides,
  };

  render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <RoleProtectedRoute allowedRoles={allowedRoles}>
                <h1>Dashboard Page</h1>
              </RoleProtectedRoute>
            }
          />

          <Route
            path="/login"
            element={<h1>Login Page</h1>}
          />

          <Route
            path="/forbidden"
            element={<h1>Forbidden Page</h1>}
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("RoleProtectedRoute", () => {
  it("shows loading while authentication initializes", () => {
    renderRoleProtectedRoute({ isLoading: true });

    expect(screen.getByText("Loading..."))
      .toBeInTheDocument();

    expect(screen.queryByText("Dashboard Page"))
      .not.toBeInTheDocument();
  });

  it("redirects users without an account to login", () => {
    renderRoleProtectedRoute();

    expect(screen.getByRole("heading", { name: "Login Page" }))
      .toBeInTheDocument();
  });

  it("prevents employees from accessing manager pages", () => {
    renderRoleProtectedRoute({
      user: createTestUser("employee"),
      isAuthenticated: true,
    });

    expect(screen.getByRole("heading", { name: "Forbidden Page" }))
      .toBeInTheDocument();

    expect(screen.queryByText("Dashboard Page"))
      .not.toBeInTheDocument();
  });

  it("allows managers to access manager pages", () => {
    renderRoleProtectedRoute({
      user: createTestUser("manager"),
      isAuthenticated: true,
    });

    expect(screen.getByRole("heading", { name: "Dashboard Page" }))
      .toBeInTheDocument();
  });

  it("allows admins to access manager pages", () => {
    renderRoleProtectedRoute({
      user: createTestUser("admin"),
      isAuthenticated: true,
    });

    expect(screen.getByRole("heading", { name: "Dashboard Page" }))
      .toBeInTheDocument();
  });

  it("allows employees when their role is permitted", () => {
    renderRoleProtectedRoute(
      {
        user: createTestUser("employee"),
        isAuthenticated: true,
      },
      ["employee", "manager", "admin"],
    );

    expect(screen.getByRole("heading", { name: "Dashboard Page" }))
      .toBeInTheDocument();
  });
});
