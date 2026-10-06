import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, Empty, Modal } from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

export function Classes() {
  const { data } = useClasses();
  const [open, setOpen] = useState<ClassRow | null>(null);

  const totalSections = data?.length ?? 0;
  const totalStudentsEnrolled = (data ?? []).reduce((acc, c) => acc + c.student_count, 0);

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Academic Classes</h1>
          <p className="text-xs text-ink-faint mt-0.5">
            Active class sections, class teachers, subject allotments and timetables
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {totalSections} Sections
          </span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            {totalStudentsEnrolled} Students Total
          </span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {(data ?? []).map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setOpen(c)}
            className="text-left bg-surface rounded-card shadow-card p-5 border border-rule/80 hover:border-slate-300 hover:shadow-md transition-all duration-150 flex flex-col justify-between group cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-3 py-1 rounded-lg bg-[#042954] text-white font-extrabold text-base tracking-wide shadow-2xs">
                    {c.class_name.match(/^\d+$/) && Number(c.class_name) <= 10 ? `Class ${c.class_label}` : c.class_label}
                  </span>
                  {c.stream && (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
                      {c.stream}
                    </span>
                  )}
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200/60 tabular">
                  {c.student_count} students
                </span>
              </div>

              <div className="mt-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center shrink-0 border border-indigo-100">
                  {c.class_teacher ? c.class_teacher.charAt(0) : "—"}
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-ink-faint font-medium">Class Teacher</p>
                  <p className="text-sm font-semibold text-ink truncate">
                    {c.class_teacher ?? <span className="text-ink-faint italic font-normal">Unassigned</span>}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-rule/60">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-faint mb-2">
                  Allotted Subjects ({c.subjects.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {c.subjects.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs font-medium border border-slate-200/50"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-2.5 flex items-center justify-between text-xs text-primary font-semibold group-hover:text-primary-dark">
              <span>View Roster & Timetable</span>
              <span aria-hidden="true">&rarr;</span>
            </div>
          </button>
        ))}
      </div>
      {data?.length === 0 && (
        <Card>
          <Empty>No class sections configured for this academic year.</Empty>
        </Card>
      )}
      {open && <ClassDetail row={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

function ClassDetail({ row, onClose }: { row: ClassRow; onClose: () => void }) {
  const roster = useQuery({
    queryKey: ["class-roster", row.id],
    // /admin/classes/{class_id}/students has no response_model; the item
    // shape below is what the screen reads from it.
    queryFn: () =>
      api.get(`/admin/classes/${row.id}/students` as "/admin/classes/{class_id}/students") as Promise<
        { id: number; full_name: string; roll_no: number; admission_no: string }[]
      >,
  });
  const timetable = useQuery({
    queryKey: ["class-timetable", row.id],
    queryFn: () => api.get("/admin/timetable", `?class_section_id=${row.id}`),
  });

  return (
    <Modal
      title={
        row.class_name.match(/^\d+$/) && Number(row.class_name) <= 10
          ? `Class ${row.class_label}`
          : `${row.class_label}${row.stream ? ` (${row.stream})` : ""}`
      }
      onClose={onClose}
    >
      <h3 className="text-sm font-medium mb-2">Roster</h3>
      <DataTable
        rows={roster.data ?? []}
          loading={roster.isLoading}
          error={roster.error}
        empty="No students in this section."
        columns={[
          { key: "roll", header: "Roll", render: (r) => r.roll_no },
          { key: "name", header: "Name", render: (r) => r.full_name },
          { key: "adm", header: "Admission No.", render: (r) => r.admission_no },
        ]}
      />

      <h3 className="text-sm font-medium mt-6 mb-2">Timetable (read only)</h3>
      <DataTable
        rows={timetable.data ?? []}
          loading={timetable.isLoading}
          error={timetable.error}
        empty="No timetable seeded for this section."
        columns={[
          { key: "day", header: "Day", render: (s) => s.day_of_week.toUpperCase() },
          { key: "p", header: "Period", render: (s) => s.period },
          {
            key: "time",
            header: "Time",
            render: (s) => `${s.start_time.slice(0, 5)}-${s.end_time.slice(0, 5)}`,
          },
          { key: "sub", header: "Subject", render: (s) => s.subject },
          { key: "t", header: "Teacher", render: (s) => s.teacher },
          { key: "room", header: "Room", render: (s) => s.room ?? "-" },
        ]}
      />
    </Modal>
  );
}
