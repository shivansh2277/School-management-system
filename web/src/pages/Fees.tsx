import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api, money } from "../api/client";
import { Card, DataTable, Empty, Pill, StatCard, inputClass } from "../components/ui";
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
    queryFn: () => api.get<Invoice[]>(`/admin/fees/invoices?month=${month}&year=${year}`),
  });
  const collection = useQuery({
    queryKey: ["collection", year],
    queryFn: () => api.get<Collection>(`/admin/fees/collection?year=${year}`),
  });

  const generate = useMutation({
    mutationFn: () =>
      api.post<{ created: number; skipped: number }>("/admin/fees/invoices/generate", {
        month,
        year,
      }),
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
          <button
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="rounded-input bg-primary px-3 py-1.5 text-sm text-white hover:bg-primary-dark disabled:opacity-60"
          >
            Generate invoices
          </button>
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

        <DataTable<Invoice>
          rows={invoices.data ?? []}
          loading={invoices.isLoading}
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
