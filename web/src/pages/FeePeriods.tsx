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

  return (
    <>
      <Card
        title="Period close"
        action={
          <input
            className="w-24 rounded-input border border-rule px-3 py-1.5 text-sm outline-none focus:border-primary"
            value={year}
            inputMode="numeric"
            onChange={(e) => setYear(Number(e.target.value) || year)}
          />
        }
      >
        <p className="text-xs text-ink-faint mb-4">
          Closing a month stops invoices being raised into it, money being dated inside it, and
          its invoices being voided. It does <strong>not</strong> stop the counter taking an old
          due today — that receipt belongs to today and lands in the current month.
        </p>

        <DataTable
          rows={rows}
          loading={periods.isLoading}
          error={periods.error}
          empty="No months to show."
          columns={[
            { key: "month", header: "Month", render: (r) => `${monthName(r.month)} ${r.year}` },
            {
              key: "state",
              header: "Status",
              render: (r) => (
                <Pill status={r.status === "closed" ? "paid" : "pending"}>{r.status}</Pill>
              ),
            },
            { key: "note", header: "Reason on record", render: (r) => r.note ?? "—" },
            {
              key: "act",
              header: "",
              render: (r) => (
                <ActionButton
                  permission="fees.payment.void"
                  variant={r.status === "closed" ? "primary" : "danger"}
                  className="!px-3 !py-1 text-xs"
                  onClick={() => setActing({ row: r, closing: r.status !== "closed" })}
                >
                  {r.status === "closed" ? "Reopen" : "Close"}
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
    </>
  );
}
