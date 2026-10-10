import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Card, Pill } from "../../components/ui";

type HostelSummary = {
  id: number;
  name: string;
  code: string;
};

type Complaint = {
  id: number;
  hostel_id: number;
  hostel_name: string;
  student_name: string;
  room_number: string;
  category: string;
  title: string;
  description: string;
  status: string;
  resolution_remarks?: string | null;
  created_at: string;
};

type Incident = {
  id: number;
  hostel_id: number;
  hostel_name: string;
  student_name: string;
  title: string;
  description: string;
  severity: string;
  incident_date: string;
  action_taken?: string | null;
  status: string;
};

export function HostelComplaintsPage() {
  const queryClient = useQueryClient();
  const { can } = useAuth();
  const canManage = can("hostel.incident.manage");

  const [activeTab, setActiveTab] = useState<"complaints" | "incidents">("complaints");
  const [selectedHostelId, setSelectedHostelId] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const [resolveTarget, setResolveTarget] = useState<Complaint | null>(null);
  const [resolutionRemarks, setResolutionRemarks] = useState("");

  const [newComplaintModal, setNewComplaintModal] = useState(false);
  const [complaintForm, setComplaintForm] = useState({
    hostel_id: "",
    category: "maintenance",
    title: "",
    description: "",
  });

  const [newIncidentModal, setNewIncidentModal] = useState(false);
  const [incidentForm, setIncidentForm] = useState({
    hostel_id: "",
    title: "",
    description: "",
    severity: "medium",
    incident_date: new Date().toISOString().split("T")[0],
    action_taken: "",
  });

  // Query hostels
  const { data: hostels = [] } = useQuery<HostelSummary[]>({
    queryKey: ["hostel", "list"],
    queryFn: () => api.rawGet<HostelSummary[]>("/admin/hostel/list"),
  });

  // Query complaints
  const {
    data: complaints = [],
    isLoading: loadingComplaints,
  } = useQuery<Complaint[]>({
    queryKey: ["hostel", "complaints", selectedHostelId],
    queryFn: () =>
      api.rawGet<Complaint[]>(
        `/admin/hostel/complaints${selectedHostelId !== "all" ? `?hostel_id=${selectedHostelId}` : ""}`,
      ),
  });

  // Query incidents
  const {
    data: incidents = [],
    isLoading: loadingIncidents,
  } = useQuery<Incident[]>({
    queryKey: ["hostel", "incidents", selectedHostelId],
    queryFn: () =>
      api.rawGet<Incident[]>(
        `/admin/hostel/incidents${selectedHostelId !== "all" ? `?hostel_id=${selectedHostelId}` : ""}`,
      ),
  });

  // Resolve complaint mutation
  const resolveMutation = useMutation({
    mutationFn: ({ id, remarks }: { id: number; remarks: string }) =>
      api.rawPatch(`/admin/hostel/complaints/${id}`, {
        status: "resolved",
        resolution_remarks: remarks,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostel", "complaints"] });
      setResolveTarget(null);
      setResolutionRemarks("");
    },
  });

  // Create complaint mutation
  const createComplaintMutation = useMutation({
    mutationFn: (payload: any) => api.rawPost("/admin/hostel/complaints", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostel", "complaints"] });
      setNewComplaintModal(false);
      setComplaintForm({ hostel_id: "", category: "maintenance", title: "", description: "" });
    },
  });

  // Create incident mutation
  const createIncidentMutation = useMutation({
    mutationFn: (payload: any) => api.rawPost("/admin/hostel/incidents", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostel", "incidents"] });
      setNewIncidentModal(false);
      setIncidentForm({
        hostel_id: "",
        title: "",
        description: "",
        severity: "medium",
        incident_date: new Date().toISOString().split("T")[0],
        action_taken: "",
      });
    },
  });

  const filteredComplaints = complaints.filter((c) => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Complaints & Incidents</h1>
            <Pill status="active">Welfare & Maintenance</Pill>
          </div>
          <p className="text-sm text-ink-soft mt-1">
            Track student grievances, infrastructure maintenance tickets, and disciplinary security logs.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {activeTab === "complaints" ? (
            <button
              onClick={() => setNewComplaintModal(true)}
              className="px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover shadow-sm"
            >
              + Log New Complaint
            </button>
          ) : (
            <button
              onClick={() => setNewIncidentModal(true)}
              className="px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover shadow-sm"
            >
              + Record Incident Log
            </button>
          )}
        </div>
      </div>

      {/* Tabs and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-rule sm:border-0 pb-2 sm:pb-0">
          <button
            onClick={() => setActiveTab("complaints")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === "complaints"
                ? "bg-primary text-white"
                : "bg-surface text-ink-soft border border-rule hover:text-ink"
            }`}
          >
            Complaints & Maintenance ({complaints.length})
          </button>
          <button
            onClick={() => setActiveTab("incidents")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === "incidents"
                ? "bg-primary text-white"
                : "bg-surface text-ink-soft border border-rule hover:text-ink"
            }`}
          >
            Incident Logs ({incidents.length})
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedHostelId}
            onChange={(e) => setSelectedHostelId(e.target.value)}
            className="px-3 py-1.5 text-xs font-medium border border-rule rounded bg-surface text-ink"
          >
            <option value="all">All Accessible Hostels</option>
            {hostels.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.code})
              </option>
            ))}
          </select>

          {activeTab === "complaints" && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 text-xs font-medium border border-rule rounded bg-surface text-ink"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>
          )}
        </div>
      </div>

      {/* Tab Content: Complaints */}
      {activeTab === "complaints" && (
        <Card className="overflow-hidden">
          {loadingComplaints ? (
            <div className="p-8 text-center text-sm text-ink-soft">Loading complaints register...</div>
          ) : filteredComplaints.length === 0 ? (
            <div className="p-8 text-center text-sm text-ink-soft">
              No complaints found for the selected filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-ground border-b border-rule text-xs font-bold uppercase text-ink-soft">
                  <tr>
                    <th className="px-4 py-3">Hostel / Room</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Issue Title & Details</th>
                    <th className="px-4 py-3">Reported By</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rule">
                  {filteredComplaints.map((c) => (
                    <tr key={c.id} className="hover:bg-ground/50 transition">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-ink">{c.hostel_name}</div>
                        <div className="text-xs text-ink-soft">
                          {c.room_number !== "N/A" ? `Room ${c.room_number}` : "Common Area"}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-xs font-medium uppercase bg-surface border border-rule text-ink">
                          {c.category}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-md">
                        <div className="font-medium text-ink">{c.title}</div>
                        <div className="text-xs text-ink-soft line-clamp-2 mt-0.5">{c.description}</div>
                        {c.resolution_remarks && (
                          <div className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-1.5 mt-1.5">
                            <span className="font-bold">Resolution: </span>
                            {c.resolution_remarks}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-xs font-medium text-ink">{c.student_name}</div>
                        <div className="text-[11px] text-ink-soft">
                          {new Date(c.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Pill
                          status={
                            c.status === "resolved"
                              ? "active"
                              : c.status === "pending"
                              ? "warning"
                              : "neutral"
                          }
                        >
                          {c.status.toUpperCase()}
                        </Pill>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {c.status !== "resolved" && canManage && (
                          <button
                            onClick={() => {
                              setResolveTarget(c);
                              setResolutionRemarks("");
                            }}
                            className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm"
                          >
                            Mark Resolved
                          </button>
                        )}
                        {c.status === "resolved" && (
                          <span className="text-xs text-ink-soft italic">Closed</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Tab Content: Incidents */}
      {activeTab === "incidents" && (
        <Card className="overflow-hidden">
          {loadingIncidents ? (
            <div className="p-8 text-center text-sm text-ink-soft">Loading incident logs...</div>
          ) : incidents.length === 0 ? (
            <div className="p-8 text-center text-sm text-ink-soft">
              No incident logs recorded for the selected hostel.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-ground border-b border-rule text-xs font-bold uppercase text-ink-soft">
                  <tr>
                    <th className="px-4 py-3">Hostel</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Incident Summary</th>
                    <th className="px-4 py-3">Involved Resident</th>
                    <th className="px-4 py-3">Action Taken</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rule">
                  {incidents.map((i) => (
                    <tr key={i.id} className="hover:bg-ground/50 transition">
                      <td className="px-4 py-3 font-semibold text-ink">{i.hostel_name}</td>
                      <td className="px-4 py-3 text-xs text-ink-soft">
                        {new Date(i.incident_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                            i.severity === "high"
                              ? "bg-rose-100 text-rose-800 border border-rose-300"
                              : i.severity === "medium"
                              ? "bg-amber-100 text-amber-800 border border-amber-300"
                              : "bg-blue-100 text-blue-800 border border-blue-300"
                          }`}
                        >
                          {i.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-sm">
                        <div className="font-medium text-ink">{i.title}</div>
                        <div className="text-xs text-ink-soft line-clamp-2 mt-0.5">{i.description}</div>
                      </td>
                      <td className="px-4 py-3 text-xs text-ink">{i.student_name}</td>
                      <td className="px-4 py-3 text-xs text-ink-soft">
                        {i.action_taken || "Under Observation"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Resolve Complaint Modal */}
      {resolveTarget && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface border border-rule rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-ink">Resolve Complaint #{resolveTarget.id}</h3>
            <p className="text-xs text-ink-soft">
              Closing ticket: <span className="font-semibold text-ink">{resolveTarget.title}</span>
            </p>

            <div>
              <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                Resolution Remarks / Action Done *
              </label>
              <textarea
                rows={3}
                required
                value={resolutionRemarks}
                onChange={(e) => setResolutionRemarks(e.target.value)}
                placeholder="e.g. Electrician repaired switchboard and verified safety."
                className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setResolveTarget(null)}
                className="px-4 py-2 border border-rule rounded text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!resolutionRemarks.trim() || resolveMutation.isPending}
                onClick={() =>
                  resolveMutation.mutate({ id: resolveTarget.id, remarks: resolutionRemarks })
                }
                className="px-4 py-2 bg-emerald-600 text-white rounded text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50"
              >
                {resolveMutation.isPending ? "Submitting..." : "Confirm Resolution"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Complaint Modal */}
      {newComplaintModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface border border-rule rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-ink">Log Maintenance Ticket / Complaint</h3>

            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Hostel *</label>
                <select
                  required
                  value={complaintForm.hostel_id}
                  onChange={(e) => setComplaintForm({ ...complaintForm, hostel_id: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                >
                  <option value="">Select Hostel</option>
                  {hostels.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name} ({h.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Category *</label>
                <select
                  value={complaintForm.category}
                  onChange={(e) => setComplaintForm({ ...complaintForm, category: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                >
                  <option value="maintenance">Maintenance / Repair</option>
                  <option value="electrical">Electrical</option>
                  <option value="plumbing">Plumbing</option>
                  <option value="cleanliness">Housekeeping & Cleanliness</option>
                  <option value="mess">Mess & Food Service</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Leaking faucet in 2nd floor washroom"
                  value={complaintForm.title}
                  onChange={(e) => setComplaintForm({ ...complaintForm, title: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Detailed Description *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Describe location and exact issue..."
                  value={complaintForm.description}
                  onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setNewComplaintModal(false)}
                className="px-4 py-2 border border-rule rounded text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={
                  !complaintForm.hostel_id ||
                  !complaintForm.title.trim() ||
                  !complaintForm.description.trim() ||
                  createComplaintMutation.isPending
                }
                onClick={() =>
                  createComplaintMutation.mutate({
                    hostel_id: Number(complaintForm.hostel_id),
                    category: complaintForm.category,
                    title: complaintForm.title,
                    description: complaintForm.description,
                  })
                }
                className="px-4 py-2 bg-primary text-white rounded text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {createComplaintMutation.isPending ? "Creating..." : "Submit Complaint"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Incident Modal */}
      {newIncidentModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface border border-rule rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-ink">Record Incident / Disciplinary Log</h3>

            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Hostel *</label>
                <select
                  required
                  value={incidentForm.hostel_id}
                  onChange={(e) => setIncidentForm({ ...incidentForm, hostel_id: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                >
                  <option value="">Select Hostel</option>
                  {hostels.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name} ({h.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                    Severity *
                  </label>
                  <select
                    value={incidentForm.severity}
                    onChange={(e) => setIncidentForm({ ...incidentForm, severity: e.target.value })}
                    className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                    Incident Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={incidentForm.incident_date}
                    onChange={(e) =>
                      setIncidentForm({ ...incidentForm, incident_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unauthorized entry after 9:30 PM"
                  value={incidentForm.title}
                  onChange={(e) => setIncidentForm({ ...incidentForm, title: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Incident Description *
                </label>
                <textarea
                  rows={2}
                  required
                  placeholder="Facts, witness details, sequence of events..."
                  value={incidentForm.description}
                  onChange={(e) => setIncidentForm({ ...incidentForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Action Taken / Remarks
                </label>
                <input
                  type="text"
                  placeholder="e.g. Verbal warning given; parents informed."
                  value={incidentForm.action_taken}
                  onChange={(e) => setIncidentForm({ ...incidentForm, action_taken: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setNewIncidentModal(false)}
                className="px-4 py-2 border border-rule rounded text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={
                  !incidentForm.hostel_id ||
                  !incidentForm.title.trim() ||
                  !incidentForm.description.trim() ||
                  createIncidentMutation.isPending
                }
                onClick={() =>
                  createIncidentMutation.mutate({
                    hostel_id: Number(incidentForm.hostel_id),
                    title: incidentForm.title,
                    description: incidentForm.description,
                    severity: incidentForm.severity,
                    incident_date: incidentForm.incident_date,
                    action_taken: incidentForm.action_taken || null,
                  })
                }
                className="px-4 py-2 bg-primary text-white rounded text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {createIncidentMutation.isPending ? "Recording..." : "Record Incident"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
