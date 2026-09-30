import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { useWrite } from "../api/useWrite";
import { ActionButton } from "../components/Can";
import { Card, ConfirmDialog, DataTable, FormError, FormField, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

// Both writes on this screen need the same permission: publishing a notice and
// taking one off the board are the same authority, read off
// api/admin/notices.py, where POST and DELETE both depend on it.
const PUBLISH = "comms.notice.publish";

type Notice = {
  id: number;
  title: string;
  body?: string;
  audience: string;
  class_label?: string | null;
  published_by: string;
  published_at: string;
  category?: string;
  is_public?: boolean;
  is_pinned?: boolean;
  summary?: string | null;
};

// `as const` so the state below is the union the API accepts rather than
// `string`: the typed request body catches a value this list does not hold.
const AUDIENCES = ["all", "students", "parents", "teachers", "class"] as const;
type Audience = (typeof AUDIENCES)[number];

const CATEGORIES = [
  "Notice",
  "Admission",
  "Academic",
  "Event",
  "Holiday",
  "Achievement",
  "General",
] as const;
type Category = (typeof CATEGORIES)[number];

export function Notices() {
  const classes = useClasses();
  const [deleting, setDeleting] = useState<Notice | null>(null);
  const [form, setForm] = useState({
    title: "",
    summary: "",
    body: "",
    audience: "all" as Audience,
    class_section_id: "",
    category: "General" as Category,
    is_public: false,
    is_pinned: false,
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const list = useQuery({
    queryKey: ["notices"],
    queryFn: () => api.get("/admin/notices"),
  });

  const publish = useWrite({
    write: () =>
      api.post("/admin/notices", {
        title: form.title,
        body: form.body,
        audience: form.audience,
        class_section_id: form.audience === "class" ? Number(form.class_section_id) : null,
        category: form.category,
        is_public: form.is_public,
        is_pinned: form.is_pinned,
        summary: form.summary.trim() ? form.summary.trim() : null,
      }),
    invalidates: [["notices"]],
    onDone: () =>
      setForm({
        title: "",
        summary: "",
        body: "",
        audience: "all",
        class_section_id: "",
        category: "General",
        is_public: false,
        is_pinned: false,
      }),
  });

  const remove = useWrite<string>({
    write: (reason: string) =>
      api.del(
        `/admin/notices/${deleting!.id}` as "/admin/notices/{notice_id}",
        `?reason=${encodeURIComponent(reason)}`,
      ),
    invalidates: [["notices"]],
    onDone: () => setDeleting(null),
  });

  return (
    <>
      <Card title="Compose notice">
        <div className="space-y-3">
          <FormField label="Title" error={publish.fields.title}>
            <input
              className={inputClass}
              value={form.title}
              onChange={set("title")}
              placeholder="e.g. Admissions Open for Academic Session 2026-27"
            />
          </FormField>

          <FormField label="Short Summary (Optional for website banner & cards)">
            <input
              className={inputClass}
              value={form.summary}
              onChange={set("summary")}
              placeholder="1-sentence executive summary displayed in public cards & news ticker"
            />
          </FormField>

          <FormField label="Full Notice / Announcement Content" error={publish.fields.body}>
            <textarea
              className={inputClass}
              rows={4}
              value={form.body}
              onChange={set("body")}
              placeholder="Provide complete details, dates, venue, and instructions..."
            />
          </FormField>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <FormField label="Category">
              <select className={inputClass} value={form.category} onChange={set("category")}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Audience">
              <select className={inputClass} value={form.audience} onChange={set("audience")}>
                {AUDIENCES.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </FormField>

            {form.audience === "class" && (
              <FormField label="Class Section">
                <select
                  className={inputClass}
                  value={form.class_section_id}
                  onChange={set("class_section_id")}
                >
                  <option value="">Select section</option>
                  {classes.data?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.class_label}
                    </option>
                  ))}
                </select>
              </FormField>
            )}
          </div>

          {/* Public Website Publishing Options */}
          <div className="rounded-input border border-rule bg-surface p-3 space-y-2">
            <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-ink select-none">
              <input
                type="checkbox"
                className="rounded border-rule text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                checked={form.is_public}
                onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
              />
              <span>Publish to Public School Website</span>
              <span className="text-xs text-ink-soft font-normal">
                (Visible to prospective parents & public visitors on the website)
              </span>
            </label>

            {form.is_public && (
              <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-ink select-none pl-6">
                <input
                  type="checkbox"
                  className="rounded border-rule text-amber-500 focus:ring-amber-500 w-4 h-4 cursor-pointer"
                  checked={form.is_pinned}
                  onChange={(e) => setForm({ ...form, is_pinned: e.target.checked })}
                />
                <span className="text-amber-800">Pin as Featured Announcement (Top of website ticker & announcements)</span>
              </label>
            )}
          </div>

          <FormError error={publish.error} />
          <ActionButton
            permission={PUBLISH}
            onClick={() => publish.run()}
            disabled={publish.busy || !form.title || !form.body}
          >
            Publish
          </ActionButton>
        </div>
      </Card>

      <Card title="Published notices & announcements">
        <DataTable
          rows={list.data ?? []}
          loading={list.isLoading}
          error={list.error}
          empty="Nothing published yet."
          columns={[
            {
              key: "title",
              header: "Title & Details",
              render: (n) => (
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-ink text-sm">{n.title}</span>
                    {n.is_pinned && (
                      <span className="rounded-pill bg-amber-100 text-amber-800 border border-amber-300 px-1.5 py-0.2 text-[10px] font-bold">
                        PINNED
                      </span>
                    )}
                  </div>
                  {n.summary && (
                    <p className="text-xs text-ink-soft line-clamp-1">{n.summary}</p>
                  )}
                </div>
              ),
            },
            {
              key: "category",
              header: "Category",
              render: (n) => (
                <span className="rounded-pill bg-slate-100 text-slate-700 px-2 py-0.5 text-xs font-medium">
                  {n.category || "General"}
                </span>
              ),
            },
            {
              key: "visibility",
              header: "Visibility",
              render: (n) =>
                n.is_public ? (
                  <span className="rounded-pill bg-emerald-100 text-emerald-800 px-2 py-0.5 text-xs font-semibold">
                    Public Website
                  </span>
                ) : (
                  <span className="rounded-pill bg-slate-100 text-slate-600 px-2 py-0.5 text-xs">
                    Internal
                  </span>
                ),
            },
            {
              key: "aud",
              header: "Audience",
              render: (n) => (
                <span className="rounded-pill bg-primary-soft text-primary px-2 py-0.5 text-xs">
                  {n.audience}
                  {n.class_label ? ` - ${n.class_label}` : ""}
                </span>
              ),
            },
            { key: "by", header: "By", render: (n) => n.published_by },
            {
              key: "at",
              header: "Published",
              render: (n) => new Date(n.published_at).toLocaleDateString(),
            },
            {
              key: "del",
              header: "",
              render: (n) => (
                <ActionButton
                  permission={PUBLISH}
                  variant="danger"
                  className="!px-3 !py-1 text-xs"
                  onClick={() => setDeleting(n)}
                >
                  Delete
                </ActionButton>
              ),
            },
          ]}
        />
      </Card>

      {deleting && (
        <ConfirmDialog
          title={`Delete "${deleting.title}"`}
          confirmLabel="Delete notice"
          busy={remove.busy}
          error={remove.error}
          intent={
            <p>
              The notice comes off the board for everyone it was published to. The reason is
              recorded in the audit log against your name; the notice itself is not recoverable.
            </p>
          }
          onConfirm={(reason) => remove.run(reason)}
          onClose={() => {
            remove.reset();
            setDeleting(null);
          }}
        />
      )}
    </>
  );
}
