/**
 * Closing the books on a month.
 *
 * Closing a period forbids three things afterwards: billing into the month,
 * receiving money dated inside it, and voiding one of its invoices. It does
 * NOT stop the counter collecting an old due today - a receipt belongs to the
 * day it was issued, so that money lands in the current period. The screen
 * says so, because a clerk told "the month is closed" reasonably assumes they
 * cannot take the payment in front of them.
 *
 * A month with no row in the database is open. `/admin/fees/periods` only
 * returns months somebody has acted on, so the grid is built from the calendar
 * and the API's rows are laid over it - rather than listing nothing for a year
 * nobody has closed yet, which reads as "no months exist".
 *
 * Both closing and reopening are audited status changes and the backend
 * refuses either without a reason, so both go through ConfirmDialog and send
 * what the user actually typed.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { useWrite } from "../api/useWrite";
import { ActionButton } from "../components/Can";
import { Card, ConfirmDialog, DataTable, Pill } from "../components/ui";

/** /admin/fees/periods has no response_model; read off api/admin/fees.py. */
type Period = {
  year: number;
  month: number;
  status: string;
  closed_at: string | null;
  note: string | null;
};

type Row = { year: number; month: number; status: string; note: string | null };

const monthName = (m: number) => new Date(2000, m - 1).toLocaleString("en", { month: "long" });

export function FeePeriods() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [acting, setActing] = useState<{ row: Row; closing: boolean } | null>(null);

  const periods = useQuery({
    queryKey: ["fee-periods", year],
    queryFn: () => api.get("/admin/fees/periods", `?year=${year}`) as Promise<Period[]>,
  });

  const byMonth = new Map((periods.data ?? []).map((p) => [p.month, p]));
  const rows: Row[] = Array.from({ length: 12 }, (_, i) => {
    const stored = byMonth.get(i + 1);
    return {
      year,
      month: i + 1,
      // No row means nobody has closed this month, which is what "open" is.
      status: stored?.status ?? "open",
      note: stored?.note ?? null,
    };
  });

  const change = useWrite<string>({
    write: (reason: string) =>
      api.post(
        `/admin/fees/periods/${acting!.row.year}/${acting!.row.month}/${
          acting!.closing ? "close" : "reopen"
        }` as "/admin/fees/periods/{year}/{month}/close",
        { reason },
      ),
    invalidates: [["fee-periods"], ["invoices"], ["collection"]],
    onDone: () => setActing(null),
  });

  const closedCount = rows.filter((r) => r.status === "closed").length;
  const openCount = 12 - closedCount;

  return (
    <div className="space-y-6">
      {/* Header Surface Card */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Accounting Period Close</h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-ink-soft uppercase tracking-wider">Financial Year:</span>
          <input
            className="w-24 rounded-input border border-rule px-3 py-1.5 text-xs font-semibold outline-none focus:border-primary shadow-2xs"
            value={year}
            inputMode="numeric"
            onChange={(e) => setYear(Number(e.target.value) || year)}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="bg-surface rounded-card p-4 border border-rule/80 shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Open Billing Months</div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">{openCount}</div>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Accepting Invoices
          </span>
        </div>
        <div className="bg-surface rounded-card p-4 border border-rule/80 shadow-card flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Locked & Closed Months</div>
            <div className="text-2xl font-bold text-slate-700 mt-1">{closedCount}</div>
          </div>
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            Books Finalized
          </span>
        </div>
      </div>

      <Card
        title={`Monthly Books for FY ${year}`}
        action={
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            12 Calendar Periods
          </span>
        }
      >
        <div className="mb-4 p-3 bg-slate-50/80 border border-slate-200/60 rounded-lg text-xs text-ink-soft">
          Closing a month stops invoices being raised into it, money being dated inside it, and
          its invoices being voided. It does <strong>not</strong> stop the counter taking an old
          due today — that receipt belongs to today and lands in the current month.
        </div>

        <DataTable
          rows={rows}
          loading={periods.isLoading}
          error={periods.error}
          empty="No months to show."
          columns={[
            {
              key: "month",
              header: "Month",
              render: (r) => (
                <span className="font-semibold text-ink">
                  {monthName(r.month)} {r.year}
                </span>
              ),
            },
            {
              key: "state",
              header: "Status",
              render: (r) => (
                <Pill status={r.status === "closed" ? "paid" : "pending"}>
                  {r.status}
                </Pill>
              ),
            },
            {
              key: "note",
              header: "Audit Reason on Record",
              render: (r) =>
                r.note ? (
                  <span className="text-xs text-ink-soft italic">“{r.note}”</span>
                ) : (
                  <span className="text-ink-faint text-xs">—</span>
                ),
            },
            {
              key: "act",
              header: "",
              render: (r) => (
                <ActionButton
                  permission="fees.payment.void"
                  variant={r.status === "closed" ? "primary" : "danger"}
                  className="!px-3 !py-1 text-xs font-semibold"
                  onClick={() => setActing({ row: r, closing: r.status !== "closed" })}
                >
                  {r.status === "closed" ? "Reopen Period" : "Close Period"}
                </ActionButton>
              ),
            },
          ]}
        />
      </Card>

      {acting && (
        <ConfirmDialog
          title={`${acting.closing ? "Close" : "Reopen"} ${monthName(acting.row.month)} ${
            acting.row.year
          }`}
          confirmLabel={acting.closing ? "Close the month" : "Reopen the month"}
          busy={change.busy}
          error={change.error}
          intent={
            acting.closing ? (
              <p>
                No further invoices can be raised into {monthName(acting.row.month)}, no money can
                be dated inside it, and none of its invoices can be voided. Collecting an old due
                at the counter still works.
              </p>
            ) : (
              <p>
                {monthName(acting.row.month)} will accept billing and dated money again. Reopening
                is allowed and audited — a system that cannot reopen a month gets the correction
                posted somewhere worse instead.
              </p>
            )
          }
          onConfirm={(reason) => change.run(reason)}
          onClose={() => {
            change.reset();
            setActing(null);
          }}
        />
      )}
    </div>
  );
}
