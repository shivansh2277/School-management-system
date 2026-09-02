import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  if (loading) return <div className="p-8 text-ink-faint">Loading...</div>;
  if (!me) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
