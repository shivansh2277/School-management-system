import { Route, Routes } from "react-router-dom";

import { LoginPage } from "./auth/LoginPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Shell } from "./layout/Shell";
import { Attendance } from "./pages/Attendance";
import { Classes } from "./pages/Classes";
import { Dashboard } from "./pages/Dashboard";
import { Exams } from "./pages/Exams";
import { Fees } from "./pages/Fees";
import { Notices } from "./pages/Notices";
import { Settings } from "./pages/Settings";
import { Students } from "./pages/Students";
import { Teachers } from "./pages/Teachers";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Shell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/students" element={<Students />} />
        <Route path="/teachers" element={<Teachers />} />
        <Route path="/classes" element={<Classes />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/exams" element={<Exams />} />
        <Route path="/fees" element={<Fees />} />
        <Route path="/notices" element={<Notices />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
