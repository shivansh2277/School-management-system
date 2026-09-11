import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { groupedNav } from "../screens";

export function Shell() {
  const { me, logout, can, hasModule } = useAuth();
  // Not persisted: this already survives navigation, because Shell is not
  // remounted between routes, and remembering it across sessions would be a
  // second decision to get wrong for no one who asked.
  const [sidebarOpen, setSidebarOpen] = useState(true);
  return (
    <div className="min-h-screen flex">
      {/* `invisible` as well as `w-0`: a zero-width overflow-hidden box still
          holds focusable links, so Tab would walk an invisible menu.
          visibility:hidden takes them out of the tab order and the a11y tree,
          and unlike unmounting the nav it leaves the width free to animate.
          The inner w-60 keeps the labels from reflowing as the box closes. */}
      <aside
        id="app-sidebar"
        className={`${sidebarOpen ? "w-60" : "w-0 invisible"} shrink-0 overflow-hidden bg-primary transition-[width,visibility] duration-200 ease-in-out`}
      >
       <div className="w-60 h-full text-white/90 p-4 flex flex-col">
        <div className="px-2 py-3 mb-2">
          <p className="font-semibold text-white">Sunrise</p>
          <p className="text-xs text-white/70">Public School</p>
        </div>
        <nav className="space-y-4 flex-1">
          {groupedNav(can, hasModule).map(({ group, screens }) => (
            <div key={group ?? "__ungrouped"}>
              {/* No heading for an ungrouped screen: Dashboard under a heading
                  reading "OVERVIEW" was a label repeating itself. */}
              {group && (
                <p className="px-3 pb-1 text-[11px] uppercase tracking-wide text-white/50">
                  {group}
                </p>
              )}
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
       </div>
      </aside>

      <div className="flex-1 min-w-0">
        <header className="h-14 bg-surface border-b border-rule flex items-center justify-between px-6">
          <div className="flex items-center gap-3 min-w-0">
            {/* In the header, not the sidebar, so it is still there to press
                once the sidebar has gone. */}
            <button
              type="button"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label={sidebarOpen ? "Hide navigation" : "Show navigation"}
              aria-expanded={sidebarOpen}
              aria-controls="app-sidebar"
              className="-ml-2 rounded-input p-2 text-ink-soft hover:bg-canvas hover:text-ink"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                <g stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
                  <line x1="2" y1="4.5" x2="16" y2="4.5" />
                  <line x1="2" y1="9" x2="16" y2="9" />
                  <line x1="2" y1="13.5" x2="16" y2="13.5" />
                </g>
              </svg>
            </button>
            <span className="text-sm text-ink-soft truncate">
              {me?.school_name}
              {me?.academic_year ? ` · Academic year ${me.academic_year}` : ""}
            </span>
          </div>
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
