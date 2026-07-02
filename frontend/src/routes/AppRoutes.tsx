// This imports React Router tools for frontend page routing.
import { BrowserRouter, Routes, Route } from "react-router-dom";

// This imports the dashboard page.
import DashboardPage from "../pages/DashboardPage";

// This component stores all frontend routes.
function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}

// This allows App.tsx to import AppRoutes.
export default AppRoutes;