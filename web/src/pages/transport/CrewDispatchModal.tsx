import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type CrewMember = {
  id: number;
  employee_code: string;
  name: string;
  phone: string;
  designation: string;
  department: string;
  has_driving_licence: boolean;
  has_police_verification: boolean;
  papers: {
    code: string;
    name: string;
    expires_on: string | null;
    days_left: number | null;
    is_expired: boolean;
  }[];
};

type VehicleOption = {
  id: number;
  registration_no: string;
  make_model: string | null;
  capacity: number;
  status: string;
};

export function CrewDispatchModal({
  route,
  onClose,
  onSaved,
}: {
  route: {
    id: number;
    code: string;
    name: string;
    vehicle_id?: number | null;
    driver_id?: number | null;
    attendant_id?: number | null;
  };
  onClose: () => void;
  onSaved: () => void;
}) {
  const [vehicleId, setVehicleId] = useState<string>(
    route.vehicle_id ? String(route.vehicle_id) : "",
  );
  const [driverId, setDriverId] = useState<string>(
    route.driver_id ? String(route.driver_id) : "",
  );
  const [attendantId, setAttendantId] = useState<string>(
    route.attendant_id ? String(route.attendant_id) : "",
  );

  const crewQuery = useQuery({
    queryKey: ["transport-crew"],
    queryFn: () => api.get("/admin/transport/crew") as Promise<CrewMember[]>,
  });

  const vehiclesQuery = useQuery({
    queryKey: ["transport-vehicles"],
    queryFn: () => api.get("/admin/transport/vehicles") as Promise<VehicleOption[]>,
  });

  const roadworthiness = useQuery({
    queryKey: ["transport-roadworthiness", route.id],
    queryFn: () =>
      api.get(
        `/admin/transport/routes/${route.id}/roadworthiness` as "/admin/transport/routes/{route_id}/roadworthiness",
      ) as Promise<{ roadworthy: boolean; gaps: string[] }>,
  });

  const saveCrew = useWrite({
    write: async () => {
      const clearList: string[] = [];
      const payload: Record<string, any> = { clear: clearList };

      if (vehicleId) payload.vehicle_id = parseInt(vehicleId, 10);
      else clearList.push("vehicle_id");

      if (driverId) payload.driver_id = parseInt(driverId, 10);
      else clearList.push("driver_id");

      if (attendantId) payload.attendant_id = parseInt(attendantId, 10);
      else clearList.push("attendant_id");

      return api.patch(
        `/admin/transport/routes/${route.id}/crew` as "/admin/transport/routes/{route_id}/crew",
        payload,
      );
    },
    invalidates: [["transport-routes"], ["transport-roadworthiness", route.id]],
    onDone: () => {
      onSaved();
      onClose();
    },
  });

  const crewList = crewQuery.data ?? [];
  const activeVehicles = (vehiclesQuery.data ?? []).filter((v) => v.status !== "grounded");

  const selectedDriver = crewList.find((c) => String(c.id) === driverId);
  const selectedAttendant = crewList.find((c) => String(c.id) === attendantId);

  return (
    <Modal title={`Crew & Vehicle Dispatch — ${route.code} (${route.name})`} onClose={onClose} wide>
      {roadworthiness.data && !roadworthiness.data.roadworthy && (
        <div className="mb-4 rounded-card bg-danger/10 border border-danger/30 p-3 text-xs text-danger">
          <p className="font-semibold mb-1">Compliance & Roadworthiness Gaps:</p>
          <ul className="list-disc list-inside space-y-0.5">
            {roadworthiness.data.gaps.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveCrew.run();
        }}
        className="space-y-4"
      >
        <FormField label="Assigned Vehicle (Bus)">
          <select
            className={inputClass}
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
          >
            <option value="">-- No vehicle assigned --</option>
            {activeVehicles.map((v) => (
              <option key={v.id} value={v.id}>
                {v.registration_no} {v.make_model ? `(${v.make_model})` : ""} — {v.capacity} seats ({v.status})
              </option>
            ))}
          </select>
        </FormField>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <FormField label="Designated Driver">
              <select
                className={inputClass}
                value={driverId}
                onChange={(e) => setDriverId(e.target.value)}
              >
                <option value="">-- No driver assigned --</option>
                {crewList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.employee_code}) - {c.designation}
                  </option>
                ))}
              </select>
            </FormField>

            {selectedDriver && (
              <div className="mt-2 text-xs p-2.5 rounded bg-ground border border-rule space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-ink-soft">Driving Licence:</span>
                  {selectedDriver.has_driving_licence ? (
                    <Pill status="active">Verified</Pill>
                  ) : (
                    <Pill status="danger">Missing</Pill>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-ink-soft">Police Verification:</span>
                  {selectedDriver.has_police_verification ? (
                    <Pill status="active">Verified</Pill>
                  ) : (
                    <Pill status="danger">Missing</Pill>
                  )}
                </div>
                <div className="text-[11px] text-ink-faint pt-1">
                  Contact: {selectedDriver.phone || "N/A"}
                </div>
              </div>
            )}
          </div>

          <div>
            <FormField label="Bus Attendant / Conductor">
              <select
                className={inputClass}
                value={attendantId}
                onChange={(e) => setAttendantId(e.target.value)}
              >
                <option value="">-- No attendant assigned --</option>
                {crewList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.employee_code}) - {c.designation}
                  </option>
                ))}
              </select>
            </FormField>

            {selectedAttendant && (
              <div className="mt-2 text-xs p-2.5 rounded bg-ground border border-rule space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-ink-soft">Police Verification:</span>
                  {selectedAttendant.has_police_verification ? (
                    <Pill status="active">Verified</Pill>
                  ) : (
                    <Pill status="danger">Missing</Pill>
                  )}
                </div>
                <div className="text-[11px] text-ink-faint pt-1">
                  Contact: {selectedAttendant.phone || "N/A"}
                </div>
              </div>
            )}
          </div>
        </div>

        <FormError error={saveCrew.error} />

        <div className="flex justify-end gap-2 pt-3 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saveCrew.busy}
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:opacity-90 disabled:opacity-60"
          >
            {saveCrew.busy ? "Updating Crew..." : "Save Crew Dispatch"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
