import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money, newIdempotencyKey } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { ActionButton, Can } from "../../components/Can";
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
} from "../../components/ui";
import { useClasses } from "../useClasses";
import { PrintableFeeReceipt } from "../../components/admission/PrintableFeeReceipt";
import { PrintableAdmissionDossier } from "../../components/admission/PrintableAdmissionDossier";
import { DossierEnrollmentResult } from "../../components/admission/dossier/DossierEnrollmentResult";
import { DossierStudentDetails } from "../../components/admission/dossier/DossierStudentDetails";
import { DossierAdmissionDetails } from "../../components/admission/dossier/DossierAdmissionDetails";
import { DossierGuardians } from "../../components/admission/dossier/DossierGuardians";
import { DossierSiblings } from "../../components/admission/dossier/DossierSiblings";
import { DossierAddress } from "../../components/admission/dossier/DossierAddress";
import { DossierPreviousSchool } from "../../components/admission/dossier/DossierPreviousSchool";
import { DossierMedical } from "../../components/admission/dossier/DossierMedical";
import { DossierDeclarations } from "../../components/admission/dossier/DossierDeclarations";
import type {
  AdmissionCycle,
  AdmissionDecision,
  ApplicationDetail,
  ApplicationMedical,
  ApplicationPayment,
  ApplicationRow,
  ChecklistResponse,
  ConversionPreview,
  EvaluationResponse,
  GuardianOut,
  OfferOut,
  SiblingOut,
} from "./types";

const asDate = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleDateString("en-GB") : "—";

