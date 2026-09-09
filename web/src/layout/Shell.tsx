import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { groupedNav } from "../screens";

export function Shell() {
  const { me, logout, can, hasModule } = useAuth();
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 bg-primary text-white/90 p-4 flex flex-col">
        <div className="px-2 py-3 mb-2">
          <p className="font-semibold text-white">Sunrise</p>
          <p className="text-xs text-white/70">Public School</p>
        </div>
        <nav className="space-y-4 flex-1">
          {groupedNav(can, hasModule).map(({ group, screens }) => (
            <div key={group}>
              <p className="px-3 pb-1 text-[11px] uppercase tracking-wide text-white/50">{group}</p>
              <div className="space-y-1">
                {screens.map((screen) => (
                  <NavLink
                    key={screen.path}
                    to={screen.path}
                    end={screen.path === "/"}
                    className={({ isActive }) =>
                      `block rounded-input px-3 py-2 text-sm ${
                        isActive ? "bg-white text-primary font-medium" : "hover:bg-white/10"
                      }`
                    }
                  >
                    {screen.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0">
        <header className="h-14 bg-surface border-b border-rule flex items-center justify-between px-6">
          <span className="text-sm text-ink-soft">
            {me?.school_name}
            {me?.academic_year ? ` · Academic year ${me.academic_year}` : ""}
          </span>
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
