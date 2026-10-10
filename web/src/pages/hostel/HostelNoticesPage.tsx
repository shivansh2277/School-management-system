import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Card, Pill } from "../../components/ui";

type HostelSummary = {
  id: number;
  name: string;
  code: string;
};

type HostelNotice = {
  id: number;
  hostel_id: number | null;
  hostel_name: string;
  title: string;
  content: string;
  priority: string;
  posted_at: string;
  posted_by_name: string;
};

export function HostelNoticesPage() {
  const queryClient = useQueryClient();
  const { can } = useAuth();
  const canManage = can("hostel.notice.manage");
  const isProvost = can("hostel.structure.manage");

  const [selectedHostelId, setSelectedHostelId] = useState<string>("all");
  const [newNoticeModal, setNewNoticeModal] = useState(false);
  const [noticeForm, setNoticeForm] = useState({
    hostel_id: "",
    title: "",
    content: "",
    priority: "normal",
  });

  // Query hostels
  const { data: hostels = [] } = useQuery<HostelSummary[]>({
    queryKey: ["hostel", "list"],
    queryFn: () => api.rawGet<HostelSummary[]>("/admin/hostel/list"),
  });

  // Query notices
  const {
    data: notices = [],
    isLoading,
    error,
  } = useQuery<HostelNotice[]>({
    queryKey: ["hostel", "notices", selectedHostelId],
    queryFn: () =>
      api.rawGet<HostelNotice[]>(
        `/admin/hostel/notices${selectedHostelId !== "all" ? `?hostel_id=${selectedHostelId}` : ""}`,
      ),
  });

  // Create notice mutation
  const createNoticeMutation = useMutation({
    mutationFn: (payload: any) => api.rawPost("/admin/hostel/notices", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostel", "notices"] });
      setNewNoticeModal(false);
      setNoticeForm({ hostel_id: "", title: "", content: "", priority: "normal" });
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel Notice Board</h1>
        <p className="text-ink-soft">Loading notices and announcements...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel Notice Board</h1>
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-card text-danger">
          Failed to load notices. Please check your network connection.
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
            <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Circulars & Notice Board</h1>
            <Pill status="active">Student & Residential Bulletins</Pill>
          </div>
          <p className="text-sm text-ink-soft mt-1">
            Broadcast official circulars, study hour guidelines, gate timing alerts, and dining notifications.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {canManage && (
            <button
              onClick={() => setNewNoticeModal(true)}
              className="px-3 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover shadow-sm"
            >
              + Publish Notice
            </button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-ink-soft uppercase tracking-wider">Scope Filter:</span>
          <select
            value={selectedHostelId}
            onChange={(e) => setSelectedHostelId(e.target.value)}
            className="px-3 py-1.5 text-xs font-medium border border-rule rounded bg-surface text-ink"
          >
            <option value="all">All Hostels & General Notices</option>
            {hostels.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.code})
              </option>
            ))}
          </select>
        </div>

        <span className="text-xs text-ink-soft">{notices.length} active announcements</span>
      </div>

      {/* Notices Feed */}
      <div className="space-y-4">
        {notices.length === 0 ? (
          <Card className="p-8 text-center text-sm text-ink-soft">
            No notices published for this selection.
          </Card>
        ) : (
          notices.map((n) => (
            <Card
              key={n.id}
              className={`p-5 transition hover:shadow-md ${
                n.priority === "urgent"
                  ? "border-l-4 border-l-rose-500 bg-rose-50/20"
                  : n.priority === "high"
                  ? "border-l-4 border-l-amber-500 bg-amber-50/20"
                  : "border-l-4 border-l-primary"
              }`}
            >
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        n.priority === "urgent"
                          ? "bg-rose-100 text-rose-800 border border-rose-200"
                          : n.priority === "high"
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : "bg-surface text-ink-soft border border-rule"
                      }`}
                    >
                      {n.priority}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-ground border border-rule text-ink">
                      {n.hostel_name}
                    </span>
                  </div>

                  <div className="text-xs text-ink-soft">
                    Posted on {new Date(n.posted_at).toLocaleDateString()} at{" "}
                    {new Date(n.posted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>

                <div>
                  <h2 className="text-base font-bold text-ink">{n.title}</h2>
                  <p className="text-sm text-ink-soft mt-1.5 whitespace-pre-line leading-relaxed">
                    {n.content}
                  </p>
                </div>

                <div className="pt-2 border-t border-rule flex items-center justify-between text-xs text-ink-soft">
                  <span>
                    Issued by: <strong className="text-ink font-semibold">{n.posted_by_name}</strong>
                  </span>
                  <span>Visible to Wardens, Parents & Students</span>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* New Notice Modal */}
      {newNoticeModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface border border-rule rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-ink">Broadcast Notice / Announcement</h3>

            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                    Audience Scope *
                  </label>
                  <select
                    value={noticeForm.hostel_id}
                    onChange={(e) => setNoticeForm({ ...noticeForm, hostel_id: e.target.value })}
                    className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                  >
                    {isProvost && <option value="">All Hostels (School-wide)</option>}
                    {hostels.map((h) => (
                      <option key={h.id} value={h.id}>
                        {h.name} Only
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                    Priority *
                  </label>
                  <select
                    value={noticeForm.priority}
                    onChange={(e) => setNoticeForm({ ...noticeForm, priority: e.target.value })}
                    className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Study Hours Routine & Night Attendance Timings"
                  value={noticeForm.title}
                  onChange={(e) => setNoticeForm({ ...noticeForm, title: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Circular Content *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Write notice body..."
                  value={noticeForm.content}
                  onChange={(e) => setNoticeForm({ ...noticeForm, content: e.target.value })}
                  className="w-full px-3 py-2 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setNewNoticeModal(false)}
                className="px-4 py-2 border border-rule rounded text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={
                  !noticeForm.title.trim() ||
                  !noticeForm.content.trim() ||
                  createNoticeMutation.isPending
                }
                onClick={() =>
                  createNoticeMutation.mutate({
                    hostel_id: noticeForm.hostel_id ? Number(noticeForm.hostel_id) : null,
                    title: noticeForm.title,
                    content: noticeForm.content,
                    priority: noticeForm.priority,
                  })
                }
                className="px-4 py-2 bg-primary text-white rounded text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {createNoticeMutation.isPending ? "Broadcasting..." : "Broadcast Notice"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
