import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Can } from "../../components/Can";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../../components/ui";
import {
  PrintablePrincipalMeetingSlip,
  PrincipalMeetingData,
} from "../../components/reception/PrintablePrincipalMeetingSlip";
import {
  PrintableTeacherMeetingSlip,
  TeacherMeetingData,
} from "../../components/reception/PrintableTeacherMeetingSlip";

export function MeetingsPage() {
  const queryClient = useQueryClient();
  const { me, can } = useAuth();

  const isTeacherOnly =
    !can("admin.settings.read") &&
    !can("reception.meetings.write") &&
    can("reception.meetings.respond_teacher");

  const [activeTab, setActiveTab] = useState<"principal" | "teacher">(
    isTeacherOnly ? "teacher" : "principal"
  );

  // Principal state
  const [principalDate, setPrincipalDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [principalStatus, setPrincipalStatus] = useState<string>("");
  const [showNewPrincipalModal, setShowNewPrincipalModal] = useState(false);
  const [activePrincipalSlip, setActivePrincipalSlip] = useState<PrincipalMeetingData | null>(null);
  const [respondPrincipalTarget, setRespondPrincipalTarget] = useState<PrincipalMeetingData | null>(null);

  const [principalForm, setPrincipalForm] = useState({
    visitor_name: "",
    visitor_phone: "",
    visitor_organization: "",
    student_name: "",
    student_admission_no: "",
    reason: "Discussion regarding academic progress and fee concession",
    meeting_date: new Date().toISOString().slice(0, 10),
    meeting_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
  });

  const [principalResponseForm, setPrincipalResponseForm] = useState({
    status: "accepted",
    wait_duration_minutes: 15,
    response_notes: "",
  });

  // Teacher state
  const [teacherDate, setTeacherDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [teacherStatus, setTeacherStatus] = useState<string>("");
  const [showNewTeacherModal, setShowNewTeacherModal] = useState(false);
  const [activeTeacherSlip, setActiveTeacherSlip] = useState<TeacherMeetingData | null>(null);
  const [respondTeacherTarget, setRespondTeacherTarget] = useState<TeacherMeetingData | null>(null);

  const [teacherForm, setTeacherForm] = useState({
    teacher_id: 0,
    visitor_name: "",
    visitor_phone: "",
    visitor_relation: "Parent / Mother",
    student_name: "",
    student_admission_no: "",
    reason: "Quarterly subject marks and class performance review",
    meeting_date: new Date().toISOString().slice(0, 10),
    meeting_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
  });

  const [teacherResponseForm, setTeacherResponseForm] = useState({
    status: "accepted",
    response_notes: "",
  });

  // Queries
  const principalMeetingsQuery = useQuery({
    queryKey: ["principal-meetings", principalDate, principalStatus],
    queryFn: () => {
      const params = new URLSearchParams();
      if (principalDate) params.append("meeting_date", principalDate);
      if (principalStatus) params.append("status", principalStatus);
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/reception/meetings/principal${q}` as any) as Promise<PrincipalMeetingData[]>;
    },
  });

  const teacherMeetingsQuery = useQuery({
    queryKey: ["teacher-meetings", teacherDate, teacherStatus],
    queryFn: () => {
      const params = new URLSearchParams();
      if (teacherDate) params.append("meeting_date", teacherDate);
      if (teacherStatus) params.append("status", teacherStatus);
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/reception/meetings/teacher${q}` as any) as Promise<TeacherMeetingData[]>;
    },
  });

  const teachersListQuery = useQuery({
    queryKey: ["teachers-for-meetings"],
    queryFn: () => {
      return api.get("/admin/reception/teachers" as any) as Promise<
        { id: number; staff_id: string; name: string; department: string }[]
      >;
    },
  });

  // Mutations
  const createPrincipalMeetingMutation = useMutation({
    mutationFn: (data: typeof principalForm) => {
      return api.post("/admin/reception/meetings/principal" as any, data) as Promise<PrincipalMeetingData>;
    },
    onSuccess: (newSlip: PrincipalMeetingData) => {
      queryClient.invalidateQueries({ queryKey: ["principal-meetings"] });
      setShowNewPrincipalModal(false);
      setActivePrincipalSlip(newSlip);
    },
  });

  const respondPrincipalMutation = useMutation({
    mutationFn: ({ meetingId, data }: { meetingId: number; data: typeof principalResponseForm }) => {
      return api.post(`/admin/reception/meetings/principal/${meetingId}/respond` as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["principal-meetings"] });
      setRespondPrincipalTarget(null);
    },
  });

  const createTeacherMeetingMutation = useMutation({
    mutationFn: (data: typeof teacherForm) => {
      return api.post("/admin/reception/meetings/teacher" as any, data) as Promise<TeacherMeetingData>;
    },
    onSuccess: (newSlip: TeacherMeetingData) => {
      queryClient.invalidateQueries({ queryKey: ["teacher-meetings"] });
      setShowNewTeacherModal(false);
      setActiveTeacherSlip(newSlip);
    },
  });

  const respondTeacherMutation = useMutation({
    mutationFn: ({ meetingId, data }: { meetingId: number; data: typeof teacherResponseForm }) => {
      return api.post(`/admin/reception/meetings/teacher/${meetingId}/respond` as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-meetings"] });
      setRespondTeacherTarget(null);
    },
  });

  const principalMeetings = principalMeetingsQuery.data || [];
  const teacherMeetings = teacherMeetingsQuery.data || [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">
            {isTeacherOnly ? "My Visitor Meetings" : "Visitor Meeting Slips"}
          </h1>
          <p className="text-sm text-ink-faint">
            {isTeacherOnly
              ? "View incoming parent and visitor meeting requests addressed to you and record your response."
              : "Manage executive visitor appointments for the Principal and academic parent-teacher interactions."}
          </p>
        </div>

        {/* Tab Buttons */}
        {!isTeacherOnly && (
          <div className="flex items-center gap-2 bg-ground p-1 rounded-pill border border-rule">
            <button
              type="button"
              onClick={() => setActiveTab("principal")}
              className={`px-4 py-1.5 rounded-pill text-xs font-semibold transition ${
                activeTab === "principal" ? "bg-primary text-white shadow-xs" : "text-ink-faint hover:text-ink"
              }`}
            >
              Principal Meeting Slips
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("teacher")}
              className={`px-4 py-1.5 rounded-pill text-xs font-semibold transition ${
                activeTab === "teacher" ? "bg-primary text-white shadow-xs" : "text-ink-faint hover:text-ink"
              }`}
            >
              Teacher Meeting Slips
            </button>
          </div>
        )}
      </div>

      {/* TAB 1: PRINCIPAL MEETINGS */}
      {activeTab === "principal" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="grid grid-cols-3 gap-3 w-full sm:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-ink-faint uppercase">Date:</span>
                <input
                  type="date"
                  value={principalDate}
                  onChange={(e) => setPrincipalDate(e.target.value)}
                  className="text-xs rounded-pill border border-rule px-3 py-1 bg-surface text-ink"
                />
              </div>
              {principalDate && (
                <button
                  type="button"
                  onClick={() => setPrincipalDate("")}
                  className="text-xs text-primary hover:underline font-medium self-center"
                >
                  Clear Date
                </button>
              )}
            </div>

            <Can permission="reception.meetings.write">
              <button
                type="button"
                onClick={() => setShowNewPrincipalModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-pill hover:bg-indigo-700 transition shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                New Principal Meeting Slip
              </button>
            </Can>
          </div>

          <Card>
            <DataTable<PrincipalMeetingData>
              columns={[
                {
                  key: "slip_code",
                  header: "Slip #",
                  render: (row) => (
                    <span className="font-mono text-xs font-bold text-indigo-700">{row.slip_code}</span>
                  ),
                },
                {
                  key: "time",
                  header: "Date & Time",
                  render: (row) => (
                    <div>
                      <span className="font-medium text-ink block">{row.meeting_date}</span>
                      <span className="text-xs text-ink-faint block">{row.meeting_time}</span>
                    </div>
                  ),
                },
                {
                  key: "visitor",
                  header: "Visitor Details",
                  render: (row) => (
                    <div>
                      <span className="font-semibold text-ink block">{row.visitor_name}</span>
                      <span className="text-xs text-ink-faint block">
                        {row.visitor_phone}
                        {row.visitor_organization && ` • ${row.visitor_organization}`}
                      </span>
                      {row.student_name && (
                        <span className="text-xs text-indigo-600 block">
                          Student: {row.student_name}
                          {row.student_admission_no && ` (${row.student_admission_no})`}
                        </span>
                      )}
                    </div>
                  ),
                },
                {
                  key: "reason",
                  header: "Reason / Agenda",
                  render: (row) => <span className="text-xs text-ink line-clamp-2">{row.reason}</span>,
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row) => (
                    <div>
                      <Pill
                        status={
                          row.status === "accepted"
                            ? "active"
                            : row.status === "waiting"
                            ? "in_progress"
                            : row.status === "declined"
                            ? "danger"
                            : "pending"
                        }
                      >
                        {row.status.toUpperCase()}
                      </Pill>
                      {row.status === "waiting" && row.wait_duration_minutes && (
                        <span className="text-xs text-amber-700 font-semibold block mt-0.5">
                          Wait: {row.wait_duration_minutes} min
                        </span>
                      )}
                    </div>
                  ),
                },
                {
                  key: "actions",
                  header: "Actions",
                  align: "right",
                  render: (row) => (
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => setActivePrincipalSlip(row)}
                        className="px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded transition"
                      >
                        Print Slip
                      </button>

                      <Can permission="reception.meetings.respond_principal">
                        {row.status === "pending" && (
                          <button
                            type="button"
                            onClick={() => {
                              setRespondPrincipalTarget(row);
                              setPrincipalResponseForm({
                                status: "accepted",
                                wait_duration_minutes: 15,
                                response_notes: "",
                              });
                            }}
                            className="px-2 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition"
                          >
                            Respond
                          </button>
                        )}
                      </Can>
                    </div>
                  ),
                },
              ]}
              rows={principalMeetingsQuery.data || []}
              empty="No Principal meeting requests found."
              loading={principalMeetingsQuery.isLoading}
              error={principalMeetingsQuery.error}
            />
          </Card>
        </div>
      )}

      {/* TAB 2: TEACHER MEETINGS */}
      {activeTab === "teacher" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="grid grid-cols-3 gap-3 w-full sm:w-auto">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-ink-faint uppercase">Date:</span>
                <input
                  type="date"
                  value={teacherDate}
                  onChange={(e) => setTeacherDate(e.target.value)}
                  className="text-xs rounded-pill border border-rule px-3 py-1 bg-surface text-ink"
                />
              </div>
              {teacherDate && (
                <button
                  type="button"
                  onClick={() => setTeacherDate("")}
                  className="text-xs text-primary hover:underline font-medium self-center"
                >
                  Clear Date
                </button>
              )}
            </div>

            <Can permission="reception.meetings.write">
              <button
                type="button"
                onClick={() => {
                  const firstTeacher = teachersListQuery.data?.[0]?.id || 0;
                  setTeacherForm((prev) => ({ ...prev, teacher_id: firstTeacher }));
                  setShowNewTeacherModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-pill hover:bg-emerald-700 transition shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                </svg>
                New Teacher Meeting Slip
              </button>
            </Can>
          </div>

          <Card>
            <DataTable<TeacherMeetingData>
              columns={[
                {
                  key: "slip_code",
                  header: "Slip No & Time",
                  render: (row) => (
                    <div>
                      <span className="font-mono font-bold text-emerald-900 block">{row.slip_code}</span>
                      <span className="text-xs text-ink-faint">
                        {row.meeting_date} at {row.meeting_time}
                      </span>
                    </div>
                  ),
                },
                {
                  key: "teacher",
                  header: "Faculty Requested",
                  render: (row) => (
                    <div>
                      <span className="font-semibold text-ink block">{row.teacher_name}</span>
                    </div>
                  ),
                },
                {
                  key: "visitor",
                  header: "Visitor Particulars",
                  render: (row) => (
                    <div>
                      <span className="font-semibold text-ink block">{row.visitor_name}</span>
                      <span className="text-xs text-ink-faint">
                        {row.visitor_relation || "Parent"} • {row.visitor_phone}
                      </span>
                      {row.student_name && (
                        <span className="text-[10px] text-ink-faint block">
                          Ward: {row.student_name} ({row.student_admission_no || "—"})
                        </span>
                      )}
                    </div>
                  ),
                },
                {
                  key: "reason",
                  header: "Agenda",
                  render: (row) => (
                    <div className="max-w-xs">
                      <span className="text-xs text-ink font-medium block truncate">{row.reason}</span>
                    </div>
                  ),
                },
                {
                  key: "status",
                  header: "Teacher Status",
                  render: (row) => (
                    <div>
                      <Pill
                        status={
                          row.status === "accepted"
                            ? "active"
                            : row.status === "declined"
                            ? "danger"
                            : "pending"
                        }
                      >
                        {row.status.toUpperCase()}
                      </Pill>
                      {row.response_notes && (
                        <span className="block text-[10px] text-ink-faint italic truncate max-w-xs">
                          {row.response_notes}
                        </span>
                      )}
                    </div>
                  ),
                },
                {
                  key: "actions",
                  header: "Actions",
                  align: "right",
                  render: (row) => (
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => setActiveTeacherSlip(row)}
                        className="px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition"
                      >
                        Print Slip
                      </button>

                      <Can permission="reception.meetings.respond_teacher">
                        {row.status === "pending" && (
                          <button
                            type="button"
                            onClick={() => {
                              setRespondTeacherTarget(row);
                              setTeacherResponseForm({
                                status: "accepted",
                                response_notes: "",
                              });
                            }}
                            className="px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition"
                          >
                            Respond
                          </button>
                        )}
                      </Can>
                    </div>
                  ),
                },
              ]}
              rows={teacherMeetingsQuery.data || []}
              empty="No Teacher meeting requests found."
              loading={teacherMeetingsQuery.isLoading}
              error={teacherMeetingsQuery.error}
            />
          </Card>
        </div>
      )}

      {/* Modal: Create Principal Meeting */}
      {showNewPrincipalModal && (
        <Modal title="Create Principal Visitor Appointment Slip" onClose={() => setShowNewPrincipalModal(false)} wide>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createPrincipalMeetingMutation.mutate(principalForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Visitor Full Name">
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Alok Mathur"
                  value={principalForm.visitor_name}
                  onChange={(e) => setPrincipalForm({ ...principalForm, visitor_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Visitor Phone Number">
                <input
                  type="text"
                  required
                  placeholder="+91 98..."
                  value={principalForm.visitor_phone}
                  onChange={(e) => setPrincipalForm({ ...principalForm, visitor_phone: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Organization / Department">
                <input
                  type="text"
                  placeholder="e.g. CBSE Inspection Panel, Parent"
                  value={principalForm.visitor_organization}
                  onChange={(e) => setPrincipalForm({ ...principalForm, visitor_organization: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Student Name (if Parent)">
                <input
                  type="text"
                  placeholder="Student Full Name"
                  value={principalForm.student_name}
                  onChange={(e) => setPrincipalForm({ ...principalForm, student_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Admission Number">
                <input
                  type="text"
                  placeholder="e.g. 2024000001"
                  value={principalForm.student_admission_no}
                  onChange={(e) => setPrincipalForm({ ...principalForm, student_admission_no: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Meeting Date">
                <input
                  type="date"
                  required
                  value={principalForm.meeting_date}
                  onChange={(e) => setPrincipalForm({ ...principalForm, meeting_date: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Requested Time">
                <input
                  type="text"
                  required
                  placeholder="e.g. 10:30 AM"
                  value={principalForm.meeting_time}
                  onChange={(e) => setPrincipalForm({ ...principalForm, meeting_time: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Reason / Agenda for Meeting">
              <textarea
                rows={2}
                required
                placeholder="Details of matter to discuss with the Principal..."
                value={principalForm.reason}
                onChange={(e) => setPrincipalForm({ ...principalForm, reason: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setShowNewPrincipalModal(false)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createPrincipalMeetingMutation.isPending}
                className="px-5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-pill hover:bg-indigo-700 transition shadow-sm"
              >
                {createPrincipalMeetingMutation.isPending ? "Submitting..." : "Generate Slip & Notify Principal"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Respond to Principal Meeting */}
      {respondPrincipalTarget && (
        <Modal
          title={`Principal Response: Slip ${respondPrincipalTarget.slip_code}`}
          onClose={() => setRespondPrincipalTarget(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              respondPrincipalMutation.mutate({
                meetingId: respondPrincipalTarget.id,
                data: principalResponseForm,
              });
            }}
            className="space-y-4"
          >
            <div className="p-2.5 bg-ground rounded text-xs">
              <span className="font-semibold text-ink">Visitor: </span>
              {respondPrincipalTarget.visitor_name} ({respondPrincipalTarget.visitor_phone})
              <div className="mt-1 text-ink-faint">Reason: {respondPrincipalTarget.reason}</div>
            </div>

            <FormField label="Response Decision">
              <div className="grid grid-cols-3 gap-2">
                {[
                  { val: "accepted", label: "Accept Meeting" },
                  { val: "waiting", label: "Ask to Wait" },
                  { val: "declined", label: "Decline" },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => setPrincipalResponseForm({ ...principalResponseForm, status: opt.val })}
                    className={`p-2 rounded text-xs font-bold uppercase transition ${
                      principalResponseForm.status === opt.val
                        ? opt.val === "accepted"
                          ? "bg-emerald-600 text-white"
                          : opt.val === "waiting"
                          ? "bg-amber-600 text-white"
                          : "bg-red-600 text-white"
                        : "bg-ground text-ink-faint hover:bg-ground-deep"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </FormField>

            {principalResponseForm.status === "waiting" && (
              <FormField label="Wait Duration (Minutes)">
                <input
                  type="number"
                  min={5}
                  max={120}
                  step={5}
                  value={principalResponseForm.wait_duration_minutes}
                  onChange={(e) =>
                    setPrincipalResponseForm({
                      ...principalResponseForm,
                      wait_duration_minutes: parseInt(e.target.value) || 15,
                    })
                  }
                  className={inputClass}
                />
              </FormField>
            )}

            <FormField label="Notes to Receptionist / Visitor">
              <input
                type="text"
                placeholder="e.g. Please send visitor inside after current meeting concludes"
                value={principalResponseForm.response_notes}
                onChange={(e) =>
                  setPrincipalResponseForm({ ...principalResponseForm, response_notes: e.target.value })
                }
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setRespondPrincipalTarget(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={respondPrincipalMutation.isPending}
                className="px-5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-pill hover:bg-indigo-700 transition"
              >
                {respondPrincipalMutation.isPending ? "Saving..." : "Send Decision"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Create Teacher Meeting */}
      {showNewTeacherModal && (
        <Modal title="Create Teacher Meeting Slip" onClose={() => setShowNewTeacherModal(false)} wide>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!teacherForm.teacher_id) {
                alert("Please select a teacher.");
                return;
              }
              createTeacherMeetingMutation.mutate(teacherForm);
            }}
            className="space-y-4"
          >
            <FormField label="Select Teacher">
              <select
                value={teacherForm.teacher_id}
                onChange={(e) => setTeacherForm({ ...teacherForm, teacher_id: parseInt(e.target.value) || 0 })}
                className={inputClass}
                required
              >
                <option value={0}>-- Select Teacher --</option>
                {teachersListQuery.data?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.staff_id} • {t.department})
                  </option>
                ))}
              </select>
            </FormField>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Visitor Full Name">
                <input
                  type="text"
                  required
                  placeholder="Visitor Name"
                  value={teacherForm.visitor_name}
                  onChange={(e) => setTeacherForm({ ...teacherForm, visitor_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Visitor Phone Number">
                <input
                  type="text"
                  required
                  placeholder="+91..."
                  value={teacherForm.visitor_phone}
                  onChange={(e) => setTeacherForm({ ...teacherForm, visitor_phone: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Relationship to Student">
                <input
                  type="text"
                  placeholder="e.g. Mother, Father, Guardian"
                  value={teacherForm.visitor_relation}
                  onChange={(e) => setTeacherForm({ ...teacherForm, visitor_relation: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Student Name">
                <input
                  type="text"
                  placeholder="Student Full Name"
                  value={teacherForm.student_name}
                  onChange={(e) => setTeacherForm({ ...teacherForm, student_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Admission Number">
                <input
                  type="text"
                  placeholder="e.g. 2024000001"
                  value={teacherForm.student_admission_no}
                  onChange={(e) => setTeacherForm({ ...teacherForm, student_admission_no: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Meeting Date">
                <input
                  type="date"
                  required
                  value={teacherForm.meeting_date}
                  onChange={(e) => setTeacherForm({ ...teacherForm, meeting_date: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Requested Time">
                <input
                  type="text"
                  required
                  placeholder="e.g. 02:15 PM"
                  value={teacherForm.meeting_time}
                  onChange={(e) => setTeacherForm({ ...teacherForm, meeting_time: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Reason / Topic of Discussion">
              <textarea
                rows={2}
                required
                placeholder="Topic of discussion with subject/class teacher..."
                value={teacherForm.reason}
                onChange={(e) => setTeacherForm({ ...teacherForm, reason: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setShowNewTeacherModal(false)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createTeacherMeetingMutation.isPending}
                className="px-5 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-pill hover:bg-emerald-700 transition shadow-sm"
              >
                {createTeacherMeetingMutation.isPending ? "Generating..." : "Generate Slip & Notify Teacher"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Respond to Teacher Meeting */}
      {respondTeacherTarget && (
        <Modal
          title={`Teacher Response: Slip ${respondTeacherTarget.slip_code}`}
          onClose={() => setRespondTeacherTarget(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              respondTeacherMutation.mutate({
                meetingId: respondTeacherTarget.id,
                data: teacherResponseForm,
              });
            }}
            className="space-y-4"
          >
            <div className="p-2.5 bg-ground rounded text-xs">
              <span className="font-semibold text-ink">Visitor: </span>
              {respondTeacherTarget.visitor_name} ({respondTeacherTarget.visitor_phone})
              <div className="mt-1 text-ink-faint">Topic: {respondTeacherTarget.reason}</div>
            </div>

            <FormField label="Decision">
              <div className="grid grid-cols-2 gap-2">
                {[
                  { val: "accepted", label: "Accept Meeting" },
                  { val: "declined", label: "Decline" },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => setTeacherResponseForm({ ...teacherResponseForm, status: opt.val })}
                    className={`p-2 rounded text-xs font-bold uppercase transition ${
                      teacherResponseForm.status === opt.val
                        ? opt.val === "accepted"
                          ? "bg-emerald-600 text-white"
                          : "bg-red-600 text-white"
                        : "bg-ground text-ink-faint hover:bg-ground-deep"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </FormField>

            <FormField label="Notes to Visitor / Front Desk">
              <input
                type="text"
                placeholder="e.g. Free after period 5 at 01:45 PM in Staff Room"
                value={teacherResponseForm.response_notes}
                onChange={(e) => setTeacherResponseForm({ ...teacherResponseForm, response_notes: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setRespondTeacherTarget(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={respondTeacherMutation.isPending}
                className="px-5 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-pill hover:bg-emerald-700 transition"
              >
                {respondTeacherMutation.isPending ? "Submitting..." : "Send Response"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Slip Print Modals */}
      {activePrincipalSlip && (
        <PrintablePrincipalMeetingSlip
          meeting={activePrincipalSlip}
          onClose={() => setActivePrincipalSlip(null)}
        />
      )}

      {activeTeacherSlip && (
        <PrintableTeacherMeetingSlip
          meeting={activeTeacherSlip}
          onClose={() => setActiveTeacherSlip(null)}
        />
      )}
    </div>
  );
}
