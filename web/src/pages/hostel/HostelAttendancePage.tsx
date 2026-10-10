import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { Card, FormError, Pill, inputClass } from "../../components/ui";

type HostelBasic = {
  id: number;
  name: string;
  code: string;
  gender: string;
};

type AttendanceEntry = {
  admission_id: number;
  student_id: number;
  admission_no: string;
  full_name: string;
  room_number: string;
  bed_number: string;
  status: "present" | "absent" | "on_leave" | "on_outing";
  is_on_approved_leave: boolean;
  leave_purpose: string | null;
  recorded_at: string | null;
};

export function HostelAttendancePage() {
  const qc = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  const [onDate, setOnDate] = useState<string>(
    new Date().toISOString().split("T")[0],
  );

  // Accessible hostels
  const { data: hostels = [] } = useQuery<HostelBasic[]>({
    queryKey: ["hostel", "list"],
    queryFn: () => api.rawGet<HostelBasic[]>("/admin/hostel/list"),
  });

  const selectedHostelId = searchParams.get("hostel_id")
    ? Number(searchParams.get("hostel_id"))
    : hostels[0]?.id;

  // Local state for attendance values before submitting
  const [rosterState, setRosterState] = useState<Record<number, "present" | "absent" | "on_leave" | "on_outing">>({});
  const [remarksState, setRemarksState] = useState<Record<number, string>>({});
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch roster
  const { data: serverRoster = [], isLoading, error } = useQuery<AttendanceEntry[]>({
    queryKey: ["hostel", "attendance-roster", selectedHostelId, onDate],
    queryFn: () =>
      api.rawGet<AttendanceEntry[]>(`/admin/hostel/${selectedHostelId}/attendance/roster?on_date=${onDate}`),
    enabled: !!selectedHostelId,
  });

  // Sync server roster into local state
  useEffect(() => {
    if (serverRoster.length > 0) {
      const initial: Record<number, "present" | "absent" | "on_leave" | "on_outing"> = {};
      serverRoster.forEach((r) => {
        initial[r.student_id] = r.status;
      });
      setRosterState(initial);
    }
  }, [serverRoster]);

  // Submit attendance mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!selectedHostelId) throw new Error("Select a hostel");
      const entries = serverRoster.map((r) => ({
        student_id: r.student_id,
        status: rosterState[r.student_id] || r.status,
        remarks: remarksState[r.student_id] || undefined,
      }));
      return api.rawPost(`/admin/hostel/${selectedHostelId}/attendance`, {
        attendance_date: onDate,
        entries,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setSubmitSuccess(true);
      setErrorMessage(null);
      setTimeout(() => setSubmitSuccess(false), 4000);
    },
    onError: (err: any) => {
      setErrorMessage(errorText(err));
    },
  });

  const handleMarkAllPresent = () => {
    const updated = { ...rosterState };
    serverRoster.forEach((r) => {
      // Don't overwrite if student is on approved leave/outing
      if (!r.is_on_approved_leave) {
        updated[r.student_id] = "present";
      }
    });
    setRosterState(updated);
  };

  const selectedHostel = hostels.find((h) => h.id === selectedHostelId);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Evening Attendance (8:00 PM)</h1>
          <p className="text-sm text-ink-soft mt-1">
            Mandatory daily residential check at 8:00 PM. Approved leaves and outings are auto-populated.
          </p>
        </div>

        {/* Date and Hostel Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {hostels.length > 1 && (
            <select
              className={inputClass}
              value={selectedHostelId || ""}
              onChange={(e) => setSearchParams({ hostel_id: e.target.value })}
            >
              {hostels.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </select>
          )}

          <input
            type="date"
            className={inputClass}
            value={onDate}
            onChange={(e) => setOnDate(e.target.value)}
          />
        </div>
      </div>

      {/* Info and helper banner */}
      <div className="p-4 bg-ground rounded-card border border-rule flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">
            {selectedHostel?.name || "Hostel"} Roll Register for {new Date(onDate).toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
          <p className="text-xs text-ink-soft mt-0.5">
            Scheduled audit check: 20:00:00 (8:00 PM) • Total residents: {serverRoster.length}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleMarkAllPresent}
            className="px-3 py-1.5 rounded border border-rule bg-surface text-ink text-xs font-semibold hover:bg-ground transition"
          >
            Mark All Unscheduled as Present
          </button>
          <button
            type="button"
            disabled={submitMutation.isPending || serverRoster.length === 0}
            onClick={() => submitMutation.mutate()}
            className="px-4 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover disabled:opacity-50 transition shadow-sm"
          >
            {submitMutation.isPending ? "Submitting..." : "Save 8:00 PM Attendance"}
          </button>
        </div>
      </div>

      {submitSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded text-xs font-semibold">
          ✓ Evening attendance saved successfully. Audit timestamp recorded.
        </div>
      )}

      {errorMessage && <p className="text-sm text-danger">{errorMessage}</p>}

      {/* Register List */}
      <Card>
        {isLoading ? (
          <p className="text-xs text-ink-soft py-6 text-center">Loading roster...</p>
        ) : error ? (
          <p className="text-xs text-danger py-4 text-center">
            Failed to load attendance roster. Note: Wardens are restricted to their assigned hostel.
          </p>
        ) : serverRoster.length === 0 ? (
          <p className="text-xs text-ink-soft py-6 text-center">No active residents in this hostel building.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-ground/60 text-ink-soft font-semibold border-b border-rule">
                <tr>
                  <th className="p-3">Resident Student</th>
                  <th className="p-3">Room / Bed</th>
                  <th className="p-3">Approved Status Note</th>
                  <th className="p-3">Attendance Action (8:00 PM)</th>
                  <th className="p-3">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule/60">
                {serverRoster.map((r) => {
                  const currentStatus = rosterState[r.student_id] || r.status;

                  return (
                    <tr key={r.student_id} className="hover:bg-ground/30 transition">
                      <td className="p-3">
                        <span className="font-semibold text-ink text-sm">{r.full_name}</span>
                        <p className="text-2xs text-ink-soft">Adm #{r.admission_no}</p>
                      </td>
                      <td className="p-3">
                        <span className="font-semibold text-ink">Room {r.room_number}</span>
                        <p className="text-2xs text-ink-soft">Bed {r.bed_number}</p>
                      </td>
                      <td className="p-3">
                        {r.is_on_approved_leave ? (
                          <span className="inline-flex items-center gap-1 text-2xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 font-medium">
                            ℹ️ Pre-approved Leave: {r.leave_purpose || "Permitted"}
                          </span>
                        ) : (
                          <span className="text-2xs text-ink-faint">In hostel campus</span>
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5">
                          {(["present", "absent", "on_leave", "on_outing"] as const).map((st) => {
                            const isSelected = currentStatus === st;
                            let activeClass = "";
                            if (isSelected) {
                              if (st === "present") activeClass = "bg-emerald-600 text-white font-bold";
                              else if (st === "absent") activeClass = "bg-rose-600 text-white font-bold";
                              else if (st === "on_leave") activeClass = "bg-blue-600 text-white font-bold";
                              else if (st === "on_outing") activeClass = "bg-purple-600 text-white font-bold";
                            } else {
                              activeClass = "bg-surface border border-rule text-ink-soft hover:bg-ground";
                            }

                            return (
                              <button
                                key={st}
                                type="button"
                                onClick={() =>
                                  setRosterState({ ...rosterState, [r.student_id]: st })
                                }
                                className={`px-2.5 py-1 rounded text-2xs capitalize transition ${activeClass}`}
                              >
                                {st.replace("_", " ")}
                              </button>
                            );
                          })}
                        </div>
                      </td>
                      <td className="p-3">
                        <input
                          type="text"
                          className={`${inputClass} text-2xs py-1`}
                          placeholder="Note (optional)..."
                          value={remarksState[r.student_id] ?? ""}
                          onChange={(e) =>
                            setRemarksState({ ...remarksState, [r.student_id]: e.target.value })
                          }
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
