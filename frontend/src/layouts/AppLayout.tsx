import {
  NavLink,
  Outlet,
} from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import ShellIcon from "./ShellIcon";

import "./AppLayout.css";

function AppLayout() {
  const { user, logout } = useAuth();

  const canViewManagementPages =
    user?.role === "manager" || user?.role === "admin";

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark"><ShellIcon name="documents" /></span>
          <div>
            <h1>DocuFlow AI</h1>
            <p>Document Workflow System</p>
          </div>
        </div>

        <p className="sidebar-section-label">Workspace</p>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {canViewManagementPages && (
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <ShellIcon name="dashboard" />Dashboard
            </NavLink>
          )}

          <NavLink
            to="/documents"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            <ShellIcon name="documents" />Documents
          </NavLink>

          <NavLink
            to="/workflows"
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            <ShellIcon name="workflows" />Workflows
          </NavLink>

          {canViewManagementPages && (
            <NavLink
              to="/audit-logs"
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              <ShellIcon name="audit" />Audit Logs
            </NavLink>
          )}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div className="header-workspace">Document workspace</div>
          <div className="header-account">
            <span className="user-avatar" aria-hidden="true">
              {user?.name.trim().charAt(0).toLocaleUpperCase()}
            </span>
            <div className="user-details">
              <strong>{user?.name}</strong>
              <span className="user-role">{user?.role}</span>
            </div>

            <button
              type="button"
              className="logout-button"
              onClick={logout}
            >
              <ShellIcon name="logout" />
              Sign out
            </button>
          </div>
        </header>

        <main className="page-content" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
