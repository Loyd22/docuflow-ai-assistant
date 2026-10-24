
import {
  type FormEvent,
  useState,
} from "react";
import axios from "axios";
import {
  Navigate,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import ShellIcon from "../layouts/ShellIcon";
import "./LoginPage.css";

function LoginPage() {
  const navigate = useNavigate();

  const {
    isAuthenticated,
    isLoading,
    login,
  } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  if (isLoading) {
    return <main className="login-loading"><p role="status">Loading...</p></main>;
  }

  // Send authenticated users to the role-based home page.
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login({
        email,
        password,
      });

      // Let RoleHomeRedirect choose the correct landing page.
      navigate("/", {
        replace: true,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage("Unable to sign in.");
        }
      } else {
        setErrorMessage("Unable to sign in.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-branding" aria-labelledby="login-brand-heading">
        <div className="login-brand">
          <span className="login-brand-mark"><ShellIcon name="documents" /></span>
          <span>DocuFlow AI</span>
        </div>
        <div className="login-brand-content">
          <h1 id="login-brand-heading">Intelligent Document Workflows</h1>
          <p>Simplify document processing, automate analysis, and manage approvals in one place.</p>
          <div className="login-illustration" aria-hidden="true">
            <div className="login-document login-document-back" />
            <div className="login-document login-document-front">
              <ShellIcon name="documents" />
              <span /><span /><span />
              <div className="login-document-lines"><i /><i /><i /></div>
            </div>
            <div className="login-flow-node"><ShellIcon name="workflows" /></div>
            <div className="login-flow-check"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" focusable="false"><path d="m5 12 4 4L19 6" /></svg></div>
          </div>
        </div>
      </section>
      <section className="login-form-panel" aria-labelledby="login-form-heading">
        <div className="login-form-content">
          <h2 id="login-form-heading">Welcome back</h2>
          <p className="login-form-description">Sign in to your DocuFlow AI account.</p>
          <form className="login-form" onSubmit={handleSubmit} aria-busy={isSubmitting}>
        <div className="login-field">
          <label htmlFor="email">
            Email
          </label>

          <input
            id="email"
            type="email"
            name="email"
            autoCapitalize="none"
            spellCheck={false}
            aria-describedby={errorMessage ? "login-error" : undefined}
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
            required
            autoComplete="email"
          />
        </div>

        <div className="login-field">
          <label htmlFor="password">
            Password
          </label>

          <input
            id="password"
            type="password"
            name="password"
            aria-describedby={errorMessage ? "login-error" : undefined}
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
            required
            autoComplete="current-password"
          />
        </div>

        {errorMessage && (
          <p className="login-error" id="login-error" role="alert">
            {errorMessage}
          </p>
        )}

        <button
          type="submit"
          className="login-submit"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Signing in..."
            : "Sign in"}
        </button>
          </form>
        </div>
      </section>
    </main>
  );
}

export default LoginPage;
