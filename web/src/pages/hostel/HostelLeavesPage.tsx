import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { useAuth } from "../../auth/AuthContext";
import { Card, DataTable, FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type LeaveRow = {
  id: number;
  student_id: number;
  admission_no: string;
  full_name: string;
  hostel_id: number;
  request_type: string;
  start_date: string;
  end_date: string;
  expected_return_time: string;
  actual_return_time: string | null;
  purpose: string;
  status: string;
  is_overdue: boolean;
  parent_name: string;
  remarks: string | null;
  rejection_reason: string | null;
  approved_at: string | null;
};

export function HostelLeavesPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Fetch leave requests
  const { data: leaves = [], isLoading, error } = useQuery<LeaveRow[]>({
    queryKey: ["hostel", "leaves", statusFilter],
    queryFn: () =>
      api.rawGet<LeaveRow[]>(`/admin/hostel/leaves${statusFilter !== "all" ? `?status=${statusFilter}` : ""}`),
  });

  // Adjudication modal state
  const [adjudicatingReq, setAdjudicatingReq] = useState<{
    id: number;
    studentName: string;
    requestType: string;
    action: "approve" | "reject";
  } | null>(null);
  const [remarks, setRemarks] = useState("");
  const [adjError, setAdjError] = useState<string | null>(null);

  // Return modal state
  const [returningReq, setReturningReq] = useState<LeaveRow | null>(null);

  // Adjudicate mutation (Approve/Reject)
  const adjudicateMutation = useMutation({
    mutationFn: async () => {
      if (!adjudicatingReq) throw new Error("No request selected");
      return api.rawPost(`/admin/hostel/leaves/${adjudicatingReq.id}/adjudicate`, {
        action: adjudicatingReq.action,
        remarks: remarks.trim() || undefined,
        rejection_reason:
          adjudicatingReq.action === "reject" ? remarks.trim() || "Rejected by Warden" : undefined,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setAdjudicatingReq(null);
      setRemarks("");
      setAdjError(null);
    },
    onError: (err: any) => {
      setAdjError(errorText(err));
    },
  });

  // Record Return mutation
  const returnMutation = useMutation({
    mutationFn: async (reqId: number) => {
      return api.rawPost(`/admin/hostel/leaves/${reqId}/return`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setReturningReq(null);
    },
  });

  const overdueCount = leaves.filter((l) => l.is_overdue).length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Leaves & Outings Management</h1>
          <p className="text-sm text-ink-soft mt-1">
            Review parent-initiated leave and outing requests, enforce safety limits, and log gate return.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {(["all", "pending", "approved", "returned", "rejected"] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded text-xs font-semibold capitalize transition ${
                statusFilter === st
                  ? "bg-primary text-white"
                  : "bg-surface border border-rule text-ink-soft hover:bg-ground"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Overdue Warning Alert */}
      {overdueCount > 0 && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/40 rounded-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-sm font-bold text-amber-900">
                Residential Gate Alert: {overdueCount} Student{overdueCount > 1 ? "s" : ""} Overdue!
              </p>
              <p className="text-xs text-amber-800">
                These students have passed their scheduled return time without recorded gate arrival. Contact parents or record return upon arrival.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Leaves Table */}
      <Card>
        {isLoading ? (
          <p className="text-xs text-ink-soft py-6 text-center">Loading requests...</p>
        ) : error ? (
          <p className="text-xs text-danger py-4 text-center">Failed to load leave requests.</p>
        ) : leaves.length === 0 ? (
          <p className="text-xs text-ink-soft py-6 text-center">No leave or outing requests found.</p>
        ) : (
          <DataTable
            rows={leaves}
            empty="No leave or outing requests found."
            columns={[
              {
                key: "resident",
                header: "Resident Student",
                render: (r: LeaveRow) => (
                  <div>
                    <span className="font-semibold text-ink text-sm">{r.full_name}</span>
                    <p className="text-2xs text-ink-soft">
                      Adm #{r.admission_no} • Parent: {r.parent_name}
                    </p>
                  </div>
                ),
              },
              {
                key: "type",
                header: "Type",
                render: (r: LeaveRow) => (
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink">
                    {r.request_type}
                  </span>
                ),
              },
              {
                key: "schedule",
                header: "Schedule & Timing",
                render: (r: LeaveRow) => (
                  <div className="text-xs">
                    <p className="text-ink">
                      {r.start_date} → {r.end_date}
                    </p>
                    <p className="text-2xs text-ink-soft">
                      Expected Return: {new Date(r.expected_return_time).toLocaleString()}
                    </p>
                    {r.actual_return_time && (
                      <p className="text-2xs text-emerald-600 font-medium">
                        Returned: {new Date(r.actual_return_time).toLocaleString()}
                      </p>
                    )}
                  </div>
                ),
              },
              {
                key: "purpose",
                header: "Purpose",
                render: (r: LeaveRow) => (
                  <div className="max-w-xs text-xs text-ink">
                    <p className="line-clamp-2">{r.purpose}</p>
                    {r.remarks && <p className="text-2xs text-ink-soft italic mt-0.5">Warden: {r.remarks}</p>}
                    {r.rejection_reason && (
                      <p className="text-2xs text-danger mt-0.5">Reason: {r.rejection_reason}</p>
                    )}
                  </div>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (r: LeaveRow) => (
                  <div className="flex flex-col gap-1 items-start">
                    <Pill status={r.status}>{r.status}</Pill>
                    {r.is_overdue && (
                      <span className="inline-flex items-center gap-1 text-2xs font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded border border-amber-300">
                        ⚠️ Overdue
                      </span>
                    )}
                  </div>
                ),
              },
              {
                key: "actions",
                header: "Actions",
                render: (r: LeaveRow) => (
                  <div className="flex items-center gap-1.5">
                    {r.status === "pending" && (
                      <>
                        <button
                          type="button"
                          onClick={() => {
                            setAdjudicatingReq({
                              id: r.id,
                              studentName: r.full_name,
                              requestType: r.request_type,
                              action: "approve",
                            });
                            setRemarks("");
                            setAdjError(null);
                          }}
                          className="px-2.5 py-1 rounded bg-emerald-600 text-white text-2xs font-semibold hover:bg-emerald-700 transition"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setAdjudicatingReq({
                              id: r.id,
                              studentName: r.full_name,
                              requestType: r.request_type,
                              action: "reject",
                            });
                            setRemarks("");
                            setAdjError(null);
                          }}
                          className="px-2.5 py-1 rounded bg-rose-600 text-white text-2xs font-semibold hover:bg-rose-700 transition"
                        >
                          Reject
                        </button>
                      </>
                    )}

                    {(r.status === "approved" || r.status === "departed") && (
                      <button
                        type="button"
                        onClick={() => setReturningReq(r)}
                        className="px-2.5 py-1 rounded bg-primary text-white text-2xs font-semibold hover:bg-primary-hover transition"
                      >
                        Record Return
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
          />
        )}
      </Card>

      {/* Adjudication Modal (Approve or Reject) */}
      {adjudicatingReq && (
        <Modal
          title={`${adjudicatingReq.action === "approve" ? "Approve" : "Reject"} ${adjudicatingReq.requestType.toUpperCase()}: ${adjudicatingReq.studentName}`}
          onClose={() => setAdjudicatingReq(null)}
        >
          <div className="space-y-4">
            {adjError && <p className="text-sm text-danger">{adjError}</p>}

            <FormField
              label={
                adjudicatingReq.action === "approve"
                  ? "Warden Approval Remarks (Optional)"
                  : "Rejection Reason (Mandatory) *"
              }
            >
              <textarea
                className={`${inputClass} min-h-[70px]`}
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder={
                  adjudicatingReq.action === "approve"
                    ? "e.g. Parental telephonic consent verified, approved for weekend"
                    : "e.g. Exam preparation week, gate curfew restriction"
                }
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setAdjudicatingReq(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={
                  (adjudicatingReq.action === "reject" && !remarks.trim()) ||
                  adjudicateMutation.isPending
                }
                onClick={() => adjudicateMutation.mutate()}
                className={`px-4 py-1.5 rounded text-white text-xs font-semibold disabled:opacity-50 ${
                  adjudicatingReq.action === "approve"
                    ? "bg-emerald-600 hover:bg-emerald-700"
                    : "bg-danger hover:bg-danger/90"
                }`}
              >
                {adjudicateMutation.isPending
                  ? "Saving..."
                  : `Confirm ${adjudicatingReq.action === "approve" ? "Approval" : "Rejection"}`}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Record Return Confirmation Modal */}
      {returningReq && (
        <Modal
          title={`Record Gate Arrival: ${returningReq.full_name}`}
          onClose={() => setReturningReq(null)}
        >
          <div className="space-y-4 text-xs">
            <p className="text-ink">
              Verify that <span className="font-bold">{returningReq.full_name}</span> has physically returned to the hostel premises and reported to the warden desk.
            </p>
            {returningReq.is_overdue && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-900">
                ⚠️ Notice: Student return was scheduled for{" "}
                <span className="font-bold">
                  {new Date(returningReq.expected_return_time).toLocaleString()}
                </span>
                . Recording return will clear the active overdue safety flag.
              </div>
            )}
            <p className="text-ink-soft">
              Timestamp will be recorded as current time ({new Date().toLocaleTimeString()}).
            </p>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setReturningReq(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={returnMutation.isPending}
                onClick={() => returnMutation.mutate(returningReq.id)}
                className="px-4 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {returnMutation.isPending ? "Recording..." : "Confirm Student Returned"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
