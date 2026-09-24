import type { ReactNode } from "react";

import { useAuth } from "./AuthContext";
import { getUserRoles, isScreenAllowed, missingModule, missingPermission, type Screen } from "../screens";

/**
 * The third gate. Hiding a menu item is not access control - typing /payroll in
 * the address bar has to hit the same check the sidebar applied.
 *
 * It renders an in-page refusal rather than redirecting: a redirect on a
 * permission failure reads as a crash to the person it happens to.
 *
 * A screen declares every module and every permission its read path needs, and
 * all of them are required. The refusal names the first one missing, because a
 * message that says only "not allowed" sends the reader to the source anyway.
 */
export function RequirePermission({ screen, children }: { screen: Screen; children: ReactNode }) {
  const { me, can, hasModule } = useAuth();
  const userRoles = getUserRoles(me);

  const offModule = missingModule(screen, hasModule);
  if (offModule !== undefined) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">Not enabled</p>
        <p className="text-sm text-ink-soft mt-1">
          The {offModule} module is not switched on for this school.
        </p>
      </div>
    );
  }

  if (!isScreenAllowed(screen, userRoles)) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">Access Restricted</p>
        <p className="text-sm text-ink-soft mt-1">
          Access to {screen.label} is restricted for your role.
        </p>
      </div>
    );
  }

  const lacking = missingPermission(screen, can);
  if (lacking !== undefined) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">You do not have permission</p>
        <p className="text-sm text-ink-soft mt-1">
          {screen.label} needs <code>{lacking}</code>, which your role does not hold.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
