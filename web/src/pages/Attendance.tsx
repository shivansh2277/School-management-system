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

  const holidays = useQuery({
    queryKey: ["admin-holidays"],
    queryFn: () =>
      api.rawGet<
        Array<{
          id: number;
          name: string;
          start_date: string;
          end_date: string;
          is_school_wide: boolean;
          status: string;
          class_section_ids: number[];
        }>
      >("/admin/attendance/holidays"),
  });

  const matchingHoliday = holidays.data?.find((h) => {
    if (h.status !== "active") return false;
    const inRange = date >= h.start_date && date <= h.end_date;
    if (!inRange) return false;
    if (h.is_school_wide) return true;
    const secIds = h.class_section_ids ?? (h as any).class_sections?.map((cs: any) => cs.id) ?? [];
    return activeClass && secIds.includes(Number(activeClass));
  });

  const sum = summary.data;
  const totalRecorded = sum ? sum.present + sum.absent + sum.leave : 0;
  const presentPct = totalRecorded > 0 ? Math.round((sum!.present / totalRecorded) * 100) : 0;
  const absentPct = totalRecorded > 0 ? Math.round((sum!.absent / totalRecorded) * 100) : 0;
  const leavePct = totalRecorded > 0 ? Math.round((sum!.leave / totalRecorded) * 100) : 0;

  return (
    <div className="space-y-5">
      {/* Page Title & Filter Header Card */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Attendance Register</h1>
          <p className="text-xs text-ink-faint mt-0.5">
            Class teacher roll-call records and cumulative section attendance
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-soft">Class:</span>
            <select
              className={`${inputClass} !w-auto font-medium py-1.5`}
              value={activeClass}
              onChange={(e) => setClassId(e.target.value)}
            >
              {classes.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.class_label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-soft">Date:</span>
            <input
              type="date"
              className={`${inputClass} !w-auto py-1.5`}
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>
        </div>
      </div>

      {matchingHoliday && (
        <div className="p-3.5 bg-amber-50/90 border border-amber-300 text-amber-900 rounded-card text-xs flex items-center gap-2.5 shadow-2xs">
          <span className="text-base">🏖️</span>
          <div>
            <strong className="font-semibold text-amber-950">{matchingHoliday.name}</strong> ({matchingHoliday.start_date} → {matchingHoliday.end_date})
            <span className="text-amber-800 ml-1.5">— Normal attendance marking is blocked on declared holidays.</span>
          </div>
        </div>
      )}

      {/* Section Cumulative Summary & Distribution */}
      {sum && sum.percent !== null && (
        <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-rule/60 pb-3">
            <div>
              <h2 className="text-sm font-bold text-ink uppercase tracking-wider">
                Section Cumulative Summary
              </h2>
              <p className="text-xs text-ink-faint">All recorded sessions for selected class</p>
            </div>
            <div className="text-xs font-semibold text-ink-soft">
              Overall Rate: <strong className="text-indigo-600 text-sm">{sum.percent}%</strong>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {/* 1. Present */}
            <div className="p-3.5 rounded-xl bg-surface border border-emerald-200/70 shadow-2xs">
              <span className="text-xs font-semibold text-ink-soft">Present</span>
              <div className="text-2xl font-extrabold text-emerald-600 mt-0.5 tabular">{sum.present}</div>
              <span className="text-[11px] text-emerald-700/80 font-medium">{presentPct}% of total</span>
            </div>

            {/* 2. Absent */}
            <div className="p-3.5 rounded-xl bg-surface border border-rose-200/70 shadow-2xs">
              <span className="text-xs font-semibold text-ink-soft">Absent</span>
              <div className="text-2xl font-extrabold text-rose-600 mt-0.5 tabular">{sum.absent}</div>
              <span className="text-[11px] text-rose-700/80 font-medium">{absentPct}% of total</span>
            </div>

            {/* 3. Leave */}
            <div className="p-3.5 rounded-xl bg-surface border border-amber-200/70 shadow-2xs">
              <span className="text-xs font-semibold text-ink-soft">On Leave</span>
              <div className="text-2xl font-extrabold text-amber-600 mt-0.5 tabular">{sum.leave}</div>
              <span className="text-[11px] text-amber-700/80 font-medium">{leavePct}% of total</span>
            </div>

            {/* 4. Attendance Rate */}
            <div className="p-3.5 rounded-xl bg-surface border border-indigo-200/70 shadow-2xs">
              <span className="text-xs font-semibold text-ink-soft">Attendance Rate</span>
              <div className="text-2xl font-extrabold text-indigo-600 mt-0.5 tabular">{sum.percent}%</div>
              <span className="text-[11px] text-indigo-700/80 font-medium">Recorded rate</span>
            </div>
          </div>

          {/* Distribution Visualizer Bar */}
          <div className="pt-2 space-y-1.5">
            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex border border-rule/60">
              <div
                className="bg-emerald-500 h-full transition-all duration-300"
                style={{ width: `${presentPct}%` }}
                title={`Present: ${sum.present}`}
              />
              <div
                className="bg-amber-400 h-full transition-all duration-300"
                style={{ width: `${leavePct}%` }}
                title={`Leave: ${sum.leave}`}
              />
              <div
                className="bg-rose-500 h-full transition-all duration-300"
                style={{ width: `${absentPct}%` }}
                title={`Absent: ${sum.absent}`}
              />
            </div>
            <div className="flex flex-wrap items-center gap-4 text-[11px] text-ink-soft pt-0.5">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Present ({presentPct}%)
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400" /> Leave ({leavePct}%)
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500" /> Absent ({absentPct}%)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Daily Attendance Roll Sheet */}
      <Card
        title={`Roll Register (${roll.data ? roll.data.length : 0} students)`}
        action={
          <span className="text-xs text-ink-faint">
            Marked by class teacher via mobile roll-call
          </span>
        }
      >
        <DataTable
          rows={roll.data ?? []}
          loading={roll.isLoading}
          error={roll.error}
          empty="No attendance marked for this section on this date yet."
          columns={[
            { key: "roll", header: "Roll", render: (r) => <span className="font-semibold text-ink">{r.roll_no}</span> },
            {
              key: "name",
              header: "Student Name",
              render: (r) => (
                <span className="font-medium text-ink flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold grid place-items-center">
                    {r.full_name.charAt(0)}
                  </span>
                  {r.full_name}
                </span>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (r) =>
                r.status ? (
                  <Pill status={r.status}>{r.status}</Pill>
                ) : (
                  <span className="text-xs text-ink-faint italic">Unmarked</span>
                ),
            },
            {
              key: "rem",
              header: "Remarks",
              render: (r) => (
                <span className="text-xs text-ink-soft">{r.remarks || "—"}</span>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
