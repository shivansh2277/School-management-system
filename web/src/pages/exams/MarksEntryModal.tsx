import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";

import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { useAuth } from "../../auth/AuthContext";
import { ActionButton } from "../../components/Can";
import { Modal, inputClass } from "../../components/ui";

export type PaperSchedule = {
  id: number;
  exam_id: number;
  exam_name: string;
  class_section_id: number;
  class_label: string;
  subject_id: number;
  subject: string;
  exam_date: string;
  start_time?: string | null;
  max_marks: number | string;
  marks_entered: boolean;
  marks_locked: boolean;
};

type MarkRowState = {
  student_id: number;
  full_name: string;
  roll_no: number;
  marks_obtained: string;
  is_absent: boolean;
  is_exempted: boolean;
  remarks: string;
};

export function MarksEntryModal({
  paper,
  onClose,
}: {
  paper: PaperSchedule;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { can } = useAuth();
  const maxMarks = Number(paper.max_marks) || 100;

  const [rows, setRows] = useState<MarkRowState[]>([]);
  const [overrideReason, setOverrideReason] = useState("");
  const [showLockConfirm, setShowLockConfirm] = useState(false);
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [unlockReason, setUnlockReason] = useState("");
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const marksQuery = useQuery({
    queryKey: ["paper-marks", paper.id],
    queryFn: () =>
      api.get(`/admin/exams/papers/${paper.id}/marks` as "/admin/exams/papers/{exam_schedule_id}/marks") as Promise<{
        student_id: number;
        full_name: string;
        roll_no: number;
        marks_obtained: number | string | null;
        is_absent: boolean;
        is_exempted: boolean;
        remarks: string | null;
      }[]>,
  });

  useEffect(() => {
    if (marksQuery.data) {
      setRows(
        marksQuery.data.map((r) => ({
          student_id: r.student_id,
          full_name: r.full_name,
          roll_no: r.roll_no,
          marks_obtained: r.marks_obtained !== null && r.marks_obtained !== undefined ? String(r.marks_obtained) : "",
          is_absent: r.is_absent || false,
          is_exempted: r.is_exempted || false,
          remarks: r.remarks || "",
        })),
      );
    }
  }, [marksQuery.data]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      // Validate entries
      for (const r of rows) {
        if (r.marks_obtained.trim() !== "") {
          const val = Number(r.marks_obtained);
          if (isNaN(val) || val < 0 || val > maxMarks) {
            throw new Error(`Invalid score for ${r.full_name}: must be between 0 and ${maxMarks}`);
          }
        }
      }

      if (paper.marks_locked && !overrideReason.trim()) {
        throw new Error("A reason is required to change marks while the paper is locked.");
      }

      const entries = rows.map((r) => ({
        student_id: r.student_id,
        marks_obtained: r.marks_obtained.trim() !== "" && !r.is_absent && !r.is_exempted ? Number(r.marks_obtained) : null,
        is_absent: r.is_absent,
        is_exempted: r.is_exempted,
        remarks: r.remarks.trim() || null,
      }));

      return api.post(`/admin/exams/papers/${paper.id}/marks` as "/admin/exams/papers/{exam_schedule_id}/marks", {
        exam_schedule_id: paper.id,
        entries,
        reason: paper.marks_locked ? overrideReason.trim() : null,
      } as any);
    },
    onSuccess: () => {
      setStatusMessage({ type: "success", text: "Marks successfully saved and audited." });
      setOverrideReason("");
      qc.invalidateQueries({ queryKey: ["paper-marks", paper.id] });
      qc.invalidateQueries({ queryKey: ["exam-schedule", paper.exam_id] });
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: (err) => {
      setStatusMessage({ type: "error", text: errorText(err) });
    },
  });

  const lockMutation = useMutation({
    mutationFn: () =>
      (api.post as any)(`/admin/exams/papers/${paper.id}/lock`),
    onSuccess: () => {
      setShowLockConfirm(false);
      setStatusMessage({ type: "success", text: "Paper has been locked. Further edits will require an audited override reason." });
      qc.invalidateQueries({ queryKey: ["exam-schedule", paper.exam_id] });
      qc.invalidateQueries({ queryKey: ["paper-marks", paper.id] });
    },
    onError: (err) => {
      setStatusMessage({ type: "error", text: errorText(err) });
    },
  });

  const unlockMutation = useMutation({
    mutationFn: () =>
      api.post(`/admin/exams/papers/${paper.id}/unlock` as "/admin/exams/papers/{exam_schedule_id}/unlock", {
        reason: unlockReason.trim(),
      } as any),
    onSuccess: () => {
      setShowUnlockModal(false);
      setUnlockReason("");
      setStatusMessage({ type: "success", text: "Paper unlocked successfully." });
      qc.invalidateQueries({ queryKey: ["exam-schedule", paper.exam_id] });
      qc.invalidateQueries({ queryKey: ["paper-marks", paper.id] });
    },
    onError: (err) => {
      setStatusMessage({ type: "error", text: errorText(err) });
    },
  });

  const updateRow = (index: number, patch: Partial<MarkRowState>) => {
    setRows((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], ...patch };
      return copy;
    });
  };

  const filledCount = rows.filter((r) => r.marks_obtained !== "" || r.is_absent || r.is_exempted).length;
  const absentCount = rows.filter((r) => r.is_absent).length;
  const exemptedCount = rows.filter((r) => r.is_exempted).length;
  const scoredCount = rows.filter((r) => r.marks_obtained !== "" && !r.is_absent && !r.is_exempted).length;

  return (
    <Modal title={`Marks Entry: ${paper.subject} (${paper.class_label})`} onClose={onClose} wide>
      <div className="space-y-4">
        {/* Header Information Bar */}
        <div className="bg-ground rounded-card p-4 flex flex-wrap items-center justify-between gap-3 text-sm">
          <div>
            <span className="text-ink-faint">Exam:</span> <span className="font-semibold text-ink">{paper.exam_name}</span>
            <span className="mx-2 text-rule">•</span>
            <span className="text-ink-faint">Max Marks:</span> <span className="font-semibold text-ink">{maxMarks}</span>
            <span className="mx-2 text-rule">•</span>
            <span className="text-ink-faint">Date:</span> <span className="font-semibold text-ink">{paper.exam_date}</span>
          </div>

          <div className="flex items-center gap-3">
            {paper.marks_locked ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill bg-amber-100 text-amber-800 text-xs font-semibold">
                🔒 Paper Locked
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill bg-emerald-100 text-emerald-800 text-xs font-semibold">
                🟢 Open for Entry
              </span>
            )}

            {/* Lock / Unlock Actions */}
            {paper.marks_locked ? (
              <ActionButton
                permission="exam.marks.lock"
                className="px-3 py-1 text-xs"
                onClick={() => setShowUnlockModal(true)}
              >
                Unlock Paper...
              </ActionButton>
            ) : (
              <ActionButton
                permission="exam.marks.lock"
                className="px-3 py-1 text-xs"
                disabled={filledCount === 0}
                onClick={() => setShowLockConfirm(true)}
              >
                Lock Paper
              </ActionButton>
            )}
          </div>
        </div>

        {/* Lock Warning & Audited Override Notice */}
        {paper.marks_locked && (
          <div className="rounded-input bg-amber-50 border border-amber-200 p-3.5 text-xs text-amber-900 space-y-2">
            <p className="font-medium">
              ⚠️ This paper is closed and locked (§5.4.7). Any changes will be recorded in the audit trail alongside the previous mark.
            </p>
            {can("exam.marks.override") ? (
              <div className="space-y-1 pt-1">
                <label className="font-semibold block text-ink">
                  Audit Override Reason <span className="text-danger">*</span>:
                </label>
                <input
                  className={`${inputClass} bg-surface`}
                  placeholder="e.g. Re-evaluation request approved by Moderation Committee"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                />
              </div>
            ) : (
              <p className="text-danger font-semibold">
                Your role does not hold the override permission (`exam.marks.override`). You cannot change marks while the paper is locked.
              </p>
            )}
          </div>
        )}

        {/* Status Toast */}
        {statusMessage && (
          <div
            className={`p-3 rounded-input text-xs font-medium ${
              statusMessage.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-red-50 text-danger border border-red-200"
            }`}
          >
            {statusMessage.text}
          </div>
        )}

        {/* Roster Stats */}
        <div className="flex items-center justify-between text-xs text-ink-faint px-1">
          <span>
            Total students: <b className="text-ink">{rows.length}</b> | Scored: <b className="text-ink">{scoredCount}</b> | Absent: <b className="text-ink">{absentCount}</b> | Exempted: <b className="text-ink">{exemptedCount}</b>
          </span>
          <span>Max score allowed: {maxMarks}</span>
        </div>

        {/* Marks Entry Grid */}
        <div className="border border-rule rounded-card overflow-hidden max-h-[50vh] overflow-y-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-ground sticky top-0 border-b border-rule text-xs text-ink-faint">
              <tr>
                <th className="py-2.5 px-3 w-16">Roll</th>
                <th className="py-2.5 px-3">Student Name</th>
                <th className="py-2.5 px-3 w-32">Marks (/{maxMarks})</th>
                <th className="py-2.5 px-3 w-20 text-center">Absent</th>
                <th className="py-2.5 px-3 w-24 text-center">Exempted</th>
                <th className="py-2.5 px-3">Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {marksQuery.isLoading && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-faint text-sm">
                    Loading student roster...
                  </td>
                </tr>
              )}
              {!marksQuery.isLoading && rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-faint text-sm">
                    No active students found in this class section.
                  </td>
                </tr>
              )}
              {rows.map((row, idx) => {
                const isLockedWithoutOverride = paper.marks_locked && !can("exam.marks.override");
                return (
                  <tr key={row.student_id} className="hover:bg-ground/50">
                    <td className="py-2 px-3 tabular font-medium text-ink-soft">
                      {row.roll_no || "-"}
                    </td>
                    <td className="py-2 px-3 font-medium text-ink">
                      {row.full_name}
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        max={maxMarks}
                        placeholder="-"
                        disabled={row.is_absent || row.is_exempted || isLockedWithoutOverride}
                        value={row.marks_obtained}
                        onChange={(e) => updateRow(idx, { marks_obtained: e.target.value })}
                        className={`${inputClass} !py-1 text-sm ${
                          row.is_absent || row.is_exempted ? "opacity-40 bg-ground" : ""
                        }`}
                      />
                    </td>
                    <td className="py-2 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={row.is_absent}
                        disabled={isLockedWithoutOverride}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          updateRow(idx, {
                            is_absent: checked,
                            is_exempted: checked ? false : row.is_exempted,
                            marks_obtained: checked ? "" : row.marks_obtained,
                          });
                        }}
                        className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                      />
                    </td>
                    <td className="py-2 px-3 text-center">
                      <input
                        type="checkbox"
                        checked={row.is_exempted}
                        disabled={isLockedWithoutOverride}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          updateRow(idx, {
                            is_exempted: checked,
                            is_absent: checked ? false : row.is_absent,
                            marks_obtained: checked ? "" : row.marks_obtained,
                          });
                        }}
                        className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="text"
                        placeholder="Optional remarks"
                        disabled={isLockedWithoutOverride}
                        value={row.remarks}
                        onChange={(e) => updateRow(idx, { remarks: e.target.value })}
                        className={`${inputClass} !py-1 text-xs`}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-ink-soft hover:text-ink font-medium"
          >
            Close
          </button>

          <div className="flex items-center gap-2">
            <ActionButton
              permission="exam.marks.manage_any"
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || (paper.marks_locked && !can("exam.marks.override"))}
            >
              {saveMutation.isPending ? "Saving..." : paper.marks_locked ? "Save Audited Override" : "Save Marks"}
            </ActionButton>
          </div>
        </div>
      </div>

      {/* Confirmation to Lock Paper */}
      {showLockConfirm && (
        <Modal title="Lock Paper Marks Entry?" onClose={() => setShowLockConfirm(false)}>
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              Once locked, marks entry is closed. Any future mark correction will require an exam controller's override and will be logged in the permanent audit trail with old and new values.
            </p>
            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowLockConfirm(false)}
              >
                Cancel
              </button>
              <ActionButton
                permission="exam.marks.lock"
                disabled={lockMutation.isPending}
                onClick={() => lockMutation.mutate()}
              >
                {lockMutation.isPending ? "Locking..." : "Confirm & Lock Paper"}
              </ActionButton>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal to Unlock Paper */}
      {showUnlockModal && (
        <Modal title="Unlock Exam Paper" onClose={() => setShowUnlockModal(false)}>
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              Reopening this paper will allow subject teachers to enter or edit marks without individual override reasons. This action is audited.
            </p>
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-ink">
                Unlock Reason <span className="text-danger">*</span>:
              </label>
              <textarea
                className={`${inputClass} min-h-[80px]`}
                placeholder="State why this paper is being unlocked (e.g. Mass re-evaluation following syllabus revision)"
                value={unlockReason}
                onChange={(e) => setUnlockReason(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowUnlockModal(false)}
              >
                Cancel
              </button>
              <ActionButton
                permission="exam.marks.lock"
                disabled={unlockReason.trim().length < 3 || unlockMutation.isPending}
                onClick={() => unlockMutation.mutate()}
              >
                {unlockMutation.isPending ? "Unlocking..." : "Confirm & Unlock"}
              </ActionButton>
            </div>
          </div>
        </Modal>
      )}
    </Modal>
  );
}
