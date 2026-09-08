import { Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "./auth/LoginPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RequirePermission } from "./auth/RequirePermission";
import { Shell } from "./layout/Shell";
import { SCREENS } from "./screens";

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
        {SCREENS.map((screen) => (
          <Route
            key={screen.path}
            path={screen.path}
            element={
              <RequirePermission screen={screen}>
                <Suspense fallback={<div className="text-ink-faint">Loading...</div>}>
                  <screen.element />
                </Suspense>
              </RequirePermission>
            }
          />
        ))}
      </Route>
    </Routes>
  );
}
