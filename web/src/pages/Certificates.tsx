import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api, tokenStore, API_BASE_URL } from "../api/client";
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

type CertificateItem = {
  id: number;
  certificate_no: string;
  certificate_type: "transfer_certificate" | "bonafide_certificate" | "character_certificate";
  student_id: number;
  student_name: string;
  admission_no: string;
  enrolment_id: number | null;
  canonical_enrolment_id: string;
  class_label: string | null;
  status: "requested" | "approved" | "issued" | "reissued" | "rejected";
  issue_date: string | null;
  issued_by_name: string | null;
  requested_by_name: string | null;
  is_reissue: boolean;
  reissue_count: number;
  reissue_reason: string | null;
};

type TemplateData = {
  id?: number;
  certificate_type: string;
  title: string;
  header_text: string | null;
  body_template: string | null;
  signatory_name: string | null;
  signatory_title: string | null;
  show_seal: boolean;
};

export function Certificates() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const [tab, setTab] = useState<"registry" | "templates">("registry");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  // Request / Issue Modal
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [targetStudentSearch, setTargetStudentSearch] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<{ id: number; name: string; enr: string; class: string } | null>(null);
  const [certType, setCertType] = useState<"transfer_certificate" | "bonafide_certificate" | "character_certificate">("bonafide_certificate");
  const [reqReason, setReqReason] = useState("Higher education admission requirement");
  const [reqRemarks, setReqRemarks] = useState("");
  const [leavingDate, setLeavingDate] = useState(new Date().toISOString().slice(0, 10));

  // TC Exit Warning Modal
  const [tcConfirmModalOpen, setTcConfirmModalOpen] = useState(false);

  // Reject Modal
  const [rejectingCert, setRejectingCert] = useState<CertificateItem | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // Reissue Modal
  const [reissuingCert, setReissuingCert] = useState<CertificateItem | null>(null);

  // Template Editor State
  const [editingTemplateType, setEditingTemplateType] = useState<"transfer_certificate" | "bonafide_certificate" | "character_certificate">("transfer_certificate");
  const [templateSavedMsg, setTemplateSavedMsg] = useState<string | null>(null);

  // Queries
  const certsQuery = useQuery({
    queryKey: ["certificates", typeFilter, statusFilter, searchQuery],
    queryFn: () => {
      const params = new URLSearchParams();
      if (typeFilter) params.set("cert_type", typeFilter);
      if (statusFilter) params.set("status", statusFilter);
      if (searchQuery) params.set("q", searchQuery);
      return api.rawGet<{ items: CertificateItem[]; total: number }>(`/admin/certificates?${params.toString()}`);
    },
  });

  const templateQuery = useQuery({
    queryKey: ["certificate-template", editingTemplateType],
    queryFn: () =>
      api.rawGet<TemplateData>(`/admin/certificates/templates/${editingTemplateType}`),
    enabled: tab === "templates",
  });

  // Student Search Query for new issuance
  const studentSearchQuery = useQuery({
    queryKey: ["cert-student-search", targetStudentSearch],
    queryFn: () =>
      api.rawGet<{ items: Array<{ id: number; full_name: string; admission_no: string; class_label: string }> }>(
        `/admin/students?q=${encodeURIComponent(targetStudentSearch)}&page_size=5`,
      ),
    enabled: targetStudentSearch.trim().length >= 2,
  });

  // Mutations
  const requestMutation = useMutation({
    mutationFn: async () => {
      if (!selectedStudent) throw new Error("No student selected");
      return api.rawPost("/admin/certificates/requests", {
        student_id: selectedStudent.id,
        certificate_type: certType,
        reason: reqReason,
        purpose: reqRemarks || null,
      });
    },
    onSuccess: () => {
      setRequestModalOpen(false);
      setSelectedStudent(null);
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
  });

  const issueMutation = useMutation({
    mutationFn: async (vars: { certId?: number; studentId?: number; type?: string; leavingDate?: string }) => {
      return api.rawPost("/admin/certificates/issue", {
        certificate_id: vars.certId ?? null,
        student_id: vars.studentId ?? null,
        certificate_type: vars.type ?? null,
        leaving_date: vars.leavingDate ?? null,
        conduct: "Good",
        remarks: reqRemarks || null,
      });
    },
    onSuccess: () => {
      setRequestModalOpen(false);
      setTcConfirmModalOpen(false);
      setSelectedStudent(null);
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (certId: number) => {
      return api.rawPost(`/admin/certificates/${certId}/approve`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ certId, reason }: { certId: number; reason: string }) => {
      return api.rawPost(`/admin/certificates/${certId}/reject`, { rejection_reason: reason });
    },
    onSuccess: () => {
      setRejectingCert(null);
      setRejectReason("");
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
  });

  const reissueMutation = useMutation({
    mutationFn: async ({ certId, reason }: { certId: number; reason: string }) => {
      return api.rawPost(`/admin/certificates/${certId}/reissue`, { reason });
    },
    onSuccess: () => {
      setReissuingCert(null);
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
  });

  const saveTemplateMutation = useMutation({
    mutationFn: async (tmpl: TemplateData) => {
      return api.rawPost(`/admin/certificates/templates/${editingTemplateType}`, {
        title: tmpl.title,
        header_text: tmpl.header_text,
        body_template: tmpl.body_template,
        signatory_name: tmpl.signatory_name,
        signatory_title: tmpl.signatory_title,
        show_seal: tmpl.show_seal,
      });
    },
    onSuccess: () => {
      setTemplateSavedMsg("Certificate template successfully updated.");
      qc.invalidateQueries({ queryKey: ["certificate-template", editingTemplateType] });
      setTimeout(() => setTemplateSavedMsg(null), 4000);
    },
  });

  const downloadPdf = async (certId: number) => {
    try {
      const token = tokenStore.get();
      const res = await fetch(`${API_BASE_URL}/admin/certificates/${certId}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Could not download certificate PDF");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `certificate-${certId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error generating certificate PDF: " + errorText(err));
    }
  };

  const handleStartIssuance = () => {
    if (!selectedStudent) return;
    if (certType === "transfer_certificate") {
      setTcConfirmModalOpen(true);
    } else {
      issueMutation.mutate({
        studentId: selectedStudent.id,
        type: certType,
      });
    }
  };

  const handleConfirmTcIssuance = () => {
    if (!selectedStudent) return;
    issueMutation.mutate({
      studentId: selectedStudent.id,
      type: "transfer_certificate",
      leavingDate,
    });
  };

  const formatCertType = (type: string) => {
    switch (type) {
      case "transfer_certificate":
        return "Transfer Certificate (TC)";
      case "bonafide_certificate":
        return "Bonafide Certificate";
      case "character_certificate":
        return "Character Certificate";
      default:
        return type.replace(/_/g, " ");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Student Certificates</h1>
          <p className="text-sm text-ink-soft">
            Manage request, approval, and issuance of Transfer, Bonafide, and Character Certificates.
          </p>
        </div>

        <div className="flex gap-2">
          {can("certificates.request") && (
            <button
              onClick={() => {
                setSelectedStudent(null);
                setRequestModalOpen(true);
              }}
              className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90"
            >
              + Issue / Request Certificate
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-rule gap-6">
        <button
          onClick={() => setTab("registry")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "registry"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Certificate Registry & Requests ({certsQuery.data?.total ?? 0})
        </button>
        <button
          onClick={() => setTab("templates")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "templates"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Institutional Templates
        </button>
      </div>

      {/* Registry Tab */}
      {tab === "registry" && (
        <Card
          title="Issued Certificates & Pending Requests"
          action={
            <div className="flex flex-wrap gap-2">
              <input
                type="text"
                className={`${inputClass} !w-44`}
                placeholder="Search student or cert no..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <select
                className={`${inputClass} !w-36`}
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Types</option>
                <option value="transfer_certificate">Transfer Certificate</option>
                <option value="bonafide_certificate">Bonafide Certificate</option>
                <option value="character_certificate">Character Certificate</option>
              </select>
              <select
                className={`${inputClass} !w-32`}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="requested">Requested</option>
                <option value="approved">Approved</option>
                <option value="issued">Issued</option>
                <option value="reissued">Reissued</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          }
        >
          <DataTable
            rows={certsQuery.data?.items ?? []}
            loading={certsQuery.isLoading}
            error={certsQuery.error}
            empty="No certificates found matching criteria."
            columns={[
              {
                key: "no",
                header: "Certificate No.",
                render: (r) => (
                  <span className="font-mono text-xs font-semibold text-primary">
                    {r.certificate_no || `REQ-${r.id}`}
                  </span>
                ),
              },
              {
                key: "type",
                header: "Type",
                render: (r) => (
                  <div>
                    <p className="font-medium text-xs">{formatCertType(r.certificate_type)}</p>
                    {r.is_reissue && (
                      <span className="text-[11px] bg-amber-100 text-amber-900 px-1.5 py-0.5 rounded font-medium">
                        Duplicate (v{r.reissue_count + 1})
                      </span>
                    )}
                  </div>
                ),
              },
              {
                key: "student",
                header: "Student & Enrolment",
                render: (r) => (
                  <div>
                    <p className="font-medium text-xs text-ink">{r.student_name}</p>
                    <p className="font-mono text-ink-soft text-[11px]">
                      {r.canonical_enrolment_id} • {r.class_label ? `Class ${r.class_label}` : "-"}
                    </p>
                  </div>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (r) => <Pill status={r.status}>{r.status}</Pill>,
              },
              {
                key: "date",
                header: "Date",
                render: (r) => <span className="text-xs">{r.issue_date ?? "-"}</span>,
              },
              {
                key: "actions",
                header: "Actions",
                align: "right",
                render: (r) => (
                  <div className="flex gap-2 justify-end">
                    {r.status === "requested" && can("certificates.approve") && (
                      <>
                        <button
                          onClick={() => approveMutation.mutate(r.id)}
                          disabled={approveMutation.isPending}
                          className="rounded bg-emerald-600 text-white px-2 py-1 text-xs font-medium hover:bg-emerald-700"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => setRejectingCert(r)}
                          className="rounded bg-danger/10 text-danger px-2 py-1 text-xs font-medium hover:bg-danger/20"
                        >
                          Reject
                        </button>
                      </>
                    )}

                    {r.status === "approved" && can("certificates.issue") && (
                      <button
                        onClick={() => {
                          if (r.certificate_type === "transfer_certificate") {
                            setSelectedStudent({
                              id: r.student_id,
                              name: r.student_name,
                              enr: r.canonical_enrolment_id,
                              class: r.class_label ?? "",
                            });
                            setTcConfirmModalOpen(true);
                          } else {
                            issueMutation.mutate({ certId: r.id });
                          }
                        }}
                        disabled={issueMutation.isPending}
                        className="rounded bg-primary text-white px-2 py-1 text-xs font-medium hover:bg-primary/90"
                      >
                        Issue
                      </button>
                    )}

                    {(r.status === "issued" || r.status === "reissued") && (
                      <>
                        <button
                          onClick={() => downloadPdf(r.id)}
                          className="rounded border border-rule px-2 py-1 text-xs font-medium hover:bg-ground flex items-center gap-1"
                        >
                          <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          PDF
                        </button>
                        {can("certificates.issue") && (
                          <button
                            onClick={() => setReissuingCert(r)}
                            className="rounded border border-rule px-2 py-1 text-xs hover:bg-ground"
                          >
                            Reissue
                          </button>
                        )}
                      </>
                    )}
                  </div>
                ),
              },
            ]}
          />
        </Card>
      )}

      {/* Templates Tab */}
      {tab === "templates" && (
        <Card title="Certificate Header & Institutional Wording Templates">
          <div className="space-y-4 max-w-2xl">
            <FormField label="Select Certificate Type to Configure">
              <select
                className={inputClass}
                value={editingTemplateType}
                onChange={(e) =>
                  setEditingTemplateType(
                    e.target.value as "transfer_certificate" | "bonafide_certificate" | "character_certificate",
                  )
                }
              >
                <option value="transfer_certificate">Transfer Certificate (TC)</option>
                <option value="bonafide_certificate">Bonafide Certificate</option>
                <option value="character_certificate">Character Certificate</option>
              </select>
            </FormField>

            {templateQuery.isLoading && <p className="text-xs text-ink-faint">Loading template...</p>}

            {templateQuery.data && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.target as HTMLFormElement;
                  const title = (form.elements.namedItem("tmpl_title") as HTMLInputElement).value;
                  const headerText = (form.elements.namedItem("tmpl_header") as HTMLInputElement).value;
                  const bodyTemplate = (form.elements.namedItem("tmpl_body") as HTMLTextAreaElement).value;
                  const signatoryName = (form.elements.namedItem("tmpl_sig_name") as HTMLInputElement).value;
                  const signatoryTitle = (form.elements.namedItem("tmpl_sig_title") as HTMLInputElement).value;
                  const showSeal = (form.elements.namedItem("tmpl_seal") as HTMLInputElement).checked;

                  saveTemplateMutation.mutate({
                    certificate_type: editingTemplateType,
                    title,
                    header_text: headerText,
                    body_template: bodyTemplate,
                    signatory_name: signatoryName,
                    signatory_title: signatoryTitle,
                    show_seal: showSeal,
                  });
                }}
                className="space-y-4"
              >
                <FormField label="Official Document Title">
                  <input
                    name="tmpl_title"
                    type="text"
                    className={inputClass}
                    defaultValue={templateQuery.data.title}
                    required
                  />
                </FormField>

                <FormField label="Affiliation / Header Subtext">
                  <input
                    name="tmpl_header"
                    type="text"
                    className={inputClass}
                    defaultValue={templateQuery.data.header_text || ""}
                    placeholder="e.g. Recognized & Affiliated to CBSE New Delhi"
                  />
                </FormField>

                <FormField label="Body Verification Wording">
                  <textarea
                    name="tmpl_body"
                    rows={3}
                    className={inputClass}
                    defaultValue={templateQuery.data.body_template || ""}
                  />
                </FormField>

                <div className="grid grid-cols-2 gap-3">
                  <FormField label="Signatory Name">
                    <input
                      name="tmpl_sig_name"
                      type="text"
                      className={inputClass}
                      defaultValue={templateQuery.data.signatory_name || "Principal"}
                    />
                  </FormField>

                  <FormField label="Signatory Designation">
                    <input
                      name="tmpl_sig_title"
                      type="text"
                      className={inputClass}
                      defaultValue={templateQuery.data.signatory_title || "Principal / Head of Institution"}
                    />
                  </FormField>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    name="tmpl_seal"
                    type="checkbox"
                    id="showSealCheck"
                    defaultChecked={templateQuery.data.show_seal}
                    className="rounded border-rule text-primary focus:ring-primary"
                  />
                  <label htmlFor="showSealCheck" className="text-sm font-medium text-ink">
                    Display Official School Seal Box on PDF
                  </label>
                </div>

                {templateSavedMsg && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-card text-xs">
                    ✓ {templateSavedMsg}
                  </div>
                )}

                <FormError error={saveTemplateMutation.error} />

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={saveTemplateMutation.isPending}
                    className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                  >
                    {saveTemplateMutation.isPending ? "Saving..." : "Save Template Changes"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </Card>
      )}

      {/* Request / Direct Issue Modal */}
      {requestModalOpen && (
        <Modal title="Generate / Request Student Certificate" onClose={() => setRequestModalOpen(false)}>
          <div className="space-y-4">
            {!selectedStudent ? (
              <div className="space-y-2">
                <FormField label="Search Student by Name or Admission No.">
                  <input
                    type="text"
                    className={inputClass}
                    placeholder="Type at least 2 characters..."
                    value={targetStudentSearch}
                    onChange={(e) => setTargetStudentSearch(e.target.value)}
                  />
                </FormField>

                {studentSearchQuery.data && (
                  <div className="border border-rule rounded divide-y divide-rule max-h-48 overflow-y-auto">
                    {studentSearchQuery.data.items.map((s) => (
                      <div
                        key={s.id}
                        onClick={() =>
                          setSelectedStudent({
                            id: s.id,
                            name: s.full_name,
                            enr: s.admission_no,
                            class: s.class_label,
                          })
                        }
                        className="p-2 text-sm hover:bg-ground cursor-pointer flex justify-between items-center"
                      >
                        <div>
                          <p className="font-semibold">{s.full_name}</p>
                          <p className="text-xs text-ink-soft">Adm No: {s.admission_no} • Class {s.class_label}</p>
                        </div>
                        <span className="text-xs text-primary font-medium">Select →</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-3 bg-ground border border-rule rounded-card flex justify-between items-center">
                <div>
                  <p className="font-semibold text-sm">{selectedStudent.name}</p>
                  <p className="text-xs text-ink-soft">
                    Adm: {selectedStudent.enr} • Class {selectedStudent.class}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedStudent(null)}
                  className="text-xs text-ink-faint hover:text-ink underline"
                >
                  Change
                </button>
              </div>
            )}

            <FormField label="Certificate Type">
              <select
                className={inputClass}
                value={certType}
                onChange={(e) =>
                  setCertType(
                    e.target.value as "transfer_certificate" | "bonafide_certificate" | "character_certificate",
                  )
                }
              >
                <option value="bonafide_certificate">Bonafide Certificate</option>
                <option value="character_certificate">Character Certificate</option>
                <option value="transfer_certificate">Transfer Certificate (TC - Student Exit)</option>
              </select>
            </FormField>

            <FormField label="Reason / Purpose">
              <input
                type="text"
                className={inputClass}
                value={reqReason}
                onChange={(e) => setReqReason(e.target.value)}
                required
              />
            </FormField>

            <FormField label="Additional Remarks (Optional)">
              <input
                type="text"
                className={inputClass}
                value={reqRemarks}
                onChange={(e) => setReqRemarks(e.target.value)}
              />
            </FormField>

            <FormError error={requestMutation.error || issueMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setRequestModalOpen(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={() => requestMutation.mutate()}
                disabled={requestMutation.isPending || !selectedStudent}
                className="rounded-input border border-primary text-primary px-4 py-2 text-sm font-medium hover:bg-primary/5 disabled:opacity-50"
              >
                Submit Request
              </button>

              {can("certificates.issue") && (
                <button
                  type="button"
                  onClick={handleStartIssuance}
                  disabled={issueMutation.isPending || !selectedStudent}
                  className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  Direct Issue
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Transfer Certificate Exit Confirmation Invariant Modal */}
      {tcConfirmModalOpen && selectedStudent && (
        <Modal title="CONFIRM TRANSFER CERTIFICATE ISSUANCE (CRITICAL ACTION)" onClose={() => setTcConfirmModalOpen(false)}>
          <div className="space-y-4">
            <div className="p-4 bg-danger/10 border-2 border-danger/30 rounded-card text-danger">
              <div className="flex items-center gap-2 mb-2 font-bold text-sm">
                <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                STUDENT STATUS TRANSITION WARNING
              </div>
              <p className="text-xs leading-relaxed text-ink font-medium">
                Issuing a <strong>Transfer Certificate (TC)</strong> will officially record the exit of <strong>{selectedStudent.name}</strong> from Sunrise School.
              </p>
              <ul className="list-disc list-inside text-xs mt-2 space-y-1 text-ink-soft">
                <li>Student lifecycle and active enrolment will atomically transition to <strong>transferred_out</strong>.</li>
                <li>All historical academic grades, fee ledgers, and library circulation records are <strong>permanently preserved</strong>.</li>
                <li>The student will no longer appear on active daily attendance rosters.</li>
              </ul>
            </div>

            <FormField label="Official School Leaving Date">
              <input
                type="date"
                className={inputClass}
                value={leavingDate}
                onChange={(e) => setLeavingDate(e.target.value)}
                required
              />
            </FormField>

            <FormError error={issueMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setTcConfirmModalOpen(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmTcIssuance}
                disabled={issueMutation.isPending}
                className="rounded-input bg-danger px-4 py-2 text-white text-sm font-semibold hover:bg-danger/90 disabled:opacity-50"
              >
                {issueMutation.isPending ? "Issuing TC & Exiting Student..." : "Confirm TC Issuance & Student Exit"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reject Modal */}
      {rejectingCert && (
        <Modal title="Reject Certificate Request" onClose={() => setRejectingCert(null)}>
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              Specify the administrative or disciplinary reason for rejecting this certificate request for{" "}
              <strong>{rejectingCert.student_name}</strong>.
            </p>
            <FormField label="Rejection Reason">
              <textarea
                className={inputClass}
                rows={2}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                required
              />
            </FormField>
            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setRejectingCert(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  rejectMutation.mutate({
                    certId: rejectingCert.id,
                    reason: rejectReason,
                  })
                }
                disabled={rejectMutation.isPending || !rejectReason.trim()}
                className="rounded-input bg-danger px-4 py-2 text-white text-sm font-medium hover:bg-danger/90 disabled:opacity-50"
              >
                {rejectMutation.isPending ? "Rejecting..." : "Confirm Rejection"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Reissue Dialog */}
      {reissuingCert && (
        <ConfirmDialog
          title="Reissue Official Certificate (Duplicate)"
          intent={
            <div className="space-y-2">
              <p>
                Reissuing will generate an official Duplicate Certificate marked with a watermark and incremented reissue count.
              </p>
              <p className="font-semibold text-xs">
                Original Certificate #{reissuingCert.certificate_no} for {reissuingCert.student_name}
              </p>
            </div>
          }
          confirmLabel="Reissue Certificate"
          busy={reissueMutation.isPending}
          error={reissueMutation.error}
          onConfirm={(reason) =>
            reissueMutation.mutate({
              certId: reissuingCert.id,
              reason,
            })
          }
          onClose={() => setReissuingCert(null)}
        />
      )}
    </div>
  );
}
