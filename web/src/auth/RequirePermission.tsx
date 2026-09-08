import type { ReactNode } from "react";

import { useAuth } from "./AuthContext";
import type { Screen } from "../screens";

/**
 * The third gate. Hiding a menu item is not access control - typing /payroll in
 * the address bar has to hit the same check the sidebar applied.
 *
 * It renders an in-page refusal rather than redirecting: a redirect on a
 * permission failure reads as a crash to the person it happens to.
 */
export function RequirePermission({ screen, children }: { screen: Screen; children: ReactNode }) {
  const { can, hasModule } = useAuth();

  if (screen.module !== undefined && !hasModule(screen.module)) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">Not enabled</p>
        <p className="text-sm text-ink-soft mt-1">
          The {screen.module} module is not switched on for this school.
        </p>
      </div>
    );
  }
  if (!can(screen.permission)) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">You do not have permission</p>
        <p className="text-sm text-ink-soft mt-1">
          {screen.label} needs <code>{screen.permission}</code>, which your role does not hold.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
