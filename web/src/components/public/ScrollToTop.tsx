import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * ScrollToTop ensures seamless route transitions on the public website:
 * 1. Automatically resets window scroll to the top (0, 0) upon route changes.
 * 2. Preserves in-page anchor links (e.g. #process, #values) by smoothly
 *    scrolling to the targeted DOM element if present.
 */
export function ScrollToTop() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (typeof window === "undefined") return;

    if (hash) {
      const targetId = hash.replace(/^#/, "");
      if (targetId) {
        const element = document.getElementById(targetId);
        if (element && typeof element.scrollIntoView === "function") {
          try {
            element.scrollIntoView({ behavior: "smooth" });
            return;
          } catch {
            // Environment does not support smooth scrolling
          }
        }
      }
    }

    try {
      if (typeof window.scrollTo === "function") {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      }
    } catch {
      // jsdom environment does not implement window.scrollTo
    }
  }, [pathname, hash]);

  return null;
}
