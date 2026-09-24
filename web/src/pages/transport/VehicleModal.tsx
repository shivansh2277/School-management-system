import { useState } from "react";
import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { FormError, FormField, Modal, inputClass } from "../../components/ui";

export type VehicleData = {
  id: number;
  registration_no: string;
  make_model: string | null;
  capacity: number;
  ownership: "owned" | "hired" | string;
  status: string;
  gps_device_id?: string | null;
};

export function VehicleModal({
  vehicle,
  onClose,
  onSaved,
}: {
  vehicle: VehicleData | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = vehicle !== null;
  const [form, setForm] = useState({
    registration_no: vehicle?.registration_no ?? "",
    make_model: vehicle?.make_model ?? "",
    capacity: vehicle?.capacity ? String(vehicle.capacity) : "32",
    ownership: (vehicle?.ownership === "hired" ? "hired" : "owned") as "owned" | "hired",
    status: vehicle?.status ?? "active",
    gps_device_id: vehicle?.gps_device_id ?? "",
  });

  const saveVehicle = useWrite({
    write: async () => {
      const capacityNum = parseInt(form.capacity, 10) || 1;
      const makeModel = form.make_model.trim() || null;
      const gpsDevice = form.gps_device_id.trim() || null;

      if (isEdit) {
        return api.put(
          `/admin/transport/vehicles/${vehicle.id}` as "/admin/transport/vehicles/{vehicle_id}",
          {
            make_model: makeModel,
            capacity: capacityNum,
            ownership: form.ownership,
            gps_device_id: gpsDevice,
          },
        );
      } else {
        return api.post("/admin/transport/vehicles", {
          registration_no: form.registration_no.trim().toUpperCase(),
          make_model: makeModel,
          capacity: capacityNum,
          ownership: form.ownership,
          gps_device_id: gpsDevice,
        });
      }
    },
    invalidates: [["transport-vehicles"], ["transport-routes"]],
    onDone: () => {
      onSaved();
      onClose();
    },
  });

  return (
    <Modal title={isEdit ? `Edit Vehicle (${vehicle.registration_no})` : "Add New Vehicle to Fleet"} onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveVehicle.run();
        }}
        className="space-y-4"
      >
        <FormField label="Registration Number" error={saveVehicle.fields.registration_no}>
          <input
            className={`${inputClass} font-mono uppercase`}
            placeholder="e.g. UP32AB1234"
            disabled={isEdit}
            value={form.registration_no}
            onChange={(e) => setForm({ ...form, registration_no: e.target.value })}
            required
          />
        </FormField>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <FormField label="Make / Model" error={saveVehicle.fields.make_model}>
            <input
              className={inputClass}
              placeholder="e.g. Tata Starbus 40"
              value={form.make_model}
              onChange={(e) => setForm({ ...form, make_model: e.target.value })}
            />
          </FormField>

          <FormField label="Seating Capacity" error={saveVehicle.fields.capacity}>
            <input
              className={inputClass}
              type="number"
              min="1"
              max="120"
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: e.target.value })}
              required
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <FormField label="Ownership" error={saveVehicle.fields.ownership}>
            <select
              className={inputClass}
              value={form.ownership}
              onChange={(e) => setForm({ ...form, ownership: e.target.value as "owned" | "hired" })}
            >
              <option value="owned">School Owned</option>
              <option value="hired">Hired / Leased Vendor</option>
            </select>
          </FormField>

          <FormField label="Fleet Status" error={saveVehicle.fields.status}>
            <select
              className={inputClass}
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              <option value="active">Active (Roadworthy)</option>
              <option value="maintenance">Under Maintenance</option>
              <option value="grounded">Grounded (Compliance / Safety)</option>
            </select>
          </FormField>
        </div>

        <FormField label="GPS Tracker Device ID (Optional)" error={saveVehicle.fields.gps_device_id}>
          <input
            className={`${inputClass} font-mono`}
            placeholder="e.g. GPS-UP32-001"
            value={form.gps_device_id}
            onChange={(e) => setForm({ ...form, gps_device_id: e.target.value })}
          />
        </FormField>

        <FormError error={saveVehicle.error} />

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saveVehicle.busy}
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:opacity-90 disabled:opacity-60"
          >
            {saveVehicle.busy ? "Saving..." : isEdit ? "Update Vehicle" : "Create Vehicle"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
