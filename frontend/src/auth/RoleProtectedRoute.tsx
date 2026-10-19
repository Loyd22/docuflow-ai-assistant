import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import type { UserRole } from "../types/auth";
import { useAuth } from "./useAuth";

type RoleProtectedRouteProps = {
  allowedRoles: UserRole[];
  children: ReactNode;
};

export function RoleProtectedRoute({
  allowedRoles,
  children,
}: RoleProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/forbidden" replace />;
  }

  return children;
}