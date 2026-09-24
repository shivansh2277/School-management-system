import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import {
  ConfirmDialog,
  DataTable,
  Empty,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../../components/ui";

type AwaitingStudent = {
  enrolment_id: number;
  student_id: number;
  name: string;
  admission_no: string;
  application_no: string;
  class_label: string;
  address: string;
  phone: string;
  latitude: number | null;
  longitude: number | null;
  is_approximate: boolean;
};

type SearchedStudent = {
  student_id: number;
  enrolment_id: number;
  name: string;
  admission_no: string;
  class_label: string;
  address: string;
  phone: string;
  latitude: number | null;
  longitude: number | null;
  is_approximate: boolean;
  current_assignment: {
    assignment_id: number;
    route_id: number;
    route_code: string;
    route_name: string;
    stop_id: number;
    stop_name: string;
    direction: string;
    status: string;
    start_date: string;
  } | null;
};

type NearbyStop = {
  stop_id: number;
  sequence: number;
  name: string;
  address: string | null;
  landmark: string | null;
  pickup_time: string | null;
  drop_time: string | null;
  route_id: number;
  route_code: string;
  route_name: string;
  vehicle_registration: string | null;
  vehicle_capacity: number | null;
  seats_taken: number;
  seats_free: number | null;
  has_capacity: boolean;
  fee_slab_name: string | null;
  monthly_amount: number | null;
  latitude: number | null;
  longitude: number | null;
  distance_km: number | null;
};

type ActiveRider = {
  assignment_id: number;
  student_id: number;
  name: string;
  admission_no: string;
  class_label: string;
  route_code: string;
  route_name: string;
  route_id: number;
  stop: string;
  stop_id: number;
  sequence: number;
  direction: string;
  status: string;
};

export function StudentAllocationDesk({ onClose }: { onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<"queue" | "search" | "riders">("queue");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<SearchedStudent | AwaitingStudent | null>(null);

  // Transfer & End Service state
  const [transferringRider, setTransferringRider] = useState<ActiveRider | null>(null);
  const [transferStopId, setTransferStopId] = useState<string>("");
  const [transferReason, setTransferReason] = useState<string>("");
  const [endingRider, setEndingRider] = useState<ActiveRider | null>(null);

  // Queries
  const queueQuery = useQuery({
    queryKey: ["transport-requests"],
    queryFn: () => api.get("/admin/transport/requests") as Promise<AwaitingStudent[]>,
  });

  const searchStudentsQuery = useQuery({
    queryKey: ["transport-student-search", searchQuery],
    queryFn: () =>
      api.get(
        `/admin/transport/students/search?q=${encodeURIComponent(searchQuery)}` as "/admin/transport/students/search",
      ) as Promise<SearchedStudent[]>,
    enabled: activeTab === "search",
  });

  // Nearby stops query for selected student
  const nearbyStopsQuery = useQuery({
    queryKey: ["transport-nearby-stops", selectedStudent?.student_id, selectedStudent?.address],
    queryFn: () => {
      if (!selectedStudent) return [] as NearbyStop[];
      const params = new URLSearchParams();
      if (selectedStudent.latitude !== null && selectedStudent.longitude !== null) {
        params.set("lat", String(selectedStudent.latitude));
        params.set("lon", String(selectedStudent.longitude));
      } else if (selectedStudent.address) {
        params.set("address", selectedStudent.address);
      }
      return api.get(
        `/admin/transport/stops/nearby?${params.toString()}` as "/admin/transport/stops/nearby",
      ) as Promise<NearbyStop[]>;
    },
    enabled: selectedStudent !== null,
  });

  // All active routes query for transfer stop dropdown
  const allStopsQuery = useQuery({
    queryKey: ["transport-all-stops"],
    queryFn: () =>
      api.get("/admin/transport/stops/nearby" as "/admin/transport/stops/nearby") as Promise<NearbyStop[]>,
    enabled: transferringRider !== null,
  });

  // All active riders query
  const allRoutesQuery = useQuery({
    queryKey: ["transport-routes"],
    queryFn: () => api.get("/admin/transport/routes") as Promise<any[]>,
    enabled: activeTab === "riders",
  });

  // Fetch riders across all routes
  const ridersQuery = useQuery({
    queryKey: ["transport-all-riders", allRoutesQuery.data],
    enabled: activeTab === "riders" && !!allRoutesQuery.data,
    queryFn: async () => {
      const routes = allRoutesQuery.data ?? [];
      const list: ActiveRider[] = [];
      for (const r of routes) {
        const riders = (await api.get(
          `/admin/transport/routes/${r.id}/students` as "/admin/transport/routes/{route_id}/students",
        )) as any[];
        for (const item of riders) {
          list.push({
            assignment_id: item.assignment_id,
            student_id: item.student_id,
            name: item.name,
            admission_no: item.admission_no,
            class_label: item.class_label,
            route_code: r.code,
            route_name: r.name,
            route_id: r.id,
            stop: item.stop,
            stop_id: item.route_stop_id || 0,
            sequence: item.sequence,
            direction: item.direction,
            status: item.status,
          });
        }
      }
      return list;
    },
  });

  // Actions
  const assignStop = useWrite<{ student_id: number; route_stop_id: number }>({
    write: async ({ student_id, route_stop_id }) => {
      const today = new Date().toISOString().slice(0, 10);
      const res = (await api.post("/admin/transport/assignments", {
        student_id,
        route_stop_id,
        direction: "both",
        start_date: today,
      })) as { id: number };

      // Activate assignment immediately
      if (res && res.id) {
        try {
          await api.patch(
            `/admin/transport/assignments/${res.id}` as "/admin/transport/assignments/{assignment_id}",
            { status: "active" },
          );
        } catch {
          // If route status prevents activation, assignment stays requested
        }
      }
    },
    invalidates: [
      ["transport-requests"],
      ["transport-routes"],
      ["transport-student-search"],
      ["transport-all-riders"],
    ],
    onDone: () => setSelectedStudent(null),
  });

  const transfer = useWrite({
    write: async () => {
      const today = new Date().toISOString().slice(0, 10);
      return api.post(
        `/admin/transport/assignments/${transferringRider!.assignment_id}/transfer` as "/admin/transport/assignments/{assignment_id}/transfer",
        {
          new_route_stop_id: parseInt(transferStopId, 10),
          reason: transferReason.trim(),
          start_date: today,
          direction: "both",
        },
      );
    },
    invalidates: [
      ["transport-routes"],
      ["transport-all-riders"],
      ["transport-student-search"],
    ],
    onDone: () => {
      setTransferringRider(null);
      setTransferStopId("");
      setTransferReason("");
    },
  });

  const endAssignment = useWrite<string>({
    write: async (reason: string) => {
      return api.del(
        `/admin/transport/assignments/${endingRider!.assignment_id}` as "/admin/transport/assignments/{assignment_id}",
        `?reason=${encodeURIComponent(reason)}`,
      );
    },
    invalidates: [
      ["transport-routes"],
      ["transport-all-riders"],
      ["transport-student-search"],
      ["transport-requests"],
    ],
    onDone: () => setEndingRider(null),
  });

  const queue = queueQuery.data ?? [];
  const searchResults = searchStudentsQuery.data ?? [];
  const nearbyStops = nearbyStopsQuery.data ?? [];
  const activeRiders = ridersQuery.data ?? [];

  return (
    <Modal title="Student Transport Allocation & Dispatch Desk" onClose={onClose} wide>
      {/* Navigation tabs */}
      <div className="flex border-b border-rule mb-4 space-x-2 text-sm font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("queue")}
          className={`pb-2 px-3 border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "queue"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          <span>Admission Queue</span>
          {queue.length > 0 && (
            <span className="bg-primary text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">
              {queue.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("search")}
          className={`pb-2 px-3 border-b-2 transition-colors ${
            activeTab === "search"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Student Search & Allocation
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("riders")}
          className={`pb-2 px-3 border-b-2 transition-colors ${
            activeTab === "riders"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Active Riders & Transfers
        </button>
      </div>

      {/* Sub-tab 1: Admission Transport Queue */}
      {activeTab === "queue" && (
        <div className="space-y-4">
          <p className="text-xs text-ink-soft">
            Enrolled applicants who opted for school transport during admission. Assign them directly to the most convenient stop.
          </p>
          <DataTable<AwaitingStudent>
            rows={queue}
            loading={queueQuery.isLoading}
            error={queueQuery.error}
            empty="No unassigned students in the admission transport queue."
            columns={[
              { key: "adm", header: "Adm No.", render: (s) => s.admission_no },
              { key: "name", header: "Student Name", render: (s) => s.name },
              { key: "class", header: "Class", render: (s) => s.class_label },
              { key: "phone", header: "Contact", render: (s) => s.phone || "-" },
              {
                key: "addr",
                header: "Address",
                render: (s) => (
                  <div className="max-w-xs truncate" title={s.address}>
                    {s.address || <span className="text-ink-faint italic">No address on file</span>}
                  </div>
                ),
              },
              {
                key: "act",
                header: "",
                render: (s) => (
                  <button
                    type="button"
                    onClick={() => setSelectedStudent(s)}
                    className="rounded-input bg-primary px-3 py-1 text-white text-xs font-medium hover:opacity-90 shadow-sm"
                  >
                    Assign Stop
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* Sub-tab 2: Enrolled Student Search & Allocation */}
      {activeTab === "search" && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              className={inputClass}
              placeholder="Search student by name or admission number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>

          <DataTable<SearchedStudent>
            rows={searchResults}
            loading={searchStudentsQuery.isLoading}
            error={searchStudentsQuery.error}
            empty={
              searchQuery.trim()
                ? "No matching enrolled students found."
                : "Type a student name or admission number above to search."
            }
            columns={[
              { key: "adm", header: "Adm No.", render: (s) => s.admission_no },
              { key: "name", header: "Student Name", render: (s) => s.name },
              { key: "class", header: "Class", render: (s) => s.class_label },
              { key: "address", header: "Home Address", render: (s) => s.address || "-" },
              {
                key: "current",
                header: "Transport Status",
                render: (s) =>
                  s.current_assignment ? (
                    <Pill status="active">
                      {s.current_assignment.route_code}: {s.current_assignment.stop_name}
                    </Pill>
                  ) : (
                    <Pill status="pending">Not Assigned</Pill>
                  ),
              },
              {
                key: "act",
                header: "",
                render: (s) => (
                  <button
                    type="button"
                    onClick={() => setSelectedStudent(s)}
                    className="rounded-input border border-primary text-primary px-3 py-1 text-xs font-medium hover:bg-primary/5"
                  >
                    {s.current_assignment ? "Change Stop" : "Allocate Stop"}
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* Sub-tab 3: Active Riders & Transfers */}
      {activeTab === "riders" && (
        <div className="space-y-4">
          <p className="text-xs text-ink-soft">
            Currently active transport assignments. Manage route/stop transfers or end transport service with mandatory reason tracking.
          </p>
          <DataTable<ActiveRider>
            rows={activeRiders}
            loading={ridersQuery.isLoading}
            error={ridersQuery.error}
            empty="No active transport riders on record."
            columns={[
              { key: "adm", header: "Adm No.", render: (r) => r.admission_no },
              { key: "name", header: "Student Name", render: (r) => r.name },
              { key: "class", header: "Class", render: (r) => r.class_label },
              {
                key: "route",
                header: "Route",
                render: (r) => (
                  <span>
                    <strong>{r.route_code}</strong> ({r.route_name})
                  </span>
                ),
              },
              { key: "stop", header: "Stop", render: (r) => r.stop },
              { key: "dir", header: "Direction", render: (r) => <span className="capitalize">{r.direction}</span> },
              {
                key: "act",
                header: "",
                render: (r) => (
                  <div className="flex gap-1.5 justify-end">
                    <button
                      type="button"
                      onClick={() => setTransferringRider(r)}
                      className="rounded-input border border-rule px-2.5 py-1 text-xs hover:bg-canvas font-medium"
                    >
                      Transfer Stop
                    </button>
                    <button
                      type="button"
                      onClick={() => setEndingRider(r)}
                      className="rounded-input border border-danger/40 text-danger px-2.5 py-1 text-xs hover:bg-danger/10 font-medium"
                    >
                      End Service
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* Modal: Allocate Nearby Stop to Selected Student */}
      {selectedStudent && (
        <Modal
          title={`Allocate Transport Stop — ${selectedStudent.name} (${selectedStudent.admission_no})`}
          onClose={() => setSelectedStudent(null)}
          wide
        >
          <div className="space-y-4">
            <div className="p-3 bg-ground rounded-card border border-rule text-xs space-y-1">
              <div>
                <span className="text-ink-soft">Student:</span> <strong>{selectedStudent.name}</strong> ({selectedStudent.class_label})
              </div>
              <div>
                <span className="text-ink-soft">Home Address:</span>{" "}
                {selectedStudent.address ? (
                  <strong>{selectedStudent.address}</strong>
                ) : (
                  <span className="text-ink-faint italic">No physical address specified</span>
                )}
              </div>
              {selectedStudent.latitude !== null && (
                <div className="text-ink-faint">
                  📍 Coordinates: {selectedStudent.latitude?.toFixed(4)}, {selectedStudent.longitude?.toFixed(4)}
                </div>
              )}
            </div>

            <h4 className="text-sm font-semibold text-ink">
              Available Route Stops (Ranked by Proximity)
            </h4>

            <FormError error={assignStop.error} />

            <div className="max-h-72 overflow-y-auto border border-rule rounded-card divide-y divide-rule">
              {nearbyStopsQuery.isLoading ? (
                <p className="text-xs text-ink-faint p-4 text-center">Calculating nearby stops and distance...</p>
              ) : nearbyStops.length === 0 ? (
                <p className="text-xs text-ink-faint p-4 text-center">No active route stops found in the school fleet.</p>
              ) : (
                nearbyStops.map((stop) => (
                  <div
                    key={stop.stop_id}
                    className="p-3 flex items-center justify-between hover:bg-ground/60 transition-colors gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{stop.name}</span>
                        <span className="text-xs text-ink-soft font-mono bg-ground px-1.5 py-0.5 rounded border border-rule">
                          Route {stop.route_code} ({stop.route_name})
                        </span>
                        {stop.distance_km !== null && (
                          <span className="text-xs text-primary font-medium">
                            ~{stop.distance_km.toFixed(1)} km away
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-ink-soft mt-1 flex gap-3">
                        <span>Pick: {stop.pickup_time ? stop.pickup_time.slice(0, 5) : "--:--"}</span>
                        <span>Drop: {stop.drop_time ? stop.drop_time.slice(0, 5) : "--:--"}</span>
                        {stop.fee_slab_name && (
                          <span>
                            Fee: ₹{stop.monthly_amount}/mo ({stop.fee_slab_name})
                          </span>
                        )}
                        <span className={stop.has_capacity ? "text-success font-medium" : "text-danger font-medium"}>
                          {stop.seats_free ?? 0} seats left
                        </span>
                      </div>
                    </div>

                    <button
                      type="button"
                      disabled={assignStop.busy || !stop.has_capacity}
                      onClick={() =>
                        assignStop.run({
                          student_id: selectedStudent.student_id,
                          route_stop_id: stop.stop_id,
                        })
                      }
                      className="rounded-input bg-primary px-3.5 py-1.5 text-white text-xs font-medium hover:opacity-90 disabled:opacity-40 shrink-0"
                    >
                      {assignStop.busy ? "Assigning..." : stop.has_capacity ? "Select & Assign" : "Bus Full"}
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setSelectedStudent(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Transfer Active Rider */}
      {transferringRider && (
        <Modal
          title={`Transfer Stop — ${transferringRider.name} (${transferringRider.admission_no})`}
          onClose={() => setTransferringRider(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              transfer.run();
            }}
            className="space-y-4"
          >
            <div className="p-3 bg-ground rounded border border-rule text-xs space-y-1">
              <div>
                <span className="text-ink-soft">Current Stop:</span> <strong>{transferringRider.stop}</strong> (Route {transferringRider.route_code})
              </div>
            </div>

            <FormField label="Select New Route Stop">
              <select
                className={inputClass}
                value={transferStopId}
                onChange={(e) => setTransferStopId(e.target.value)}
                required
              >
                <option value="">-- Choose destination stop --</option>
                {(allStopsQuery.data ?? []).map((s) => (
                  <option key={s.stop_id} value={s.stop_id} disabled={!s.has_capacity}>
                    Route {s.route_code}: {s.name} ({s.seats_free} seats free)
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Reason for Transfer (Mandatory for Audit)">
              <textarea
                className={inputClass}
                rows={2}
                placeholder="e.g. Family relocated to Gomti Nagar extension"
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                required
                minLength={3}
              />
            </FormField>

            <FormError error={transfer.error} />

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setTransferringRider(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={transfer.busy || !transferStopId || transferReason.trim().length < 3}
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:opacity-90 disabled:opacity-60"
              >
                {transfer.busy ? "Transferring..." : "Confirm Transfer"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Confirm Dialog: End Service */}
      {endingRider && (
        <ConfirmDialog
          title={`End Transport Service — ${endingRider.name}`}
          confirmLabel="End Service"
          busy={endAssignment.busy}
          error={endAssignment.error}
          intent={
            <p>
              Ending transport service for <strong>{endingRider.name}</strong> will remove them from Route {endingRider.route_code} ({endingRider.stop}) and stop future monthly fee billing. A mandatory reason is required.
            </p>
          }
          onConfirm={(reason) => endAssignment.run(reason)}
          onClose={() => setEndingRider(null)}
        />
      )}
    </Modal>
  );
}
