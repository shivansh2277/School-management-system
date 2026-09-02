import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, Empty, Modal } from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

type Slot = {
  period: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject: string;
  teacher: string;
  room: string | null;
};

export function Classes() {
  const { data } = useClasses();
  const [open, setOpen] = useState<ClassRow | null>(null);

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {(data ?? []).map((c) => (
          <button
            key={c.id}
            onClick={() => setOpen(c)}
            className="text-left bg-surface rounded-card shadow-card p-5 hover:ring-2 hover:ring-primary/30"
          >
            <p className="text-lg font-semibold">{c.class_label}</p>
            <p className="text-sm text-ink-soft">{c.class_teacher ?? "No class teacher"}</p>
            <p className="text-sm text-ink-faint mt-1 tabular">{c.student_count} students</p>
            <div className="flex flex-wrap gap-1 mt-3">
              {c.subjects.map((s) => (
                <span key={s} className="rounded-pill bg-primary-soft text-primary px-2 py-0.5 text-xs">
                  {s}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
      {data?.length === 0 && (
        <Card>
          <Empty>No class sections for this academic year.</Empty>
        </Card>
      )}
      {open && <ClassDetail row={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function ClassDetail({ row, onClose }: { row: ClassRow; onClose: () => void }) {
  const roster = useQuery({
    queryKey: ["class-roster", row.id],
    queryFn: () =>
      api.get<{ id: number; full_name: string; roll_no: number; admission_no: string }[]>(
        `/admin/classes/${row.id}/students`,
      ),
  });
  const timetable = useQuery({
    queryKey: ["class-timetable", row.id],
    queryFn: () => api.get<Slot[]>(`/admin/timetable?class_section_id=${row.id}`),
  });

  return (
    <Modal title={`Class ${row.class_label}`} onClose={onClose}>
      <h3 className="text-sm font-medium mb-2">Roster</h3>
      <DataTable
        rows={roster.data ?? []}
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
