import type { User, UserRole } from "./auth";

// Paginated user list returned by FastAPI.
export type AdminUserListResponse = {
  users: User[];
  total: number;
  limit: number;
  offset: number;
};

// Query parameters for the user directory.
export type AdminUserListParams = {
  limit?: number;
  offset?: number;
};

// Request body for changing a user's role.
export type AdminUserRoleUpdateRequest = {
  role: UserRole;
};

// Request body for activating or deactivating an account.
export type AdminUserStatusUpdateRequest = {
  is_active: boolean;
};