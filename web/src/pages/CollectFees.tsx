/**
 * The counter. Find a child, see what they owe, take the money, hand over a
 * receipt number.
 *
 * This is the screen a clerk has open all morning with a queue in front of
 * them, so it is built around one action and the keyboard: type into the search
 * box that already has focus, Enter to search, Enter again on the amount to
 * take the payment. Nothing on the primary path needs a mouse.
 *
 * Two rules from the money design it would be easy to break here:
 *
 *  - **The balance is never cached.** Every figure on screen comes from the
 *    ledger query and the ledger is refetched after a write. A balance held in
 *    component state and decremented locally is how a counter starts telling
 *    two people different numbers.
 *  - **Amounts stay strings end to end.** `Numeric` is serialised as a string
 *    on purpose; the amount the clerk types goes to the API as typed and comes
 *    back as typed. Nothing here calls Number() on money.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money, newIdempotencyKey } from "../api/client";
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

/** Free text at a counter becomes a reporting problem, so this is a fixed list. */
const METHODS = ["cash", "upi", "cheque", "card", "bank_transfer"];

/** dd/mm/yyyy, the way the office writes a date. */
const asDate = (iso: string) => new Date(iso).toLocaleDateString("en-GB");

const monthName = (m: number) => new Date(2000, m - 1).toLocaleString("en", { month: "short" });

export function CollectFees() {
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
    <>
      <Card title="Collect fees">
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
              <FormField label="Find a student">
                <input
                  className={inputClass}
                  autoFocus
                  value={term}
                  placeholder="Name, admission number or guardian's phone"
                  onChange={(e) => setTerm(e.target.value)}
                />
              </FormField>
            </div>
            <button
              type="submit"
              className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary-dark"
            >
              Search
            </button>
          </div>
        </form>

        {searched.length > 0 && (
          <div className="mt-4">
            <DataTable
              rows={results.data?.items ?? []}
              loading={results.isLoading}
              error={results.error}
              empty={`Nobody matches "${searched}". Try the admission number.`}
              onRowClick={pick}
              columns={[
                { key: "name", header: "Student", render: (s) => s.full_name },
                { key: "adm", header: "Admission No.", render: (s) => s.admission_no },
                { key: "class", header: "Class", render: (s) => s.class_label ?? "—" },
                { key: "ph", header: "Guardian", render: (s) => s.guardian_phone ?? "—" },
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
    </>
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
  // The API takes an enrolment, not a student, and only the invoice rows carry
  // one - see the report's blocked-dependency note. No invoice, no way to post.
  const enrolmentId = data?.invoices[0]?.enrolment_id;

  return (
    <>
      <Card
        title={`${student.full_name} — ${student.admission_no}`}
        action={
          <button onClick={onClear} className="text-sm text-ink-faint hover:text-ink">
            Change student
          </button>
        }
      >
        {ledger.isLoading && <Empty>Loading the account…</Empty>}
        {ledger.error != null && <FormError error={ledger.error} />}
        {data && (
          <>
            <div className="grid gap-4 sm:grid-cols-3 mb-5">
              <StatCard label="Outstanding" value={money(data.outstanding)} hint={student.class_label ?? undefined} />
              <StatCard label="Credit on account" value={money(data.credit)} />
              <StatCard label="Receipts" value={data.payments.length} />
            </div>

            {enrolmentId === undefined ? (
              <Empty>
                No invoices have been raised for this student yet — generate them on the Fees
                screen before taking a payment.
              </Empty>
            ) : (
              <TakePayment
                enrolmentId={enrolmentId}
                studentId={student.id}
                outstanding={data.outstanding}
              />
            )}
          </>
        )}
      </Card>

      {data && (
        <>
          <Card title="Invoices">
            <DataTable
              rows={data.invoices}
              empty="No invoices raised for this student."
              columns={[
                { key: "no", header: "Invoice", render: (i) => i.invoice_no },
                { key: "period", header: "Period", render: (i) => `${monthName(i.month)} ${i.year}` },
                { key: "due", header: "Due", render: (i) => asDate(i.due_date) },
                { key: "billed", header: "Billed", render: (i) => money(i.payable), align: "right" },
                { key: "paid", header: "Paid", render: (i) => money(i.paid), align: "right" },
                { key: "bal", header: "Balance", render: (i) => money(i.balance), align: "right" },
                { key: "st", header: "Status", render: (i) => <Pill status={i.status}>{i.status}</Pill> },
              ]}
            />
          </Card>

          <Card title="Receipts">
            <Receipts payments={data.payments} studentId={student.id} />
          </Card>
        </>
      )}
    </>
  );
}

function TakePayment({
  enrolmentId,
  studentId,
  outstanding,
}: {
  enrolmentId: number;
  studentId: number;
  outstanding: string;
}) {
  const [amount, setAmount] = useState(outstanding);
  const [method, setMethod] = useState("cash");
  const [ref, setRef] = useState("");
  const [receipt, setReceipt] = useState<{ receipt_no: string; amount: string } | null>(null);

  /**
   * One key per logical transaction, not per click.
   *
   * That is the whole mechanism: a double-tap or a retry after a dropped
   * connection returns the original receipt instead of taking the money twice.
   * A fresh key per click would defeat it, so this is regenerated only once the
   * previous payment has actually succeeded.
   */
  const [txKey, setTxKey] = useState(newIdempotencyKey);

  const collect = useWrite<void, { receipt_no: string; amount: string }>({
    write: () =>
      api.post("/admin/fees/payments", {
        enrolment_id: enrolmentId,
        amount,
        method,
        instrument_ref: ref || null,
        idempotency_key: txKey,
      }) as Promise<{ receipt_no: string; amount: string }>,
    invalidates: [["ledger", studentId], ["invoices"], ["collection"], ["defaulters"]],
    onDone: (r) => {
      setReceipt({ receipt_no: r.receipt_no, amount: r.amount });
      setTxKey(newIdempotencyKey());
      setRef("");
      setAmount("0");
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        collect.run();
      }}
      className="space-y-3"
    >
      <div className="grid gap-3 sm:grid-cols-3">
        <FormField label="Amount" error={collect.fields.amount}>
          <input
            className={inputClass}
            value={amount}
            inputMode="decimal"
            onChange={(e) => setAmount(e.target.value)}
          />
        </FormField>
        <FormField label="Method" error={collect.fields.method}>
          <select className={inputClass} value={method} onChange={(e) => setMethod(e.target.value)}>
            {METHODS.map((m) => (
              <option key={m} value={m}>
                {m.replace("_", " ")}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Reference" error={collect.fields.instrument_ref}>
          <input
            className={inputClass}
            value={ref}
            placeholder={method === "cash" ? "not needed for cash" : "cheque or txn number"}
            onChange={(e) => setRef(e.target.value)}
          />
        </FormField>
      </div>

      <FormError error={collect.error} />

      <div className="flex items-center gap-3">
        <ActionButton
          permission="fees.payment.collect"
          onClick={() => collect.run()}
          disabled={collect.busy}
        >
          {collect.busy ? "Taking…" : `Take ${money(amount || "0")}`}
        </ActionButton>
        {receipt && (
          <p className="text-sm text-ink-soft">
            Received {money(receipt.amount)} — receipt <strong>{receipt.receipt_no}</strong>.
          </p>
        )}
      </div>
    </form>
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
