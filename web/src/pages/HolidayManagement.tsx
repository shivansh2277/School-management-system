import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { errorText } from "../api/errors";
import { useAuth } from "../auth/AuthContext";
import {
  Card,
  ConfirmDialog,
  DataTable,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../components/ui";
import { useClasses } from "./useClasses";

type HolidayItem = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  description: string | null;
  is_school_wide: boolean;
  status: "active" | "cancelled";
  class_section_ids: number[];
  cancellation_reason: string | null;
};

export function HolidayManagement() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const classes = useClasses();

  // Create Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [holidayName, setHolidayName] = useState("");
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [isSchoolWide, setIsSchoolWide] = useState(true);
  const [selectedSectionIds, setSelectedSectionIds] = useState<number[]>([]);
  const [description, setDescription] = useState("");

  // Cancel Dialog State
  const [cancellingHoliday, setCancellingHoliday] = useState<HolidayItem | null>(null);

  // Edit Modal State
  const [editingHoliday, setEditingHoliday] = useState<HolidayItem | null>(null);
  const [editName, setEditName] = useState("");
  const [editStartDate, setEditStartDate] = useState("");
  const [editEndDate, setEditEndDate] = useState("");
  const [editIsSchoolWide, setEditIsSchoolWide] = useState(true);
  const [editSectionIds, setEditSectionIds] = useState<number[]>([]);
  const [editDescription, setEditDescription] = useState("");

  const openEditModal = (h: HolidayItem) => {
    setEditingHoliday(h);
    setEditName(h.name);
    setEditStartDate(h.start_date);
    setEditEndDate(h.end_date);
    setEditIsSchoolWide(h.is_school_wide);
    setEditSectionIds(h.class_section_ids ?? []);
    setEditDescription(h.description ?? "");
  };

  const handleToggleEditSection = (id: number) => {
    setEditSectionIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  // Queries
  const holidaysQuery = useQuery({
    queryKey: ["admin-holidays"],
    queryFn: () => api.rawGet<HolidayItem[]>("/admin/attendance/holidays"),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: async () => {
      return api.rawPost("/admin/attendance/holidays", {
        name: holidayName.trim(),
        start_date: startDate,
        end_date: endDate,
        description: description.trim() || null,
        is_school_wide: isSchoolWide,
        class_section_ids: isSchoolWide ? [] : selectedSectionIds,
      });
    },
    onSuccess: () => {
      setModalOpen(false);
      setHolidayName("");
      setDescription("");
      setSelectedSectionIds([]);
      setIsSchoolWide(true);
      qc.invalidateQueries({ queryKey: ["admin-holidays"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingHoliday) return;
      return api.rawPut(`/admin/attendance/holidays/${editingHoliday.id}`, {
        name: editName.trim(),
        start_date: editStartDate,
        end_date: editEndDate,
        description: editDescription.trim() || null,
        is_school_wide: editIsSchoolWide,
        class_section_ids: editIsSchoolWide ? [] : editSectionIds,
      });
    },
    onSuccess: () => {
      setEditingHoliday(null);
      qc.invalidateQueries({ queryKey: ["admin-holidays"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async ({ holidayId, reason }: { holidayId: number; reason: string }) => {
      return api.rawPost(`/admin/attendance/holidays/${holidayId}/cancel`, { reason });
    },
    onSuccess: () => {
      setCancellingHoliday(null);
      qc.invalidateQueries({ queryKey: ["admin-holidays"] });
    },
  });

  const handleToggleSection = (id: number) => {
    setSelectedSectionIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  const calculateDays = (start: string, end: string) => {
    const s = new Date(start).getTime();
    const e = new Date(end).getTime();
    if (isNaN(s) || isNaN(e) || e < s) return 1;
    return Math.round((e - s) / (1000 * 3600 * 24)) + 1;
  };

  const holidayList = holidaysQuery.data ?? [];
  const activeHolidaysCount = holidayList.filter((h) => h.status === "active").length;

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Holiday Management</h1>
          <p className="text-xs text-ink-faint mt-0.5">
            Declare school-wide and section-specific holidays to lock roll-call and preserve attendance rates
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {activeHolidaysCount} Active Holidays
          </span>
          {can("attendance.holiday.manage") && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="rounded-input bg-[#042954] hover:bg-[#07366f] px-3.5 py-2 text-white text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
            >
              + Declare New Holiday
            </button>
          )}
        </div>
      </div>

      <div className="p-4 bg-sky-50/80 border border-sky-200/90 rounded-card text-sky-900 text-xs flex items-start gap-3 shadow-2xs">
        <svg className="w-5 h-5 shrink-0 text-sky-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <strong className="font-semibold text-sky-950">Holiday Attendance Invariant:</strong> Declared holidays prevent teachers from marking attendance in the web ERP and mobile application. Attendance summaries exclude declared holidays from the absence denominator to prevent skewing student attendance percentages.
        </div>
      </div>

      <Card title={`Declared Holidays & Vacations (${holidayList.length})`}>
        <DataTable
          rows={holidaysQuery.data ?? []}
          loading={holidaysQuery.isLoading}
          error={holidaysQuery.error}
          empty="No holidays have been declared yet."
          columns={[
            {
              key: "name",
              header: "Holiday Name",
              render: (r) => (
                <div>
                  <p className="font-semibold text-sm text-ink">{r.name}</p>
                  {r.description && <p className="text-xs text-ink-soft">{r.description}</p>}
                </div>
              ),
            },
            {
              key: "dates",
              header: "Date(s)",
              render: (r) => (
                <div>
                  <span className="text-xs font-medium">
                    {r.start_date === r.end_date ? r.start_date : `${r.start_date} → ${r.end_date}`}
                  </span>
                  <span className="text-[11px] text-ink-soft ml-2">
                    ({calculateDays(r.start_date, r.end_date)} day{calculateDays(r.start_date, r.end_date) > 1 ? "s" : ""})
                  </span>
                </div>
              ),
            },
            {
              key: "scope",
              header: "Scope",
              render: (r) =>
                r.is_school_wide ? (
                  <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded font-medium">
                    School-Wide
                  </span>
                ) : (
                  <span className="text-xs bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded font-medium">
                    Specific Sections ({r.class_section_ids?.length ?? 0})
                  </span>
                ),
            },
            {
              key: "status",
              header: "Status",
              render: (r) => (
                <div>
                  <Pill status={r.status}>{r.status}</Pill>
                  {r.status === "cancelled" && r.cancellation_reason && (
                    <p className="text-[11px] text-danger mt-1 italic">Reason: {r.cancellation_reason}</p>
                  )}
                </div>
              ),
            },
            {
              key: "actions",
              header: "Action",
              align: "right",
              render: (r) =>
                r.status === "active" && can("attendance.holiday.manage") ? (
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => openEditModal(r)}
                      className="rounded bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 px-2.5 py-1 text-xs font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setCancellingHoliday(r)}
                      className="rounded bg-danger/10 text-danger hover:bg-danger/20 px-2.5 py-1 text-xs font-medium"
                    >
                      Cancel Holiday
                    </button>
                  </div>
                ) : null,
            },
          ]}
        />
      </Card>

      {/* Declare Holiday Modal */}
      {modalOpen && (
        <Modal title="Declare School Holiday / Vacation" onClose={() => setModalOpen(false)}>
          <div className="space-y-4">
            <FormField label="Holiday Name / Title">
              <input
                type="text"
                className={inputClass}
                placeholder="e.g. Gandhi Jayanti, Diwali Break"
                value={holidayName}
                onChange={(e) => setHolidayName(e.target.value)}
                required
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Start Date">
                <input
                  type="date"
                  className={inputClass}
                  value={startDate}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    if (endDate < e.target.value) setEndDate(e.target.value);
                  }}
                  required
                />
              </FormField>

              <FormField label="End Date">
                <input
                  type="date"
                  className={inputClass}
                  value={endDate}
                  min={startDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  required
                />
              </FormField>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="schoolWideCheck"
                checked={isSchoolWide}
                onChange={(e) => setIsSchoolWide(e.target.checked)}
                className="rounded border-rule text-primary focus:ring-primary"
              />
              <label htmlFor="schoolWideCheck" className="text-sm font-medium text-ink cursor-pointer">
                Applies to all classes and sections (School-Wide Holiday)
              </label>
            </div>

            {!isSchoolWide && (
              <div className="space-y-2 border border-rule rounded p-3 bg-ground">
                <p className="text-xs font-semibold text-ink-soft">Select Applicable Class Sections:</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-40 overflow-y-auto pt-1">
                  {classes.data?.map((c) => (
                    <label key={c.id} className="flex items-center gap-2 text-xs cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedSectionIds.includes(c.id)}
                        onChange={() => handleToggleSection(c.id)}
                        className="rounded border-rule text-primary focus:ring-primary"
                      />
                      <span>{c.class_label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <FormField label="Description / Circular Notes (Optional)">
              <input
                type="text"
                className={inputClass}
                placeholder="Brief administrative reason or circular reference..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </FormField>

            <FormError error={createMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => createMutation.mutate()}
                disabled={
                  createMutation.isPending ||
                  !holidayName.trim() ||
                  (!isSchoolWide && selectedSectionIds.length === 0)
                }
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {createMutation.isPending ? "Declaring..." : "Declare Holiday"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Edit Holiday Modal */}
      {editingHoliday && (
        <Modal title="Edit Declared Holiday" onClose={() => setEditingHoliday(null)}>
          <div className="space-y-4">
            {updateMutation.error && (
              <div className="p-3 bg-danger/10 text-danger text-xs rounded-input">
                {updateMutation.error.message}
              </div>
            )}

            <FormField label="Holiday Name / Title">
              <input
                type="text"
                className={inputClass}
                placeholder="e.g. Gandhi Jayanti, Diwali Break"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Start Date">
                <input
                  type="date"
                  className={inputClass}
                  value={editStartDate}
                  onChange={(e) => {
                    setEditStartDate(e.target.value);
                    if (editEndDate < e.target.value) setEditEndDate(e.target.value);
                  }}
                />
              </FormField>

              <FormField label="End Date">
                <input
                  type="date"
                  className={inputClass}
                  value={editEndDate}
                  min={editStartDate}
                  onChange={(e) => setEditEndDate(e.target.value)}
                />
              </FormField>
            </div>

            <div className="flex items-center gap-2 p-2 bg-ground rounded text-xs text-ink-soft">
              <span>Duration:</span>
              <strong className="text-ink">
                {calculateDays(editStartDate, editEndDate)} day(s)
              </strong>
            </div>

            <FormField label="Description / Reason (Optional)">
              <textarea
                className={`${inputClass} h-16 resize-none`}
                placeholder="Additional notes for parents and staff..."
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
              />
            </FormField>

            <div className="space-y-2 pt-2 border-t border-rule">
              <label className="text-xs font-semibold text-ink uppercase tracking-wider block">
                Holiday Scope
              </label>

              <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
                <input
                  type="radio"
                  name="edit-holiday-scope"
                  checked={editIsSchoolWide}
                  onChange={() => setEditIsSchoolWide(true)}
                  className="accent-primary"
                />
                Applies to all classes and sections (School-Wide Holiday)
              </label>

              <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
                <input
                  type="radio"
                  name="edit-holiday-scope"
                  checked={!editIsSchoolWide}
                  onChange={() => setEditIsSchoolWide(false)}
                  className="accent-primary"
                />
                Specific class sections only (Section-Scoped)
              </label>

              {!editIsSchoolWide && (
                <div className="mt-3 p-3 bg-ground rounded border border-rule max-h-40 overflow-y-auto space-y-1.5">
                  <p className="text-[11px] font-medium text-ink-soft mb-2">
                    Select sections affected by this holiday:
                  </p>
                  {classes.data?.map((c) => (
                    <label key={c.id} className="flex items-center gap-2 text-xs cursor-pointer">
                      <input
                        type="checkbox"
                        checked={editSectionIds.includes(c.id)}
                        onChange={() => handleToggleEditSection(c.id)}
                        className="rounded border-rule text-primary accent-primary"
                      />
                      <span>{c.class_label}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-rule">
              <button
                type="button"
                onClick={() => setEditingHoliday(null)}
                className="rounded-input border border-rule px-4 py-2 text-ink text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => updateMutation.mutate()}
                disabled={
                  updateMutation.isPending ||
                  !editName.trim() ||
                  (!editIsSchoolWide && editSectionIds.length === 0)
                }
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {updateMutation.isPending ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Cancel Holiday Confirm Dialog */}
      {cancellingHoliday && (
        <ConfirmDialog
          title="Cancel Declared Holiday"
          intent={
            <div className="space-y-2 text-sm text-ink-soft">
              <p>
                Are you sure you want to cancel the holiday <strong>{cancellingHoliday.name}</strong> ({cancellingHoliday.start_date} → {cancellingHoliday.end_date})?
              </p>
              <p className="text-xs text-ink-faint">
                Cancelling will re-enable normal attendance marking for the affected dates. An audit record will be logged with your cancellation reason.
              </p>
            </div>
          }
          confirmLabel="Cancel Holiday"
          busy={cancelMutation.isPending}
          error={cancelMutation.error}
          onConfirm={(reason) =>
            cancelMutation.mutate({
              holidayId: cancellingHoliday.id,
              reason,
            })
          }
          onClose={() => setCancellingHoliday(null)}
        />
      )}
    </div>
  );
}
