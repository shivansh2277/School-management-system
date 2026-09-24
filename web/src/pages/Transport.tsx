/**
 * Transport — the routes, fleet manager, student allocation desk, and compliance.
 *
 * Implements Transport Upgrade Plan 1 & Plan 2:
 * - Address-First Location System with auto-geocoded coordinates
 * - Fleet Manager (add/edit vehicles, seat capacity guard, ownership, GPS tracker, grounding)
 * - Route Builder (route code, name, distance, stops sequence with address geocoding)
 * - Crew Dispatcher (driver, attendant, compliance indicators for licences and police verification)
 * - Distance Fee Slabs Manager
 * - Student Transport Allocation Desk (Admission queue, search & allocate, proximity stop ranking, transfers, end service)
 * - Printable Route Roster (A4 format with parent emergency contacts and escort photos)
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { useWrite } from "../api/useWrite";
import { ActionButton, Can } from "../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  FormError,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";
import { PrintableRouteRoster } from "./PrintableRouteRoster";
import { RouteMap, type MapStop } from "./RouteMap";
import { CrewDispatchModal } from "./transport/CrewDispatchModal";
import { RouteBuilderModal, type RouteEditData } from "./transport/RouteBuilderModal";
import { SlabsModal } from "./transport/SlabsModal";
import { StudentAllocationDesk } from "./transport/StudentAllocationDesk";
import { VehicleModal, type VehicleData } from "./transport/VehicleModal";

/** api/admin/transport.py::_route_out, plus services/transport.py::seats. */
type Route = {
  id: number;
  code: string;
  name: string;
  status: string;
  distance_km: number | null;
  vehicle_id: number | null;
  driver_id: number | null;
  attendant_id: number | null;
  vehicle: string | null;
  capacity: number | null;
  taken: number;
  free: number | null;
  stops: MapStop[];
};

/** services/transport.py::expiring_papers. */
type Paper = {
  owner_type: string;
  owner: string;
  document: string;
  expires_on: string;
  days_left: number;
};

/** api/admin/transport.py::route_students. */
type Rider = {
  assignment_id: number;
  name: string;
  admission_no: string;
  class_label: string;
  stop: string;
  sequence: number;
  direction: string;
  status: string;
};

const asDate = (iso: string) => new Date(iso).toLocaleDateString("en-GB");
const SETUP_WRITE = "transport.setup.write";

