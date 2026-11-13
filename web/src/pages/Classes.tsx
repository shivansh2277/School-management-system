import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { errorText } from "../api/errors";
import { ActionButton } from "../components/Can";
import { Card, DataTable, Empty, FormError, FormField, Modal, Pill, inputClass } from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

type TimetableSlotItem = {
  id: number;
  period: number;
  period_id?: number | null;
  day_of_week: string;
  start_time: string;
  end_time: string;
  class_section_id: number;
  class_label: string;
  subject: string;
  subject_id?: number | null;
  teacher: string;
  teacher_id?: number | null;
  room: string | null;
  is_published: boolean;
};

type PeriodItem = {
  id: number;
  period_no: number;
  start_time: string;
  end_time: string;
  name?: string | null;
  is_break: boolean;
};

type SubjectItem = {
  id: number;
  name: string;
  code: string;
};

type TeacherItem = {
  id: number;
  full_name: string;
  employee_code?: string;
};

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
  const qc = useQueryClient();
  const [editingSlot, setEditingSlot] = useState<TimetableSlotItem | "new" | null>(null);

  const roster = useQuery({
    queryKey: ["class-roster", row.id],
    queryFn: () =>
      api.get(`/admin/classes/${row.id}/students` as "/admin/classes/{class_id}/students") as Promise<
        { id: number; full_name: string; roll_no: number; admission_no: string }[]
      >,
  });

  const timetable = useQuery<TimetableSlotItem[]>({
    queryKey: ["class-timetable", row.id],
    queryFn: () => api.rawGet<TimetableSlotItem[]>("/admin/timetable", `?class_section_id=${row.id}`),
  });

  const publish = useMutation({
    mutationFn: () => api.rawPost(`/admin/timetable/publish?class_section_id=${row.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", row.id] });
    },
  });

  const unpublish = useMutation({
    mutationFn: () => api.rawPost(`/admin/timetable/unpublish?class_section_id=${row.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", row.id] });
    },
  });

  const deleteSlot = useMutation({
    mutationFn: (slotId: number) => api.rawDel(`/admin/timetable/slots/${slotId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", row.id] });
    },
  });

  const slots = timetable.data ?? [];
  const publishedCount = slots.filter((s) => s.is_published).length;
  const draftCount = slots.length - publishedCount;
  const allPublished = slots.length > 0 && draftCount === 0;

  return (
    <Modal
      wide
      title={
        row.class_name.match(/^\d+$/) && Number(row.class_name) <= 10
          ? `Class ${row.class_label}`
          : `${row.class_label}${row.stream ? ` (${row.stream})` : ""}`
      }
      onClose={onClose}
    >
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-ink mb-2">Class Roster</h3>
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
        </div>

        <div className="border-t border-rule/60 pt-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-ink">Timetable Builder</h3>
                {slots.length > 0 && (
                  <Pill status={allPublished ? "approved" : "draft"}>
                    {allPublished ? "Published" : `${draftCount} Draft Changes`}
                  </Pill>
                )}
              </div>
              <p className="text-xs text-ink-faint mt-0.5">
                Draft timetable changes remain invisible to students and parents until published.
              </p>
            </div>

            <div className="flex items-center gap-2">
              {draftCount > 0 && (
                <ActionButton
                  permission="timetable.slot.write"
                  onClick={() => publish.mutate()}
                  disabled={publish.isPending}
                  className="rounded-input bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5"
                >
                  {publish.isPending ? "Publishing…" : "Publish Changes"}
                </ActionButton>
              )}
              {publishedCount > 0 && (
                <ActionButton
                  permission="timetable.slot.write"
                  onClick={() => unpublish.mutate()}
                  disabled={unpublish.isPending}
                  className="rounded-input border border-rule hover:bg-ground text-ink text-xs font-medium px-3 py-1.5"
                >
                  {unpublish.isPending ? "Reverting…" : "Revert to Draft"}
                </ActionButton>
              )}
              <ActionButton
                permission="timetable.slot.write"
                onClick={() => setEditingSlot("new")}
                className="rounded-input bg-primary hover:bg-primary/90 text-white text-xs font-semibold px-3 py-1.5"
              >
                + Add Slot
              </ActionButton>
            </div>
          </div>

          <DataTable
            rows={slots}
            loading={timetable.isLoading}
            error={timetable.error}
            empty="No timetable slots configured for this class section."
            columns={[
              {
                key: "day",
                header: "Day",
                render: (s) => (
                  <span className="font-semibold text-xs uppercase text-slate-700">
                    {s.day_of_week}
                  </span>
                ),
              },
              {
                key: "p",
                header: "Period",
                render: (s) => (
                  <span className="font-medium text-xs text-ink">
                    Period {s.period}
                  </span>
                ),
              },
              {
                key: "time",
                header: "Time",
                render: (s) => (
                  <span className="text-xs text-ink-soft tabular">
                    {s.start_time?.slice(0, 5)} - {s.end_time?.slice(0, 5)}
                  </span>
                ),
              },
              {
                key: "sub",
                header: "Subject",
                render: (s) => (
                  <span className="font-medium text-xs text-indigo-900 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                    {s.subject}
                  </span>
                ),
              },
              {
                key: "t",
                header: "Teacher",
                render: (s) => (
                  <span className="text-xs text-ink">
                    {s.teacher || "—"}
                  </span>
                ),
              },
              {
                key: "room",
                header: "Room",
                render: (s) => (
                  <span className="text-xs font-mono text-slate-700">
                    {s.room || "—"}
                  </span>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (s) => (
                  <Pill status={s.is_published ? "approved" : "draft"}>
                    {s.is_published ? "Published" : "Draft"}
                  </Pill>
                ),
              },
              {
                key: "actions",
                header: "",
                render: (s) => (
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => setEditingSlot(s)}
                      className="text-xs font-medium text-primary hover:underline px-1.5 py-0.5"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (confirm(`Delete slot for ${s.day_of_week.toUpperCase()} Period ${s.period}?`)) {
                          deleteSlot.mutate(s.id);
                        }
                      }}
                      className="text-xs font-medium text-danger hover:underline px-1.5 py-0.5"
                    >
                      Delete
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      </div>

      {editingSlot && (
        <SlotModal
          classSectionId={row.id}
          slot={editingSlot === "new" ? null : editingSlot}
          onClose={() => setEditingSlot(null)}
          onSaved={() => {
            setEditingSlot(null);
            qc.invalidateQueries({ queryKey: ["class-timetable", row.id] });
          }}
        />
      )}
    </Modal>
  );
}

function SlotModal({
  classSectionId,
  slot,
  onClose,
  onSaved,
}: {
  classSectionId: number;
  slot: TimetableSlotItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const subjects = useQuery<SubjectItem[]>({
    queryKey: ["subjects"],
    queryFn: () => api.rawGet<SubjectItem[]>("/admin/subjects"),
  });

  const teachers = useQuery<TeacherItem[]>({
    queryKey: ["teachers"],
    queryFn: () => api.rawGet<TeacherItem[]>("/admin/teachers"),
  });

  const [form, setForm] = useState({
    day_of_week: slot?.day_of_week?.toLowerCase() || "mon",
    period_id: slot?.period_id ? String(slot.period_id) : "",
    subject_id: slot?.subject_id ? String(slot.subject_id) : "",
    teacher_id: slot?.teacher_id ? String(slot.teacher_id) : "",
    room: slot?.room || "",
  });

  type ConflictItem = string | { kind?: string; detail: string; slot_id?: number };
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Auto-populate first period/subject/teacher if creating new
  useEffect(() => {
    if (!slot) {
      if (!form.period_id && periods.data && periods.data.length > 0) {
        setForm((f) => ({ ...f, period_id: String(periods.data![0].id) }));
      }
      if (!form.subject_id && subjects.data && subjects.data.length > 0) {
        setForm((f) => ({ ...f, subject_id: String(subjects.data![0].id) }));
      }
      if (!form.teacher_id && teachers.data && teachers.data.length > 0) {
        setForm((f) => ({ ...f, teacher_id: String(teachers.data![0].id) }));
      }
    }
  }, [slot, periods.data, subjects.data, teachers.data]);

  // Live conflict detection
  useEffect(() => {
    if (!form.period_id || !form.teacher_id) {
      setConflicts([]);
      return;
    }
    let active = true;
    const timer = setTimeout(async () => {
      try {
        const res = await api.rawPost<{ ok: boolean; conflicts: ConflictItem[] }>("/admin/timetable/slots/check", {
          class_section_id: classSectionId,
          day_of_week: form.day_of_week,
          period_id: Number(form.period_id),
          subject_id: Number(form.subject_id) || 1,
          teacher_id: Number(form.teacher_id),
          room: form.room.trim() || null,
        });
        if (active) {
          // If editing this slot, filter out conflicts caused by the current slot itself
          const filtered = (res.conflicts || []).filter((c) => {
            const detail = typeof c === "string" ? c : c.detail;
            if (slot && detail.includes(`Period ${slot.period}`) && detail.includes(slot.day_of_week.toUpperCase())) {
              return false;
            }
            return true;
          });
          setConflicts(filtered);
        }
      } catch {
        // Non-blocking conflict check
      }
    }, 250);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [classSectionId, form.day_of_week, form.period_id, form.teacher_id, form.room, slot]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    setSaving(true);
    try {
      const payload = {
        class_section_id: classSectionId,
        day_of_week: form.day_of_week,
        period_id: Number(form.period_id),
        subject_id: Number(form.subject_id),
        teacher_id: Number(form.teacher_id),
        room: form.room.trim() || null,
      };

      if (slot) {
        await api.rawPut(`/admin/timetable/slots/${slot.id}`, payload);
      } else {
        await api.rawPost("/admin/timetable/slots", payload);
      }
      onSaved();
    } catch (err: unknown) {
      setSaveError(errorText(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={slot ? "Edit Timetable Slot" : "Add Timetable Slot"} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Day of Week">
            <select
              className={inputClass}
              value={form.day_of_week}
              onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
            >
              <option value="mon">Monday</option>
              <option value="tue">Tuesday</option>
              <option value="wed">Wednesday</option>
              <option value="thu">Thursday</option>
              <option value="fri">Friday</option>
              <option value="sat">Saturday</option>
            </select>
          </FormField>

          <FormField label="Period">
            <select
              className={inputClass}
              value={form.period_id}
              onChange={(e) => setForm({ ...form, period_id: e.target.value })}
              required
            >
              {periods.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  Period {p.period_no} ({p.start_time.slice(0, 5)} - {p.end_time.slice(0, 5)})
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Subject">
          <select
            className={inputClass}
            value={form.subject_id}
            onChange={(e) => setForm({ ...form, subject_id: e.target.value })}
            required
          >
            {subjects.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Teacher">
          <select
            className={inputClass}
            value={form.teacher_id}
            onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}
            required
          >
            {teachers.data?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Room / Location (Optional)">
          <input
            className={inputClass}
            placeholder="e.g. Room 101, Science Lab"
            value={form.room}
            onChange={(e) => setForm({ ...form, room: e.target.value })}
          />
        </FormField>

        {conflicts.length > 0 && (
          <div className="rounded-card border border-danger/30 bg-danger/5 p-3 text-xs text-danger space-y-1">
            <p className="font-semibold flex items-center gap-1.5">
              <span>⚠️</span> Scheduling Conflicts Detected:
            </p>
            <ul className="list-disc list-inside space-y-0.5">
              {conflicts.map((c, i) => (
                <li key={i}>{typeof c === "string" ? c : c.detail}</li>
              ))}
            </ul>
          </div>
        )}

        {saveError && <FormError error={saveError} />}

        <div className="flex justify-end gap-2 pt-2 border-t border-rule/60">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {saving ? "Saving…" : slot ? "Update Slot" : "Create Slot"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
