import { useState, type ReactNode } from "react";

import { ApiError, errorText } from "../api/errors";
import { statusColor, theme } from "../theme";

export function Card({ title, children, action }: { title?: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="bg-surface rounded-card shadow-card p-5">
      {(title || action) && (
        <header className="flex items-center justify-between mb-4">
          {title && <h2 className="font-semibold">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="bg-surface rounded-card shadow-card p-5">
      <p className="text-sm text-ink-faint">{label}</p>
      <p className="text-2xl font-semibold mt-1 tabular">{value}</p>
      {hint && <p className="text-xs text-ink-faint mt-1">{hint}</p>}
    </div>
  );
}

export function Pill({ status, children }: { status?: string; children: ReactNode }) {
  const color = status ? statusColor[status] : theme.inkSoft;
  return (
    <span
      className="inline-block rounded-pill px-2.5 py-0.5 text-xs font-medium"
      style={{ color, backgroundColor: `${color}1A` }}
    >
      {children}
    </span>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-ink-faint py-6 text-center">{children}</p>;
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
  return <p className="text-sm text-danger py-6 text-center">{message}</p>;
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
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-ink-faint border-b border-rule">
            {columns.map((c) => (
              <th key={c.key} className={`py-2 pr-4 font-medium ${c.align === "right" ? "text-right" : ""}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-rule last:border-0 ${onRowClick ? "cursor-pointer hover:bg-ground" : ""}`}
            >
              {columns.map((c) => (
                <td key={c.key} className={`py-2.5 pr-4 ${c.align === "right" ? "text-right tabular" : ""}`}>
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
    <div className="fixed inset-0 z-50 bg-ink/40 grid place-items-center p-4" onClick={onClose}>
      <div
        className={`bg-surface rounded-card shadow-card w-full ${
          wide ? "max-w-4xl" : "max-w-lg"
        } p-6 max-h-[85vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg text-ink">{title}</h2>
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
