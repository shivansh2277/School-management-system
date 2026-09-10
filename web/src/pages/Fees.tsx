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
    <>
      <Card
        title="Fees"
        action={
          // fees.invoice.generate, read off api/admin/fees.py - a separate
          // permission from the fees.invoice.read the screen itself needs, so
          // the counter clerk sees this list and cannot raise a month's bills.
          <ActionButton
            permission="fees.invoice.generate"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="!px-3 !py-1.5"
          >
            Generate invoices
          </ActionButton>
        }
      >
        <div className="flex gap-3 mb-4">
          <select
            className={inputClass}
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
          >
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>
                {new Date(2000, m - 1).toLocaleString("en", { month: "long" })}
              </option>
            ))}
          </select>
          <input
            className={inputClass}
            value={year}
            onChange={(e) => setYear(Number(e.target.value) || year)}
          />
        </div>
        {note && <p className="text-sm text-ink-soft mb-3">{note}</p>}
        <div className="mb-3">
          <FormError error={generate.error} />
        </div>

        <DataTable
          rows={invoices.data ?? []}
          loading={invoices.isLoading}
          error={invoices.error}
          empty="No invoices for this month yet. Use Generate invoices."
          columns={[
            { key: "name", header: "Student", render: (i) => i.student_name },
            { key: "adm", header: "Admission No.", render: (i) => i.admission_no },
            { key: "class", header: "Class", render: (i) => i.class_label },
            { key: "amt", header: "Amount", render: (i) => money(i.amount), align: "right" },
            { key: "due", header: "Due", render: (i) => i.due_date },
            {
              key: "status",
              header: "Status",
              render: (i) => <Pill status={i.status}>{i.status}</Pill>,
            },
            { key: "rcp", header: "Receipt", render: (i) => i.receipt_no ?? "-" },
          ]}
        />
      </Card>

      {collection.data && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Billed" value={money(collection.data.billed)} />
            <StatCard label="Collected" value={money(collection.data.collected)} />
            <StatCard label="Outstanding" value={money(collection.data.outstanding)} />
          </div>

          <Card title={`Monthly collection ${collection.data.year}`}>
            {collection.data.months.length === 0 ? (
              <Empty>No invoices raised in this year.</Empty>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
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
                  <Bar dataKey="billed" fill={theme.rule} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  <Bar dataKey="collected" fill={theme.primary} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>
        </>
      )}
    </>
  );
}
