
import {
  Route,
  Routes,
} from "react-router-dom";

import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleHomeRedirect } from "./auth/RoleHomeRedirect";
import { RoleProtectedRoute } from "./auth/RoleProtectedRoute";

import AppLayout from "./layouts/AppLayout";

import AdminUsersPage from "./pages/AdminUsersPage";
import AuditLogsPage from "./pages/AuditLogsPage";
import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import WorkflowsPage from "./pages/WorkflowsPage";

function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/forbidden"
        element={<ForbiddenPage />}
      />

      {/* All routes inside this layout require authentication. */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route
          path="/"
          element={<RoleHomeRedirect />}
        />

        <Route
          path="/dashboard"
          element={
            <RoleProtectedRoute
              allowedRoles={["manager", "admin"]}
            >
              <DashboardPage />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/documents"
          element={<DocumentsPage />}
        />

        <Route
          path="/workflows"
          element={<WorkflowsPage />}
        />

        <Route
          path="/audit-logs"
          element={
            <RoleProtectedRoute
              allowedRoles={["manager", "admin"]}
            >
              <AuditLogsPage />
            </RoleProtectedRoute>
          }
        />

        {/* Only administrators can access user management. */}
        <Route
          path="/admin/users"
          element={
            <RoleProtectedRoute
              allowedRoles={["admin"]}
            >
              <AdminUsersPage />
            </RoleProtectedRoute>
          }
        />
      </Route>

      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}

export default App;
