import { Outlet } from "react-router-dom";
import { PublicNavbar } from "./PublicNavbar";
import { PublicFooter } from "./PublicFooter";

export function PublicLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-ink selection:bg-primary-soft selection:text-primary">
      <PublicNavbar />
      <main className="flex-1">
        {children ? children : <Outlet />}
      </main>
      <PublicFooter />
    </div>
  );
}
