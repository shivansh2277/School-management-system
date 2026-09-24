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
  PrintableStudentPass,
  StudentPassData,
} from "../../components/reception/PrintableStudentPass";

export interface StudentAuthorizedPerson {
  id: number;
  school_id: number;
  student_id: number;
  name: string;
  relationship: string;
  phone: string;
  id_proof_type?: string | null;
  id_proof_number?: string | null;
  photo_url?: string | null;
  is_active: boolean;
  notes?: string | null;
}

export function StudentPassPage() {
  const queryClient = useQueryClient();
  const { me } = useAuth();

  const [dateFilter, setDateFilter] = useState<string>(new Date().toISOString().slice(0, 10));
  const [search, setSearch] = useState<string>("");

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activePrintPass, setActivePrintPass] = useState<StudentPassData | null>(null);
  const [showRosterModal, setShowRosterModal] = useState(false);
  const [rosterStudent, setRosterStudent] = useState<{ id: number; name: string; admission_no: string } | null>(null);

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // Form states for creating a pass
  const [passForm, setPassForm] = useState({
    student_id: 0,
    student_name: "",
    admission_no: "",
    class_name: "",
    reason: "Medical appointment / Feeling unwell",
    pickup_person_name: "",
    pickup_person_relation: "Parent / Father",
    pickup_person_phone: "",
    pickup_person_id_proof: "",
    pickup_person_photo_url: null as string | null,
    pass_date: new Date().toISOString().slice(0, 10),
    pass_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    remarks: "",
  });

  // Form state for managing student authorized persons roster
  const [rosterForm, setRosterForm] = useState({
    name: "",
    relationship: "Uncle",
    phone: "",
    id_proof_type: "Aadhaar",
    id_proof_number: "",
    photo_url: "",
    notes: "",
  });

  const [studentSearchQuery, setStudentSearchQuery] = useState("");

  // Queries
  const passesQuery = useQuery({
    queryKey: ["student-passes", dateFilter, search],
    queryFn: () => {
      const params = new URLSearchParams();
      if (dateFilter) params.append("pass_date", dateFilter);
      if (search) params.append("search", search);
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/reception/passes${q}` as any) as Promise<StudentPassData[]>;
    },
  });

  const studentSearchQueryResults = useQuery({
    queryKey: ["student-search-passes", studentSearchQuery],
    queryFn: () => {
      return api.get(`/admin/reception/students/search?q=${encodeURIComponent(studentSearchQuery)}` as any) as Promise<
        { id: number; admission_no: string; name: string; class_name: string; phone?: string }[]
      >;
    },
    enabled: studentSearchQuery.trim().length >= 2,
  });

  // Query authorized persons for the currently selected student in pass creation
  const authorizedPersonsQuery = useQuery({
    queryKey: ["student-authorized-persons", passForm.student_id],
    queryFn: () => {
      return api.get(`/admin/reception/students/${passForm.student_id}/authorized-persons` as any) as Promise<
        StudentAuthorizedPerson[]
      >;
    },
    enabled: passForm.student_id > 0,
  });

  // Query authorized persons for the roster management modal
  const rosterPersonsQuery = useQuery({
    queryKey: ["student-roster-persons", rosterStudent?.id],
    queryFn: () => {
      return api.get(`/admin/reception/students/${rosterStudent?.id}/authorized-persons` as any) as Promise<
        StudentAuthorizedPerson[]
      >;
    },
    enabled: !!rosterStudent && rosterStudent.id > 0,
  });

  // Mutations
  const createPassMutation = useMutation({
    mutationFn: (data: typeof passForm) => {
      return api.post("/admin/reception/passes" as any, {
        student_id: data.student_id,
        reason: data.reason,
        pickup_person_name: data.pickup_person_name,
        pickup_person_relation: data.pickup_person_relation,
        pickup_person_phone: data.pickup_person_phone,
        pickup_person_id_proof: data.pickup_person_id_proof || null,
        pass_date: data.pass_date,
        pass_time: data.pass_time,
        remarks: data.remarks || null,
      }) as Promise<StudentPassData>;
    },
    onSuccess: (newPass: StudentPassData) => {
      queryClient.invalidateQueries({ queryKey: ["student-passes"] });
      setShowCreateModal(false);
      setActivePrintPass({
        ...newPass,
        pickup_person_photo_url: passForm.pickup_person_photo_url,
      });
    },
  });

  const updatePassStatusMutation = useMutation({
    mutationFn: ({ passId, status }: { passId: number; status: string }) => {
      return api.patch(`/admin/reception/passes/${passId}/status` as any, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-passes"] });
    },
  });

  const addRosterPersonMutation = useMutation({
    mutationFn: (data: typeof rosterForm) => {
      return api.post(`/admin/reception/students/${rosterStudent?.id}/authorized-persons` as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-roster-persons"] });
      queryClient.invalidateQueries({ queryKey: ["student-authorized-persons"] });
      setRosterForm({
        name: "",
        relationship: "Uncle",
        phone: "",
        id_proof_type: "Aadhaar",
        id_proof_number: "",
        photo_url: "",
        notes: "",
      });
    },
  });

  const deleteRosterPersonMutation = useMutation({
    mutationFn: (personId: number) => {
      return api.del(`/admin/reception/authorized-persons/${personId}` as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-roster-persons"] });
      queryClient.invalidateQueries({ queryKey: ["student-authorized-persons"] });
    },
  });

  const passes = passesQuery.data || [];

  const handleSelectStudentForPass = (s: { id: number; admission_no: string; name: string; class_name: string }) => {
    setPassForm((prev) => ({
      ...prev,
      student_id: s.id,
      student_name: s.name,
      admission_no: s.admission_no,
      class_name: s.class_name,
    }));
    setStudentSearchQuery("");
  };

  const handleSelectAuthorizedPerson = (person: StudentAuthorizedPerson) => {
    setPassForm((prev) => ({
      ...prev,
      pickup_person_name: person.name,
      pickup_person_relation: person.relationship,
      pickup_person_phone: person.phone,
      pickup_person_id_proof: person.id_proof_number
        ? `${person.id_proof_type || "ID"}: ${person.id_proof_number}`
        : "",
      pickup_person_photo_url: person.photo_url || null,
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header & New Pass Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Student Gate Pass System</h1>
          <p className="text-sm text-ink-faint">
            Issue one-time departure gate passes on behalf of parents, verify escorts, and manage permanent authorized rosters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Can permission="reception.passes.write">
            <button
              type="button"
              onClick={() => {
                setPassForm({
                  student_id: 0,
                  student_name: "",
                  admission_no: "",
                  class_name: "",
                  reason: "Medical emergency / unwell",
                  pickup_person_name: "",
                  pickup_person_relation: "Parent / Father",
                  pickup_person_phone: "",
                  pickup_person_id_proof: "",
                  pickup_person_photo_url: null,
                  pass_date: new Date().toISOString().slice(0, 10),
                  pass_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
                  remarks: "",
                });
                setShowCreateModal(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-semibold rounded-pill shadow-sm hover:opacity-90 transition"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              Issue Gate Pass
            </button>
          </Can>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Passes Issued" value={passes.length} hint="Passes registered for selected date" />
        <StatCard
          label="Active / In Departure"
          value={passes.filter((p) => p.status === "issued").length}
          hint="Awaiting gate security checkpoint sign-off"
        />
        <StatCard
          label="Departed / Completed"
          value={passes.filter((p) => p.status === "departed").length}
          hint="Student successfully signed out of campus"
        />
      </div>

      {/* Filter and Table Card */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center mb-4">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-ink-faint uppercase">Date:</span>
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="text-xs rounded-pill border border-rule px-3 py-1 bg-surface text-ink"
              />
            </div>
            {dateFilter && (
              <button
                type="button"
                onClick={() => setDateFilter("")}
                className="text-xs text-primary hover:underline font-medium"
              >
                Clear Date
              </button>
            )}
          </div>

          <div className="w-full sm:w-72">
            <input
              type="text"
              placeholder="Search pass code, student, escort..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        <DataTable<StudentPassData>
          columns={[
            {
              key: "pass_code",
              header: "Pass Code & Time",
              render: (row) => (
                <div>
                  <span className="font-mono font-bold text-primary block">{row.pass_code}</span>
                  <span className="text-xs text-ink-faint">
                    {row.pass_date} at {row.pass_time}
                  </span>
                </div>
              ),
            },
            {
              key: "student",
              header: "Student Particulars",
              render: (row) => (
                <div>
                  <span className="font-semibold text-ink block">{row.student_name}</span>
                  <span className="text-xs text-ink-faint font-mono">
                    Adm: {row.admission_no} • {row.class_name || "—"}
                  </span>
                </div>
              ),
            },
            {
              key: "escort",
              header: "Pickup Person / Escort",
              render: (row) => (
                <div>
                  <span className="font-semibold text-ink block">{row.pickup_person_name}</span>
                  <span className="text-xs text-ink-faint">
                    {row.pickup_person_relation} • {row.pickup_person_phone}
                  </span>
                  {row.pickup_person_id_proof && (
                    <span className="block text-[10px] text-ink-faint">{row.pickup_person_id_proof}</span>
                  )}
                </div>
              ),
            },
            {
              key: "reason",
              header: "Reason for Leaving",
              render: (row) => (
                <div className="max-w-xs">
                  <span className="text-xs text-ink font-medium block truncate">{row.reason}</span>
                  {row.remarks && <span className="text-[10px] text-ink-faint block truncate">{row.remarks}</span>}
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <Pill status={row.status === "departed" ? "active" : row.status === "cancelled" ? "danger" : "pending"}>
                  {row.status.toUpperCase()}
                </Pill>
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
                    onClick={() => setActivePrintPass(row)}
                    className="px-2.5 py-1 text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded transition"
                  >
                    Print Slip
                  </button>

                  {row.status === "issued" && (
                    <>
                      <button
                        type="button"
                        onClick={() => updatePassStatusMutation.mutate({ passId: row.id, status: "departed" })}
                        className="px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50 rounded transition"
                      >
                        Departed
                      </button>
                      <button
                        type="button"
                        onClick={() => updatePassStatusMutation.mutate({ passId: row.id, status: "cancelled" })}
                        className="px-2 py-1 text-xs font-medium text-danger hover:bg-danger/10 rounded transition"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              ),
            },
          ]}
          rows={passes}
          empty="No gate passes found for this date or search."
          loading={passesQuery.isLoading}
          error={passesQuery.error}
        />
      </Card>

      {/* Modal: Issue Student Pass */}
      {showCreateModal && (
        <Modal title="Issue One-Time Student Gate Pass" onClose={() => setShowCreateModal(false)} wide>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!passForm.student_id) {
                alert("Please select an enrolled student first.");
                return;
              }
              createPassMutation.mutate(passForm);
            }}
            className="space-y-4"
          >
            {/* Step 1: Student Search & Selection */}
            <div className="border border-rule rounded p-3 bg-ground/50">
              <span className="text-xs font-bold text-ink uppercase tracking-wider block mb-1">
                1. Select Enrolled Student
              </span>
              {passForm.student_id ? (
                <div className="flex items-center justify-between p-2.5 bg-surface border border-primary/30 rounded">
                  <div>
                    <span className="font-bold text-ink text-sm block">{passForm.student_name}</span>
                    <span className="text-xs text-ink-faint font-mono">
                      Admission No: {passForm.admission_no} • {passForm.class_name || "—"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setRosterStudent({
                          id: passForm.student_id,
                          name: passForm.student_name,
                          admission_no: passForm.admission_no,
                        });
                        setShowRosterModal(true);
                      }}
                      className="px-2.5 py-1 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition"
                    >
                      Manage Authorized Roster
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setPassForm((prev) => ({
                          ...prev,
                          student_id: 0,
                          student_name: "",
                          admission_no: "",
                          class_name: "",
                        }))
                      }
                      className="text-xs text-danger hover:underline font-medium"
                    >
                      Change Student
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <input
                    type="text"
                    placeholder="Search by student name or admission number..."
                    value={studentSearchQuery}
                    onChange={(e) => setStudentSearchQuery(e.target.value)}
                    className={inputClass}
                  />
                  {studentSearchQueryResults.data && studentSearchQueryResults.data.length > 0 && (
                    <div className="mt-2 border border-rule rounded bg-surface max-h-36 overflow-y-auto divide-y divide-rule">
                      {studentSearchQueryResults.data.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => handleSelectStudentForPass(s)}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-ground flex justify-between items-center"
                        >
                          <div>
                            <span className="font-semibold text-ink">{s.name}</span>
                            <span className="text-ink-faint ml-2 font-mono">({s.admission_no})</span>
                          </div>
                          <span className="text-ink-faint font-medium">{s.class_name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Permanent Authorized Roster Quick Select */}
            {passForm.student_id > 0 && (
              <div className="border border-rule rounded p-3 bg-surface">
                <span className="text-xs font-bold text-ink uppercase tracking-wider block mb-1">
                  2. Permanent Authorized Pickup Persons (Master Record)
                </span>
                <p className="text-[11px] text-ink-faint mb-2">
                  Click any verified permanent person below to auto-fill pass escort details, or type an ad-hoc escort below.
                </p>

                {authorizedPersonsQuery.data && authorizedPersonsQuery.data.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {authorizedPersonsQuery.data.map((person) => (
                      <button
                        key={person.id}
                        type="button"
                        onClick={() => handleSelectAuthorizedPerson(person)}
                        className="text-left p-2.5 rounded border border-rule hover:border-primary/50 hover:bg-primary/5 transition text-xs flex justify-between items-center gap-2"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          {person.photo_url ? (
                            <img
                              src={
                                person.photo_url.startsWith("http")
                                  ? person.photo_url
                                  : `${apiBase}${person.photo_url.startsWith("/") ? "" : "/"}${person.photo_url}`
                              }
                              alt={person.name}
                              className="w-8 h-8 rounded-full object-cover border border-rule shadow-xs flex-shrink-0"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs flex-shrink-0">
                              {person.name.charAt(0)}
                            </div>
                          )}
                          <div className="min-w-0">
                            <span className="font-bold text-ink block truncate">{person.name}</span>
                            <span className="text-ink-faint truncate block text-[11px]">
                              {person.relationship} • {person.phone}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold uppercase flex-shrink-0">
                          Authorized
                        </span>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-2 bg-ground text-center text-xs text-ink-faint rounded">
                    No permanent authorized persons registered yet for this student.
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Escort / Pickup Details */}
            <div className="border border-rule rounded p-3 bg-surface space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-ink uppercase tracking-wider">
                  3. Escort Particulars (One-Time Gate Pass Recipient)
                </span>
                <span className="text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Invariant: Entering details here does NOT alter the student's permanent roster.
                </span>
              </div>

              {passForm.pickup_person_photo_url && (
                <div className="flex items-center gap-3 p-2 bg-primary/5 border border-primary/20 rounded">
                  <img
                    src={
                      passForm.pickup_person_photo_url.startsWith("http")
                        ? passForm.pickup_person_photo_url
                        : `http://localhost:8000${passForm.pickup_person_photo_url.startsWith("/") ? "" : "/"}${passForm.pickup_person_photo_url}`
                    }
                    alt={passForm.pickup_person_name || "Escort photo"}
                    className="w-12 h-12 rounded object-cover border border-primary/30 shadow-sm shrink-0"
                  />
                  <div className="text-xs">
                    <span className="font-bold text-ink block">Verified Escort Photo Attached</span>
                    <span className="text-ink-faint">Included on printed student exit slip</span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3">
                <FormField label="Escort / Pickup Name">
                  <input
                    type="text"
                    required
                    placeholder="Full Name"
                    value={passForm.pickup_person_name}
                    onChange={(e) => setPassForm({ ...passForm, pickup_person_name: e.target.value })}
                    className={inputClass}
                  />
                </FormField>

                <FormField label="Relationship">
                  <input
                    type="text"
                    required
                    placeholder="e.g. Father, Mother, Uncle, Grandparent"
                    value={passForm.pickup_person_relation}
                    onChange={(e) => setPassForm({ ...passForm, pickup_person_relation: e.target.value })}
                    className={inputClass}
                  />
                </FormField>

                <FormField label="Contact Phone">
                  <input
                    type="text"
                    required
                    placeholder="+91..."
                    value={passForm.pickup_person_phone}
                    onChange={(e) => setPassForm({ ...passForm, pickup_person_phone: e.target.value })}
                    className={inputClass}
                  />
                </FormField>
              </div>

              <FormField label="ID Proof Type & Last 4 Digits">
                <input
                  type="text"
                  placeholder="e.g. Aadhaar XXXX-XXXX-1234, Driver License DL-..."
                  value={passForm.pickup_person_id_proof}
                  onChange={(e) => setPassForm({ ...passForm, pickup_person_id_proof: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            {/* Reason and Date/Time */}
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <FormField label="Reason for Leaving Campus">
                  <input
                    type="text"
                    required
                    placeholder="e.g. Severe headache, family emergency, official dentist visit"
                    value={passForm.reason}
                    onChange={(e) => setPassForm({ ...passForm, reason: e.target.value })}
                    className={inputClass}
                  />
                </FormField>
              </div>

              <FormField label="Pass Departure Time">
                <input
                  type="text"
                  required
                  placeholder="e.g. 01:30 PM"
                  value={passForm.pass_time}
                  onChange={(e) => setPassForm({ ...passForm, pass_time: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Remarks / Office Notes">
              <input
                type="text"
                placeholder="Parent telephonic confirmation taken by receptionist..."
                value={passForm.remarks}
                onChange={(e) => setPassForm({ ...passForm, remarks: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createPassMutation.isPending}
                className="px-5 py-2 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm"
              >
                {createPassMutation.isPending ? "Generating..." : "Generate & Print Gate Pass"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Permanent Authorized Persons Roster (Editable on Student Master Record) */}
      {showRosterModal && rosterStudent && (
        <Modal
          title={`Permanent Authorized Pickup Roster: ${rosterStudent.name} (${rosterStudent.admission_no})`}
          onClose={() => setShowRosterModal(false)}
          wide
        >
          <div className="space-y-4">
            <div className="p-2.5 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900">
              <span className="font-semibold">Student Master Record Roster: </span>
              Receptionist can edit permanent authorized persons upon parent request. Entries saved here are stored
              permanently on the student master record and pre-populate future gate pass forms.
            </div>

            {/* List of existing roster persons */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-ink uppercase tracking-wider block">
                Current Authorized Persons
              </span>
              {rosterPersonsQuery.data && rosterPersonsQuery.data.length > 0 ? (
                <div className="divide-y divide-rule border border-rule rounded bg-surface">
                  {rosterPersonsQuery.data.map((p) => (
                    <div key={p.id} className="p-3 flex justify-between items-center text-xs gap-3">
                      <div className="flex items-center gap-2.5 min-w-0">
                        {p.photo_url ? (
                          <img
                            src={
                              p.photo_url.startsWith("http")
                                ? p.photo_url
                                : `${apiBase}${p.photo_url.startsWith("/") ? "" : "/"}${p.photo_url}`
                            }
                            alt={p.name}
                            className="w-9 h-9 rounded-full object-cover border border-rule shadow-xs flex-shrink-0"
                          />
                        ) : (
                          <div className="w-9 h-9 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs flex-shrink-0">
                            {p.name.charAt(0)}
                          </div>
                        )}
                        <div className="min-w-0">
                          <span className="font-bold text-ink block truncate">{p.name}</span>
                          <span className="text-ink-faint">
                            {p.relationship} • Tel: {p.phone}
                            {p.id_proof_number ? ` • ${p.id_proof_type || "ID"}: ${p.id_proof_number}` : ""}
                          </span>
                          {p.notes && <span className="block text-[10px] text-ink-faint mt-0.5">{p.notes}</span>}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => deleteRosterPersonMutation.mutate(p.id)}
                        className="text-xs text-danger hover:bg-danger/10 px-2 py-1 rounded transition flex-shrink-0"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 text-center text-xs text-ink-faint border border-rule rounded">
                  No permanent authorized persons on file for this student.
                </div>
              )}
            </div>

            {/* Add new permanent person */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                addRosterPersonMutation.mutate(rosterForm);
              }}
              className="border border-rule rounded p-3 bg-ground/40 space-y-3"
            >
              <span className="text-xs font-bold text-ink uppercase tracking-wider block">
                Add New Permanent Authorized Person
              </span>

              <div className="grid grid-cols-3 gap-3">
                <FormField label="Full Name">
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramesh Chandra"
                    value={rosterForm.name}
                    onChange={(e) => setRosterForm({ ...rosterForm, name: e.target.value })}
                    className={inputClass}
                  />
                </FormField>

                <FormField label="Relationship">
                  <input
                    type="text"
                    required
                    placeholder="e.g. Uncle, Grandparent, Driver"
                    value={rosterForm.relationship}
                    onChange={(e) => setRosterForm({ ...rosterForm, relationship: e.target.value })}
                    className={inputClass}
                  />
                </FormField>

                <FormField label="Phone Number">
                  <input
                    type="text"
                    required
                    placeholder="+91..."
                    value={rosterForm.phone}
                    onChange={(e) => setRosterForm({ ...rosterForm, phone: e.target.value })}
                    className={inputClass}
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="ID Proof Type">
                  <select
                    value={rosterForm.id_proof_type}
                    onChange={(e) => setRosterForm({ ...rosterForm, id_proof_type: e.target.value })}
                    className={inputClass}
                  >
                    <option value="Aadhaar">Aadhaar Card</option>
                    <option value="Driver License">Driver License</option>
                    <option value="Voter ID">Voter ID</option>
                    <option value="Passport">Passport</option>
                  </select>
                </FormField>

                <FormField label="ID Proof Number">
                  <input
                    type="text"
                    placeholder="e.g. XXXX-XXXX-4589"
                    value={rosterForm.id_proof_number}
                    onChange={(e) => setRosterForm({ ...rosterForm, id_proof_number: e.target.value })}
                    className={inputClass}
                  />
                </FormField>
              </div>

              <FormField label="Authorization Notes">
                <input
                  type="text"
                  placeholder="e.g. Authorized for daily evening pickup and emergency doctor visits"
                  value={rosterForm.notes}
                  onChange={(e) => setRosterForm({ ...rosterForm, notes: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={addRosterPersonMutation.isPending}
                  className="px-4 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-pill hover:bg-blue-700 transition"
                >
                  {addRosterPersonMutation.isPending ? "Adding..." : "Save to Student Master Record"}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}

      {/* Printable Gate Pass Slip Modal */}
      {activePrintPass && (
        <PrintableStudentPass pass={activePrintPass} onClose={() => setActivePrintPass(null)} />
      )}
    </div>
  );
}
