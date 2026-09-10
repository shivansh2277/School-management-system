/**
 * The route drawn on a map: numbered stops in sequence, joined in order.
 *
 * Leaflet with OpenStreetMap tiles rather than a keyed provider - the office
 * runs on a school budget and nothing here needs a billing account. Leaflet is
 * driven imperatively against a ref instead of through react-leaflet: one
 * dependency instead of two, and no wrapper to keep in step with React.
 *
 * Coordinates come from `route_stops.latitude/longitude`, which are nullable.
 * A stop nobody has pinned is listed under the map as unplaced rather than
 * being dropped silently or given a plausible position - a bus route is a
 * thing a parent stands at the kerb waiting for, and a wrong pin is worse than
 * an absent one.
 */
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Empty, Modal } from "../components/ui";
import { theme } from "../theme";

export type MapStop = {
  id: number;
  sequence: number;
  name: string;
  landmark?: string | null;
  pickup_time?: string | null;
  latitude: number | null;
  longitude: number | null;
};

type Rider = { stop: string; sequence: number };

/** A numbered pin in the app's own primary colour, not Leaflet's blue teardrop.
 *
 * A `divIcon` also sidesteps Leaflet's default marker images, whose URLs break
 * under a bundler - the usual fix is to re-point them at the packaged assets,
 * which is more code than simply not using them.
 */
function pin(sequence: number) {
  return L.divIcon({
    className: "",
    html: `<span style="
      display:grid;place-items:center;
      width:26px;height:26px;border-radius:9999px;
      background:${theme.primary};color:#fff;
      font:600 12px/1 system-ui,sans-serif;
      box-shadow:0 1px 4px rgba(0,0,0,.35);
      border:2px solid #fff;">${sequence}</span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string,
  );

export function RouteMap({
  code,
  name,
  routeId,
  stops,
  onClose,
}: {
  code: string;
  name: string;
  routeId: number;
  stops: MapStop[];
  onClose: () => void;
}) {
  const { can } = useAuth();
  const holder = useRef<HTMLDivElement>(null);

  // Riders are how many children board at each stop. Behind the same
  // permission the route's student list is behind; without it the map still
  // draws, it just does not claim a number it was not allowed to read.
  const mayCount = can("transport.assignment.read");
  const riders = useQuery({
    queryKey: ["transport-riders", routeId],
    enabled: mayCount,
    queryFn: () =>
      api.get(
        `/admin/transport/routes/${routeId}/students` as "/admin/transport/routes/{route_id}/students",
      ) as Promise<Rider[]>,
  });

  const ordered = [...stops].sort((a, b) => a.sequence - b.sequence);
  const placed = ordered.filter(
    (s): s is MapStop & { latitude: number; longitude: number } =>
      s.latitude !== null && s.longitude !== null,
  );
  const unplaced = ordered.filter((s) => s.latitude === null || s.longitude === null);

  const boarding = new Map<number, number>();
  for (const r of riders.data ?? []) {
    boarding.set(r.sequence, (boarding.get(r.sequence) ?? 0) + 1);
  }

  useEffect(() => {
    if (holder.current === null || placed.length === 0) return;

    const map = L.map(holder.current, { scrollWheelZoom: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      // OpenStreetMap's licence requires the credit; it is not decoration.
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const points: [number, number][] = placed.map((s) => [s.latitude, s.longitude]);

    // Drawn before the markers so the line sits under the pins.
    if (points.length > 1) {
      L.polyline(points, { color: theme.primary, weight: 4, opacity: 0.75 }).addTo(map);
    }

    placed.forEach((stop) => {
      const count = boarding.get(stop.sequence);
      const lines = [
        `<strong>${escapeHtml(stop.name)}</strong>`,
        `Stop ${stop.sequence} of ${ordered.length}`,
        stop.landmark ? escapeHtml(stop.landmark) : null,
        stop.pickup_time ? `Pick-up ${escapeHtml(stop.pickup_time.slice(0, 5))}` : null,
        mayCount
          ? riders.isLoading
            ? "Counting children…"
            : `${count ?? 0} child${count === 1 ? "" : "ren"} board here`
          : null,
      ].filter(Boolean);
      L.marker([stop.latitude, stop.longitude], { icon: pin(stop.sequence) })
        .addTo(map)
        .bindPopup(lines.join("<br/>"));
    });

    // Fit the whole route. A single pinned stop has no extent to fit, so it
    // gets a sensible street-level zoom instead of Leaflet's world view.
    if (points.length === 1) map.setView(points[0], 15);
    else map.fitBounds(L.latLngBounds(points), { padding: [32, 32] });

    // The modal sizes its box after this effect runs on some paints, and a
    // Leaflet map measured against the wrong height renders grey bands.
    const settle = setTimeout(() => map.invalidateSize(), 0);

    return () => {
      clearTimeout(settle);
      map.remove();
    };
    // Re-runs when the counts arrive so the popups stop saying "counting".
  }, [routeId, stops, riders.data, riders.isLoading, mayCount]);

  return (
    <Modal title={`${code} — ${name}`} onClose={onClose} wide>
      {placed.length === 0 ? (
        <Empty>
          No stop on this route has been placed on the map yet. Open the route and set a
          location on each stop — the map draws them in sequence once they have one.
        </Empty>
      ) : (
        <div
          ref={holder}
          // Tall enough to read a route on a laptop, capped against the
          // viewport so it still fits a smaller screen inside the modal.
          className="h-[55vh] min-h-[280px] w-full rounded-input overflow-hidden border border-rule"
        />
      )}

      {unplaced.length > 0 && (
        <p className="mt-3 text-xs text-ink-faint">
          Not on the map yet:{" "}
          {unplaced.map((s) => `${s.sequence}. ${s.name}`).join(", ")}. A stop without a
          location is left off rather than guessed at.
        </p>
      )}
    </Modal>
  );
}
