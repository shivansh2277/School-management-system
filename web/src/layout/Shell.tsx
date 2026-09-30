import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { groupedNav, getUserRoles } from "../screens";
import { NavIcon, screenHasChevron } from "./NavIcons";

export function Shell() {
  const { me, logout, can, hasModule } = useAuth();
  const userRoles = getUserRoles(me);
  const location = useLocation();

  const [sidebarOpen, setSidebarOpen] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth >= 768 : true,
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
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-xs transition-opacity duration-200"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Solid Dark-Blue Vertical Sidebar (Akkhor design pattern) */}
      <aside
        id="app-sidebar"
        className={`${
          sidebarOpen
            ? "translate-x-0 w-60"
            : "-translate-x-full w-0 invisible md:translate-x-0"
        } fixed inset-y-0 left-0 z-50 md:static md:inset-auto md:z-auto shrink-0 overflow-hidden bg-[#042954] shadow-2xl md:shadow-none transition-all duration-200 ease-in-out`}
      >
        <div className="w-60 h-full text-white/90 flex flex-col justify-between overflow-y-auto">
          <div>
            {/* Top Amber Branding Header with Logo */}
            <div className="h-14 bg-gradient-to-r from-[#ffa726] to-[#fb8c00] px-4 flex items-center shadow-xs select-none">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-white shadow-xs flex items-center justify-center shrink-0">
                  <svg
                    className="w-5 h-5 text-amber-500"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zm0 2c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.29 1.29c.39.39 1.02.39 1.41 0 .39-.39.39-1.02 0-1.41l-1.29-1.29zm-13.78 1.41l1.29-1.29c.39-.39.39-1.02 0-1.41a.996.996 0 00-1.41 0l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0zm15.19-15.19l-1.29 1.29c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.29-1.29a.996.996 0 000-1.41c-.39-.39-1.02-.39-1.41 0z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <p className="font-extrabold text-white tracking-wider text-sm leading-tight uppercase truncate">
                    Sunrise
                  </p>
                  <p className="text-[10px] text-amber-100 font-semibold tracking-wider uppercase leading-none truncate">
                    Public School
                  </p>
                </div>
              </div>
            </div>

            {/* Structured Vertical Navigation List */}
            <nav className="flex-1 py-1 divide-y divide-[#0d3361]/40">
              {groupedNav(can, hasModule, userRoles).map(
                ({ group, screens }, idx) => (
                  <div key={group ?? "__ungrouped"} className="py-1">
                    {/* Visually Distinct Section/Category Heading */}
                    {group && (
                      <div className="px-3.5 pt-3 pb-1 flex items-center justify-between text-[10px] font-bold tracking-wider text-blue-200/50 uppercase select-none">
                        <div className="flex items-center gap-1.5">
                          <span className="w-1 h-2.5 rounded-full bg-[#ffa726]/80 shrink-0" />
                          <span>{group}</span>
                        </div>
                        <div className="flex-1 h-px bg-white/[0.06] ml-2" />
                      </div>
                    )}

                    {/* Navigation Items */}
                    <div className="space-y-0.5">
                      {screens.map((screen) => {
                        const hasChevron = screenHasChevron(screen.path);
                        return (
                          <NavLink
                            key={screen.path}
                            to={screen.path}
                            end={screen.path === "/"}
                            onClick={() => {
                              if (
                                typeof window !== "undefined" &&
                                window.innerWidth < 768
                              ) {
                                setSidebarOpen(false);
                              }
                            }}
                            className={({ isActive }) =>
                              `group flex items-center gap-3 px-3.5 py-2.5 text-sm transition-all duration-150 border-b border-white/[0.03] ${
                                isActive
                                  ? "bg-[#021b38] text-[#ffa726] font-semibold border-l-4 border-l-[#ffa726] pl-[10px]"
                                  : "text-[#c2d0e2] hover:bg-[#072d5c] hover:text-white"
                              }`
                            }
                          >
                            {({ isActive }) => (
                              <>
                                <NavIcon
                                  path={screen.path}
                                  active={isActive}
                                />
                                <span className="truncate flex-1">
                                  {screen.label}
                                </span>
                                {hasChevron && (
                                  <svg
                                    className={`w-3.5 h-3.5 shrink-0 transition-colors ${
                                      isActive
                                        ? "text-[#ffa726]"
                                        : "text-slate-400/50 group-hover:text-slate-200"
                                    }`}
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={2.5}
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  >
                                    <path d="M9 5l7 7-7 7" />
                                  </svg>
                                )}
                              </>
                            )}
                          </NavLink>
                        );
                      })}
                    </div>
                  </div>
                ),
              )}
            </nav>
          </div>

          {/* Mobile Footer User Details */}
          <div className="p-4 border-t border-white/10 text-xs text-white/60 md:hidden bg-[#021b38]/50">
            <p className="truncate font-medium text-white/90">
              {me?.user.full_name}
            </p>
            <p className="truncate text-white/50">{me?.user.login_id}</p>
            <button
              onClick={logout}
              className="mt-3 w-full py-1.5 px-3 rounded-sm bg-white/10 hover:bg-white/20 text-white font-medium text-center transition-colors cursor-pointer"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Main Header with Secondary Toggle & Branding */}
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
                <span className="hidden sm:inline">
                  {" "}
                  · Academic year {me.academic_year}
                </span>
              ) : null}
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm shrink-0">
            <span className="text-ink-soft hidden md:inline truncate max-w-[180px]">
              {me?.user.full_name}
            </span>
            <button
              onClick={logout}
              className="text-primary hover:underline font-medium cursor-pointer"
            >
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
