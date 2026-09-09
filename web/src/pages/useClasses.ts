import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

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

/**
 * The class list, from `/admin/classes` - `academics.class.read`, no module.
 *
 * Five screens use this and only some of them need it to function. On
 * /classes, /attendance and /exams it is load-bearing and those screens
 * declare the permission in the registry. On /students and /notices it fills
 * an optional filter or a target picker, and declaring it there would take the
 * whole student roster away from a fee collector and the whole notices screen
 * from a receptionist - neither of whom holds `academics.class.read`, and both
 * of whom need the screen. So the hook returns nothing rather than 403ing, and
 * those two pickers degrade to their "all classes" option.
 */
export function useClasses() {
  const { can } = useAuth();
  return useQuery({
    queryKey: ["classes"],
    // /admin/classes has no response_model in the schema; ClassRow documents
    // the real shape.
    queryFn: () => api.get("/admin/classes") as Promise<ClassRow[]>,
    enabled: can("academics.class.read"),
  });
}
