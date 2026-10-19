import { Link } from "react-router-dom";

function ForbiddenPage() {
  return (
    <main className="standalone-page">
      <h1>Access denied</h1>

      <p>
        Your account does not have permission to view this page.
      </p>

      <Link to="/">
        Return to DocuFlow
      </Link>
    </main>
  );
}

export default ForbiddenPage;