export function Applications() {
  const [term, setTerm] = useState("");
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [classFilter, setClassFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<
    | "student_admission"
    | "guardians"
    | "siblings"
    | "address_school"
    | "medical"
    | "documents"
    | "declarations"
    | "evaluation"
    | "decision"
    | "conversion"
  >("student_admission");

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [lastEnrollmentResult, setLastEnrollmentResult] = useState<{
    receipt: ApplicationPayment;
    student?: {
      id?: number;
      admission_no?: string;
      class_label?: string;
      roll_no?: number;
    };
  } | null>(null);
  const [printingReceipt, setPrintingReceipt] = useState<ApplicationPayment | null>(null);
  const [printingDossier, setPrintingDossier] = useState(false);

  const classesQuery = useClasses();

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

  // Build query string
  const params: string[] = [];
  if (cycleId) params.push(`cycle_id=${cycleId}`);
  if (statusFilter) params.push(`status=${encodeURIComponent(statusFilter)}`);
  if (classFilter) params.push(`class_applying_for=${encodeURIComponent(classFilter)}`);
  if (categoryFilter) params.push(`category=${encodeURIComponent(categoryFilter)}`);
  if (term.trim()) params.push(`q=${encodeURIComponent(term.trim())}`);
  const queryString = params.length > 0 ? `?${params.join("&")}` : "";

  // Applications list query
  const applicationsQuery = useQuery({
    queryKey: [
      "admission-applications",
      cycleId,
      statusFilter,
      classFilter,
      categoryFilter,
      term,
    ],
    queryFn: () =>
      api.get(
        "/admin/admission/applications",
        queryString,
      ) as Promise<ApplicationRow[]>,
  });

  // Application 360 Detail query
  const appDetailQuery = useQuery({
    queryKey: ["admission-application-detail", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}` as "/admin/admission/applications/{application_id}",
      ) as Promise<ApplicationDetail>,
    enabled: selectedAppId !== null,
  });

  // Documents query
  const documentsQuery = useQuery({
    queryKey: ["admission-application-documents", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/documents` as "/admin/admission/applications/{application_id}/documents",
      ) as Promise<ChecklistResponse>,
    enabled: selectedAppId !== null && (activeTab === "documents" || printingDossier),
  });

  // Evaluation query
  const evaluationQuery = useQuery({
    queryKey: ["admission-application-evaluation", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/evaluation` as "/admin/admission/applications/{application_id}/evaluation",
      ) as Promise<EvaluationResponse>,
    enabled: selectedAppId !== null && activeTab === "evaluation",
  });

  // Decisions query
  const decisionsQuery = useQuery({
    queryKey: ["admission-application-decisions", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/decisions` as "/admin/admission/applications/{application_id}/decisions",
      ) as Promise<AdmissionDecision[]>,
    enabled: selectedAppId !== null && activeTab === "decision",
  });

  // Payments query
  const paymentsQuery = useQuery({
    queryKey: ["admission-application-payments", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/payments` as "/admin/admission/applications/{application_id}/payments",
      ) as Promise<ApplicationPayment[]>,
    enabled: selectedAppId !== null && activeTab === "conversion",
  });

  // Conversion Preview query
  const conversionPreviewQuery = useQuery({
    queryKey: ["admission-application-conversion-preview", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/conversion-preview` as "/admin/admission/applications/{application_id}/conversion-preview",
      ) as Promise<ConversionPreview>,
    enabled: selectedAppId !== null && activeTab === "conversion",
  });

  // Medical info query
  const medicalQuery = useQuery({
    queryKey: ["admission-application-medical", selectedAppId],
    queryFn: () =>
      api.get(
        `/admin/admission/applications/${selectedAppId}/medical` as "/admin/admission/applications/{application_id}/medical",
      ) as Promise<ApplicationMedical>,
    enabled: selectedAppId !== null && (activeTab === "medical" || printingDossier),
  });

  // Create Application write
  const [createForm, setCreateForm] = useState({
    first_name: "",
    middle_name: "",
    last_name: "",
    date_of_birth: "2020-01-01",
    gender: "male",
    class_applying_for: "Class 1",
    stream: "",
    admission_category: "general",
    transport_required: false,
    source: "walk_in",
  });

  const createApplication = useWrite({
    write: (data: typeof createForm) =>
      api.post("/admin/admission/applications", {
        cycle_id: cycleId ?? undefined,
        first_name: data.first_name,
        middle_name: data.middle_name || undefined,
        last_name: data.last_name,
        date_of_birth: data.date_of_birth,
        gender: data.gender,
        class_applying_for: data.class_applying_for,
        stream: data.stream || undefined,
        admission_category: data.admission_category as any,
        transport_required: data.transport_required,
        source: data.source as any,
      } as any),
    invalidates: [["admission-applications"], ["admission-dashboard", cycleId]],
    onDone: (created: any) => {
      setShowCreateModal(false);
      if (created?.id) {
        setSelectedAppId(created.id);
        setActiveTab("student_admission");
      }
    },
  });

  // Patch Application Details write (for child details, preferences, address, school, declarations)
  const patchApplication = useWrite({
    write: (data: Partial<ApplicationDetail>) =>
      api.patch(
        `/admin/admission/applications/${selectedAppId}` as "/admin/admission/applications/{application_id}",
        data as any,
      ),
    invalidates: [
      ["admission-applications"],
      ["admission-application-detail", selectedAppId],
      ["admission-dashboard", cycleId],
    ],
  });

  // Submit Application write
  const submitApplication = useWrite({
    write: () =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/submit` as "/admin/admission/applications/{application_id}/submit",
      ),
    invalidates: [
      ["admission-applications"],
      ["admission-application-detail", selectedAppId],
      ["admission-dashboard", cycleId],
    ],
  });

  // Move Status write
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [targetStatus, setTargetStatus] = useState<string>("under_document_verification");
  const moveStatus = useWrite({
    write: ({ status, reason }: { status: string; reason?: string }) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/status` as "/admin/admission/applications/{application_id}/status",
        {
          status: status as any,
          reason: reason || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-applications"],
      ["admission-application-detail", selectedAppId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => setShowStatusDialog(false),
  });

  // Verify Claims write
  const verifyClaims = useWrite({
    write: () =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/verify-claims` as "/admin/admission/applications/{application_id}/verify-claims",
      ),
    invalidates: [
      ["admission-applications"],
      ["admission-application-detail", selectedAppId],
    ],
  });

  // Guardians write
  const [showGuardianModal, setShowGuardianModal] = useState(false);
  const [guardiansList, setGuardiansList] = useState<GuardianOut[]>([]);
  const saveGuardians = useWrite({
    write: (list: GuardianOut[]) =>
      api.put(
        `/admin/admission/applications/${selectedAppId}/guardians` as "/admin/admission/applications/{application_id}/guardians",
        list.map((g) => ({
          relation: g.relation as any,
          full_name: g.full_name,
          date_of_birth: g.date_of_birth || undefined,
          qualification: g.qualification || undefined,
          occupation: g.occupation || undefined,
          designation: g.designation || undefined,
          organisation: g.organisation || undefined,
          annual_income_band: g.annual_income_band || undefined,
          office_address: g.office_address || undefined,
          mobile: g.mobile,
          alternate_mobile: g.alternate_mobile || undefined,
          email: g.email || undefined,
          is_primary: g.is_primary,
          is_emergency_contact: g.is_emergency_contact,
          is_authorised_for_pickup: g.is_authorised_for_pickup,
          is_school_alumnus: g.is_school_alumnus,
          is_school_staff: g.is_school_staff,
          employee_id: g.employee_id || undefined,
        })) as any,
      ),
    invalidates: [
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
    ],
    onDone: () => setShowGuardianModal(false),
  });

  // Sibling Search & Link
  const [showSiblingModal, setShowSiblingModal] = useState(false);
  const [siblingQueryTerm, setSiblingQueryTerm] = useState("");
  const siblingSearchResults = useQuery({
    queryKey: ["sibling-search", siblingQueryTerm],
    queryFn: () =>
      api.get(
        "/admin/admission/sibling-search",
        `?q=${encodeURIComponent(siblingQueryTerm)}`,
      ) as Promise<any[]>,
    enabled: siblingQueryTerm.length >= 2,
  });

  const saveSiblings = useWrite({
    write: (siblings: SiblingOut[]) =>
      api.put(
        `/admin/admission/applications/${selectedAppId}/siblings` as "/admin/admission/applications/{application_id}/siblings",
        siblings.map((s) => ({
          student_id: s.student_id || undefined,
          name: s.name || undefined,
          age: s.age || undefined,
          school_name: s.school_name || undefined,
        })) as any,
      ),
    invalidates: [
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
    ],
    onDone: () => setShowSiblingModal(false),
  });

  // Document upload & verification
  const [uploadCode, setUploadCode] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadCode || !selectedAppId) return;
    setUploadingDoc(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("code", uploadCode);
      formData.append("file", uploadFile);

      const token = localStorage.getItem("sunrise.token");
      const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
      const res = await fetch(
        `${base}/admin/admission/applications/${selectedAppId}/documents`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Upload failed");
      }
      setUploadCode("");
      setUploadFile(null);
      documentsQuery.refetch();
      appDetailQuery.refetch();
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload file");
    } finally {
      setUploadingDoc(false);
    }
  };

  // Verify Document write
  const [verifyingDocId, setVerifyingDocId] = useState<number | null>(null);
  const [verifyVerdict, setVerifyVerdict] = useState({
    approved: true,
    original_seen: true,
    reason: "",
  });

  const verifyDocument = useWrite({
    write: ({ id, approved, original_seen, reason }: any) =>
      api.post(
        `/admin/admission/documents/${id}/verify` as "/admin/admission/documents/{document_id}/verify",
        {
          approved,
          original_seen,
          reason: reason || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-application-documents", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
    ],
    onDone: () => setVerifyingDocId(null),
  });

  // Schedule Assessment write
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({
    assessment_type: "written_test",
    scheduled_at: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
    venue: "Main Examination Hall A",
    seat_no: "SEAT-101",
    subjects: [{ subject: "English", max_marks: "50" }, { subject: "Maths", max_marks: "50" }],
  });

  const scheduleAssessment = useWrite({
    write: (data: typeof assessmentForm) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/assessments` as "/admin/admission/applications/{application_id}/assessments",
        {
          assessment_type: data.assessment_type as any,
          scheduled_at: new Date(data.scheduled_at).toISOString(),
          venue: data.venue || undefined,
          seat_no: data.seat_no || undefined,
          subjects: data.subjects.map((s) => ({
            subject: s.subject,
            max_marks: s.max_marks,
          })),
        } as any,
      ),
    invalidates: [
      ["admission-application-evaluation", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
    ],
    onDone: () => setShowAssessmentModal(false),
  });

  // Enter Marks write
  const [scoringAssessmentId, setScoringAssessmentId] = useState<number | null>(null);
  const [marksForm, setMarksForm] = useState({
    obtained_marks: "85",
    total_marks: "100",
    is_absent: false,
    remarks: "Good performance in logical reasoning.",
    reason: "",
  });

  const recordMarks = useWrite({
    write: ({ id, data }: any) =>
      api.post(
        `/admin/admission/assessments/${id}/marks` as "/admin/admission/assessments/{assessment_id}/marks",
        {
          obtained_marks: data.is_absent ? undefined : data.obtained_marks,
          total_marks: data.total_marks,
          is_absent: data.is_absent,
          remarks: data.remarks || undefined,
          reason: data.reason || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-application-evaluation", selectedAppId],
      ["admission-application-detail", selectedAppId],
    ],
    onDone: () => setScoringAssessmentId(null),
  });

  // Schedule Interview write
  const [showInterviewModal, setShowInterviewModal] = useState(false);
  const [interviewForm, setInterviewForm] = useState({
    scheduled_at: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
    venue: "Principal's Office / Panel Room",
    panel_member_ids: [] as number[],
  });

  const scheduleInterview = useWrite({
    write: (data: typeof interviewForm) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/interviews` as "/admin/admission/applications/{application_id}/interviews",
        {
          scheduled_at: new Date(data.scheduled_at).toISOString(),
          venue: data.venue || undefined,
          panel_member_ids: data.panel_member_ids,
        } as any,
      ),
    invalidates: [
      ["admission-application-evaluation", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
    ],
    onDone: () => setShowInterviewModal(false),
  });

  // Panel Feedback write
  const [scoringInterviewId, setScoringInterviewId] = useState<number | null>(null);
  const [feedbackForm, setFeedbackForm] = useState({
    child_rating: 4,
    parent_rating: 4,
    recommendation: "admit",
    notes: "Articulate and confident child. Supportive parents.",
    reason: "",
  });

  const recordFeedback = useWrite({
    write: ({ id, data }: any) =>
      api.post(
        `/admin/admission/interviews/${id}/feedback` as "/admin/admission/interviews/{interview_id}/feedback",
        {
          child_rating: Number(data.child_rating),
          parent_rating: Number(data.parent_rating),
          recommendation: data.recommendation as any,
          notes: data.notes || undefined,
          reason: data.reason || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-application-evaluation", selectedAppId],
      ["admission-application-detail", selectedAppId],
    ],
    onDone: () => setScoringInterviewId(null),
  });

  // Decision write
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisionForm, setDecisionForm] = useState({
    decision: "admitted",
    reason: "Cleared entrance assessment and interview criteria.",
    seat_category: "general",
    conditions: "",
    over_allocation_approved: false,
  });

  const decideApplication = useWrite({
    write: (data: typeof decisionForm) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/decision` as "/admin/admission/applications/{application_id}/decision",
        {
          decision: data.decision as any,
          reason: data.reason,
          seat_category: data.seat_category || undefined,
          conditions: data.conditions || undefined,
          over_allocation_approved: data.over_allocation_approved,
        } as any,
      ),
    invalidates: [
      ["admission-application-decisions", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
      ["admission-seats", cycleId],
    ],
    onDone: () => setShowDecisionModal(false),
  });

  // Issue Offer write
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [offerForm, setOfferForm] = useState({
    expires_on: new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0],
    offer_amount: "25000.00",
  });

  const issueOffer = useWrite({
    write: (data: typeof offerForm) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/offer` as "/admin/admission/applications/{application_id}/offer",
        {
          expires_on: data.expires_on,
          offer_amount: data.offer_amount,
        } as any,
      ),
    invalidates: [
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => setShowOfferModal(false),
  });

  // Record Offer Response write
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [responseForm, setResponseForm] = useState({
    accepted: true,
    reason: "Parents visited school and accepted offer letter.",
  });

  const respondOffer = useWrite({
    write: (data: typeof responseForm) =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/offer/response` as "/admin/admission/applications/{application_id}/offer/response",
        {
          accepted: data.accepted,
          reason: data.reason || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
      ["admission-seats", cycleId],
    ],
    onDone: () => setShowResponseModal(false),
  });

  // Fee payment collect write
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentForm, setPaymentForm] = useState({
    purpose: "application_fee",
    amount: activeCycle?.application_fee ? String(activeCycle.application_fee) : "500.00",
    method: "cash",
    reference: "REC-" + Date.now().toString().slice(-6),
  });

  const collectPayment = useWrite({
    write: async (data: typeof paymentForm) => {
      const res = await api.post(
        `/admin/admission/applications/${selectedAppId}/payments` as "/admin/admission/applications/{application_id}/payments",
        {
          purpose: data.purpose as any,
          amount: data.amount,
          method: data.method,
          reference: data.reference || undefined,
          idempotency_key: newIdempotencyKey(),
        } as any,
      );
      if (res) {
        setLastEnrollmentResult({
          receipt: res as any,
          student: (res as any).student,
        });
      }
      return res;
    },
    invalidates: [
      ["admission-application-payments", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-application-conversion-preview", selectedAppId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
      ["students"],
    ],
    onDone: () => setShowPaymentModal(false),
  });

  // Void payment write
  const [voidingPaymentId, setVoidingPaymentId] = useState<number | null>(null);
  const voidPayment = useWrite({
    write: ({ id, reason }: { id: number; reason: string }) =>
      api.del(
        `/admin/admission/payments/${id}` as "/admin/admission/payments/{payment_id}",
        `?reason=${encodeURIComponent(reason)}`,
      ),
    invalidates: [
      ["admission-application-payments", selectedAppId],
      ["admission-application-detail", selectedAppId],
      ["admission-application-conversion-preview", selectedAppId],
    ],
    onDone: () => setVoidingPaymentId(null),
  });

  // Convert Application write
  const convertStudent = useWrite({
    write: () =>
      api.post(
        `/admin/admission/applications/${selectedAppId}/convert` as "/admin/admission/applications/{application_id}/convert",
      ),
    invalidates: [
      ["admission-application-detail", selectedAppId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
      ["admission-seats", cycleId],
      ["students"],
    ],
  });

  // Medical info write
  const [showMedicalModal, setShowMedicalModal] = useState(false);
  const [medicalForm, setMedicalForm] = useState<ApplicationMedical>({});
  const saveMedical = useWrite({
    write: (data: ApplicationMedical) =>
      api.put(
        `/admin/admission/applications/${selectedAppId}/medical` as "/admin/admission/applications/{application_id}/medical",
        {
          blood_group: data.blood_group || undefined,
          known_allergies: data.known_allergies || undefined,
          chronic_conditions: data.chronic_conditions || undefined,
          regular_medication: data.regular_medication || undefined,
          physical_disability: data.physical_disability || undefined,
          learning_needs: data.learning_needs || undefined,
          vision_hearing_notes: data.vision_hearing_notes || undefined,
          emergency_doctor: data.emergency_doctor || undefined,
          emergency_doctor_phone: data.emergency_doctor_phone || undefined,
          consent_for_emergency_treatment:
            data.consent_for_emergency_treatment ?? false,
        } as any,
      ),
    invalidates: [["admission-application-medical", selectedAppId]],
    onDone: () => setShowMedicalModal(false),
  });

  const applications = applicationsQuery.data ?? [];
  const appDetail = appDetailQuery.data ?? null;

  return (
    <div className="space-y-6">
      {/* Header & Main Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Application Register</h1>
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

          <ActionButton
            permission="admission.application.write"
            onClick={() => setShowCreateModal(true)}
          >
            + New application
          </ActionButton>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[220px]">
            <input
              className={inputClass}
              placeholder="Search applicant name or application no..."
              value={term}
              onChange={(e) => setTerm(e.target.value)}
            />
          </div>

          <select
            className={`${inputClass} w-auto`}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="submitted">Submitted</option>
            <option value="under_document_verification">Under Verification</option>
            <option value="documents_verified">Docs Verified</option>
            <option value="assessment_scheduled">Assessment Scheduled</option>
            <option value="assessment_completed">Assessment Completed</option>
            <option value="interview_scheduled">Interview Scheduled</option>
            <option value="interview_completed">Interview Completed</option>
            <option value="decision_pending">Decision Pending</option>
            <option value="admitted">Admitted</option>
            <option value="waitlisted">Waitlisted</option>
            <option value="offer_issued">Offer Issued</option>
            <option value="offer_accepted">Offer Accepted</option>
            <option value="fee_paid">Fee Paid</option>
            <option value="enrolled">Enrolled</option>
            <option value="rejected">Rejected</option>
          </select>

          <select
            className={`${inputClass} w-auto`}
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
          >
            <option value="">All Classes</option>
            {availableClasses.map((cl) => (
              <option key={cl.id} value={cl.class_name}>
                Class {cl.class_name}
              </option>
            ))}
          </select>

          <select
            className={`${inputClass} w-auto`}
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="general">General</option>
            <option value="sibling">Sibling</option>
            <option value="staff_ward">Staff Ward</option>
            <option value="rte">RTE</option>
            <option value="management">Management</option>
            <option value="sports">Sports</option>
            <option value="alumni_child">Alumni Child</option>
          </select>
        </div>
      </Card>

      {/* Applications Table */}
      <Card>
        <DataTable<ApplicationRow>
          loading={applicationsQuery.isLoading}
          error={applicationsQuery.error}
          empty={
            term || statusFilter || classFilter || categoryFilter
              ? "No applications match the search and filter criteria."
              : "No applications registered for this cycle yet. Click '+ New application' to open a draft."
          }
          onRowClick={(r) => {
            setSelectedAppId(r.id);
            setActiveTab("student_admission");
          }}
          columns={[
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
                  <p className="text-xs text-ink-soft">
                    DOB: {asDate(r.date_of_birth)} ({r.gender})
                  </p>
                </div>
              ),
            },
            {
              key: "class_applying_for",
              header: "Applied Class",
              render: (r) => (
                <span className="text-ink font-medium">
                  {r.class_applying_for} {r.stream ? `(${r.stream})` : ""}
                </span>
              ),
            },
            {
              key: "claims",
              header: "Category & Claims",
              render: (r) => (
                <div className="flex flex-wrap gap-1 items-center">
                  <span className="capitalize text-xs text-ink-soft bg-ground px-1.5 py-0.5 rounded border border-rule">
                    {r.admission_category.replace(/_/g, " ")}
                  </span>
                  {r.sibling_verified && (
                    <span className="bg-success/15 text-success text-2xs px-1 py-0.5 rounded font-semibold">
                      Sibling ✓
                    </span>
                  )}
                  {r.staff_ward_verified && (
                    <span className="bg-success/15 text-success text-2xs px-1 py-0.5 rounded font-semibold">
                      Staff Ward ✓
                    </span>
                  )}
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (r) => (
                <Pill
                  status={
                    r.status === "enrolled" || r.status === "admitted"
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
              key: "submitted_at",
              header: "Submitted",
              render: (r) => (
                <span className="text-xs text-ink-soft tabular">
                  {asDate(r.submitted_at)}
                </span>
              ),
            },
            {
              key: "actions",
              header: "",
              align: "right",
              render: (r) => (
                <button
                  type="button"
                  className="text-xs text-primary hover:underline font-medium"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAppId(r.id);
                    setActiveTab("student_admission");
                  }}
                >
                  360° Profile →
                </button>
              ),
            },
          ]}
          rows={applications}
        />
      </Card>

      {/* Modal: New Application Draft */}
      {showCreateModal && (
        <Modal
          title="New Application (Step 1: Open Draft)"
          onClose={() => setShowCreateModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createApplication.run(createForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-3 gap-3">
              <FormField
                label="First Name"
                error={createApplication.fields["first_name"]}
              >
                <input
                  required
                  className={inputClass}
                  placeholder="First name"
                  value={createForm.first_name}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      first_name: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Middle Name">
                <input
                  className={inputClass}
                  placeholder="Middle"
                  value={createForm.middle_name}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      middle_name: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField
                label="Last Name"
                error={createApplication.fields["last_name"]}
              >
                <input
                  required
                  className={inputClass}
                  placeholder="Last name"
                  value={createForm.last_name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, last_name: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Date of Birth"
                error={createApplication.fields["date_of_birth"]}
              >
                <input
                  type="date"
                  required
                  className={inputClass}
                  value={createForm.date_of_birth}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      date_of_birth: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Gender">
                <select
                  className={inputClass}
                  value={createForm.gender}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, gender: e.target.value })
                  }
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Class Applying For">
                <input
                  required
                  className={inputClass}
                  placeholder="e.g. Class 1"
                  value={createForm.class_applying_for}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      class_applying_for: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Stream (if higher secondary)">
                <input
                  className={inputClass}
                  placeholder="e.g. Science, Commerce"
                  value={createForm.stream}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, stream: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Admission Category Claimed">
                <select
                  className={inputClass}
                  value={createForm.admission_category}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      admission_category: e.target.value,
                    })
                  }
                >
                  <option value="general">General</option>
                  <option value="sibling">Sibling (Claim)</option>
                  <option value="staff_ward">Staff Ward (Claim)</option>
                  <option value="rte">RTE</option>
                  <option value="management">Management</option>
                  <option value="sports">Sports Quota</option>
                  <option value="alumni_child">Alumni Child</option>
                </select>
              </FormField>
              <FormField label="Source">
                <select
                  className={inputClass}
                  value={createForm.source}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, source: e.target.value })
                  }
                >
                  <option value="walk_in">Walk-in</option>
                  <option value="phone">Phone</option>
                  <option value="website">Website</option>
                  <option value="referral">Referral</option>
                  <option value="social_media">Social Media</option>
                </select>
              </FormField>
            </div>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.transport_required}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      transport_required: e.target.checked,
                    })
                  }
                />
                Requires School Bus / Transport Facility
              </label>
            </div>

            <FormError error={createApplication.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createApplication.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {createApplication.busy ? "Opening draft..." : "Open Draft Application"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* 360° Applicant Detail Modal */}
      {selectedAppId !== null && (
        <Modal
          title={`Applicant 360°: ${appDetail?.application_no ?? `App #${selectedAppId}`}`}
          wide
          onClose={() => setSelectedAppId(null)}
        >
          {appDetailQuery.isLoading ? (
            <Empty>Loading applicant details...</Empty>
          ) : appDetailQuery.error ? (
            <ErrorState error={appDetailQuery.error} />
          ) : appDetail ? (
            <div className="space-y-5">
              {/* Applicant Header Bar */}
              <div className="bg-ground rounded-input p-4 border border-rule flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-ink">{appDetail.name}</h2>
                    <Pill
                      status={
                        appDetail.status === "enrolled" || appDetail.status === "admitted"
                          ? "present"
                          : appDetail.status === "rejected"
                            ? "absent"
                            : "pending"
                      }
                    >
                      {appDetail.status.replace(/_/g, " ").toUpperCase()}
                    </Pill>
                    <span className="text-xs bg-surface px-2 py-0.5 rounded border border-rule text-ink-soft font-medium">
                      Class: {appDetail.class_applying_for} {appDetail.stream ? `(${appDetail.stream})` : ""}
                    </span>
                  </div>
                  <p className="text-xs text-ink-soft mt-1">
                    DOB: <span className="font-semibold tabular">{asDate(appDetail.date_of_birth)}</span> |
                    Gender: {appDetail.gender} | Effective Category:{" "}
                    <span className="font-semibold uppercase">{appDetail.effective_category}</span>
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="w-32 bg-rule rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-primary h-full transition-all"
                        style={{ width: `${appDetail.completeness_pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-ink-faint tabular">
                      {appDetail.completeness_pct}% complete
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-input text-xs font-medium border border-rule bg-surface text-ink hover:bg-ground transition-colors flex items-center gap-1.5"
                    onClick={() => setPrintingDossier(true)}
                  >
                    Print Dossier (PDF)
                  </button>

                  {appDetail.status === "draft" && (
                    <ActionButton
                      permission="admission.application.write"
                      onClick={() => submitApplication.run()}
                      disabled={submitApplication.busy}
                    >
                      {submitApplication.busy ? "Submitting..." : "Submit application"}
                    </ActionButton>
                  )}

                  <ActionButton
                    permission="admission.application.write"
                    onClick={() => {
                      setTargetStatus(appDetail.status);
                      setShowStatusDialog(true);
                    }}
                  >
                    Change status...
                  </ActionButton>
                </div>
              </div>

              {/* Official Enrollment Banner if enrolled or confirmed */}
              <DossierEnrollmentResult
                application={appDetail}
                onPrintDossier={() => setPrintingDossier(true)}
                onPrintReceipt={(r) => setPrintingReceipt(r)}
                recentPayment={lastEnrollmentResult?.receipt}
              />

              {/* Navigation Tabs */}
              <div className="flex border-b border-rule overflow-x-auto text-sm gap-1">
                {[
                  { id: "student_admission", label: "1. Student & Admission" },
                  {
                    id: "guardians",
                    label: `2. Parents & Guardians (${appDetail.guardians.length})`,
                  },
                  {
                    id: "siblings",
                    label: `3. Siblings & Claims (${appDetail.siblings.length})`,
                  },
                  { id: "address_school", label: "4. Address & Previous School" },
                  { id: "medical", label: "5. Medical Profile" },
                  { id: "documents", label: "6. Documents Checklist" },
                  { id: "declarations", label: "7. Declarations & Undertaking" },
                  { id: "evaluation", label: "8. Evaluation & Scoring" },
                  { id: "decision", label: "9. Decision & Offers" },
                  { id: "conversion", label: "10. Fees & Enrolment" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`px-3 py-2 font-medium border-b-2 whitespace-nowrap transition-colors ${
                      activeTab === tab.id
                        ? "border-primary text-primary"
                        : "border-transparent text-ink-soft hover:text-ink"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab 1: Student & Admission */}
              {activeTab === "student_admission" && (
                <div className="space-y-6">
                  <DossierStudentDetails
                    application={appDetail}
                    onSave={async (patch) => {
                      await patchApplication.runAsync(patch);
                    }}
                    isSaving={patchApplication.busy}
                  />
                  <DossierAdmissionDetails
                    application={appDetail}
                    availableClasses={availableClasses}
                    onSave={async (patch) => {
                      await patchApplication.runAsync(patch);
                    }}
                    isSaving={patchApplication.busy}
                  />
                </div>
              )}

              {/* Tab 2: Parents & Guardians */}
              {activeTab === "guardians" && (
                <DossierGuardians
                  application={appDetail}
                  onSave={async (guardians) => {
                    await saveGuardians.runAsync(guardians);
                  }}
                  isSaving={saveGuardians.busy}
                />
              )}

              {/* Tab 3: Siblings & Claims */}
              {activeTab === "siblings" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between bg-ground p-3 rounded-input border border-rule">
                    <div>
                      <h4 className="font-semibold text-ink text-sm">CBSE / Institutional Claims Authentication</h4>
                      <p className="text-xs text-ink-soft">
                        Verify sibling and staff-ward status against school active registers.
                      </p>
                    </div>
                    <ActionButton
                      permission="admission.application.write"
                      onClick={() => verifyClaims.run()}
                      disabled={verifyClaims.busy}
                    >
                      {verifyClaims.busy ? "Verifying claims..." : "Verify claims now"}
                    </ActionButton>
                  </div>

                  <DossierSiblings
                    application={appDetail}
                    onSave={async (siblings) => {
                      await saveSiblings.runAsync(siblings);
                    }}
                    isSaving={saveSiblings.busy}
                  />
                </div>
              )}

              {/* Tab 4: Address & Previous School */}
              {activeTab === "address_school" && (
                <div className="space-y-6">
                  <DossierAddress
                    application={appDetail}
                    onSave={async (patch) => {
                      await patchApplication.runAsync(patch);
                    }}
                    isSaving={patchApplication.busy}
                  />
                  <DossierPreviousSchool
                    application={appDetail}
                    onSave={async (patch) => {
                      await patchApplication.runAsync(patch);
                    }}
                    isSaving={patchApplication.busy}
                  />
                </div>
              )}

              {/* Tab 5: Medical Profile */}
              {activeTab === "medical" && (
                <Can
                  permission="admission.medical.read"
                  fallback={
                    <Empty>
                      Refused: Medical information is restricted and requires admission.medical.read permission.
                    </Empty>
                  }
                >
                  <DossierMedical
                    applicationId={appDetail.id}
                    medical={medicalQuery.data}
                    onSave={async (data) => {
                      await saveMedical.runAsync(data);
                    }}
                    isSaving={saveMedical.busy}
                  />
                </Can>
              )}

              {/* Tab 6: Documents Checklist */}
              {activeTab === "documents" && (
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-ink">Required Documents Checklist</h3>
                      <p className="text-xs text-ink-soft">
                        Upload documents and verify against physical originals.
                      </p>
                    </div>
                  </div>

                  {documentsQuery.isLoading ? (
                    <Empty>Loading checklist...</Empty>
                  ) : documentsQuery.data ? (
                    <div className="space-y-3">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-ink-faint border-b border-rule">
                              <th className="py-2 pr-4 font-medium">Document</th>
                              <th className="py-2 pr-4 font-medium">Requirement</th>
                              <th className="py-2 pr-4 font-medium">Status</th>
                              <th className="py-2 pr-4 font-medium">File Uploaded</th>
                              <th className="py-2 pr-4 font-medium text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {documentsQuery.data.items.map((doc) => (
                              <tr key={doc.code} className="border-b border-rule last:border-0">
                                <td className="py-2.5 pr-4 font-semibold text-ink">
                                  {doc.name}
                                </td>
                                <td className="py-2.5 pr-4 text-xs text-ink-soft">
                                  {doc.mandatory ? (
                                    <span className="text-danger font-medium">Mandatory</span>
                                  ) : (
                                    <span>Optional</span>
                                  )}
                                  {doc.is_conditional && doc.condition_category && (
                                    <span className="ml-1 text-ink-faint">
                                      (for {doc.condition_category})
                                    </span>
                                  )}
                                </td>
                                <td className="py-2.5 pr-4">
                                  <Pill
                                    status={
                                      doc.status === "verified"
                                        ? "present"
                                        : doc.status === "rejected"
                                          ? "absent"
                                          : "pending"
                                    }
                                  >
                                    {doc.status.replace(/_/g, " ").toUpperCase()}
                                  </Pill>
                                </td>
                                <td className="py-2.5 pr-4 text-xs">
                                  {doc.filename ? (
                                    <span className="font-mono text-ink-soft">{doc.filename}</span>
                                  ) : (
                                    <span className="text-ink-faint">Not uploaded</span>
                                  )}
                                </td>
                                <td className="py-2.5 pr-4 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    {doc.document_id ? (
                                      <>
                                        <button
                                          type="button"
                                          className="text-xs text-primary hover:underline font-medium"
                                          onClick={async () => {
                                            try {
                                              const res = (await api.get(
                                                `/admin/admission/documents/${doc.document_id}/url` as "/admin/admission/documents/{document_id}/url",
                                              )) as { url: string };
                                              window.open(res.url, "_blank");
                                            } catch (err) {
                                              alert("Could not load signed document URL.");
                                            }
                                          }}
                                        >
                                          Download / View
                                        </button>

                                        <ActionButton
                                          permission="admission.document.verify"
                                          className="px-2.5 py-0.5 text-xs"
                                          onClick={() => {
                                            setVerifyingDocId(doc.document_id);
                                            setVerifyVerdict({
                                              approved: true,
                                              original_seen: true,
                                              reason: "",
                                            });
                                          }}
                                        >
                                          Scrutiny verdict
                                        </ActionButton>
                                      </>
                                    ) : (
                                      <ActionButton
                                        permission="admission.application.write"
                                        className="px-2.5 py-0.5 text-xs"
                                        onClick={() => setUploadCode(doc.code)}
                                      >
                                        Upload file
                                      </ActionButton>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* File Upload Section */}
                      {uploadCode && (
                        <div className="bg-ground p-4 rounded-input border border-rule mt-4 space-y-3">
                          <h4 className="font-semibold text-ink text-sm">
                            Upload Document: {uploadCode}
                          </h4>
                          <form onSubmit={handleUploadDocument} className="flex flex-wrap items-center gap-3">
                            <input
                              type="file"
                              required
                              className="text-sm"
                              onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                            />
                            {uploadError && <p className="text-xs text-danger">{uploadError}</p>}
                            <div className="flex gap-2 ml-auto">
                              <button
                                type="button"
                                className="px-3 py-1 text-xs text-ink-soft"
                                onClick={() => {
                                  setUploadCode("");
                                  setUploadFile(null);
                                }}
                              >
                                Cancel
                              </button>
                              <button
                                type="submit"
                                disabled={uploadingDoc || !uploadFile}
                                className="px-3 py-1 bg-primary text-white rounded text-xs font-medium disabled:opacity-50"
                              >
                                {uploadingDoc ? "Uploading..." : "Submit File"}
                              </button>
                            </div>
                          </form>
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              )}

              {/* Tab 7: Declarations & Undertaking */}
              {activeTab === "declarations" && (
                <DossierDeclarations
                  application={appDetail}
                  onSave={async (patch) => {
                    await patchApplication.runAsync(patch);
                  }}
                  isSaving={patchApplication.busy}
                />
              )}

              {/* Tab 8: Evaluation & Scoring */}
              {activeTab === "evaluation" && (
                <div className="space-y-6">
                  {/* Assessments Section */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-ink">Written Tests & Observations</h3>
                        <p className="text-xs text-ink-soft">
                          Schedule entrance papers and record marks.
                        </p>
                      </div>
                      <ActionButton
                        permission="admission.application.write"
                        onClick={() => setShowAssessmentModal(true)}
                      >
                        + Schedule written test
                      </ActionButton>
                    </div>

                    {evaluationQuery.isLoading ? (
                      <Empty>Loading assessments...</Empty>
                    ) : (evaluationQuery.data?.assessments.length ?? 0) === 0 ? (
                      <Empty>No written assessments scheduled yet.</Empty>
                    ) : (
                      <div className="space-y-2">
                        {evaluationQuery.data?.assessments.map((a) => (
                          <div
                            key={a.id}
                            className="p-3 bg-ground rounded-input border border-rule flex flex-wrap items-center justify-between gap-3 text-sm"
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold capitalize text-ink">
                                  {a.assessment_type.replace(/_/g, " ")}
                                </span>
                                <Pill
                                  status={
                                    a.status === "completed"
                                      ? "present"
                                      : a.status === "absent"
                                        ? "absent"
                                        : "pending"
                                  }
                                >
                                  {a.status.toUpperCase()}
                                </Pill>
                              </div>
                              <p className="text-xs text-ink-soft mt-0.5">
                                Scheduled: {new Date(a.scheduled_at).toLocaleString("en-GB")} | Venue:{" "}
                                {a.venue || "TBD"} {a.seat_no ? `| Seat: ${a.seat_no}` : ""}
                              </p>
                              {a.remarks && (
                                <p className="text-xs text-ink mt-1 italic">Remarks: "{a.remarks}"</p>
                              )}
                            </div>

                            <div className="flex items-center gap-3">
                              {a.status === "completed" ? (
                                <div className="text-right">
                                  <p className="font-bold tabular text-ink text-base">
                                    {a.obtained_marks} / {a.total_marks}
                                  </p>
                                  <p className="text-xs text-success font-medium">{a.percent}%</p>
                                </div>
                              ) : a.status === "absent" ? (
                                <span className="text-danger font-semibold text-xs">MARKED ABSENT</span>
                              ) : (
                                <ActionButton
                                  permission="admission.assessment.enter"
                                  onClick={() => {
                                    setScoringAssessmentId(a.id);
                                    setMarksForm({
                                      obtained_marks: a.obtained_marks || "80",
                                      total_marks: a.total_marks || "100",
                                      is_absent: false,
                                      remarks: a.remarks || "",
                                      reason: "",
                                    });
                                  }}
                                >
                                  Enter marks
                                </ActionButton>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Interviews Section */}
                  <div className="border-t border-rule pt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-ink">Panel Interviews</h3>
                        <p className="text-xs text-ink-soft">
                          Parent and candidate interview feedback.
                        </p>
                      </div>
                      <ActionButton
                        permission="admission.application.write"
                        onClick={() => setShowInterviewModal(true)}
                      >
                        + Schedule interview
                      </ActionButton>
                    </div>

                    {evaluationQuery.isLoading ? (
                      <Empty>Loading interviews...</Empty>
                    ) : (evaluationQuery.data?.interviews.length ?? 0) === 0 ? (
                      <Empty>No interviews scheduled yet.</Empty>
                    ) : (
                      <div className="space-y-2">
                        {evaluationQuery.data?.interviews.map((iv) => (
                          <div
                            key={iv.id}
                            className="p-3 bg-ground rounded-input border border-rule flex flex-wrap items-center justify-between gap-3 text-sm"
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-ink">Interview #{iv.id}</span>
                                <Pill
                                  status={iv.status === "completed" ? "present" : "pending"}
                                >
                                  {iv.status.toUpperCase()}
                                </Pill>
                              </div>
                              <p className="text-xs text-ink-soft mt-0.5">
                                Scheduled: {new Date(iv.scheduled_at).toLocaleString("en-GB")} | Venue:{" "}
                                {iv.venue || "TBD"}
                              </p>
                              {iv.recommendation && (
                                <p className="text-xs text-ink mt-1 font-medium">
                                  Recommendation:{" "}
                                  <span className="uppercase text-primary font-bold">
                                    {iv.recommendation.replace(/_/g, " ")}
                                  </span>{" "}
                                  (Child: {iv.child_rating}/5, Parents: {iv.parent_rating}/5)
                                </p>
                              )}
                            </div>

                            <div>
                              {iv.status !== "completed" && (
                                <ActionButton
                                  permission="admission.interview.enter"
                                  onClick={() => {
                                    setScoringInterviewId(iv.id);
                                    setFeedbackForm({
                                      child_rating: iv.child_rating || 4,
                                      parent_rating: iv.parent_rating || 4,
                                      recommendation: iv.recommendation || "admit",
                                      notes: "",
                                      reason: "",
                                    });
                                  }}
                                >
                                  Enter panel feedback
                                </ActionButton>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 5: Decision & Offers */}
              {activeTab === "decision" && (
                <div className="space-y-6">
                  {/* Decision action bar */}
                  <div className="flex items-center justify-between bg-ground p-4 rounded-input border border-rule">
                    <div>
                      <h3 className="font-bold text-ink">Admission Committee Decision</h3>
                      <p className="text-xs text-ink-soft">
                        Admit, waitlist, or reject applicant with required reason.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <ActionButton
                        permission="admission.decision.make"
                        variant="primary"
                        onClick={() => {
                          setDecisionForm({
                            decision: "admitted",
                            reason: "Met entrance marks and eligibility criteria.",
                            seat_category: appDetail.effective_category || "general",
                            conditions: "",
                            over_allocation_approved: false,
                          });
                          setShowDecisionModal(true);
                        }}
                      >
                        Make decision
                      </ActionButton>
                    </div>
                  </div>

                  {/* Decision history audit log */}
                  <Card title="Decision History Trail">
                    {decisionsQuery.isLoading ? (
                      <Empty>Loading decision audit log...</Empty>
                    ) : (decisionsQuery.data?.length ?? 0) === 0 ? (
                      <Empty>No decision recorded yet.</Empty>
                    ) : (
                      <div className="space-y-2">
                        {decisionsQuery.data?.map((d, i) => (
                          <div
                            key={i}
                            className="p-3 bg-ground rounded-input border border-rule space-y-1 text-sm"
                          >
                            <div className="flex items-center justify-between">
                              <span
                                className={`font-bold uppercase tracking-wide text-xs ${
                                  d.decision === "admitted"
                                    ? "text-success"
                                    : d.decision === "rejected"
                                      ? "text-danger"
                                      : "text-warning"
                                }`}
                              >
                                Decision: {d.decision}
                              </span>
                              <span className="text-xs text-ink-faint tabular">
                                {new Date(d.decided_at).toLocaleString("en-GB")}
                              </span>
                            </div>
                            <p className="text-sm text-ink">{d.reason}</p>
                            <p className="text-xs text-ink-soft">
                              Seat Quota: {d.seat_category || "General"}
                              {d.conditions ? ` | Conditions: ${d.conditions}` : ""}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>

                  {/* Offer Letters Section */}
                  <div className="border-t border-rule pt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-ink">Offer Letter Management</h3>
                        <p className="text-xs text-ink-soft">
                          Issue provisional admission offer letter with expiry date. Lapsed offers release seats.
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <ActionButton
                          permission="admission.decision.make"
                          variant="primary"
                          onClick={() => setShowOfferModal(true)}
                        >
                          Issue offer letter
                        </ActionButton>
                        <ActionButton
                          permission="admission.application.write"
                          onClick={() => setShowResponseModal(true)}
                        >
                          Record family response
                        </ActionButton>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 6: Fees & Student Conversion */}
              {activeTab === "conversion" && (
                <div className="space-y-6">
                  {/* Fee Collection Section */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-ink">Admission & Application Fees</h3>
                        <p className="text-xs text-ink-soft">
                          Offline receipts. Payments can be voided with reason, never edited.
                        </p>
                      </div>
                      <ActionButton
                        permission="fees.payment.collect"
                        onClick={() => {
                          setPaymentForm({
                            purpose: "application_fee",
                            amount: activeCycle?.application_fee ? String(activeCycle.application_fee) : "500.00",
                            method: "cash",
                            reference: "REC-" + Date.now().toString().slice(-6),
                          });
                          setShowPaymentModal(true);
                        }}
                      >
                        + Collect fee payment
                      </ActionButton>
                    </div>

                    {paymentsQuery.isLoading ? (
                      <Empty>Loading payments...</Empty>
                    ) : (paymentsQuery.data?.length ?? 0) === 0 ? (
                      <Empty>No fee payments recorded yet.</Empty>
                    ) : (
                      <div className="space-y-2">
                        {paymentsQuery.data?.map((p) => (
                          <div
                            key={p.id}
                            className="p-3 bg-ground rounded-input border border-rule flex flex-wrap items-center justify-between gap-3 text-sm"
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-ink">
                                  {p.receipt_no}
                                </span>
                                <Pill status={p.status === "paid" ? "present" : "absent"}>
                                  {p.status.toUpperCase()}
                                </Pill>
                                <span className="text-xs text-ink-soft capitalize">
                                  ({p.purpose.replace(/_/g, " ")})
                                </span>
                              </div>
                              <p className="text-xs text-ink-soft mt-0.5">
                                Paid via: <span className="capitalize">{p.method}</span> | Ref:{" "}
                                {p.reference || "None"} | Date: {new Date(p.paid_at).toLocaleString("en-GB")}
                              </p>
                              {p.void_reason && (
                                <p className="text-xs text-danger mt-1 italic">
                                  Void reason: "{p.void_reason}"
                                </p>
                              )}
                            </div>

                            <div className="flex items-center gap-3">
                              <span className="font-bold text-base tabular text-ink">
                                {money(p.amount)}
                              </span>

                              <button
                                type="button"
                                className="text-xs px-2.5 py-1 rounded border border-rule hover:bg-surface font-medium text-ink transition-colors flex items-center gap-1"
                                onClick={() => setPrintingReceipt(p)}
                              >
                                Print receipt
                              </button>

                              {p.status === "paid" && (
                                <ActionButton
                                  permission="fees.payment.void"
                                  variant="danger"
                                  className="text-xs px-2.5 py-1"
                                  onClick={() => setVoidingPaymentId(p.id)}
                                >
                                  Void receipt
                                </ActionButton>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Immediate Student Enrollment Section (Automatic Trigger on Payment) */}
                  <div className="border-t border-rule pt-4 space-y-4">
                    {appDetail.status === "enrolled" || lastEnrollmentResult ? (
                      <div className="p-4 bg-emerald-50 border-2 border-emerald-500/30 rounded-lg space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-emerald-700 font-bold text-base flex items-center gap-1.5">
                              <span>✓</span> Student Officially Enrolled!
                            </span>
                            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 font-mono font-bold text-xs rounded">
                              ADM: {lastEnrollmentResult?.student?.admission_no || (appDetail as any).admission_no || (appDetail as any).student_id || "ENROLLED"}
                            </span>
                          </div>
                          <span className="text-xs font-semibold text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded">
                            Active in School Roster
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-xs bg-white p-3 rounded border border-emerald-200">
                          <div>
                            <span className="text-gray-500 block text-[10px] uppercase">Enrolled Class & Section:</span>
                            <span className="font-bold text-gray-900">
                              {lastEnrollmentResult?.student?.class_label || (appDetail as any).class_label || `Class ${appDetail.class_applying_for}`}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500 block text-[10px] uppercase">Assigned Roll Number:</span>
                            <span className="font-mono font-bold text-gray-900">
                              {lastEnrollmentResult?.student?.roll_no ? `Roll #${lastEnrollmentResult.student.roll_no}` : "Assigned"}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500 block text-[10px] uppercase">Student Login ID:</span>
                            <span className="font-mono font-bold text-blue-900">
                              {lastEnrollmentResult?.student?.admission_no || (appDetail as any).admission_no || "Admission No"}
                            </span>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          <button
                            type="button"
                            className="px-3 py-1.5 rounded text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition flex items-center gap-1.5 shadow-sm"
                            onClick={() => {
                              const p = lastEnrollmentResult?.receipt || paymentsQuery.data?.[0];
                              if (p) setPrintingReceipt(p);
                            }}
                          >
                            Print Fee Receipt Voucher
                          </button>
                          <button
                            type="button"
                            className="px-3 py-1.5 rounded text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition flex items-center gap-1.5 shadow-sm"
                            onClick={() => setPrintingDossier(true)}
                          >
                            Print Full Admission Dossier (PDF)
                          </button>
                          <a
                            href={`#/students?q=${encodeURIComponent(lastEnrollmentResult?.student?.admission_no || appDetail.name)}`}
                            className="px-3 py-1.5 rounded text-xs font-semibold border border-emerald-400 bg-white text-emerald-800 hover:bg-emerald-50 transition ml-auto"
                          >
                            View in Students Roster →
                          </a>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-ground p-4 rounded-input border border-rule space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-ink text-sm">
                            Automated Student Enrolment
                          </span>
                          <span className="text-xs font-medium text-ink-soft">
                            Configured Application Fee: ₹{activeCycle?.application_fee || "0.00"}
                          </span>
                        </div>
                        <p className="text-xs text-ink-soft">
                          Successful application fee payment is the single, automatic trigger for student enrollment. Recording payment will atomically generate the permanent admission number, allocate the class section with balanced headcount, create student and parent logins, and activate student enrolment.
                        </p>
                        <div className="flex justify-end pt-1">
                          <ActionButton
                            permission="fees.payment.collect"
                            variant="primary"
                            onClick={() => {
                              setPaymentForm({
                                purpose: "application_fee",
                                amount: activeCycle?.application_fee ? String(activeCycle.application_fee) : "500.00",
                                method: "cash",
                                reference: "REC-" + Date.now().toString().slice(-6),
                              });
                              setShowPaymentModal(true);
                            }}
                          >
                            Collect Application Fee & Auto-Enroll →
                          </ActionButton>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </Modal>
      )}

      {/* Modal: Status Move */}
      {showStatusDialog && (
        <Modal
          title="Move Application Status"
          onClose={() => setShowStatusDialog(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const reason = (e.currentTarget.elements.namedItem("reason") as HTMLTextAreaElement).value;
              moveStatus.run({ status: targetStatus, reason });
            }}
            className="space-y-4"
          >
            <FormField label="Target Status">
              <select
                className={inputClass}
                value={targetStatus}
                onChange={(e) => setTargetStatus(e.target.value)}
              >
                <option value="draft">Draft</option>
                <option value="submitted">Submitted</option>
                <option value="under_document_verification">Under Document Verification</option>
                <option value="documents_verified">Documents Verified</option>
                <option value="documents_rejected">Documents Rejected</option>
                <option value="assessment_scheduled">Assessment Scheduled</option>
                <option value="assessment_completed">Assessment Completed</option>
                <option value="interview_scheduled">Interview Scheduled</option>
                <option value="interview_completed">Interview Completed</option>
                <option value="decision_pending">Decision Pending</option>
                <option value="admitted">Admitted</option>
                <option value="waitlisted">Waitlisted</option>
                <option value="rejected">Rejected</option>
                <option value="withdrawn_by_parent">Withdrawn by Parent</option>
              </select>
            </FormField>

            <FormField label="Audit Reason (Required for backward moves & reversals)">
              <textarea
                name="reason"
                className={inputClass}
                rows={2}
                placeholder="Reason for changing status..."
              />
            </FormField>

            <FormError error={moveStatus.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowStatusDialog(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={moveStatus.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {moveStatus.busy ? "Updating..." : "Update Status"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Make Decision */}
      {showDecisionModal && (
        <Modal
          title="Make Admission Decision"
          onClose={() => setShowDecisionModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              decideApplication.run(decisionForm);
            }}
            className="space-y-4"
          >
            <FormField label="Decision Outcome">
              <select
                className={inputClass}
                value={decisionForm.decision}
                onChange={(e) =>
                  setDecisionForm({
                    ...decisionForm,
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
              error={decideApplication.fields["reason"]}
            >
              <textarea
                required
                className={inputClass}
                rows={3}
                placeholder="Reason is required by ERP §5.1.9(13) for auditing..."
                value={decisionForm.reason}
                onChange={(e) =>
                  setDecisionForm({
                    ...decisionForm,
                    reason: e.target.value,
                  })
                }
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Seat Quota Category">
                <select
                  className={inputClass}
                  value={decisionForm.seat_category}
                  onChange={(e) =>
                    setDecisionForm({
                      ...decisionForm,
                      seat_category: e.target.value,
                    })
                  }
                >
                  <option value="general">General</option>
                  <option value="sibling">Sibling Quota</option>
                  <option value="staff_ward">Staff Ward Quota</option>
                  <option value="rte">RTE</option>
                  <option value="management">Management Quota</option>
                </select>
              </FormField>

              <FormField label="Conditions (if provisional)">
                <input
                  className={inputClass}
                  placeholder="e.g. Subject to final board marksheet"
                  value={decisionForm.conditions}
                  onChange={(e) =>
                    setDecisionForm({
                      ...decisionForm,
                      conditions: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={decisionForm.over_allocation_approved}
                  onChange={(e) =>
                    setDecisionForm({
                      ...decisionForm,
                      over_allocation_approved: e.target.checked,
                    })
                  }
                />
                Over-allocation Approved (Requires admission.decision.override)
              </label>
            </div>

            <FormError error={decideApplication.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowDecisionModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={decideApplication.busy || !decisionForm.reason.trim()}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {decideApplication.busy ? "Recording..." : "Record Decision"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Issue Offer */}
      {showOfferModal && (
        <Modal
          title="Issue Admission Offer Letter"
          onClose={() => setShowOfferModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              issueOffer.run(offerForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Offer Expiry Date"
                error={issueOffer.fields["expires_on"]}
              >
                <input
                  type="date"
                  required
                  className={inputClass}
                  value={offerForm.expires_on}
                  onChange={(e) =>
                    setOfferForm({ ...offerForm, expires_on: e.target.value })
                  }
                />
              </FormField>

              <FormField
                label="Fee Amount Due (₹)"
                error={issueOffer.fields["offer_amount"]}
              >
                <input
                  type="number"
                  step="0.01"
                  required
                  className={inputClass}
                  value={offerForm.offer_amount}
                  onChange={(e) =>
                    setOfferForm({ ...offerForm, offer_amount: e.target.value })
                  }
                />
              </FormField>
            </div>

            <p className="text-xs text-ink-soft">
              Seats are reserved until the expiry date. If unpaid or lapsed, the seat is released automatically for the waitlist.
            </p>

            <FormError error={issueOffer.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowOfferModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={issueOffer.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {issueOffer.busy ? "Generating..." : "Generate Offer Letter"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Record Offer Response */}
      {showResponseModal && (
        <Modal
          title="Record Offer Letter Response"
          onClose={() => setShowResponseModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              respondOffer.run(responseForm);
            }}
            className="space-y-4"
          >
            <FormField label="Response Outcome">
              <select
                className={inputClass}
                value={responseForm.accepted ? "yes" : "no"}
                onChange={(e) =>
                  setResponseForm({
                    ...responseForm,
                    accepted: e.target.value === "yes",
                  })
                }
              >
                <option value="yes">Accepted by Family</option>
                <option value="no">Declined by Family (Releases Seat)</option>
              </select>
            </FormField>

            <FormField label="Remarks / Details">
              <textarea
                className={inputClass}
                rows={2}
                value={responseForm.reason}
                onChange={(e) =>
                  setResponseForm({ ...responseForm, reason: e.target.value })
                }
              />
            </FormField>

            <FormError error={respondOffer.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowResponseModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={respondOffer.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {respondOffer.busy ? "Saving..." : "Record Response"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Collect Payment */}
      {showPaymentModal && (
        <Modal
          title="Collect Application Fee & Auto-Enroll Student"
          onClose={() => setShowPaymentModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              collectPayment.run(paymentForm);
            }}
            className="space-y-4"
          >
            <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900 leading-relaxed">
              <strong>Single-Action Enrolment:</strong> Collecting this payment atomically creates the permanent student record, allocates their class section with balanced headcount, issues a sequential receipt, creates user logins, and activates enrolment.
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Purpose">
                <select
                  className={inputClass}
                  value={paymentForm.purpose}
                  onChange={(e) =>
                    setPaymentForm({
                      ...paymentForm,
                      purpose: e.target.value as any,
                    })
                  }
                >
                  <option value="application_fee">Application Form Fee (Auto-Enrolls)</option>
                  <option value="admission_fee">Admission / Tuition Fee</option>
                </select>
              </FormField>

              <FormField
                label="Amount (₹)"
                error={collectPayment.fields["amount"]}
              >
                <input
                  type="number"
                  step="0.01"
                  required
                  className={inputClass}
                  value={paymentForm.amount}
                  onChange={(e) =>
                    setPaymentForm({ ...paymentForm, amount: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Payment Method">
                <select
                  className={inputClass}
                  value={paymentForm.method}
                  onChange={(e) =>
                    setPaymentForm({ ...paymentForm, method: e.target.value })
                  }
                >
                  <option value="cash">Cash</option>
                  <option value="upi">UPI / QR Code</option>
                  <option value="cheque">Cheque</option>
                  <option value="card">Card / POS</option>
                  <option value="net_banking">NEFT / Net Banking</option>
                </select>
              </FormField>

              <FormField label="Receipt / Bank Reference">
                <input
                  className={inputClass}
                  placeholder="e.g. UPI-923849102"
                  value={paymentForm.reference}
                  onChange={(e) =>
                    setPaymentForm({
                      ...paymentForm,
                      reference: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <FormError error={collectPayment.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowPaymentModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={collectPayment.busy}
                className="rounded-input bg-emerald-600 text-white text-sm font-semibold px-4 py-2 hover:bg-emerald-700 disabled:opacity-50 transition shadow-sm"
              >
                {collectPayment.busy ? "Enrolling student..." : "Collect Fee & Enroll Student ✓"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Document Verification Verdict */}
      {verifyingDocId !== null && (
        <Modal
          title="Document Scrutiny Verdict"
          onClose={() => setVerifyingDocId(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              verifyDocument.run({
                id: verifyingDocId,
                ...verifyVerdict,
              });
            }}
            className="space-y-4"
          >
            <FormField label="Scrutiny Verdict">
              <select
                className={inputClass}
                value={verifyVerdict.approved ? "yes" : "no"}
                onChange={(e) =>
                  setVerifyVerdict({
                    ...verifyVerdict,
                    approved: e.target.value === "yes",
                  })
                }
              >
                <option value="yes">Approve & Accept Document</option>
                <option value="no">Reject Document (Request Resubmission)</option>
              </select>
            </FormField>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={verifyVerdict.original_seen}
                  onChange={(e) =>
                    setVerifyVerdict({
                      ...verifyVerdict,
                      original_seen: e.target.checked,
                    })
                  }
                />
                Physical Original Seen & Verified at Counter
              </label>
            </div>

            <FormField label="Verification Remarks / Reason for Rejection">
              <textarea
                className={inputClass}
                rows={2}
                placeholder="Notes for parent or audit record..."
                value={verifyVerdict.reason}
                onChange={(e) =>
                  setVerifyVerdict({
                    ...verifyVerdict,
                    reason: e.target.value,
                  })
                }
              />
            </FormField>

            <FormError error={verifyDocument.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setVerifyingDocId(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={verifyDocument.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {verifyDocument.busy ? "Saving..." : "Record Scrutiny Verdict"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Confirm Dialog: Void Payment */}
      {voidingPaymentId !== null && (
        <ConfirmDialog
          title="Void Fee Payment Receipt"
          intent="Voiding an admission payment permanently cancels the receipt in the ledger. Audited reason is mandatory."
          confirmLabel="Void Receipt"
          busy={voidPayment.busy}
          error={voidPayment.error}
          onConfirm={(reason) =>
            voidPayment.run({ id: voidingPaymentId, reason })
          }
          onClose={() => setVoidingPaymentId(null)}
        />
      )}

      {/* Modal: Schedule Assessment */}
      {showAssessmentModal && (
        <Modal
          title="Schedule Written Assessment / Observation"
          onClose={() => setShowAssessmentModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              scheduleAssessment.run(assessmentForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Assessment Type">
                <select
                  className={inputClass}
                  value={assessmentForm.assessment_type}
                  onChange={(e) =>
                    setAssessmentForm({
                      ...assessmentForm,
                      assessment_type: e.target.value,
                    })
                  }
                >
                  <option value="written_test">Written Test</option>
                  <option value="readiness_observation">Readiness Observation</option>
                  <option value="previous_result_review">Previous Board Result Review</option>
                </select>
              </FormField>

              <FormField label="Date & Time">
                <input
                  type="datetime-local"
                  required
                  className={inputClass}
                  value={assessmentForm.scheduled_at}
                  onChange={(e) =>
                    setAssessmentForm({
                      ...assessmentForm,
                      scheduled_at: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Venue / Room">
                <input
                  className={inputClass}
                  value={assessmentForm.venue}
                  onChange={(e) =>
                    setAssessmentForm({
                      ...assessmentForm,
                      venue: e.target.value,
                    })
                  }
                />
              </FormField>

              <FormField label="Seat Number">
                <input
                  className={inputClass}
                  value={assessmentForm.seat_no}
                  onChange={(e) =>
                    setAssessmentForm({
                      ...assessmentForm,
                      seat_no: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <FormError error={scheduleAssessment.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowAssessmentModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={scheduleAssessment.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {scheduleAssessment.busy ? "Scheduling..." : "Schedule Assessment"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Enter Assessment Marks */}
      {scoringAssessmentId !== null && (
        <Modal
          title="Enter Assessment Marks"
          onClose={() => setScoringAssessmentId(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              recordMarks.run({ id: scoringAssessmentId, data: marksForm });
            }}
            className="space-y-4"
          >
            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={marksForm.is_absent}
                  onChange={(e) =>
                    setMarksForm({ ...marksForm, is_absent: e.target.checked })
                  }
                />
                Applicant was Absent (Mark Absent)
              </label>
            </div>

            {!marksForm.is_absent && (
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Obtained Marks">
                  <input
                    type="number"
                    step="0.5"
                    required
                    className={inputClass}
                    value={marksForm.obtained_marks}
                    onChange={(e) =>
                      setMarksForm({
                        ...marksForm,
                        obtained_marks: e.target.value,
                      })
                    }
                  />
                </FormField>

                <FormField label="Total Marks">
                  <input
                    type="number"
                    step="0.5"
                    required
                    className={inputClass}
                    value={marksForm.total_marks}
                    onChange={(e) =>
                      setMarksForm({
                        ...marksForm,
                        total_marks: e.target.value,
                      })
                    }
                  />
                </FormField>
              </div>
            )}

            <FormField label="Remarks">
              <textarea
                className={inputClass}
                rows={2}
                placeholder="Assessor remarks..."
                value={marksForm.remarks}
                onChange={(e) =>
                  setMarksForm({ ...marksForm, remarks: e.target.value })
                }
              />
            </FormField>

            <FormError error={recordMarks.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setScoringAssessmentId(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={recordMarks.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {recordMarks.busy ? "Saving..." : "Save Marks"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Schedule Interview */}
      {showInterviewModal && (
        <Modal
          title="Schedule Panel Interview"
          onClose={() => setShowInterviewModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              scheduleInterview.run(interviewForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Scheduled Date & Time">
                <input
                  type="datetime-local"
                  required
                  className={inputClass}
                  value={interviewForm.scheduled_at}
                  onChange={(e) =>
                    setInterviewForm({
                      ...interviewForm,
                      scheduled_at: e.target.value,
                    })
                  }
                />
              </FormField>

              <FormField label="Venue / Room">
                <input
                  className={inputClass}
                  value={interviewForm.venue}
                  onChange={(e) =>
                    setInterviewForm({
                      ...interviewForm,
                      venue: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <FormError error={scheduleInterview.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowInterviewModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={scheduleInterview.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {scheduleInterview.busy ? "Scheduling..." : "Schedule Interview"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Enter Interview Feedback */}
      {scoringInterviewId !== null && (
        <Modal
          title="Enter Panel Feedback"
          onClose={() => setScoringInterviewId(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              recordFeedback.run({ id: scoringInterviewId, data: feedbackForm });
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Candidate Rating (1 to 5)">
                <input
                  type="number"
                  min="1"
                  max="5"
                  required
                  className={inputClass}
                  value={feedbackForm.child_rating}
                  onChange={(e) =>
                    setFeedbackForm({
                      ...feedbackForm,
                      child_rating: Number(e.target.value),
                    })
                  }
                />
              </FormField>

              <FormField label="Parent Rating (1 to 5)">
                <input
                  type="number"
                  min="1"
                  max="5"
                  required
                  className={inputClass}
                  value={feedbackForm.parent_rating}
                  onChange={(e) =>
                    setFeedbackForm({
                      ...feedbackForm,
                      parent_rating: Number(e.target.value),
                    })
                  }
                />
              </FormField>
            </div>

            <FormField label="Panel Recommendation">
              <select
                className={inputClass}
                value={feedbackForm.recommendation}
                onChange={(e) =>
                  setFeedbackForm({
                    ...feedbackForm,
                    recommendation: e.target.value,
                  })
                }
              >
                <option value="strong_admit">Strongly Recommend Admit</option>
                <option value="admit">Recommend Admit</option>
                <option value="waitlist">Consider for Waitlist</option>
                <option value="reject">Recommend Rejection</option>
              </select>
            </FormField>

            <FormField label="Panel Notes">
              <textarea
                className={inputClass}
                rows={3}
                placeholder="Feedback on child interaction and parent interview..."
                value={feedbackForm.notes}
                onChange={(e) =>
                  setFeedbackForm({ ...feedbackForm, notes: e.target.value })
                }
              />
            </FormField>

            <FormError error={recordFeedback.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setScoringInterviewId(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={recordFeedback.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {recordFeedback.busy ? "Saving..." : "Submit Feedback"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Edit Medical Info */}
      {showMedicalModal && (
        <Modal
          title="Edit Medical & Special Needs Information"
          onClose={() => setShowMedicalModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              saveMedical.run(medicalForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Blood Group">
                <input
                  className={inputClass}
                  placeholder="e.g. O+, B+, AB-"
                  value={medicalForm.blood_group || ""}
                  onChange={(e) =>
                    setMedicalForm({
                      ...medicalForm,
                      blood_group: e.target.value,
                    })
                  }
                />
              </FormField>

              <FormField label="Emergency Doctor Phone">
                <input
                  className={inputClass}
                  placeholder="Doctor's phone"
                  value={medicalForm.emergency_doctor_phone || ""}
                  onChange={(e) =>
                    setMedicalForm({
                      ...medicalForm,
                      emergency_doctor_phone: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <FormField label="Known Allergies (Food, Meds, Environmental)">
              <input
                className={inputClass}
                placeholder="e.g. Peanut allergy, penicillin"
                value={medicalForm.known_allergies || ""}
                onChange={(e) =>
                  setMedicalForm({
                    ...medicalForm,
                    known_allergies: e.target.value,
                  })
                }
              />
            </FormField>

            <FormField label="Chronic Conditions & Regular Medications">
              <textarea
                className={inputClass}
                rows={2}
                placeholder="e.g. Asthma inhaler, diabetes"
                value={medicalForm.chronic_conditions || ""}
                onChange={(e) =>
                  setMedicalForm({
                    ...medicalForm,
                    chronic_conditions: e.target.value,
                  })
                }
              />
            </FormField>

            <FormField label="Learning Needs & Accommodations">
              <textarea
                className={inputClass}
                rows={2}
                placeholder="e.g. Dyslexia accommodation, speech therapy"
                value={medicalForm.learning_needs || ""}
                onChange={(e) =>
                  setMedicalForm({
                    ...medicalForm,
                    learning_needs: e.target.value,
                  })
                }
              />
            </FormField>

            <div className="pt-1">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={medicalForm.consent_for_emergency_treatment ?? false}
                  onChange={(e) =>
                    setMedicalForm({
                      ...medicalForm,
                      consent_for_emergency_treatment: e.target.checked,
                    })
                  }
                />
                Parent Consent for Immediate Emergency Medical Treatment
              </label>
            </div>

            <FormError error={saveMedical.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowMedicalModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saveMedical.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {saveMedical.busy ? "Saving..." : "Save Medical Record"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Link Sibling Student */}
      {showSiblingModal && (
        <Modal
          title="Link Real Enrolled Sibling"
          onClose={() => setShowSiblingModal(false)}
        >
          <div className="space-y-4">
            <FormField label="Search Enrolled Student (by Name or Admission No)">
              <input
                className={inputClass}
                placeholder="Type at least 2 characters..."
                value={siblingQueryTerm}
                onChange={(e) => setSiblingQueryTerm(e.target.value)}
              />
            </FormField>

            {siblingSearchResults.isLoading ? (
              <Empty>Searching students...</Empty>
            ) : siblingSearchResults.data && siblingSearchResults.data.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {siblingSearchResults.data.map((st: any) => (
                  <div
                    key={st.student_id}
                    className="p-3 bg-ground rounded-input border border-rule flex items-center justify-between"
                  >
                    <div>
                      <p className="font-bold text-ink">{st.full_name}</p>
                      <p className="text-xs text-ink-soft">
                        Adm No: {st.admission_no} | Class: {st.class_name}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="px-3 py-1 bg-primary text-white text-xs rounded font-medium hover:bg-primary-dark"
                      onClick={() => {
                        const newSiblings = [
                          ...(appDetail?.siblings ?? []),
                          {
                            id: 0,
                            student_id: st.student_id,
                            name: st.full_name,
                            age: null,
                            school_name: "Sunrise Public School",
                          },
                        ];
                        saveSiblings.run(newSiblings);
                      }}
                    >
                      Link Sibling
                    </button>
                  </div>
                ))}
              </div>
            ) : siblingQueryTerm.length >= 2 ? (
              <Empty>No matching enrolled students found.</Empty>
            ) : null}

            <div className="flex justify-end pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowSiblingModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Printable Fee Receipt Modal */}
      {printingReceipt && appDetail && (
        <PrintableFeeReceipt
          payment={printingReceipt}
          application={appDetail}
          studentInfo={lastEnrollmentResult?.student}
          onClose={() => setPrintingReceipt(null)}
        />
      )}

      {/* Printable Full Admission Dossier Modal */}
      {printingDossier && appDetail && (
        <PrintableAdmissionDossier
          application={appDetail}
          medical={medicalQuery.data}
          checklist={documentsQuery.data?.items}
          payments={paymentsQuery.data}
          studentInfo={lastEnrollmentResult?.student}
          onClose={() => setPrintingDossier(false)}
        />
      )}
    </div>
  );
}
