import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, Empty, Pill, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

const today = () => new Date().toISOString().slice(0, 10);

export function Attendance() {
  const classes = useClasses();
  const [date, setDate] = useState(today());
  const [classId, setClassId] = useState<string>("");

  const activeClass = classId || (classes.data?.[0]?.id?.toString() ?? "");

  const roll = useQuery({
    queryKey: ["admin-roll", activeClass, date],
    queryFn: () =>
      api.get("/admin/attendance", `?class_section_id=${activeClass}&date=${date}`),
    enabled: Boolean(activeClass),
  });

  const summary = useQuery({
    queryKey: ["admin-att-summary", activeClass],
    queryFn: () =>
      api.get("/admin/attendance/summary", `?class_section_id=${activeClass}`),
    enabled: Boolean(activeClass),
  });

  const marked = (roll.data ?? []).filter((r) => r.status !== null);

  return (
    <>
      <Card title="Attendance">
        <div className="flex gap-3 mb-4">
          <select
            className={inputClass}
            value={activeClass}
            onChange={(e) => setClassId(e.target.value)}
          >
            {classes.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.class_label}
              </option>
            ))}
          </select>
          <input
            type="date"
            className={inputClass}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <p className="text-xs text-ink-faint mb-3">
          Read only. Attendance is marked by the class teacher in the mobile app.
        </p>

        <DataTable
          rows={marked}
          loading={roll.isLoading}
          error={roll.error}
          empty="No attendance marked for this date yet."
          columns={[
            { key: "roll", header: "Roll", render: (r) => r.roll_no },
            { key: "name", header: "Name", render: (r) => r.full_name },
            {
              key: "status",
              header: "Status",
              render: (r) =>
                r.status ? <Pill status={r.status}>{r.status}</Pill> : <span className="text-ink-faint">-</span>,
            },
            { key: "rem", header: "Remarks", render: (r) => r.remarks ?? "-" },
          ]}
        />
      </Card>

      <Card title="Section summary (all recorded days)">
        {!summary.data || summary.data.percent === null ? (
          <Empty>No attendance recorded for this section yet.</Empty>
        ) : (
          <div className="grid grid-cols-4 gap-4 text-sm">
            <Figure label="Present" value={summary.data.present} />
            <Figure label="Absent" value={summary.data.absent} />
            <Figure label="Leave" value={summary.data.leave} />
            <Figure label="Attendance" value={`${summary.data.percent}%`} />
          </div>
        )}
      </Card>
    </>
  );
}

function Figure({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <p className="text-ink-faint text-xs">{label}</p>
      <p className="text-xl font-semibold tabular">{value}</p>
    </div>
  );
}
