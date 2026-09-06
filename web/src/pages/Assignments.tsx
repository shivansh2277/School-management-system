import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, Modal, Pill } from "../components/ui";

type Row = {
  id: number;
  title: string;
  subject: string;
  class_label: string;
  teacher: string;
  due_date: string;
  submitted_count: number;
  total_students: number;
};

type SubmissionRow = {
  student_id: number;
  full_name: string;
  roll_no: number;
  submitted: boolean;
  late: boolean;
};

export function Assignments() {
  // Homework is created by teachers; the admin view is a read-only roll-up.
  const { data, isLoading } = useQuery({
    queryKey: ["all-homework"],
    queryFn: () => api.get<Row[]>("/admin/assignments"),
  });
  const [open, setOpen] = useState<Row | null>(null);

  return (
    <>
      <Card title="Assignments">
        <DataTable<Row>
          rows={data ?? []}
          loading={isLoading}
          onRowClick={setOpen}
          empty="No homework has been assigned yet."
          columns={[
            { key: "title", header: "Title", render: (r) => r.title },
            { key: "sub", header: "Subject", render: (r) => r.subject },
            { key: "class", header: "Class", render: (r) => r.class_label },
            { key: "t", header: "Teacher", render: (r) => r.teacher },
            { key: "due", header: "Due", render: (r) => r.due_date },
            {
              key: "count",
              header: "Submitted",
              align: "right",
              render: (r) => `${r.submitted_count} / ${r.total_students}`,
            },
          ]}
        />
      </Card>
      {open && <Submissions row={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function Submissions({ row, onClose }: { row: Row; onClose: () => void }) {
  const { data } = useQuery({
    queryKey: ["assignment-subs", row.id],
    queryFn: () => api.get<SubmissionRow[]>(`/admin/assignments/${row.id}/submissions`),
  });

  return (
    <Modal title={row.title} onClose={onClose}>
      <p className="text-sm text-ink-soft mb-4">
        {row.subject} - {row.class_label} - due {row.due_date}
      </p>
      <DataTable<SubmissionRow>
        rows={data ?? []}
        empty="No students in this section."
        columns={[
          { key: "roll", header: "Roll", render: (r) => r.roll_no },
          { key: "name", header: "Name", render: (r) => r.full_name },
          {
            key: "status",
            header: "Status",
            render: (r) =>
              r.submitted ? (
                <Pill status={r.late ? "pending" : "present"}>
                  {r.late ? "Submitted (late)" : "Submitted"}
                </Pill>
              ) : (
                <Pill status="absent">Not submitted</Pill>
              ),
          },
        ]}
      />
    </Modal>
  );
}
