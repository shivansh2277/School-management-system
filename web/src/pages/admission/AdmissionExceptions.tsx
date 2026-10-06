import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import {
  Card,
  DataTable,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../../components/ui";

export type OverrideRow = {
  id: number;
  application_id: number;
  application_no: string | null;
  applicant_name: string;
  class_applying_for: string;
  document_code: string;
  document_name?: string;
  status: "pending" | "approved" | "rejected";
  authorized_by_id?: number | null;
  authorized_by_name: string | null;
  reason: string;
  rejection_reason?: string | null;
  created_at: string | null;
  authorized_at: string | null;
};

type LookupResult = {
  id: number;
  application_no: string;
  full_name: string;
  date_of_birth: string;
  class_applying_for: string;
  status: string;
  checklist: Array<{
    document_code: string;
    document_name: string;
    required: boolean;
    has_override?: boolean;
  }>;
  overrides: Array<{
    id: number;
    document_code: string;
    reason: string;
    authorized_by_name: string | null;
    authorized_at: string | null;
  }>;
};

const COMMON_REASONS = [
  "Birth certificate under process at Municipal Corporation / Registrar of Births",
  "Affidavit submitted by parent guaranteeing submission within 30 days",
  "Parent out of station / Relocation in progress",
  "Single parent / Guardian legal documentation under verification",
  "Other administrative exception approved by Principal",
];

export function AdmissionExceptions() {
  const qc = useQueryClient();
  const [ref, setRef] = useState("");
  const [activeRef, setActiveRef] = useState("");
  const [selectedDoc, setSelectedDoc] = useState("birth_certificate");
  const [reasonPreset, setReasonPreset] = useState(COMMON_REASONS[0]);
  const [customReason, setCustomReason] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Modal review & rejection states
  const [reviewTarget, setReviewTarget] = useState<OverrideRow | null>(null);
  const [rejectTarget, setRejectTarget] = useState<OverrideRow | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [showManualLookup, setShowManualLookup] = useState(true);

  // All overrides list
  const overridesQuery = useQuery({
    queryKey: ["admission-document-overrides"],
    queryFn: () =>
      api.rawGet<OverrideRow[]>("/admin/admission/document-overrides"),
  });

  // Lookup single application by reference code (DFT-xxx or application_no)
  const lookupQuery = useQuery({
    queryKey: ["admission-lookup", activeRef],
    queryFn: () =>
      api.rawGet<LookupResult>(`/admin/admission/applications/lookup?ref=${encodeURIComponent(activeRef)}`),
    enabled: Boolean(activeRef),
  });

  // Manual authorize mutation
  const overrideMutation = useMutation({
    mutationFn: async ({ appId, docCode, reason }: { appId: number; docCode: string; reason: string }) => {
      return api.rawPost(`/admin/admission/applications/${appId}/document-overrides`, {
        document_code: docCode,
        reason,
      });
    },
    onSuccess: () => {
      setActionSuccess("Document override successfully authorized and audit logged.");
      setActionError(null);
      qc.invalidateQueries({ queryKey: ["admission-document-overrides"] });
      qc.invalidateQueries({ queryKey: ["admission-lookup", activeRef] });
      setCustomReason("");
    },
    onError: (err: any) => {
      setActionError(errorText(err));
    },
  });

  // Approve pending override mutation
  const approveMutation = useMutation({
    mutationFn: async (overrideId: number) => {
      return api.rawPost(`/admin/admission/document-overrides/${overrideId}/approve`, {});
    },
    onSuccess: () => {
      setActionSuccess("Document exception approved successfully.");
      setActionError(null);
      qc.invalidateQueries({ queryKey: ["admission-document-overrides"] });
      setReviewTarget(null);
    },
    onError: (err: any) => {
      setActionError(errorText(err));
    },
  });

  // Reject pending override mutation
  const rejectMutation = useMutation({
    mutationFn: async ({ overrideId, reason }: { overrideId: number; reason: string }) => {
      return api.rawPost(`/admin/admission/document-overrides/${overrideId}/reject`, { reason });
    },
    onSuccess: () => {
      setActionSuccess("Document exception rejected successfully.");
      setActionError(null);
      qc.invalidateQueries({ queryKey: ["admission-document-overrides"] });
      setRejectTarget(null);
      setRejectReason("");
      setReviewTarget(null);
    },
    onError: (err: any) => {
      setActionError(errorText(err));
    },
  });

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ref.trim()) return;
    setActiveRef(ref.trim());
    setActionSuccess(null);
    setActionError(null);
  };

  const handleAuthorize = () => {
    if (!lookupQuery.data) return;
    const finalReason = customReason.trim() ? customReason.trim() : reasonPreset;
    overrideMutation.mutate({
      appId: lookupQuery.data.id,
      docCode: selectedDoc,
      reason: finalReason,
    });
  };

  const allOverrides = overridesQuery.data ?? [];
  const pendingQueue = allOverrides.filter((r) => r.status === "pending");
  const processedOverrides = allOverrides.filter((r) => r.status !== "pending");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">
            Admission Document Overrides & Exceptions
          </h1>
          <p className="text-xs sm:text-sm text-ink-soft mt-1">
            Automatic pending queue for applicant document exception requests and official waiver authorizations.
          </p>
        </div>
        <div>
          <span className="text-xs bg-amber-50 text-amber-800 border border-amber-200 font-medium px-2.5 py-1 rounded-full whitespace-nowrap">
            Admin Scoped Exception Authorization
          </span>
        </div>
      </div>

      {/* Notifications */}
      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-card text-sm flex items-center justify-between">
          <span>✓ {actionSuccess}</span>
          <button
            type="button"
            onClick={() => setActionSuccess(null)}
            className="text-emerald-600 hover:text-emerald-900 font-bold ml-2 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}
      {actionError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-800 rounded-card text-sm flex items-center justify-between">
          <span>⚠ {actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            className="text-red-600 hover:text-red-900 font-bold ml-2 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}

      {/* SECTION 1: Automatic Pending Queue */}
      <Card
        title="Pending Exceptions Queue"
        action={
          <span className="text-xs bg-amber-100 text-amber-800 font-bold px-2.5 py-1 rounded-full border border-amber-200">
            {pendingQueue.length} Pending
          </span>
        }
      >
        <p className="text-xs text-ink-soft mb-3">
          When parents or applicants submit an application or exception request with missing mandatory documents,
          it automatically appears in this queue for administrative review without manual searching.
        </p>

        {overridesQuery.isLoading && (
          <p className="text-sm text-ink-faint py-4">Loading pending queue items...</p>
        )}

        {!overridesQuery.isLoading && pendingQueue.length === 0 ? (
          <div className="py-8 text-center bg-ground/50 rounded-card border border-dashed border-rule">
            <p className="text-sm font-medium text-ink-soft">
              No pending document exception requests.
            </p>
            <p className="text-xs text-ink-faint mt-1">
              New document exceptions submitted by prospective students will automatically arrive here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-ink border-collapse">
              <thead>
                <tr className="border-b border-rule bg-ground/80 text-ink-soft font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Application ID</th>
                  <th className="py-2.5 px-3">Requested Document</th>
                  <th className="py-2.5 px-3">Reason / Details</th>
                  <th className="py-2.5 px-3">Date Requested</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule/60">
                {pendingQueue.map((item) => (
                  <tr key={item.id} className="hover:bg-ground/40 transition-colors">
                    <td className="py-3 px-3 font-semibold text-ink">
                      {item.applicant_name || `Applicant #${item.application_id}`}
                      {item.class_applying_for && (
                        <span className="text-[10px] text-ink-faint block font-normal">
                          Class: {item.class_applying_for}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono font-medium text-primary">
                      {item.application_no || `DFT-${item.application_id}`}
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold capitalize text-ink-soft bg-ground px-2 py-0.5 rounded border border-rule inline-block">
                        {item.document_name || item.document_code.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="py-3 px-3 max-w-xs text-ink-soft">
                      <span className="line-clamp-2" title={item.reason}>
                        {item.reason}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-ink-faint whitespace-nowrap">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : "-"}
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                        Pending
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap space-x-1.5">
                      <button
                        type="button"
                        onClick={() => setReviewTarget(item)}
                        className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 hover:bg-slate-200 text-slate-800 transition cursor-pointer"
                      >
                        Review
                      </button>
                      <button
                        type="button"
                        disabled={approveMutation.isPending}
                        onClick={() => approveMutation.mutate(item.id)}
                        className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-700 text-white transition cursor-pointer"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setRejectTarget(item);
                          setRejectReason("");
                        }}
                        className="px-2.5 py-1 text-xs font-semibold rounded bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition cursor-pointer"
                      >
                        Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* SECTION 2: Audit Trail of Authorized & Processed Overrides */}
      <Card title="Authorized Overrides Audit Trail">
        <DataTable
          rows={processedOverrides}
          loading={overridesQuery.isLoading}
          error={overridesQuery.error}
          empty="No document overrides have been recorded yet."
          columns={[
            {
              key: "ref",
              header: "Reference",
              render: (r) => (
                <span className="font-mono text-xs font-medium">
                  {r.application_no || `DFT-${r.application_id}`}
                </span>
              ),
            },
            { key: "applicant", header: "Applicant", render: (r) => r.applicant_name || `App #${r.application_id}` },
            { key: "class", header: "Class", render: (r) => r.class_applying_for || "-" },
            {
              key: "doc",
              header: "Document",
              render: (r) => (
                <span className="capitalize font-medium text-xs bg-ground px-2 py-0.5 rounded border border-rule">
                  {r.document_code.replace(/_/g, " ")}
                </span>
              ),
            },
            { key: "reason", header: "Reason", render: (r) => <span className="text-xs">{r.reason}</span> },
            {
              key: "status",
              header: "Status",
              render: (r) => (
                <span
                  className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                    r.status === "approved"
                      ? "bg-emerald-100 text-emerald-800"
                      : r.status === "rejected"
                      ? "bg-red-100 text-red-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {r.status || "approved"}
                </span>
              ),
            },
            {
              key: "by",
              header: "Processed By",
              render: (r) => (r.status === "pending" ? "-" : r.authorized_by_name ?? "Admin"),
            },
            {
              key: "date",
              header: "Processed At",
              render: (r) =>
                r.authorized_at
                  ? new Date(r.authorized_at).toLocaleDateString()
                  : r.created_at
                  ? new Date(r.created_at).toLocaleDateString()
                  : "-",
            },
          ]}
        />
      </Card>

      {/* SECTION 3: Manual Lookup & Exception Authorization (Collapsible) */}
      <Card
        title="Manual Application Lookup & Ad-hoc Authorization"
        action={
          <button
            type="button"
            onClick={() => setShowManualLookup(!showManualLookup)}
            className="text-xs font-semibold text-primary hover:underline cursor-pointer"
          >
            {showManualLookup ? "Hide Lookup Form ▲" : "Show Lookup Form ▼"}
          </button>
        }
      >
        <p className="text-xs text-ink-soft mb-4">
          Optionally look up an individual draft or submitted application by its reference code (e.g. DFT-12) to inspect the complete checklist or grant an ad-hoc exception.
        </p>

        {showManualLookup && (
          <div>
            <form onSubmit={handleLookup} className="flex gap-2 max-w-md mb-6">
              <input
                type="text"
                className={inputClass}
                placeholder="Enter Draft Ref (e.g. DFT-12) or App No..."
                value={ref}
                onChange={(e) => setRef(e.target.value)}
              />
              <button
                type="submit"
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 shrink-0 cursor-pointer"
              >
                Lookup Draft
              </button>
            </form>

            {lookupQuery.isLoading && <p className="text-sm text-ink-faint">Searching application records...</p>}
            {lookupQuery.error && (
              <p className="text-sm text-danger">{errorText(lookupQuery.error)}</p>
            )}

            {lookupQuery.data && (
              <div className="border border-rule rounded-card p-4 bg-ground space-y-4 mb-2">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule pb-3">
                  <div>
                    <h3 className="font-semibold text-base">{lookupQuery.data.full_name}</h3>
                    <p className="text-xs text-ink-soft">
                      Ref: <span className="font-mono font-medium">{lookupQuery.data.application_no}</span> • Class Applied:{" "}
                      <span className="font-medium">{lookupQuery.data.class_applying_for}</span> • DOB: {lookupQuery.data.date_of_birth}
                    </p>
                  </div>
                  <Pill status={lookupQuery.data.status}>{lookupQuery.data.status}</Pill>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-ink-soft uppercase tracking-wider mb-2">
                    Mandatory & Optional Checklist
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                    {lookupQuery.data.checklist.map((item) => (
                      <div
                        key={item.document_code}
                        className="flex items-center justify-between p-2 bg-surface rounded border border-rule"
                      >
                        <span>
                          {item.document_name}{" "}
                          {item.required && <span className="text-danger font-medium text-xs">(Mandatory)</span>}
                        </span>
                        {item.has_override ? (
                          <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-medium">
                            Authorized Exception
                          </span>
                        ) : (
                          <span className="text-xs text-ink-faint">Pending</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-rule space-y-3">
                  <h4 className="text-sm font-semibold text-ink">Authorize Document Exception</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <FormField label="Target Document">
                      <select
                        className={inputClass}
                        value={selectedDoc}
                        onChange={(e) => setSelectedDoc(e.target.value)}
                      >
                        <option value="birth_certificate">Birth Certificate</option>
                        <option value="apaar_consent">APAAR ID / Parental Consent</option>
                        <option value="previous_report_card">Previous Report Card</option>
                        <option value="transfer_certificate">Transfer Certificate</option>
                        <option value="address_proof">Address Proof</option>
                      </select>
                    </FormField>

                    <FormField label="Reason Template">
                      <select
                        className={inputClass}
                        value={reasonPreset}
                        onChange={(e) => setReasonPreset(e.target.value)}
                      >
                        {COMMON_REASONS.map((r, i) => (
                          <option key={i} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </FormField>
                  </div>

                  <FormField label="Additional Audit Notes / Remarks (Optional)">
                    <input
                      type="text"
                      className={inputClass}
                      placeholder="Specific undertaking reference or parent request details..."
                      value={customReason}
                      onChange={(e) => setCustomReason(e.target.value)}
                    />
                  </FormField>

                  <FormError error={overrideMutation.error} />

                  <div className="flex justify-end pt-1">
                    <button
                      type="button"
                      onClick={handleAuthorize}
                      disabled={overrideMutation.isPending}
                      className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                    >
                      {overrideMutation.isPending ? "Recording Authorization..." : "Authorize Document Exception"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Review Modal */}
      {reviewTarget && (
        <Modal
          title={`Review Exception: ${reviewTarget.applicant_name || `App #${reviewTarget.application_id}`}`}
          onClose={() => setReviewTarget(null)}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs bg-ground p-3 rounded-card border border-rule">
              <div>
                <span className="text-ink-faint block">Application ID</span>
                <span className="font-mono font-bold text-primary">
                  {reviewTarget.application_no || `DFT-${reviewTarget.application_id}`}
                </span>
              </div>
              <div>
                <span className="text-ink-faint block">Class</span>
                <span className="font-semibold text-ink">{reviewTarget.class_applying_for || "Not specified"}</span>
              </div>
              <div>
                <span className="text-ink-faint block">Requested Document</span>
                <span className="font-semibold text-ink capitalize">
                  {reviewTarget.document_name || reviewTarget.document_code.replace(/_/g, " ")}
                </span>
              </div>
              <div>
                <span className="text-ink-faint block">Status</span>
                <span className="font-bold text-amber-700 capitalize">{reviewTarget.status}</span>
              </div>
            </div>

            <div>
              <span className="text-xs font-bold uppercase text-ink-faint block mb-1">
                Applicant Reason / Exception Details
              </span>
              <p className="text-xs text-ink bg-surface p-3 rounded border border-rule whitespace-pre-wrap">
                {reviewTarget.reason}
              </p>
            </div>

            <div className="text-xs text-ink-faint">
              Requested: {reviewTarget.created_at ? new Date(reviewTarget.created_at).toLocaleString() : "-"}
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setReviewTarget(null)}
                className="px-3 py-1.5 text-xs font-medium text-ink-faint hover:text-ink cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setRejectTarget(reviewTarget);
                  setRejectReason("");
                }}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 cursor-pointer"
              >
                Reject Exception
              </button>
              <button
                type="button"
                disabled={approveMutation.isPending}
                onClick={() => approveMutation.mutate(reviewTarget.id)}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
              >
                {approveMutation.isPending ? "Approving..." : "Approve Exception"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reject Modal */}
      {rejectTarget && (
        <Modal
          title={`Reject Exception: ${rejectTarget.applicant_name || `App #${rejectTarget.application_id}`}`}
          onClose={() => setRejectTarget(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (rejectReason.trim().length < 2) return;
              rejectMutation.mutate({
                overrideId: rejectTarget.id,
                reason: rejectReason.trim(),
              });
            }}
            className="space-y-4"
          >
            <div className="p-3 bg-red-50 rounded text-xs text-red-800 border border-red-200">
              Rejecting this request will mark the exception as rejected. The applicant will still be required to provide the mandatory document ({rejectTarget.document_code.replace(/_/g, " ")}).
            </div>

            <FormField label="Reason for Rejection">
              <textarea
                required
                minLength={2}
                rows={3}
                className={inputClass}
                placeholder="State the reason for rejecting this exception request..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setRejectTarget(null)}
                className="px-3 py-1.5 text-xs font-medium text-ink-faint hover:text-ink cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={rejectMutation.isPending || rejectReason.trim().length < 2}
                className="px-4 py-1.5 text-xs font-semibold rounded bg-red-600 hover:bg-red-700 text-white cursor-pointer"
              >
                {rejectMutation.isPending ? "Rejecting..." : "Confirm Rejection"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
