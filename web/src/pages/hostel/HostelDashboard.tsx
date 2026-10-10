import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Card, Pill, StatCard } from "../../components/ui";
import { getUserRoles } from "../../screens";

type HostelOverview = {
  hostels: Array<{
    id: number;
    name: string;
    code: string;
    gender: string;
    status: string;
    total_floors: number;
    total_rooms: number;
    total_capacity: number;
    active_occupants: number;
    vacant_beds: number;
    occupancy_pct: number;
  }>;
  total_hostels: number;
  total_capacity: number;
  total_occupants: number;
  total_vacant: number;
  overall_occupancy_pct: number;
  today_attendance: {
    total_marked: number;
    present: number;
    absent: number;
    on_leave: number;
    on_outing: number;
    unmarked: number;
  };
  pending_leaves: number;
  overdue_outings: number;
  open_complaints: number;
};

export function HostelDashboard() {
  const { me, can } = useAuth();

  const { data: overview, isLoading, error } = useQuery<HostelOverview>({
    queryKey: ["hostel", "overview"],
    queryFn: () => api.rawGet<HostelOverview>("/admin/hostel/overview"),
  });

  const userRoles = getUserRoles(me);
  const isChiefProvost = userRoles.includes("chief_provost");
  const isWarden = userRoles.includes("warden");
  const isSuperAdminOrAdmin = userRoles.includes("super_admin") || userRoles.includes("admin");

  const roleBadge = isChiefProvost
    ? "Chief Provost Portal"
    : isWarden
    ? "Warden Portal"
    : "Hostel Administrative Overview";

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel & Mess Management</h1>
        <p className="text-ink-soft">Loading hostel metrics...</p>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel & Mess Management</h1>
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-card text-danger">
          Failed to load hostel overview. Please check permissions or network status.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel & Mess Overview</h1>
            <Pill status="active">{roleBadge}</Pill>
          </div>
          <p className="text-sm text-ink-soft mt-1">
            Residential facility monitoring, 8:00 PM attendance, leave approvals, and dining menu.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {!isSuperAdminOrAdmin && can("hostel.attendance.read") && (
            <Link
              to="/hostel/attendance"
              className="px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition shadow-sm"
            >
              Mark 8:00 PM Attendance
            </Link>
          )}
          {!isSuperAdminOrAdmin && can("hostel.leave.read") && (
            <Link
              to="/hostel/leaves"
              className="px-3 py-1.5 rounded bg-surface border border-rule text-ink text-xs font-semibold hover:bg-ground transition"
            >
              Review Leaves & Outings
            </Link>
          )}
          {!isSuperAdminOrAdmin && can("hostel.mess.read") && (
            <Link
              to="/hostel/mess"
              className="px-3 py-1.5 rounded bg-surface border border-rule text-ink text-xs font-semibold hover:bg-ground transition"
            >
              Weekly Mess Menu
            </Link>
          )}
          {can("hostel.resident.admit") && !isWarden && (
            <Link
              to="/hostel/admissions"
              className="px-3 py-1.5 rounded bg-surface border border-rule text-ink text-xs font-semibold hover:bg-ground transition"
            >
              Hostel Admissions Queue
            </Link>
          )}
        </div>
      </div>

      {/* Overdue Alert Banner if any student is overdue */}
      {overview.overdue_outings > 0 && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/40 rounded-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <p className="text-sm font-bold text-amber-900">
                Residential Safety Notice: {overview.overdue_outings} student{overview.overdue_outings > 1 ? "s" : ""} overdue from outing!
              </p>
              <p className="text-xs text-amber-800">
                Expected return time has lapsed without recorded arrival at hostel gate.
              </p>
            </div>
          </div>
          {!isSuperAdminOrAdmin && can("hostel.leave.read") && (
            <Link
              to="/hostel/leaves"
              className="px-3 py-1 rounded bg-amber-600 text-white text-xs font-semibold hover:bg-amber-700 transition"
            >
              View Overdue Outings
            </Link>
          )}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Beds"
          value={overview.total_capacity}
          hint={`${overview.total_hostels} residential building${overview.total_hostels > 1 ? "s" : ""}`}
        />
        <StatCard
          label="Occupied Beds"
          value={overview.total_occupants}
          hint={`${overview.overall_occupancy_pct}% active occupancy`}
        />
        <StatCard
          label="Vacant Beds"
          value={overview.total_vacant}
          hint="Available for Class 9+ allocation"
        />
        <StatCard
          label="Pending Leaves / Outings"
          value={overview.pending_leaves}
          hint={overview.overdue_outings > 0 ? `${overview.overdue_outings} overdue` : "Awaiting approval"}
        />
      </div>

      {/* 8:00 PM Attendance & Welfare Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="Today's Evening Roll Call (8:00 PM)" className="lg:col-span-2">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
            <div className="p-3 bg-ground rounded border border-rule text-center">
              <p className="text-2xs uppercase tracking-wider text-ink-faint font-semibold">Present</p>
              <p className="text-xl font-bold text-emerald-600 mt-1">{overview.today_attendance.present}</p>
            </div>
            <div className="p-3 bg-ground rounded border border-rule text-center">
              <p className="text-2xs uppercase tracking-wider text-ink-faint font-semibold">Absent</p>
              <p className="text-xl font-bold text-rose-600 mt-1">{overview.today_attendance.absent}</p>
            </div>
            <div className="p-3 bg-ground rounded border border-rule text-center">
              <p className="text-2xs uppercase tracking-wider text-ink-faint font-semibold">On Leave</p>
              <p className="text-xl font-bold text-blue-600 mt-1">{overview.today_attendance.on_leave}</p>
            </div>
            <div className="p-3 bg-ground rounded border border-rule text-center">
              <p className="text-2xs uppercase tracking-wider text-ink-faint font-semibold">On Outing</p>
              <p className="text-xl font-bold text-purple-600 mt-1">{overview.today_attendance.on_outing}</p>
            </div>
            <div className="p-3 bg-ground rounded border border-rule text-center">
              <p className="text-2xs uppercase tracking-wider text-ink-faint font-semibold">Unmarked</p>
              <p className="text-xl font-bold text-ink-soft mt-1">{overview.today_attendance.unmarked}</p>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-ink-soft pt-2 border-t border-rule">
            <span>
              Evening attendance is mandated daily at 8:00 PM to verify physical residential safety.
            </span>
            {!isSuperAdminOrAdmin && can("hostel.attendance.read") && (
              <Link to="/hostel/attendance" className="font-semibold text-primary hover:underline">
                Open Register →
              </Link>
            )}
          </div>
        </Card>

        <Card title="Hostel Operations & Safety">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-2.5 bg-ground rounded border border-rule text-sm">
              <span className="text-ink-soft">Active Hostels</span>
              <span className="font-bold text-ink">{overview.total_hostels}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-ground rounded border border-rule text-sm">
              <span className="text-ink-soft">Open Maintenance Complaints</span>
              <span className={`font-bold ${overview.open_complaints > 0 ? "text-amber-600" : "text-ink"}`}>
                {overview.open_complaints}
              </span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-ground rounded border border-rule text-sm">
              <span className="text-ink-soft">Overdue Outings</span>
              <span className={`font-bold ${overview.overdue_outings > 0 ? "text-danger" : "text-emerald-600"}`}>
                {overview.overdue_outings}
              </span>
            </div>
            {!isSuperAdminOrAdmin && can("hostel.incident.read") && (
              <div className="pt-2">
                <Link
                  to="/hostel/complaints"
                  className="w-full block text-center py-2 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground transition"
                >
                  View Maintenance Register
                </Link>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Buildings Breakdown */}
      <Card title="Hostel Buildings & Occupancy Breakdown">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {overview.hostels.map((h) => (
            <div key={h.id} className="p-4 bg-ground rounded-card border border-rule space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-ink">{h.name}</h3>
                  <p className="text-xs text-ink-soft">
                    Code: {h.code} • Category: {h.gender === "male" ? "Boys Hostel" : "Girls Hostel"}
                  </p>
                </div>
                <Pill status={h.occupancy_pct >= 100 ? "failed" : "active"}>
                  {h.occupancy_pct}% Occupied
                </Pill>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-rule/50 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    h.occupancy_pct >= 100 ? "bg-rose-500" : h.occupancy_pct > 80 ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(h.occupancy_pct, 100)}%` }}
                />
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs pt-1">
                <div className="p-2 bg-surface rounded border border-rule">
                  <p className="text-ink-faint">Floors</p>
                  <p className="font-bold text-ink mt-0.5">{h.total_floors}</p>
                </div>
                <div className="p-2 bg-surface rounded border border-rule">
                  <p className="text-ink-faint">Rooms / Beds</p>
                  <p className="font-bold text-ink mt-0.5">{h.total_rooms} / {h.total_capacity}</p>
                </div>
                <div className="p-2 bg-surface rounded border border-rule">
                  <p className="text-ink-faint">Vacancies</p>
                  <p className="font-bold text-emerald-600 mt-0.5">{h.vacant_beds}</p>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                {!isSuperAdminOrAdmin ? (
                  <Link
                    to={`/hostel/rooms?hostel_id=${h.id}`}
                    className="text-xs font-semibold text-primary hover:underline"
                  >
                    View Floor & Bed Layout →
                  </Link>
                ) : (
                  <Link
                    to="/hostel/admissions"
                    className="text-xs font-semibold text-primary hover:underline"
                  >
                    Manage Admissions →
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
