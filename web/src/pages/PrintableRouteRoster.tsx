import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { Modal } from "../components/ui";

type Escort = {
  name: string;
  relationship: string;
  phone: string;
  photo_url?: string | null;
};

type Rider = {
  assignment_id: number;
  student_id: number;
  name: string;
  admission_no: string;
  class_label: string;
  direction: string;
  parent_name: string;
  parent_phone: string;
  escorts: Escort[];
};

type StopRoster = {
  id: number;
  sequence: number;
  name: string;
  address: string;
  landmark?: string | null;
  pickup_time: string;
  drop_time: string;
  riders: Rider[];
};

export type RouteRosterData = {
  route_id: number;
  code: string;
  name: string;
  status: string;
  distance_km: number | null;
  vehicle: {
    registration_no: string;
    make_model: string;
    capacity: number;
  };
  driver: {
    name: string;
    phone: string;
    code: string;
  };
  attendant: {
    name: string;
    phone: string;
    code: string;
  };
  total_riders: number;
  stops: StopRoster[];
};

export function PrintableRouteRoster({
  routeId,
  onClose,
}: {
  routeId: number;
  onClose: () => void;
}) {
  const roster = useQuery({
    queryKey: ["transport-roster", routeId],
    queryFn: () =>
      api.get(
        `/admin/transport/routes/${routeId}/roster` as "/admin/transport/routes/{route_id}/roster",
      ) as Promise<RouteRosterData>,
  });

  const data = roster.data;

  const handlePrint = () => {
    window.print();
  };

  return (
    <Modal title="Print Route Manifest & Roster" onClose={onClose} wide>
      <div className="flex justify-end gap-2 mb-4 print:hidden">
        <button
          type="button"
          onClick={handlePrint}
          className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:opacity-90 flex items-center gap-1.5 shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Print A4 Route Sheet
        </button>
      </div>

      {roster.isLoading && <p className="text-sm text-ink-faint py-8 text-center">Loading roster data...</p>}
      {roster.error && (
        <p className="text-sm text-danger py-8 text-center">Failed to load route roster. Please try again.</p>
      )}

      {data && (
        <div className="printable-roster bg-white text-black p-6 rounded-card border border-rule font-sans">
          {/* Header */}
          <div className="border-b-2 border-primary pb-3 mb-4 text-center">
            <h1 className="text-xl font-bold tracking-wide text-primary">SUNRISE PUBLIC SCHOOL</h1>
            <p className="text-xs text-ink-soft">Vibhuti Khand, Gomti Nagar, Lucknow | CBSE Affiliation No. 2130890</p>
            <h2 className="text-sm font-semibold uppercase tracking-wider mt-1 bg-ground py-1 rounded">
              Daily Transport Manifest & Student Route Roster
            </h2>
          </div>

          {/* Route & Crew Details Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs border border-rule rounded p-3 mb-4 bg-ground">
            <div>
              <span className="text-ink-faint block">Route Code & Name:</span>
              <strong className="text-sm font-semibold">{data.code} — {data.name}</strong>
            </div>
            <div>
              <span className="text-ink-faint block">Vehicle (Bus):</span>
              <strong>{data.vehicle.registration_no}</strong> {data.vehicle.make_model ? `(${data.vehicle.make_model})` : ""}
              <div className="text-[10px] text-ink-soft">Seats: {data.total_riders} / {data.vehicle.capacity || "N/A"}</div>
            </div>
            <div>
              <span className="text-ink-faint block">Driver:</span>
              <strong>{data.driver.name}</strong>
              <div className="text-[11px] text-ink-soft">Ph: {data.driver.phone || "N/A"}</div>
            </div>
            <div>
              <span className="text-ink-faint block">Attendant:</span>
              <strong>{data.attendant.name}</strong>
              <div className="text-[11px] text-ink-soft">Ph: {data.attendant.phone || "N/A"}</div>
            </div>
          </div>

          {/* Stops and Riders */}
          <div className="space-y-4">
            {data.stops.map((stop) => (
              <div key={stop.id} className="border border-rule rounded overflow-hidden">
                <div className="bg-primary/10 px-3 py-2 flex flex-wrap items-center justify-between gap-2 border-b border-rule">
                  <div>
                    <span className="inline-block bg-primary text-white rounded-full w-5 h-5 text-center text-xs leading-5 font-bold mr-2">
                      {stop.sequence}
                    </span>
                    <strong className="text-sm">{stop.name}</strong>
                    {stop.landmark && <span className="text-xs text-ink-soft ml-2">({stop.landmark})</span>}
                  </div>
                  <div className="text-xs flex gap-4 text-ink-soft font-mono">
                    <span>Pick-up: <strong className="text-ink">{stop.pickup_time || "--:--"}</strong></span>
                    <span>Drop-off: <strong className="text-ink">{stop.drop_time || "--:--"}</strong></span>
                    <span className="bg-white px-2 py-0.5 rounded border border-rule">
                      <strong>{stop.riders.length}</strong> student{stop.riders.length === 1 ? "" : "s"}
                    </span>
                  </div>
                </div>

                {stop.riders.length === 0 ? (
                  <p className="text-xs text-ink-faint p-2.5 italic">No students boarding at this stop.</p>
                ) : (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-ground/50 text-left border-b border-rule font-medium text-ink-soft">
                        <th className="p-2 w-12 text-center">#</th>
                        <th className="p-2">Student Name</th>
                        <th className="p-2 w-20">Adm No.</th>
                        <th className="p-2 w-20">Class</th>
                        <th className="p-2 w-16">Ride</th>
                        <th className="p-2">Parent Emergency Contact</th>
                        <th className="p-2">Authorized Pickup Escorts</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rule">
                      {stop.riders.map((r, idx) => (
                        <tr key={r.assignment_id} className="hover:bg-ground/30">
                          <td className="p-2 text-center text-ink-faint font-mono">{idx + 1}</td>
                          <td className="p-2 font-medium">{r.name}</td>
                          <td className="p-2 font-mono">{r.admission_no}</td>
                          <td className="p-2">{r.class_label}</td>
                          <td className="p-2 capitalize">{r.direction}</td>
                          <td className="p-2">
                            <div>{r.parent_name}</div>
                            <div className="font-mono text-ink-soft">{r.parent_phone || "N/A"}</div>
                          </td>
                          <td className="p-2">
                            {r.escorts.length === 0 ? (
                              <span className="text-ink-faint italic">Standard Parent Pickup</span>
                            ) : (
                              <div className="space-y-1">
                                {r.escorts.map((esc, eIdx) => (
                                  <div key={eIdx} className="flex items-center gap-2">
                                    {esc.photo_url ? (
                                      <img
                                        src={esc.photo_url}
                                        alt={esc.name}
                                        className="w-6 h-6 rounded-full object-cover border border-rule shrink-0"
                                      />
                                    ) : (
                                      <span className="w-6 h-6 rounded-full bg-ground border border-rule flex items-center justify-center text-[10px] font-bold text-ink-faint shrink-0">
                                        {esc.name[0]}
                                      </span>
                                    )}
                                    <span className="font-medium">{esc.name}</span>
                                    <span className="text-[10px] text-ink-soft">({esc.relationship})</span>
                                    <span className="font-mono text-[10px] text-ink-faint">{esc.phone}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>

          {/* Signature Footer */}
          <div className="mt-8 pt-6 border-t border-rule grid grid-cols-3 gap-6 text-center text-xs">
            <div>
              <div className="h-10 border-b border-rule"></div>
              <p className="mt-1 font-medium">Driver Signature</p>
              <p className="text-[10px] text-ink-faint">{data.driver.name}</p>
            </div>
            <div>
              <div className="h-10 border-b border-rule"></div>
              <p className="mt-1 font-medium">Attendant Signature</p>
              <p className="text-[10px] text-ink-faint">{data.attendant.name}</p>
            </div>
            <div>
              <div className="h-10 border-b border-rule"></div>
              <p className="mt-1 font-medium">Transport In-Charge</p>
              <p className="text-[10px] text-ink-faint">Sunrise Public School</p>
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
