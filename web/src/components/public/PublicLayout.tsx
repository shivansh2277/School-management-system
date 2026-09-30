import { Outlet } from "react-router-dom";
import { PublicNavbar } from "./PublicNavbar";
import { GlobalAnnouncementStrip } from "./GlobalAnnouncementStrip";
import { PublicFooter } from "./PublicFooter";
import { ScrollToTop } from "./ScrollToTop";
import { AdmissionSideCTA } from "./AdmissionSideCTA";

export function PublicLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-ink selection:bg-primary-soft selection:text-primary">
      <ScrollToTop />
      <PublicNavbar />
      <GlobalAnnouncementStrip />
      <main className="flex-1">
        {children ? children : <Outlet />}
      </main>
      <PublicFooter />
      <AdmissionSideCTA />
    </div>
  );
}
