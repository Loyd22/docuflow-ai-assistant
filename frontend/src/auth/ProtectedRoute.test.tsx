
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "./AuthContext";
import type { AuthContextValue } from "./AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";

// Render a protected page with fake authentication state.
function renderProtectedRoute(
  overrides: Partial<AuthContextValue> = {},
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
      <MemoryRouter initialEntries={["/documents"]}>
        <Routes>
          <Route
            path="/documents"
            element={
              <ProtectedRoute>
                <h1>Documents Page</h1>
              </ProtectedRoute>
            }
          />

          <Route
            path="/login"
            element={<h1>Login Page</h1>}
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users to login", () => {
    renderProtectedRoute();

    expect(
      screen.getByRole("heading", { name: "Login Page" }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("heading", { name: "Documents Page" }),
    ).not.toBeInTheDocument();
  });

  it("allows authenticated users to access protected pages", () => {
    renderProtectedRoute({
      isAuthenticated: true,
    });

    expect(
      screen.getByRole("heading", { name: "Documents Page" }),
    ).toBeInTheDocument();
  });

  it("shows loading while authentication initializes", () => {
    renderProtectedRoute({
      isLoading: true,
    });

    expect(screen.getByText("Loading..."))
      .toBeInTheDocument();

    expect(
      screen.queryByRole("heading", { name: "Documents Page" }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("heading", { name: "Login Page" }),
    ).not.toBeInTheDocument();
  });
});
