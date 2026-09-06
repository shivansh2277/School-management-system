import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

/** Only screens that exist are linked. BLUEPRINT section 18: no dead menu items. */
const NAV = [
  ["/", "Dashboard"],
  ["/students", "Students"],
  ["/teachers", "Teachers"],
  ["/classes", "Classes"],
  ["/attendance", "Attendance"],
  ["/exams", "Exams"],
  ["/fees", "Fees"],
  ["/notices", "Notices"],
  ["/settings", "Settings"],
] as const;

export function Shell() {
  const { me, logout } = useAuth();
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 bg-primary text-white/90 p-4 flex flex-col">
        <div className="px-2 py-3 mb-2">
          <p className="font-semibold text-white">Sunrise</p>
          <p className="text-xs text-white/70">Public School</p>
        </div>
        <nav className="space-y-1 flex-1">
          {NAV.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `block rounded-input px-3 py-2 text-sm ${
                  isActive ? "bg-white text-primary font-medium" : "hover:bg-white/10"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0">
        <header className="h-14 bg-surface border-b border-rule flex items-center justify-between px-6">
          <span className="text-sm text-ink-soft">Academic year 2025-26</span>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-ink-soft">{me?.user.full_name}</span>
            <button onClick={logout} className="text-primary hover:underline">
              Sign out
            </button>
          </div>
        </header>
        <main className="p-6 space-y-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
