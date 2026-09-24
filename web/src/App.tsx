import { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import { LoginPage } from "./auth/LoginPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RequirePermission } from "./auth/RequirePermission";
import { PublicLayout } from "./components/public/PublicLayout";
import { Shell } from "./layout/Shell";
import { PublicApplyPage } from "./pages/public/PublicApplyPage";
import { AboutPage } from "./pages/public/website/AboutPage";
import { AcademicsPage } from "./pages/public/website/AcademicsPage";
import { AdmissionsPage } from "./pages/public/website/AdmissionsPage";
import { FacilitiesPage } from "./pages/public/website/FacilitiesPage";
import { HomePage } from "./pages/public/website/HomePage";
import { SCREENS, getUserRoles, visibleScreens } from "./screens";

/**
 * The root "/" route:
 * - When an unauthenticated visitor (parent, student, visitor) visits,
 *   it renders the public Sunrise School HomePage.
 * - When an authenticated staff member navigates to "/", it sends them to
 *   the first screen the registry says their role can open (e.g. /dashboard
 *   for Admin, /students for Fee Collector) without a redirect loop.
 */
function Home() {
  const { me, can, hasModule, logout } = useAuth();
  if (me) {
    const userRoles = getUserRoles(me);
    const screens = visibleScreens(can, hasModule, userRoles);
    const transportScreen = userRoles.includes("transport_incharge")
      ? screens.find((s) => s.path === "/transport")
      : undefined;
    const first = transportScreen ?? screens[0];
    if (!first) {
      return (
        <div className="min-h-[60vh] flex items-center justify-center p-4">
          <div className="rounded-card bg-surface border border-rule p-8 max-w-md w-full shadow-card text-center space-y-4">
            <p className="font-semibold text-lg text-ink">No screens enabled</p>
            <p className="text-sm text-ink-soft">
              Your account does not have access to any enabled screens, or your session needs to be refreshed.
            </p>
            <button
              onClick={() => {
                logout();
                window.location.hash = "#/login";
              }}
              className="rounded-input bg-primary text-white px-5 py-2.5 text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer w-full"
            >
              Sign out & Re-login
            </button>
          </div>
        </div>
      );
    }
    return <Navigate to={first.path} replace />;
  }
  return <HomePage />;
}

function NotFound() {
  return (
    <div className="rounded-card bg-surface border border-rule p-8">
      <p className="font-medium text-ink">Page not found</p>
      <p className="text-sm text-ink-soft mt-1">There is nothing at this address.</p>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      {/* Existing ERP Login & Application Entry Points */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/apply" element={<PublicApplyPage />} />

      {/* Public School Website Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/academics" element={<AcademicsPage />} />
        <Route path="/admissions" element={<AdmissionsPage />} />
        <Route path="/facilities" element={<FacilitiesPage />} />
      </Route>

      {/* Protected ERP Screens for Authorized School Staff */}
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
        {/* Direct URL aliases for legacy or alternate route naming */}
        <Route path="/admission/selection" element={<Navigate to="/admission/merit" replace />} />
        <Route path="/reception/found-lost" element={<Navigate to="/reception/found-items" replace />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
