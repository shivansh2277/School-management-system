import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useMemo } from "react";


import { api, money } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Card, Empty, ErrorState, FormError, FormField, Modal, Pill, StatCard } from "../components/ui";
import { theme } from "../theme";

type Stats = {
  totals: {
    students: number;
    teachers: number;
    classes: number;
    fees_collected: string | number;
    fees_remaining?: string | number;
  };
  attendance: {
    present: number;
    absent: number;
    leave: number;
    percent: number | null;
    is_school_day?: boolean;
    non_school_reason?: string | null;
  };
  top_performers: { student_id: number; name: string; class_label: string; average_percent: number }[];
  recent_notices: { id: number; title: string; audience: string; published_at: string }[];
  fee_trend: { month: string; collected: string }[];
};

type ExamRow = { id: number; name: string; term: string; start_date: string; end_date: string };
type HolidayRow = { id: number; date: string; name: string };

type DefaulterRow = {
  student_id: number;
  enrolment_id: number;
  student_name: string;
  admission_no: string;
  class_label: string;
  class_teacher_name?: string;
  academic_year?: string;
  fee_type?: string;
  due_date?: string;
  payment_status?: "Unpaid" | "Partially Paid" | "Overdue";
  contact: string;
  months_due: number;
  oldest_due_date: string;
  outstanding: number | string;
  late_fee: number | string;
  days_overdue: number;
};

type GrievanceRow = {
  id: number;
  school_id: number;
  title: string;
  description: string;
  category: string;
  raised_by_id: number;
  raised_by_role: string;
  raised_by_name: string;
  student_id?: number | null;
  student_name?: string | null;
  status: "open" | "in_progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "urgent";
  assigned_to_id?: number | null;
  assigned_to_name?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
  replies_count: number;
  replies?: GrievanceReplyRow[];
};

type GrievanceReplyRow = {
  id: number;
  grievance_id: number;
  author_id: number;
  author_name: string;
  author_role: string;
  message: string;
  is_internal: boolean;
  created_at: string;
};

type GrievanceStats = {
  total_count: number;
  open_count: number;
  in_progress_count: number;
  resolved_count: number;
  teacher_count: number;
  parent_count: number;
};

type TeacherRow = {
  id: number;
  full_name: string;
  employee_code: string;
  employee_type: string;
};

