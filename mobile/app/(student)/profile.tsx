import { ProfileScreen } from "../../src/components/ProfileScreen";

export default function StudentProfile() {
  return (
    <ProfileScreen
      path="/student/profile"
      fields={[
        ["Name", "full_name"],
        ["Admission No.", "admission_no"],
        ["Class", "class_label"],
        ["Roll No.", "roll_no"],
        ["Date of birth", "dob"],
        ["Address", "address"],
      ]}
    />
  );
}
