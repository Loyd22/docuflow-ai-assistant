
import { AxiosError, AxiosHeaders } from "axios";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "../auth/AuthContext";
import type { AuthContextValue } from "../auth/AuthContext";
import LoginPage from "./LoginPage";

// Render the login page with fake authentication data.
function renderLoginPage(
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
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={<h1>Role-based home</h1>}
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );

  return auth;
}

describe("LoginPage", () => {
  it("renders the login form", () => {
    renderLoginPage();

    expect(
      screen.getByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText("Email"),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText("Password"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Sign in" }),
    ).toBeEnabled();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign out" })).not.toBeInTheDocument();
  });

  it("preserves required fields and email validation", async () => {
    const user = userEvent.setup();
    const auth = renderLoginPage();
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(auth.login).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Email")).toBeInvalid();
    expect(screen.getByLabelText("Password")).toBeInvalid();
    await user.type(screen.getByLabelText("Email"), "invalid-email");
    await user.type(screen.getByLabelText("Password"), "test-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(auth.login).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Email")).toBeInvalid();
  });

  it("shows loading while authentication initializes", () => {
    renderLoginPage({ isLoading: true });

    expect(
      screen.getByText("Loading..."),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Sign in" }),
    ).not.toBeInTheDocument();
  });

  it("redirects already authenticated users to the home route", async () => {
    renderLoginPage({
      isAuthenticated: true,
    });

    expect(
      await screen.findByRole("heading", {
        name: "Role-based home",
      }),
    ).toBeInTheDocument();
  });

  it("submits credentials and navigates on success", async () => {
    const user = userEvent.setup();
    const auth = renderLoginPage();

    await user.type(
      screen.getByLabelText("Email"),
      "employee@example.com",
    );

    await user.type(
      screen.getByLabelText("Password"),
      "password123",
    );

    await user.click(
      screen.getByRole("button", { name: "Sign in" }),
    );

    // Verify that the login function receives the credentials.
    expect(auth.login).toHaveBeenCalledWith({
      email: "employee@example.com",
      password: "password123",
    });

    // Successful login should navigate to the home route.
    expect(
      await screen.findByRole("heading", {
        name: "Role-based home",
      }),
    ).toBeInTheDocument();
  });

  it("shows an error when login fails", async () => {
    const user = userEvent.setup();

    renderLoginPage({
      login: vi.fn().mockRejectedValue(
        new Error("Network failure"),
      ),
    });

    await user.type(
      screen.getByLabelText("Email"),
      "employee@example.com",
    );

    await user.type(
      screen.getByLabelText("Password"),
      "wrongpassword",
    );

    await user.click(
      screen.getByRole("button", { name: "Sign in" }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("Unable to sign in.");

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Sign in" }),
      ).toBeEnabled();
    });
  });

  it("disables submission while login is pending", async () => {
    const user = userEvent.setup();

    // Simulate a login request that has not finished.
    const login = vi.fn(
      () => new Promise<void>(() => {}),
    );

    renderLoginPage({ login });

    await user.type(
      screen.getByLabelText("Email"),
      "employee@example.com",
    );

    await user.type(
      screen.getByLabelText("Password"),
      "password123",
    );

    await user.click(
      screen.getByRole("button", { name: "Sign in" }),
    );

    expect(
      screen.getByRole("button", {
        name: "Signing in...",
      }),
    ).toBeDisabled();

    expect(login).toHaveBeenCalledTimes(1);
  });

  it("displays the error message returned by the backend", async () => {
    const user = userEvent.setup();

    // Simulate a 401 Unauthorized response from FastAPI.
    const apiError = new AxiosError(
      "Unauthorized",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        data: {
          detail: "Incorrect email or password.",
        },
        status: 401,
        statusText: "Unauthorized",
        headers: {},
        config: {
          headers: new AxiosHeaders(),
        },
      },
    );

    renderLoginPage({
      login: vi.fn().mockRejectedValue(apiError),
    });

    await user.type(
      screen.getByLabelText("Email"),
      "employee@example.com",
    );

    await user.type(
      screen.getByLabelText("Password"),
      "wrongpassword",
    );

    await user.click(
      screen.getByRole("button", { name: "Sign in" }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Incorrect email or password.",
    );
  });
});
