import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type FeeSlab = {
  id: number;
  name: string;
  monthly_amount: number;
};

export type StopDraft = {
  id?: number;
  sequence: number;
  name: string;
  address: string;
  landmark: string;
  pickup_time: string;
  drop_time: string;
  fee_slab_id: number | null;
  latitude: number | null;
  longitude: number | null;
  is_geocoded?: boolean;
};

export type RouteEditData = {
  id: number;
  code: string;
  name: string;
  distance_km: number | null;
  stops: {
    id: number;
    sequence: number;
    name: string;
    address?: string | null;
    landmark?: string | null;
    pickup_time?: string | null;
    drop_time?: string | null;
    fee_slab_id?: number | null;
    latitude: number | null;
    longitude: number | null;
  }[];
};

export function RouteBuilderModal({
  route,
  onClose,
  onSaved,
}: {
  route: RouteEditData | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = route !== null;
  const [code, setCode] = useState(route?.code ?? "");
  const [name, setName] = useState(route?.name ?? "");
  const [distanceKm, setDistanceKm] = useState(
    route?.distance_km !== null && route?.distance_km !== undefined ? String(route.distance_km) : "",
  );

  const [stops, setStops] = useState<StopDraft[]>(() => {
    if (route && route.stops.length > 0) {
      return route.stops
        .slice()
        .sort((a, b) => a.sequence - b.sequence)
        .map((s) => ({
          id: s.id,
          sequence: s.sequence,
          name: s.name,
          address: s.address ?? "",
          landmark: s.landmark ?? "",
          pickup_time: s.pickup_time ? s.pickup_time.slice(0, 5) : "07:00",
          drop_time: s.drop_time ? s.drop_time.slice(0, 5) : "14:30",
          fee_slab_id: s.fee_slab_id ?? null,
          latitude: s.latitude,
          longitude: s.longitude,
          is_geocoded: s.latitude !== null && s.longitude !== null,
        }));
    }
    return [
      {
        sequence: 1,
        name: "First Stop",
        address: "Vibhuti Khand, Gomti Nagar, Lucknow",
        landmark: "Near Mall",
        pickup_time: "06:45",
        drop_time: "14:30",
        fee_slab_id: null,
        latitude: null,
        longitude: null,
        is_geocoded: false,
      },
    ];
  });

  const slabsQuery = useQuery({
    queryKey: ["transport-slabs"],
    queryFn: () => api.get("/admin/transport/slabs") as Promise<FeeSlab[]>,
  });

  const slabs = slabsQuery.data ?? [];

  const geocodeStop = async (index: number) => {
    const s = stops[index];
    const query = s.address.trim() || s.name.trim();
    if (!query) return;

    try {
      const res = (await api.get(
        `/admin/transport/geocode?address=${encodeURIComponent(query)}` as "/admin/transport/geocode",
      )) as { latitude: number; longitude: number; is_approximate: boolean };

      const updated = [...stops];
      updated[index] = {
        ...updated[index],
        latitude: res.latitude,
        longitude: res.longitude,
        is_geocoded: true,
      };
      setStops(updated);
    } catch {
      // Ignored; server will attempt geocoding upon save
    }
  };

  const handleAddStop = () => {
    const lastStop = stops[stops.length - 1];
    let nextPickup = "07:00";
    let nextDrop = "14:45";

    if (lastStop && lastStop.pickup_time) {
      const [h, m] = lastStop.pickup_time.split(":").map(Number);
      const totalM = h * 60 + m + 15;
      const nh = Math.min(23, Math.floor(totalM / 60));
      const nm = totalM % 60;
      nextPickup = `${String(nh).padStart(2, "0")}:${String(nm).padStart(2, "0")}`;
    }
    if (lastStop && lastStop.drop_time) {
      const [h, m] = lastStop.drop_time.split(":").map(Number);
      const totalM = h * 60 + m + 15;
      const nh = Math.min(23, Math.floor(totalM / 60));
      const nm = totalM % 60;
      nextDrop = `${String(nh).padStart(2, "0")}:${String(nm).padStart(2, "0")}`;
    }

    setStops([
      ...stops,
      {
        sequence: stops.length + 1,
        name: `Stop ${stops.length + 1}`,
        address: "",
        landmark: "",
        pickup_time: nextPickup,
        drop_time: nextDrop,
        fee_slab_id: slabs[0]?.id ?? null,
        latitude: null,
        longitude: null,
        is_geocoded: false,
      },
    ]);
  };

  const handleRemoveStop = (index: number) => {
    if (stops.length <= 1) return;
    const filtered = stops.filter((_, i) => i !== index);
    const resequenced = filtered.map((s, i) => ({ ...s, sequence: i + 1 }));
    setStops(resequenced);
  };

  const handleMoveStop = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= stops.length) return;
    const reordered = [...stops];
    const temp = reordered[index];
    reordered[index] = reordered[target];
    reordered[target] = temp;
    const resequenced = reordered.map((s, i) => ({ ...s, sequence: i + 1 }));
    setStops(resequenced);
  };

  const saveRoute = useWrite({
    write: async () => {
      const dist = distanceKm.trim() ? parseFloat(distanceKm) : null;
      let routeId = route?.id;

      if (isEdit) {
        await api.put(
          `/admin/transport/routes/${route.id}` as "/admin/transport/routes/{route_id}",
          { code: code.trim(), name: name.trim(), distance_km: dist },
        );
      } else {
        const created = (await api.post("/admin/transport/routes", {
          code: code.trim(),
          name: name.trim(),
          distance_km: dist,
        })) as { id: number };
        routeId = created.id;
      }

      // Save stops
      if (routeId) {
        const stopsPayload = stops.map((s, i) => ({
          sequence: i + 1,
          name: s.name.trim(),
          address: s.address.trim() || null,
          landmark: s.landmark.trim() || null,
          pickup_time: s.pickup_time,
          drop_time: s.drop_time || null,
          fee_slab_id: s.fee_slab_id || null,
          latitude: s.latitude,
          longitude: s.longitude,
        }));

        await api.put(
          `/admin/transport/routes/${routeId}/stops` as "/admin/transport/routes/{route_id}/stops",
          stopsPayload,
        );
      }
    },
    invalidates: [["transport-routes"]],
    onDone: () => {
      onSaved();
      onClose();
    },
  });

  return (
    <Modal
      title={isEdit ? `Route & Stop Builder — ${route.code}` : "Create New Bus Route"}
      onClose={onClose}
      wide
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          saveRoute.run();
        }}
        className="space-y-6"
      >
        {/* Route Details */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-ground rounded-card border border-rule">
          <FormField label="Route Code" error={saveRoute.fields.code}>
            <input
              className={`${inputClass} font-mono uppercase`}
              placeholder="e.g. R1 or EXP-3"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Route Name" error={saveRoute.fields.name}>
            <input
              className={inputClass}
              placeholder="e.g. Gomti Nagar Express"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Total Distance (km)" error={saveRoute.fields.distance_km}>
            <input
              className={inputClass}
              type="number"
              step="0.1"
              min="0"
              placeholder="e.g. 14.5"
              value={distanceKm}
              onChange={(e) => setDistanceKm(e.target.value)}
            />
          </FormField>
        </div>

        {/* Stops Builder */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-sm text-ink">Route Stops & Timings</h3>
              <p className="text-xs text-ink-soft">
                Address-First: Type stop name or address and click "Resolve" — coordinates are geocoded automatically for GPS & maps.
              </p>
            </div>
            <button
              type="button"
              onClick={handleAddStop}
              className="rounded-input bg-primary px-3 py-1.5 text-white text-xs font-medium hover:opacity-90 flex items-center gap-1"
            >
              + Add Stop
            </button>
          </div>

          <div className="space-y-3">
            {stops.map((stop, idx) => (
              <div
                key={idx}
                className="p-3.5 border border-rule rounded-card bg-surface space-y-3 hover:border-primary/50 transition-colors"
              >
                <div className="flex items-center justify-between border-b border-rule pb-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-primary text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                      {stop.sequence}
                    </span>
                    <span className="font-semibold text-sm">Stop #{stop.sequence}</span>
                    {stop.is_geocoded ? (
                      <Pill status="active">
                        📍 {stop.latitude?.toFixed(4)}, {stop.longitude?.toFixed(4)}
                      </Pill>
                    ) : (
                      <Pill status="pending">Coordinates auto-geocoded on save</Pill>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      disabled={idx === 0}
                      onClick={() => handleMoveStop(idx, -1)}
                      className="p-1 rounded hover:bg-ground disabled:opacity-30 text-ink-soft text-xs"
                      title="Move up"
                    >
                      ▲
                    </button>
                    <button
                      type="button"
                      disabled={idx === stops.length - 1}
                      onClick={() => handleMoveStop(idx, 1)}
                      className="p-1 rounded hover:bg-ground disabled:opacity-30 text-ink-soft text-xs"
                      title="Move down"
                    >
                      ▼
                    </button>
                    {stops.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveStop(idx)}
                        className="text-danger hover:bg-danger/10 px-2 py-1 rounded text-xs ml-2 font-medium"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  <FormField label="Stop Name">
                    <input
                      className={inputClass}
                      placeholder="e.g. Vibhuti Khand"
                      value={stop.name}
                      onChange={(e) => {
                        const updated = [...stops];
                        updated[idx].name = e.target.value;
                        setStops(updated);
                      }}
                      required
                    />
                  </FormField>

                  <div className="md:col-span-2">
                    <FormField label="Physical Address / Location">
                      <div className="flex gap-2">
                        <input
                          className={inputClass}
                          placeholder="e.g. Vibhuti Khand, Gomti Nagar, Lucknow"
                          value={stop.address}
                          onChange={(e) => {
                            const updated = [...stops];
                            updated[idx].address = e.target.value;
                            setStops(updated);
                          }}
                        />
                        <button
                          type="button"
                          onClick={() => geocodeStop(idx)}
                          title="Auto-resolve coordinates via geocoding"
                          className="shrink-0 px-3 py-1.5 rounded-input border border-primary text-primary text-xs font-medium hover:bg-primary/5"
                        >
                          Resolve 📍
                        </button>
                      </div>
                    </FormField>
                  </div>

                  <FormField label="Landmark">
                    <input
                      className={inputClass}
                      placeholder="e.g. Opp. Fun Republic Mall"
                      value={stop.landmark}
                      onChange={(e) => {
                        const updated = [...stops];
                        updated[idx].landmark = e.target.value;
                        setStops(updated);
                      }}
                    />
                  </FormField>

                  <div className="grid grid-cols-2 gap-2">
                    <FormField label="Pickup Time">
                      <input
                        className={inputClass}
                        type="time"
                        value={stop.pickup_time}
                        onChange={(e) => {
                          const updated = [...stops];
                          updated[idx].pickup_time = e.target.value;
                          setStops(updated);
                        }}
                        required
                      />
                    </FormField>

                    <FormField label="Drop Time">
                      <input
                        className={inputClass}
                        type="time"
                        value={stop.drop_time}
                        onChange={(e) => {
                          const updated = [...stops];
                          updated[idx].drop_time = e.target.value;
                          setStops(updated);
                        }}
                        required
                      />
                    </FormField>
                  </div>

                  <FormField label="Distance Fee Slab">
                    <select
                      className={inputClass}
                      value={stop.fee_slab_id ? String(stop.fee_slab_id) : ""}
                      onChange={(e) => {
                        const updated = [...stops];
                        updated[idx].fee_slab_id = e.target.value ? parseInt(e.target.value, 10) : null;
                        setStops(updated);
                      }}
                    >
                      <option value="">-- Default / None --</option>
                      {slabs.map((slab) => (
                        <option key={slab.id} value={slab.id}>
                          {slab.name} (₹{slab.monthly_amount}/mo)
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>
              </div>
            ))}
          </div>
        </div>

        <FormError error={saveRoute.error} />

        <div className="flex justify-end gap-2 pt-4 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saveRoute.busy || !code.trim() || !name.trim()}
            className="rounded-input bg-primary px-5 py-2 text-white text-sm font-medium hover:opacity-90 disabled:opacity-60"
          >
            {saveRoute.busy ? "Saving Route..." : isEdit ? "Save Changes" : "Create Route"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
