import { useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { me, login } = useAuth();
  const [loginId, setLoginId] = useState("admin@sunrisepublic.edu");
  const [password, setPassword] = useState("Admin@123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (me) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(loginId, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-ground px-4">
      <form
        onSubmit={submit}
        className="w-full max-w-sm bg-surface rounded-card shadow-card p-8 space-y-5"
      >
        <div>
          <h1 className="text-xl font-semibold">Sunrise Public School</h1>
          <p className="text-sm text-ink-soft">Admin dashboard</p>
        </div>

        <label className="block text-sm">
          <span className="text-ink-soft">Email</span>
          <input
            className="mt-1 w-full rounded-input border border-rule px-3 py-2 outline-none focus:border-primary"
            value={loginId}
            onChange={(e) => setLoginId(e.target.value)}
            autoComplete="username"
          />
        </label>

        <label className="block text-sm">
          <span className="text-ink-soft">Password</span>
          <input
            type="password"
            className="mt-1 w-full rounded-input border border-rule px-3 py-2 outline-none focus:border-primary"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          disabled={busy}
          className="w-full rounded-input bg-primary py-2 text-white font-medium hover:bg-primary-dark disabled:opacity-60"
        >
          {busy ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-xs text-ink-faint">
          Demo admin: admin@sunrisepublic.edu / Admin@123
        </p>
      </form>
    </div>
  );
}
