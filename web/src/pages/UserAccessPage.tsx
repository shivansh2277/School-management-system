import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Can } from "../components/Can";
import {
  Card,
  DataTable,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";

export interface UserAccessItem {
  id: number;
  login_id: string;
  role: "admin" | "teacher" | "parent" | "student";
  full_name: string;
  phone: string | null;
  email: string | null;
  is_active: boolean;
  app_access_blocked: boolean;
  token_version: number;
  created_at: string | null;
  identifier: string | null;
  subtext: string | null;
}

export function UserAccessPage() {
  const queryClient = useQueryClient();

  const [roleFilter, setRoleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal states
  const [blockTarget, setBlockTarget] = useState<UserAccessItem | null>(null);
  const [blockReason, setBlockReason] = useState<string>("");

  const [resetTarget, setResetTarget] = useState<UserAccessItem | null>(null);
  const [newPassword, setNewPassword] = useState<string>("");
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Query users
  const { data: users = [], isLoading, error } = useQuery({
    queryKey: ["admin-users-access", roleFilter, statusFilter, searchQuery],
    queryFn: () => {
      const params = new URLSearchParams();
      if (roleFilter) params.append("role", roleFilter);
      if (statusFilter !== "") params.append("blocked", statusFilter === "blocked" ? "true" : "false");
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/users${q}` as any) as Promise<UserAccessItem[]>;
    },
  });

  // Block mutation
  const blockMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: number; reason: string }) =>
      api.post(`/admin/users/${userId}/block` as any, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users-access"] });
      setBlockTarget(null);
      setBlockReason("");
      setFeedbackMsg({ type: "success", text: "Mobile app access blocked successfully. Active sessions invalidated." });
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: "error", text: err?.message || "Failed to block user access." });
    },
  });

  // Unblock mutation
  const unblockMutation = useMutation({
    mutationFn: (userId: number) => api.post(`/admin/users/${userId}/unblock` as any, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users-access"] });
      setFeedbackMsg({ type: "success", text: "Mobile app access unblocked successfully." });
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: "error", text: err?.message || "Failed to unblock user access." });
    },
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: ({ userId, newPassword }: { userId: number; newPassword: string }) =>
      api.post(`/admin/users/${userId}/reset-password` as any, { new_password: newPassword }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users-access"] });
      setResetTarget(null);
      setNewPassword("");
      setFeedbackMsg({
        type: "success",
        text: "Password successfully changed. All existing sessions and tokens have been invalidated.",
      });
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: "error", text: err?.message || "Failed to reset password." });
    },
  });

  // Stats calculation
  const totalUsers = users.length;
  const blockedCount = users.filter((u) => u.app_access_blocked).length;
  const activeCount = totalUsers - blockedCount;
  const teacherCount = users.filter((u) => u.role === "teacher").length;
  const studentCount = users.filter((u) => u.role === "student").length;
  const parentCount = users.filter((u) => u.role === "parent").length;

  const generateRandomPassword = () => {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%";
    let pwd = "";
    for (let i = 0; i < 10; i++) {
      pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setNewPassword(pwd);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">App User Access & Security</h1>
          <p className="text-sm text-ink-faint">
            Manage mobile application access, block/unblock accounts, and securely reset passwords for Teachers, Parents, and Students.
          </p>
        </div>
      </div>

      {/* Feedback banner */}
      {feedbackMsg && (
        <div
          className={`p-3 rounded-lg flex items-center justify-between text-sm ${
            feedbackMsg.type === "success" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          <span>{feedbackMsg.text}</span>
          <button
            type="button"
            onClick={() => setFeedbackMsg(null)}
            className="text-xs font-semibold uppercase hover:underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total App Users" value={totalUsers} />
        <StatCard label="Active Accounts" value={activeCount} />
        <StatCard label="Blocked Accounts" value={blockedCount} />
        <StatCard
          label="Breakdown"
          value={`${teacherCount} T / ${studentCount} S / ${parentCount} P`}
        />
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between bg-surface p-3 rounded-xl border border-rule">
        <div className="flex flex-wrap items-center gap-2">
          {/* Role Filter Tabs */}
          {[
            { key: "", label: "All Roles" },
            { key: "teacher", label: "Teachers" },
            { key: "parent", label: "Parents" },
            { key: "student", label: "Students" },
          ].map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setRoleFilter(tab.key)}
              className={`px-3 py-1.5 rounded-pill text-xs font-semibold transition ${
                roleFilter === tab.key
                  ? "bg-primary text-white shadow-xs"
                  : "bg-ground text-ink-faint hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs rounded-pill border border-rule px-3 py-1.5 bg-ground text-ink font-medium ml-2"
          >
            <option value="">All Statuses</option>
            <option value="active">Active Access Only</option>
            <option value="blocked">Blocked Access Only</option>
          </select>
        </div>

        {/* Search Input */}
        <div className="w-full md:w-72">
          <input
            type="text"
            placeholder="Search by name, login, phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`${inputClass} text-xs py-1.5`}
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        <DataTable<UserAccessItem>
          columns={[
            {
              key: "user",
              header: "User Details",
              render: (row) => (
                <div>
                  <div className="font-semibold text-ink flex items-center gap-2">
                    {row.full_name}
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        row.role === "teacher"
                          ? "bg-purple-100 text-purple-700"
                          : row.role === "student"
                          ? "bg-blue-100 text-blue-700"
                          : row.role === "parent"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {row.role}
                    </span>
                  </div>
                  <div className="text-xs text-ink-faint font-mono mt-0.5">
                    ID: {row.login_id}
                  </div>
                </div>
              ),
            },
            {
              key: "affiliation",
              header: "Designation / Affiliation",
              render: (row) => (
                <div>
                  {row.identifier && (
                    <span className="text-xs font-semibold text-ink block">
                      {row.identifier}
                    </span>
                  )}
                  {row.subtext && (
                    <span className="text-xs text-ink-faint block">{row.subtext}</span>
                  )}
                </div>
              ),
            },
            {
              key: "contact",
              header: "Contact Info",
              render: (row) => (
                <div className="text-xs">
                  <span className="text-ink block">{row.phone || "No phone"}</span>
                  <span className="text-ink-faint block">{row.email || "No email"}</span>
                </div>
              ),
            },
            {
              key: "status",
              header: "App Access Status",
              render: (row) => (
                <div>
                  {row.app_access_blocked ? (
                    <Pill status="danger">BLOCKED</Pill>
                  ) : (
                    <Pill status="active">ACTIVE</Pill>
                  )}
                  <span className="text-[10px] text-ink-faint block mt-1">
                    v{row.token_version} session
                  </span>
                </div>
              ),
            },
            {
              key: "actions",
              header: "Actions",
              align: "right",
              render: (row) => (
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setResetTarget(row);
                      setNewPassword("");
                    }}
                    className="px-2.5 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded transition"
                  >
                    Reset Password
                  </button>

                  {row.app_access_blocked ? (
                    <button
                      type="button"
                      disabled={unblockMutation.isPending}
                      onClick={() => unblockMutation.mutate(row.id)}
                      className="px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition"
                    >
                      {unblockMutation.isPending ? "Unblocking..." : "Unblock App"}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setBlockTarget(row);
                        setBlockReason("");
                      }}
                      className="px-2.5 py-1 text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100 rounded transition"
                    >
                      Block App
                    </button>
                  )}
                </div>
              ),
            },
          ]}
          rows={users}
          empty="No users found matching current filters."
          loading={isLoading}
          error={error}
        />
      </Card>

      {/* Modal: Block User */}
      {blockTarget && (
        <Modal
          title={`Block Mobile App Access: ${blockTarget.full_name}`}
          onClose={() => setBlockTarget(null)}
        >
          <div className="space-y-4">
            <div className="p-3 bg-red-50 rounded-lg text-xs text-red-800 leading-relaxed border border-red-200">
              <span className="font-bold">Security Enforcement: </span>
              Blocking this user will immediately invalidate all active mobile tokens and sessions. The user will be unable to log in or use the mobile app until an administrator explicitly unblocks them.
            </div>

            <FormField label="Reason for Blocking Access (Optional)">
              <textarea
                rows={2}
                placeholder="e.g. Fees overdue, disciplinary inquiry, or parent request..."
                value={blockReason}
                onChange={(e) => setBlockReason(e.target.value)}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setBlockTarget(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={blockMutation.isPending}
                onClick={() => blockMutation.mutate({ userId: blockTarget.id, reason: blockReason })}
                className="px-5 py-2 bg-red-600 text-white text-sm font-semibold rounded-pill hover:bg-red-700 transition"
              >
                {blockMutation.isPending ? "Blocking Access..." : "Confirm & Block Access"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Reset Password */}
      {resetTarget && (
        <Modal
          title={`Reset Password: ${resetTarget.full_name} (${resetTarget.login_id})`}
          onClose={() => setResetTarget(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (newPassword.length < 6) {
                alert("Password must be at least 6 characters long.");
                return;
              }
              resetPasswordMutation.mutate({ userId: resetTarget.id, newPassword });
            }}
            className="space-y-4"
          >
            <div className="p-3 bg-amber-50 rounded-lg text-xs text-amber-800 leading-relaxed border border-amber-200">
              <span className="font-bold">Session Termination: </span>
              Resetting this password will immediately invalidate all current sessions and refresh tokens on all devices. The user must log in using this new password.
            </div>

            <FormField label="New Password">
              <div className="flex gap-2">
                <input
                  type="text"
                  required
                  minLength={6}
                  placeholder="Enter new secure password..."
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={generateRandomPassword}
                  className="px-3 py-2 bg-ground hover:bg-ground-deep border border-rule text-xs font-semibold rounded-pill whitespace-nowrap"
                >
                  Generate
                </button>
              </div>
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setResetTarget(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={resetPasswordMutation.isPending || newPassword.length < 6}
                className="px-5 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-pill hover:bg-indigo-700 transition"
              >
                {resetPasswordMutation.isPending ? "Updating Password..." : "Set New Password"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
