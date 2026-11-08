
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

import {
  getAdminUsers,
  updateAdminUserRole,
  updateAdminUserStatus,
} from "../api/adminUserApi";
import { useAuth } from "../auth/useAuth";
import type { User } from "../types/auth";
import AdminUsersPage from "./AdminUsersPage";

// Mock external dependencies so tests never modify real accounts.
vi.mock("../auth/useAuth", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../api/adminUserApi", () => ({
  getAdminUsers: vi.fn(),
  updateAdminUserRole: vi.fn(),
  updateAdminUserStatus: vi.fn(),
}));

// These users represent records returned by the backend.
const admin: User = {
  id: 1,
  name: "Admin",
  email: "admin@example.com",
  role: "admin",
  is_active: true,
};

const employee: User = {
  id: 2,
  name: "Employee",
  email: "employee@example.com",
  role: "employee",
  is_active: true,
};

// Create a user directory response for testing.
function userList(users: User[] = [admin, employee]) {
  return {
    users,
    total: users.length,
    offset: 0,
    limit: 10,
  };
}

// Control exactly when an asynchronous request succeeds or fails.
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;

  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });

  return { promise, resolve, reject };
}

// Restore a predictable starting state before each test.
beforeEach(() => {
  vi.resetAllMocks();

  vi.mocked(useAuth).mockReturnValue({
    user: admin,
    logout: vi.fn(),
    login: vi.fn(),
    isLoading: false,
    isAuthenticated: true,
  });

  vi.mocked(getAdminUsers).mockResolvedValue(userList());
});

// --------------------------------------------------
// 1. DIRECTORY LOADING
// --------------------------------------------------

it("displays users after loading the directory", async () => {
  render(<AdminUsersPage />);

  expect(
    await screen.findByText("Employee"),
  ).toBeInTheDocument();

  expect(screen.getByText("Admin")).toBeInTheDocument();

  expect(
    screen.getByText("employee@example.com"),
  ).toBeInTheDocument();

  expect(getAdminUsers).toHaveBeenCalledWith({
    limit: 10,
    offset: 0,
  });
});

it("shows a loading indicator while the directory is pending", async () => {
  const request =
    deferred<Awaited<ReturnType<typeof getAdminUsers>>>();

  vi.mocked(getAdminUsers).mockReturnValue(
    request.promise,
  );

  render(<AdminUsersPage />);

  // The loading indicator should appear during the request.
  expect(
    screen.getByRole("status"),
  ).toHaveTextContent("Loading users...");

  expect(
    screen.getByRole("button", {
      name: "Refreshing users...",
    }),
  ).toBeDisabled();

  // Complete the request.
  await act(async () => {
    request.resolve(userList());
  });

  // The loading state should disappear afterward.
  expect(
    screen.queryByText("Loading users..."),
  ).not.toBeInTheDocument();

  expect(
    screen.getByRole("button", {
      name: "Refresh users",
    }),
  ).toBeEnabled();

  expect(getAdminUsers).toHaveBeenCalledTimes(1);
});

// --------------------------------------------------
// 2. ROLE MANAGEMENT
// --------------------------------------------------

it("requires confirmation before updating a user's role", async () => {
  const request = deferred<User>();

  vi.mocked(updateAdminUserRole).mockReturnValue(
    request.promise,
  );

  render(<AdminUsersPage />);

  // Open the role editor.
  fireEvent.click(
    await screen.findByRole("button", {
      name: "Change role for Employee",
    }),
  );

  // Select a new role.
  fireEvent.change(
    screen.getByLabelText("New role"),
    { target: { value: "manager" } },
  );

  expect(updateAdminUserRole).not.toHaveBeenCalled();

  // Reviewing the change must not immediately call the API.
  fireEvent.click(
    screen.getByRole("button", {
      name: "Review Change",
    }),
  );

  expect(updateAdminUserRole).not.toHaveBeenCalled();

  // Only explicit confirmation sends the request.
  fireEvent.click(
    screen.getByRole("button", {
      name: "Confirm Role Change",
    }),
  );

  expect(updateAdminUserRole).toHaveBeenCalledWith(
    employee.id,
    { role: "manager" },
  );

  expect(updateAdminUserRole).toHaveBeenCalledTimes(1);

  // Controls must stay disabled while the request is pending.
  expect(
    screen.getByRole("button", {
      name: "Saving...",
    }),
  ).toBeDisabled();

  expect(
    screen.getByLabelText("New role"),
  ).toBeDisabled();

  expect(
    screen.getByRole("button", {
      name: "Cancel",
    }),
  ).toBeDisabled();

  expect(
    screen.getByText("Saving account changes..."),
  ).toHaveAttribute("role", "status");

  // Complete the request successfully.
  await act(async () => {
    request.resolve({
      ...employee,
      role: "manager",
    });
  });

  expect(
    screen.getByText(
      "Employee's role was changed to manager.",
    ),
  ).toBeInTheDocument();

  await waitFor(() => {
    expect(
      screen.getByRole("button", {
        name: "Refresh users",
      }),
    ).toBeEnabled();
  });
});

