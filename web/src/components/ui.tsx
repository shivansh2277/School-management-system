import { useState, type ReactNode } from "react";

import { ApiError, errorText } from "../api/errors";
import { statusColor, theme } from "../theme";

export function Card({
  title,
  children,
  action,
  className,
}: {
  title?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`bg-surface rounded-card shadow-card p-5 border border-rule/80 ${className || ""}`}>
      {(title || action) && (
        <header className="flex items-center justify-between mb-4 pb-2.5 border-b border-rule/60">
          {title && <h2 className="font-bold text-ink text-base tracking-tight">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function StatCard({
  label,
  value,
  hint,
  className,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  className?: string;
  icon?: ReactNode;
}) {
  return (
    <div className={`bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col justify-between ${className || ""}`}>
      <div>
        {icon && <div className="mb-2.5">{icon}</div>}
        <p className="text-xs font-semibold text-ink-soft">{label}</p>
        <p className="text-2xl font-bold tracking-tight text-ink mt-1 tabular">{value}</p>
      </div>
      {hint && <p className="text-xs text-ink-faint mt-1.5">{hint}</p>}
    </div>
  );
}

export function Pill({ status, children, className }: { status?: string; children: ReactNode; className?: string }) {
  const normalized = status?.toLowerCase() || "";
  let badgeColor = status ? statusColor[normalized] || statusColor[status] : undefined;

  // Semantic fallbacks for common statuses
  if (!badgeColor) {
    if (["active", "approved", "completed", "success"].includes(normalized)) badgeColor = theme.success;
    else if (["rejected", "cancelled", "failed", "void"].includes(normalized)) badgeColor = theme.danger;
    else if (["in_progress", "submitted", "review", "open"].includes(normalized)) badgeColor = theme.info;
    else if (["draft", "neutral"].includes(normalized)) badgeColor = theme.inkSoft;
  }

  const color = badgeColor || theme.inkSoft;
  return (
    <span
      className={`inline-flex items-center rounded-pill px-2.5 py-0.5 text-xs font-semibold border ${className || ""}`}
      style={{
        color,
        backgroundColor: `${color}14`,
        borderColor: `${color}28`,
      }}
    >
      {children}
    </span>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="py-8 px-4 text-center">
      <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-2.5">
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
      <p className="text-sm text-ink-faint max-w-sm mx-auto">{children}</p>
    </div>
  );
}

/**
 * A distinct message for a query that failed, so a 403/404/500 never reads
 * as "we checked and there is genuinely nothing here" - which for a fee
 * structure or an invoice list is a false statement about the school's
 * money, not a cosmetic gap.
 */
export function ErrorState({ error }: { error: unknown }) {
  let message = "Could not load this. Try again.";
  if (error instanceof ApiError) {
    if (error.status === 403) message = "Refused: your role does not have permission to view this.";
    else if (error.status === 404) message = "Not available for this school.";
  }
  return <p className="text-sm text-danger py-6 text-center font-medium">{message}</p>;
}

export function DataTable<T>({
  columns,
  rows,
  onRowClick,
  empty,
  loading = false,
  error,
}: {
  columns: { key: string; header: string; render: (row: T) => ReactNode; align?: "right" }[];
  rows: T[];
  onRowClick?: (row: T) => void;
  empty: string;
  /** While fetching, an empty table means "not known yet", not "none exist". */
  loading?: boolean;
  /** The query's error, if any. Takes priority over the empty state. */
  error?: unknown;
}) {
  if (loading && rows.length === 0) return <Empty>Loading...</Empty>;
  if (error && rows.length === 0) return <ErrorState error={error} />;
  if (rows.length === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="overflow-x-auto rounded-lg border border-rule/80">
      <table className="w-full text-sm">
        <thead className="bg-slate-50/75 border-b border-rule">
          <tr className="text-left text-xs uppercase tracking-wider text-ink-soft font-semibold">
            {columns.map((c) => (
              <th key={c.key} className={`py-2.5 px-3.5 font-semibold ${c.align === "right" ? "text-right" : ""}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-rule/60 bg-surface">
          {rows.map((row, i) => (
            <tr
              key={i}
              onClick={() => onRowClick?.(row)}
              className={`transition-colors ${onRowClick ? "cursor-pointer hover:bg-slate-50" : "hover:bg-slate-50/50"}`}
            >
              {columns.map((c) => (
                <td key={c.key} className={`py-3 px-3.5 ${c.align === "right" ? "text-right tabular" : ""}`}>
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Modal({
  title,
  onClose,
  wide = false,
  children,
}: {
  title: string;
  onClose: () => void;
  /** A map needs room a form does not. Default is unchanged for every caller. */
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-ink/40 grid place-items-center p-2 sm:p-4" onClick={onClose}>
      <div
        className={`bg-surface rounded-card shadow-card w-full ${
          wide ? "max-w-4xl" : "max-w-lg"
        } p-4 sm:p-6 max-h-[92vh] sm:max-h-[85vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-base sm:text-lg text-ink">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1.5 rounded-full transition-colors flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-red-400"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

export function FormField({
  label,
  error,
  children,
}: {
  label: string;
  /** The backend's own message for this field, from `ApiError.fields`. */
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="text-ink-soft">{label}</span>
      <div className="mt-1">{children}</div>
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </label>
  );
}

/**
 * What is left of a failure after the per-field messages are shown.
 *
 * A 422 carries `ApiError.fields`, and those belong next to their inputs where
 * the person can act on them - pass each to that FormField's `error`. This
 * renders the rest: a 500, a 409, a business rule that names no field. It
 * returns null only when there is genuinely nothing left to say, because a
 * write that failed silently is how a clerk concludes the money went through.
 */
export function FormError({ error }: { error: unknown }) {
  if (!error) return null;
  if (error instanceof ApiError && Object.keys(error.fields).length > 0) {
    // Every message is already pinned to an input; repeating them here would
    // just be the same sentence twice.
    return null;
  }
  return <p className="text-sm text-danger">{errorText(error)}</p>;
}

/**
 * Confirmation for anything destructive, with the reason the audit log needs.
 *
 * `services/audit.py` refuses to commit a void, a status change or a delete
 * without one, so the reason is not decoration - a dialog that returns an empty
 * string produces a 422 the clerk cannot interpret. It is sent as the person
 * typed it; a hardcoded string in the client would make the whole audit trail
 * a record of the UI's opinion rather than theirs.
 */
export function ConfirmDialog({
  title,
  intent,
  confirmLabel = "Confirm",
  busy,
  error,
  onConfirm,
  onClose,
}: {
  title: string;
  /** What is about to happen, in the clerk's terms. */
  intent: ReactNode;
  confirmLabel?: string;
  busy?: boolean;
  error?: unknown;
  onConfirm: (reason: string) => void;
  onClose: () => void;
}) {
  const [reason, setReason] = useState("");
  const ready = reason.trim().length > 0;

  return (
    <Modal title={title} onClose={onClose}>
      <div className="space-y-3">
        <div className="text-sm text-ink-soft">{intent}</div>
        <FormField label="Reason">
          <textarea
            className={inputClass}
            rows={2}
            value={reason}
            autoFocus
            onChange={(e) => setReason(e.target.value)}
          />
        </FormField>
        <FormError error={error} />
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <button
            onClick={() => ready && onConfirm(reason.trim())}
            disabled={!ready || busy}
            title={ready ? undefined : "A reason is required"}
            className="rounded-input bg-danger px-4 py-2 text-white text-sm font-medium disabled:opacity-60"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </Modal>
  );
}

export const inputClass =
  "w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary";
