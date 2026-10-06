import { useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { me, login } = useAuth();
  const [loginId, setLoginId] = useState("admin@sunrisepublic.edu");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (me && me.permissions && me.permissions.length > 0) return <Navigate to="/" replace />;

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

  const setDemoRole = (id: string) => {
    setLoginId(id);
    setPassword("Admin@123");
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-gradient-to-b from-[#f8fafc] via-[#f1f5f9] to-[#e2e8f0] px-4 py-8">
      {/* Top micro brand banner */}
      <div className="flex items-center justify-between max-w-4xl w-full mx-auto pb-4">
        <Link to="/" className="flex items-center gap-2 group text-ink hover:text-primary transition-colors">
          <div className="w-8 h-8 rounded-lg bg-[#042954] flex items-center justify-center text-[#ffa726] shadow-xs">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zm0 2c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41l-1.29-1.29zm-13.78 1.41l1.29-1.29c.39-.39.39-1.02 0-1.41a.996.996 0 00-1.41 0l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0zm15.19-15.19l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.29-1.29a.996.996 0 000-1.41c-.39-.39-1.02-.39-1.41 0z" />
            </svg>
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight text-[#042954]">Sunrise Public School</span>
            <span className="hidden sm:inline text-xs text-ink-faint"> · ERP Portal</span>
          </div>
        </Link>
        <Link
          to="/"
          className="text-xs font-semibold text-ink-soft hover:text-primary transition-colors flex items-center gap-1"
        >
          <span>&larr; Public Website</span>
        </Link>
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-md mx-auto my-auto">
        <div className="bg-surface rounded-2xl shadow-xl border border-rule/80 overflow-hidden">
          {/* Card Accent Top Header */}
          <div className="bg-gradient-to-r from-[#042954] to-[#0a3a70] p-6 text-white text-center relative">
            <div className="w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-xs border border-white/20 mx-auto flex items-center justify-center text-[#ffa726] shadow-sm mb-3">
              <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zm0 2c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41l-1.29-1.29zm-13.78 1.41l1.29-1.29c.39-.39.39-1.02 0-1.41a.996.996 0 00-1.41 0l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0zm15.19-15.19l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.29-1.29a.996.996 0 000-1.41c-.39-.39-1.02-.39-1.41 0z" />
              </svg>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white">Sunrise Public School</h1>
            <p className="text-xs text-blue-200/80 font-medium mt-1">Admin ERP & Management Portal</p>
          </div>

          {/* Form Body */}
          <form onSubmit={submit} className="p-6 sm:p-8 space-y-5">
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-start gap-2.5">
                <svg className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="flex-1">{error}</div>
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-ink-soft uppercase tracking-wider">
                Staff Email / Login ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-faint">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" />
                  </svg>
                </div>
                <input
                  type="text"
                  className="w-full rounded-xl border border-rule/90 pl-9 pr-3 py-2.5 text-sm font-medium text-ink bg-white outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 shadow-2xs transition-all"
                  placeholder="admin@sunrisepublic.edu"
                  value={loginId}
                  onChange={(e) => setLoginId(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-ink-soft uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-ink-faint">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  className="w-full rounded-xl border border-rule/90 pl-9 pr-10 py-2.5 text-sm font-medium text-ink bg-white outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 shadow-2xs transition-all"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-ink-faint hover:text-ink cursor-pointer transition-colors"
                >
                  {showPassword ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Sign in Button */}
            <button
              disabled={busy}
              type="submit"
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#042954] to-[#0a3a70] hover:from-[#021b38] hover:to-[#042954] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {busy ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Signing in to Portal...</span>
                </>
              ) : (
                <span>Sign in to ERP</span>
              )}
            </button>

            {/* Demo Quick-Fill Selector */}
            <div className="pt-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
                <span className="font-semibold text-ink-soft block mb-1.5">Quick Demo Roles (Password: Admin@123):</span>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => setDemoRole("admin@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Admin
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("accounts@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Accounts
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("admission@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Admissions
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("receptionist@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Reception
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("transport@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Transport
                  </button>
                  <button
                    type="button"
                    onClick={() => setDemoRole("librarian@sunrisepublic.edu")}
                    className="px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-primary text-ink text-[11px] font-medium transition-colors cursor-pointer"
                  >
                    Librarian
                  </button>
                </div>
              </div>
            </div>

            {/* Secondary navigation footer */}
            <div className="pt-4 border-t border-rule/80 text-center space-y-2">
              <p className="text-xs text-ink-soft">
                Prospective parent?{" "}
                <Link to="/apply" className="text-primary font-bold hover:underline">
                  Apply for Online Admission &rarr;
                </Link>
              </p>
              <p className="text-xs">
                <Link to="/" className="text-ink-faint hover:text-ink font-medium transition-colors">
                  &larr; Back to Sunrise School Website
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>

      {/* Footer copyright */}
      <div className="text-center text-xs text-ink-faint max-w-md mx-auto pt-6">
        &copy; {new Date().getFullYear()} Sunrise Public School. All rights reserved.
      </div>
    </div>
  );
}
