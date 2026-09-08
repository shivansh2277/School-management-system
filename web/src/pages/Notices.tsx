import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, FormField, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

const AUDIENCES = ["all", "students", "parents", "teachers", "class"];

export function Notices() {
  const qc = useQueryClient();
  const classes = useClasses();
  const [form, setForm] = useState({ title: "", body: "", audience: "all", class_section_id: "" });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const list = useQuery({
    queryKey: ["notices"],
    queryFn: () => api.get("/admin/notices"),
  });

  const publish = useMutation({
    mutationFn: () =>
      api.post("/admin/notices", {
        title: form.title,
        body: form.body,
        audience: form.audience,
        class_section_id: form.audience === "class" ? Number(form.class_section_id) : null,
      }),
    onSuccess: () => {
      setForm({ title: "", body: "", audience: "all", class_section_id: "" });
      qc.invalidateQueries({ queryKey: ["notices"] });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.del(`/admin/notices/${id}` as "/admin/notices/{notice_id}"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notices"] }),
  });

  return (
    <>
      <Card title="Compose notice">
        <div className="space-y-3">
          <FormField label="Title">
            <input className={inputClass} value={form.title} onChange={set("title")} />
          </FormField>
          <FormField label="Body">
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
          {publish.isError && (
            <p className="text-sm text-danger">{(publish.error as Error).message}</p>
          )}
          <button
            onClick={() => publish.mutate()}
            disabled={publish.isPending || !form.title || !form.body}
            className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
          >
            Publish
          </button>
        </div>
      </Card>

      <Card title="Published notices">
        <DataTable
          rows={list.data ?? []}
          loading={list.isLoading}
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
                <button
                  onClick={() => remove.mutate(n.id)}
                  className="text-danger text-xs hover:underline"
                >
                  Delete
                </button>
              ),
            },
          ]}
        />
      </Card>
    </>
  );
}
