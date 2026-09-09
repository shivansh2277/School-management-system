import { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RequirePermission } from "./auth/RequirePermission";
import { Shell } from "./layout/Shell";
import { SCREENS, visibleScreens } from "./screens";

/**
 * "/" used to be the Dashboard's own path, gated on admin.settings.read -
 * a permission only 4 of 11 staff roles hold. Everyone else who signed in
 * landed on a permission-denied panel with no way back, since Dashboard is
 * (correctly) hidden from their sidebar too.
 *
 * Dashboard now lives at /dashboard like any other screen, and "/" is this
 * index route: send the caller to the first screen the registry says they
 * can actually open. That's the same list the sidebar renders from, so this
 * can never redirect somewhere RequirePermission would then refuse - no
 * loop. A caller with no visible screens at all (a role holding nothing in
 * SCREENS) gets a plain explanation instead of bouncing anywhere.
 */
function Home() {
  const { can, hasModule } = useAuth();
  const first = visibleScreens(can, hasModule)[0];
  if (!first) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">No screens enabled</p>
        <p className="text-sm text-ink-soft mt-1">
          Your account does not have access to anything in this dashboard. Contact the office.
        </p>
      </div>
    );
  }
  return <Navigate to={first.path} replace />;
}

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
        <Route index element={<Home />} />
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
