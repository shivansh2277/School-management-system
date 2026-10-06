/**
 * A student's fee account, read-only.
 *
 * Find a child, see what they owe and what they have paid. **Money is not
 * taken here.** Collection happens in the mobile app, at the counter, in the
 * hands of whoever is facing the parent — this screen is the office's view of
 * the same ledger, not a second till.
 *
 * It used to carry a payment form. That was built to the brief
 * (FRONTEND-HANDOFF Packet 2, "collect payment ... take amount") and removed
 * on the owner's decision once collection moved to the app. The backend route
 * is untouched and still live: `POST /admin/fees/payments` is what the app
 * calls. Nothing about the money rules changed, only who has the till.
 *
 * What is still here, and why:
 *
 *  - **Reversing a payment.** A correction, not a collection. The API refuses
 *    a reversal by whoever took the money, so it has to be done by someone
 *    else — which on a phone-collected payment means the office. Writes a
 *    contra entry; the original receipt stays.
 *  - **The balance is never cached.** Every figure comes from the ledger query
 *    and is refetched after a write, so this screen cannot start disagreeing
 *    with the app.
 *  - **Amounts stay strings end to end.** `Numeric` is serialised as a string
 *    on purpose; nothing here calls Number() on money.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../api/client";
import { useWrite } from "../api/useWrite";
import { ActionButton } from "../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  FormError,
  FormField,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";


/** /admin/students has no response_model; this documents the roster row. */
type StudentRow = {
  id: number;
  full_name: string;
  admission_no: string;
  class_label: string | null;
  guardian_phone: string | null;
};
type Page = { items: StudentRow[]; total: number };

/**
 * /admin/fees/ledger/{id} has no `response_model`, so the generated schema
 * types it `unknown` and these hand-written shapes are unchecked. Every field
 * below was read off `services/fees.py::invoice_out` and `totals` rather than
 * guessed: an earlier draft of this type said `total`, which does not exist,
 * and the column rendered "₹NaN" on a live fee screen with tsc perfectly green.
 * Change nothing here without reading those two functions.
 */
type LedgerInvoice = {
  id: number;
  invoice_no: string;
  enrolment_id: number;
  month: number;
  year: number;
  due_date: string;
  status: string;
  /** Gross, before concessions. */
  charged: string;
  discount: string;
  /** What is actually owed: charged - discount. */
  payable: string;
  paid: string;
  balance: string;
};
type LedgerPayment = {
  id: number;
  receipt_no: string;
  amount: string;
  method: string;
  received_at: string;
  status: string;
  reverses_payment_id: number | null;
};
type Ledger = {
  student_id: number;
  invoices: LedgerInvoice[];
  payments: LedgerPayment[];
  outstanding: string;
  credit: string;
};

/** dd/mm/yyyy, the way the office writes a date. */
const asDate = (iso: string) => new Date(iso).toLocaleDateString("en-GB");

const monthName = (m: number) => new Date(2000, m - 1).toLocaleString("en", { month: "short" });

export function FeeLedger() {
  const [term, setTerm] = useState("");
  const [searched, setSearched] = useState("");
  const [student, setStudent] = useState<StudentRow | null>(null);

  const results = useQuery({
    queryKey: ["student-search", searched],
    queryFn: () =>
      api.get("/admin/students", `?q=${encodeURIComponent(searched)}&page_size=10`) as Promise<Page>,
    enabled: searched.length > 0,
  });

  const ledger = useQuery({
    queryKey: ["ledger", student?.id],
    queryFn: () =>
      api.get(
        `/admin/fees/ledger/${student!.id}` as "/admin/fees/ledger/{student_id}",
      ) as Promise<Ledger>,
    enabled: student !== null,
  });

  const pick = (row: StudentRow) => {
    setStudent(row);
    setSearched("");
    setTerm("");
  };

  return (
    <div className="space-y-6">
      {/* Header Surface Card */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Student Fee Ledger</h1>
        </div>
      </div>

      <Card title="Find Student Account">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSearched(term.trim());
          }}
        >
          {/*
            The Search button is not decoration. A form with no submit button
            relies on implicit submission, which did not fire on Enter when this
            screen was driven from the keyboard - so the one control a clerk
            with a queue actually uses silently did nothing. An explicit submit
            button makes Enter work as well as the click.
          */}
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <FormField label="Search student by name, admission no., or guardian phone">
                <input
                  className={inputClass}
                  autoFocus
                  value={term}
                  placeholder="e.g. Aarav Sharma, ADM-2024-001, 9876543210..."
                  onChange={(e) => setTerm(e.target.value)}
                />
              </FormField>
            </div>
            <button
              type="submit"
              className="rounded-input bg-primary px-4 py-2 text-white text-sm font-semibold hover:bg-primary/90 transition-colors shadow-2xs"
            >
              Search
            </button>
          </div>
        </form>

        {searched.length > 0 && (
          <div className="mt-4 pt-4 border-t border-rule/60">
            <DataTable
              rows={results.data?.items ?? []}
              loading={results.isLoading}
              error={results.error}
              empty={`Nobody matches "${searched}". Try the admission number.`}
              onRowClick={pick}
              columns={[
                {
                  key: "name",
                  header: "Student",
                  render: (s) => (
                    <span className="font-semibold text-ink hover:text-primary transition-colors">
                      {s.full_name}
                    </span>
                  ),
                },
                {
                  key: "adm",
                  header: "Admission No.",
                  render: (s) => (
                    <span className="font-mono text-xs text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200/60">
                      {s.admission_no}
                    </span>
                  ),
                },
                {
                  key: "class",
                  header: "Class",
                  render: (s) => (
                    <span className="text-xs font-medium text-slate-700 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/50">
                      {s.class_label ?? "—"}
                    </span>
                  ),
                },
                { key: "ph", header: "Guardian Phone", render: (s) => s.guardian_phone ?? "—" },
              ]}
            />
          </div>
        )}
      </Card>

      {student && (
        <StudentAccount
          student={student}
          ledger={ledger}
          onClear={() => setStudent(null)}
        />
      )}
    </div>
  );
}