export function Dashboard() {
  const { me } = useAuth();
  const [showDefaultersModal, setShowDefaultersModal] = useState(false);
  const [selectedGrievance, setSelectedGrievance] = useState<GrievanceRow | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: () => api.get("/admin/dashboard/stats") as Promise<Stats>,
  });

  const grievancesQuery = useQuery({
    queryKey: ["admin-grievances"],
    queryFn: () => api.get("/admin/grievances") as Promise<GrievanceRow[]>,
  });

  const grievanceStatsQuery = useQuery({
    queryKey: ["admin-grievance-stats"],
    queryFn: () => api.get("/admin/grievances/stats") as Promise<GrievanceStats>,
  });

  if (error) {
    return (
      <Card title="Overview">
        <ErrorState error={error} />
      </Card>
    );
  }
  if (isLoading || !data) return <p className="text-ink-faint">Loading...</p>;

  const collectedNum = Number(data.totals.fees_collected || 0);
  const remainingNum = Number(data.totals.fees_remaining || 0);
  const totalBilled = collectedNum + remainingNum;
  const collectionPct = totalBilled > 0 ? Math.round((collectedNum / totalBilled) * 100) : 100;

  const gStats = grievanceStatsQuery.data || {
    total_count: 0,
    open_count: 0,
    in_progress_count: 0,
    resolved_count: 0,
    teacher_count: 0,
    parent_count: 0,
  };

  const totalStudents = data.totals.students;
  const presentToday = data.attendance?.present ?? 0;
  const unexcusedAbsent = data.attendance?.absent ?? 0;
  const onLeave = data.attendance?.leave ?? 0;
  const absentToday = unexcusedAbsent + onLeave;
  const attendancePercent =
    data.attendance?.percent ??
    (totalStudents > 0 && presentToday + absentToday > 0
      ? Math.round((presentToday / (presentToday + absentToday)) * 1000) / 10
      : null);

  const totalRecordedAttendance = presentToday + absentToday;
  const presentRatio = totalRecordedAttendance > 0 ? Math.round((presentToday / totalRecordedAttendance) * 100) : 0;
  const absentRatio = totalRecordedAttendance > 0 ? Math.round((absentToday / totalRecordedAttendance) * 100) : 0;
  const leaveRatio = totalRecordedAttendance > 0 ? Math.round((onLeave / totalRecordedAttendance) * 100) : 0;
  const unexcusedRatio = Math.max(0, absentRatio - leaveRatio);

  const todayFormatted = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());

  return (
    <div className="space-y-6">
      {/* Dashboard Top Header Bar with Greeting & Calendar Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Dashboard</h1>
          <p className="text-xs sm:text-sm text-ink-soft mt-0.5">
            Welcome back, {me?.user.full_name || "Office Administrator"}
          </p>
        </div>
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-rule shadow-2xs text-xs font-medium text-ink-soft self-start sm:self-auto select-none">
          <svg className="w-4 h-4 text-ink-faint shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>{todayFormatted}</span>
        </div>
      </div>

      {/* Attendance Overview Card */}
      <Card
        title="Attendance Overview"
        action={
          <div className="flex items-center gap-2">
            {data.attendance?.is_school_day === false ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                No school today ({data.attendance.non_school_reason || "Sunday"})
              </span>
            ) : totalRecordedAttendance === 0 ? (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                Roll call pending
              </span>
            ) : null}
            <a
              href="#/attendance"
              className="text-xs font-semibold text-primary hover:text-primary-dark transition-colors px-2.5 py-1 rounded-md bg-primary/10 hover:bg-primary/20 inline-flex items-center gap-1"
            >
              <span>View Register</span>
              <span aria-hidden="true">&rarr;</span>
            </a>
          </div>
        }
      >
        <div className="space-y-5">
          {/* 4 Attendance Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Total Students */}
            <div className="relative overflow-hidden p-4 rounded-xl bg-surface border border-rule hover:border-slate-300 transition-all shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
              <div>
                <span className="text-xs font-semibold text-ink-soft">Total Students</span>
                <div className="text-3xl font-extrabold tracking-tight text-ink mt-1 tabular">
                  {totalStudents}
                </div>
                <span className="text-xs text-ink-faint mt-1 block">Enrolled active students</span>
              </div>
            </div>

            {/* 2. Present Today */}
            <div className="relative overflow-hidden p-4 rounded-xl bg-surface border border-emerald-100/80 hover:border-emerald-300 transition-all shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <span className="text-[10px] uppercase font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  Present
                </span>
              </div>
              <div>
                <span className="text-xs font-semibold text-ink-soft">Present Today</span>
                <div className="text-3xl font-extrabold tracking-tight text-emerald-600 mt-1 tabular">
                  {data.attendance?.is_school_day === false ? 0 : presentToday}
                </div>
                <span className="text-xs text-ink-faint mt-1 block">
                  {data.attendance?.is_school_day === false
                    ? "No school today"
                    : totalRecordedAttendance === 0
                    ? "Roll call pending"
                    : "Attending school today"}
                </span>
              </div>
            </div>

            {/* 3. Absent Today */}
            <div className="relative overflow-hidden p-4 rounded-xl bg-surface border border-rose-100/80 hover:border-rose-300 transition-all shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a7 7 0 00-7 7h14a7 7 0 00-7-7zM21 12h-6" />
                  </svg>
                </div>
                <span className="text-[10px] uppercase font-bold text-rose-800 bg-rose-100 px-2 py-0.5 rounded-full">
                  Absent
                </span>
              </div>
              <div>
                <span className="text-xs font-semibold text-ink-soft">Absent Today</span>
                <div className="text-3xl font-extrabold tracking-tight text-rose-600 mt-1 tabular">
                  {data.attendance?.is_school_day === false ? 0 : absentToday}
                </div>
                <span className="text-xs text-ink-faint mt-1 block">
                  {data.attendance?.is_school_day === false
                    ? "No school today"
                    : onLeave > 0
                    ? `${unexcusedAbsent} absent · ${onLeave} on leave`
                    : "Not in school"}
                </span>
              </div>
            </div>

            {/* 4. Attendance Percentage */}
            <div className="relative overflow-hidden p-4 rounded-xl bg-surface border border-indigo-100/80 hover:border-indigo-300 transition-all shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                  </svg>
                </div>
                <span className="text-[11px] font-bold text-indigo-800 bg-indigo-100 px-2 py-0.5 rounded-full">
                  Rate
                </span>
              </div>
              <div>
                <span className="text-xs font-semibold text-ink-soft">Attendance Percentage</span>
                <div className="text-3xl font-extrabold tracking-tight text-ink mt-1 tabular">
                  {data.attendance?.is_school_day === false
                    ? "—"
                    : attendancePercent !== null
                    ? `${attendancePercent}%`
                    : "—"}
                </div>
                <span className="text-xs text-ink-faint mt-1 block">
                  {data.attendance?.is_school_day === false ? "School closed today" : "Daily attendance rate"}
                </span>
              </div>
            </div>
          </div>

          {/* Daily Attendance Distribution Progress Visualization */}
          <div className="pt-3 border-t border-rule space-y-2.5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1">
              <span className="text-ink-soft font-semibold">Daily Attendance Distribution</span>
              <span className="font-semibold tabular text-ink">
                {data.attendance?.is_school_day === false
                  ? `No school today (${data.attendance.non_school_reason || "Sunday / Holiday"})`
                  : attendancePercent !== null
                  ? `${attendancePercent}% Present (${presentToday} out of ${totalStudents} students)`
                  : "No attendance recorded today"}
              </span>
            </div>
            {data.attendance?.is_school_day === false ? (
              <div className="w-full bg-amber-50/80 border border-amber-200/80 rounded-lg p-2.5 text-center text-xs text-amber-900 font-medium">
                No school today — {data.attendance.non_school_reason || "Sunday / Holiday"}. Campus is not in session.
              </div>
            ) : totalRecordedAttendance === 0 ? (
              <div className="w-full bg-slate-50 border border-rule/60 rounded-lg p-2.5 text-center text-xs text-ink-faint font-medium">
                Attendance has not been recorded yet for today. Open the Attendance Register to mark morning roll call.
              </div>
            ) : (
              <>
                <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden flex border border-rule/60">
                  <div
                    className="bg-emerald-500 h-full transition-all duration-500 rounded-l-full"
                    style={{ width: `${Math.min(presentRatio, 100)}%` }}
                    title={`Present: ${presentToday}`}
                  />
                  {onLeave > 0 && (
                    <div
                      className="bg-amber-400 h-full transition-all duration-500"
                      style={{ width: `${Math.min(leaveRatio, 100)}%` }}
                      title={`On Leave: ${onLeave}`}
                    />
                  )}
                  <div
                    className="bg-rose-500 h-full transition-all duration-500 rounded-r-full"
                    style={{ width: `${Math.max(0, 100 - presentRatio - (onLeave > 0 ? leaveRatio : 0))}%` }}
                    title={`Absent: ${unexcusedAbsent}`}
                  />
                </div>
                <div className="flex flex-wrap items-center gap-4 text-xs text-ink-soft pt-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
                    <span>Present: <strong className="text-ink font-semibold">{presentToday}</strong> ({presentRatio}%)</span>
                  </div>
                  {onLeave > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shrink-0" />
                      <span>On Leave: <strong className="text-ink font-semibold">{onLeave}</strong> ({leaveRatio}%)</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
                    <span>Unexcused Absent: <strong className="text-ink font-semibold">{unexcusedAbsent}</strong> ({unexcusedRatio}%)</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Row 2: Fees Overview & Grievances in 2-Column Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Fees Overview Card */}
        <Card
          title="Fees Overview"
          action={
            <button
              onClick={() => setShowDefaultersModal(true)}
              className="text-xs font-semibold text-primary hover:text-primary-dark transition-colors px-2.5 py-1 rounded-md bg-primary/10 hover:bg-primary/20 inline-flex items-center gap-1 cursor-pointer"
            >
              <span>View Roster</span>
              <span aria-hidden="true">&rarr;</span>
            </button>
          }
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3.5">
              {/* Fees Collected */}
              <div
                onClick={() => setShowDefaultersModal(true)}
                className="p-3.5 sm:p-4 rounded-xl bg-surface border border-emerald-100 hover:border-emerald-300 hover:shadow-2xs cursor-pointer transition-all group"
                title="Click to view pending fee students"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <span className="text-xs font-semibold text-ink-soft truncate">Fees Collected</span>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full tabular shrink-0">
                    {collectionPct}%
                  </span>
                </div>
                <p className="text-xl xl:text-2xl font-bold text-emerald-600 mt-2.5 tabular group-hover:underline">
                  {money(collectedNum)}
                </p>
                <p className="text-xs text-ink-faint mt-1">Realized collection</p>
              </div>

              {/* Fees Remaining */}
              <div
                onClick={() => setShowDefaultersModal(true)}
                className="p-3.5 sm:p-4 rounded-xl bg-surface border border-rose-100 hover:border-rose-300 hover:shadow-2xs cursor-pointer transition-all group"
                title="Click to view pending fee students"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                      </svg>
                    </div>
                    <span className="text-xs font-semibold text-ink-soft truncate">Fees Remaining</span>
                  </div>
                  <span className="text-[11px] font-bold text-rose-800 bg-rose-100 px-2 py-0.5 rounded-full shrink-0">
                    PENDING
                  </span>
                </div>
                <p className="text-xl xl:text-2xl font-bold text-rose-600 mt-2.5 tabular group-hover:underline">
                  {money(remainingNum)}
                </p>
                <p className="text-xs text-ink-faint mt-1">Click to view roster & export</p>
              </div>
            </div>

            {/* Visual Progress Bar */}
            <div className="space-y-2 pt-1">
              <div className="flex justify-between text-xs text-ink-soft">
                <span className="font-medium">Collection Progress</span>
                <span className="font-bold tabular text-ink">{collectionPct}% complete</span>
              </div>
              <div className="w-full bg-rose-100/60 h-2.5 rounded-full overflow-hidden flex border border-rule/40">
                <div
                  className="bg-emerald-500 transition-all duration-500 rounded-l-full"
                  style={{ width: `${Math.min(100, collectionPct)}%` }}
                />
                <div
                  className="bg-rose-400/80 transition-all duration-500 rounded-r-full"
                  style={{ width: `${Math.max(0, 100 - collectionPct)}%` }}
                />
              </div>
              <div className="flex justify-between items-center text-xs text-ink-faint pt-0.5">
                <span>Total Demand: <strong className="text-ink font-semibold">{money(totalBilled)}</strong></span>
                <button
                  type="button"
                  onClick={() => setShowDefaultersModal(true)}
                  className="text-primary hover:text-primary-dark font-semibold transition-colors inline-flex items-center gap-1 cursor-pointer"
                >
                  <span>Inspect Defaulters</span>
                  <span aria-hidden="true">&rarr;</span>
                </button>
              </div>
            </div>
          </div>
        </Card>

        {/* Grievances & Feedback Card */}
        <Card
          title="Grievances & Feedback"
          action={
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 tabular">
                {gStats.open_count} Open
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 tabular">
                {gStats.in_progress_count} In Progress
              </span>
            </div>
          }
        >
          <div className="space-y-3.5">
            {/* Quick Filter Counts */}
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="p-2 rounded-lg bg-surface border border-rule">
                <span className="text-ink-faint block text-[10px] uppercase font-semibold">Teachers</span>
                <span className="font-bold text-sm text-ink tabular">{gStats.teacher_count}</span>
              </div>
              <div className="p-2 rounded-lg bg-surface border border-rule">
                <span className="text-ink-faint block text-[10px] uppercase font-semibold">Parents</span>
                <span className="font-bold text-sm text-ink tabular">{gStats.parent_count}</span>
              </div>
              <div className="p-2 rounded-lg bg-surface border border-rule">
                <span className="text-ink-faint block text-[10px] uppercase font-semibold">Resolved</span>
                <span className="font-bold text-sm text-emerald-600 tabular">{gStats.resolved_count}</span>
              </div>
              <div className="p-2 rounded-lg bg-surface border border-rule">
                <span className="text-ink-faint block text-[10px] uppercase font-semibold">Total</span>
                <span className="font-bold text-sm text-ink tabular">{gStats.total_count}</span>
              </div>
            </div>

            {/* Recent Grievance List */}
            {grievancesQuery.isLoading ? (
              <Empty>Loading grievances...</Empty>
            ) : grievancesQuery.data && grievancesQuery.data.length > 0 ? (
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {grievancesQuery.data.slice(0, 5).map((g) => (
                  <div
                    key={g.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedGrievance(g)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setSelectedGrievance(g);
                      }
                    }}
                    className="p-3 rounded-xl border border-rule bg-surface hover:bg-slate-50/80 cursor-pointer transition-all hover:shadow-2xs flex items-start justify-between gap-3 group focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                            g.status === "open"
                              ? "bg-rose-100 text-rose-700"
                              : g.status === "in_progress"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-emerald-100 text-emerald-700"
                          }`}
                        >
                          {g.status.replace("_", " ")}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 capitalize">
                          {g.raised_by_role}
                        </span>
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            g.priority === "urgent"
                              ? "bg-rose-600 text-white font-bold"
                              : g.priority === "high"
                              ? "bg-amber-100 text-amber-800"
                              : g.priority === "medium"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {g.priority}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-ink group-hover:text-primary transition-colors truncate">
                        {g.title}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-ink-faint mt-1 flex-wrap">
                        <span>By {g.raised_by_name}</span>
                        {g.created_at && (
                          <span>&bull; {new Date(g.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span>
                        )}
                        {g.student_name && <span>&bull; Child: {g.student_name}</span>}
                        {g.assigned_to_name && (
                          <span className="text-primary font-medium">&bull; Assigned: {g.assigned_to_name}</span>
                        )}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedGrievance(g);
                      }}
                      className="text-xs text-primary hover:text-primary-dark font-semibold shrink-0 pt-1 group-hover:translate-x-0.5 transition-transform inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>{g.replies_count > 0 ? `${g.replies_count} replies` : "Inspect"}</span>
                      <span aria-hidden="true">&rarr;</span>
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <Empty>No grievances reported.</Empty>
            )}
          </div>
        </Card>
      </div>

      {/* Row 3: Top Performers, Recent Notices, and Upcoming Events in 3-Column Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Top Performers Card */}
        <Card title="Top Performers">
          {data.top_performers.length === 0 ? (
            <Empty>No exam results yet.</Empty>
          ) : (
            <ol className="space-y-3 text-sm">
              {data.top_performers.map((t, i) => (
                <li key={t.student_id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
                  <span
                    className={`w-7 h-7 rounded-full grid place-items-center font-bold text-xs shrink-0 ${
                      i === 0
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : i === 1
                        ? "bg-slate-200 text-slate-800 border border-slate-300"
                        : i === 2
                        ? "bg-orange-100 text-orange-800 border border-orange-300"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {i + 1}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className="block font-semibold text-ink truncate">{t.name}</span>
                    <span className="text-xs text-ink-faint">{t.class_label}</span>
                  </span>
                  <span className="tabular font-bold text-xs px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-100 shrink-0">
                    {t.average_percent}%
                  </span>
                </li>
              ))}
            </ol>
          )}
        </Card>

        {/* Recent Notices Card */}
        <Card title="Recent Notices">
          {data.recent_notices.length === 0 ? (
            <Empty>Nothing published yet.</Empty>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.recent_notices.map((n) => (
                <li key={n.id} className="p-2.5 rounded-lg border border-rule/60 hover:border-rule bg-surface transition-all">
                  <p className="font-semibold text-ink line-clamp-1">{n.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wider bg-slate-100 text-slate-700">
                      {n.audience}
                    </span>
                    <span className="text-xs text-ink-faint">
                      {new Date(n.published_at).toLocaleDateString("en-GB")}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Upcoming Events Card */}
        <UpcomingEvents />
      </div>


      {/* Unpaid Fee Students Modal with all 10 requested columns & CSV Export */}
      {showDefaultersModal && (
        <DefaultersModal onClose={() => setShowDefaultersModal(false)} />
      )}

      {/* Grievance Detail, Reply, and Teacher Assignment Modal */}
      {selectedGrievance && (
        <GrievanceDetailModal
          grievanceId={selectedGrievance.id}
          onClose={() => {
            setSelectedGrievance(null);
            grievancesQuery.refetch();
            grievanceStatsQuery.refetch();
          }}
        />
      )}
    </div>
  );
}

/**
 * Modal displaying students who have not submitted fees with:
 * Student Name, Admission ID, Class & Section, Class Teacher Name,
 * Academic Year, Fee Type, Due Date, Payment Status, Pending Fee Amount,
 * and Total Pending Amount at the bottom row.
 * Includes CSV Export button with the summary row.
 */
function DefaultersModal({ onClose }: { onClose: () => void }) {
  const [search, setSearch] = useState("");
  const [classFilter, setClassFilter] = useState("all");

  const { data: rows = [], isLoading, error } = useQuery({
    queryKey: ["admin-fee-defaulters"],
    queryFn: () => api.get("/admin/fees/defaulters") as Promise<DefaulterRow[]>,
  });

  const classes = useMemo(() => {
    const set = new Set<string>();
    rows.forEach((r) => {
      if (r.class_label) set.add(r.class_label);
    });
    return Array.from(set).sort();
  }, [rows]);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      const matchSearch =
        search === "" ||
        r.student_name.toLowerCase().includes(search.toLowerCase()) ||
        r.admission_no.toLowerCase().includes(search.toLowerCase()) ||
        (r.class_teacher_name && r.class_teacher_name.toLowerCase().includes(search.toLowerCase()));
      const matchClass = classFilter === "all" || r.class_label === classFilter;
      return matchSearch && matchClass;
    });
  }, [rows, search, classFilter]);

  const totalPending = useMemo(() => {
    return filtered.reduce((acc, r) => acc + Number(r.outstanding || 0), 0);
  }, [filtered]);

  const exportCSV = () => {
    const headers = [
      "Student Name",
      "Admission / Student ID",
      "Class & Section",
      "Class Teacher Name",
      "Academic Year",
      "Fee Type",
      "Due Date",
      "Payment Status",
      "Pending Fee Amount (INR)",
    ];

    const dataLines = filtered.map((r) => [
      `"${r.student_name.replace(/"/g, '""')}"`,
      `"${r.admission_no}"`,
      `"${r.class_label}"`,
      `"${(r.class_teacher_name || "—").replace(/"/g, '""')}"`,
      `"${r.academic_year || "—"}"`,
      `"${(r.fee_type || "Tuition Fee").replace(/"/g, '""')}"`,
      `"${r.due_date || r.oldest_due_date}"`,
      `"${r.payment_status || "Unpaid"}"`,
      Number(r.outstanding).toFixed(2),
    ]);

    // Bottom row with Total Pending Amount
    dataLines.push([
      `"TOTAL PENDING AMOUNT"`,
      `""`,
      `""`,
      `""`,
      `""`,
      `""`,
      `""`,
      `""`,
      totalPending.toFixed(2),
    ]);

    const csvContent = [headers.join(","), ...dataLines.map((l) => l.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `Pending_Fee_Students_Report_${new Date().toISOString().split("T")[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Modal title="Pending Fee Students" onClose={onClose} wide={true}>
      <div className="space-y-4">
        {/* Controls: Search, Class Filter, and Export Button */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1">
            <input
              type="text"
              placeholder="Search by student name or admission ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 max-w-xs px-3 py-1.5 text-sm border border-rule rounded-md bg-ground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              className="px-3 py-1.5 text-sm border border-rule rounded-md bg-ground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="all">All Classes</option>
              {classes.map((c) => (
                <option key={c} value={c}>
                  Class {c}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-ink-faint tabular">
              {filtered.length} student{filtered.length === 1 ? "" : "s"}
            </span>
            <button
              onClick={exportCSV}
              disabled={filtered.length === 0}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-md bg-primary text-white hover:bg-primary-dark disabled:opacity-50 transition-colors flex items-center gap-1.5 shadow-sm"
            >
              Export Report (CSV)
            </button>
          </div>
        </div>

        {/* Table of Defaulters with all 10 columns */}
        {error ? (
          <ErrorState error={error} />
        ) : isLoading ? (
          <Empty>Loading pending fee roster...</Empty>
        ) : filtered.length === 0 ? (
          <Empty>No students found with pending fees.</Empty>
        ) : (
          <div className="overflow-x-auto border border-rule rounded-lg">
            <table className="w-full text-xs text-left">
              <thead className="bg-ground/60 border-b border-rule font-semibold text-ink-soft">
                <tr>
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Admission ID</th>
                  <th className="py-2.5 px-3">Class & Section</th>
                  <th className="py-2.5 px-3">Class Teacher</th>
                  <th className="py-2.5 px-3">Academic Year</th>
                  <th className="py-2.5 px-3">Fee Type</th>
                  <th className="py-2.5 px-3">Due Date</th>
                  <th className="py-2.5 px-3">Payment Status</th>
                  <th className="py-2.5 px-3 text-right">Pending Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule">
                {filtered.map((r) => (
                  <tr key={r.student_id} className="hover:bg-ground/30 transition-colors">
                    <td className="py-2.5 px-3 font-medium text-ink">{r.student_name}</td>
                    <td className="py-2.5 px-3 tabular text-ink-soft">{r.admission_no}</td>
                    <td className="py-2.5 px-3 font-medium">{r.class_label}</td>
                    <td className="py-2.5 px-3 text-ink-soft">{r.class_teacher_name || "—"}</td>
                    <td className="py-2.5 px-3 text-ink-soft tabular">{r.academic_year || "—"}</td>
                    <td className="py-2.5 px-3 text-ink-soft max-w-[130px] truncate" title={r.fee_type}>
                      {r.fee_type || "Tuition Fee"}
                    </td>
                    <td className="py-2.5 px-3 tabular text-ink-soft">
                      {new Date(r.due_date || r.oldest_due_date).toLocaleDateString("en-GB")}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          r.payment_status === "Overdue"
                            ? "bg-danger/15 text-danger"
                            : r.payment_status === "Partially Paid"
                            ? "bg-warning/15 text-warning"
                            : "bg-ink-faint/15 text-ink-soft"
                        }`}
                      >
                        {r.payment_status || "Unpaid"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right tabular font-semibold text-danger">
                      {money(r.outstanding)}
                    </td>
                  </tr>
                ))}
              </tbody>
              {/* Bottom Row: Total Pending Amount */}
              <tfoot className="bg-ground border-t-2 border-rule font-bold">
                <tr>
                  <td colSpan={8} className="py-3 px-3 text-right text-ink uppercase tracking-wider text-xs">
                    Total Pending Amount:
                  </td>
                  <td className="py-3 px-3 text-right tabular text-sm text-danger font-bold">
                    {money(totalPending)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}

