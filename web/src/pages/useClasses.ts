import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

export type ClassRow = {
  id: number;
  class_name: string;
  section: string;
  class_label: string;
  academic_year: string;
  class_teacher_id: number | null;
  class_teacher: string | null;
  student_count: number;
  subjects: string[];
};

export function useClasses() {
  return useQuery({
    queryKey: ["classes"],
    // /admin/classes has no response_model in the schema; ClassRow documents
    // the real shape.
    queryFn: () => api.get("/admin/classes") as Promise<ClassRow[]>,
  });
}
