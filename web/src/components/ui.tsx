import type { ReactNode } from "react";

import { ApiError } from "../api/errors";
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
function ErrorState({ error }: { error: unknown }) {
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
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-ink/40 grid place-items-center p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-card shadow-card w-full max-w-lg p-6 max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="text-ink-faint hover:text-ink">
            Close
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

export function FormField({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="text-ink-soft">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

export const inputClass =
  "w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary";
