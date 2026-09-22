import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Can } from "../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  ErrorState,
  FormError,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";

type StaffLeaveRequest = {
  id: number;
  school_id: number;
  employee_id: number;
  employee_name: string;
  employee_type?: string;
  leave_type: string | null;
  from_date: string;
  to_date: string;
  is_half_day: boolean;
  days: number;
  reason: string;
  status: "applied" | "approved" | "rejected" | "cancelled";
  decided_by_name: string | null;
  decided_at: string | null;
  decision_note: string | null;
};

type AffectedPeriod = {
  slot_id: number;
  date: string;
  period_no: number;
  start_time: string;
  end_time: string;
  class_label: string;
  subject_name: string;
  room_number: string | null;
  status: "unassigned" | "provisional" | "confirmed";
  substitution_id: number | null;
  substitute_teacher_id: number | null;
  substitute_teacher_name: string | null;
  free_teachers: {
    id: number;
    name: string;
    employee_code: string;
  }[];
};

type SubstitutionMatrix = {
  leave_request_id: number;
  teacher_name: string;
  from_date: string;
  to_date: string;
  total_periods: number;
  covered_periods: number;
  ready_for_approval: boolean;
  periods: AffectedPeriod[];
};

export function StaffLeavePage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [reviewModalRequestId, setReviewModalRequestId] = useState<number | null>(null);
  const [rejectDialogTarget, setRejectDialogTarget] = useState<StaffLeaveRequest | null>(null);
  const [selectedSubstitutes, setSelectedSubstitutes] = useState<Record<string, number>>({});

  // Fetch leave requests
  const requestsQuery = useQuery({
    queryKey: ["staff-leave-requests", statusFilter],
    queryFn: () => {
      const q = statusFilter ? `?request_status=${statusFilter}` : "";
      return api.get(`/admin/staff-leave${q}` as "/admin/staff-leave") as Promise<StaffLeaveRequest[]>;
    },
  });

  // Fetch substitution matrix for the currently reviewed request
  const matrixQuery = useQuery({
    queryKey: ["substitution-matrix", reviewModalRequestId],
    queryFn: () =>
      api.get(
        `/admin/staff-leave/${reviewModalRequestId}/substitution-matrix` as "/admin/staff-leave/{request_id}/substitution-matrix",
      ) as Promise<SubstitutionMatrix>,
    enabled: reviewModalRequestId !== null,
  });

  // Assign provisional substitution mutation
  const assignMutation = useMutation({
    mutationFn: ({
      requestId,
      slotId,
      date,
      teacherId,
    }: {
      requestId: number;
      slotId: number;
      date: string;
      teacherId: number;
    }) =>
      api.post(
        `/admin/staff-leave/${requestId}/provisional-substitution` as "/admin/staff-leave/{request_id}/provisional-substitution",
        {
          slot_id: slotId,
          date: date,
          substitute_teacher_id: teacherId,
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["substitution-matrix", reviewModalRequestId] });
    },
  });

  // Remove provisional substitution mutation
  const removeMutation = useMutation({
    mutationFn: ({ requestId, subId }: { requestId: number; subId: number }) =>
      api.del(
        `/admin/staff-leave/${requestId}/provisional-substitution/${subId}` as "/admin/staff-leave/{request_id}/provisional-substitution/{substitution_id}",
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["substitution-matrix", reviewModalRequestId] });
    },
  });

  // Approve leave with substitutions mutation
  const approveMutation = useMutation({
    mutationFn: (requestId: number) =>
      api.post(
        `/admin/staff-leave/${requestId}/approve-with-substitutions` as "/admin/staff-leave/{request_id}/approve-with-substitutions",
        { note: "Approved with complete timetable substitution coverage." },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staff-leave-requests"] });
      setReviewModalRequestId(null);
    },
  });

  // Reject leave mutation
  const rejectMutation = useMutation({
    mutationFn: ({ requestId, reason }: { requestId: number; reason: string }) =>
      api.post(`/admin/staff-leave/${requestId}/reject` as "/admin/staff-leave/{request_id}/reject", {
        reason: reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staff-leave-requests"] });
      setRejectDialogTarget(null);
      setReviewModalRequestId(null);
    },
  });

  const allRequests = requestsQuery.data ?? [];
  const pendingCount = allRequests.filter((r) => r.status === "applied").length;
  const approvedCount = allRequests.filter((r) => r.status === "approved").length;
  const rejectedCount = allRequests.filter((r) => r.status === "rejected").length;

  const matrix = matrixQuery.data;
  const canApprove = matrix ? matrix.ready_for_approval : false;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Staff Leave & Substitution Gate</h1>
          <p className="text-sm text-ink-faint mt-1">
            Teacher leave applications, timetable collision detection, and provisional substitution coverage.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Applications" value={allRequests.length} />
        <StatCard label="Pending Approval" value={pendingCount} hint="Requires substitution gating" />
        <StatCard label="Approved Leaves" value={approvedCount} />
        <StatCard label="Rejected" value={rejectedCount} />
      </div>

      {/* Leave Requests Table */}
      <Card title="Staff Leave Applications">
        <div className="flex flex-wrap items-center gap-2 mb-4 border-b border-rule pb-2">
          {[
            { key: "", label: `All (${allRequests.length})` },
            { key: "applied", label: `Pending Review (${pendingCount})` },
            { key: "approved", label: `Approved (${approvedCount})` },
            { key: "rejected", label: `Rejected (${rejectedCount})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-pill transition ${
                statusFilter === tab.key
                  ? "bg-primary text-white"
                  : "text-ink-soft hover:bg-ground hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <DataTable<StaffLeaveRequest>
          rows={allRequests}
          loading={requestsQuery.isLoading}
          error={requestsQuery.error}
          empty="No leave applications found."
          columns={[
            {
              key: "staff",
              header: "Employee",
              render: (r) => (
                <div>
                  <div className="font-semibold text-ink">
                    {r.employee_name || (r as any).employee || "Staff Member"}
                  </div>
                  <div className="text-xs text-ink-faint">
                    {r.leave_type ? r.leave_type : "Teacher Leave (No Quota)"}
                  </div>
                </div>
              ),
            },
            {
              key: "dates",
              header: "Duration & Dates",
              render: (r) => (
                <div>
                  <div className="font-medium text-ink">
                    {r.from_date} {r.from_date !== r.to_date ? `to ${r.to_date}` : ""}
                  </div>
                  <div className="text-xs text-ink-faint">
                    {r.days} day{r.days === 1 ? "" : "s"} {r.is_half_day ? "(Half Day)" : ""}
                  </div>
                </div>
              ),
            },
            {
              key: "reason",
              header: "Reason",
              render: (r) => (
                <div className="max-w-xs text-xs text-ink-soft truncate" title={r.reason}>
                  {r.reason}
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (r) => {
                const map: Record<StaffLeaveRequest["status"], { label: string; pill: string }> = {
                  applied: { label: "Pending", pill: "pending" },
                  approved: { label: "Approved", pill: "paid" },
                  rejected: { label: "Rejected", pill: "overdue" },
                  cancelled: { label: "Cancelled", pill: "overdue" },
                };
                const s = map[r.status] ?? { label: r.status, pill: "pending" };
                return <Pill status={s.pill}>{s.label}</Pill>;
              },
            },
            {
              key: "actions",
              header: "Review / Actions",
              align: "right",
              render: (r) => (
                <div className="flex items-center justify-end gap-2">
                  {r.status === "applied" ? (
                    <Can permission="hr.leave.approve">
                      <button
                        onClick={() => setReviewModalRequestId(r.id)}
                        className="px-3 py-1.5 text-xs bg-primary text-white rounded-input font-semibold hover:bg-primary-hover shadow-sm transition flex items-center gap-1"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                        </svg>
                        Review & Substitute
                      </button>
                    </Can>
                  ) : (
                    <span className="text-xs text-ink-faint">
                      {r.decision_note ? `Note: ${r.decision_note}` : "Processed"}
                    </span>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Teacher Leave Review & Substitution Matrix Modal */}
      {reviewModalRequestId !== null && (
        <Modal
          title={`Teacher Leave Review & Timetable Matrix (Req #${reviewModalRequestId})`}
          onClose={() => setReviewModalRequestId(null)}
        >
          {matrixQuery.isLoading ? (
            <div className="py-12 text-center text-sm text-ink-faint">
              Calculating affected timetable periods & substitute availability...
            </div>
          ) : matrixQuery.error ? (
            <ErrorState error={matrixQuery.error} />
          ) : matrix ? (
            <div className="space-y-5">
              {/* Applicant & Leave Summary Banner */}
              <div className="bg-ground border border-rule rounded-lg p-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-ink-faint block">Teacher Name:</span>
                  <span className="font-bold text-ink text-sm">{matrix.teacher_name}</span>
                </div>
                <div>
                  <span className="text-ink-faint block">Leave Dates:</span>
                  <span className="font-semibold text-ink">
                    {matrix.from_date} to {matrix.to_date}
                  </span>
                </div>
                <div>
                  <span className="text-ink-faint block">Affected Periods:</span>
                  <span className="font-bold text-primary tabular text-sm">{matrix.total_periods}</span>
                </div>
                <div>
                  <span className="text-ink-faint block">Coverage Status:</span>
                  <span
                    className={`font-bold text-sm ${
                      matrix.ready_for_approval ? "text-success" : "text-amber-600"
                    }`}
                  >
                    {matrix.covered_periods} of {matrix.total_periods} Assigned
                  </span>
                </div>
              </div>

              {/* Progress & Safety Gate Indicator */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-ink-soft">Timetable Substitution Coverage</span>
                  <span className={matrix.ready_for_approval ? "text-success" : "text-amber-600"}>
                    {matrix.total_periods === 0
                      ? "No teaching periods affected"
                      : `${Math.round((matrix.covered_periods / matrix.total_periods) * 100)}% Covered`}
                  </span>
                </div>
                <div className="w-full bg-rule h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      matrix.ready_for_approval ? "bg-success" : "bg-amber-500"
                    }`}
                    style={{
                      width: `${
                        matrix.total_periods === 0
                          ? 100
                          : (matrix.covered_periods / matrix.total_periods) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>

              {/* Safety Gate Warning Alert */}
              {!matrix.ready_for_approval ? (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-md text-xs flex items-start gap-2">
                  <svg className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div>
                    <span className="font-bold block">Approval Gate Locked</span>
                    School policy strictly forbids approving teacher leave until 100% of affected timetable
                    periods have confirmed substitutes assigned. Select available free teachers below.
                  </div>
                </div>
              ) : (
                <div className="bg-success/10 border border-success/30 text-success p-3 rounded-md text-xs flex items-center gap-2">
                  <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="font-semibold">
                    100% of affected timetable periods covered! Leave application is ready for approval.
                  </span>
                </div>
              )}

              {/* Affected Periods Matrix Grid */}
              <div className="border border-rule rounded-lg overflow-hidden">
                <div className="bg-ground px-4 py-2 text-xs font-bold text-ink border-b border-rule flex justify-between items-center">
                  <span>Affected Timetable Periods ({matrix.periods.length})</span>
                  <span className="text-[11px] text-ink-faint font-normal">
                    Original timetable slots remain completely unchanged
                  </span>
                </div>

                {matrix.periods.length === 0 ? (
                  <div className="p-6 text-center text-xs text-ink-faint">
                    No scheduled periods found for this teacher during the selected dates.
                  </div>
                ) : (
                  <div className="divide-y divide-rule max-h-96 overflow-y-auto">
                    {matrix.periods.map((p) => {
                      const periodKey = `${p.slot_id}_${p.date}`;
                      const isCovered = p.status !== "unassigned";

                      return (
                        <div key={periodKey} className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs hover:bg-ground/50">
                          {/* Period Details */}
                          <div className="space-y-0.5 min-w-44">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-ink">
                                Period {p.period_no} ({p.start_time} - {p.end_time})
                              </span>
                              <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-medium text-[10px]">
                                {p.date}
                              </span>
                            </div>
                            <div className="text-ink-soft font-medium">
                              Class: <span className="font-semibold text-ink">{p.class_label}</span> • Subject:{" "}
                              <span className="font-semibold text-ink">{p.subject_name}</span>
                            </div>
                          </div>

                          {/* Substitution State & Selector */}
                          <div className="flex items-center gap-2 flex-1 justify-end">
                            {isCovered ? (
                              <div className="flex items-center gap-2 bg-success/10 border border-success/30 px-3 py-1.5 rounded-md">
                                <svg className="w-3.5 h-3.5 text-success" fill="currentColor" viewBox="0 0 20 20">
                                  <path
                                    fillRule="evenodd"
                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                                <div>
                                  <span className="text-[11px] text-ink-faint block">Assigned Substitute:</span>
                                  <span className="font-bold text-success text-xs">
                                    {p.substitute_teacher_name}
                                  </span>
                                </div>
                                <button
                                  onClick={() =>
                                    p.substitution_id &&
                                    removeMutation.mutate({
                                      requestId: matrix.leave_request_id,
                                      subId: p.substitution_id,
                                    })
                                  }
                                  disabled={removeMutation.isPending}
                                  className="ml-2 text-danger hover:text-red-700 text-xs font-medium underline"
                                >
                                  Remove
                                </button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2">
                                <select
                                  value={selectedSubstitutes[periodKey] ?? ""}
                                  onChange={(e) =>
                                    setSelectedSubstitutes({
                                      ...selectedSubstitutes,
                                      [periodKey]: parseInt(e.target.value),
                                    })
                                  }
                                  className={`${inputClass} w-52 text-xs`}
                                >
                                  <option value="">-- Choose Free Teacher --</option>
                                  {p.free_teachers.map((t) => (
                                    <option key={t.id} value={t.id}>
                                      {t.name} ({t.employee_code})
                                    </option>
                                  ))}
                                </select>

                                <button
                                  type="button"
                                  disabled={!selectedSubstitutes[periodKey] || assignMutation.isPending}
                                  onClick={() => {
                                    const teacherId = selectedSubstitutes[periodKey];
                                    if (teacherId) {
                                      assignMutation.mutate({
                                        requestId: matrix.leave_request_id,
                                        slotId: p.slot_id,
                                        date: p.date,
                                        teacherId: teacherId,
                                      });
                                    }
                                  }}
                                  className="px-3 py-1.5 bg-primary text-white rounded-input text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
                                >
                                  Assign
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between border-t border-rule pt-4">
                <button
                  type="button"
                  onClick={() => {
                    const req = allRequests.find((r) => r.id === reviewModalRequestId);
                    if (req) setRejectDialogTarget(req);
                  }}
                  className="px-4 py-2 border border-danger/30 text-danger rounded-input text-xs font-semibold hover:bg-danger/10 transition"
                >
                  Reject Application (Purge Substitutions)
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewModalRequestId(null)}
                    className="px-4 py-2 border border-rule rounded-input text-xs text-ink-soft hover:bg-ground"
                  >
                    Close
                  </button>

                  <button
                    type="button"
                    disabled={!canApprove || approveMutation.isPending}
                    onClick={() => approveMutation.mutate(matrix.leave_request_id)}
                    title={
                      canApprove
                        ? "Approve leave and activate confirmed timetable substitutions"
                        : "Locked: All affected periods must have assigned substitutes before approval"
                    }
                    className={`px-5 py-2 rounded-input text-xs font-bold text-white transition ${
                      canApprove
                        ? "bg-success hover:opacity-90 cursor-pointer shadow"
                        : "bg-gray-400 cursor-not-allowed opacity-60"
                    }`}
                  >
                    {approveMutation.isPending
                      ? "Approving..."
                      : canApprove
                      ? "Approve Leave & Confirm Substitutions"
                      : "Approve Locked (Uncovered Periods)"}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </Modal>
      )}

      {/* Reject Confirmation Dialog */}
      {rejectDialogTarget && (
        <ConfirmDialog
          title="Reject Leave Application"
          intent={
            <div className="space-y-2">
              <p>
                Are you sure you want to reject the leave application for{" "}
                <strong>{rejectDialogTarget.employee_name}</strong> ({rejectDialogTarget.from_date} to{" "}
                {rejectDialogTarget.to_date})?
              </p>
              <p className="text-danger font-medium text-xs">
                Important: All provisional substitutions assigned for this application will be immediately
                purged. The master timetable will remain 100% untouched.
              </p>
            </div>
          }
          confirmLabel="Reject Leave"
          busy={rejectMutation.isPending}
          error={rejectMutation.error}
          onConfirm={(reason) =>
            rejectMutation.mutate({
              requestId: rejectDialogTarget.id,
              reason: reason,
            })
          }
          onClose={() => setRejectDialogTarget(null)}
        />
      )}
    </div>
  );
}
