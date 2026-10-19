import { apiClient } from "./client";

import type {
  LoginRequest,
  TokenResponse,
  User,
} from "../types/auth";

export async function login(
  credentials: LoginRequest,
): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(
    "/auth/login",
    credentials,
  );

  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");

  return response.data;
}