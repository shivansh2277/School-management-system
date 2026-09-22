import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ActionButton, Can } from "../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  ErrorState,
  FormField,
  FormError,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";

type Tab = "runs" | "structures" | "components";

interface PayrollRunItem {
  id: number;
  month: string;
  run_no: number;
  is_supplementary: boolean;
  status: string;
  working_days: number;
  approved_at?: string | null;
  paid_at?: string | null;
  staff?: number;
  gross?: string;
  deductions?: string;
  net?: string;
  employer_cost?: string;
}

interface PayslipItem {
  id: number;
  payslip_no: string;
  month: string;
  run_no: number;
  status: string;
  employee_id: number;
  employee_code: string;
  name: string;
  working_days: number;
  lop_days: number;
  monthly_gross: string;
  total_earnings: string;
  total_deductions: string;
  net_pay: string;
  employer_cost: string;
  lines: { code: string; name: string; type: string; amount: string }[];
}

interface ComponentItem {
  id: number;
  code: string;
  name: string;
  type: string;
  calculation: string;
  value: string;
  applies_below_gross?: string | null;
  taxable: boolean;
  statutory: boolean;
  active: boolean;
  sequence: number;
}

export function Payroll() {
  const qc = useQueryClient();
  const { can } = useAuth();

  const [activeTab, setActiveTab] = useState<Tab>("runs");
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [registerCode, setRegisterCode] = useState<string>("PF");

  // Modals state
  const [showOpenRunModal, setShowOpenRunModal] = useState(false);
  const [showStructureModal, setShowStructureModal] = useState(false);
  const [editingComponent, setEditingComponent] = useState<ComponentItem | null>(null);
  const [viewingPayslip, setViewingPayslip] = useState<PayslipItem | null>(null);
  const [approvingRunId, setApprovingRunId] = useState<number | null>(null);
  const [discardingRunId, setDiscardingRunId] = useState<number | null>(null);

  // Form states
  const now = new Date();
  const [runYear, setRunYear] = useState(now.getFullYear());
  const [runMonth, setRunMonth] = useState(now.getMonth() + 1);
  const [runSupplementary, setRunSupplementary] = useState(false);
  const [approvalNote, setApprovalNote] = useState("");

  // Structure form state
  const [structEmployeeId, setStructEmployeeId] = useState<number | "">("");
  const [structGross, setStructGross] = useState("");
  const [structEffective, setStructEffective] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [structTdsOverride, setStructTdsOverride] = useState("");
  const [structNote, setStructNote] = useState("");

  // Component form state
  const [compValue, setCompValue] = useState("");
  const [compActive, setCompActive] = useState(true);

  // Filter / Search for payslips
  const [payslipSearch, setPayslipSearch] = useState("");

  // Queries
  const runsQuery = useQuery({
    queryKey: ["payroll-runs"],
    queryFn: () => api.get("/admin/payroll/runs"),
  });

  const componentsQuery = useQuery({
    queryKey: ["payroll-components"],
    queryFn: () => api.get("/admin/payroll/components"),
  });

  const employeesQuery = useQuery({
    queryKey: ["employees-list"],
    queryFn: () => api.get("/admin/employees"),
  });

  const selectedRunPayslipsQuery = useQuery({
    queryKey: ["payroll-payslips", selectedRunId],
    queryFn: () =>
      selectedRunId
        ? api.get(`/admin/payroll/runs/${selectedRunId}/payslips` as any)
        : Promise.resolve([]),
    enabled: !!selectedRunId,
  });

  const registerQuery = useQuery({
    queryKey: ["payroll-register", selectedRunId, registerCode],
    queryFn: () =>
      selectedRunId
        ? api.get(`/admin/payroll/runs/${selectedRunId}/register/${registerCode}` as any)
        : Promise.resolve([]),
    enabled: !!selectedRunId && !!registerCode,
  });

  const departmentCostQuery = useQuery({
    queryKey: ["payroll-dept-cost", selectedRunId],
    queryFn: () =>
      selectedRunId
        ? api.get(`/admin/payroll/runs/${selectedRunId}/cost-by-department` as any)
        : Promise.resolve([]),
    enabled: !!selectedRunId,
  });

  // Mutations
  const openRunMutation = useMutation({
    mutationFn: (body: { year: number; month: number; supplementary: boolean }) =>
      api.post("/admin/payroll/runs", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-runs"] });
      setShowOpenRunModal(false);
    },
  });

  const calculateMutation = useMutation({
    mutationFn: (runId: number) =>
      api.post(`/admin/payroll/runs/${runId}/calculate` as any, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-runs"] });
      qc.invalidateQueries({ queryKey: ["payroll-payslips", selectedRunId] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: ({ runId, note }: { runId: number; note: string }) =>
      api.post(`/admin/payroll/runs/${runId}/approve` as any, { note }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-runs"] });
      setApprovingRunId(null);
      setApprovalNote("");
    },
  });

  const markPaidMutation = useMutation({
    mutationFn: (runId: number) =>
      api.post(`/admin/payroll/runs/${runId}/paid` as any, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-runs"] });
    },
  });

  const discardMutation = useMutation({
    mutationFn: ({ runId, reason }: { runId: number; reason: string }) =>
      api.post(`/admin/payroll/runs/${runId}/discard` as any, { reason }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-runs"] });
      setDiscardingRunId(null);
    },
  });

  const setStructureMutation = useMutation({
    mutationFn: (body: any) => api.post("/admin/payroll/structures", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employees-list"] });
      setShowStructureModal(false);
      setStructGross("");
      setStructTdsOverride("");
      setStructNote("");
    },
  });

  const updateComponentMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: any }) =>
      api.put(`/admin/payroll/components/${id}` as any, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["payroll-components"] });
      setEditingComponent(null);
    },
  });

  const runs = (runsQuery.data ?? []) as unknown as PayrollRunItem[];
  const components = (componentsQuery.data ?? []) as unknown as ComponentItem[];
  const employees = (employeesQuery.data ?? []) as any[];
  const selectedRun = runs.find((r) => r.id === selectedRunId);
  const payslips = (selectedRunPayslipsQuery.data ?? []) as PayslipItem[];
  const registers = (registerQuery.data ?? []) as any[];
  const deptCosts = (departmentCostQuery.data ?? []) as any[];

  // Filtered payslips
  const filteredPayslips = payslips.filter((p) => {
    if (!payslipSearch) return true;
    const q = payslipSearch.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.employee_code.toLowerCase().includes(q) ||
      p.payslip_no.toLowerCase().includes(q)
    );
  });

  // Latest / Active run metrics
  const latestRun = runs[0];
  const activeStaffCount = latestRun?.staff ?? 0;
  const activeGrossTotal = latestRun?.gross ? money(latestRun.gross) : "₹0.00";
  const activeDeductionsTotal = latestRun?.deductions ? money(latestRun.deductions) : "₹0.00";
  const activeNetPayout = latestRun?.net ? money(latestRun.net) : "₹0.00";

  const exportBankDisbursal = (runId: number) => {
    const token = localStorage.getItem("sunrise.token");
    const url = `${import.meta.env.VITE_API_URL ?? "http://localhost:8078"}/admin/payroll/runs/${runId}/bank-disbursal?format=csv`;
    // Trigger download via fetch with auth header
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `salary_disbursal_run_${runId}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch((err) => console.error("Export error:", err));
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Payroll & Salary Disbursal</h1>
          <p className="text-sm text-ink-faint mt-1">
            Monthly staff salary calculation, statutory registers, and bank disbursal sheets
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Can permission="payroll.setup.manage">
            <button
              onClick={() => setActiveTab("components")}
              className="rounded-input border border-rule px-3.5 py-2 text-sm font-medium hover:bg-ground transition-colors"
            >
              Salary Components
            </button>
            <button
              onClick={() => setShowStructureModal(true)}
              className="rounded-input border border-rule px-3.5 py-2 text-sm font-medium hover:bg-ground transition-colors"
            >
              + Set Salary Structure
            </button>
          </Can>
          <ActionButton
            permission="payroll.run.manage"
            onClick={() => setShowOpenRunModal(true)}
            className="rounded-input bg-primary text-white px-4 py-2 text-sm font-medium hover:bg-primary-hover shadow-sm"
          >
            + Run Payroll
          </ActionButton>
        </div>
      </div>

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Latest Run"
          value={
            latestRun ? (
              <span className="flex items-center gap-2">
                <span>{latestRun.month}</span>
                <Pill status={latestRun.status}>{latestRun.status}</Pill>
              </span>
            ) : (
              "None"
            )
          }
          hint={latestRun ? `Run #${latestRun.run_no}` : "No payroll executed"}
        />
        <StatCard label="Staff Covered" value={activeStaffCount} hint="Active employees on payroll" />
        <StatCard label="Total Gross Wage Bill" value={activeGrossTotal} hint="Gross monthly demand" />
        <StatCard label="Total Deductions" value={activeDeductionsTotal} hint="PF, ESI, TDS & LOP" />
        <StatCard label="Net Disbursal Payout" value={activeNetPayout} hint="Direct bank credit total" />
      </div>

      {/* Main Tabs Navigation */}
      <div className="border-b border-rule flex gap-6 text-sm font-medium">
        <button
          onClick={() => {
            setActiveTab("runs");
            setSelectedRunId(null);
          }}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "runs"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-faint hover:text-ink"
          }`}
        >
          Payroll Runs ({runs.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("structures");
            setSelectedRunId(null);
          }}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "structures"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-faint hover:text-ink"
          }`}
        >
          Staff Packages & Structures ({employees.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("components");
            setSelectedRunId(null);
          }}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "components"
              ? "border-primary text-primary font-semibold"
              : "border-transparent text-ink-faint hover:text-ink"
          }`}
        >
          Salary Components ({components.length})
        </button>
      </div>

      {/* TAB 1: PAYROLL RUNS */}
      {activeTab === "runs" && !selectedRunId && (
        <Card title="Monthly Payroll Cycles">
          <DataTable<PayrollRunItem>
            columns={[
              {
                key: "month",
                header: "Month / Year",
                render: (r) => (
                  <div className="font-semibold text-ink">
                    {r.month}
                    {r.is_supplementary && (
                      <span className="ml-2 text-xs text-secondary bg-secondary/10 px-2 py-0.5 rounded-pill font-normal">
                        Supplementary
                      </span>
                    )}
                  </div>
                ),
              },
              {
                key: "run_no",
                header: "Run #",
                render: (r) => <span className="tabular font-medium">#{r.run_no}</span>,
              },
              {
                key: "status",
                header: "Status",
                render: (r) => <Pill status={r.status}>{r.status}</Pill>,
              },
              {
                key: "working_days",
                header: "Working Days",
                render: (r) => <span className="tabular">{r.working_days} days</span>,
              },
              {
                key: "staff",
                header: "Staff Count",
                render: (r) => <span className="tabular">{r.staff ?? "-"}</span>,
              },
              {
                key: "gross",
                header: "Gross Demand",
                align: "right",
                render: (r) => <span className="tabular font-medium">{r.gross ? money(r.gross) : "-"}</span>,
              },
              {
                key: "deductions",
                header: "Deductions",
                align: "right",
                render: (r) => (
                  <span className="tabular text-danger">{r.deductions ? money(r.deductions) : "-"}</span>
                ),
              },
              {
                key: "net",
                header: "Net Disbursal",
                align: "right",
                render: (r) => (
                  <span className="tabular font-bold text-success">{r.net ? money(r.net) : "-"}</span>
                ),
              },
              {
                key: "actions",
                header: "Actions",
                render: (r) => (
                  <div className="flex items-center gap-1.5 justify-end" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setSelectedRunId(r.id)}
                      className="rounded border border-rule px-2.5 py-1 text-xs font-medium hover:bg-ground text-primary hover:border-primary transition-colors"
                    >
                      View Details
                    </button>
                    {r.status === "draft" && (
                      <Can permission="payroll.run.manage">
                        <button
                          onClick={() => calculateMutation.mutate(r.id)}
                          disabled={calculateMutation.isPending}
                          className="rounded bg-primary text-white px-2.5 py-1 text-xs font-medium hover:bg-primary-hover transition-colors"
                        >
                          Calculate
                        </button>
                      </Can>
                    )}
                    {r.status === "calculated" && (
                      <>
                        <Can permission="payroll.run.manage">
                          <button
                            onClick={() => calculateMutation.mutate(r.id)}
                            title="Recalculate with latest attendance & structures"
                            className="rounded border border-rule px-2 py-1 text-xs font-medium hover:bg-ground"
                          >
                            Recalculate
                          </button>
                        </Can>
                        <Can permission="payroll.run.approve">
                          <button
                            onClick={() => setApprovingRunId(r.id)}
                            className="rounded bg-purple-600 text-white px-2.5 py-1 text-xs font-medium hover:bg-purple-700"
                          >
                            Approve
                          </button>
                        </Can>
                        <Can permission="payroll.run.manage">
                          <button
                            onClick={() => setDiscardingRunId(r.id)}
                            className="rounded border border-danger/40 text-danger px-2 py-1 text-xs font-medium hover:bg-danger/10"
                          >
                            Discard
                          </button>
                        </Can>
                      </>
                    )}
                    {r.status === "approved" && (
                      <>
                        <button
                          onClick={() => exportBankDisbursal(r.id)}
                          className="rounded border border-primary text-primary px-2.5 py-1 text-xs font-medium hover:bg-primary/10"
                        >
                          Bank CSV
                        </button>
                        <Can permission="payroll.run.approve">
                          <button
                            onClick={() => markPaidMutation.mutate(r.id)}
                            disabled={markPaidMutation.isPending}
                            className="rounded bg-success text-white px-2.5 py-1 text-xs font-medium hover:bg-success/90"
                          >
                            Mark Paid
                          </button>
                        </Can>
                      </>
                    )}
                    {r.status === "paid" && (
                      <button
                        onClick={() => exportBankDisbursal(r.id)}
                        className="rounded border border-rule px-2.5 py-1 text-xs font-medium hover:bg-ground"
                      >
                        Download NEFT
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
            rows={runs}
            loading={runsQuery.isLoading}
            error={runsQuery.error}
            empty="No payroll runs opened yet. Click '+ Run Payroll' above to open a month."
          />
        </Card>
      )}

      {/* SELECTED RUN DETAILS VIEW */}
      {selectedRunId && selectedRun && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 bg-surface p-4 rounded-card border border-rule">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSelectedRunId(null)}
                className="text-sm font-medium text-ink-faint hover:text-ink flex items-center gap-1"
              >
                &larr; Back to Runs
              </button>
              <div className="h-4 w-px bg-rule" />
              <div>
                <span className="font-bold text-lg text-ink">
                  Payroll Run {selectedRun.month} (Run #{selectedRun.run_no})
                </span>
                <span className="ml-3">
                  <Pill status={selectedRun.status}>{selectedRun.status}</Pill>
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => exportBankDisbursal(selectedRun.id)}
                className="rounded-input border border-primary text-primary px-3.5 py-1.5 text-sm font-medium hover:bg-primary/10 transition-colors"
              >
                Export Bank Disbursal (CSV)
              </button>
              {selectedRun.status === "calculated" && (
                <Can permission="payroll.run.approve">
                  <button
                    onClick={() => setApprovingRunId(selectedRun.id)}
                    className="rounded-input bg-purple-600 text-white px-3.5 py-1.5 text-sm font-medium hover:bg-purple-700"
                  >
                    Approve Run
                  </button>
                </Can>
              )}
              {selectedRun.status === "approved" && (
                <Can permission="payroll.run.approve">
                  <button
                    onClick={() => markPaidMutation.mutate(selectedRun.id)}
                    className="rounded-input bg-success text-white px-3.5 py-1.5 text-sm font-medium hover:bg-success/90"
                  >
                    Mark as Disbursed
                  </button>
                </Can>
              )}
            </div>
          </div>

          {/* Run breakdown cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard label="Working Days" value={`${selectedRun.working_days} Days`} />
            <StatCard label="Total Staff Paid" value={selectedRun.staff ?? payslips.length} />
            <StatCard label="Total Deductions" value={selectedRun.deductions ? money(selectedRun.deductions) : "-"} />
            <StatCard label="Net Disbursal Total" value={selectedRun.net ? money(selectedRun.net) : "-"} />
          </div>

          {/* Payslips Roster Card */}
          <Card
            title={`Payslips Register (${filteredPayslips.length})`}
            action={
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Search staff name or code..."
                  value={payslipSearch}
                  onChange={(e) => setPayslipSearch(e.target.value)}
                  className="rounded-input border border-rule px-3 py-1.5 text-xs outline-none focus:border-primary w-64"
                />
              </div>
            }
          >
            <DataTable<PayslipItem>
              columns={[
                {
                  key: "payslip_no",
                  header: "Slip #",
                  render: (p) => <span className="font-mono text-xs text-ink-soft">{p.payslip_no}</span>,
                },
                {
                  key: "employee",
                  header: "Staff Member",
                  render: (p) => (
                    <div>
                      <p className="font-semibold text-ink">{p.name}</p>
                      <p className="text-xs text-ink-faint">{p.employee_code}</p>
                    </div>
                  ),
                },
                {
                  key: "days",
                  header: "Days / LOP",
                  render: (p) => (
                    <span className="text-xs tabular">
                      {p.working_days} worked
                      {p.lop_days > 0 && <span className="ml-1 text-danger font-medium">({p.lop_days} LOP)</span>}
                    </span>
                  ),
                },
                {
                  key: "monthly_gross",
                  header: "Gross Target",
                  align: "right",
                  render: (p) => <span className="tabular">{money(p.monthly_gross)}</span>,
                },
                {
                  key: "total_earnings",
                  header: "Earned",
                  align: "right",
                  render: (p) => <span className="tabular font-medium text-ink">{money(p.total_earnings)}</span>,
                },
                {
                  key: "total_deductions",
                  header: "Deductions",
                  align: "right",
                  render: (p) => <span className="tabular text-danger">{money(p.total_deductions)}</span>,
                },
                {
                  key: "net_pay",
                  header: "Net Salary",
                  align: "right",
                  render: (p) => (
                    <span className="tabular font-bold text-success text-base">{money(p.net_pay)}</span>
                  ),
                },
                {
                  key: "actions",
                  header: "",
                  align: "right",
                  render: (p) => (
                    <button
                      onClick={() => setViewingPayslip(p)}
                      className="rounded border border-rule px-3 py-1 text-xs font-medium hover:bg-ground text-primary hover:border-primary"
                    >
                      View Slip & Print
                    </button>
                  ),
                },
              ]}
              rows={filteredPayslips}
              loading={selectedRunPayslipsQuery.isLoading}
              error={selectedRunPayslipsQuery.error}
              empty="No payslips generated for this run yet. Click 'Calculate' to generate slips."
            />
          </Card>

          {/* Statutory Registers Section */}
          <Card title="Statutory & Departmental Breakdown">
            <div className="space-y-4">
              <div className="flex gap-4 border-b border-rule pb-2">
                {(["PF", "ESI", "TDS"] as const).map((code) => (
                  <button
                    key={code}
                    onClick={() => setRegisterCode(code)}
                    className={`text-sm font-medium pb-1 transition-colors ${
                      registerCode === code
                        ? "text-primary border-b-2 border-primary font-semibold"
                        : "text-ink-faint hover:text-ink"
                    }`}
                  >
                    {code} Register
                  </button>
                ))}
                <button
                  onClick={() => setRegisterCode("DEPT")}
                  className={`text-sm font-medium pb-1 transition-colors ${
                    registerCode === "DEPT"
                      ? "text-primary border-b-2 border-primary font-semibold"
                      : "text-ink-faint hover:text-ink"
                  }`}
                >
                  Cost by Department
                </button>
              </div>

              {registerCode !== "DEPT" ? (
                <DataTable<any>
                  columns={[
                    { key: "employee_code", header: "Code", render: (r) => <span className="tabular">{r.employee_code}</span> },
                    { key: "name", header: "Employee", render: (r) => <span className="font-medium">{r.name}</span> },
                    { key: "payslip_no", header: "Payslip #", render: (r) => <span className="font-mono text-xs">{r.payslip_no}</span> },
                    {
                      key: "amount",
                      header: `${registerCode} Amount`,
                      align: "right",
                      render: (r) => <span className="tabular font-bold text-danger">{money(r.amount)}</span>,
                    },
                  ]}
                  rows={registers}
                  loading={registerQuery.isLoading}
                  error={registerQuery.error}
                  empty={`No ${registerCode} contributions recorded in this run.`}
                />
              ) : (
                <DataTable<any>
                  columns={[
                    { key: "department", header: "Department", render: (r) => <span className="font-semibold">{r.department || "Unassigned"}</span> },
                    { key: "staff", header: "Staff Count", render: (r) => <span className="tabular">{r.staff} staff</span> },
                    {
                      key: "cost",
                      header: "Total Cost (CTC)",
                      align: "right",
                      render: (r) => <span className="tabular font-bold text-ink">{r.cost}</span>,
                    },
                  ]}
                  rows={deptCosts}
                  loading={departmentCostQuery.isLoading}
                  error={departmentCostQuery.error}
                  empty="No departmental cost data available."
                />
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: SALARY STRUCTURES */}
      {activeTab === "structures" && (
        <Card
          title="Staff Salary Structures & Gross Packages"
          action={
            <Can permission="payroll.setup.manage">
              <button
                onClick={() => setShowStructureModal(true)}
                className="rounded bg-primary text-white px-3.5 py-1.5 text-xs font-medium hover:bg-primary-hover shadow-sm"
              >
                + Set / Revise Structure
              </button>
            </Can>
          }
        >
          <DataTable<any>
            columns={[
              {
                key: "code",
                header: "Staff Code",
                render: (e) => <span className="tabular font-mono text-xs">{e.employee_code}</span>,
              },
              {
                key: "name",
                header: "Staff Name",
                render: (e) => (
                  <div>
                    <span className="font-semibold text-ink">{e.name}</span>
                    <p className="text-xs text-ink-faint">{e.department || "No Department"}</p>
                  </div>
                ),
              },
              {
                key: "role",
                header: "Designation",
                render: (e) => <span className="text-xs">{e.role_title || e.user_role || "Staff"}</span>,
              },
              {
                key: "bank",
                header: "Bank & Account",
                render: (e) => (
                  <div className="text-xs text-ink-soft">
                    <p className="font-medium">{e.bank_name || "Bank not set"}</p>
                    <p className="text-ink-faint font-mono">
                      {e.bank_account_no ? `A/C: ${e.bank_account_no}` : "No A/C"}
                      {e.bank_ifsc ? ` (${e.bank_ifsc})` : ""}
                    </p>
                  </div>
                ),
              },
              {
                key: "actions",
                header: "",
                align: "right",
                render: (e) => (
                  <Can permission="payroll.setup.manage">
                    <button
                      onClick={() => {
                        setStructEmployeeId(e.id);
                        setShowStructureModal(true);
                      }}
                      className="rounded border border-rule px-2.5 py-1 text-xs font-medium hover:bg-ground"
                    >
                      Update Structure
                    </button>
                  </Can>
                ),
              },
            ]}
            rows={employees}
            loading={employeesQuery.isLoading}
            error={employeesQuery.error}
            empty="No staff records found."
          />
        </Card>
      )}

      {/* TAB 3: SALARY COMPONENTS CONFIGURATION */}
      {activeTab === "components" && (
        <Card title="School-wide Salary Components Configuration">
          <p className="text-xs text-ink-faint mb-4">
            Zero hardcoded rates: edit calculation percentages, allowances and statutory deduction rates for your school.
          </p>
          <DataTable<ComponentItem>
            columns={[
              {
                key: "sequence",
                header: "Seq",
                render: (c) => <span className="tabular font-mono text-xs">{c.sequence}</span>,
              },
              {
                key: "code",
                header: "Code",
                render: (c) => <span className="font-mono font-bold text-ink">{c.code}</span>,
              },
              {
                key: "name",
                header: "Component Name",
                render: (c) => <span className="font-medium text-ink">{c.name}</span>,
              },
              {
                key: "type",
                header: "Type",
                render: (c) => (
                  <span
                    className={`text-xs px-2 py-0.5 rounded-pill font-medium ${
                      c.type === "earning"
                        ? "bg-success/10 text-success"
                        : c.type === "deduction"
                        ? "bg-danger/10 text-danger"
                        : "bg-ink-faint/10 text-ink-soft"
                    }`}
                  >
                    {c.type}
                  </span>
                ),
              },
              {
                key: "calculation",
                header: "Calculation Method",
                render: (c) => <span className="text-xs font-mono">{c.calculation}</span>,
              },
              {
                key: "value",
                header: "Value / Rate",
                align: "right",
                render: (c) => (
                  <span className="tabular font-bold">
                    {c.calculation.includes("percent") ? `${c.value}%` : money(c.value)}
                  </span>
                ),
              },
              {
                key: "statutory",
                header: "Statutory",
                render: (c) => (
                  <span className="text-xs">{c.statutory ? "✓ Statutory" : "—"}</span>
                ),
              },
              {
                key: "active",
                header: "Status",
                render: (c) => (
                  <span
                    className={`inline-block w-2.5 h-2.5 rounded-full ${
                      c.active ? "bg-success" : "bg-rule"
                    }`}
                    title={c.active ? "Active" : "Disabled"}
                  />
                ),
              },
              {
                key: "actions",
                header: "",
                align: "right",
                render: (c) => (
                  <Can permission="payroll.setup.manage">
                    <button
                      onClick={() => {
                        setEditingComponent(c);
                        setCompValue(c.value);
                        setCompActive(c.active);
                      }}
                      className="rounded border border-rule px-2.5 py-1 text-xs font-medium hover:bg-ground"
                    >
                      Edit
                    </button>
                  </Can>
                ),
              },
            ]}
            rows={components}
            loading={componentsQuery.isLoading}
            error={componentsQuery.error}
            empty="No salary components configured."
          />
        </Card>
      )}

      {/* MODAL: OPEN RUN */}
      {showOpenRunModal && (
        <Modal title="Open New Payroll Run" onClose={() => setShowOpenRunModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              openRunMutation.mutate({
                year: Number(runYear),
                month: Number(runMonth),
                supplementary: runSupplementary,
              });
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Year">
                <input
                  type="number"
                  min="2000"
                  max="2100"
                  value={runYear}
                  onChange={(e) => setRunYear(Number(e.target.value))}
                  className={inputClass}
                  required
                />
              </FormField>
              <FormField label="Month">
                <select
                  value={runMonth}
                  onChange={(e) => setRunMonth(Number(e.target.value))}
                  className={inputClass}
                  required
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>
                      {new Date(2000, m - 1, 1).toLocaleString("default", { month: "long" })} ({m})
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
              <input
                type="checkbox"
                checked={runSupplementary}
                onChange={(e) => setRunSupplementary(e.target.checked)}
                className="rounded border-rule"
              />
              <span>Supplementary run (corrections/arrears for an already approved month)</span>
            </label>
            <FormError error={openRunMutation.error} />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowOpenRunModal(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={openRunMutation.isPending}
                className="rounded-input bg-primary text-white px-4 py-2 text-sm font-medium hover:bg-primary-hover disabled:opacity-50"
              >
                {openRunMutation.isPending ? "Opening..." : "Create Run"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL: SET SALARY STRUCTURE */}
      {showStructureModal && (
        <Modal title="Set Staff Salary Structure" onClose={() => setShowStructureModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const overrides: Record<string, string> = {};
              if (structTdsOverride.trim()) {
                overrides["TDS"] = structTdsOverride.trim();
              }
              setStructureMutation.mutate({
                employee_id: Number(structEmployeeId),
                monthly_gross: structGross,
                effective_from: structEffective,
                overrides: Object.keys(overrides).length > 0 ? overrides : undefined,
                note: structNote.trim() || undefined,
              });
            }}
            className="space-y-4"
          >
            <FormField label="Staff Member">
              <select
                value={structEmployeeId}
                onChange={(e) => setStructEmployeeId(Number(e.target.value))}
                className={inputClass}
                required
              >
                <option value="">Select an employee...</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name} ({e.employee_code}) — {e.department || "Staff"}
                  </option>
                ))}
              </select>
            </FormField>

            <div className="grid grid-cols-2 gap-4">
              <FormField label="Monthly Gross Salary (₹)">
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 45000"
                  value={structGross}
                  onChange={(e) => setStructGross(e.target.value)}
                  className={inputClass}
                  required
                />
              </FormField>
              <FormField label="Effective From Date">
                <input
                  type="date"
                  value={structEffective}
                  onChange={(e) => setStructEffective(e.target.value)}
                  className={inputClass}
                  required
                />
              </FormField>
            </div>

            <FormField label="Monthly TDS Deduction Override (₹, optional)">
              <input
                type="number"
                step="0.01"
                placeholder="e.g. 2500 (fixed monthly TDS)"
                value={structTdsOverride}
                onChange={(e) => setStructTdsOverride(e.target.value)}
                className={inputClass}
              />
            </FormField>

            <FormField label="Notes / Order Reference (optional)">
              <input
                type="text"
                placeholder="e.g. Annual increment or appointment terms"
                value={structNote}
                onChange={(e) => setStructNote(e.target.value)}
                className={inputClass}
              />
            </FormField>

            <FormError error={setStructureMutation.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowStructureModal(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={setStructureMutation.isPending}
                className="rounded-input bg-primary text-white px-4 py-2 text-sm font-medium hover:bg-primary-hover disabled:opacity-50"
              >
                {setStructureMutation.isPending ? "Saving..." : "Save Salary Terms"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL: EDIT SALARY COMPONENT */}
      {editingComponent && (
        <Modal
          title={`Edit Salary Component: ${editingComponent.name} (${editingComponent.code})`}
          onClose={() => setEditingComponent(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateComponentMutation.mutate({
                id: editingComponent.id,
                body: {
                  value: compValue,
                  active: compActive,
                },
              });
            }}
            className="space-y-4"
          >
            <div className="bg-ground p-3 rounded text-xs space-y-1">
              <p>
                <span className="font-semibold">Calculation Method:</span> {editingComponent.calculation}
              </p>
              <p>
                <span className="font-semibold">Statutory:</span> {editingComponent.statutory ? "Yes" : "No"}
              </p>
            </div>

            <FormField label={editingComponent.calculation.includes("percent") ? "Percentage Rate (%)" : "Fixed Amount (₹)"}>
              <input
                type="number"
                step="0.01"
                value={compValue}
                onChange={(e) => setCompValue(e.target.value)}
                className={inputClass}
                required
              />
            </FormField>

            <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
              <input
                type="checkbox"
                checked={compActive}
                onChange={(e) => setCompActive(e.target.checked)}
                className="rounded border-rule"
              />
              <span>Component is actively applied to salary computations</span>
            </label>

            <FormError error={updateComponentMutation.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditingComponent(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateComponentMutation.isPending}
                className="rounded-input bg-primary text-white px-4 py-2 text-sm font-medium hover:bg-primary-hover disabled:opacity-50"
              >
                {updateComponentMutation.isPending ? "Updating..." : "Save Rate"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL: APPROVE RUN NOTE */}
      {approvingRunId && (
        <Modal title="Approve Payroll Run" onClose={() => setApprovingRunId(null)}>
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              Approving this payroll run locks calculations and makes all payslips final and immutable (§5.3.9).
              Subsequent adjustments require a supplementary run.
            </p>
            <FormField label="Approval Note (optional)">
              <textarea
                rows={2}
                value={approvalNote}
                onChange={(e) => setApprovalNote(e.target.value)}
                placeholder="e.g. Verified against attendance registers and biometric logs"
                className={inputClass}
              />
            </FormField>
            <FormError error={approveMutation.error} />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setApprovingRunId(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  approveMutation.mutate({ runId: approvingRunId, note: approvalNote })
                }
                disabled={approveMutation.isPending}
                className="rounded-input bg-purple-600 text-white px-4 py-2 text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
              >
                {approveMutation.isPending ? "Approving..." : "Confirm Approval"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* MODAL: DISCARD RUN WITH REASON */}
      {discardingRunId && (
        <ConfirmDialog
          title="Discard Payroll Run"
          intent="Are you sure you want to discard this payroll run? All draft/calculated payslips will be discarded."
          confirmLabel="Discard Run"
          busy={discardMutation.isPending}
          error={discardMutation.error}
          onConfirm={(reason) => discardMutation.mutate({ runId: discardingRunId, reason })}
          onClose={() => setDiscardingRunId(null)}
        />
      )}

      {/* MODAL: VIEW / PRINT PAYSLIP */}
      {viewingPayslip && (
        <Modal title="Teacher / Staff Payslip" onClose={() => setViewingPayslip(null)} wide>
          <div className="space-y-6 print:space-y-4" id="printable-payslip">
            {/* Header */}
            <div className="border-b border-rule pb-4 text-center">
              <h2 className="text-xl font-bold text-ink">Sunrise Public School</h2>
              <p className="text-xs text-ink-faint">Sector 14, Indira Nagar, Lucknow, Uttar Pradesh · CBSE Affiliation #2130890</p>
              <div className="mt-2 inline-block bg-primary/10 text-primary px-3 py-0.5 rounded-full text-xs font-semibold">
                SALARY PAYSLIP — {viewingPayslip.month} (Run #{viewingPayslip.run_no})
              </div>
            </div>

            {/* Profile Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs bg-ground p-4 rounded-card border border-rule">
              <div>
                <p className="text-ink-faint">Employee Code</p>
                <p className="font-bold text-ink font-mono mt-0.5">{viewingPayslip.employee_code}</p>
              </div>
              <div>
                <p className="text-ink-faint">Employee Name</p>
                <p className="font-bold text-ink mt-0.5">{viewingPayslip.name}</p>
              </div>
              <div>
                <p className="text-ink-faint">Payslip Number</p>
                <p className="font-bold text-ink font-mono mt-0.5">{viewingPayslip.payslip_no}</p>
              </div>
              <div>
                <p className="text-ink-faint">Status</p>
                <Pill status={viewingPayslip.status}>{viewingPayslip.status}</Pill>
              </div>
              <div>
                <p className="text-ink-faint">Working Days</p>
                <p className="font-semibold text-ink mt-0.5">{viewingPayslip.working_days} Days</p>
              </div>
              <div>
                <p className="text-ink-faint">Loss of Pay (LOP)</p>
                <p className="font-semibold text-danger mt-0.5">{viewingPayslip.lop_days} Days</p>
              </div>
              <div>
                <p className="text-ink-faint">Monthly Gross Target</p>
                <p className="font-semibold text-ink mt-0.5">{money(viewingPayslip.monthly_gross)}</p>
              </div>
              <div>
                <p className="text-ink-faint">Employer Cost (CTC)</p>
                <p className="font-semibold text-ink mt-0.5">{money(viewingPayslip.employer_cost)}</p>
              </div>
            </div>

            {/* Two-column Earnings vs Deductions Table */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Earnings */}
              <div className="border border-rule rounded-card overflow-hidden">
                <div className="bg-success/10 px-4 py-2 text-xs font-bold text-success uppercase tracking-wider">
                  Earnings
                </div>
                <table className="w-full text-xs">
                  <tbody>
                    {viewingPayslip.lines
                      .filter((l) => l.type === "earning")
                      .map((l, i) => (
                        <tr key={i} className="border-b border-rule last:border-0">
                          <td className="px-4 py-2 font-medium text-ink">{l.name}</td>
                          <td className="px-4 py-2 text-right font-mono tabular">{money(l.amount)}</td>
                        </tr>
                      ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-ground font-bold text-ink border-t border-rule">
                      <td className="px-4 py-2.5">Total Earnings</td>
                      <td className="px-4 py-2.5 text-right font-mono tabular text-success">
                        {money(viewingPayslip.total_earnings)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {/* Deductions */}
              <div className="border border-rule rounded-card overflow-hidden">
                <div className="bg-danger/10 px-4 py-2 text-xs font-bold text-danger uppercase tracking-wider">
                  Deductions
                </div>
                <table className="w-full text-xs">
                  <tbody>
                    {viewingPayslip.lines
                      .filter((l) => l.type === "deduction")
                      .map((l, i) => (
                        <tr key={i} className="border-b border-rule last:border-0">
                          <td className="px-4 py-2 font-medium text-ink">{l.name}</td>
                          <td className="px-4 py-2 text-right font-mono tabular text-danger">{money(l.amount)}</td>
                        </tr>
                      ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-ground font-bold text-ink border-t border-rule">
                      <td className="px-4 py-2.5">Total Deductions</td>
                      <td className="px-4 py-2.5 text-right font-mono tabular text-danger">
                        {money(viewingPayslip.total_deductions)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Net Salary Banner */}
            <div className="flex items-center justify-between p-4 bg-primary/10 border border-primary/20 rounded-card">
              <div>
                <p className="text-xs font-semibold text-primary uppercase">Net Salary Payable</p>
                <p className="text-xs text-ink-faint mt-0.5">Credited directly to employee bank account</p>
              </div>
              <div className="text-2xl font-bold font-mono text-primary tabular">
                {money(viewingPayslip.net_pay)}
              </div>
            </div>

            {/* Footer with Signatures & Print */}
            <div className="flex justify-between items-end pt-8 text-xs text-ink-faint">
              <div className="border-t border-rule pt-2 w-48 text-center">
                Accountant Signature
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="rounded-input bg-ink text-white px-4 py-2 text-sm font-medium hover:bg-ink-soft transition-colors"
                >
                  🖨️ Print Payslip
                </button>
                <button
                  type="button"
                  onClick={() => setViewingPayslip(null)}
                  className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
                >
                  Close
                </button>
              </div>
              <div className="border-t border-rule pt-2 w-48 text-center">
                Principal / Authorized Signatory
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
