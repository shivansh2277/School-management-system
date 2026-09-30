import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { Can } from "../../components/Can";
import {
  Card,
  DataTable,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../../components/ui";
import {
  PrintablePrincipalMeetingSlip,
  PrincipalMeetingData,
} from "../../components/reception/PrintablePrincipalMeetingSlip";

export function MeetingsPage() {
  const queryClient = useQueryClient();

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

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">
            Principal Meeting Slips
          </h1>
          <p className="text-sm text-ink-faint">
            Manage executive visitor appointments and meeting requests for the Principal.
          </p>
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

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
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
              className="text-xs text-primary hover:underline font-medium"
            >
              Clear Date
            </button>
          )}

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-ink-faint uppercase">Status:</span>
            <select
              value={principalStatus}
              onChange={(e) => setPrincipalStatus(e.target.value)}
              className="text-xs rounded-pill border border-rule px-3 py-1 bg-surface text-ink"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="accepted">Accepted</option>
              <option value="waiting">Waiting</option>
              <option value="declined">Declined</option>
            </select>
          </div>
        </div>
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

      {/* Slip Print Modal */}
      {activePrincipalSlip && (
        <PrintablePrincipalMeetingSlip
          meeting={activePrincipalSlip}
          onClose={() => setActivePrincipalSlip(null)}
        />
      )}
    </div>
  );
}
