import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api, money } from "../api/client";
import { ActionButton } from "../components/Can";
import { Card, DataTable, Empty, FormError, Pill, StatCard, inputClass } from "../components/ui";
import { theme } from "../theme";

type Invoice = {
  id: number;
  student_name: string;
  admission_no: string;
  class_label: string;
  month: number;
  year: number;
  amount: string;
  due_date: string;
  status: string;
  receipt_no: string | null;
};

type Collection = {
  year: number;
  billed: string;
  collected: string;
  outstanding: string;
  months: { month: number; billed: string; collected: string }[];
};

const now = new Date();

export function Fees() {
  const qc = useQueryClient();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [note, setNote] = useState<string | null>(null);

  const invoices = useQuery({
    queryKey: ["invoices", month, year],
    // /admin/fees/invoices has no response_model; Invoice documents the shape.
    queryFn: () =>
      api.get("/admin/fees/invoices", `?month=${month}&year=${year}`) as Promise<Invoice[]>,
  });
  const collection = useQuery({
    queryKey: ["collection", year],
    // /admin/fees/collection has no response_model; Collection documents it.
    queryFn: () => api.get("/admin/fees/collection", `?year=${year}`) as Promise<Collection>,
  });

  const generate = useMutation({
    mutationFn: () =>
      api.post("/admin/fees/invoices/generate", { month, year }) as Promise<{
        created: number;
        skipped: number;
      }>,
    onSuccess: (r) => {
      setNote(`${r.created} invoice(s) created, ${r.skipped} already existed.`);
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["collection"] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header Surface Card */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Fee Billing & Invoicing</h1>
        </div>
        <div className="flex items-center gap-2">
          <ActionButton
            permission="fees.invoice.generate"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="!px-3.5 !py-2 text-xs font-semibold shadow-2xs"
          >
            {generate.isPending ? "Generating..." : "Generate Invoices"}
          </ActionButton>
        </div>
      </div>

      {/* Collection Metric Cards */}
      {collection.data && (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Annual Billed"
            value={money(collection.data.billed)}
            hint={`Session ${collection.data.year}`}
          />
          <StatCard
            label="Total Collected"
            value={money(collection.data.collected)}
            hint={
              Number(collection.data.billed) > 0
                ? `${((Number(collection.data.collected) / Number(collection.data.billed)) * 100).toFixed(1)}% recovery rate`
                : undefined
            }
          />
          <StatCard
            label="Outstanding Balance"
            value={money(collection.data.outstanding)}
            hint="Pending payment dues"
          />
        </div>
      )}

      {/* Invoices Register Card */}
      <Card
        title={`Invoices for ${new Date(2000, month - 1).toLocaleString("en", { month: "long" })} ${year}`}
        action={
          invoices.data && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              {invoices.data.length} invoices
            </span>
          )
        }
      >
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-slate-50/70 rounded-lg border border-slate-200/60">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-soft uppercase tracking-wider">Month:</span>
            <select
              className={`${inputClass} !py-1.5 !text-xs sm:w-44`}
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1).toLocaleString("en", { month: "long" })}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-soft uppercase tracking-wider">Year:</span>
            <input
              className={`${inputClass} !py-1.5 !text-xs w-24`}
              value={year}
              inputMode="numeric"
              onChange={(e) => setYear(Number(e.target.value) || year)}
            />
          </div>
        </div>

        {note && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-medium flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
            <span>{note}</span>
          </div>
        )}

        <div className="mb-3">
          <FormError error={generate.error} />
        </div>

        <DataTable
          rows={invoices.data ?? []}
          loading={invoices.isLoading}
          error={invoices.error}
          empty="No invoices for this month yet. Use Generate invoices."
          columns={[
            {
              key: "name",
              header: "Student",
              render: (i) => <span className="font-semibold text-ink">{i.student_name}</span>,
            },
            {
              key: "adm",
              header: "Admission No.",
              render: (i) => (
                <span className="font-mono text-xs text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200/60">
                  {i.admission_no}
                </span>
              ),
            },
            {
              key: "class",
              header: "Class",
              render: (i) => (
                <span className="text-xs font-medium text-slate-700 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/50">
                  {i.class_label}
                </span>
              ),
            },
            {
              key: "amt",
              header: "Amount",
              render: (i) => <span className="font-semibold font-mono text-ink">{money(i.amount)}</span>,
              align: "right",
            },
            { key: "due", header: "Due Date", render: (i) => <span className="text-xs text-ink-soft">{i.due_date}</span> },
            {
              key: "status",
              header: "Status",
              render: (i) => <Pill status={i.status}>{i.status}</Pill>,
            },
            {
              key: "rcp",
              header: "Receipt No.",
              render: (i) =>
                i.receipt_no ? (
                  <span className="font-mono text-xs text-slate-700">{i.receipt_no}</span>
                ) : (
                  <span className="text-ink-faint text-xs">—</span>
                ),
            },
          ]}
        />
      </Card>

      {/* Annual Monthly Collection Chart */}
      {collection.data && (
        <Card title={`Monthly collection ${collection.data.year}`}>
          {collection.data.months.length === 0 ? (
            <Empty>No invoices raised in this year.</Empty>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={collection.data.months.map((m) => ({
                  month: new Date(2000, m.month - 1).toLocaleString("en", { month: "short" }),
                  collected: Number(m.collected),
                  billed: Number(m.billed),
                }))}
              >
                <CartesianGrid stroke={theme.rule} vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} width={70} />
                <Tooltip formatter={(v: number) => money(v)} />
                <Bar dataKey="billed" name="Billed" fill={theme.rule} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                <Bar dataKey="collected" name="Collected" fill={theme.primary} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      )}
    </div>
  );
}
