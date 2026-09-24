import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { SchoolCrest } from "./SchoolCrest";

const NAV_ITEMS = [
  { label: "Home", path: "/" },
  { label: "About", path: "/about" },
  { label: "Academics", path: "/academics" },
  { label: "Admissions", path: "/admissions" },
  { label: "Facilities", path: "/facilities" },
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
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-rule transition-all shadow-sm">
      {/* Top micro-bar for parent helpline and affiliation notice */}
      <div className="bg-slate-900 text-slate-300 text-xs py-1.5 px-4 hidden sm:block">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Admissions Open for Session 2025–26 (Pre-Primary to XI)</span>
            </span>
            <span className="text-slate-500">•</span>
            <span>CBSE Affiliation No. 2130000 (Demo Institution)</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="tel:+915222990000"
              className="hover:text-white transition-colors flex items-center gap-1"
            >
              <span>Desk:</span> <span className="text-slate-100 font-medium">+91 522 299 0000</span>
            </a>
            <span className="text-slate-500">•</span>
            <Link to="/admissions" className="text-amber-300 hover:text-amber-200 font-medium transition-colors">
              Admission Guidelines &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo & School Identity */}
          <Link
            to="/"
            className="flex items-center gap-3.5 group focus:outline-none"
            onClick={() => setMobileMenuOpen(false)}
          >
            <SchoolCrest className="w-11 h-11 transition-transform group-hover:scale-105 duration-200" />
            <div className="flex flex-col">
              <span className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 leading-none group-hover:text-primary transition-colors">
                Sunrise School
              </span>
              <span className="text-xs text-ink-soft tracking-wider font-medium uppercase mt-1">
                Lucknow • CBSE Affiliated
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 xl:gap-2">
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all duration-150 ${
                    active
                      ? "text-primary bg-primary-soft/70 shadow-xs"
                      : "text-slate-700 hover:text-primary hover:bg-slate-50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Desktop ERP Action */}
          <div className="hidden lg:flex items-center gap-3">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary-dark text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-sm hover:shadow transition-all duration-150 active:scale-95"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                />
              </svg>
              <span>Login to ERP</span>
            </Link>
          </div>

          {/* Mobile Hamburger & ERP Button */}
          <div className="flex items-center gap-2 lg:hidden">
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-xs transition-colors"
            >
              <span>ERP</span>
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>

            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-700 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-rule bg-white shadow-lg animate-fadeIn">
          <div className="px-4 pt-3 pb-6 space-y-1.5">
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-3.5 py-2.5 rounded-lg text-base font-semibold transition-colors ${
                    active
                      ? "text-primary bg-primary-soft font-bold"
                      : "text-slate-700 hover:text-primary hover:bg-slate-50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}

            <div className="pt-4 border-t border-rule mt-3 space-y-2">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-semibold py-3 px-4 rounded-lg shadow-sm"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                  />
                </svg>
                <span>Login to ERP Portal</span>
              </Link>

              <div className="text-xs text-center text-slate-500 pt-2">
                Office Hours: Mon–Sat 8:00 AM – 3:30 PM • Ph: +91 522 299 0000
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
