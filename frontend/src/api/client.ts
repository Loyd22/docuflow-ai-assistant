/**
 * Shared HTTP client for communication with the DocuFlow backend.
 *
 * All frontend features should use this client instead of
 * creating separate Axios configurations.
 */

import axios from "axios";

// Read the backend URL from the Vite environment configuration.
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!apiBaseUrl) {
  throw new Error("VITE_API_BASE_URL is not configured.");
}

export const apiClient = axios.create({
  baseURL: apiBaseUrl,

  // Prevent requests from waiting forever.
  timeout: 10_000,

  headers: {
    "Content-Type": "application/json",
  },
});