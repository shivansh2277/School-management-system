import { ProfileScreen } from "../../src/components/ProfileScreen";

export default function TeacherProfile() {
  return (
    <ProfileScreen
      path="/teacher/profile"
      fields={[
        ["Name", "full_name"],
        ["Employee ID", "employee_id"],
        ["Qualification", "qualification"],
        ["Subjects", "subjects"],
        ["Sections", "sections"],
        ["Class teacher of", "class_teacher_of"],
      ]}
    />
  );
}
