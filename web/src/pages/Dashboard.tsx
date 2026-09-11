import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, money } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Card, Empty, ErrorState, Pill, StatCard } from "../components/ui";
import { theme } from "../theme";

type Stats = {
  totals: { students: number; teachers: number; classes: number; fees_collected: string };
  attendance: { present: number; absent: number; leave: number; percent: number | null };
  performance: { excellent: number; good: number; average: number; needs_improvement: number };
  top_performers: { student_id: number; name: string; class_label: string; average_percent: number }[];
  recent_notices: { id: number; title: string; audience: string; published_at: string }[];
  fee_trend: { month: string; collected: string }[];
};

/** /admin/exams is response_model'd; these are the fields this card reads. */
type ExamRow = { id: number; name: string; term: string; start_date: string; end_date: string };
/** /admin/holidays has no response_model; read off api/admin/attendance.py. */
type HolidayRow = { id: number; date: string; name: string };

const PERF_COLORS = [theme.success, theme.info, theme.warning, theme.danger];
const PERF_LABELS: [keyof Stats["performance"], string][] = [
  ["excellent", "Excellent (80%+)"],
  ["good", "Good (60-79%)"],
  ["average", "Average (40-59%)"],
  ["needs_improvement", "Needs improvement (<40%)"],
];

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-stats"],
    // The backend route has no response_model, so the generated schema types
    // it only as `{[key: string]: unknown}` - Stats documents the real shape.
    queryFn: () => api.get("/admin/dashboard/stats") as Promise<Stats>,
  });

  // A failed load used to fall through to "Loading..." and stay there: `error`
  // was never read, so a 500 or a dropped connection was indistinguishable from
  // a slow one. This is the screen a principal opens twice a day, and a
  // permanent "Loading..." is how they conclude the system is hung rather than
  // that one request failed. Part Three rule 8: if a query failed, say so.
  if (error) {
    return (
      <Card title="Overview">
        <ErrorState error={error} />
      </Card>
    );
  }
  if (isLoading || !data) return <p className="text-ink-faint">Loading...</p>;

  const perf = PERF_LABELS.map(([key, label], i) => ({
    name: label,
    value: data.performance[key],
    fill: PERF_COLORS[i],
  }));
  const perfTotal = perf.reduce((a, b) => a + b.value, 0);

  const att = [
    { name: "Present", value: data.attendance.present, fill: theme.success },
    { name: "Absent", value: data.attendance.absent, fill: theme.danger },
    { name: "Leave", value: data.attendance.leave, fill: theme.warning },
  ];
  const attTotal = att.reduce((a, b) => a + b.value, 0);

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Students" value={data.totals.students} />
        <StatCard label="Total Teachers" value={data.totals.teachers} />
        <StatCard label="Total Classes" value={data.totals.classes} />
        <StatCard
          label="Fees Collected"
          value={money(data.totals.fees_collected)}
          hint="Current academic year"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Student Performance">
          {perfTotal === 0 ? (
            <Empty>No marks have been entered yet.</Empty>
          ) : (
            <div className="flex items-center gap-6">
              <PieChart width={180} height={180}>
                  <Pie
                    data={perf}
                    dataKey="value"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={2}
                    isAnimationActive={false}
                  >
                    {perf.map((d) => (
                      <Cell key={d.name} fill={d.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
              </PieChart>
              <ul className="text-sm space-y-2 flex-1">
                {perf.map((d) => (
                  <li key={d.name} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.fill }} />
                    <span className="flex-1 text-ink-soft">{d.name}</span>
                    <span className="tabular">
                      {d.value} ({Math.round((d.value / perfTotal) * 100)}%)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>

        <Card title="Attendance Overview">
          {attTotal === 0 ? (
            <Empty>No attendance marked this month yet.</Empty>
          ) : (
            <div className="flex items-center gap-6">
              <div className="relative">
                <PieChart width={180} height={180}>
                    <Pie
                      data={att}
                      dataKey="value"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={2}
                      isAnimationActive={false}
                    >
                      {att.map((d) => (
                        <Cell key={d.name} fill={d.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                </PieChart>
                <div className="absolute inset-0 grid place-items-center pointer-events-none">
                  <span className="text-2xl font-semibold tabular">
                    {/* The backend returns null rather than a fake 0 when
                        nothing is marked; rendering it raw printed a bare "%". */}
                    {data.attendance.percent === null ? "—" : `${data.attendance.percent}%`}
                  </span>
                </div>
              </div>
              <ul className="text-sm space-y-2 flex-1">
                {att.map((d) => (
                  <li key={d.name} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.fill }} />
                    <span className="flex-1 text-ink-soft">{d.name}</span>
                    <span className="tabular">{d.value}</span>
                  </li>
                ))}
                <li className="text-xs text-ink-faint pt-1">
                  Present as a share of all marked days this month; leave counts against presence.
                </li>
              </ul>
            </div>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Top Performers">
          {data.top_performers.length === 0 ? (
            <Empty>No exam results yet.</Empty>
          ) : (
            <ol className="space-y-3 text-sm">
              {data.top_performers.map((t, i) => (
                <li key={t.student_id} className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-full bg-primary-soft text-primary grid place-items-center font-medium">
                    {i + 1}
                  </span>
                  <span className="flex-1">
                    <span className="block">{t.name}</span>
                    <span className="text-xs text-ink-faint">{t.class_label}</span>
                  </span>
                  <span className="tabular font-medium">{t.average_percent}%</span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        <Card title="Recent Notices">
          {data.recent_notices.length === 0 ? (
            <Empty>Nothing published yet.</Empty>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.recent_notices.map((n) => (
                <li key={n.id}>
                  <p>{n.title}</p>
                  <p className="text-xs text-ink-faint">
                    {/* en-GB: a bare toLocaleDateString() renders 9/10/2026 for
                        10 September, and the office reads dd/mm/yyyy. The
                        Upcoming Events card below already did this. */}
                    {n.audience} - {new Date(n.published_at).toLocaleDateString("en-GB")}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <UpcomingEvents />
      </div>

      <Card title="Fee Collection">
        {data.fee_trend.length === 0 ? (
          <Empty>No payments recorded yet.</Empty>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.fee_trend.map((p) => ({ ...p, collected: Number(p.collected) }))}>
              <CartesianGrid stroke={theme.rule} vertical={false} />
              <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis tickLine={false} axisLine={false} fontSize={12} width={70} />
              <Tooltip formatter={(v: number) => money(v)} />
              <Bar dataKey="collected" fill={theme.primary} radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </>
  );
}

/**
 * What the school has coming, drawn from what the backend actually holds.
 *
 * Two sources, both real: exams from /admin/exams and closures from
 * /admin/holidays. There is no table for parent-teacher meetings or staff
 * meetings anywhere in this system, so none are shown - inventing a PTM row to
 * fill the card would be a fabricated entry on a screen a principal reads, and
 * an empty state beats a made-up one.
 *
 * Both queries gate themselves on permission and module rather than being
 * declared on the screen, so the Dashboard does not disappear from a role that
 * cannot read exams. That does mean the list can be partial, so the card says
 * which sources it actually read instead of implying it covers everything.
 */
function UpcomingEvents() {
  const { can, hasModule } = useAuth();

  const canExams = can("exam.definition.read") && hasModule("examinations");
  const canHolidays = can("attendance.record.read") && hasModule("attendance");

  const exams = useQuery({
    queryKey: ["exams"],
    queryFn: () => api.get("/admin/exams") as Promise<ExamRow[]>,
    enabled: canExams,
  });
  const holidays = useQuery({
    queryKey: ["holidays"],
    queryFn: () => api.get("/admin/attendance/holidays") as Promise<HolidayRow[]>,
    enabled: canHolidays,
  });

  // Midnight today, so an exam starting later today still counts as upcoming.
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const events = [
    ...(exams.data ?? []).map((e) => ({
      key: `exam-${e.id}`,
      date: e.start_date,
      kind: "Exam",
      title: e.name,
      note: e.term,
    })),
    ...(holidays.data ?? []).map((h) => ({
      key: `holiday-${h.id}`,
      date: h.date,
      kind: "Holiday",
      title: h.name,
      note: "School closed",
    })),
  ]
    .filter((e) => new Date(e.date) >= today)
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(0, 8);

  const sources = [canExams ? "exams" : null, canHolidays ? "closures" : null].filter(Boolean);
  const loading = (canExams && exams.isLoading) || (canHolidays && holidays.isLoading);

  return (
    <Card title="Upcoming Events">
      {sources.length === 0 ? (
        <Empty>Your role cannot read the exam calendar or the holiday list.</Empty>
      ) : loading ? (
        <Empty>Loading…</Empty>
      ) : events.length === 0 ? (
        <Empty>Nothing scheduled ahead — no exams and no closures on the calendar.</Empty>
      ) : (
        <>
          <ul className="space-y-3 text-sm max-h-64 overflow-y-auto">
            {events.map((e) => (
              <li key={e.key} className="flex gap-3">
                <span className="tabular text-xs text-ink-faint w-24 shrink-0">
                  {new Date(e.date).toLocaleDateString("en-GB")}
                </span>
                <span>
                  <span className="block">
                    <Pill status={e.kind === "Exam" ? "pending" : "paid"}>{e.kind}</Pill>{" "}
                    {e.title}
                  </span>
                  <span className="text-xs text-ink-faint">{e.note}</span>
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-ink-faint">
            From {sources.join(" and ")}. Meetings and PTMs are not recorded anywhere in the
            system yet, so none are listed.
          </p>
        </>
      )}
    </Card>
  );
}