function StudentAccount({
  student,
  ledger,
  onClear,
}: {
  student: StudentRow;
  ledger: ReturnType<typeof useQuery<Ledger>>;
  onClear: () => void;
}) {
  const data = ledger.data;

  return (
    <div className="space-y-6">
      <Card
        title={`${student.full_name} — ${student.admission_no}`}
        action={
          <button
            onClick={onClear}
            className="text-xs font-semibold text-primary hover:underline px-2.5 py-1 rounded bg-blue-50 border border-blue-200"
          >
            ← Change student
          </button>
        }
      >
        {ledger.isLoading && <Empty>Loading the account…</Empty>}
        {ledger.error != null && <FormError error={ledger.error} />}
        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-3 mb-5">
              <StatCard label="Outstanding Balance" value={money(data.outstanding)} hint={student.class_label ?? undefined} />
              <StatCard label="Credit on Account" value={money(data.credit)} hint="Advance balance" />
              <StatCard label="Total Receipts" value={data.payments.length} hint="Recorded transactions" />
            </div>

            {data.invoices.length === 0 && (
              <Empty>
                No invoices have been raised for this student yet — generate them on the Fees
                screen.
              </Empty>
            )}
          </>
        )}
      </Card>

      {data && (
        <>
          <Card
            title="Invoices"
            action={
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {data.invoices.length} billed
              </span>
            }
          >
            <DataTable
              rows={data.invoices}
              empty="No invoices raised for this student."
              columns={[
                {
                  key: "no",
                  header: "Invoice No.",
                  render: (i) => <span className="font-mono text-xs font-medium text-slate-800">{i.invoice_no}</span>,
                },
                { key: "period", header: "Period", render: (i) => `${monthName(i.month)} ${i.year}` },
                { key: "due", header: "Due Date", render: (i) => asDate(i.due_date) },
                { key: "billed", header: "Billed", render: (i) => <span className="font-mono">{money(i.payable)}</span>, align: "right" },
                { key: "paid", header: "Paid", render: (i) => <span className="font-mono text-emerald-700 font-medium">{money(i.paid)}</span>, align: "right" },
                { key: "bal", header: "Balance", render: (i) => <span className="font-mono font-semibold text-rose-700">{money(i.balance)}</span>, align: "right" },
                { key: "st", header: "Status", render: (i) => <Pill status={i.status}>{i.status}</Pill> },
              ]}
            />
          </Card>

          <Card
            title="Payment Receipts"
            action={
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {data.payments.length} receipts
              </span>
            }
          >
            <Receipts payments={data.payments} studentId={student.id} />
          </Card>
        </>
      )}
    </div>
  );
}

function Receipts({ payments, studentId }: { payments: LedgerPayment[]; studentId: number }) {
  const [reversing, setReversing] = useState<LedgerPayment | null>(null);

  const reverse = useWrite<string>({
    write: (reason: string) =>
      api.post(
        `/admin/fees/payments/${reversing!.id}/reverse` as "/admin/fees/payments/{payment_id}/reverse",
        { reason },
      ),
    invalidates: [["ledger", studentId], ["invoices"], ["collection"], ["defaulters"]],
    onDone: () => setReversing(null),
  });

  return (
    <>
      <DataTable
        rows={payments}
        empty="No payments taken for this student yet."
        columns={[
          { key: "rcp", header: "Receipt", render: (p) => p.receipt_no },
          { key: "at", header: "Received", render: (p) => asDate(p.received_at) },
          { key: "method", header: "Method", render: (p) => p.method.replace("_", " ") },
          { key: "amt", header: "Amount", render: (p) => money(p.amount), align: "right" },
          {
            key: "st",
            header: "Status",
            render: (p) => (
              <Pill status={p.status}>
                {p.reverses_payment_id ? "reversal" : p.status}
              </Pill>
            ),
          },
          {
            key: "act",
            header: "",
            render: (p) =>
              // Two rows the API will always refuse, so no button is offered:
              // a reversal cannot itself be reversed, and an already-reversed
              // payment 409s. Both guards are in services/fees.py::reverse -
              // this only stops the clerk being handed a control that fails.
              p.reverses_payment_id !== null || p.status === "reversed" ? null : (
                <ActionButton
                  permission="fees.payment.void"
                  variant="danger"
                  className="!px-3 !py-1 text-xs"
                  onClick={() => setReversing(p)}
                >
                  Reverse
                </ActionButton>
              ),
          },
        ]}
      />

      {reversing && (
        <ConfirmDialog
          title={`Reverse receipt ${reversing.receipt_no}`}
          confirmLabel="Reverse payment"
          busy={reverse.busy}
          error={reverse.error}
          intent={
            <>
              <p>
                {money(reversing.amount)} taken on {asDate(reversing.received_at)} will be
                reversed by a contra entry. The original receipt stays on the account — money is
                never edited or deleted.
              </p>
              <p className="mt-2 text-xs text-ink-faint">
                Whoever took the payment cannot be the one to reverse it; the API refuses that.
              </p>
            </>
          }
          onConfirm={(reason) => reverse.run(reason)}
          onClose={() => {
            reverse.reset();
            setReversing(null);
          }}
        />
      )}
    </>
  );
}
