import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { ActionButton } from "../components/Can";
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
} from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

// --- Types ---

type TimetableSlotItem = {
  id: number;
  class_section_id: number;
  class_label: string;
  day_of_week: string;
  period: number;
  period_id?: number | null;
  start_time: string;
  end_time: string;
  subject: string;
  subject_id?: number | null;
  teacher: string;
  teacher_id?: number | null;
  room: string | null;
  is_published: boolean;
  is_relief?: boolean;
  relief_teacher?: string | null;
  substituted?: boolean;
  status?: string;
  reason?: string;
};

type PeriodItem = {
  id: number;
  period_no: number;
  name?: string | null;
  start_time: string;
  end_time: string;
  is_break: boolean;
};

type TeacherItem = {
  id: number;
  full_name: string;
  employee_code?: string;
};

type SubjectItem = {
  id: number;
  name: string;
  code: string;
};

type FreeTeacher = {
  teacher_id: number;
  name: string;
  teaches_this_subject: boolean;
  weekly_load: number;
};

type WorkloadData = {
  teachers: number;
  total_periods: number;
  limit: number;
  fair_share: number;
  lightest: number;
  heaviest: number;
  spread: number;
  over_limit: string[];
  unassigned: string[];
  rows: {
    teacher_id: number;
    employee_code: string;
    name: string;
    department: string | null;
    periods: number;
    limit: number;
    over: boolean;
    share: number | null;
  }[];
};

type CompletenessItem = {
  class_section_id: number;
  class_label: string;
  placed: number;
  expected: number;
  missing: number;
};

type SubstitutionItem = {
  id: number;
  date: string;
  slot_id: number;
  class_label: string;
  period: number;
  absent_teacher: string;
  substitute_teacher: string | null;
  status: string;
  reason: string;
};

const DAYS = [
  { key: "mon", label: "Monday" },
  { key: "tue", label: "Tuesday" },
  { key: "wed", label: "Wednesday" },
  { key: "thu", label: "Thursday" },
  { key: "fri", label: "Friday" },
  { key: "sat", label: "Saturday" },
];

