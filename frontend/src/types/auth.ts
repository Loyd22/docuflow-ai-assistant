// Roles currently supported by the DocuFlow backend.
export type UserRole = "employee" | "manager" | "admin";

// Data sent to the backend when a user logs in.
export type LoginRequest = {
  email: string;
  password: string;
};

// JWT response returned by POST /auth/login.
export type TokenResponse = {
  access_token: string;
  token_type: string;
};

// Safe user data returned by GET /auth/me.
export type User = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
};