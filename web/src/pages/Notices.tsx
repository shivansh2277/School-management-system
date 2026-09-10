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

type Notice = { id: number; title: string };

// `as const` so the state below is the union the API accepts rather than
// `string`: the typed request body catches a value this list does not hold.
const AUDIENCES = ["all", "students", "parents", "teachers", "class"] as const;
type Audience = (typeof AUDIENCES)[number];

export function Notices() {
  const classes = useClasses();
  const [deleting, setDeleting] = useState<Notice | null>(null);
  const [form, setForm] = useState({
    title: "",
    body: "",
    audience: "all" as Audience,
    class_section_id: "",
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
      }),
    invalidates: [["notices"]],
    onDone: () => setForm({ title: "", body: "", audience: "all", class_section_id: "" }),
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
            <input className={inputClass} value={form.title} onChange={set("title")} />
          </FormField>
          <FormField label="Body" error={publish.fields.body}>
            <textarea className={inputClass} rows={3} value={form.body} onChange={set("body")} />
          </FormField>
          <div className="grid grid-cols-2 gap-3">
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
              <FormField label="Class">
                <select
                  className={inputClass}
                  value={form.class_section_id}
                  onChange={set("class_section_id")}
                >
                  <option value="">Select</option>
                  {classes.data?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.class_label}
                    </option>
                  ))}
                </select>
              </FormField>
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

      <Card title="Published notices">
        <DataTable
          rows={list.data ?? []}
          loading={list.isLoading}
          error={list.error}
          empty="Nothing published yet."
          columns={[
            { key: "title", header: "Title", render: (n) => n.title },
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
