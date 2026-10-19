import { Navigate } from "react-router-dom";

import { useAuth } from "./useAuth";

export function RoleHomeRedirect() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === "manager" || user.role === "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Navigate to="/documents" replace />;
}