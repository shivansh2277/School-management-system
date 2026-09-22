import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  StatCard,
  inputClass,
} from "../../components/ui";
import type { AdmissionCycle, AdmissionReports as AdmissionReportsType } from "./types";

export function AdmissionReports() {
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);

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

  // Reports query
  const reportsQuery = useQuery({
    queryKey: ["admission-reports", cycleId],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/reports` as "/admin/admission/cycles/{cycle_id}/reports",
      ) as Promise<AdmissionReportsType>,
    enabled: cycleId !== null,
  });

  const rep = reportsQuery.data ?? null;

  // Source tally rows
  const sourceRows = rep
    ? Object.entries(rep.by_source || {}).map(([source, stats]) => {
        const enq = stats.enquiries || 0;
        const conv = stats.converted || 0;
        const rate = enq ? Math.round((conv / enq) * 100) : 0;
        return { source, enquiries: enq, converted: conv, rate };
      })
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Admission Analytics & Reports</h1>
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
        </div>
      </div>

      {reportsQuery.isLoading ? (
        <Empty>Loading admission reports...</Empty>
      ) : reportsQuery.error ? (
        <ErrorState error={reportsQuery.error} />
      ) : rep ? (
        <div className="space-y-6">
          {/* Velocity & Pipeline Cycle Time */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              label="Median Days to Decision"
              value={
                rep.cycle_time.median_days_to_decision !== null &&
                rep.cycle_time.median_days_to_decision !== undefined
                  ? `${rep.cycle_time.median_days_to_decision} days`
                  : "—"
              }
              hint="From application submission to committee decision"
            />
            <StatCard
              label="Median Days to Enrolment"
              value={
                rep.cycle_time.median_days_to_enrolment !== null &&
                rep.cycle_time.median_days_to_enrolment !== undefined
                  ? `${rep.cycle_time.median_days_to_enrolment} days`
                  : "—"
              }
              hint="From application submission to completed conversion"
            />
            <StatCard
              label="Total Decided Applications"
              value={rep.cycle_time.decided ?? 0}
              hint="Admitted, waitlisted, or rejected"
            />
          </div>

          {/* Funnel Breakdown */}
          <Card title="Admission Funnel Progression & Conversion">
            {((rep.funnel as any)?.stages ?? []).length === 0 ? (
              <Empty>No funnel stages recorded.</Empty>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-ink-faint border-b border-rule">
                      <th className="py-2 pr-4 font-medium">Stage</th>
                      <th className="py-2 pr-4 font-medium text-right">Count</th>
                      <th className="py-2 pr-4 font-medium text-right">
                        Conversion from Previous
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {((rep.funnel as any).stages as any[]).map((st, i) => (
                      <tr
                        key={st.stage}
                        className="border-b border-rule last:border-0"
                      >
                        <td className="py-2.5 pr-4 font-semibold text-ink capitalize">
                          {i + 1}. {st.stage.replace(/_/g, " ")}
                        </td>
                        <td className="py-2.5 pr-4 text-right font-mono tabular font-medium text-ink">
                          {st.count}
                        </td>
                        <td className="py-2.5 pr-4 text-right tabular text-ink-soft">
                          {st.of_previous !== null ? (
                            <span className="font-semibold text-primary">
                              {st.of_previous}%
                            </span>
                          ) : (
                            <span className="text-ink-faint">Baseline (100%)</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* Lead Source Effectiveness & Seat Utilisation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Lead Source Effectiveness">
              <DataTable
                empty="No source attribution records."
                columns={[
                  {
                    key: "source",
                    header: "Channel",
                    render: (r: any) => (
                      <span className="font-semibold capitalize text-ink">
                        {r.source.replace(/_/g, " ")}
                      </span>
                    ),
                  },
                  {
                    key: "enquiries",
                    header: "Enquiries",
                    align: "right",
                    render: (r: any) => (
                      <span className="tabular">{r.enquiries}</span>
                    ),
                  },
                  {
                    key: "converted",
                    header: "Enrolled",
                    align: "right",
                    render: (r: any) => (
                      <span className="tabular font-medium text-success">
                        {r.converted}
                      </span>
                    ),
                  },
                  {
                    key: "rate",
                    header: "Yield %",
                    align: "right",
                    render: (r: any) => (
                      <span className="tabular font-semibold text-primary">
                        {r.rate}%
                      </span>
                    ),
                  },
                ]}
                rows={sourceRows}
              />
            </Card>

            <Card title="Seat Utilisation by Class">
              <DataTable
                empty="No class utilisation records."
                columns={[
                  {
                    key: "class",
                    header: "Class",
                    render: (r: any) => (
                      <span className="font-semibold text-ink">
                        {r.class_name} {r.stream ? `(${r.stream})` : ""}
                      </span>
                    ),
                  },
                  {
                    key: "capacity",
                    header: "Capacity",
                    align: "right",
                    render: (r: any) => (
                      <span className="tabular">{r.total_seats}</span>
                    ),
                  },
                  {
                    key: "enrolled",
                    header: "Enrolled",
                    align: "right",
                    render: (r: any) => (
                      <span className="tabular font-medium">{r.enrolled}</span>
                    ),
                  },
                  {
                    key: "pct",
                    header: "Utilisation",
                    align: "right",
                    render: (r: any) => (
                      <span
                        className={`tabular font-bold ${
                          r.utilisation_pct >= 90
                            ? "text-success"
                            : r.utilisation_pct < 50
                              ? "text-danger"
                              : "text-ink"
                        }`}
                      >
                        {r.utilisation_pct}%
                      </span>
                    ),
                  },
                ]}
                rows={rep.seat_utilisation || []}
              />
            </Card>
          </div>

          {/* Demographics & Rejection Reasons */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Applicant Demographics">
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="text-xs font-semibold text-ink-faint uppercase tracking-wider mb-2">
                    Gender Distribution
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(
                      (rep.demographics as any)?.applied?.gender || {},
                    ).map(([g, count]) => (
                      <div
                        key={g}
                        className="p-3 bg-ground rounded-input border border-rule flex-1 min-w-[100px]"
                      >
                        <span className="capitalize text-xs text-ink-soft">
                          {g}
                        </span>
                        <p className="text-xl font-bold tabular mt-0.5">
                          {count as number}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-ink-faint uppercase tracking-wider mb-2">
                    Category Distribution
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(
                      (rep.demographics as any)?.applied?.category || {},
                    ).map(([cat, count]) => (
                      <div
                        key={cat}
                        className="p-3 bg-ground rounded-input border border-rule flex-1 min-w-[100px]"
                      >
                        <span className="capitalize text-xs text-ink-soft">
                          {cat.replace(/_/g, " ")}
                        </span>
                        <p className="text-xl font-bold tabular mt-0.5">
                          {count as number}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            <Card title="Rejection Reasons Analysis">
              {((rep.rejections as any) || []).length === 0 ? (
                <Empty>No rejections recorded for this cycle.</Empty>
              ) : (
                <div className="space-y-2">
                  {((rep.rejections as any) as any[]).map((r, i) => (
                    <div
                      key={i}
                      className="p-2.5 bg-ground rounded-input border border-rule flex items-center justify-between text-sm"
                    >
                      <span className="text-ink font-medium">{r.reason}</span>
                      <span className="text-xs font-bold text-danger bg-danger/10 px-2 py-0.5 rounded tabular">
                        {r.count} applicant(s)
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