export function Transport() {
  const [openRouteId, setOpenRouteId] = useState<number | null>(null);
  const [mapRouteId, setMapRouteId] = useState<number | null>(null);
  const [rosterRouteId, setRosterRouteId] = useState<number | null>(null);

  // Modals state
  const [editingRoute, setEditingRoute] = useState<RouteEditData | null>(null);
  const [isCreatingRoute, setIsCreatingRoute] = useState(false);
  const [dispatchingRoute, setDispatchingRoute] = useState<Route | null>(null);
  const [editingVehicle, setEditingVehicle] = useState<VehicleData | null>(null);
  const [isCreatingVehicle, setIsCreatingVehicle] = useState(false);
  const [showSlabsModal, setShowSlabsModal] = useState(false);
  const [showAllocationDesk, setShowAllocationDesk] = useState(false);

  // Status & Grounding
  const [routeStatus, setRouteStatus] = useState<{ route: Route; to: "active" | "suspended" } | null>(
    null,
  );
  const [grounding, setGrounding] = useState<VehicleData | null>(null);

  const routes = useQuery({
    queryKey: ["transport-routes"],
    queryFn: () => api.get("/admin/transport/routes") as Promise<Route[]>,
  });
  const vehicles = useQuery({
    queryKey: ["transport-vehicles"],
    queryFn: () => api.get("/admin/transport/vehicles") as Promise<VehicleData[]>,
  });
  const papers = useQuery({
    queryKey: ["transport-expiring"],
    queryFn: () => api.get("/admin/transport/expiring") as Promise<Paper[]>,
  });

  const setRoute = useWrite<string>({
    write: (reason: string) =>
      api.patch(
        `/admin/transport/routes/${routeStatus!.route.id}/status` as "/admin/transport/routes/{route_id}/status",
        { status: routeStatus!.to, reason },
      ),
    invalidates: [["transport-routes"]],
    onDone: () => setRouteStatus(null),
  });

  const ground = useWrite<string>({
    write: (reason: string) =>
      api.patch(
        `/admin/transport/vehicles/${grounding!.id}/status` as "/admin/transport/vehicles/{vehicle_id}/status",
        { status: "grounded", reason },
      ),
    invalidates: [["transport-vehicles"], ["transport-routes"]],
    onDone: () => setGrounding(null),
  });

  const openRoute = (routes.data ?? []).find((r) => r.id === openRouteId) ?? null;
  const mapRoute = (routes.data ?? []).find((r) => r.id === mapRouteId) ?? null;

  const lapsed = (papers.data ?? []).filter((p) => p.days_left < 0).length;
  const active = (routes.data ?? []).filter((r) => r.status === "active").length;
  const riding = (routes.data ?? []).reduce((n, r) => n + r.taken, 0);
  const totalFleetCapacity = (vehicles.data ?? []).reduce((sum, v) => sum + v.capacity, 0);

  return (
    <div className="space-y-6">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-surface p-4 rounded-card border border-rule shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-ink">Transport & Fleet Management Desk</h1>
          <p className="text-xs text-ink-soft">
            Manage routes, vehicles, address-first geocoded stops, crew compliance, and student allocations.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton
            permission={SETUP_WRITE}
            onClick={() => setShowAllocationDesk(true)}
            className="!px-3.5 !py-2 text-xs font-semibold shadow-sm flex items-center gap-1.5"
          >
            <span>🎒</span> Student Allocation Desk
          </ActionButton>

          <ActionButton
            permission={SETUP_WRITE}
            variant="secondary"
            onClick={() => setShowSlabsModal(true)}
            className="!px-3.5 !py-2 text-xs font-semibold border border-rule hover:bg-canvas"
          >
            Distance Fee Slabs
          </ActionButton>

          <ActionButton
            permission={SETUP_WRITE}
            variant="secondary"
            onClick={() => setIsCreatingVehicle(true)}
            className="!px-3.5 !py-2 text-xs font-semibold border border-rule hover:bg-canvas"
          >
            + Add Vehicle
          </ActionButton>

          <ActionButton
            permission={SETUP_WRITE}
            variant="primary"
            onClick={() => setIsCreatingRoute(true)}
            className="!px-3.5 !py-2 text-xs font-semibold"
          >
            + New Route
          </ActionButton>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-4">
        <StatCard label="Routes running" value={active} hint={`${routes.data?.length ?? 0} configured`} />
        <StatCard label="Children riding" value={riding} hint="Active assignments" />
        <StatCard label="Fleet capacity" value={`${riding} / ${totalFleetCapacity}`} hint="Riders / Total seats" />
        <StatCard
          label="Papers lapsed"
          value={lapsed}
          hint={lapsed > 0 ? "On road without valid papers" : "All papers compliant"}
        />
      </div>

      {/* Routes Card */}
      <Card
        title="Bus Routes & Operation"
        action={
          <ActionButton
            permission={SETUP_WRITE}
            onClick={() => setIsCreatingRoute(true)}
            className="!px-3 !py-1 text-xs"
          >
            + New Route
          </ActionButton>
        }
      >
        <DataTable<Route>
          rows={routes.data ?? []}
          loading={routes.isLoading}
          error={routes.error}
          onRowClick={(r) => setOpenRouteId(r.id)}
          empty="No routes configured yet. Create a route using the button above."
          columns={[
            { key: "code", header: "Code", render: (r) => <strong className="font-mono">{r.code}</strong> },
            {
              key: "name",
              header: "Route Name",
              render: (r) => (
                <div>
                  <div className="font-medium">{r.name}</div>
                  {r.distance_km && <div className="text-[11px] text-ink-faint">{r.distance_km} km</div>}
                </div>
              ),
            },
            {
              key: "bus",
              header: "Assigned Bus",
              render: (r) =>
                r.vehicle ? (
                  <span className="font-mono text-xs bg-ground px-2 py-0.5 rounded border border-rule">
                    {r.vehicle}
                  </span>
                ) : (
                  <span className="text-danger text-xs font-medium">No bus</span>
                ),
            },
            {
              key: "seats",
              header: "Seats Occupied",
              render: (r) => {
                if (r.capacity === null) return <span className="text-ink-faint">No bus</span>;
                const percent = Math.min(100, Math.round((r.taken / r.capacity) * 100));
                return (
                  <div className="w-32">
                    <div className="flex justify-between text-xs mb-1">
                      <span>{r.taken}/{r.capacity}</span>
                      <span className="text-[10px] text-ink-soft">{percent}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-ground rounded-full overflow-hidden border border-rule">
                      <div
                        className={`h-full ${
                          percent >= 95 ? "bg-danger" : percent >= 75 ? "bg-amber-500" : "bg-primary"
                        }`}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              },
            },
            { key: "stops", header: "Stops", align: "right", render: (r) => r.stops.length },
            {
              key: "status",
              header: "Status",
              render: (r) => <Pill status={r.status}>{r.status}</Pill>,
            },
            {
              key: "actions",
              header: "Desk Actions",
              render: (r) => (
                <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    title="Interactive Route Map"
                    onClick={() => setMapRouteId(r.id)}
                    className="rounded-input border border-rule px-2.5 py-1 text-xs hover:bg-canvas font-medium"
                  >
                    Map
                  </button>

                  <button
                    type="button"
                    title="Print A4 Daily Manifest & Roster"
                    onClick={() => setRosterRouteId(r.id)}
                    className="rounded-input border border-primary text-primary px-2.5 py-1 text-xs hover:bg-primary/5 font-medium"
                  >
                    Roster 🖨️
                  </button>

                  <ActionButton
                    permission={SETUP_WRITE}
                    onClick={() => setDispatchingRoute(r)}
                    className="!px-2.5 !py-1 text-xs font-medium"
                  >
                    Crew
                  </ActionButton>

                  <ActionButton
                    permission={SETUP_WRITE}
                    variant="secondary"
                    onClick={() =>
                      setEditingRoute({
                        id: r.id,
                        code: r.code,
                        name: r.name,
                        distance_km: r.distance_km,
                        stops: r.stops,
                      })
                    }
                    className="!px-2.5 !py-1 text-xs font-medium border border-rule hover:bg-canvas"
                  >
                    Stops
                  </ActionButton>

                  {r.status !== "closed" && (
                    <ActionButton
                      permission={SETUP_WRITE}
                      variant={r.status === "active" ? "danger" : "primary"}
                      className="!px-2.5 !py-1 text-xs font-medium"
                      onClick={() =>
                        setRouteStatus({
                          route: r,
                          to: r.status === "active" ? "suspended" : "active",
                        })
                      }
                    >
                      {r.status === "active" ? "Suspend" : "Activate"}
                    </ActionButton>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Fleet & Vehicles Card */}
      <Card
        title="Fleet & Vehicles"
        action={
          <ActionButton
            permission={SETUP_WRITE}
            onClick={() => setIsCreatingVehicle(true)}
            className="!px-3 !py-1 text-xs"
          >
            + Add Bus
          </ActionButton>
        }
      >
        <DataTable<VehicleData>
          rows={vehicles.data ?? []}
          loading={vehicles.isLoading}
          error={vehicles.error}
          empty="No vehicles in the fleet registry."
          columns={[
            {
              key: "reg",
              header: "Registration",
              render: (v) => <strong className="font-mono">{v.registration_no}</strong>,
            },
            { key: "model", header: "Make & Model", render: (v) => v.make_model ?? "-" },
            { key: "cap", header: "Seating Capacity", align: "right", render: (v) => v.capacity },
            { key: "own", header: "Ownership", render: (v) => <span className="capitalize">{v.ownership}</span> },
            {
              key: "gps",
              header: "GPS Device",
              render: (v) =>
                v.gps_device_id ? (
                  <span className="font-mono text-xs bg-ground px-2 py-0.5 rounded border border-rule">
                    {v.gps_device_id}
                  </span>
                ) : (
                  <span className="text-ink-faint text-xs">Uninstalled</span>
                ),
            },
            {
              key: "status",
              header: "Status",
              render: (v) => <Pill status={v.status}>{v.status.replace("_", " ")}</Pill>,
            },
            {
              key: "act",
              header: "",
              render: (v) => (
                <div className="flex gap-1.5 justify-end">
                  <ActionButton
                    permission={SETUP_WRITE}
                    className="!px-2.5 !py-1 text-xs"
                    onClick={() => setEditingVehicle(v)}
                  >
                    Edit
                  </ActionButton>
                  {v.status === "active" && (
                    <ActionButton
                      permission={SETUP_WRITE}
                      variant="danger"
                      className="!px-2.5 !py-1 text-xs"
                      onClick={() => setGrounding(v)}
                    >
                      Ground
                    </ActionButton>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Compliance & Expiring Papers */}
      <Card title="Compliance & Expiring Papers">
        <DataTable<Paper>
          rows={papers.data ?? []}
          loading={papers.isLoading}
          error={papers.error}
          empty="All vehicle fitness certificates, permits, and crew driving licences are compliant."
          columns={[
            { key: "owner", header: "Bus or Driver", render: (p) => p.owner },
            { key: "doc", header: "Document / Certificate", render: (p) => p.document },
            { key: "on", header: "Expiry Date", render: (p) => asDate(p.expires_on) },
            {
              key: "left",
              header: "Status",
              render: (p) =>
                p.days_left < 0 ? (
                  <Pill status="overdue">Lapsed {Math.abs(p.days_left)}d ago</Pill>
                ) : (
                  <Pill status="pending">{p.days_left}d left</Pill>
                ),
            },
          ]}
        />
      </Card>

      {/* Riders Drilldown Modal */}
      {openRoute && (
        <Riders
          route={openRoute}
          onClose={() => setOpenRouteId(null)}
          onShowMap={() => {
            setMapRouteId(openRoute.id);
            setOpenRouteId(null);
          }}
          onPrintRoster={() => {
            setRosterRouteId(openRoute.id);
            setOpenRouteId(null);
          }}
        />
      )}

      {/* Interactive Leaflet Map Modal */}
      {mapRoute && (
        <RouteMap
          code={mapRoute.code}
          name={mapRoute.name}
          routeId={mapRoute.id}
          stops={mapRoute.stops}
          onClose={() => setMapRouteId(null)}
        />
      )}

      {/* Printable Route Roster Modal */}
      {rosterRouteId !== null && (
        <PrintableRouteRoster
          routeId={rosterRouteId}
          onClose={() => setRosterRouteId(null)}
        />
      )}

      {/* Student Transport Allocation Desk Modal */}
      {showAllocationDesk && (
        <StudentAllocationDesk onClose={() => setShowAllocationDesk(false)} />
      )}

      {/* Distance Fee Slabs Modal */}
      {showSlabsModal && (
        <SlabsModal onClose={() => setShowSlabsModal(false)} />
      )}

      {/* Vehicle Add / Edit Modal */}
      {(isCreatingVehicle || editingVehicle) && (
        <VehicleModal
          vehicle={editingVehicle}
          onClose={() => {
            setIsCreatingVehicle(false);
            setEditingVehicle(null);
          }}
          onSaved={() => {
            vehicles.refetch();
          }}
        />
      )}

      {/* Route & Stop Builder Modal */}
      {(isCreatingRoute || editingRoute) && (
        <RouteBuilderModal
          route={editingRoute}
          onClose={() => {
            setIsCreatingRoute(false);
            setEditingRoute(null);
          }}
          onSaved={() => {
            routes.refetch();
          }}
        />
      )}

      {/* Crew & Vehicle Dispatch Modal */}
      {dispatchingRoute && (
        <CrewDispatchModal
          route={dispatchingRoute}
          onClose={() => setDispatchingRoute(null)}
          onSaved={() => {
            routes.refetch();
          }}
        />
      )}

      {/* Confirm Dialog: Suspend / Activate Route */}
      {routeStatus && (
        <ConfirmDialog
          title={`${routeStatus.to === "suspended" ? "Suspend" : "Make active"} route ${routeStatus.route.code}`}
          confirmLabel={routeStatus.to === "suspended" ? "Suspend route" : "Make active"}
          busy={setRoute.busy}
          error={setRoute.error}
          intent={
            routeStatus.to === "suspended" ? (
              <p>
                {routeStatus.route.taken} child(ren) ride {routeStatus.route.name}. Suspending it stops
                the bus running; their assignments are preserved. A mandatory reason is required.
              </p>
            ) : (
              <p>
                The route will become active and roadworthy if stops and valid vehicle papers are present.
              </p>
            )
          }
          onConfirm={(reason) => setRoute.run(reason)}
          onClose={() => {
            setRoute.reset();
            setRouteStatus(null);
          }}
        />
      )}

      {/* Confirm Dialog: Ground Vehicle */}
      {grounding && (
        <ConfirmDialog
          title={`Ground ${grounding.registration_no}`}
          confirmLabel="Ground this bus"
          busy={ground.busy}
          error={ground.error}
          intent={
            <p>
              The bus stops being roadworthy immediately. Routes it is assigned to will not be able to
              carry students until resolved. Enter a mandatory reason for grounding.
            </p>
          }
          onConfirm={(reason) => ground.run(reason)}
          onClose={() => {
            ground.reset();
            setGrounding(null);
          }}
        />
      )}
    </div>
  );
}

/**
 * Who is on this bus, in the order it reaches them.
 */
function Riders({
  route,
  onClose,
  onShowMap,
  onPrintRoster,
}: {
  route: Route;
  onClose: () => void;
  onShowMap: () => void;
  onPrintRoster: () => void;
}) {
  const riders = useQuery({
    queryKey: ["transport-riders", route.id],
    queryFn: () =>
      api.get(
        `/admin/transport/routes/${route.id}/students` as "/admin/transport/routes/{route_id}/students",
      ) as Promise<Rider[]>,
  });

  const placed = route.stops.filter((s) => s.latitude !== null).length;

  return (
    <Modal title={`${route.code} — ${route.name}`} onClose={onClose} wide>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-ink-faint">
          {placed} of {route.stops.length} stop(s) placed on the map
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onPrintRoster}
            className="rounded-input border border-primary text-primary px-3 py-1.5 text-xs font-medium hover:bg-primary/5"
          >
            Print Manifest 🖨️
          </button>
          <button
            type="button"
            onClick={onShowMap}
            className="rounded-input border border-rule px-3 py-1.5 text-xs font-medium hover:bg-canvas"
          >
            View map
          </button>
        </div>
      </div>

      <Stops route={route} />

      <h3 className="text-sm font-medium mt-6 mb-2">Who rides this route</h3>
      <Can
        permission="transport.assignment.read"
        fallback={<Empty>Your role can see the route but not who rides it.</Empty>}
      >
        <DataTable<Rider>
          rows={riders.data ?? []}
          loading={riders.isLoading}
          error={riders.error}
          empty="No children are assigned to this route yet."
          columns={[
            { key: "seq", header: "#", align: "right", render: (r) => r.sequence },
            { key: "stop", header: "Stop", render: (r) => r.stop },
            { key: "name", header: "Child", render: (r) => r.name },
            { key: "adm", header: "Admission No.", render: (r) => r.admission_no },
            { key: "class", header: "Class", render: (r) => r.class_label },
            { key: "dir", header: "Rides", render: (r) => <span className="capitalize">{r.direction}</span> },
          ]}
        />
      </Can>
    </Modal>
  );
}

/**
 * The stops, with address-first location display and quick pin adjustment.
 */
function Stops({ route }: { route: Route }) {
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ latitude: "", longitude: "", address: "" });

  const pin = useWrite({
    write: () =>
      api.patch(
        `/admin/transport/stops/${editing}/location` as "/admin/transport/stops/{stop_id}/location",
        {
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          address: form.address.trim() || undefined,
        },
      ),
    invalidates: [["transport-routes"]],
    onDone: () => setEditing(null),
  });

  const geocodeAddress = async () => {
    if (!form.address.trim()) return;
    try {
      const res = (await api.get(
        `/admin/transport/geocode?address=${encodeURIComponent(form.address)}` as "/admin/transport/geocode",
      )) as { latitude: number; longitude: number };
      setForm((prev) => ({
        ...prev,
        latitude: String(res.latitude),
        longitude: String(res.longitude),
      }));
    } catch {
      // Ignored
    }
  };

  const ordered = [...route.stops].sort((a, b) => a.sequence - b.sequence);

  return (
    <>
      <h3 className="text-sm font-medium mb-2">Stops</h3>
      <DataTable<MapStop>
        rows={ordered}
        empty="This route has no stops yet."
        columns={[
          { key: "seq", header: "#", align: "right", render: (s) => s.sequence },
          { key: "name", header: "Stop", render: (s) => s.name },
          {
            key: "addr",
            header: "Physical Address",
            render: (s) => (s as any).address || <span className="text-ink-faint">None</span>,
          },
          {
            key: "at",
            header: "Location",
            render: (s) =>
              s.latitude === null || s.longitude === null ? (
                <span className="text-ink-faint">Not placed</span>
              ) : (
                <span className="font-mono text-xs">{`${s.latitude.toFixed(5)}, ${s.longitude.toFixed(5)}`}</span>
              ),
          },
          {
            key: "act",
            header: "",
            render: (s) => (
              <ActionButton
                permission={SETUP_WRITE}
                className="!px-3 !py-1 text-xs"
                onClick={() => {
                  pin.reset();
                  setEditing(s.id);
                  setForm({
                    latitude: s.latitude?.toString() ?? "",
                    longitude: s.longitude?.toString() ?? "",
                    address: (s as any).address ?? "",
                  });
                }}
              >
                {s.latitude === null ? "Set location" : "Move"}
              </ActionButton>
            ),
          },
        ]}
      />

      {editing !== null && (
        <div className="mt-3 rounded-input border border-rule p-3 bg-ground/50 space-y-3">
          <p className="text-xs text-ink-soft">
            Address-first location for{" "}
            <strong>{ordered.find((s) => s.id === editing)?.name}</strong>. Enter an address or fine-tune coordinates.
          </p>

          <FormField label="Physical Address">
            <div className="flex gap-2">
              <input
                className={inputClass}
                placeholder="e.g. Vibhuti Khand, Gomti Nagar, Lucknow"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
              <button
                type="button"
                onClick={geocodeAddress}
                className="shrink-0 px-3 py-1.5 rounded-input border border-primary text-primary text-xs font-medium hover:bg-primary/5"
              >
                Auto-Geocode 📍
              </button>
            </div>
          </FormField>

          <div className="grid grid-cols-2 gap-3">
            <FormField label="Latitude" error={pin.fields.latitude}>
              <input
                className={inputClass}
                value={form.latitude}
                inputMode="decimal"
                placeholder="26.84670"
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
              />
            </FormField>
            <FormField label="Longitude" error={pin.fields.longitude}>
              <input
                className={inputClass}
                value={form.longitude}
                inputMode="decimal"
                placeholder="80.94620"
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
              />
            </FormField>
          </div>
          <FormError error={pin.error} />
          <div className="flex gap-2">
            <ActionButton
              permission={SETUP_WRITE}
              onClick={() => pin.run()}
              disabled={pin.busy || form.latitude.trim() === "" || form.longitude.trim() === ""}
              className="!px-3 !py-1.5 text-xs"
            >
              Save location
            </ActionButton>
            <button
              type="button"
              onClick={() => setEditing(null)}
              className="rounded-input border border-rule px-3 py-1.5 text-xs hover:bg-canvas"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );
}
