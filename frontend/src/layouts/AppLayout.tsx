import {
  NavLink,
  Outlet,
} from "react-router-dom";

import { useAuth } from "../auth/useAuth";

import "./AppLayout.css";

function AppLayout() {
  const { user, logout } = useAuth();

  const canViewManagementPages =
    user?.role === "manager" || user?.role === "admin";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>DocuFlow AI</h1>
          <p>Document Workflow System</p>
        </div>

        <nav className="sidebar-nav">
          {canViewManagementPages && (
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              Dashboard
            </NavLink>
          )}

          <NavLink
            to="/documents"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Documents
          </NavLink>

          <NavLink
            to="/workflows"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            Workflows
          </NavLink>

          {canViewManagementPages && (
            <NavLink
              to="/audit-logs"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              Audit Logs
            </NavLink>
          )}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            <strong>{user?.name}</strong>
            <span className="user-role">{user?.role}</span>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={logout}
          >
            Sign out
          </button>
        </header>

        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default AppLayout;