import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { SchoolCrest } from "./SchoolCrest";

export const NAV_ITEMS = [
  { label: "Home", path: "/" },
  { label: "About", path: "/about" },
  { label: "Academics", path: "/academics" },
  { label: "Admissions", path: "/admissions" },
  { label: "Campus & Facilities", path: "/facilities" },
  { label: "School Life", path: "/school-life" },
  { label: "Events", path: "/events" },
  { label: "Public Disclosure", path: "/public-disclosure" },
  { label: "Resources", path: "/resources" },
];

export function PublicNavbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/" || location.pathname === "/home";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 transition-all shadow-xs">
        {/* Main Navbar */}
        <div className="max-w-[1440px] mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20 gap-2">
            {/* Logo & School Identity */}
            <Link
              to="/"
              className="flex items-center gap-2 sm:gap-3 group focus:outline-none min-w-0 shrink"
              onClick={() => setMobileMenuOpen(false)}
            >
              <SchoolCrest className="w-9 h-9 sm:w-10 sm:h-10 xl:w-11 xl:h-11 transition-transform group-hover:scale-105 duration-200 shrink-0" />
              <div className="flex flex-col min-w-0">
                <span className="text-base sm:text-xl xl:text-2xl font-bold tracking-tight text-slate-900 leading-none group-hover:text-primary transition-colors font-serif truncate">
                  Sunrise School
                </span>
                <span className="text-[9px] sm:text-[10px] xl:text-[11px] text-slate-500 tracking-wider font-semibold uppercase mt-1 truncate">
                  Gomti Nagar • Lucknow
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links (9 Primary Views) */}
            <nav className="hidden lg:flex items-center gap-0.5 xl:gap-1 2xl:gap-1.5" aria-label="Main navigation">
              {NAV_ITEMS.map((item) => {
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-2 py-1.5 xl:px-2.5 2xl:px-3 rounded-lg text-xs xl:text-[13px] 2xl:text-sm font-semibold transition-all duration-150 whitespace-nowrap ${
                      active
                        ? "text-primary bg-amber-50 font-bold shadow-xs border border-amber-200/50"
                        : "text-slate-700 hover:text-primary hover:bg-slate-50"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Desktop Action: ERP Login CTA */}
            <div className="hidden lg:flex items-center gap-2 xl:gap-3 shrink-0">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white text-xs xl:text-sm font-bold px-3.5 xl:px-4 py-2 rounded-lg shadow-xs hover:shadow transition-all duration-150 active:scale-95"
              >
                <span>ERP Login</span>
                <span className="text-xs font-normal" aria-hidden="true">&rarr;</span>
              </Link>
            </div>

            {/* Mobile Actions: Phone Call + ERP Login + Hamburger */}
            <div className="flex items-center gap-1.5 sm:gap-2 lg:hidden shrink-0">
              <a
                href="tel:+915222990000"
                className="inline-flex items-center justify-center p-1.5 sm:p-2 rounded-lg text-emerald-700 hover:bg-emerald-50 border border-emerald-200 transition-colors shrink-0"
                aria-label="Call Admissions Desk"
                title="Call +91 522 299 0000"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
              </a>

              <Link
                to="/login"
                className="inline-flex items-center gap-1 bg-primary hover:bg-primary-dark text-white text-[11px] sm:text-xs font-bold px-2 sm:px-2.5 py-1.5 rounded-lg shadow-xs transition-colors shrink-0"
              >
                <span>ERP Login</span>
                <span className="text-[10px] sm:text-xs">&rarr;</span>
              </Link>

              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-1.5 sm:p-2 rounded-lg text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-primary shrink-0"
                aria-label="Toggle Navigation Menu"
              >
                {mobileMenuOpen ? (
                  <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-2 shadow-lg animate-fade-in">
            <nav className="flex flex-col space-y-1">
              {NAV_ITEMS.map((item) => {
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors flex items-center justify-between ${
                      active
                        ? "text-primary bg-amber-50 font-bold border border-amber-200/50"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <span>{item.label}</span>
                    {active && <span className="w-1.5 h-1.5 rounded-full bg-primary" />}
                  </Link>
                );
              })}
            </nav>

            <div className="pt-4 border-t border-slate-100 space-y-2">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full inline-flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-bold text-sm px-4 py-2.5 rounded-lg shadow-xs transition-colors"
              >
                <span>ERP Login</span>
                <span>&rarr;</span>
              </Link>

              <Link
                to="/apply"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition-colors"
              >
                <span>Apply Online Portal</span>
              </Link>
            </div>
          </div>
        )}
      </header>
    </>
  );
}