/**
 * Modal to view Grievance thread, submit replies, assign to a teacher,
 * and update status (open, in_progress, resolved).
 */
function GrievanceDetailModal({
  grievanceId,
  onClose,
}: {
  grievanceId: number;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [replyText, setReplyText] = useState("");
  const [selectedTeacherId, setSelectedTeacherId] = useState<number | "">("");
  const [resolutionNotes, setResolutionNotes] = useState("");

  const { data: g, isLoading, error } = useQuery({
    queryKey: ["admin-grievance-detail", grievanceId],
    queryFn: () =>
      api.get(`/admin/grievances/${grievanceId}` as "/admin/grievances/{id}") as Promise<GrievanceRow>,
  });

  const teachersQuery = useQuery({
    queryKey: ["admin-grievances-staff"],
    queryFn: () => api.get("/admin/grievances/staff" as "/admin/grievances") as unknown as Promise<TeacherRow[]>,
  });

  const replyMutation = useMutation({
    mutationFn: (msg: string) =>
      api.post(`/admin/grievances/${grievanceId}/reply` as "/admin/grievances/{id}/reply", {
        message: msg,
      }),
    onSuccess: () => {
      setReplyText("");
      queryClient.invalidateQueries({ queryKey: ["admin-grievance-detail", grievanceId] });
      queryClient.invalidateQueries({ queryKey: ["admin-grievances"] });
      queryClient.invalidateQueries({ queryKey: ["admin-grievance-stats"] });
    },
  });

  const assignMutation = useMutation({
    mutationFn: (teacherId: number) =>
      api.post(`/admin/grievances/${grievanceId}/assign` as "/admin/grievances/{id}/assign", {
        assigned_to_id: teacherId,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-grievance-detail", grievanceId] });
      queryClient.invalidateQueries({ queryKey: ["admin-grievances"] });
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ status, notes }: { status: "open" | "in_progress" | "resolved" | "closed"; notes?: string }) =>
      api.patch(`/admin/grievances/${grievanceId}/status` as "/admin/grievances/{id}/status", {
        status,
        resolution_notes: notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-grievance-detail", grievanceId] });
      queryClient.invalidateQueries({ queryKey: ["admin-grievances"] });
      queryClient.invalidateQueries({ queryKey: ["admin-grievance-stats"] });
    },
  });

  if (isLoading || !g) {
    return (
      <Modal title="Grievance Details" onClose={onClose}>
        <Empty>Loading grievance details...</Empty>
      </Modal>
    );
  }

  return (
    <Modal title={`Grievance #${g.id}: ${g.title}`} onClose={onClose} wide={true}>
      <div className="space-y-5">
        {/* Header Badges & Info */}
        <div className="p-4 rounded-lg bg-ground border border-rule space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${
                g.status === "open"
                  ? "bg-danger/15 text-danger"
                  : g.status === "in_progress"
                  ? "bg-warning/15 text-warning"
                  : "bg-success/15 text-success"
              }`}
            >
              {g.status.replace("_", " ")}
            </span>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-surface border border-rule text-ink-soft capitalize">
              Role: {g.raised_by_role}
            </span>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-surface border border-rule text-ink-soft capitalize">
              Category: {g.category}
            </span>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded ${
                g.priority === "urgent"
                  ? "bg-danger text-white font-bold"
                  : g.priority === "high"
                  ? "bg-warning/20 text-warning font-semibold"
                  : "bg-ink-faint/15 text-ink-soft"
              }`}
            >
              Priority: {g.priority}
            </span>
          </div>

          <div className="grid sm:grid-cols-2 gap-2 text-xs text-ink-soft pt-1">
            <p>
              <strong className="text-ink">Raised by:</strong> {g.raised_by_name}
            </p>
            {g.student_name && (
              <p>
                <strong className="text-ink">Student:</strong> {g.student_name}
              </p>
            )}
            <p>
              <strong className="text-ink">Submitted on:</strong>{" "}
              {new Date(g.created_at).toLocaleString("en-GB")}
            </p>
            <p>
              <strong className="text-ink">Currently Assigned:</strong>{" "}
              <span className={g.assigned_to_name ? "text-primary font-medium" : "text-ink-faint"}>
                {g.assigned_to_name || "Unassigned"}
              </span>
            </p>
          </div>

          <div className="mt-2 pt-2 border-t border-rule text-sm text-ink bg-surface p-3 rounded">
            <strong className="block text-xs font-medium text-ink-faint uppercase mb-1">Issue Description</strong>
            <p className="whitespace-pre-line">{g.description}</p>
          </div>

          {g.resolution_notes && (
            <div className="mt-2 pt-2 border-t border-success/30 text-xs text-success bg-success/5 p-2.5 rounded">
              <strong className="block font-semibold uppercase mb-0.5">Resolution Notes</strong>
              <p>{g.resolution_notes}</p>
              {g.resolved_at && (
                <span className="text-[10px] text-ink-faint mt-1 block">
                  Resolved on: {new Date(g.resolved_at).toLocaleString("en-GB")}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Action Controls: Assign to Teacher & Status Update */}
        <div className="grid sm:grid-cols-2 gap-4 p-4 rounded-lg bg-surface border border-rule">
          {/* Assign to Teacher */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-ink-soft uppercase tracking-wider">
              Assign to Teacher / Staff
            </label>
            <div className="flex items-center gap-2">
              <select
                value={selectedTeacherId}
                onChange={(e) => setSelectedTeacherId(e.target.value ? Number(e.target.value) : "")}
                className="flex-1 px-3 py-1.5 text-xs border border-rule rounded-md bg-ground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Select teacher...</option>
                {(teachersQuery.data || []).map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name} ({t.employee_code})
                  </option>
                ))}
              </select>
              <button
                onClick={() => {
                  if (selectedTeacherId !== "") {
                    assignMutation.mutate(Number(selectedTeacherId));
                  }
                }}
                disabled={selectedTeacherId === "" || assignMutation.isPending}
                className="px-3 py-1.5 text-xs font-semibold rounded-md bg-primary text-white hover:bg-primary-dark disabled:opacity-50 transition-colors shrink-0"
              >
                {assignMutation.isPending ? "Assigning..." : "Assign"}
              </button>
            </div>
          </div>

          {/* Status Update Action */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-ink-soft uppercase tracking-wider">
              Status Actions
            </label>
            <div className="flex items-center gap-2">
              {g.status === "open" && (
                <button
                  onClick={() => statusMutation.mutate({ status: "in_progress" })}
                  disabled={statusMutation.isPending}
                  className="px-3 py-1.5 text-xs font-semibold rounded-md bg-warning/20 text-warning hover:bg-warning/30 transition-colors"
                >
                  Mark In Progress
                </button>
              )}
              {g.status !== "resolved" && (
                <button
                  onClick={() => {
                    const notes = window.prompt("Enter resolution notes (optional):", resolutionNotes) || undefined;
                    statusMutation.mutate({ status: "resolved", notes });
                  }}
                  disabled={statusMutation.isPending}
                  className="px-3 py-1.5 text-xs font-semibold rounded-md bg-success text-white hover:bg-success/90 transition-colors"
                >
                  Mark Resolved
                </button>
              )}
              {g.status === "resolved" && (
                <button
                  onClick={() => statusMutation.mutate({ status: "closed" })}
                  disabled={statusMutation.isPending}
                  className="px-3 py-1.5 text-xs font-semibold rounded-md bg-ink-faint/20 text-ink-soft hover:bg-ink-faint/30 transition-colors"
                >
                  Close Grievance
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Conversation Thread */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-ink">Conversation History</h3>
          {g.replies && g.replies.length > 0 ? (
            <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
              {g.replies.map((r) => (
                <div
                  key={r.id}
                  className={`p-3 rounded-lg text-xs space-y-1 ${
                    r.author_role === "admin"
                      ? "bg-primary-soft/40 border border-primary/20 ml-6"
                      : "bg-ground border border-rule mr-6"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-ink">
                      {r.author_name}{" "}
                      <span className="text-[10px] font-medium text-ink-faint uppercase px-1 rounded bg-surface border border-rule">
                        {r.author_role}
                      </span>
                    </span>
                    <span className="text-[10px] text-ink-faint">
                      {new Date(r.created_at).toLocaleString("en-GB")}
                    </span>
                  </div>
                  <p className="text-ink whitespace-pre-line text-xs pt-0.5">{r.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-ink-faint italic py-2">No replies yet. Send an official response below.</p>
          )}

          {/* Reply Form */}
          <div className="pt-2 border-t border-rule space-y-2">
            <textarea
              rows={2}
              placeholder="Type your response to this grievance..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-rule rounded-md bg-ground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <div className="flex justify-end">
              <button
                onClick={() => {
                  if (replyText.trim()) {
                    replyMutation.mutate(replyText.trim());
                  }
                }}
                disabled={!replyText.trim() || replyMutation.isPending}
                className="px-4 py-1.5 text-xs font-semibold rounded-md bg-primary text-white hover:bg-primary-dark disabled:opacity-50 transition-colors shadow-sm"
              >
                {replyMutation.isPending ? "Sending..." : "Send Reply"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}

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
    queryKey: ["admin-holidays"],
    queryFn: () => api.get("/admin/attendance/holidays") as Promise<HolidayRow[]>,
    enabled: canHolidays,
  });

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
    ...(holidays.data ?? []).filter((h: any) => h.status !== "cancelled").map((h) => ({
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
