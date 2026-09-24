import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, tokenStore, API_BASE_URL } from "../api/client";
import { errorText } from "../api/errors";
import { Card, Empty, FormField, Modal, Pill, inputClass } from "../components/ui";
import { useClasses, type ClassRow } from "./useClasses";

const BASE = API_BASE_URL;

type ReportItem = {
  code: string;
  name: string;
  category: string;
  permission: string;
  module?: string | null;
  scope: "school" | "section";
  required: string[];
  optional: string[];
  description: string;
};

type ReportLibraryResponse = {
  categories: string[];
  reports: ReportItem[];
};

type ReportRunResult = {
  report: ReportItem;
  meta: {
    academic_year: string;
    filters: Record<string, any>;
    generated_at: string;
    generated_by: string;
  };
  data: any[] | Record<string, any>;
};

export function Reports() {
  const classes = useClasses();
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [activeReport, setActiveReport] = useState<ReportItem | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [runResult, setRunResult] = useState<ReportRunResult | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const libraryQuery = useQuery({
    queryKey: ["report-library"],
    queryFn: () => api.get("/admin/reports" as "/admin/reports") as Promise<ReportLibraryResponse>,
  });

  const categories = ["All", ...(libraryQuery.data?.categories ?? [])];
  const allReports = libraryQuery.data?.reports ?? [];

  const filteredReports = allReports.filter((r) => {
    const matchCat = selectedCategory === "All" || r.category === selectedCategory;
    const matchSearch =
      !searchTerm ||
      r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchCat && matchSearch;
  });

  const openRunner = (report: ReportItem) => {
    setActiveReport(report);
    setRunResult(null);
    setReportError(null);

    // Set intelligent defaults for required/optional parameters
    const todayStr = new Date().toISOString().split("T")[0];
    const initial: Record<string, string> = {};

    const allParams = [...report.required, ...report.optional];
    for (const p of allParams) {
      if (p === "on") initial[p] = todayStr;
      else if (p === "date_from") initial[p] = `${new Date().getFullYear()}-01-01`;
      else if (p === "date_to") initial[p] = todayStr;
      else if (p === "year") initial[p] = String(new Date().getFullYear());
      else if (p === "month") initial[p] = String(new Date().getMonth() + 1);
      else if (p === "threshold") initial[p] = "75.0";
      else if (p === "limit") initial[p] = "10";
      else if (p === "min_amount") initial[p] = "500";
      else if (p === "within_days") initial[p] = "30";
      else if (p === "cycle_id") initial[p] = "1";
      else if (p === "run_id") initial[p] = "1";
      else if (p === "code") initial[p] = "BASIC";
      else if (p === "class_section_id" && classes.data?.[0]) initial[p] = String(classes.data[0].id);
      else initial[p] = "";
    }
    setParamValues(initial);
  };

  const handleRun = async () => {
    if (!activeReport) return;
    setRunning(true);
    setReportError(null);

    try {
      const q = new URLSearchParams();
      for (const [k, v] of Object.entries(paramValues)) {
        if (v !== undefined && v !== "") {
          q.append(k, v);
        }
      }
      const queryStr = q.toString() ? `?${q.toString()}` : "";
      const res = (await api.get(
        `/admin/reports/${activeReport.code}` as "/admin/reports/{code}",
        queryStr,
      )) as ReportRunResult;
      setRunResult(res);
    } catch (err) {
      setReportError(errorText(err));
    } finally {
      setRunning(false);
    }
  };

  const handleExportCsv = async () => {
    if (!activeReport) return;
    setExporting(true);
    setReportError(null);

    try {
      const q = new URLSearchParams();
      for (const [k, v] of Object.entries(paramValues)) {
        if (v !== undefined && v !== "") {
          q.append(k, v);
        }
      }
      const queryStr = q.toString() ? `?${q.toString()}` : "";
      const url = `${BASE}/admin/reports/${activeReport.code}/export${queryStr}`;
      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${tokenStore.get()}`,
        },
      });

      if (!res.ok) {
        throw new Error(`Export failed with HTTP status ${res.status}`);
      }

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `${activeReport.code}-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setReportError(errorText(err));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Search */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Reports Library</h1>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="search"
            placeholder="Search reports by title or code..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={`${inputClass} !py-1.5 w-64 text-xs`}
          />
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex border-b border-rule overflow-x-auto gap-1 pb-2">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded-pill text-xs font-medium whitespace-nowrap transition-colors ${
              selectedCategory === cat
                ? "bg-primary text-white"
                : "bg-surface text-ink-soft border border-rule hover:bg-ground hover:text-ink"
            }`}
          >
            {cat}
            {cat !== "All" && (
              <span className="ml-1.5 opacity-70">
                ({allReports.filter((r) => r.category === cat).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Reports Grid */}
      {libraryQuery.isLoading ? (
        <Card>
          <p className="py-8 text-center text-sm text-ink-faint">Loading reports library catalogue...</p>
        </Card>
      ) : filteredReports.length === 0 ? (
        <Card>
          <Empty>No reports found matching your criteria.</Empty>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredReports.map((r) => (
            <div
              key={r.code}
              className="bg-surface rounded-card border border-rule p-4 flex flex-col justify-between space-y-3 hover:border-primary/40 hover:shadow-card transition-all"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2 min-w-0">
                  <span
                    className="text-[11px] font-mono px-2 py-0.5 rounded bg-ground text-ink-soft font-semibold truncate min-w-0"
                    title={r.code}
                  >
                    {r.code}
                  </span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Pill status="neutral">{r.category}</Pill>
                    {r.scope === "section" ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium shrink-0">
                        Section
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-medium shrink-0">
                        School
                      </span>
                    )}
                  </div>
                </div>

                <h3 className="font-semibold text-ink text-sm">{r.name}</h3>
                <p className="text-xs text-ink-soft line-clamp-2 leading-relaxed">
                  {r.description}
                </p>
              </div>

              <div className="pt-2 border-t border-rule/60 flex items-center justify-between text-xs">
                <span className="text-[11px] text-ink-faint">
                  {r.required.length > 0 ? `${r.required.length} required param(s)` : "No required params"}
                </span>

                <button
                  type="button"
                  onClick={() => openRunner(r)}
                  className="px-3 py-1 bg-primary text-white rounded-input hover:bg-primary-dark font-medium shadow-sm"
                >
                  Run Report →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Report Runner Modal */}
      {activeReport && (
        <Modal title={`Report: ${activeReport.name}`} onClose={() => setActiveReport(null)} wide>
          <div className="space-y-5">
            <div className="rounded-card bg-ground p-3.5 space-y-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-ink font-mono">{activeReport.code}</span>
                <span className="text-ink-soft">Category: <b>{activeReport.category}</b></span>
              </div>
              <p className="text-ink-soft">{activeReport.description}</p>
            </div>

            {/* Error Message */}
            {reportError && (
              <div className="p-3 rounded-card bg-red-50 border border-red-200 text-xs text-danger font-medium">
                {reportError}
              </div>
            )}

            {/* Dynamic Parameter Form */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink-faint">
                Report Filters & Parameters
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {activeReport.required.concat(activeReport.optional).map((param) => {
                  const isRequired = activeReport.required.includes(param);

                  if (param === "class_section_id") {
                    return (
                      <FormField
                        key={param}
                        label={`Class Section ${isRequired ? "*" : "(Optional)"}`}
                      >
                        <select
                          className={inputClass}
                          value={paramValues[param] || ""}
                          onChange={(e) => setParamValues({ ...paramValues, [param]: e.target.value })}
                        >
                          <option value="">{isRequired ? "Select class" : "All Class Sections"}</option>
                          {classes.data?.map((c: ClassRow) => (
                            <option key={c.id} value={c.id}>
                              {c.class_label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                    );
                  }

                  if (param === "on" || param === "date_from" || param === "date_to") {
                    return (
                      <FormField
                        key={param}
                        label={`${param.replace("_", " ").toUpperCase()} ${isRequired ? "*" : "(Optional)"}`}
                      >
                        <input
                          type="date"
                          className={inputClass}
                          value={paramValues[param] || ""}
                          onChange={(e) => setParamValues({ ...paramValues, [param]: e.target.value })}
                        />
                      </FormField>
                    );
                  }

                  if (param === "month") {
                    return (
                      <FormField key={param} label={`Month ${isRequired ? "*" : "(Optional)"}`}>
                        <select
                          className={inputClass}
                          value={paramValues[param] || ""}
                          onChange={(e) => setParamValues({ ...paramValues, [param]: e.target.value })}
                        >
                          <option value="">All months</option>
                          {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                            <option key={m} value={m}>
                              Month {m}
                            </option>
                          ))}
                        </select>
                      </FormField>
                    );
                  }

                  return (
                    <FormField
                      key={param}
                      label={`${param.replace("_", " ")} ${isRequired ? "*" : "(Optional)"}`}
                    >
                      <input
                        type="text"
                        className={inputClass}
                        placeholder={isRequired ? "Required" : "Optional"}
                        value={paramValues[param] || ""}
                        onChange={(e) => setParamValues({ ...paramValues, [param]: e.target.value })}
                      />
                    </FormField>
                  );
                })}
              </div>
            </div>

            {/* Runner Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setActiveReport(null)}
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink font-medium"
              >
                Close
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={exporting}
                  onClick={handleExportCsv}
                  className="px-3.5 py-2 text-xs font-semibold rounded-input bg-surface text-primary border border-primary hover:bg-primary/5 disabled:opacity-60"
                >
                  {exporting ? "Exporting CSV..." : "📥 Export Audited CSV"}
                </button>

                <button
                  type="button"
                  disabled={running}
                  onClick={handleRun}
                  className="px-4 py-2 text-xs font-semibold rounded-input bg-primary text-white hover:bg-primary-dark disabled:opacity-60 shadow-sm"
                >
                  {running ? "Generating..." : "▶ Generate Report"}
                </button>
              </div>
            </div>

            {/* Report Results View */}
            {runResult && (
              <div className="mt-4 pt-4 border-t border-rule space-y-4">
                {/* Result Meta Banner */}
                <div className="bg-primary/5 border border-primary/20 rounded-card p-3.5 text-xs text-ink space-y-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-bold text-primary">
                      Academic Year {runResult.meta.academic_year}
                    </span>
                    <span className="text-ink-faint">
                      Generated at {new Date(runResult.meta.generated_at).toLocaleString()} by {runResult.meta.generated_by}
                    </span>
                  </div>
                  {Object.keys(runResult.meta.filters).length > 0 && (
                    <p className="text-ink-soft text-[11px]">
                      Filters: {Object.entries(runResult.meta.filters).map(([k, v]) => `${k}=${v}`).join(", ")}
                    </p>
                  )}
                </div>

                {/* Render Result Data */}
                {Array.isArray(runResult.data) ? (
                  runResult.data.length === 0 ? (
                    <Empty>No records found matching the specified parameters.</Empty>
                  ) : (
                    <div className="border border-rule rounded-card overflow-hidden max-h-80 overflow-y-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-ground sticky top-0 border-b border-rule text-ink-faint">
                          <tr>
                            {Object.keys(runResult.data[0] || {}).map((col) => (
                              <th key={col} className="py-2.5 px-3 font-semibold capitalize whitespace-nowrap">
                                {col.replace(/_/g, " ")}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-rule">
                          {runResult.data.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-ground/40">
                              {Object.entries(row).map(([k, v], cIdx) => (
                                <td key={cIdx} className="py-2 px-3 tabular text-ink">
                                  {v === null || v === undefined ? (
                                    "-"
                                  ) : typeof v === "object" ? (
                                    (v as any).name ? (
                                      <div>
                                        <div className="font-semibold text-ink">{(v as any).name}</div>
                                        {((v as any).phone || (v as any).email) && (
                                          <div className="text-[11px] text-ink-soft">
                                            {[(v as any).phone, (v as any).email].filter(Boolean).join(" • ")}
                                          </div>
                                        )}
                                      </div>
                                    ) : (
                                      <span className="font-mono text-[11px]">{JSON.stringify(v)}</span>
                                    )
                                  ) : (
                                    String(v)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                ) : typeof runResult.data === "object" && runResult.data !== null ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(runResult.data).map(([k, v]) => (
                      <div key={k} className="p-3 bg-ground rounded-card border border-rule">
                        <p className="text-[11px] text-ink-faint capitalize">{k.replace(/_/g, " ")}</p>
                        <p className="text-lg font-bold text-ink tabular mt-1">
                          {v === null || v === undefined ? "-" : String(v)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm font-semibold text-ink">{String(runResult.data)}</p>
                )}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
