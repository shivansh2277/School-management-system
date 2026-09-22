import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ActionButton } from "../components/Can";
import { Card, Empty, ErrorState, FormField, FormError, StatCard, inputClass } from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

export interface AcademicYearItem {
  id: number;
  code: string;
  start_date: string;
  end_date: string;
  status: string;
  is_current: boolean;
  is_writable: boolean;
}

export interface PromotionLine {
  student_id: number;
  student_name: string;
  admission_no: string;
  from_roll_no: number;
  outcome: "promote" | "detain" | "pass_out" | "transfer_out";
  to_class_label: string | null;
  to_roll_no: number | null;
  note: string | null;
}

export interface PromotionPreview {
  from_year: string;
  to_year: string;
  from_section: string;
  to_section: string | null;
  lines: PromotionLine[];
  blockers: string[];
  can_commit: boolean;
}

export function SessionRollover() {
  const { me, can } = useAuth();
  const qc = useQueryClient();

  // Wizard Steps: 1 (Select), 2 (Review & Overrides), 3 (Safety Gate), 4 (Completed)
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form & Selection State
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  const [selectedToYearId, setSelectedToYearId] = useState<number | null>(null);
  const [finalClass, setFinalClass] = useState<string>("12");
  const [outcomes, setOutcomes] = useState<Record<number, "promote" | "detain" | "pass_out" | "transfer_out">>({});

  // Safety Confirmation State
  const [confirmText, setConfirmText] = useState("");
  const [auditReason, setAuditReason] = useState("Annual academic session rollover");

  // Fetch Academic Years
  const yearsQuery = useQuery({
    queryKey: ["promotion-years"],
    queryFn: () => api.get("/admin/promotion/years" as "/admin/promotion/years") as Promise<AcademicYearItem[]>,
    enabled: can("academics.class.read"),
  });

  // Fetch Classes for current school
  const { data: classes, isLoading: classesLoading } = useClasses();

  // Selected Section Object
  const selectedSection = useMemo(() => {
    return (classes ?? []).find((c) => c.id === selectedSectionId) || null;
  }, [classes, selectedSectionId]);

  // Target Years (exclude the current source year)
  const availableTargetYears = useMemo(() => {
    if (!yearsQuery.data) return [];
    return yearsQuery.data;
  }, [yearsQuery.data]);

  // Default target year selection
  const activeTargetYear = useMemo(() => {
    if (!selectedToYearId && availableTargetYears.length > 0) {
      // Pick first non-current or planning year, else first available
      const found = availableTargetYears.find((y) => !y.is_current) || availableTargetYears[0];
      return found;
    }
    return availableTargetYears.find((y) => y.id === selectedToYearId) || null;
  }, [availableTargetYears, selectedToYearId]);

  // Preview Query / Mutation
  const previewMutation = useMutation({
    mutationFn: async (payload: {
      class_section_id: number;
      to_year_id: number;
      outcomes?: Record<number, string>;
      final_class?: string;
    }) => {
      return (api.post(
        "/admin/promotion/preview" as "/admin/promotion/preview",
        payload as any,
      ) as unknown) as Promise<PromotionPreview>;
    },
    onSuccess: () => {
      setStep(2);
    },
  });

  // Commit Mutation
  const commitMutation = useMutation({
    mutationFn: async (payload: {
      class_section_id: number;
      to_year_id: number;
      outcomes?: Record<number, string>;
      final_class?: string;
      reason?: string;
    }) => {
      return (api.post(
        "/admin/promotion/commit" as "/admin/promotion/commit",
        payload as any,
      ) as unknown) as Promise<PromotionPreview>;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["classes"] });
      qc.invalidateQueries({ queryKey: ["students"] });
      setStep(4);
    },
  });

  // Handle preview inspection
  const handleInspectPreview = (overrideOutcomes?: Record<number, "promote" | "detain" | "pass_out" | "transfer_out">) => {
    if (!selectedSectionId || !activeTargetYear) return;
    previewMutation.mutate({
      class_section_id: selectedSectionId,
      to_year_id: activeTargetYear.id,
      outcomes: overrideOutcomes ?? outcomes,
      final_class: finalClass,
    });
  };

  // Handle individual outcome change
  const handleOutcomeChange = (studentId: number, newOutcome: "promote" | "detain" | "pass_out" | "transfer_out") => {
    const updated = { ...outcomes, [studentId]: newOutcome };
    setOutcomes(updated);
    handleInspectPreview(updated);
  };

  // Reset outcomes
  const handleResetOutcomes = () => {
    setOutcomes({});
    handleInspectPreview({});
  };

  // Counts from preview lines
  const stats = useMemo(() => {
    const lines = previewMutation.data?.lines ?? [];
    const total = lines.length;
    const promoted = lines.filter((l) => l.outcome === "promote").length;
    const detained = lines.filter((l) => l.outcome === "detain").length;
    const passedOut = lines.filter((l) => l.outcome === "pass_out").length;
    const transferredOut = lines.filter((l) => l.outcome === "transfer_out").length;
    return { total, promoted, detained, passedOut, transferredOut };
  }, [previewMutation.data]);

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header Banner */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-rule pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">Session Rollover &amp; Promotion Wizard</h1>
            <span className="rounded-pill bg-primary/10 text-primary text-xs font-semibold px-2.5 py-0.5">
              CBSE Academic Engine
            </span>
          </div>
          <p className="text-sm text-ink-soft mt-1">
            Batch promote class sections from one academic session to the next with roll number continuity, detention handling, and gapless record retention.
          </p>
        </div>

        {/* Current Session Indicator */}
        <div className="flex items-center gap-2 bg-surface rounded-card p-2.5 border border-rule text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-ink-soft font-medium">Current Session:</span>
          <span className="font-semibold text-ink">{me?.academic_year || "2025-26"}</span>
        </div>
      </header>

      {/* Stepper Wizard Indicator */}
      <nav aria-label="Wizard Steps" className="bg-surface rounded-card shadow-card p-3.5 border border-rule">
        <ol className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-medium">
          <li
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
              step === 1 ? "bg-primary text-white font-semibold shadow-sm" : step > 1 ? "text-primary bg-primary/10" : "text-ink-faint"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${step === 1 ? "bg-white text-primary" : "border border-current"}`}>
              1
            </span>
            <span>1. Select Section</span>
          </li>

          <li
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
              step === 2 ? "bg-primary text-white font-semibold shadow-sm" : step > 2 ? "text-primary bg-primary/10" : "text-ink-faint"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${step === 2 ? "bg-white text-primary" : "border border-current"}`}>
              2
            </span>
            <span>2. Review Roster</span>
          </li>

          <li
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
              step === 3 ? "bg-primary text-white font-semibold shadow-sm" : step > 3 ? "text-primary bg-primary/10" : "text-ink-faint"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${step === 3 ? "bg-white text-primary" : "border border-current"}`}>
              3
            </span>
            <span>3. Safety Gate</span>
          </li>

          <li
            className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${
              step === 4 ? "bg-emerald-600 text-white font-semibold shadow-sm" : "text-ink-faint"
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${step === 4 ? "bg-white text-emerald-600" : "border border-current"}`}>
              4
            </span>
            <span>4. Completed</span>
          </li>
        </ol>
      </nav>

      {/* STEP 1: Select Section & Target Session */}
      {step === 1 && (
        <div className="space-y-6">
          <Card title="Step 1: Select Academic Session & Source Class Section">
            <div className="grid md:grid-cols-2 gap-6 mt-2">
              {/* Target Academic Year Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-ink">
                  Target Academic Session (To Year) <span className="text-danger">*</span>
                </label>
                <select
                  className={inputClass}
                  value={activeTargetYear?.id || ""}
                  onChange={(e) => setSelectedToYearId(Number(e.target.value))}
                >
                  {availableTargetYears.map((y) => (
                    <option key={y.id} value={y.id}>
                      {y.code} {y.is_current ? "(Current Active)" : `(${y.status.toUpperCase()})`}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-ink-faint">
                  The academic session in which promoted students will be newly enrolled. Must be writable/open.
                </p>
              </div>

              {/* Final Class Definition */}
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-ink">
                  Terminal / Graduating Class <span className="text-danger">*</span>
                </label>
                <select
                  className={inputClass}
                  value={finalClass}
                  onChange={(e) => setFinalClass(e.target.value)}
                >
                  <option value="12">Class 12 (Higher Secondary Terminal)</option>
                  <option value="10">Class 10 (Secondary Terminal)</option>
                  <option value="8">Class 8 (Middle School Terminal)</option>
                </select>
                <p className="text-xs text-ink-faint">
                  Students in this class have reached terminal graduation and will automatically pass out instead of promoting.
                </p>
              </div>
            </div>

            {/* Source Class Section Grid */}
            <div className="mt-6 pt-6 border-t border-rule">
              <label className="block text-sm font-semibold text-ink mb-2">
                Choose Source Class Section to Promote <span className="text-danger">*</span>
              </label>
              {classesLoading ? (
                <Empty>Loading classes...</Empty>
              ) : (classes ?? []).length === 0 ? (
                <Empty>No class sections found for your school.</Empty>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {(classes ?? []).map((c) => {
                    const isSelected = selectedSectionId === c.id;
                    return (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => setSelectedSectionId(c.id)}
                        className={`p-3.5 rounded-card text-left transition-all border ${
                          isSelected
                            ? "border-primary ring-2 ring-primary/20 bg-primary-soft"
                            : "border-rule bg-surface hover:bg-ground"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-base text-ink">{c.class_label}</span>
                          <span className="text-xs text-ink-soft bg-canvas px-1.5 py-0.5 rounded border border-rule">
                            {c.student_count}
                          </span>
                        </div>
                        <p className="text-xs text-ink-faint mt-1 truncate">
                          {c.class_teacher || "No teacher"}
                        </p>
                        <p className="text-[10px] text-ink-faint mt-0.5">{c.academic_year}</p>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Selected Section Projection Summary */}
            {selectedSection && (
              <div className="mt-6 p-4 rounded-card bg-canvas border border-rule flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-ink">
                    Promoting: <span className="font-bold text-primary">{selectedSection.class_label}</span> ({selectedSection.student_count} students)
                  </p>
                  <p className="text-xs text-ink-soft mt-0.5">
                    Target Session: <span className="font-semibold">{activeTargetYear?.code}</span> · Target Class Section:{" "}
                    <span className="font-semibold">
                      {selectedSection.class_name === finalClass
                        ? "Pass Out / Graduating"
                        : `${Number(selectedSection.class_name) + 1}-${selectedSection.section}`}
                    </span>
                  </p>
                </div>
                <button
                  type="button"
                  disabled={previewMutation.isPending}
                  onClick={() => handleInspectPreview()}
                  className="rounded-input bg-primary px-5 py-2.5 text-white text-sm font-semibold hover:bg-primary/90 shadow-sm disabled:opacity-60 flex items-center gap-2"
                >
                  {previewMutation.isPending ? "Calculating Projection..." : "Inspect Roster & Next Steps →"}
                </button>
              </div>
            )}

            <FormError error={previewMutation.error} />
          </Card>
        </div>
      )}

      {/* STEP 2: Roster Review & Student Outcome Overrides */}
      {step === 2 && previewMutation.data && (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard label="Total Enrolled" value={stats.total} hint="Source class roster" />
            <StatCard label="Promoted" value={<span className="text-emerald-600">{stats.promoted}</span>} hint="Next class grade" />
            <StatCard label="Detained" value={<span className="text-amber-600">{stats.detained}</span>} hint="Repeating same class" />
            <StatCard label="Passed Out" value={<span className="text-blue-600">{stats.passedOut}</span>} hint="Completed final grade" />
            <StatCard label="Transfer / Left" value={<span className="text-rose-600">{stats.transferredOut}</span>} hint="TC issued / withdrawn" />
          </div>

          {/* Blockers Warning Banner */}
          {previewMutation.data.blockers.length > 0 && (
            <div className="rounded-card bg-danger/10 border border-danger/30 p-4">
              <div className="flex items-start gap-3">
                <span className="text-xl">⚠️</span>
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-danger">Promotion Blockers Detected</h3>
                  <ul className="text-xs text-danger space-y-1 list-disc list-inside">
                    {previewMutation.data.blockers.map((b, idx) => (
                      <li key={idx}>{b}</li>
                    ))}
                  </ul>
                  <p className="text-xs text-danger/80 mt-1">
                    You cannot commit this rollover until the above blockers are resolved (e.g. create missing target section in Classes or check prior promotions).
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Review Table Card */}
          <Card
            title={`Roster Review for Class ${previewMutation.data.from_section} → ${previewMutation.data.to_section || "Final Class"}`}
            action={
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleResetOutcomes}
                  className="text-xs text-ink-soft hover:text-ink px-2.5 py-1.5 rounded border border-rule"
                >
                  Reset All Overrides
                </button>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-xs text-ink-soft hover:text-ink px-2.5 py-1.5 rounded border border-rule"
                >
                  Change Section
                </button>
              </div>
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-faint border-b border-rule bg-canvas/60">
                    <th className="py-2.5 px-3 font-semibold w-16">Roll #</th>
                    <th className="py-2.5 px-3 font-semibold w-28">Adm No</th>
                    <th className="py-2.5 px-3 font-semibold">Student Name</th>
                    <th className="py-2.5 px-3 font-semibold w-36">Outcome Decision</th>
                    <th className="py-2.5 px-3 font-semibold w-32">Target Section</th>
                    <th className="py-2.5 px-3 font-semibold w-24">New Roll #</th>
                    <th className="py-2.5 px-3 font-semibold">Notes / Details</th>
                  </tr>
                </thead>
                <tbody>
                  {previewMutation.data.lines.map((line) => {
                    const isCustom = line.student_id in outcomes;
                    return (
                      <tr
                        key={line.student_id}
                        className={`border-b border-rule last:border-0 hover:bg-canvas/50 ${
                          isCustom ? "bg-primary/5" : ""
                        }`}
                      >
                        <td className="py-2.5 px-3 font-mono text-xs tabular text-ink-soft">
                          {line.from_roll_no}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-xs font-semibold text-ink">
                          {line.admission_no}
                        </td>
                        <td className="py-2.5 px-3 font-medium text-ink">
                          {line.student_name}
                        </td>
                        <td className="py-2.5 px-3">
                          <select
                            className={`rounded-input border px-2 py-1 text-xs font-medium outline-none ${
                              line.outcome === "promote"
                                ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                                : line.outcome === "detain"
                                ? "border-amber-300 bg-amber-50 text-amber-800"
                                : line.outcome === "pass_out"
                                ? "border-blue-300 bg-blue-50 text-blue-800"
                                : "border-rose-300 bg-rose-50 text-rose-800"
                            }`}
                            value={line.outcome}
                            onChange={(e) =>
                              handleOutcomeChange(
                                line.student_id,
                                e.target.value as "promote" | "detain" | "pass_out" | "transfer_out",
                              )
                            }
                          >
                            <option value="promote">Promote</option>
                            <option value="detain">Detain (Repeat)</option>
                            <option value="pass_out">Pass Out (Graduate)</option>
                            <option value="transfer_out">Transfer Out (TC)</option>
                          </select>
                        </td>
                        <td className="py-2.5 px-3 text-xs font-medium text-ink-soft">
                          {line.to_class_label ? (
                            <span className="rounded px-2 py-0.5 bg-primary/10 text-primary font-semibold">
                              {line.to_class_label}
                            </span>
                          ) : (
                            <span className="text-ink-faint">—</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-xs tabular text-ink font-semibold">
                          {line.to_roll_no !== null ? `#${line.to_roll_no}` : "—"}
                        </td>
                        <td className="py-2.5 px-3 text-xs text-ink-soft">
                          {line.note || (line.outcome === "promote" ? "Regular progression" : "—")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Bottom Actions Bar */}
            <div className="mt-6 pt-4 border-t border-rule flex items-center justify-between">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="rounded-input border border-rule px-4 py-2 text-sm text-ink-soft hover:bg-canvas"
              >
                ← Back to Section Picker
              </button>

              <button
                type="button"
                disabled={!previewMutation.data.can_commit}
                onClick={() => setStep(3)}
                className="rounded-input bg-primary px-6 py-2.5 text-white text-sm font-semibold hover:bg-primary/90 shadow-sm disabled:opacity-50 flex items-center gap-2"
                title={previewMutation.data.can_commit ? undefined : "Resolve blockers first"}
              >
                Proceed to Safety Gate Verification →
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* STEP 3: Safety Gate Verification Modal / View */}
      {step === 3 && previewMutation.data && (
        <div className="max-w-2xl mx-auto space-y-6">
          <Card title="Step 3: Critical Safety Gate & Audit Verification">
            <div className="space-y-4">
              <div className="rounded-card bg-amber-50 border border-amber-200 p-4 text-amber-900 space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-900 text-base">
                  <span>🛡️</span>
                  <span>Irreversible Academic Transition</span>
                </div>
                <p className="text-xs leading-relaxed text-amber-800">
                  Year-end promotion generates live enrolment rows in academic session{" "}
                  <strong>{previewMutation.data.to_year}</strong> and marks existing records in{" "}
                  <strong>{previewMutation.data.from_year}</strong> as completed. Historical attendance,
                  grades, and ledger snapshots remain immutable.
                </p>
              </div>

              <div className="border border-rule rounded-card p-4 space-y-2 bg-surface text-xs">
                <div className="font-semibold text-ink text-sm">Promotion Execution Summary:</div>
                <div className="grid grid-cols-2 gap-2 text-ink-soft pt-1">
                  <div>Source Section: <strong className="text-ink">{previewMutation.data.from_section} ({previewMutation.data.from_year})</strong></div>
                  <div>Target Session: <strong className="text-ink">{previewMutation.data.to_year}</strong></div>
                  <div>Students to Promote: <strong className="text-emerald-700 font-semibold">{stats.promoted}</strong></div>
                  <div>Students to Detain: <strong className="text-amber-700 font-semibold">{stats.detained}</strong></div>
                  <div>Pass Out / Graduating: <strong className="text-blue-700 font-semibold">{stats.passedOut}</strong></div>
                  <div>Transfer Out (TC): <strong className="text-rose-700 font-semibold">{stats.transferredOut}</strong></div>
                </div>
              </div>

              {/* Audit Reason */}
              <FormField label="Audit Trail Reason (Mandatory)">
                <input
                  type="text"
                  className={inputClass}
                  value={auditReason}
                  onChange={(e) => setAuditReason(e.target.value)}
                  placeholder="e.g. Annual Academic Rollover 2025-26"
                />
              </FormField>

              {/* Safety Typed Confirmation */}
              <div className="space-y-1 pt-2">
                <label className="block text-xs font-semibold text-ink">
                  Type <span className="font-mono font-bold text-danger px-1 bg-danger/10 rounded">PROMOTE</span> to confirm:
                </label>
                <input
                  type="text"
                  className={`${inputClass} font-mono tracking-wider uppercase font-bold`}
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value.trim().toUpperCase())}
                  placeholder="PROMOTE"
                />
              </div>

              <FormError error={commitMutation.error} />

              {/* Action Buttons */}
              <div className="pt-4 border-t border-rule flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="rounded-input border border-rule px-4 py-2 text-sm text-ink-soft hover:bg-canvas"
                >
                  ← Back to Review
                </button>

                <ActionButton
                  permission="students.enrolment.promote"
                  disabled={confirmText !== "PROMOTE" || !auditReason.trim() || commitMutation.isPending}
                  onClick={() => {
                    if (!selectedSectionId || !activeTargetYear) return;
                    commitMutation.mutate({
                      class_section_id: selectedSectionId,
                      to_year_id: activeTargetYear.id,
                      outcomes,
                      final_class: finalClass,
                      reason: auditReason,
                    });
                  }}
                  variant="primary"
                  className="px-6 py-2.5 font-bold"
                >
                  {commitMutation.isPending ? "Executing Promotion..." : "Commit Promotion Now"}
                </ActionButton>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* STEP 4: Success & Summary */}
      {step === 4 && (
        <div className="max-w-xl mx-auto space-y-6">
          <Card>
            <div className="text-center py-6 space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-3xl">
                ✓
              </div>
              <div>
                <h2 className="text-xl font-bold text-ink">Promotion Successfully Completed!</h2>
                <p className="text-xs text-ink-soft mt-1">
                  Enrolments have been created in the target academic session with continuous roll numbers.
                </p>
              </div>

              <div className="bg-canvas border border-rule rounded-card p-4 text-left text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-ink-soft">Processed Section:</span>
                  <span className="font-semibold text-ink">{selectedSection?.class_label} ({previewMutation.data?.from_year})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Target Academic Session:</span>
                  <span className="font-semibold text-ink">{previewMutation.data?.to_year}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Promoted Students:</span>
                  <span className="font-semibold text-emerald-600">{stats.promoted}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Detained / Repeating:</span>
                  <span className="font-semibold text-amber-600">{stats.detained}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Passed Out:</span>
                  <span className="font-semibold text-blue-600">{stats.passedOut}</span>
                </div>
              </div>

              <div className="pt-4 flex flex-col sm:flex-row gap-2 justify-center">
                <button
                  type="button"
                  onClick={() => {
                    setStep(1);
                    setSelectedSectionId(null);
                    setOutcomes({});
                    setConfirmText("");
                  }}
                  className="rounded-input bg-primary px-5 py-2.5 text-white text-sm font-semibold hover:bg-primary/90 shadow-sm"
                >
                  Promote Another Section
                </button>
                <Link
                  to="/classes"
                  className="rounded-input border border-rule px-4 py-2.5 text-sm text-ink-soft hover:bg-canvas text-center"
                >
                  View Classes Directory
                </Link>
                <Link
                  to="/reports"
                  className="rounded-input border border-rule px-4 py-2.5 text-sm text-ink-soft hover:bg-canvas text-center"
                >
                  Reports Library
                </Link>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
