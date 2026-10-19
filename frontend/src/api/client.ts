/**
 * Shared HTTP client for communication with the DocuFlow backend.
 *
 * All frontend features should use this client instead of
 * creating separate Axios configurations.
 */

import axios from "axios";

import { getAccessToken } from "../auth/tokenStorage";

// Read the backend URL from the Vite environment configuration.
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!apiBaseUrl) {
  throw new Error("VITE_API_BASE_URL is not configured.");
}

export const apiClient = axios.create({
  baseURL: apiBaseUrl,

  // Prevent normal requests from waiting forever.
  timeout: 10_000,
});

// Add the JWT automatically when the user is logged in.
apiClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken();

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});