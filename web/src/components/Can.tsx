/**
 * Permission gating for write controls.
 *
 * The backend already refuses what a caller may not do, so this is not access
 * control - `RequirePermission` and the route guard are. This exists because a
 * UI that renders a button which always 403s is a broken UI: the clerk clicks
 * it, gets a refusal they cannot act on, and reasonably concludes the system is
 * down. Until now no page checked `can()` and every write control rendered for
 * every role.
 *
 * There is no `useCan` hook: `AuthContext` already exposes `can` through
 * `useAuth()`, and a second name for the same function is one more thing to
 * keep in step.
 */
import type { ReactNode } from "react";

import { useAuth } from "../auth/AuthContext";

/**
 * Render children only when the permission is held.
 *
 * Prefer `ActionButton` where the person would otherwise wonder whether the
 * feature exists at all - a disabled control that says why is kinder than a
 * gap. Use `Can` for whole sections that would be meaningless without the
 * permission, and for anything whose mere presence would mislead.
 */
export function Can({
  permission,
  fallback = null,
  children,
}: {
  permission: string;
  fallback?: ReactNode;
  children: ReactNode;
}) {
  const { can } = useAuth();
  return <>{can(permission) ? children : fallback}</>;
}

/**
 * A write control that disables itself, with a reason, when the permission is
 * absent. The reason is in `title` so it survives hover and a screen reader,
 * and the button keeps its place in the layout so the screen does not reflow
 * between roles.
 */
export function ActionButton({
  permission,
  onClick,
  disabled,
  variant = "primary",
  className = "",
  children,
}: {
  /** The permission the write needs. Omit only for a control that writes nothing. */
  permission?: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: "primary" | "danger";
  className?: string;
  children: ReactNode;
}) {
  const { can } = useAuth();
  const allowed = permission === undefined || can(permission);
  const base =
    variant === "danger"
      ? "bg-danger hover:opacity-90"
      : "bg-primary hover:bg-primary-dark";

  return (
    <button
      onClick={onClick}
      disabled={!allowed || disabled}
      aria-disabled={!allowed || disabled}
      title={allowed ? undefined : `Your role does not hold ${permission}`}
      className={`rounded-input px-4 py-2 text-white text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed ${base} ${className}`}
    >
      {children}
    </button>
  );
}
