import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { groupedNav, getUserRoles } from "../screens";

export function Shell() {
  const { me, logout, can, hasModule } = useAuth();
  const userRoles = getUserRoles(me);
  const location = useLocation();

  const [sidebarOpen, setSidebarOpen] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth >= 768 : true
  );

  // Close sidebar on mobile route change
  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, [location.pathname]);

  // Close on Escape key when on mobile
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && sidebarOpen && window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [sidebarOpen]);

  return (
    <div className="min-h-screen flex bg-canvas text-ink">
      {/* Mobile backdrop overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-xs transition-opacity duration-200"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* `invisible` as well as `w-0`: a zero-width overflow-hidden box still
          holds focusable links, so Tab would walk an invisible menu.
          visibility:hidden takes them out of the tab order and the a11y tree,
          and unlike unmounting the nav it leaves the width free to animate.
          On mobile (<768px), it acts as a fixed off-canvas drawer with z-50. */}
      <aside
        id="app-sidebar"
        className={`${
          sidebarOpen
            ? "translate-x-0 w-60"
            : "-translate-x-full w-0 invisible md:translate-x-0"
        } fixed inset-y-0 left-0 z-50 md:static md:inset-auto md:z-auto shrink-0 overflow-hidden bg-primary shadow-xl md:shadow-none transition-all duration-200 ease-in-out`}
      >
       <div className="w-60 h-full text-white/90 p-4 flex flex-col justify-between overflow-y-auto">
        <div>
          <div className="px-3 py-3 mb-2 flex items-center justify-between">
            <div>
              <p className="font-semibold text-white tracking-tight">Sunrise</p>
              <p className="text-xs text-white/70">Public School</p>
            </div>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="md:hidden text-white/70 hover:text-white p-1 rounded-sm focus:outline-none"
              aria-label="Close navigation panel"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <nav className="space-y-4">
            {groupedNav(can, hasModule, userRoles).map(({ group, screens }) => (
              <div key={group ?? "__ungrouped"}>
                {group && (
                  <p className="px-3 pb-1 text-[11px] uppercase tracking-wider font-semibold text-white/50">
                    {group}
                  </p>
                )}
                <div className="space-y-1">
                  {screens.map((screen) => (
                    <NavLink
                      key={screen.path}
                      to={screen.path}
                      end={screen.path === "/"}
                      onClick={() => {
                        if (typeof window !== "undefined" && window.innerWidth < 768) {
                          setSidebarOpen(false);
                        }
                      }}
                      className={({ isActive }) =>
                        `block rounded-input px-3 py-2 text-sm transition-colors ${
                          isActive ? "bg-white text-primary font-semibold shadow-xs" : "hover:bg-white/10 text-white/80"
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
        </div>

        {/* Mobile footer user info */}
        <div className="pt-4 mt-6 border-t border-white/10 text-xs text-white/60 md:hidden">
          <p className="truncate font-medium text-white/80">{me?.user.full_name}</p>
          <p className="truncate text-white/50">{me?.user.login_id}</p>
          <button
            onClick={logout}
            className="mt-3 w-full py-1.5 px-3 rounded-sm bg-white/10 hover:bg-white/20 text-white font-medium text-center transition-colors"
          >
            Sign out
          </button>
        </div>
       </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-14 bg-surface border-b border-rule flex items-center justify-between px-3 sm:px-6 sticky top-0 z-30">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label={sidebarOpen ? "Hide navigation" : "Show navigation"}
              aria-expanded={sidebarOpen}
              aria-controls="app-sidebar"
              className="-ml-1 sm:-ml-2 rounded-input p-2 text-ink-soft hover:bg-canvas hover:text-ink cursor-pointer transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                <g stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
                  <line x1="2" y1="4.5" x2="16" y2="4.5" />
                  <line x1="2" y1="9" x2="16" y2="9" />
                  <line x1="2" y1="13.5" x2="16" y2="13.5" />
                </g>
              </svg>
            </button>
            <span className="text-xs sm:text-sm text-ink-soft truncate">
              <span>{me?.school_name}</span>
              {me?.academic_year ? (
                <span className="hidden sm:inline"> · Academic year {me.academic_year}</span>
              ) : null}
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm shrink-0">
            <span className="text-ink-soft hidden md:inline truncate max-w-[180px]">{me?.user.full_name}</span>
            <button onClick={logout} className="text-primary hover:underline font-medium cursor-pointer">
              Sign out
            </button>
          </div>
        </header>
        <main className="p-3 sm:p-5 md:p-6 space-y-4 sm:space-y-6 max-w-full overflow-x-hidden flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
