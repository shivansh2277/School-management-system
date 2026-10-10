import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { useAuth } from "../../auth/AuthContext";
import { Card, DataTable, FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type PendingApplication = {
  application_id: number;
  application_no: string;
  student_id: number;
  full_name: string;
  class_name: string;
  gender: string;
  submitted_at: string | null;
  hostel_request_status: string;
  is_allocated: boolean;
  allocated_hostel_name: string | null;
};

type DayScholar = {
  student_id: number;
  admission_no: string;
  full_name: string;
  gender: string;
  class_label: string;
};

type HostelBasic = {
  id: number;
  name: string;
  code: string;
  gender: string;
};

type AvailableBed = {
  id?: number;
  bed_id?: number;
  bed_number: string;
  room_number: string;
  floor_number: number;
};

export function HostelAdmissionsPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"intake" | "day_scholar">("intake");

  // Fetch pending applications with hostel requests
  const { data: intakeQueue = [], isLoading: loadingIntake } = useQuery<PendingApplication[]>({
    queryKey: ["hostel", "pending-applications"],
    queryFn: () => api.rawGet<PendingApplication[]>("/admin/hostel/admissions/pending-applications"),
  });

  // Fetch eligible Class 9+ day scholars
  const { data: dayScholars = [], isLoading: loadingDayScholars } = useQuery<DayScholar[]>({
    queryKey: ["hostel", "eligible-day-scholars"],
    queryFn: () => api.rawGet<DayScholar[]>("/admin/hostel/admissions/eligible-students"),
  });

  // Fetch hostels
  const { data: hostels = [] } = useQuery<HostelBasic[]>({
    queryKey: ["hostel", "list"],
    queryFn: () => api.rawGet<HostelBasic[]>("/admin/hostel/list"),
  });

  // Admission Modal State
  const [admittingStudent, setAdmittingStudent] = useState<{
    studentId: number;
    studentName: string;
    gender: string;
    className: string;
  } | null>(null);

  const [selectedHostelId, setSelectedHostelId] = useState<number | null>(null);
  const [selectedBedId, setSelectedBedId] = useState<number | null>(null);
  const [admissionDate, setAdmissionDate] = useState<string>(
    new Date().toISOString().split("T")[0],
  );
  const [admissionRemarks, setAdmissionRemarks] = useState("");
  const [modalError, setModalError] = useState<string | null>(null);

  // Filter hostels matching student gender
  const matchingHostels = hostels.filter(
    (h) => !admittingStudent || h.gender.toLowerCase() === admittingStudent.gender.toLowerCase(),
  );

  // Available beds for selected hostel
  const { data: availableBeds = [] } = useQuery<AvailableBed[]>({
    queryKey: ["hostel", "available-beds", selectedHostelId],
    queryFn: () => api.rawGet<AvailableBed[]>(`/admin/hostel/${selectedHostelId}/available-beds`),
    enabled: !!selectedHostelId,
  });

  // Direct admission mutation
  const admitMutation = useMutation({
    mutationFn: async () => {
      if (!admittingStudent || !selectedHostelId || !selectedBedId) {
        throw new Error("Select both hostel and bed");
      }
      return api.rawPost(`/admin/hostel/${selectedHostelId}/admissions/direct`, {
        student_id: admittingStudent.studentId,
        bed_id: selectedBedId,
        admission_date: admissionDate,
        remarks: admissionRemarks.trim() || undefined,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setAdmittingStudent(null);
      setSelectedHostelId(null);
      setSelectedBedId(null);
      setAdmissionRemarks("");
      setModalError(null);
    },
    onError: (err: any) => {
      setModalError(errorText(err));
    },
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Admissions Queue</h1>
          <p className="text-sm text-ink-soft mt-1">
            Process incoming enrolled applications and admit eligible Class 9+ day scholars.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-rule">
        <button
          type="button"
          onClick={() => setTab("intake")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            tab === "intake"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Application Intake Requests ({intakeQueue.filter((q) => !q.is_allocated).length} Pending)
        </button>
        <button
          type="button"
          onClick={() => setTab("day_scholar")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            tab === "day_scholar"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Day Scholars Direct Admission ({dayScholars.length} Eligible)
        </button>
      </div>

      {/* Tab 1: Application Intake Queue */}
      {tab === "intake" && (
        <Card title="Admission Pipeline Hostel Requests (Class 9+ Enrolled)">
          <div className="mb-4 p-3 bg-ground rounded border border-rule text-xs text-ink-soft">
            Students who indicated hostel accommodation was required on their admission application.
            Admission Cell handles school enrolment; Hostel Administration allocates building and bed.
          </div>

          {loadingIntake ? (
            <p className="text-xs text-ink-soft py-4 text-center">Loading applications...</p>
          ) : intakeQueue.length === 0 ? (
            <p className="text-xs text-ink-soft py-4 text-center">No hostel intake requests found.</p>
          ) : (
            <DataTable
              rows={intakeQueue}
              empty="No pending hostel intake requests found."
              columns={[
                {
                  key: "student",
                  header: "Applicant / Student",
                  render: (row: PendingApplication) => (
                    <div>
                      <span className="font-semibold text-ink text-sm">{row.full_name}</span>
                      <p className="text-2xs text-ink-soft">
                        App #{row.application_no} • {row.gender === "male" ? "Male" : "Female"}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "class",
                  header: "Class",
                  render: (row: PendingApplication) => (
                    <span className="text-xs font-semibold text-ink">Class {row.class_name}</span>
                  ),
                },
                {
                  key: "request_status",
                  header: "Request Status",
                  render: (row: PendingApplication) => (
                    <Pill status={row.is_allocated ? "active" : "neutral"}>
                      {row.hostel_request_status}
                    </Pill>
                  ),
                },
                {
                  key: "assigned_facility",
                  header: "Assigned Facility",
                  render: (row: PendingApplication) => (
                    <span className="text-xs text-ink">
                      {row.allocated_hostel_name || "—"}
                    </span>
                  ),
                },
                {
                  key: "action",
                  header: "Action",
                  render: (row: PendingApplication) =>
                    row.is_allocated ? (
                      <span className="text-2xs text-emerald-600 font-semibold">Allocated</span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setAdmittingStudent({
                            studentId: row.student_id,
                            studentName: row.full_name,
                            gender: row.gender,
                            className: row.class_name,
                          });
                          setSelectedHostelId(null);
                          setSelectedBedId(null);
                          setModalError(null);
                        }}
                        className="px-3 py-1 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition"
                      >
                        Allocate Bed
                      </button>
                    ),
                },
              ]}
            />
          )}
        </Card>
      )}

      {/* Tab 2: Day Scholars Independent Admission */}
      {tab === "day_scholar" && (
        <Card title="Eligible Enrolled Day Scholars (Class 9+)">
          <div className="mb-4 p-3 bg-ground rounded border border-rule text-xs text-ink-soft">
            Currently enrolled Class 9, 10, 11, and 12 day scholars available for independent hostel admission during the active session.
          </div>

          {loadingDayScholars ? (
            <p className="text-xs text-ink-soft py-4 text-center">Loading day scholars...</p>
          ) : dayScholars.length === 0 ? (
            <p className="text-xs text-ink-soft py-4 text-center">No unassigned Class 9+ day scholars found.</p>
          ) : (
            <DataTable
              rows={dayScholars}
              empty="No unassigned Class 9+ day scholars found."
              columns={[
                {
                  key: "student",
                  header: "Student",
                  render: (row: DayScholar) => (
                    <div>
                      <span className="font-semibold text-ink text-sm">{row.full_name}</span>
                      <p className="text-2xs text-ink-soft">
                        Adm #{row.admission_no} • {row.gender === "male" ? "Male" : "Female"}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "class",
                  header: "Class & Section",
                  render: (row: DayScholar) => (
                    <span className="text-xs font-semibold text-ink">{row.class_label}</span>
                  ),
                },
                {
                  key: "action",
                  header: "Action",
                  render: (row: DayScholar) => (
                    <button
                      type="button"
                      onClick={() => {
                        setAdmittingStudent({
                          studentId: row.student_id,
                          studentName: row.full_name,
                          gender: row.gender,
                          className: row.class_label,
                        });
                        setSelectedHostelId(null);
                        setSelectedBedId(null);
                        setModalError(null);
                      }}
                      className="px-3 py-1 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition"
                    >
                      Admit to Hostel
                    </button>
                  ),
                },
              ]}
            />
          )}
        </Card>
      )}

      {/* Process Admission Modal */}
      {admittingStudent && (
        <Modal
          title={`Admit Student to Hostel: ${admittingStudent.studentName}`}
          onClose={() => setAdmittingStudent(null)}
        >
          <div className="space-y-4">
            <div className="p-3 bg-ground rounded border border-rule text-xs space-y-1">
              <p>
                <span className="font-semibold text-ink">Student:</span> {admittingStudent.studentName} ({admittingStudent.className})
              </p>
              <p>
                <span className="font-semibold text-ink">Gender Integrity:</span> Must be allocated to a{" "}
                <span className="font-semibold text-primary capitalize">{admittingStudent.gender}</span> hostel.
              </p>
            </div>

            {modalError && <p className="text-sm text-danger">{modalError}</p>}

            <FormField label="Hostel Building *">
              <select
                className={inputClass}
                value={selectedHostelId || ""}
                onChange={(e) => {
                  setSelectedHostelId(Number(e.target.value) || null);
                  setSelectedBedId(null);
                }}
              >
                <option value="">-- Select Matching Hostel --</option>
                {matchingHostels.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} ({h.code})
                  </option>
                ))}
              </select>
            </FormField>

            {matchingHostels.length === 0 && (
              <p className="text-xs text-rose-600 bg-rose-50 p-2 rounded border border-rose-200">
                No accessible hostels found matching gender: {admittingStudent.gender}.
              </p>
            )}

            {selectedHostelId && (
              <FormField label="Available Room & Bed *">
                <select
                  className={inputClass}
                  value={selectedBedId || ""}
                  onChange={(e) => setSelectedBedId(Number(e.target.value) || null)}
                >
                  <option value="">-- Choose Vacant Bed --</option>
                  {availableBeds.map((b) => {
                    const bId = b.bed_id ?? b.id;
                    return (
                      <option key={bId} value={bId}>
                        Floor {b.floor_number} • Room {b.room_number} • Bed {b.bed_number}
                      </option>
                    );
                  })}
                </select>
              </FormField>
            )}

            {selectedHostelId && availableBeds.length === 0 && (
              <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
                No vacant beds remaining in this hostel building.
              </p>
            )}

            <FormField label="Effective Admission Date *">
              <input
                type="date"
                className={inputClass}
                value={admissionDate}
                onChange={(e) => setAdmissionDate(e.target.value)}
              />
            </FormField>

            <FormField label="Remarks (Optional)">
              <input
                type="text"
                className={inputClass}
                value={admissionRemarks}
                onChange={(e) => setAdmissionRemarks(e.target.value)}
                placeholder="e.g. Regular hostel admission, room preference noted"
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setAdmittingStudent(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedHostelId || !selectedBedId || admitMutation.isPending}
                onClick={() => admitMutation.mutate()}
                className="px-4 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {admitMutation.isPending ? "Admitting..." : "Confirm Admission & Bed"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
