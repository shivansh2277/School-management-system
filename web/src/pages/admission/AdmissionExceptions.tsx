import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { Card, DataTable, FormError, FormField, Pill, inputClass } from "../../components/ui";

type OverrideRow = {
  id: number;
  application_id: number;
  application_no: string | null;
  applicant_name: string;
  class_applying_for: string;
  document_code: string;
  authorized_by_name: string | null;
  reason: string;
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

  const overrideMutation = useMutation({
    mutationFn: async ({ appId, docCode, reason }: { appId: number; docCode: string; reason: string }) => {
      return api.rawPost(`/admin/admission/applications/${appId}/document-overrides`, {
        document_code: docCode,
        reason,
      });
    },
    onSuccess: () => {
      setActionSuccess("Document override successfully authorized and audit logged.");
      qc.invalidateQueries({ queryKey: ["admission-document-overrides"] });
      qc.invalidateQueries({ queryKey: ["admission-lookup", activeRef] });
      setCustomReason("");
    },
  });

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ref.trim()) return;
    setActiveRef(ref.trim());
    setActionSuccess(null);
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

  return (
    <div className="space-y-6">
      <Card
        title="Admission Document Overrides & Exceptions"
        action={
          <span className="text-xs bg-amber-50 text-amber-800 border border-amber-200 font-medium px-2.5 py-1 rounded-full">
            Admin Scoped Exception Authorization
          </span>
        }
      >
        <p className="text-sm text-ink-soft mb-4">
          Authorize exceptions for missing mandatory admission documents (e.g. Birth Certificate, APAAR ID) for prospective applicants.
          This narrowly scoped interface records an immutable audit log and allows public drafts or admissions to proceed without granting access to general admission cell processing.
        </p>

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
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 shrink-0"
          >
            Lookup Draft
          </button>
        </form>

        {lookupQuery.isLoading && <p className="text-sm text-ink-faint">Searching application records...</p>}
        {lookupQuery.error && (
          <p className="text-sm text-danger">{errorText(lookupQuery.error)}</p>
        )}

        {actionSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-card text-sm mb-4">
            ✓ {actionSuccess}
          </div>
        )}

        {lookupQuery.data && (
          <div className="border border-rule rounded-card p-4 bg-ground space-y-4 mb-6">
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
                  className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {overrideMutation.isPending ? "Recording Authorization..." : "Authorize Document Exception"}
                </button>
              </div>
            </div>
          </div>
        )}
      </Card>

      <Card title="Authorized Overrides Audit Trail">
        <DataTable
          rows={overridesQuery.data ?? []}
          loading={overridesQuery.isLoading}
          error={overridesQuery.error}
          empty="No document overrides have been authorized yet."
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
            { key: "by", header: "Authorized By", render: (r) => r.authorized_by_name ?? "Admin" },
            {
              key: "date",
              header: "Authorized At",
              render: (r) => (r.authorized_at ? new Date(r.authorized_at).toLocaleDateString() : "-"),
            },
          ]}
        />
      </Card>
    </div>
  );
}
