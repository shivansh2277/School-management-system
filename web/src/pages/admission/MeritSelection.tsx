import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { ActionButton } from "../../components/Can";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../../components/ui";
import { useClasses } from "../useClasses";
import type {
  AdmissionCycle,
  MeritApplicant,
  MeritResponse,
} from "./types";

export function MeritSelection() {
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);

  // Selection checkboxes for batch decisions
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showSingleModal, setShowSingleModal] = useState(false);
  const [singleTarget, setSingleTarget] = useState<MeritApplicant | null>(null);

  // Cycles
  const cyclesQuery = useQuery({
    queryKey: ["admission-cycles"],
    queryFn: () =>
      api.get("/admin/admission/cycles") as Promise<AdmissionCycle[]>,
  });

  const cycles = cyclesQuery.data ?? [];
  const activeCycle =
    cycles.find((c) => c.id === selectedCycleId) ??
    cycles.find((c) => c.status === "open") ??
    cycles[0] ??
    null;
  const cycleId = activeCycle?.id ?? null;

  const cycleClassesQuery = useQuery({
    queryKey: ["admission-cycle-classes", cycleId],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/classes` as "/admin/admission/cycles/{cycle_id}/classes",
      ) as Promise<{ id: number; class_name: string }[]>,
    enabled: cycleId !== null,
  });

  const classesQuery = useClasses();
  const availableClasses: { id: string | number; class_name: string }[] =
    classesQuery.data && classesQuery.data.length > 0
      ? classesQuery.data
      : cycleClassesQuery.data && cycleClassesQuery.data.length > 0
      ? cycleClassesQuery.data
      : [
          { id: "1", class_name: "1" },
          { id: "6", class_name: "6" },
          { id: "9", class_name: "9" },
        ];
  const defaultClass = availableClasses[0]?.class_name ?? "1";
  const [selectedClass, setSelectedClass] = useState<string>("");
  const activeClass = selectedClass || defaultClass;

  // Merit List query
  const meritQuery = useQuery({
    queryKey: ["admission-merit", cycleId, activeClass],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/merit` as "/admin/admission/cycles/{cycle_id}/merit",
        `?class_name=${encodeURIComponent(activeClass)}`,
      ) as Promise<MeritResponse>,
    enabled: cycleId !== null && activeClass.length > 0,
  });

  // Batch decision form
  const [batchForm, setBatchForm] = useState({
    decision: "admitted",
    reason: "Selected in top merit ranking quota.",
    seat_category: "general",
    over_allocation_approved: false,
  });

  const runBatchDecisions = useWrite({
    write: (data: typeof batchForm) =>
      api.post(
        `/admin/admission/cycles/${cycleId}/decisions` as "/admin/admission/cycles/{cycle_id}/decisions",
        {
          decisions: selectedAppIds.map((id) => ({
            application_id: id,
            decision: data.decision,
            reason: data.reason,
            seat_category: data.seat_category || undefined,
            over_allocation_approved: data.over_allocation_approved,
          })),
        } as any,
      ),
    invalidates: [
      ["admission-merit", cycleId, activeClass],
      ["admission-applications"],
      ["admission-seats", cycleId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => {
      setShowBatchModal(false);
      setSelectedAppIds([]);
    },
  });

  // Single decision form
  const [singleForm, setSingleForm] = useState({
    decision: "admitted",
    reason: "Candidate qualified on merit score.",
    seat_category: "general",
    over_allocation_approved: false,
  });

  const runSingleDecision = useWrite({
    write: (data: typeof singleForm) =>
      api.post(
        `/admin/admission/applications/${singleTarget!.application_id}/decision` as "/admin/admission/applications/{application_id}/decision",
        {
          decision: data.decision as any,
          reason: data.reason,
          seat_category: data.seat_category || undefined,
          over_allocation_approved: data.over_allocation_approved,
        } as any,
      ),
    invalidates: [
      ["admission-merit", cycleId, activeClass],
      ["admission-applications"],
      ["admission-seats", cycleId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => {
      setShowSingleModal(false);
      setSingleTarget(null);
    },
  });

  const applicants = meritQuery.data?.applicants ?? [];
  const seats = meritQuery.data?.seats ?? null;

  const toggleSelectAll = () => {
    if (selectedAppIds.length === applicants.length) {
      setSelectedAppIds([]);
    } else {
      setSelectedAppIds(applicants.map((a) => a.application_id));
    }
  };

  const toggleSelectOne = (id: number) => {
    if (selectedAppIds.includes(id)) {
      setSelectedAppIds(selectedAppIds.filter((x) => x !== id));
    } else {
      setSelectedAppIds([...selectedAppIds, id]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Merit Ranking & Selection</h1>
        </div>

        <div className="flex items-center gap-3">
          <select
            className={`${inputClass} w-auto font-medium py-1.5`}
            value={activeCycle?.id ?? ""}
            onChange={(e) => setSelectedCycleId(Number(e.target.value))}
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.academic_year})
              </option>
            ))}
          </select>

          <select
            className={`${inputClass} w-auto font-medium py-1.5`}
            value={activeClass}
            onChange={(e) => {
              setSelectedClass(e.target.value);
              setSelectedAppIds([]);
            }}
          >
            {availableClasses.map((c) => (
              <option key={c.id} value={c.class_name}>
                {c.class_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Seat Allocation Quota Banner */}
      {seats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 bg-surface p-4 rounded-card shadow-card border border-rule">
          <div>
            <p className="text-xs text-ink-faint">Class Intake Capacity</p>
            <p className="text-2xl font-bold text-ink tabular mt-0.5">
              {seats.total_seats}
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-faint">General Seats</p>
            <p className="text-2xl font-bold text-ink tabular mt-0.5">
              {seats.general_seats}
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-faint">Reserved Seats</p>
            <p className="text-2xl font-bold text-ink tabular mt-0.5">
              {Object.values(seats.reserved_seats || (seats as any).reserved || {}).reduce((a: number, b: any) => a + Number(b), 0)}
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-faint">Seats Admitted</p>
            <p className="text-2xl font-bold text-ink tabular mt-0.5">
              {seats.filled_total ?? (seats as any).taken ?? 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-faint">Seats Remaining</p>
            <p
              className={`text-2xl font-bold tabular mt-0.5 ${
                (seats.remaining_total ?? (seats as any).available ?? 0) > 0 ? "text-success" : "text-danger"
              }`}
            >
              {seats.remaining_total ?? (seats as any).available ?? 0}
            </p>
          </div>
        </div>
      )}

      {/* Batch Action Bar */}
      {selectedAppIds.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-primary/10 border border-primary/30 rounded-input">
          <span className="text-sm font-semibold text-primary">
            {selectedAppIds.length} applicant(s) selected
          </span>
          <ActionButton
            permission="admission.decision.make"
            onClick={() => {
              setBatchForm({
                decision: "admitted",
                reason: `Top merit list selection for Class ${activeClass}`,
                seat_category: "general",
                over_allocation_approved: false,
              });
              setShowBatchModal(true);
            }}
          >
            Batch decide selected →
          </ActionButton>
        </div>
      )}

      {/* Merit Table */}
      <Card>
        <DataTable<MeritApplicant>
          loading={meritQuery.isLoading}
          error={meritQuery.error}
          empty={`No ranked applicants found for Class ${activeClass} in this cycle.`}
          columns={[
            {
              key: "select",
              header: "",
              render: (r) => (
                <input
                  type="checkbox"
                  checked={selectedAppIds.includes(r.application_id)}
                  onChange={() => toggleSelectOne(r.application_id)}
                />
              ),
            },
            {
              key: "rank",
              header: "Rank",
              render: (r) => (
                <span className="font-bold text-ink tabular">
                  #{r.rank ?? (r as any).priority ?? "—"}
                </span>
              ),
            },
            {
              key: "application_no",
              header: "App No",
              render: (r) => (
                <span className="font-mono text-xs font-semibold text-primary">
                  {r.application_no}
                </span>
              ),
            },
            {
              key: "name",
              header: "Applicant Name",
              render: (r) => (
                <div>
                  <p className="font-semibold text-ink">{r.name}</p>
                  <p className="text-xs text-ink-soft capitalize">
                    Category: {r.category}
                  </p>
                </div>
              ),
            },
            {
              key: "scores",
              header: "Scores (Test / Interview)",
              render: (r) => {
                const total = r.total_score ?? (r as any).composite;
                const testScore = r.assessment_score ?? (r as any).assessment_percent;
                return (
                  <div>
                    <p className="font-semibold text-ink tabular">
                      Total: {total !== null && total !== undefined ? `${total}%` : "—"}
                    </p>
                    <p className="text-xs text-ink-soft">
                      Test: {testScore !== null && testScore !== undefined ? `${testScore}%` : "—"} | Interview:{" "}
                      {r.interview_score ?? "—"}
                    </p>
                  </div>
                );
              },
            },
            {
              key: "claims",
              header: "Verified Claims",
              render: (r) => (
                <div className="flex flex-wrap gap-1">
                  {r.sibling_verified ? (
                    <span className="text-2xs bg-success/15 text-success font-semibold px-1.5 py-0.5 rounded">
                      Sibling ✓
                    </span>
                  ) : null}
                  {r.staff_ward_verified ? (
                    <span className="text-2xs bg-success/15 text-success font-semibold px-1.5 py-0.5 rounded">
                      Staff Ward ✓
                    </span>
                  ) : null}
                  {!r.sibling_verified && !r.staff_ward_verified && (
                    <span className="text-xs text-ink-faint">None</span>
                  )}
                </div>
              ),
            },
            {
              key: "status",
              header: "Current Status",
              render: (r) => (
                <Pill
                  status={
                    r.status === "admitted" || r.status === "enrolled"
                      ? "present"
                      : r.status === "rejected"
                        ? "absent"
                        : "pending"
                  }
                >
                  {r.status.replace(/_/g, " ").toUpperCase()}
                </Pill>
              ),
            },
            {
              key: "action",
              header: "",
              align: "right",
              render: (r) => (
                <ActionButton
                  permission="admission.decision.make"
                  className="px-2.5 py-0.5 text-xs"
                  onClick={() => {
                    setSingleTarget(r);
                    setSingleForm({
                      decision: "admitted",
                      reason: `Admitted on merit rank #${applicants.indexOf(r) + 1}`,
                      seat_category: r.category || "general",
                      over_allocation_approved: false,
                    });
                    setShowSingleModal(true);
                  }}
                >
                  Decide
                </ActionButton>
              ),
            },
          ]}
          rows={applicants}
        />
      </Card>

      {/* Modal: Batch Decision */}
      {showBatchModal && (
        <Modal
          title={`Batch Decide ${selectedAppIds.length} Applicants`}
          onClose={() => setShowBatchModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              runBatchDecisions.run(batchForm);
            }}
            className="space-y-4"
          >
            <FormField label="Decision Outcome">
              <select
                className={inputClass}
                value={batchForm.decision}
                onChange={(e) =>
                  setBatchForm({
                    ...batchForm,
                    decision: e.target.value as any,
                  })
                }
              >
                <option value="admitted">Admit All Selected</option>
                <option value="waitlisted">Place All on Waitlist</option>
                <option value="rejected">Reject All Selected</option>
              </select>
            </FormField>

            <FormField
              label="Common Audit Reason (Recorded against each applicant)"
              error={runBatchDecisions.fields["reason"]}
            >
              <textarea
                required
                className={inputClass}
                rows={3}
                placeholder="e.g. Approved merit list round 1 for Class 1..."
                value={batchForm.reason}
                onChange={(e) =>
                  setBatchForm({ ...batchForm, reason: e.target.value })
                }
              />
            </FormField>

            <FormField label="Seat Quota Category">
              <select
                className={inputClass}
                value={batchForm.seat_category}
                onChange={(e) =>
                  setBatchForm({
                    ...batchForm,
                    seat_category: e.target.value,
                  })
                }
              >
                <option value="general">General</option>
                <option value="sibling">Sibling</option>
                <option value="staff_ward">Staff Ward</option>
                <option value="rte">RTE</option>
                <option value="management">Management</option>
              </select>
            </FormField>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={batchForm.over_allocation_approved}
                  onChange={(e) =>
                    setBatchForm({
                      ...batchForm,
                      over_allocation_approved: e.target.checked,
                    })
                  }
                />
                Over-allocation Approved (Requires admission.decision.override)
              </label>
            </div>

            <FormError error={runBatchDecisions.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowBatchModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={runBatchDecisions.busy || !batchForm.reason.trim()}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {runBatchDecisions.busy
                  ? "Processing batch..."
                  : `Apply to ${selectedAppIds.length} Applicants`}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Single Applicant Decision */}
      {showSingleModal && singleTarget && (
        <Modal
          title={`Decide: ${singleTarget.name} (${singleTarget.application_no})`}
          onClose={() => {
            setShowSingleModal(false);
            setSingleTarget(null);
          }}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              runSingleDecision.run(singleForm);
            }}
            className="space-y-4"
          >
            <FormField label="Decision Outcome">
              <select
                className={inputClass}
                value={singleForm.decision}
                onChange={(e) =>
                  setSingleForm({
                    ...singleForm,
                    decision: e.target.value as any,
                  })
                }
              >
                <option value="admitted">Admit Applicant</option>
                <option value="waitlisted">Place on Waitlist</option>
                <option value="rejected">Reject Application</option>
              </select>
            </FormField>

            <FormField
              label="Mandatory Reason"
              error={runSingleDecision.fields["reason"]}
            >
              <textarea
                required
                className={inputClass}
                rows={3}
                value={singleForm.reason}
                onChange={(e) =>
                  setSingleForm({ ...singleForm, reason: e.target.value })
                }
              />
            </FormField>

            <FormField label="Seat Category">
              <select
                className={inputClass}
                value={singleForm.seat_category}
                onChange={(e) =>
                  setSingleForm({
                    ...singleForm,
                    seat_category: e.target.value,
                  })
                }
              >
                <option value="general">General</option>
                <option value="sibling">Sibling Quota</option>
                <option value="staff_ward">Staff Ward Quota</option>
                <option value="rte">RTE</option>
                <option value="management">Management</option>
              </select>
            </FormField>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={singleForm.over_allocation_approved}
                  onChange={(e) =>
                    setSingleForm({
                      ...singleForm,
                      over_allocation_approved: e.target.checked,
                    })
                  }
                />
                Over-allocation Approved (Requires admission.decision.override)
              </label>
            </div>

            <FormError error={runSingleDecision.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => {
                  setShowSingleModal(false);
                  setSingleTarget(null);
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={runSingleDecision.busy || !singleForm.reason.trim()}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {runSingleDecision.busy ? "Saving..." : "Record Decision"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
