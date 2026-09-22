import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { ActionButton } from "../../components/Can";
import { Card, DataTable, FormField, Modal, Pill, inputClass } from "../../components/ui";
import { useClasses } from "../useClasses";
import { ReportCardModal, type ReportCardPayload } from "./ReportCardModal";

type EnrolledStudent = {
  id: number;
  full_name: string;
  roll_no: number;
  admission_no: string;
};

type PublicationRecord = {
  id: number;
  document_no: string;
  enrolment_id: number;
  term: string;
  result_status: "pass" | "fail" | "withheld" | string;
  published_at: string;
};

type ReadinessInfo = {
  enrolment_id: number;
  term: string;
  unlocked_papers: { exam_schedule_id: number; subject_id: number }[];
  outstanding: string | number;
  already_published: boolean;
};

const PUBLISH_PERMISSION = "exam.result.publish";

export function ReportCardsTab() {
  const qc = useQueryClient();
  const classes = useClasses();

  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [term, setTerm] = useState<string>("Term 1");
  const [readinessData, setReadinessData] = useState<{ student: EnrolledStudent; readiness: ReadinessInfo } | null>(null);
  const [viewingCard, setViewingCard] = useState<ReportCardPayload | null>(null);
  const [releasingPub, setReleasingPub] = useState<PublicationRecord | null>(null);
  const [releaseReason, setReleaseReason] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Set default class when classes load
  if (!selectedClassId && classes.data && classes.data.length > 0) {
    setSelectedClassId(String(classes.data[0].id));
  }

  // Query roster for class
  const rosterQuery = useQuery({
    queryKey: ["class-roster", selectedClassId],
    enabled: Boolean(selectedClassId),
    queryFn: () =>
      api.get(`/admin/classes/${selectedClassId}/students` as "/admin/classes/{class_id}/students") as Promise<
        EnrolledStudent[]
      >,
  });

  // Query published report cards for this section and term
  const publicationsQuery = useQuery({
    queryKey: ["published-report-cards", selectedClassId, term],
    enabled: Boolean(selectedClassId),
    queryFn: () =>
      api.get(
        "/admin/report-cards" as "/admin/report-cards",
        `?class_section_id=${selectedClassId}&term=${encodeURIComponent(term)}`,
      ) as Promise<PublicationRecord[]>,
  });

  // Map student to publication
  const pubMap = new Map<number, PublicationRecord>();
  if (publicationsQuery.data) {
    for (const p of publicationsQuery.data) {
      pubMap.set(p.enrolment_id, p);
    }
  }

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: async (studentId: number) => {
      setErrorMessage(null);
      return (api.post as any)(
        `/admin/report-cards/publish?enrolment_id=${studentId}&term=${encodeURIComponent(term)}`,
        {},
      );
    },
    onSuccess: (data: any) => {
      qc.invalidateQueries({ queryKey: ["published-report-cards", selectedClassId, term] });
      setViewingCard(data);
    },
    onError: (err) => {
      setErrorMessage(errorText(err));
    },
  });

  // Release mutation
  const releaseMutation = useMutation({
    mutationFn: async ({ pubId, reason }: { pubId: number; reason: string }) => {
      setErrorMessage(null);
      return api.post(
        `/admin/report-cards/${pubId}/release` as "/admin/report-cards/{publication_id}/release",
        { reason } as any,
      );
    },
    onSuccess: (data: any) => {
      setReleasingPub(null);
      setReleaseReason("");
      qc.invalidateQueries({ queryKey: ["published-report-cards", selectedClassId, term] });
      setViewingCard(data);
    },
    onError: (err) => {
      setErrorMessage(errorText(err));
    },
  });

  // Check Readiness action
  const checkReadiness = async (student: EnrolledStudent) => {
    setErrorMessage(null);
    try {
      const res = (await api.get(
        "/admin/report-cards/readiness" as "/admin/report-cards/readiness",
        `?enrolment_id=${student.id}&term=${encodeURIComponent(term)}`,
      )) as ReadinessInfo;
      setReadinessData({ student, readiness: res });
    } catch (err) {
      setErrorMessage(errorText(err));
    }
  };

  // Preview Live Card action
  const previewLiveCard = async (student: EnrolledStudent) => {
    setErrorMessage(null);
    try {
      const res = (await api.get(
        "/admin/report-cards/preview" as "/admin/report-cards/preview",
        `?enrolment_id=${student.id}&term=${encodeURIComponent(term)}`,
      )) as ReportCardPayload;
      setViewingCard(res);
    } catch (err) {
      setErrorMessage(errorText(err));
    }
  };

  // View Issued Card action
  const viewIssuedCard = async (pubId: number) => {
    setErrorMessage(null);
    try {
      const res = (await api.get(
        `/admin/report-cards/${pubId}` as "/admin/report-cards/{publication_id}",
      )) as ReportCardPayload;
      setViewingCard(res);
    } catch (err) {
      setErrorMessage(errorText(err));
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Filter Bar */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <FormField label="Class Section">
              <select
                className={`${inputClass} min-w-[180px]`}
                value={selectedClassId}
                onChange={(e) => setSelectedClassId(e.target.value)}
              >
                {classes.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.class_label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Assessment Term">
              <select
                className={`${inputClass} min-w-[140px]`}
                value={term}
                onChange={(e) => setTerm(e.target.value)}
              >
                <option value="Term 1">Term 1</option>
                <option value="Term 2">Term 2</option>
              </select>
            </FormField>
          </div>

          <div className="text-right text-xs text-ink-soft">
            <p>
              Students: <b>{rosterQuery.data?.length ?? 0}</b> | Published:{" "}
              <b>{publicationsQuery.data?.length ?? 0}</b>
            </p>
            <p className="text-[11px] text-ink-faint mt-0.5">
              Withholdings apply automatically to fee defaulters (§0.6b).
            </p>
          </div>
        </div>
      </Card>

      {/* Error alert */}
      {errorMessage && (
        <div className="p-3.5 rounded-card bg-red-50 border border-red-200 text-xs text-danger font-medium">
          {errorMessage}
        </div>
      )}

      {/* Roster & Publication Table */}
      <Card title={`Report Cards: Class Section (${term})`}>
        <DataTable<EnrolledStudent>
          rows={rosterQuery.data ?? []}
          loading={rosterQuery.isLoading}
          error={rosterQuery.error}
          empty="No students found in this class section."
          columns={[
            {
              key: "roll",
              header: "Roll",
              render: (s) => <span className="tabular font-medium text-ink-soft">{s.roll_no || "-"}</span>,
            },
            {
              key: "name",
              header: "Student",
              render: (s) => (
                <div>
                  <p className="font-semibold text-ink">{s.full_name}</p>
                  <p className="text-[11px] text-ink-faint tabular">Adm: {s.admission_no}</p>
                </div>
              ),
            },
            {
              key: "status",
              header: "Publication Status",
              render: (s) => {
                const pub = pubMap.get(s.id);
                if (!pub) {
                  return <Pill status="pending">Not Published</Pill>;
                }
                if (pub.result_status === "withheld") {
                  return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-pill bg-red-100 text-red-800 text-xs font-bold">
                      ⚠️ WITHHELD (DUES)
                    </span>
                  );
                }
                return (
                  <div className="space-y-0.5">
                    <Pill status="paid">PUBLISHED</Pill>
                    <p className="text-[10px] font-mono text-primary font-bold">{pub.document_no}</p>
                  </div>
                );
              },
            },
            {
              key: "actions",
              header: "",
              align: "right",
              render: (s) => {
                const pub = pubMap.get(s.id);
                return (
                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => checkReadiness(s)}
                      className="px-2.5 py-1 text-xs text-ink-soft border border-rule rounded-input hover:bg-ground hover:text-ink font-medium"
                    >
                      Readiness
                    </button>

                    {pub ? (
                      <>
                        <button
                          type="button"
                          onClick={() => viewIssuedCard(pub.id)}
                          className="px-2.5 py-1 text-xs text-primary border border-primary/30 rounded-input hover:bg-primary/5 font-semibold"
                        >
                          View Issued
                        </button>
                        {pub.result_status === "withheld" && (
                          <ActionButton
                            permission={PUBLISH_PERMISSION}
                            className="px-2.5 py-1 text-xs !bg-amber-600 hover:!bg-amber-700 text-white"
                            onClick={() => setReleasingPub(pub)}
                          >
                            Release Withholding...
                          </ActionButton>
                        )}
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => previewLiveCard(s)}
                          className="px-2.5 py-1 text-xs text-primary border border-primary/30 rounded-input hover:bg-primary/5 font-semibold"
                        >
                          Preview Live
                        </button>
                        <ActionButton
                          permission={PUBLISH_PERMISSION}
                          className="px-2.5 py-1 text-xs"
                          disabled={publishMutation.isPending}
                          onClick={() => publishMutation.mutate(s.id)}
                        >
                          Publish
                        </ActionButton>
                      </>
                    )}
                  </div>
                );
              },
            },
          ]}
        />
      </Card>

      {/* Modal: Readiness Check */}
      {readinessData && (
        <Modal
          title={`Publication Readiness: ${readinessData.student.full_name}`}
          onClose={() => setReadinessData(null)}
        >
          <div className="space-y-4">
            <div className="rounded-card bg-ground p-4 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-ink-faint">Class & Term:</span>
                <span className="font-semibold text-ink">Class {selectedClassId} • {term}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-faint">Admission Number:</span>
                <span className="font-semibold text-ink">{readinessData.student.admission_no}</span>
              </div>
            </div>

            {/* Check 1: Paper Locks */}
            <div className="border border-rule rounded-card p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold text-ink">1. Examination Papers Locked</span>
                {readinessData.readiness.unlocked_papers.length === 0 ? (
                  <span className="text-xs text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                    ✓ All papers locked
                  </span>
                ) : (
                  <span className="text-xs text-danger font-bold bg-red-50 px-2 py-0.5 rounded">
                    ✗ {readinessData.readiness.unlocked_papers.length} paper(s) unlocked
                  </span>
                )}
              </div>
              {readinessData.readiness.unlocked_papers.length > 0 && (
                <p className="text-xs text-danger">
                  Results cannot be published until every paper for this term is locked against marks entry (§5.4.9).
                </p>
              )}
            </div>

            {/* Check 2: Outstanding Fee Dues */}
            <div className="border border-rule rounded-card p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold text-ink">2. Fee Ledger Clearance</span>
                {Number(readinessData.readiness.outstanding) > 0 ? (
                  <span className="text-xs text-amber-800 font-bold bg-amber-100 px-2 py-0.5 rounded">
                    ⚠️ Dues: ₹{readinessData.readiness.outstanding}
                  </span>
                ) : (
                  <span className="text-xs text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                    ✓ Dues Cleared (₹0.00)
                  </span>
                )}
              </div>
              {Number(readinessData.readiness.outstanding) > 0 ? (
                <p className="text-xs text-amber-800">
                  Under school policy (§0.6b), publishing now will issue this report card with <b>WITHHELD</b> status. The family will not receive official grades until dues are settled.
                </p>
              ) : (
                <p className="text-xs text-ink-soft">
                  Student is clear of fee arrears. Report card will publish with standard PASS status.
                </p>
              )}
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-rule">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setReadinessData(null)}
              >
                Close
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const student = readinessData.student;
                    setReadinessData(null);
                    previewLiveCard(student);
                  }}
                  className="px-3 py-1.5 text-xs text-primary border border-primary/30 rounded-input hover:bg-primary/5 font-semibold"
                >
                  Preview Card
                </button>

                {!readinessData.readiness.already_published && (
                  <ActionButton
                    permission={PUBLISH_PERMISSION}
                    disabled={readinessData.readiness.unlocked_papers.length > 0 || publishMutation.isPending}
                    onClick={() => {
                      const studentId = readinessData.student.id;
                      setReadinessData(null);
                      publishMutation.mutate(studentId);
                    }}
                  >
                    {readinessData.readiness.unlocked_papers.length > 0
                      ? "Locked Papers Required"
                      : Number(readinessData.readiness.outstanding) > 0
                      ? "Publish Withheld"
                      : "Publish Now"}
                  </ActionButton>
                )}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Release Withholding */}
      {releasingPub && (
        <Modal
          title={`Release Withheld Report Card (${releasingPub.document_no})`}
          onClose={() => setReleasingPub(null)}
        >
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              Lifting a withholding transitions the report card to standard released status. This action is permanently logged in the audit trail (§0.6b).
            </p>

            <FormField label="Audited Release Reason *">
              <textarea
                className={`${inputClass} min-h-[80px]`}
                placeholder="e.g. Fees cleared at counter via receipt #RCP-1029 or Hardship waiver approved by Management"
                value={releaseReason}
                onChange={(e) => setReleaseReason(e.target.value)}
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setReleasingPub(null)}
              >
                Cancel
              </button>
              <ActionButton
                permission={PUBLISH_PERMISSION}
                disabled={releaseReason.trim().length < 3 || releaseMutation.isPending}
                onClick={() => releaseMutation.mutate({ pubId: releasingPub.id, reason: releaseReason.trim() })}
              >
                {releaseMutation.isPending ? "Releasing..." : "Confirm & Release Card"}
              </ActionButton>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Report Card Viewer (Preview or Issued) */}
      {viewingCard && (
        <ReportCardModal card={viewingCard} onClose={() => setViewingCard(null)} />
      )}
    </div>
  );
}
