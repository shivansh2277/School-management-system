import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

export function GlobalAnnouncementStrip() {
  const location = useLocation();
  const [announcements, setAnnouncements] = useState<any[]>([]);

  // Do NOT show announcement strip on application workflow (/apply)
  if (location.pathname.startsWith("/apply")) {
    return null;
  }

  useEffect(() => {
    let isMounted = true;
    const fetchAnnouncements = async () => {
      try {
        const apiHost = window.location.hostname === "localhost" ? "http://localhost:8000" : "";
        const res = await fetch(`${apiHost}/public/sunrise/announcements`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && Array.isArray(data) && data.length > 0) {
            setAnnouncements(data);
          }
        }
      } catch {
        // Fallback demo items if backend unreachable
      }
    };
    fetchAnnouncements();
    return () => {
      isMounted = false;
    };
  }, []);

  const defaultItems = [
    "Admissions Open for Academic Session 2026–27",
    "Annual Sports Meet Registration Open",
    "Science Exhibition & STEM Innovation Showcase on 15 Nov 2025",
  ];

  const displayItems =
    announcements.length > 0
      ? announcements.map((a) => a.title)
      : defaultItems;

  return (
    <div className="bg-slate-900 text-white text-xs py-2.5 px-4 sm:px-6 lg:px-8 border-b border-slate-800 shadow-inner overflow-hidden transition-all">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between gap-3">
        {/* Left Badge & Ticker */}
        <div className="flex items-center gap-3 overflow-hidden min-w-0">
          <div className="flex items-center gap-1.5 shrink-0 bg-amber-500/20 text-amber-300 border border-amber-400/30 px-2.5 py-0.5 rounded-full font-bold text-[11px] tracking-wide">
            <svg className="w-3.5 h-3.5 text-amber-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
            </svg>
            <span>Latest Announcements</span>
          </div>

          <span className="text-slate-600 hidden sm:inline">|</span>

          {/* Ticker Text */}
          <div className="truncate font-medium text-slate-200">
            {displayItems.map((title, i) => (
              <span key={i} className="inline-flex items-center">
                {i > 0 && <span className="mx-3 text-amber-400/80 font-bold">•</span>}
                <Link
                  to="/announcements"
                  className="hover:text-amber-300 hover:underline transition-colors truncate"
                >
                  {title}
                </Link>
              </span>
            ))}
          </div>
        </div>

        {/* Right Action */}
        <Link
          to="/announcements"
          className="shrink-0 flex items-center gap-1 text-amber-400 hover:text-amber-300 font-bold text-[11px] uppercase tracking-wider transition-colors hover:underline"
        >
          <span>View All</span>
          <span className="text-xs">&rarr;</span>
        </Link>
      </div>
    </div>
  );
}
