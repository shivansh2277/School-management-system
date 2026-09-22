import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { ActionButton } from "../../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  ErrorState,
  Pill,
  StatCard,
  inputClass,
} from "../../components/ui";
import { useClasses } from "../useClasses";
import type {
  AdmissionCycle,
  SeatUsage,
  WaitlistEntry,
} from "./types";

export function Waitlist() {
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);
  const [showPromoteConfirm, setShowPromoteConfirm] = useState(false);
  const [promoteResult, setPromoteResult] = useState<string | null>(null);

  // Cycles
  const cyclesQuery = useQuery({
    queryKey: ["admission-cycles"],
    queryFn: () =>
      api.get("/admin/admission/cycles") as Promise<AdmissionCycle[]>,
  });

  const cycles = cyclesQuery.data ?? [];
  const activeCycle =
    cycles.find((c) => c.id === selectedCycleId) ??
    cycles.find((c) => c.status === "open") ??
    cycles[0] ??
    null;
  const cycleId = activeCycle?.id ?? null;

  const cycleClassesQuery = useQuery({
    queryKey: ["admission-cycle-classes", cycleId],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/classes` as "/admin/admission/cycles/{cycle_id}/classes",
      ) as Promise<{ id: number; class_name: string }[]>,
    enabled: cycleId !== null,
  });

  const classesQuery = useClasses();
  const availableClasses: { id: string | number; class_name: string }[] =
    classesQuery.data && classesQuery.data.length > 0
      ? classesQuery.data
      : cycleClassesQuery.data && cycleClassesQuery.data.length > 0
      ? cycleClassesQuery.data
      : [
          { id: "1", class_name: "1" },
          { id: "6", class_name: "6" },
          { id: "9", class_name: "9" },
        ];
  const defaultClass = availableClasses[0]?.class_name ?? "1";
  const [selectedClass, setSelectedClass] = useState<string>("");
  const activeClass = selectedClass || defaultClass;

  // Waitlist query
  const waitlistQuery = useQuery({
    queryKey: ["admission-waitlist", cycleId, activeClass],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/waitlist` as "/admin/admission/cycles/{cycle_id}/waitlist",
        `?class_name=${encodeURIComponent(activeClass)}`,
      ) as Promise<WaitlistEntry[]>,
    enabled: cycleId !== null && activeClass.length > 0,
  });

  // Seat capacity check
  const seatQuery = useQuery({
    queryKey: ["admission-seats-single", cycleId, activeClass],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/seats` as "/admin/admission/cycles/{cycle_id}/seats",
        `?class_name=${encodeURIComponent(activeClass)}`,
      ) as Promise<SeatUsage[]>,
    enabled: cycleId !== null && activeClass.length > 0,
  });

  // Promote next candidate write
  const promoteNext = useWrite({
    write: () =>
      api.post(
        `/admin/admission/cycles/${cycleId}/waitlist/promote?class_name=${encodeURIComponent(activeClass)}` as any,
        {},
      ),
    invalidates: [
      ["admission-waitlist", cycleId, activeClass],
      ["admission-seats-single", cycleId, activeClass],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
    ],
    onDone: (res: any) => {
      setShowPromoteConfirm(false);
      if (res?.promoted) {
        setPromoteResult(
          `Successfully promoted Application #${res.application_no} to offered seat!`,
        );
      } else {
        setPromoteResult(res?.detail || "Nobody is waiting or no seat is free.");
      }
    },
  });

  const waitlist = waitlistQuery.data ?? [];
  const classSeat = seatQuery.data?.[0] ?? null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Waitlist Queue</h1>
        </div>

        <div className="flex items-center gap-3">
          <select
            className={`${inputClass} w-auto font-medium py-1.5`}
            value={activeCycle?.id ?? ""}
            onChange={(e) => setSelectedCycleId(Number(e.target.value))}
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.academic_year})
              </option>
            ))}
          </select>

          <select
            className={`${inputClass} w-auto font-medium py-1.5`}
            value={activeClass}
            onChange={(e) => setSelectedClass(e.target.value)}
          >
            {availableClasses.map((c) => (
              <option key={c.id} value={c.class_name}>
                {c.class_name}
              </option>
            ))}
          </select>

          <ActionButton
            permission="admission.decision.make"
            onClick={() => setShowPromoteConfirm(true)}
            disabled={waitlist.length === 0}
          >
            Promote next candidate →
          </ActionButton>
        </div>
      </div>

      {/* Promotion Result Alert */}
      {promoteResult && (
        <div className="p-4 bg-primary/10 border border-primary/30 rounded-input text-sm text-ink flex items-center justify-between">
          <span>{promoteResult}</span>
          <button
            type="button"
            className="text-xs text-ink-soft hover:text-ink font-semibold"
            onClick={() => setPromoteResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Capacity & Queue Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Waitlist Queue Length"
          value={waitlist.length}
          hint={`Applicants waiting for Class ${activeClass}`}
        />
        <StatCard
          label="Current Seats Free / Open"
          value={classSeat?.remaining_total ?? (classSeat as any)?.available ?? 0}
          hint={
            (classSeat?.remaining_total ?? (classSeat as any)?.available ?? 0) > 0
              ? "Seats available for immediate promotion"
              : "Class is currently at full capacity"
          }
        />
        <StatCard
          label="Total Class Capacity"
          value={classSeat?.total_seats ?? 0}
          hint={`${classSeat?.filled_total ?? (classSeat as any)?.taken ?? 0} confirmed admissions`}
        />
      </div>

      {/* Waitlist Table */}
      <Card title={`Waitlist Queue — Class ${activeClass}`}>
        <DataTable<WaitlistEntry>
          loading={waitlistQuery.isLoading}
          error={waitlistQuery.error}
          empty={`No applicants currently waiting on the waitlist for Class ${activeClass}.`}
          columns={[
            {
              key: "rank",
              header: "Waitlist Rank",
              render: (r) => (
                <span className="font-bold text-primary tabular text-sm">
                  #{r.rank}
                </span>
              ),
            },
            {
              key: "application_no",
              header: "App No",
              render: (r) => (
                <span className="font-mono text-xs font-semibold text-ink">
                  {r.application_no}
                </span>
              ),
            },
            {
              key: "name",
              header: "Applicant Name",
              render: (r) => <span className="font-semibold text-ink">{r.name}</span>,
            },
            {
              key: "application_status",
              header: "Application Status",
              render: (r) => (
                <Pill status={r.application_status === "admitted" ? "present" : "pending"}>
                  {r.application_status.replace(/_/g, " ").toUpperCase()}
                </Pill>
              ),
            },
            {
              key: "status",
              header: "Waitlist Status",
              render: (r) => (
                <span className="capitalize text-xs font-medium text-ink-soft bg-ground px-2 py-0.5 rounded border border-rule">
                  {r.status}
                </span>
              ),
            },
          ]}
          rows={waitlist}
        />
      </Card>

      {/* Confirm Promotion Dialog */}
      {showPromoteConfirm && (
        <ConfirmDialog
          title={`Promote Next Applicant in ${selectedClass}`}
          intent={`Promote the #1 ranked waitlist candidate into an available seat for ${selectedClass}. An offer letter or status update will be generated.`}
          confirmLabel="Promote Candidate"
          busy={promoteNext.busy}
          error={promoteNext.error}
          onConfirm={() => promoteNext.run()}
          onClose={() => setShowPromoteConfirm(false)}
        />
      )}
    </div>
  );
}
