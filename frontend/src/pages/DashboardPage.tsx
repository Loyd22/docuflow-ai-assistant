import type { DashboardStats } from "../types/dashboardTypes";


function DashboardPage() {
  // This is temporary static data.
  // Later, this will come from the backend dashboard API.
  const stats: DashboardStats = {
    totalDocuments: 0,
    pendingApprovals: 0,
    urgentDocuments: 0,
  };

  return (
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>DocuFlow AI Dashboard</h1>

      <p>
        Welcome to DocuFlow AI. This dashboard will later show document
        statistics, pending approvals, urgent documents, and recent activity.
      </p>

      <section style={{ display: "flex", gap: "1rem", marginTop: "2rem" }}>
        <div style={{ border: "1px solid #ddd", padding: "1rem", borderRadius: "8px" }}>
          <h3>Total Documents</h3>
          <p>{stats.totalDocuments}</p>
        </div>

        <div style={{ border: "1px solid #ddd", padding: "1rem", borderRadius: "8px" }}>
          <h3>Pending Approvals</h3>
          <p>{stats.pendingApprovals}</p>
        </div>

        <div style={{ border: "1px solid #ddd", padding: "1rem", borderRadius: "8px" }}>
          <h3>Urgent Documents</h3>
          <p>{stats.urgentDocuments}</p>
        </div>
      </section>
    </main>
  );
}


export default DashboardPage;