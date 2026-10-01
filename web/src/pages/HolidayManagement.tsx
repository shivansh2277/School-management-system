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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Holiday Management</h1>
          <p className="text-sm text-ink-soft">
            Declare school-wide or section-specific holidays. Normal attendance marking is blocked on declared holidays.
          </p>
        </div>

        {can("attendance.holiday.manage") && (
          <button
            onClick={() => setModalOpen(true)}
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90"
          >
            + Declare New Holiday
          </button>
        )}
      </div>

      <div className="p-4 bg-sky-50 border border-sky-200 rounded-card text-sky-900 text-xs flex items-start gap-3">
        <svg className="w-5 h-5 shrink-0 text-sky-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <strong className="font-semibold">Holiday Attendance Invariant:</strong> Declared holidays prevent teachers from marking attendance in the web ERP and mobile application. Attendance summaries exclude declared holidays from the absence denominator to prevent skewing student attendance percentages.
        </div>
      </div>

      <Card title="Declared Holidays & Vacations">
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
                  <button
                    onClick={() => setCancellingHoliday(r)}
                    className="rounded bg-danger/10 text-danger hover:bg-danger/20 px-2.5 py-1 text-xs font-medium"
                  >
                    Cancel Holiday
                  </button>
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
