import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../../components/ui";
import {
  FeeReceiptData,
  PrintableFeeReceiptSlip,
} from "../../components/reception/PrintableFeeReceiptSlip";

interface InvoiceLineSummary {
  description: string;
  amount: string;
  discount: string;
  net: string;
}

interface OutstandingInvoiceSummary {
  id: number;
  invoice_no: string;
  month: number;
  year: number;
  due_date: string;
  amount: string;
  discount: string;
  payable: string;
  paid: string;
  balance: string;
  lines: InvoiceLineSummary[];
}

interface MonthOption {
  months_count: number;
  label: string;
  total_amount: string;
  invoices_covered: string[];
}

interface FeeCounterStatus {
  student: {
    id: number;
    enrolment_id: number;
    admission_no: string;
    name: string;
    phone?: string | null;
    email?: string | null;
    class_label: string;
    roll_number?: number | null;
  };
  outstanding_invoices: OutstandingInvoiceSummary[];
  available_month_options: MonthOption[];
  total_outstanding: string;
}

export function ReceptionFeeCounterPage() {
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [activeSearchStudent, setActiveSearchStudent] = useState<string>("");

  const [selectedMonthsCount, setSelectedMonthsCount] = useState<number>(1);
  const [paymentMethod, setPaymentMethod] = useState<string>("cash");
  const [counterNotes, setCounterNotes] = useState<string>("");

  const [activeReceipt, setActiveReceipt] = useState<FeeReceiptData | null>(null);

  // Search query
  const feeStatusQuery = useQuery({
    queryKey: ["reception-fee-status", activeSearchStudent],
    queryFn: () => {
      return api.get(
        `/admin/reception/fees/status?q=${encodeURIComponent(activeSearchStudent)}` as any,
      ) as Promise<FeeCounterStatus>;
    },
    enabled: activeSearchStudent.trim().length > 0,
  });

  // Collection mutation
  const collectFeeMutation = useMutation({
    mutationFn: (data: {
      enrolment_id: number;
      num_months: number;
      payment_method: string;
      notes?: string;
    }) => {
      return api.post("/admin/reception/fees/collect" as any, data);
    },
    onSuccess: (receiptRes: any) => {
      queryClient.invalidateQueries({ queryKey: ["reception-fee-status"] });
      // Launch receipt print modal immediately
      setActiveReceipt(receiptRes);
    },
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setActiveSearchStudent(searchQuery.trim());
      setSelectedMonthsCount(1);
    }
  };

  const statusData = feeStatusQuery.data;
  const currentOption = statusData?.available_month_options.find(
    (o) => o.months_count === selectedMonthsCount,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Front Desk Fee Counter</h1>
          <p className="text-sm text-ink-faint">
            Collect complete-month student fees, enforce strict FIFO invoice settlement, and generate official receipts.
          </p>
        </div>
      </div>

      {/* Student Lookup Form */}
      <Card>
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 items-end">
          <div className="flex-1">
            <FormField label="Search Enrolled Student (Admission Number or Name)">
              <input
                type="text"
                required
                placeholder="e.g. 2024000001, Aarav, Ananya..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={inputClass}
              />
            </FormField>
          </div>
          <button
            type="submit"
            disabled={feeStatusQuery.isFetching}
            className="px-6 py-2.5 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm whitespace-nowrap"
          >
            {feeStatusQuery.isFetching ? "Searching..." : "Lookup Student"}
          </button>
        </form>

        {feeStatusQuery.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800">
            Student fee ledger not found or student has no active enrollment. Please check the admission number.
          </div>
        )}
      </Card>

      {/* Student Fee Ledger & Complete-Month Collection Counter */}
      {statusData && (
        <div className="space-y-6">
          {/* Student Profile & Outstanding Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 bg-surface rounded-card shadow-card p-5 border-l-4 border-primary">
              <span className="text-[10px] font-bold text-primary uppercase tracking-wider block mb-1">
                Active Enrolment Details
              </span>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h2 className="text-xl font-bold text-ink">{statusData.student.name}</h2>
                  <p className="text-xs text-ink-faint">
                    Admission No: <span className="font-mono font-semibold text-ink">{statusData.student.admission_no}</span>
                    {statusData.student.class_label && ` • ${statusData.student.class_label}`}
                    {statusData.student.roll_number && ` • Roll No: ${statusData.student.roll_number}`}
                  </p>
                </div>
                {statusData.student.phone && (
                  <span className="text-xs font-mono bg-ground px-2.5 py-1 rounded border border-rule text-ink">
                    📞 {statusData.student.phone}
                  </span>
                )}
              </div>
            </div>

            <StatCard
              label="Total Outstanding Dues"
              value={`₹${parseFloat(statusData.total_outstanding).toLocaleString("en-IN", {
                minimumFractionDigits: 2,
              })}`}
              hint={`${statusData.outstanding_invoices.length} unpaid / overdue invoices`}
            />
          </div>

          {/* Chronological Outstanding Invoices Table */}
          <Card title="Outstanding Invoices (Strict Chronological FIFO Order)">
            {statusData.outstanding_invoices.length === 0 ? (
              <div className="p-8 text-center">
                <span className="text-4xl block mb-2">🎉</span>
                <p className="text-base font-semibold text-emerald-800">No Outstanding Dues</p>
                <p className="text-xs text-ink-faint mt-1">
                  All fee invoices for this student have been cleared in full.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-ink-faint border-b border-rule pb-2">
                      <th className="py-2 pr-4 font-semibold">Priority</th>
                      <th className="py-2 pr-4 font-semibold">Invoice No</th>
                      <th className="py-2 pr-4 font-semibold">Billing Period</th>
                      <th className="py-2 pr-4 font-semibold">Due Date</th>
                      <th className="py-2 pr-4 font-semibold text-right">Net Billed</th>
                      <th className="py-2 pr-4 font-semibold text-right">Already Paid</th>
                      <th className="py-2 pr-4 font-semibold text-right">Due Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statusData.outstanding_invoices.map((inv, idx) => (
                      <tr
                        key={inv.id}
                        className={`border-b border-rule last:border-0 ${
                          idx < selectedMonthsCount ? "bg-primary/5 font-medium" : ""
                        }`}
                      >
                        <td className="py-2.5 pr-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                              idx < selectedMonthsCount
                                ? "bg-primary text-white"
                                : "bg-ground text-ink-faint"
                            }`}
                          >
                            #{idx + 1}
                          </span>
                        </td>
                        <td className="py-2.5 pr-4 font-mono font-bold text-ink">{inv.invoice_no}</td>
                        <td className="py-2.5 pr-4">
                          {inv.month.toString().padStart(2, "0")}/{inv.year}
                        </td>
                        <td className="py-2.5 pr-4 text-ink-faint">{inv.due_date}</td>
                        <td className="py-2.5 pr-4 text-right tabular">₹{parseFloat(inv.payable).toFixed(2)}</td>
                        <td className="py-2.5 pr-4 text-right tabular text-ink-faint">
                          ₹{parseFloat(inv.paid).toFixed(2)}
                        </td>
                        <td className="py-2.5 pr-4 text-right tabular font-bold text-red-900">
                          ₹{parseFloat(inv.balance).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* Collection Console: Enforces Complete Months Selection */}
          {statusData.outstanding_invoices.length > 0 && (
            <Card title="Fee Collection & Receipt Issuance">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  collectFeeMutation.mutate({
                    enrolment_id: statusData.student.enrolment_id,
                    num_months: selectedMonthsCount,
                    payment_method: paymentMethod,
                    notes: counterNotes,
                  });
                }}
                className="space-y-5"
              >
                {/* Notice on Financial Invariants */}
                <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 space-y-1">
                  <p className="font-bold uppercase tracking-wider text-[10px]">
                    Operational Rule: Complete-Month Collection Invariant
                  </p>
                  <p>
                    Receptionist can only collect complete outstanding months ($1, 2, \dots, N$). Arbitrary or partial month
                    amounts are strictly forbidden. System automatically allocates funds starting from the oldest invoice
                    downwards in strict FIFO order.
                  </p>
                </div>

                {/* Step 1: Select Number of Complete Months */}
                <div>
                  <label className="text-xs font-bold text-ink uppercase tracking-wider block mb-2">
                    1. Select Number of Complete Months to Collect:
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
                    {statusData.available_month_options.map((opt) => (
                      <button
                        key={opt.months_count}
                        type="button"
                        onClick={() => setSelectedMonthsCount(opt.months_count)}
                        className={`p-3 rounded-card text-left border transition flex flex-col justify-between ${
                          selectedMonthsCount === opt.months_count
                            ? "border-primary bg-primary/10 shadow-xs ring-2 ring-primary/30"
                            : "border-rule bg-surface hover:bg-ground"
                        }`}
                      >
                        <span className="text-xs font-bold text-ink">
                          {opt.months_count} Month{opt.months_count > 1 ? "s" : ""}
                        </span>
                        <span className="text-[10px] text-ink-faint mt-1 block truncate">
                          {opt.invoices_covered.join(", ")}
                        </span>
                        <span className="text-sm font-black font-mono text-primary mt-2">
                          ₹{parseFloat(opt.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 2: Auto-calculated Amount & Payment Details */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 bg-ground/60 border border-rule rounded-card">
                  <div>
                    <span className="text-xs text-ink-faint block uppercase font-medium">Exact Computed Total:</span>
                    <span className="text-2xl font-black font-mono text-emerald-900 block mt-1">
                      ₹
                      {currentOption
                        ? parseFloat(currentOption.total_amount).toLocaleString("en-IN", {
                            minimumFractionDigits: 2,
                          })
                        : "0.00"}
                    </span>
                    <span className="text-[10px] text-ink-faint">
                      Auto-locked to {selectedMonthsCount} complete invoice(s)
                    </span>
                  </div>

                  <FormField label="Payment Method">
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className={inputClass}
                    >
                      <option value="cash">Cash (Counter)</option>
                      <option value="upi">UPI / QR Code</option>
                      <option value="card">Debit / Credit Card (POS)</option>
                      <option value="bank_transfer">Cheque / Demand Draft</option>
                    </select>
                  </FormField>

                  <FormField label="Counter Collection Notes / Reference">
                    <input
                      type="text"
                      placeholder="e.g. Paid by father at front desk, POS slip #8912"
                      value={counterNotes}
                      onChange={(e) => setCounterNotes(e.target.value)}
                      className={inputClass}
                    />
                  </FormField>
                </div>

                {/* Step 3: Action */}
                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={collectFeeMutation.isPending || !currentOption}
                    className="px-6 py-3 bg-emerald-700 text-white text-sm font-bold rounded-pill hover:bg-emerald-800 transition shadow-md flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {collectFeeMutation.isPending
                      ? "Recording Collection..."
                      : `Collect ₹${currentOption?.total_amount} & Issue Receipt`}
                  </button>
                </div>
              </form>
            </Card>
          )}
        </div>
      )}

      {/* Printable Fee Receipt Modal */}
      {activeReceipt && (
        <PrintableFeeReceiptSlip receipt={activeReceipt} onClose={() => setActiveReceipt(null)} />
      )}
    </div>
  );
}
