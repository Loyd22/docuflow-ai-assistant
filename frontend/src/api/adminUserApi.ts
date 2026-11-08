import { apiClient } from "./client";

import type { User } from "../types/auth";

import type {
  AdminUserListParams,
  AdminUserListResponse,
  AdminUserRoleUpdateRequest,
  AdminUserStatusUpdateRequest,
} from "../types/adminUser";

// Retrieve a paginated list of users.
export async function getAdminUsers(
  params: AdminUserListParams = {},
): Promise<AdminUserListResponse> {
  const response = await apiClient.get<AdminUserListResponse>(
    "/admin/users",
    { params },
  );

  return response.data;
}

// Change an existing user's role.
export async function updateAdminUserRole(
  userId: number,
  request: AdminUserRoleUpdateRequest,
): Promise<User> {
  const response = await apiClient.patch<User>(
    `/admin/users/${userId}/role`,
    request,
  );

  return response.data;
}

// Activate or deactivate an account.
export async function updateAdminUserStatus(
  userId: number,
  request: AdminUserStatusUpdateRequest,
): Promise<User> {
  const response = await apiClient.patch<User>(
    `/admin/users/${userId}/status`,
    request,
  );

  return response.data;
}