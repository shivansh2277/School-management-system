import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { AdmissionEnquiryModal } from "./AdmissionEnquiryModal";

export const OPEN_ADMISSION_ENQUIRY_EVENT = "open-admission-enquiry";

/**
 * Programmatically open the global Admission Enquiry modal from anywhere in the application.
 */
export function openAdmissionEnquiry() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(OPEN_ADMISSION_ENQUIRY_EVENT));
  }
}

/**
 * Persistent Admission Enquiry side CTA visible across public informational pages.
 * - Desktop: Subtle, premium vertical tab flush against the right edge.
 * - Mobile: Compact, non-intrusive floating action pill at bottom-right.
 * - Strictly excluded from `/apply` and `/login` routes.
 */
export function AdmissionSideCTA() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener(OPEN_ADMISSION_ENQUIRY_EVENT, handleOpen);
    return () => window.removeEventListener(OPEN_ADMISSION_ENQUIRY_EVENT, handleOpen);
  }, []);

  // Strictly excluded from the admission application flow (/apply) and login (/login)
  if (location.pathname.startsWith("/apply") || location.pathname.startsWith("/login")) {
    return null;
  }

  return (
    <>
      {/* ============================================================== */}
      {/* 1. DESKTOP / TABLET PERSISTENT SIDE TAB (>= 640px)             */}
      {/* ============================================================== */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="hidden sm:flex fixed right-0 top-1/2 -translate-y-1/2 z-40 flex-col items-center gap-2 bg-slate-900/95 hover:bg-slate-900 text-white pl-2.5 pr-2 py-4 rounded-l-xl shadow-2xl border-y border-l-2 border-amber-400/80 hover:border-amber-400 group transition-all duration-200 hover:-translate-x-1 cursor-pointer select-none backdrop-blur-xs focus:outline-none focus:ring-2 focus:ring-amber-400"
        aria-label="Admission Enquiry"
        title="Admission Enquiry 2026–27"
        data-testid="admission-side-cta-desktop"
      >
        {/* Glow / Icon */}
        <div className="w-7 h-7 rounded-full bg-amber-400/20 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.2}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
        </div>

        {/* Vertical Text */}
        <span
          style={{ writingMode: "vertical-rl" }}
          className="rotate-180 text-[11px] font-bold tracking-widest text-amber-300 uppercase font-sans py-1 leading-none"
        >
          Admission Enquiry
        </span>

        {/* Session Badge */}
        <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-amber-400 text-slate-950 uppercase tracking-tight shadow-xs">
          26–27
        </span>
      </button>

      {/* ============================================================== */}
      {/* 2. MOBILE COMPACT FLOATING CTA (< 640px)                       */}
      {/* ============================================================== */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="sm:hidden fixed bottom-5 right-4 z-50 inline-flex items-center gap-2 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 text-slate-950 font-bold text-xs px-3.5 py-2.5 rounded-full shadow-xl border border-amber-300 active:scale-95 transition-all select-none focus:outline-none focus:ring-2 focus:ring-amber-500"
        aria-label="Admission Enquiry"
        data-testid="admission-side-cta-mobile"
      >
        <div className="w-4 h-4 rounded-full bg-slate-950/15 flex items-center justify-center">
          <svg className="w-2.5 h-2.5 text-slate-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
        </div>
        <span>Admission Enquiry</span>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
      </button>

      {/* ============================================================== */}
      {/* 3. UNIFIED ADMISSION ENQUIRY MODAL                             */}
      {/* ============================================================== */}
      <AdmissionEnquiryModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
