/**
 * Temporary Phase 2 application screen.
 *
 * This screen verifies that the React frontend can communicate
 * with the FastAPI backend.
 */

import { useEffect, useState } from "react";

import { apiClient } from "./api/client";


type HealthResponse = {
  status: string;
  service: string;
};


function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function checkBackendHealth() {
      try {
        const response = await apiClient.get<HealthResponse>("/health");

        setBackendStatus(response.data.status);
      } catch {
        setBackendStatus("unavailable");
        setErrorMessage("The frontend could not connect to the backend.");
      }
    }

    checkBackendHealth();
  }, []);

  return (
    <main>
      <h1>DocuFlow AI</h1>

      <p>Backend status: {backendStatus}</p>

      {errorMessage && <p>{errorMessage}</p>}
    </main>
  );
}

export default App;