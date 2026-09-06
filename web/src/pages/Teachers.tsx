import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { Card, DataTable } from "../components/ui";

type Row = {
  id: number;
  employee_code: string;
  full_name: string;
  qualification: string | null;
  subjects: string[];
  sections: string[];
  class_teacher_of: string[];
};

export function Teachers() {
  const { data, isLoading } = useQuery({
    queryKey: ["teachers"],
    queryFn: () => api.get<Row[]>("/admin/teachers"),
  });

  return (
    <Card title="Teachers">
      <DataTable<Row>
        rows={data ?? []}
          loading={isLoading}
        empty="No teachers on record."
        columns={[
          { key: "emp", header: "Employee ID", render: (r) => r.employee_code },
          { key: "name", header: "Name", render: (r) => r.full_name },
          { key: "qual", header: "Qualification", render: (r) => r.qualification ?? "-" },
          { key: "subj", header: "Subjects", render: (r) => r.subjects.join(", ") || "-" },
          { key: "sec", header: "Sections", render: (r) => r.sections.join(", ") || "-" },
          {
            key: "ct",
            header: "Class teacher of",
            render: (r) => r.class_teacher_of.join(", ") || "-",
          },
        ]}
      />
    </Card>
  );
}