export function Timetable() {
  const [tab, setTab] = useState<"class" | "teacher" | "daily" | "dashboards" | "periods">("class");

  return (
    <div className="space-y-6">
      {/* Page Title & Navigation Tabs */}
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-[#042954] flex items-center justify-center text-[#ffa726] shadow-2xs font-bold text-sm">
                TT
              </span>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">
                Timetable Administration
              </h1>
            </div>
            <p className="text-xs text-ink-faint mt-1">
              Master schedule configuration, bell timings, class/faculty timetables, substitutions and conflict resolution
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-800 text-xs font-semibold">
              Academic Coordinator Workspace
            </span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex flex-wrap gap-2 mt-5 pt-4 border-t border-rule/60">
          <button
            type="button"
            onClick={() => setTab("class")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              tab === "class"
                ? "bg-[#042954] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Class Timetables
          </button>
          <button
            type="button"
            onClick={() => setTab("teacher")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              tab === "teacher"
                ? "bg-[#042954] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Teacher Schedules
          </button>
          <button
            type="button"
            onClick={() => setTab("daily")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              tab === "daily"
                ? "bg-[#042954] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Daily Schedule & Substitutions
          </button>
          <button
            type="button"
            onClick={() => setTab("dashboards")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              tab === "dashboards"
                ? "bg-[#042954] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Workload & Completeness
          </button>
          <button
            type="button"
            onClick={() => setTab("periods")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              tab === "periods"
                ? "bg-[#042954] text-white shadow-xs"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Bell Timings / Periods
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      {tab === "class" && <ClassTimetableTab />}
      {tab === "teacher" && <TeacherTimetableTab />}
      {tab === "daily" && <DailyScheduleTab />}
      {tab === "dashboards" && <DashboardsTab />}
      {tab === "periods" && <PeriodsTab />}
    </div>
  );
}

// ==========================================
// Tab 1: Class Timetables
// ==========================================

function ClassTimetableTab() {
  const qc = useQueryClient();
  const { data: classesData, isLoading: loadingClasses } = useClasses();
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [editingSlot, setEditingSlot] = useState<TimetableSlotItem | "new" | null>(null);

  useEffect(() => {
    if (!selectedClassId && classesData && classesData.length > 0) {
      setSelectedClassId(classesData[0].id);
    }
  }, [classesData, selectedClassId]);

  const selectedClass = classesData?.find((c) => c.id === selectedClassId);

  const timetable = useQuery<TimetableSlotItem[]>({
    queryKey: ["class-timetable", selectedClassId],
    queryFn: () =>
      selectedClassId
        ? api.rawGet<TimetableSlotItem[]>("/admin/timetable/slots", `?class_section_id=${selectedClassId}`)
        : Promise.resolve([]),
    enabled: !!selectedClassId,
  });

  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const publishClass = useMutation({
    mutationFn: () => api.rawPost(`/admin/timetable/publish?class_section_id=${selectedClassId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", selectedClassId] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
    },
  });

  const unpublishClass = useMutation({
    mutationFn: () =>
      api.rawPost(
        `/admin/timetable/unpublish?class_section_id=${selectedClassId}&reason=Reverted+to+draft+by+Academic+Coordinator`
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", selectedClassId] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
    },
  });

  const publishAll = useMutation({
    mutationFn: () => api.rawPost("/admin/timetable/publish"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable"] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
    },
  });

  const deleteSlot = useMutation({
    mutationFn: (slotId: number) =>
      api.rawDel(`/admin/timetable/slots/${slotId}?reason=Removed+by+Academic+Coordinator`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-timetable", selectedClassId] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
    },
  });

  const slots = timetable.data ?? [];
  const publishedCount = slots.filter((s) => s.is_published).length;
  const draftCount = slots.length - publishedCount;
  const allPublished = slots.length > 0 && draftCount === 0;

  const sortedPeriods = [...(periods.data ?? [])].sort((a, b) => a.period_no - b.period_no);

  return (
    <div className="space-y-5">
      {/* Class Section Selector & Controls */}
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-bold text-ink-soft uppercase tracking-wider">
            Select Class:
          </label>
          <select
            className={inputClass + " w-48 font-semibold text-ink"}
            value={selectedClassId ?? ""}
            onChange={(e) => setSelectedClassId(Number(e.target.value))}
            disabled={loadingClasses}
          >
            {(classesData ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                Class {c.class_label} {c.stream ? `(${c.stream})` : ""}
              </option>
            ))}
          </select>

          {selectedClass && (
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium border border-slate-200">
                Teacher: <strong className="text-ink">{selectedClass.class_teacher ?? "Unassigned"}</strong>
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium border border-slate-200">
                {slots.length} Slots Configured
              </span>
              {slots.length > 0 && (
                <Pill status={allPublished ? "approved" : "draft"}>
                  {allPublished ? "Published" : `${draftCount} Draft Changes`}
                </Pill>
              )}
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {draftCount > 0 && (
            <ActionButton
              permission="timetable.slot.write"
              onClick={() => publishClass.mutate()}
              disabled={publishClass.isPending}
              className="rounded-input bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5"
            >
              {publishClass.isPending ? "Publishing…" : "Publish Section"}
            </ActionButton>
          )}
          {publishedCount > 0 && (
            <ActionButton
              permission="timetable.slot.write"
              onClick={() => unpublishClass.mutate()}
              disabled={unpublishClass.isPending}
              className="rounded-input border border-rule hover:bg-ground text-ink text-xs font-medium px-3 py-1.5"
            >
              {unpublishClass.isPending ? "Reverting…" : "Revert to Draft"}
            </ActionButton>
          )}
          <ActionButton
            permission="timetable.slot.write"
            onClick={() => publishAll.mutate()}
            disabled={publishAll.isPending}
            className="rounded-input border border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 text-xs font-semibold px-3 py-1.5"
          >
            {publishAll.isPending ? "Publishing All…" : "Publish All Classes"}
          </ActionButton>
          <ActionButton
            permission="timetable.slot.write"
            onClick={() => setEditingSlot("new")}
            className="rounded-input bg-primary hover:bg-primary/90 text-white text-xs font-semibold px-3.5 py-1.5"
          >
            + Add Lesson Slot
          </ActionButton>
        </div>
      </div>

      {/* Timetable Grid View */}
      <Card title={selectedClass ? `Weekly Timetable — Class ${selectedClass.class_label}` : "Timetable"}>
        {sortedPeriods.length === 0 ? (
          <Empty>No school periods configured. Please add school periods under the Bell Timings tab.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-rule">
                  <th className="p-3 font-bold text-ink uppercase tracking-wider w-24 border-r border-rule">
                    Day
                  </th>
                  {sortedPeriods.map((p) => (
                    <th key={p.id} className="p-2.5 font-semibold text-ink border-r border-rule min-w-[130px]">
                      <div className="font-bold text-ink">Period {p.period_no}</div>
                      <div className="text-[10px] text-ink-faint tabular">
                        {p.start_time?.slice(0, 5)} - {p.end_time?.slice(0, 5)}
                      </div>
                      {p.is_break && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 font-bold block mt-0.5">
                          {p.name || "BREAK"}
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-rule/60">
                {DAYS.map((d) => (
                  <tr key={d.key} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold uppercase tracking-wide text-slate-700 bg-slate-50/60 border-r border-rule">
                      {d.label}
                    </td>
                    {sortedPeriods.map((p) => {
                      if (p.is_break) {
                        return (
                          <td
                            key={p.id}
                            className="p-2 bg-amber-50/40 border-r border-rule text-center text-[11px] text-amber-900 font-medium italic"
                          >
                            {p.name || "Recess"}
                          </td>
                        );
                      }
                      const slot = slots.find(
                        (s) =>
                          s.day_of_week?.toLowerCase() === d.key &&
                          (s.period === p.period_no || s.period_id === p.id)
                      );
                      return (
                        <td key={p.id} className="p-2 border-r border-rule align-top min-w-[130px]">
                          {slot ? (
                            <div className="p-2 rounded-lg bg-indigo-50/70 border border-indigo-200/80 hover:border-indigo-400 transition-all flex flex-col justify-between h-full group relative shadow-2xs">
                              <div>
                                <div className="flex items-center justify-between gap-1 mb-1">
                                  <span className="font-bold text-[11px] text-indigo-950 truncate">
                                    {slot.subject}
                                  </span>
                                  <span
                                    className={`w-2 h-2 rounded-full ${
                                      slot.is_published ? "bg-emerald-500" : "bg-amber-500"
                                    }`}
                                    title={slot.is_published ? "Published" : "Draft (Unpublished)"}
                                  />
                                </div>
                                <div className="text-[10px] text-indigo-900 font-medium truncate">
                                  {slot.teacher || "—"}
                                </div>
                                {slot.room && (
                                  <div className="text-[9px] text-slate-600 font-mono mt-0.5">
                                    Rm {slot.room}
                                  </div>
                                )}
                              </div>
                              <div className="mt-2 pt-1 border-t border-indigo-100 flex items-center justify-between text-[10px]">
                                <button
                                  type="button"
                                  onClick={() => setEditingSlot(slot)}
                                  className="text-primary font-bold hover:underline"
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (
                                      confirm(
                                        `Delete slot for ${d.label} Period ${p.period_no} (${slot.subject})?`
                                      )
                                    ) {
                                      deleteSlot.mutate(slot.id);
                                    }
                                  }}
                                  className="text-danger font-semibold hover:underline"
                                >
                                  Del
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setEditingSlot({
                                  id: 0,
                                  class_section_id: selectedClassId!,
                                  class_label: selectedClass?.class_label ?? "",
                                  day_of_week: d.key,
                                  period: p.period_no,
                                  period_id: p.id,
                                  start_time: p.start_time,
                                  end_time: p.end_time,
                                  subject: "",
                                  teacher: "",
                                  room: "",
                                  is_published: false,
                                });
                              }}
                              className="w-full h-full min-h-[64px] border border-dashed border-slate-200 hover:border-primary/50 hover:bg-primary/5 rounded-lg text-slate-400 hover:text-primary flex items-center justify-center text-xs font-semibold transition-all cursor-pointer"
                              title={`Add lesson on ${d.label} Period ${p.period_no}`}
                            >
                              + Add
                            </button>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Slot Modal */}
      {editingSlot && selectedClassId && (
        <SlotModal
          classSectionId={selectedClassId}
          slot={editingSlot === "new" ? null : editingSlot}
          onClose={() => setEditingSlot(null)}
          onSaved={() => {
            setEditingSlot(null);
            qc.invalidateQueries({ queryKey: ["class-timetable", selectedClassId] });
            qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
          }}
        />
      )}
    </div>
  );
}

// ==========================================
// Tab 2: Teacher Timetables
// ==========================================

function TeacherTimetableTab() {
  const teachers = useQuery<TeacherItem[]>({
    queryKey: ["teachers"],
    queryFn: () => api.rawGet<TeacherItem[]>("/admin/teachers"),
  });

  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const [selectedTeacherId, setSelectedTeacherId] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedTeacherId && teachers.data && teachers.data.length > 0) {
      setSelectedTeacherId(teachers.data[0].id);
    }
  }, [teachers.data, selectedTeacherId]);

  const selectedTeacher = teachers.data?.find((t) => t.id === selectedTeacherId);

  const timetable = useQuery<TimetableSlotItem[]>({
    queryKey: ["teacher-timetable", selectedTeacherId],
    queryFn: () =>
      selectedTeacherId
        ? api.rawGet<TimetableSlotItem[]>("/admin/timetable/slots", `?teacher_id=${selectedTeacherId}`)
        : Promise.resolve([]),
    enabled: !!selectedTeacherId,
  });

  const slots = timetable.data ?? [];
  const sortedPeriods = [...(periods.data ?? [])].sort((a, b) => a.period_no - b.period_no);

  return (
    <div className="space-y-5">
      {/* Teacher Picker Bar */}
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-bold text-ink-soft uppercase tracking-wider">
            Select Faculty Teacher:
          </label>
          <select
            className={inputClass + " w-64 font-semibold text-ink"}
            value={selectedTeacherId ?? ""}
            onChange={(e) => setSelectedTeacherId(Number(e.target.value))}
            disabled={teachers.isLoading}
          >
            {(teachers.data ?? []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name} {t.employee_code ? `(${t.employee_code})` : ""}
              </option>
            ))}
          </select>

          {selectedTeacher && (
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded-full bg-blue-50 text-blue-800 font-bold border border-blue-200">
                {slots.length} Assigned Periods / Week
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Teacher Schedule Grid */}
      <Card title={selectedTeacher ? `Weekly Schedule — ${selectedTeacher.full_name}` : "Faculty Timetable"}>
        {sortedPeriods.length === 0 ? (
          <Empty>No periods configured.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-rule">
                  <th className="p-3 font-bold text-ink uppercase tracking-wider w-24 border-r border-rule">
                    Day
                  </th>
                  {sortedPeriods.map((p) => (
                    <th key={p.id} className="p-2.5 font-semibold text-ink border-r border-rule min-w-[130px]">
                      <div className="font-bold text-ink">Period {p.period_no}</div>
                      <div className="text-[10px] text-ink-faint tabular">
                        {p.start_time?.slice(0, 5)} - {p.end_time?.slice(0, 5)}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-rule/60">
                {DAYS.map((d) => (
                  <tr key={d.key} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold uppercase tracking-wide text-slate-700 bg-slate-50/60 border-r border-rule">
                      {d.label}
                    </td>
                    {sortedPeriods.map((p) => {
                      if (p.is_break) {
                        return (
                          <td
                            key={p.id}
                            className="p-2 bg-amber-50/40 border-r border-rule text-center text-[11px] text-amber-900 font-medium italic"
                          >
                            {p.name || "Recess"}
                          </td>
                        );
                      }
                      const slot = slots.find(
                        (s) =>
                          s.day_of_week?.toLowerCase() === d.key &&
                          (s.period === p.period_no || s.period_id === p.id)
                      );
                      return (
                        <td key={p.id} className="p-2 border-r border-rule align-top min-w-[130px]">
                          {slot ? (
                            <div className="p-2 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-950 shadow-2xs">
                              <div className="font-extrabold text-[11px]">{slot.class_label}</div>
                              <div className="text-[11px] font-semibold text-emerald-900 mt-0.5">
                                {slot.subject}
                              </div>
                              {slot.room && (
                                <div className="text-[9px] text-slate-600 font-mono mt-1">
                                  Room: {slot.room}
                                </div>
                              )}
                              {slot.is_relief && (
                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 block mt-1">
                                  Relief Cover
                                </span>
                              )}
                            </div>
                          ) : (
                            <div className="h-full min-h-[50px] flex items-center justify-center text-slate-300 text-xs italic">
                              Free
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

// ==========================================
// Tab 3: Daily Schedule & Substitution Desk
// ==========================================

function DailyScheduleTab() {
  const qc = useQueryClient();
  const todayStr = new Date().toISOString().slice(0, 10);
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [reliefSlot, setReliefSlot] = useState<TimetableSlotItem | null>(null);

  const daySchedule = useQuery<TimetableSlotItem[]>({
    queryKey: ["daily-schedule", selectedDate],
    queryFn: () => api.rawGet<TimetableSlotItem[]>(`/admin/timetable/day?date=${selectedDate}`),
  });

  const substitutions = useQuery<SubstitutionItem[]>({
    queryKey: ["substitutions-log", selectedDate],
    queryFn: () => api.rawGet<SubstitutionItem[]>(`/admin/timetable/substitutions?date=${selectedDate}`),
  });

  const slots = daySchedule.data ?? [];
  const totalSlots = slots.length;
  const substitutedSlots = slots.filter((s) => s.substituted).length;
  const normalSlots = totalSlots - substitutedSlots;

  return (
    <div className="space-y-6">
      {/* Date Bar & Overview */}
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-bold text-ink-soft uppercase tracking-wider">
            Operational Date:
          </label>
          <input
            type="date"
            className={inputClass + " w-44 font-semibold text-ink"}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setSelectedDate(todayStr)}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold cursor-pointer"
          >
            Today
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {totalSlots} Scheduled Lessons
          </span>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
            {substitutedSlots} Active Reliefs
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Total Scheduled Periods" value={totalSlots} hint="Operational for selected date" />
        <StatCard
          label="Regular Faculty Conducting"
          value={normalSlots}
          hint="Lessons running on normal schedule"
        />
        <StatCard
          label="Substitutions / Relief Assigned"
          value={substitutedSlots}
          hint="Arranged via Substitution Desk"
        />
      </div>

      {/* Daily Operations Schedule Table */}
      <Card title={`Operational Schedule for ${selectedDate}`}>
        <DataTable
          rows={slots}
          loading={daySchedule.isLoading}
          error={daySchedule.error}
          empty="No timetable slots scheduled for this day (school may be closed or weekend)."
          columns={[
            {
              key: "period",
              header: "Period",
              render: (r) => (
                <span className="font-bold text-xs text-ink">
                  Period {r.period}
                </span>
              ),
            },
            {
              key: "time",
              header: "Timing",
              render: (r) => (
                <span className="text-xs text-ink-soft tabular">
                  {r.start_time?.slice(0, 5)} - {r.end_time?.slice(0, 5)}
                </span>
              ),
            },
            {
              key: "class",
              header: "Class Section",
              render: (r) => (
                <span className="font-semibold text-xs text-indigo-900 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                  {r.class_label}
                </span>
              ),
            },
            {
              key: "subject",
              header: "Subject",
              render: (r) => <span className="font-medium text-xs text-ink">{r.subject}</span>,
            },
            {
              key: "teacher",
              header: "Faculty / Teacher",
              render: (r) => (
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-semibold text-ink">{r.teacher || "—"}</span>
                  {r.substituted && (
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-200">
                      SUBSTITUTE
                    </span>
                  )}
                </div>
              ),
            },
            {
              key: "room",
              header: "Room",
              render: (r) => <span className="font-mono text-xs text-slate-600">{r.room || "—"}</span>,
            },
            {
              key: "status",
              header: "Status",
              render: (r) => (
                <Pill status={r.substituted ? "review" : "approved"}>
                  {r.substituted ? "Relief Active" : "Normal"}
                </Pill>
              ),
            },
            {
              key: "action",
              header: "",
              render: (r) => (
                <ActionButton
                  permission="timetable.substitution.manage"
                  onClick={() => setReliefSlot(r)}
                  className="rounded bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-bold px-2.5 py-1"
                >
                  Assign Relief
                </ActionButton>
              ),
            },
          ]}
        />
      </Card>

      {/* Substitutions Desk Log */}
      <Card title={`Active Substitution Records for ${selectedDate}`}>
        <DataTable
          rows={substitutions.data ?? []}
          loading={substitutions.isLoading}
          error={substitutions.error}
          empty="No substitutions have been logged for this date."
          columns={[
            {
              key: "class",
              header: "Class & Period",
              render: (s) => (
                <span className="font-semibold text-xs text-ink">
                  {s.class_label} (Period {s.period})
                </span>
              ),
            },
            {
              key: "absent",
              header: "Absent Teacher",
              render: (s) => <span className="text-xs text-danger font-medium">{s.absent_teacher}</span>,
            },
            {
              key: "sub",
              header: "Substitute Teacher",
              render: (s) => (
                <span className="text-xs text-emerald-700 font-bold">
                  {s.substitute_teacher || <span className="text-amber-600 font-semibold italic">Unfilled</span>}
                </span>
              ),
            },
            {
              key: "reason",
              header: "Reason",
              render: (s) => <span className="text-xs text-ink-soft">{s.reason}</span>,
            },
            {
              key: "status",
              header: "Status",
              render: (s) => (
                <Pill status={s.status === "assigned" ? "approved" : "draft"}>
                  {s.status.toUpperCase()}
                </Pill>
              ),
            },
          ]}
        />
      </Card>

      {/* Assign Relief Modal */}
      {reliefSlot && (
        <ReliefModal
          slot={reliefSlot}
          date={selectedDate}
          onClose={() => setReliefSlot(null)}
          onSaved={() => {
            setReliefSlot(null);
            qc.invalidateQueries({ queryKey: ["daily-schedule", selectedDate] });
            qc.invalidateQueries({ queryKey: ["substitutions-log", selectedDate] });
          }}
        />
      )}
    </div>
  );
}

// ==========================================
// Tab 4: Workload & Completeness Dashboards
// ==========================================

function DashboardsTab() {
  const workload = useQuery<WorkloadData>({
    queryKey: ["timetable-workload"],
    queryFn: () => api.rawGet<WorkloadData>("/admin/timetable/workload"),
  });

  const completeness = useQuery<CompletenessItem[]>({
    queryKey: ["timetable-completeness"],
    queryFn: () => api.rawGet<CompletenessItem[]>("/admin/timetable/completeness"),
  });

  const wData = workload.data;
  const cData = completeness.data ?? [];

  return (
    <div className="space-y-6">
      {/* Workload Summary KPI Cards */}
      {wData && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Teaching Faculty"
            value={wData.teachers}
            hint="Active instructional staff"
          />
          <StatCard
            label="Total Weekly Periods"
            value={wData.total_periods}
            hint={`Fair Share: ~${wData.fair_share} periods/teacher`}
          />
          <StatCard
            label="Heaviest Load"
            value={`${wData.heaviest} periods`}
            hint={`Lightest: ${wData.lightest} periods`}
          />
          <StatCard
            label="Workload Spread"
            value={`${wData.spread} periods`}
            hint={wData.spread <= 4 ? "Evenly distributed" : "High load disparity"}
          />
        </div>
      )}

      {/* Completeness Matrix Card */}
      <Card title="Timetable Completeness by Class Section">
        <p className="text-xs text-ink-faint mb-3">
          Verifies every class section has all required weekly teaching periods allotted.
        </p>
        <DataTable
          rows={cData}
          loading={completeness.isLoading}
          error={completeness.error}
          empty="No class sections found."
          columns={[
            {
              key: "class",
              header: "Class Section",
              render: (c) => <span className="font-bold text-xs text-ink">{c.class_label}</span>,
            },
            {
              key: "placed",
              header: "Allotted Periods",
              render: (c) => <span className="text-xs font-semibold tabular">{c.placed}</span>,
            },
            {
              key: "expected",
              header: "Expected Periods",
              render: (c) => <span className="text-xs text-ink-soft tabular">{c.expected}</span>,
            },
            {
              key: "missing",
              header: "Missing / Gaps",
              render: (c) => (
                <span
                  className={`text-xs font-bold ${
                    c.missing > 0 ? "text-danger" : "text-emerald-600"
                  }`}
                >
                  {c.missing > 0 ? `${c.missing} periods missing` : "Complete"}
                </span>
              ),
            },
            {
              key: "status",
              header: "Completeness Status",
              render: (c) => (
                <Pill status={c.missing === 0 ? "approved" : "draft"}>
                  {c.missing === 0 ? "100% Complete" : `${c.missing} Gaps`}
                </Pill>
              ),
            },
          ]}
        />
      </Card>

      {/* Faculty Workload Distribution Table */}
      <Card title="Faculty Teaching Workload & Fair Share Analysis">
        <DataTable
          rows={wData?.rows ?? []}
          loading={workload.isLoading}
          error={workload.error}
          empty="No teaching faculty found."
          columns={[
            {
              key: "code",
              header: "Emp Code",
              render: (r) => <span className="font-mono text-xs text-slate-600">{r.employee_code}</span>,
            },
            {
              key: "name",
              header: "Teacher Name",
              render: (r) => <span className="font-bold text-xs text-ink">{r.name}</span>,
            },
            {
              key: "dept",
              header: "Department",
              render: (r) => <span className="text-xs text-ink-soft">{r.department || "—"}</span>,
            },
            {
              key: "periods",
              header: "Weekly Load",
              render: (r) => (
                <span className="font-extrabold text-xs text-ink tabular">
                  {r.periods} periods
                </span>
              ),
            },
            {
              key: "share",
              header: "Fair Share Ratio",
              render: (r) => (
                <span className="text-xs font-medium tabular text-slate-700">
                  {r.share ? `${r.share}x` : "—"}
                </span>
              ),
            },
            {
              key: "status",
              header: "Workload Status",
              render: (r) => {
                if (r.over) {
                  return <Pill status="danger">Over Limit (&gt;{r.limit})</Pill>;
                }
                if (r.periods === 0) {
                  return <Pill status="draft">Unassigned</Pill>;
                }
                return <Pill status="approved">Optimal</Pill>;
              },
            },
          ]}
        />
      </Card>
    </div>
  );
}

// ==========================================
// Tab 5: Bell Timings / Periods
// ==========================================

function PeriodsTab() {
  const qc = useQueryClient();
  const [addingPeriod, setAddingPeriod] = useState(false);
  const [editingPeriod, setEditingPeriod] = useState<PeriodItem | null>(null);

  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const toggleBreak = useMutation({
    mutationFn: (p: PeriodItem) =>
      api.rawPut(`/admin/timetable/periods/${p.id}`, {
        is_break: !p.is_break,
        name: !p.is_break ? (p.name || "Break") : null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timetable-periods"] });
      qc.invalidateQueries({ queryKey: ["class-timetable"] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
      qc.invalidateQueries({ queryKey: ["timetable-workload"] });
    },
  });

  const rows = [...(periods.data ?? [])].sort((a, b) => a.period_no - b.period_no);

  return (
    <div className="space-y-5">
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-ink">School Bell Timings & Period Slots</h2>
          <p className="text-xs text-ink-faint mt-0.5">
            Configure school periods, recess/break timings, and instructional lessons. Break periods are dynamically configurable at any time.
          </p>
        </div>
        <ActionButton
          permission="timetable.slot.write"
          onClick={() => setAddingPeriod(true)}
          className="rounded-input bg-primary hover:bg-primary/90 text-white text-xs font-semibold px-3.5 py-1.5"
        >
          + Add School Period
        </ActionButton>
      </div>

      <Card>
        <DataTable
          rows={rows}
          loading={periods.isLoading}
          error={periods.error}
          empty="No school periods configured."
          columns={[
            {
              key: "no",
              header: "Period No.",
              render: (p) => (
                <span className="font-extrabold text-xs text-ink">
                  Period {p.period_no}
                </span>
              ),
            },
            {
              key: "name",
              header: "Label / Name",
              render: (p) => (
                <span className="font-semibold text-xs text-slate-800">
                  {p.name || `Period ${p.period_no}`}
                </span>
              ),
            },
            {
              key: "start",
              header: "Start Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.start_time?.slice(0, 5)}</span>,
            },
            {
              key: "end",
              header: "End Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.end_time?.slice(0, 5)}</span>,
            },
            {
              key: "type",
              header: "Period Type",
              render: (p) => (
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    p.is_break
                      ? "bg-amber-100 text-amber-900 border border-amber-300 font-bold"
                      : "bg-blue-100 text-blue-800 border border-blue-200"
                  }`}
                >
                  {p.is_break ? "Break / Recess" : "Instructional Lesson"}
                </span>
              ),
            },
            {
              key: "actions",
              header: "Configure Period",
              render: (p) => (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingPeriod(p)}
                    className="px-2.5 py-1 text-xs font-semibold rounded border border-rule hover:bg-slate-100 text-ink cursor-pointer"
                  >
                    Edit / Configure
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleBreak.mutate(p)}
                    disabled={toggleBreak.isPending}
                    className={`px-2.5 py-1 text-xs font-bold rounded cursor-pointer transition-all ${
                      p.is_break
                        ? "bg-blue-50 text-blue-800 hover:bg-blue-100 border border-blue-200"
                        : "bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200"
                    }`}
                    title={
                      p.is_break
                        ? "Convert this break period back to an instructional lesson period"
                        : "Configure this period as a school break/recess"
                    }
                  >
                    {p.is_break ? "Set as Lesson" : "Set as Break"}
                  </button>
                </div>
              ),
            },
          ]}
        />
      </Card>

      {addingPeriod && (
        <PeriodModal
          onClose={() => setAddingPeriod(false)}
          onSaved={() => {
            setAddingPeriod(false);
            qc.invalidateQueries({ queryKey: ["timetable-periods"] });
            qc.invalidateQueries({ queryKey: ["class-timetable"] });
            qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
            qc.invalidateQueries({ queryKey: ["timetable-workload"] });
          }}
        />
      )}

      {editingPeriod && (
        <PeriodModal
          period={editingPeriod}
          onClose={() => setEditingPeriod(null)}
          onSaved={() => {
            setEditingPeriod(null);
            qc.invalidateQueries({ queryKey: ["timetable-periods"] });
            qc.invalidateQueries({ queryKey: ["class-timetable"] });
            qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
            qc.invalidateQueries({ queryKey: ["timetable-workload"] });
          }}
        />
      )}
    </div>
  );
}

// ==========================================
// Modals
// ==========================================

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

  const [overrideConflicts, setOverrideConflicts] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  type ConflictItem = string | { kind?: string; detail: string; slot_id?: number };
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
          const filtered = (res.conflicts || []).filter((c) => {
            if (slot?.id) {
              return true;
            }
            return true;
          });
          setConflicts(filtered);
        }
      } catch {
        if (active) setConflicts([]);
      }
    }, 250);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [classSectionId, form, slot]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);

    const payload = {
      class_section_id: classSectionId,
      day_of_week: form.day_of_week,
      period_id: Number(form.period_id),
      subject_id: Number(form.subject_id),
      teacher_id: Number(form.teacher_id),
      room: form.room.trim() || null,
      override_conflicts: overrideConflicts,
      override_reason: overrideReason.trim() || undefined,
    };

    try {
      if (slot?.id) {
        await api.rawPut(`/admin/timetable/slots/${slot.id}`, payload);
      } else {
        await api.rawPost("/admin/timetable/slots", payload);
      }
      onSaved();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save timetable slot";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={slot?.id ? "Edit Lesson Slot" : "Add Lesson Slot"} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {saveError && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
            {saveError}
          </div>
        )}

        {conflicts.length > 0 && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
            <span className="font-bold flex items-center gap-1 text-amber-900">
              Scheduling Conflict Detected:
            </span>
            <ul className="list-disc pl-5 space-y-0.5 font-medium">
              {conflicts.map((c, i) => (
                <li key={i}>{typeof c === "string" ? c : c.detail}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Day of Week">
            <select
              className={inputClass}
              value={form.day_of_week}
              onChange={(e) => setForm((f) => ({ ...f, day_of_week: e.target.value }))}
            >
              {DAYS.map((d) => (
                <option key={d.key} value={d.key}>
                  {d.label}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Period / Bell Timing">
            <select
              className={inputClass}
              value={form.period_id}
              onChange={(e) => setForm((f) => ({ ...f, period_id: e.target.value }))}
            >
              {(periods.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  Period {p.period_no} ({p.start_time?.slice(0, 5)} - {p.end_time?.slice(0, 5)})
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Subject">
            <select
              className={inputClass}
              value={form.subject_id}
              onChange={(e) => setForm((f) => ({ ...f, subject_id: e.target.value }))}
            >
              {(subjects.data ?? []).map((s) => (
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
              onChange={(e) => setForm((f) => ({ ...f, teacher_id: e.target.value }))}
            >
              {(teachers.data ?? []).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.full_name} {t.employee_code ? `(${t.employee_code})` : ""}
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Classroom / Room No.">
          <input
            type="text"
            className={inputClass}
            placeholder="e.g. 101, Science Lab 2"
            value={form.room}
            onChange={(e) => setForm((f) => ({ ...f, room: e.target.value }))}
          />
        </FormField>

        {conflicts.length > 0 && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={overrideConflicts}
                onChange={(e) => setOverrideConflicts(e.target.checked)}
                className="rounded text-primary focus:ring-primary"
              />
              <span className="text-xs font-bold text-ink">
                Override Scheduling Conflicts (Coordinator Authorization)
              </span>
            </label>
            {overrideConflicts && (
              <FormField label="Reason for Override">
                <input
                  type="text"
                  required
                  className={inputClass}
                  placeholder="Explain why this scheduling conflict is permitted..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                />
              </FormField>
            )}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-input border border-rule hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || (conflicts.length > 0 && (!overrideConflicts || !overrideReason.trim()))}
            className="px-5 py-2 text-xs font-bold rounded-input bg-primary hover:bg-primary/90 text-white disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Lesson Slot"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ReliefModal({
  slot,
  date,
  onClose,
  onSaved,
}: {
  slot: TimetableSlotItem;
  date: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const freeTeachers = useQuery<FreeTeacher[]>({
    queryKey: ["free-teachers", slot.id, date],
    queryFn: () => api.rawGet<FreeTeacher[]>(`/admin/timetable/slots/${slot.id}/free-teachers?date=${date}`),
  });

  const [subTeacherId, setSubTeacherId] = useState<string>("");
  const [reason, setReason] = useState("Medical Leave / Personal Emergency");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (freeTeachers.data && freeTeachers.data.length > 0 && !subTeacherId) {
      setSubTeacherId(String(freeTeachers.data[0].teacher_id));
    }
  }, [freeTeachers.data, subTeacherId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.rawPost("/admin/timetable/substitutions", {
        slot_id: slot.id,
        date,
        substitute_teacher_id: subTeacherId ? Number(subTeacherId) : null,
        reason,
      });
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to assign substitution");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={`Assign Relief Duty — ${slot.class_label} (Period ${slot.period})`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
            {error}
          </div>
        )}

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1">
          <div><strong>Class:</strong> {slot.class_label}</div>
          <div><strong>Scheduled Subject:</strong> {slot.subject}</div>
          <div><strong>Scheduled Faculty:</strong> {slot.teacher || "Unassigned"}</div>
          <div><strong>Date & Time:</strong> {date} · Period {slot.period} ({slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)})</div>
        </div>

        <FormField label="Available Free Teachers (Ranked by Subject Specialism & Workload)">
          <select
            className={inputClass}
            value={subTeacherId}
            onChange={(e) => setSubTeacherId(e.target.value)}
          >
            <option value="">-- Leave Unfilled (Record Unattended) --</option>
            {(freeTeachers.data ?? []).map((t) => (
              <option key={t.teacher_id} value={t.teacher_id}>
                {t.name} {t.teaches_this_subject ? "★ [Subject Specialist]" : ""} — Load: {t.weekly_load} periods
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Absence / Relief Reason">
          <input
            type="text"
            required
            className={inputClass}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Sick Leave, Duty Leave, Personal Emergency"
          />
        </FormField>

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-input border border-rule hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 text-xs font-bold rounded-input bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50"
          >
            {saving ? "Assigning…" : "Confirm Relief Duty"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function PeriodModal({
  period,
  onClose,
  onSaved,
}: {
  period?: PeriodItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [periodNo, setPeriodNo] = useState(period ? String(period.period_no) : "1");
  const [name, setName] = useState(period?.name || "");
  const [startTime, setStartTime] = useState(period?.start_time ? period.start_time.slice(0, 5) : "08:00");
  const [endTime, setEndTime] = useState(period?.end_time ? period.end_time.slice(0, 5) : "08:45");
  const [isBreak, setIsBreak] = useState(period?.is_break ?? false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        period_no: Number(periodNo),
        name: name.trim() || (isBreak ? "Break" : undefined),
        start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
        end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
        is_break: isBreak,
      };

      if (period?.id) {
        await api.rawPut(`/admin/timetable/periods/${period.id}`, payload);
      } else {
        await api.rawPost("/admin/timetable/periods", payload);
      }
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save period");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={period ? `Configure Period ${period.period_no}` : "Add School Period / Bell Timing"}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Period Number">
            <input
              type="number"
              min="1"
              max="20"
              required
              className={inputClass}
              value={periodNo}
              onChange={(e) => setPeriodNo(e.target.value)}
            />
          </FormField>

          <FormField label="Name / Label (Optional)">
            <input
              type="text"
              className={inputClass}
              placeholder="e.g. Morning Assembly, Recess"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Start Time (HH:MM)">
            <input
              type="time"
              required
              className={inputClass}
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </FormField>

          <FormField label="End Time (HH:MM)">
            <input
              type="time"
              required
              className={inputClass}
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            />
          </FormField>
        </div>

        <label className="flex items-center gap-2 cursor-pointer pt-1">
          <input
            type="checkbox"
            checked={isBreak}
            onChange={(e) => setIsBreak(e.target.checked)}
            className="rounded text-primary focus:ring-primary"
          />
          <span className="text-xs font-bold text-ink">
            Is Break / Recess Period (Non-instructional)
          </span>
        </label>

        <div className="flex items-center justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-input border border-rule hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 text-xs font-bold rounded-input bg-primary hover:bg-primary/90 text-white disabled:opacity-50"
          >
            {saving ? "Saving…" : period ? "Update Period Configuration" : "Add Period"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