it("cancels a role change without modifying the user", async () => {
  render(<AdminUsersPage />);

  fireEvent.click(
    await screen.findByRole("button", {
      name: "Change role for Employee",
    }),
  );

  fireEvent.change(
    screen.getByLabelText("New role"),
    { target: { value: "manager" } },
  );

  // Cancel before confirming anything.
  fireEvent.click(
    screen.getByRole("button", {
      name: "Cancel",
    }),
  );

  expect(updateAdminUserRole).not.toHaveBeenCalled();
});

// --------------------------------------------------
// 3. ACCOUNT STATUS MANAGEMENT
// --------------------------------------------------

it.each([true, false])(
  "shows pending and retry feedback for status changes (active=%s)",
  async (isActive) => {
    const selectedEmployee: User = {
      ...employee,
      is_active: isActive,
    };

    vi.mocked(getAdminUsers).mockResolvedValue(
      userList([admin, selectedEmployee]),
    );

    const request = deferred<User>();

    vi.mocked(updateAdminUserStatus).mockReturnValue(
      request.promise,
    );

    render(<AdminUsersPage />);

    const action = isActive
      ? "Deactivation"
      : "Activation";

    const buttonName = isActive
      ? "Deactivate account for Employee"
      : "Activate account for Employee";

    // Open the status editor.
    fireEvent.click(
      await screen.findByRole("button", {
        name: buttonName,
      }),
    );

    // Reviewing should not send a mutation.
    fireEvent.click(
      screen.getByRole("button", {
        name: `Review ${action}`,
      }),
    );

    expect(updateAdminUserStatus).not.toHaveBeenCalled();

    // Confirm the change.
    fireEvent.click(
      screen.getByRole("button", {
        name: `Confirm ${action}`,
      }),
    );

    expect(updateAdminUserStatus).toHaveBeenCalledWith(
      employee.id,
      { is_active: !isActive },
    );

    expect(updateAdminUserStatus).toHaveBeenCalledTimes(1);

    expect(
      screen.getByRole("button", {
        name: "Saving...",
      }),
    ).toBeDisabled();

    // Simulate a failed network request.
    await act(async () => {
      request.reject(new Error("offline"));
    });

    // The user must see the failure and be able to retry.
    expect(
      await screen.findByRole("alert"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", {
        name: `Review ${action}`,
      }),
    ).toBeEnabled();

    expect(
      screen.getByRole("button", {
        name: "Cancel",
      }),
    ).toBeEnabled();

    // Failure must not trigger a second mutation automatically.
    expect(updateAdminUserStatus).toHaveBeenCalledTimes(1);
  },
);

it.each([true, false])(
  "handles successful status changes (active=%s)",
  async (isActive) => {
    const selectedEmployee: User = {
      ...employee,
      is_active: isActive,
    };

    const updatedEmployee: User = {
      ...selectedEmployee,
      is_active: !isActive,
    };

    // Return the updated state for any subsequent refresh.
    vi.mocked(getAdminUsers)
      .mockResolvedValueOnce(
        userList([admin, selectedEmployee]),
      )
      .mockResolvedValue(
        userList([admin, updatedEmployee]),
      );

    vi.mocked(updateAdminUserStatus).mockResolvedValue(
      updatedEmployee,
    );

    render(<AdminUsersPage />);

    const action = isActive
      ? "Deactivation"
      : "Activation";

    fireEvent.click(
      await screen.findByRole("button", {
        name: isActive
          ? "Deactivate account for Employee"
          : "Activate account for Employee",
      }),
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: `Review ${action}`,
      }),
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: `Confirm ${action}`,
      }),
    );

    // The API receives the intended new status.
    await waitFor(() => {
      expect(updateAdminUserStatus).toHaveBeenCalledWith(
        employee.id,
        { is_active: !isActive },
      );
    });

    expect(updateAdminUserStatus).toHaveBeenCalledTimes(1);

    // Once complete, normal refresh interaction is available.
    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Refresh users",
        }),
      ).toBeEnabled();
    });
  },
);

// --------------------------------------------------
// 4. SELF-MANAGEMENT PROTECTION
// --------------------------------------------------

it("does not show account-management buttons for the current admin", async () => {
  render(<AdminUsersPage />);

  const adminName = await screen.findByText("Admin");

  // Locate the current Admin's table row.
  const adminRow = adminName.closest("tr");

  expect(adminRow).not.toBeNull();

  const row = within(adminRow as HTMLTableRowElement);

  expect(
    row.queryByRole("button", {
      name: "Change role for Admin",
    }),
  ).not.toBeInTheDocument();

  expect(
    row.queryByRole("button", {
      name: "Deactivate account for Admin",
    }),
  ).not.toBeInTheDocument();
});
