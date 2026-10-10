import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { useAuth } from "../../auth/AuthContext";
import { Card, DataTable, FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type ResidentRow = {
  id?: number;
  admission_id: number;
  student_id: number;
  admission_no: string;
  student_name: string;
  full_name?: string;
  gender: string;
  class_label: string;
  hostel_id: number;
  hostel_name: string;
  floor_number: number;
  room_number: string;
  bed_id: number;
  bed_number: string;
  admission_date: string;
  status: string;
};

type AllocationHistoryItem = {
  id: number;
  hostel_name: string;
  room_number: string;
  bed_number: string;
  allocated_at: string;
  vacated_at: string | null;
  is_active: boolean;
  remarks: string | null;
};

type AvailableBed = {
  bed_id: number;
  bed_number: string;
  room_number: string;
  floor_number: number;
};

export function HostelResidentsPage() {
  const qc = useQueryClient();
  const { can } = useAuth();

  const isProvost = can("hostel.resident.exit");

  // Search and filter state
  const [search, setSearch] = useState("");
  const [hostelFilter, setHostelFilter] = useState<string>("all");

  // Fetch residents
  const { data: residents = [], isLoading, error } = useQuery<ResidentRow[]>({
    queryKey: ["hostel", "residents"],
    queryFn: () => api.rawGet<ResidentRow[]>("/admin/hostel/residents"),
  });

  // Transfer Bed Modal state
  const [transferringResident, setTransferringResident] = useState<ResidentRow | null>(null);
  const [selectedNewBedId, setSelectedNewBedId] = useState<number | null>(null);
  const [transferReason, setTransferReason] = useState("");
  const [transferError, setTransferError] = useState<string | null>(null);

  // Available vacant beds for transfer
  const { data: availableBeds = [] } = useQuery<AvailableBed[]>({
    queryKey: ["hostel", "available-beds", transferringResident?.hostel_id],
    queryFn: () => api.rawGet<AvailableBed[]>(`/admin/hostel/${transferringResident?.hostel_id}/available-beds`),
    enabled: !!transferringResident,
  });

  // Allocation History Modal state
  const [historyAdmissionId, setHistoryAdmissionId] = useState<number | null>(null);
  const [historyStudentName, setHistoryStudentName] = useState<string>("");

  const { data: history = [], isLoading: isLoadingHistory } = useQuery<AllocationHistoryItem[]>({
    queryKey: ["hostel", "history", historyAdmissionId],
    queryFn: () => api.rawGet<AllocationHistoryItem[]>(`/admin/hostel/admissions/${historyAdmissionId}/history`),
    enabled: !!historyAdmissionId,
  });

  // Exit Student Modal state (Chief Provost only)
  const [exitingAdmission, setExitingAdmission] = useState<ResidentRow | null>(null);
  const [exitDate, setExitDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [exitReason, setExitReason] = useState("");
  const [exitError, setExitError] = useState<string | null>(null);

  // Transfer mutation
  const transferMutation = useMutation({
    mutationFn: async () => {
      if (!transferringResident || !selectedNewBedId) throw new Error("Select destination bed");
      const admId = transferringResident.admission_id ?? transferringResident.id;
      return api.rawPost(`/admin/hostel/admissions/${admId}/transfer`, {
        new_bed_id: selectedNewBedId,
        reason: transferReason.trim() || undefined,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setTransferringResident(null);
      setSelectedNewBedId(null);
      setTransferReason("");
      setTransferError(null);
    },
    onError: (err: any) => {
      setTransferError(errorText(err));
    },
  });

  // Exit mutation (Chief Provost only)
  const exitMutation = useMutation({
    mutationFn: async () => {
      if (!exitingAdmission) throw new Error("No admission selected");
      if (!exitReason.trim()) throw new Error("Exit reason is required");
      const admId = exitingAdmission.admission_id ?? exitingAdmission.id;
      return api.rawPost(`/admin/hostel/admissions/${admId}/exit`, {
        exit_date: exitDate,
        exit_reason: exitReason.trim(),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setExitingAdmission(null);
      setExitReason("");
      setExitError(null);
    },
    onError: (err: any) => {
      setExitError(errorText(err));
    },
  });

  // Filter residents
  const filtered = residents.filter((r) => {
    if (hostelFilter !== "all" && String(r.hostel_id) !== hostelFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        r.student_name.toLowerCase().includes(q) ||
        r.admission_no.toLowerCase().includes(q) ||
        r.room_number.toLowerCase().includes(q) ||
        r.bed_number.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Unique hostels for filter
  const hostelsList = Array.from(
    new Map(residents.map((r) => [r.hostel_id, { id: r.hostel_id, name: r.hostel_name }])).values(),
  );

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Residents Roster</h1>
          <p className="text-sm text-ink-soft mt-1">
            Active residential students, room and bed allocations, room transfers, and stay history.
          </p>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <input
          type="text"
          className={`${inputClass} flex-1`}
          placeholder="Search by student name, admission no, room, or bed..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {hostelsList.length > 1 && (
          <select
            className={inputClass}
            value={hostelFilter}
            onChange={(e) => setHostelFilter(e.target.value)}
          >
            <option value="all">All Hostels ({residents.length})</option>
            {hostelsList.map((h) => (
              <option key={h.id} value={String(h.id)}>
                {h.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Residents Table */}
      <Card>
        {isLoading ? (
          <p className="text-sm text-ink-soft text-center py-8">Loading residents...</p>
        ) : error ? (
          <p className="text-sm text-danger text-center py-4">Failed to load residents roster.</p>
        ) : (
          <DataTable
            rows={filtered}
            empty="No residents found matching the criteria."
            columns={[
              {
                key: "student",
                header: "Student",
                render: (r: ResidentRow) => (
                  <div>
                    <span className="font-semibold text-ink text-sm">{r.student_name || r.full_name}</span>
                    <p className="text-2xs text-ink-soft">
                      Adm #{r.admission_no} • {r.class_label}
                    </p>
                  </div>
                ),
              },
              {
                key: "hostel",
                header: "Hostel",
                render: (r: ResidentRow) => <span className="text-xs text-ink">{r.hostel_name}</span>,
              },
              {
                key: "location",
                header: "Location",
                render: (r: ResidentRow) => (
                  <div>
                    <span className="text-xs font-semibold text-ink">Room {r.room_number}</span>
                    <p className="text-2xs text-ink-soft">
                      {r.floor_number ? `Floor ${r.floor_number} • ` : ""}Bed {r.bed_number}
                    </p>
                  </div>
                ),
              },
              {
                key: "admission_date",
                header: "Admitted On",
                render: (r: ResidentRow) => (
                  <span className="text-xs text-ink-soft">{r.admission_date}</span>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (r: ResidentRow) => <Pill status={r.status}>{r.status}</Pill>,
              },
              {
                key: "actions",
                header: "Actions",
                render: (r: ResidentRow) => (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setHistoryAdmissionId(r.admission_id ?? r.id ?? null);
                        setHistoryStudentName(r.student_name ?? r.full_name ?? "");
                      }}
                      className="px-2 py-1 rounded border border-rule text-2xs font-semibold text-ink hover:bg-ground"
                    >
                      History
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setTransferringResident({
                          ...r,
                          admission_id: r.admission_id ?? r.id ?? 0,
                          student_name: r.student_name ?? r.full_name ?? "",
                        });
                        setSelectedNewBedId(null);
                        setTransferReason("");
                        setTransferError(null);
                      }}
                      className="px-2 py-1 rounded bg-surface border border-primary/40 text-primary text-2xs font-semibold hover:bg-primary/5"
                    >
                      Transfer
                    </button>
                    {isProvost && (
                      <button
                        type="button"
                        onClick={() => {
                          setExitingAdmission({
                            ...r,
                            admission_id: r.admission_id ?? r.id ?? 0,
                            student_name: r.student_name ?? r.full_name ?? "",
                          });
                          setExitDate(new Date().toISOString().split("T")[0]);
                          setExitReason("");
                          setExitError(null);
                        }}
                        className="px-2 py-1 rounded bg-surface border border-danger/40 text-danger text-2xs font-semibold hover:bg-danger/5"
                      >
                        Exit Student
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
          />
        )}
      </Card>

      {/* Transfer Room/Bed Modal */}
      {transferringResident && (
        <Modal
          title={`Transfer Bed: ${transferringResident.student_name}`}
          onClose={() => setTransferringResident(null)}
        >
          <div className="space-y-4">
            <div className="p-3 bg-ground rounded border border-rule text-xs">
              <p>
                <span className="font-semibold text-ink">Current Allotment:</span> {transferringResident.hostel_name}, Room {transferringResident.room_number}, Bed {transferringResident.bed_number}
              </p>
            </div>

            {transferError && <p className="text-sm text-danger">{transferError}</p>}

            <FormField label="Select Vacant Bed in Hostel *">
              <select
                className={inputClass}
                value={selectedNewBedId || ""}
                onChange={(e) => setSelectedNewBedId(Number(e.target.value) || null)}
              >
                <option value="">-- Choose Destination Bed --</option>
                {availableBeds
                  .filter((b) => b.bed_id !== transferringResident.bed_id)
                  .map((b) => (
                    <option key={b.bed_id} value={b.bed_id}>
                      Floor {b.floor_number} • Room {b.room_number} • Bed {b.bed_number}
                    </option>
                  ))}
              </select>
            </FormField>

            {availableBeds.length <= 1 && (
              <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
                No other vacant beds available in this hostel.
              </p>
            )}

            <FormField label="Reason for Transfer (Mandatory for record)">
              <input
                type="text"
                className={inputClass}
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                placeholder="e.g. Mutual room shift, medical preference, senior study quiet wing"
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setTransferringResident(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedNewBedId || transferMutation.isPending}
                onClick={() => transferMutation.mutate()}
                className="px-4 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {transferMutation.isPending ? "Transferring..." : "Confirm Transfer"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Allocation History Modal */}
      {historyAdmissionId && (
        <Modal
          title={`Allocation History: ${historyStudentName}`}
          onClose={() => setHistoryAdmissionId(null)}
        >
          <div className="space-y-4">
            {isLoadingHistory ? (
              <p className="text-xs text-ink-soft py-4 text-center">Loading allocation timeline...</p>
            ) : history.length === 0 ? (
              <p className="text-xs text-ink-soft py-4 text-center">No prior allocation history recorded.</p>
            ) : (
              <div className="space-y-3">
                {history.map((h, i) => (
                  <div
                    key={h.id}
                    className={`p-3 rounded border text-xs ${
                      h.is_active ? "bg-emerald-50/50 border-emerald-200" : "bg-ground border-rule"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-ink">
                        {h.hostel_name} • Room {h.room_number} • Bed {h.bed_number}
                      </span>
                      <Pill status={h.is_active ? "active" : "neutral"}>
                        {h.is_active ? "Active Allocation" : "Vacated"}
                      </Pill>
                    </div>
                    <div className="text-2xs text-ink-soft mt-1.5 flex gap-4">
                      <span>Allocated: {new Date(h.allocated_at).toLocaleDateString()}</span>
                      {h.vacated_at && (
                        <span>Vacated: {new Date(h.vacated_at).toLocaleDateString()}</span>
                      )}
                    </div>
                    {h.remarks && (
                      <p className="text-2xs text-ink-soft mt-1 italic">Remarks: {h.remarks}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setHistoryAdmissionId(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Chief Provost Exclusive Exit Student Modal */}
      {exitingAdmission && (
        <Modal
          title={`Permanent Hostel Exit: ${exitingAdmission.student_name}`}
          onClose={() => setExitingAdmission(null)}
        >
          <div className="space-y-4">
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-900">
              <p className="font-bold">Chief Provost Authorization Required</p>
              <p className="mt-0.5">
                Permanently exits the student from hostel accommodation. The student will revert to Day Scholar status and hostel fee billing will terminate.
              </p>
            </div>

            {exitError && <p className="text-sm text-danger">{exitError}</p>}

            <FormField label="Effective Exit Date *">
              <input
                type="date"
                className={inputClass}
                value={exitDate}
                onChange={(e) => setExitDate(e.target.value)}
              />
            </FormField>

            <FormField label="Mandatory Exit Reason *">
              <textarea
                className={`${inputClass} min-h-[80px]`}
                value={exitReason}
                onChange={(e) => setExitReason(e.target.value)}
                placeholder="State the reason for hostel exit (e.g. Parent requested reversion to day scholar, completed senior secondary session, disciplinary transfer)..."
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setExitingAdmission(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!exitReason.trim() || exitMutation.isPending}
                onClick={() => exitMutation.mutate()}
                className="px-4 py-1.5 rounded bg-danger text-white text-xs font-semibold hover:bg-danger/90 disabled:opacity-50"
              >
                {exitMutation.isPending ? "Exiting..." : "Confirm Permanent Exit"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
