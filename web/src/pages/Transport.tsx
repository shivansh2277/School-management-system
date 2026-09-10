/**
 * Transport — the routes, who rides them, and whether the buses are legal.
 *
 * The office's daily questions are "which children are on this bus" and "is
 * this bus allowed on the road". Everything else the router offers (adding
 * vehicles, fee slabs, editing stops, crew assignment, the assignment desk) is
 * setup done once a term, and is not built here - see reports/packet-5-transport.md.
 *
 * None of the transport routes declare a `response_model`, so the generated
 * schema types them `unknown` and the shapes below are hand-written assertions
 * checked against the service, not by the compiler. Each one names where it
 * was read from. This is the trap that put a live `₹NaN` on a fee screen.
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
import { RouteMap, type MapStop } from "./RouteMap";

/** api/admin/transport.py::_route_out, plus services/transport.py::seats. */
type Route = {
  id: number;
  code: string;
  name: string;
  status: string;
  distance_km: number | null;
  vehicle: string | null;
  capacity: number | null;
  taken: number;
  free: number | null;
  stops: MapStop[];
};

/** api/admin/transport.py::_vehicle_out. */
type Vehicle = {
  id: number;
  registration_no: string;
  make_model: string | null;
  capacity: number;
  ownership: string;
  status: string;
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

// transport.setup.write, read off api/admin/transport.py:49 - the `setup`
// dependency both status routes declare.
const SETUP_WRITE = "transport.setup.write";

export function Transport() {
  // Ids, not the row objects. Holding a Route in state freezes it: pinning a
  // stop invalidates the routes query, the table refetches, and a modal built
  // from a captured snapshot goes on showing "Not placed" for a stop that is
  // now in the database. Deriving from the query data means one source of
  // truth and no stale copy to keep in step.
  const [openRouteId, setOpenRouteId] = useState<number | null>(null);
  const [mapRouteId, setMapRouteId] = useState<number | null>(null);
  // `to` is the union the PATCH body accepts, not `string`: the typed request
  // body rejects anything else at compile time, which is the whole point of it.
  const [routeStatus, setRouteStatus] = useState<{ route: Route; to: "active" | "suspended" } | null>(
    null,
  );
  const [grounding, setGrounding] = useState<Vehicle | null>(null);

  const routes = useQuery({
    queryKey: ["transport-routes"],
    queryFn: () => api.get("/admin/transport/routes") as Promise<Route[]>,
  });
  const vehicles = useQuery({
    queryKey: ["transport-vehicles"],
    queryFn: () => api.get("/admin/transport/vehicles") as Promise<Vehicle[]>,
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

  // Already lapsed, not merely lapsing. The service returns both and sorts by
  // expiry, so a negative days_left is a bus on the road without valid papers
  // - which is the one number on this screen worth putting above the fold.
  const lapsed = (papers.data ?? []).filter((p) => p.days_left < 0).length;
  const active = (routes.data ?? []).filter((r) => r.status === "active").length;
  const riding = (routes.data ?? []).reduce((n, r) => n + r.taken, 0);

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Routes running" value={active} hint={`${routes.data?.length ?? 0} in total`} />
        <StatCard label="Children riding" value={riding} />
        <StatCard
          label="Papers lapsed"
          value={lapsed}
          hint={lapsed > 0 ? "On the road without valid papers" : "Nothing overdue"}
        />
      </div>

      <Card title="Routes">
        <DataTable<Route>
          rows={routes.data ?? []}
          loading={routes.isLoading}
          error={routes.error}
          onRowClick={(r) => setOpenRouteId(r.id)}
          empty="No routes set up yet. Add one in the transport office."
          columns={[
            { key: "code", header: "Code", render: (r) => r.code },
            { key: "name", header: "Route", render: (r) => r.name },
            { key: "bus", header: "Bus", render: (r) => r.vehicle ?? "Not assigned" },
            {
              key: "seats",
              header: "Seats",
              align: "right",
              // No capacity means no bus on the route, which is not "0 free".
              render: (r) =>
                r.capacity === null ? "No bus" : `${r.taken} of ${r.capacity}`,
            },
            { key: "stops", header: "Stops", align: "right", render: (r) => r.stops.length },
            {
              key: "status",
              header: "Status",
              render: (r) => <Pill status={r.status}>{r.status}</Pill>,
            },
            {
              key: "map",
              header: "",
              render: (r) => (
                <button
                  type="button"
                  // No permission: drawing the route you can already read is a
                  // read, and gating it on a write would hide the map from the
                  // setup reader this screen exists for.
                  onClick={(e) => {
                    e.stopPropagation();
                    setMapRouteId(r.id);
                  }}
                  className="rounded-input border border-rule px-3 py-1 text-xs hover:bg-canvas"
                >
                  Route map
                </button>
              ),
            },
            {
              key: "act",
              header: "",
              render: (r) =>
                r.status === "closed" ? null : (
                  <ActionButton
                    permission={SETUP_WRITE}
                    variant={r.status === "active" ? "danger" : "primary"}
                    className="!px-3 !py-1 text-xs"
                    onClick={() =>
                      setRouteStatus({ route: r, to: r.status === "active" ? "suspended" : "active" })
                    }
                  >
                    {r.status === "active" ? "Suspend" : "Make active"}
                  </ActionButton>
                ),
            },
          ]}
        />
      </Card>

      <Card title="Papers expiring">
        <DataTable<Paper>
          rows={papers.data ?? []}
          loading={papers.isLoading}
          error={papers.error}
          empty="No vehicle or driver papers are due in the next 30 days."
          columns={[
            { key: "owner", header: "Bus or driver", render: (p) => p.owner },
            { key: "doc", header: "Document", render: (p) => p.document },
            { key: "on", header: "Expires", render: (p) => asDate(p.expires_on) },
            {
              key: "left",
              header: "",
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

      <Card title="Buses">
        <DataTable<Vehicle>
          rows={vehicles.data ?? []}
          loading={vehicles.isLoading}
          error={vehicles.error}
          empty="No buses on the books yet."
          columns={[
            { key: "reg", header: "Registration", render: (v) => v.registration_no },
            { key: "model", header: "Model", render: (v) => v.make_model ?? "-" },
            { key: "cap", header: "Seats", align: "right", render: (v) => v.capacity },
            { key: "own", header: "Ownership", render: (v) => v.ownership },
            {
              key: "status",
              header: "Status",
              render: (v) => <Pill status={v.status}>{v.status.replace("_", " ")}</Pill>,
            },
            {
              key: "act",
              header: "",
              render: (v) =>
                // Grounding a grounded or retired bus is a no-op the API would
                // accept; offering it invites a pointless audit row.
                v.status === "active" ? (
                  <ActionButton
                    permission={SETUP_WRITE}
                    variant="danger"
                    className="!px-3 !py-1 text-xs"
                    onClick={() => setGrounding(v)}
                  >
                    Ground
                  </ActionButton>
                ) : null,
            },
          ]}
        />
      </Card>

      {openRoute && (
        <Riders
          route={openRoute}
          onClose={() => setOpenRouteId(null)}
          onShowMap={() => {
            setMapRouteId(openRoute.id);
            setOpenRouteId(null);
          }}
        />
      )}

      {mapRoute && (
        <RouteMap
          code={mapRoute.code}
          name={mapRoute.name}
          routeId={mapRoute.id}
          stops={mapRoute.stops}
          onClose={() => setMapRouteId(null)}
        />
      )}

      {routeStatus && (
        <ConfirmDialog
          title={`${routeStatus.to === "suspended" ? "Suspend" : "Make active"} route ${routeStatus.route.code}`}
          confirmLabel={routeStatus.to === "suspended" ? "Suspend route" : "Make active"}
          busy={setRoute.busy}
          error={setRoute.error}
          intent={
            routeStatus.to === "suspended" ? (
              <p>
                {routeStatus.route.taken} child(ren) ride {routeStatus.route.name}. Suspending it
                stops the bus running; their assignments are kept, so it can be restarted without
                re-entering anyone. Say why — this is the only record of it.
              </p>
            ) : (
              <p>
                The API refuses this unless the route has stops and a roadworthy bus, so a refusal
                here is a real compliance problem and not a form error.
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

      {grounding && (
        <ConfirmDialog
          title={`Ground ${grounding.registration_no}`}
          confirmLabel="Ground this bus"
          busy={ground.busy}
          error={ground.error}
          intent={
            <>
              <p>
                The bus stops being roadworthy immediately. Routes it is on are left exactly as they
                are and simply stop being able to go active, rather than being rewritten for you.
              </p>
              <p className="mt-2 text-xs text-ink-faint">
                Use this for a bus that must not carry children today. Sending it for service or
                retiring it are different facts and are not set from this screen.
              </p>
            </>
          }
          onConfirm={(reason) => ground.run(reason)}
          onClose={() => {
            ground.reset();
            setGrounding(null);
          }}
        />
      )}
    </>
  );
}

/**
 * Who is on this bus, in the order it reaches them.
 *
 * Behind `Can` rather than declared on the screen: the riders come from
 * transport.assignment.read, which the setup reader does not necessarily hold,
 * and hiding the whole screen over one drill-down costs that role more than
 * the missing list does.
 */
function Riders({
  route,
  onClose,
  onShowMap,
}: {
  route: Route;
  onClose: () => void;
  onShowMap: () => void;
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
    <Modal title={`${route.code} — ${route.name}`} onClose={onClose}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-xs text-ink-faint">
          {placed} of {route.stops.length} stop(s) placed on the map
        </p>
        <button
          type="button"
          onClick={onShowMap}
          className="rounded-input border border-rule px-3 py-1.5 text-sm hover:bg-canvas"
        >
          View map
        </button>
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
            { key: "dir", header: "Rides", render: (r) => r.direction },
          ]}
        />
      </Can>
    </Modal>
  );
}

/**
 * The stops, and where each one is.
 *
 * Coordinates are entered here because there is nowhere else yet: route setup
 * has no UI, and `PUT /routes/{id}/stops` cannot be used to add them to a route
 * anyone rides (see the note on the backend route). This writes one stop at a
 * time through `PATCH /admin/transport/stops/{id}/location`, which leaves the
 * stop row - and every assignment pointing at it - exactly where it was.
 */
function Stops({ route }: { route: Route }) {
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ latitude: "", longitude: "" });

  const pin = useWrite({
    write: () =>
      api.patch(
        `/admin/transport/stops/${editing}/location` as "/admin/transport/stops/{stop_id}/location",
        { latitude: Number(form.latitude), longitude: Number(form.longitude) },
      ),
    invalidates: [["transport-routes"]],
    onDone: () => setEditing(null),
  });

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
            key: "at",
            header: "Location",
            render: (s) =>
              s.latitude === null || s.longitude === null ? (
                <span className="text-ink-faint">Not placed</span>
              ) : (
                `${s.latitude.toFixed(5)}, ${s.longitude.toFixed(5)}`
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
        <div className="mt-3 rounded-input border border-rule p-3">
          <p className="text-xs text-ink-soft mb-2">
            Latitude and longitude for{" "}
            <strong>{ordered.find((s) => s.id === editing)?.name}</strong>. Read them off a map
            rather than estimating — a pin in the wrong street sends a parent to the wrong kerb.
          </p>
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
          <div className="mt-3 flex gap-2">
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
