import LoadingIndicator, { Spinner } from "../components/ui/LoadingIndicator";
import { useEffect, useState } from "react";
import axios from "axios";

import {
  getAdminUsers,
  updateAdminUserRole,
  updateAdminUserStatus,
} from "../api/adminUserApi";
import { useAuth } from "../auth/useAuth";

import type { User, UserRole } from "../types/auth";
import type { AdminUserListResponse } from "../types/adminUser";

import "./AdminUsersPage.css";

const PAGE_SIZE = 10;

const AVAILABLE_ROLES: UserRole[] = [
  "employee",
  "manager",
  "admin",
];

function getErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return "An unexpected error occurred.";
  }

  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  switch (error.response?.status) {
    case 403:
      return "This account change is not permitted.";
    case 404:
      return "This user account no longer exists.";
    case 409:
      return "This change would remove the last active administrator.";
    case 422:
      return "The requested account change is invalid.";
    default:
      return "Unable to complete the request.";
  }
}

function AdminUsersPage() {
  const { user: currentUser } = useAuth();

  const [offset, setOffset] = useState(0);
  const [refreshCount, setRefreshCount] = useState(0);

  const [userList, setUserList] =
    useState<AdminUserListResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);
  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  // Track the user whose role is being edited.
  const [editingUser, setEditingUser] =
    useState<User | null>(null);

  const [selectedRole, setSelectedRole] =
    useState<UserRole>("employee");

  const [isConfirming, setIsConfirming] =
    useState(false);

  // Status edits use a separate confirmation workflow.
  const [statusUser, setStatusUser] = useState<User | null>(null);
  const [isStatusConfirming, setIsStatusConfirming] = useState(false);

  const [isSaving, setIsSaving] = useState(false);

  // Load the directory when pagination or refresh changes.
  useEffect(() => {
    let isCurrentRequest = true;

    async function loadUsers() {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const response = await getAdminUsers({
          limit: PAGE_SIZE,
          offset,
        });

        if (!isCurrentRequest) {
          return;
        }

        setUserList(response);
      } catch (error) {
        if (!isCurrentRequest) {
          return;
        }

        setErrorMessage(getErrorMessage(error));
      } finally {
        if (isCurrentRequest) {
          setIsLoading(false);
        }
      }
    }

    void loadUsers();

    return () => {
      isCurrentRequest = false;
    };
  }, [offset, refreshCount]);

  const users = userList?.users ?? [];
  const total = userList?.total ?? 0;

  const hasPreviousPage = offset > 0;
  const hasNextPage = offset + PAGE_SIZE < total;

  const isBusy = isLoading || isSaving;

  function closeEditor() {
    setEditingUser(null);
    setIsConfirming(false);
    setStatusUser(null);
    setIsStatusConfirming(false);
  }

  function handlePrevious() {
    if (isBusy) return;

    closeEditor();
    setSuccessMessage(null);

    setOffset((current) =>
      Math.max(0, current - PAGE_SIZE),
    );
  }

  function handleNext() {
    if (isBusy || !hasNextPage) return;

    closeEditor();
    setSuccessMessage(null);

    setOffset((current) => current + PAGE_SIZE);
  }

  function handleRefresh() {
    if (isBusy) return;

    closeEditor();
    setSuccessMessage(null);

    setRefreshCount((current) => current + 1);
  }

  function handleEditRole(targetUser: User) {
    if (isBusy || targetUser.id === currentUser?.id) {
      return;
    }

    closeEditor();
    setEditingUser(targetUser);
    setSelectedRole(targetUser.role);
    setIsConfirming(false);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  function handleRoleSelection(role: UserRole) {
    setSelectedRole(role);

    // A changed selection requires a new confirmation.
    setIsConfirming(false);
  }

  function handleReviewChange() {
    if (
      !editingUser ||
      selectedRole === editingUser.role ||
      isBusy
    ) {
      return;
    }

    setIsConfirming(true);
  }

  async function handleConfirmRoleChange() {
    if (
      !editingUser ||
      !isConfirming ||
      isBusy ||
      editingUser.id === currentUser?.id ||
      selectedRole === editingUser.role
    ) {
      return;
    }

    const targetUser = editingUser;
    const newRole = selectedRole;

    try {
      setIsSaving(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      const updatedUser = await updateAdminUserRole(
        targetUser.id,
        { role: newRole },
      );

      // Update the visible row immediately.
      setUserList((current) => {
        if (!current) return current;

        return {
          ...current,
          users: current.users.map((user) =>
            user.id === updatedUser.id
              ? updatedUser
              : user,
          ),
        };
      });

      closeEditor();

      setSuccessMessage(
        `${updatedUser.name}'s role was changed to ${updatedUser.role}.`,
      );

      // Fetch the latest database state afterward.
      setRefreshCount((current) => current + 1);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));

      // The server rejected the change: require review again.
      setIsConfirming(false);
    } finally {
      setIsSaving(false);
    }
  }

  function handleEditStatus(targetUser: User) {
    if (isBusy || targetUser.id === currentUser?.id) return;

    closeEditor();
    setStatusUser(targetUser);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  async function handleConfirmStatusChange() {
    if (
      !statusUser ||
      !isStatusConfirming ||
      isBusy ||
      statusUser.id === currentUser?.id
    ) {
      return;
    }

    const targetUser = statusUser;
    const nextIsActive = !targetUser.is_active;

    try {
      setIsSaving(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      const updatedUser = await updateAdminUserStatus(targetUser.id, {
        is_active: nextIsActive,
      });

      setUserList((current) => {
        if (!current) return current;

        return {
          ...current,
          users: current.users.map((user) =>
            user.id === updatedUser.id ? updatedUser : user,
          ),
        };
      });

      closeEditor();
      setSuccessMessage(
        `${updatedUser.name}'s account was ${
          updatedUser.is_active ? "activated" : "deactivated"
        }.`,
      );
      setRefreshCount((current) => current + 1);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setIsStatusConfirming(false);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="admin-users-page">
      <div className="workflows-heading">
        <div>
          <h2>User Management</h2>
          <p>
            View registered users, manage roles,
            and control account access.
          </p>
        </div>
      </div>

      <div className="admin-users-toolbar">
        <button
          type="button"
          className="admin-secondary-button"
          onClick={handleRefresh}
          disabled={isBusy}
        >
          {isLoading && <Spinner />}
          {isLoading ? "Refreshing users..." : "Refresh users"}
        </button>
      </div>

      {errorMessage && (
        <p className="admin-message admin-error" role="alert">
          {errorMessage}
        </p>
      )}

      {successMessage && (
        <p className="admin-message admin-success" role="status">
          {successMessage}
        </p>
      )}

      {isSaving && <p className="admin-saving-status" role="status">Saving account changes...</p>}

      {isLoading ? (
        <LoadingIndicator label="Loading users..." />
      ) : errorMessage ? null
        : users.length === 0 ? (
          <div className="admin-empty-state">
            <h3>No users found</h3>
            <p>
              There are no users to display on this page.
            </p>
          </div>
        ) : (
          <div className="admin-users-card">
            <div className="admin-users-table-container">
              <table className="admin-users-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Role</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {users.map((user) => {
                    const isCurrentUser =
                      user.id === currentUser?.id;

                    return (
                      <tr key={user.id}>
                        <td>{user.name}</td>
                        <td>{user.email}</td>
                        <td>
                          <span className="admin-role-badge">
                            {user.role}
                          </span>
                        </td>
                        <td>
                          <span
                            className={
                              user.is_active
                                ? "admin-status active"
                                : "admin-status inactive"
                            }
                          >
                            {user.is_active
                              ? "Active"
                              : "Inactive"}
                          </span>
                        </td>
                        <td>
                          {isCurrentUser ? (
                            <span className="admin-self-label">
                              Your account
                            </span>
                          ) : (
                            <div className="admin-user-actions">
                              <button
                                type="button"
                                className="admin-secondary-button"
                                onClick={() => handleEditRole(user)}
                                disabled={isBusy}
                                aria-label={`Change role for ${user.name}`}
                              >
                                Change Role
                              </button>
                              <button
                                type="button"
                                className={
                                  user.is_active
                                    ? "admin-danger-button"
                                    : "admin-secondary-button"
                                }
                                onClick={() => handleEditStatus(user)}
                                disabled={isBusy}
                                aria-label={`${
                                  user.is_active ? "Deactivate" : "Activate"
                                } account for ${user.name}`}
                              >
                                {user.is_active ? "Deactivate" : "Activate"}
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="admin-pagination">
              <p>
                Showing {offset + 1}–
                {offset + users.length} of {total} users
              </p>

              <nav
                aria-label="User directory pagination"
                className="admin-pagination-actions"
              >
                <button
                  type="button"
                  className="admin-secondary-button"
                  onClick={handlePrevious}
                  disabled={isBusy || !hasPreviousPage}
                >
                  Previous
                </button>

                <button
                  type="button"
                  className="admin-secondary-button"
                  onClick={handleNext}
                  disabled={isBusy || !hasNextPage}
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        )}

      {statusUser && (
        <section
          className="admin-role-editor"
          aria-labelledby="admin-status-editor-heading"
        >
          <h3 id="admin-status-editor-heading">
            {statusUser.is_active ? "Deactivate Account" : "Activate Account"}
          </h3>
          <p>Account: <strong>{statusUser.name}</strong></p>
          <p>Email: {statusUser.email}</p>
          <p>
            Current status: <strong>{statusUser.is_active ? "Active" : "Inactive"}</strong>
          </p>
          {!isStatusConfirming ? (
            <p>
              {statusUser.is_active
                ? "Deactivation prevents this account from signing in and accessing protected endpoints."
                : "Reactivation restores account access, subject to authentication and permissions."}
            </p>
          ) : (
            <div className="admin-confirmation" role="status">
              <strong>Confirm account status change</strong>
              <p>
                {statusUser.is_active ? "Deactivate" : "Activate"} the account
                belonging to <strong>{statusUser.name}</strong>?
              </p>
              <p>This action will be recorded in the audit log.</p>
            </div>
          )}
          <div className="admin-editor-actions">
            <button
              type="button"
              className="admin-secondary-button"
              onClick={closeEditor}
              disabled={isSaving}
            >
              Cancel
            </button>
            {isStatusConfirming ? (
              <button
                type="button"
                className={statusUser.is_active ? "admin-danger-button" : "admin-primary-button"}
                onClick={() => void handleConfirmStatusChange()}
                disabled={isBusy}
                aria-busy={isSaving}
              >
                {isSaving && <Spinner />}
                {isSaving
                  ? "Saving..."
                  : `Confirm ${statusUser.is_active ? "Deactivation" : "Activation"}`}
              </button>
            ) : (
              <button
                type="button"
                className={statusUser.is_active ? "admin-danger-button" : "admin-primary-button"}
                onClick={() => setIsStatusConfirming(true)}
                disabled={isBusy}
              >
                Review {statusUser.is_active ? "Deactivation" : "Activation"}
              </button>
            )}
          </div>
        </section>
      )}

      {editingUser && (
        <section
          className="admin-role-editor"
          aria-labelledby="admin-role-editor-heading"
        >
          <h3 id="admin-role-editor-heading">
            Change User Role
          </h3>

          <p>
            Account: <strong>{editingUser.name}</strong>
          </p>

          <p>
            Current role: <strong>{editingUser.role}</strong>
          </p>

          <div className="admin-form-field">
            <label htmlFor="admin-role-select">
              New role
            </label>

            <select
              id="admin-role-select"
              value={selectedRole}
              disabled={isSaving}
              onChange={(event) =>
                handleRoleSelection(
                  event.target.value as UserRole,
                )
              }
            >
              {AVAILABLE_ROLES.map((role) => (
                <option key={role} value={role}>
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {isConfirming && (
            <div className="admin-confirmation" role="status">
              <strong>Confirm permission change</strong>
              <p>
                Change {editingUser.name}'s role from{" "}
                <strong>{editingUser.role}</strong> to{" "}
                <strong>{selectedRole}</strong>?
              </p>
              <p>
                This will modify the user's access permissions.
              </p>
            </div>
          )}

          <div className="admin-editor-actions">
            <button
              type="button"
              className="admin-secondary-button"
              onClick={closeEditor}
              disabled={isSaving}
            >
              Cancel
            </button>

            {isConfirming ? (
              <button
                type="button"
                className="admin-primary-button"
                onClick={() => void handleConfirmRoleChange()}
                disabled={isBusy}
                aria-busy={isSaving}
              >
                {isSaving && <Spinner />}
                {isSaving
                  ? "Saving..."
                  : "Confirm Role Change"}
              </button>
            ) : (
              <button
                type="button"
                className="admin-primary-button"
                onClick={handleReviewChange}
                disabled={
                  isBusy ||
                  selectedRole === editingUser.role
                }
              >
                Review Change
              </button>
            )}
          </div>
        </section>
      )}
    </section>
  );
}

export default AdminUsersPage;
