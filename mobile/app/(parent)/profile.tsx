import { ProfileScreen } from "../../src/components/ProfileScreen";

export default function ParentProfile() {
  return (
    <ProfileScreen
      path="/parent/profile"
      fields={[
        ["Name", "full_name"],
        ["Mobile", "phone"],
        ["Occupation", "occupation"],
        ["Children", "children_names"],
      ]}
    />
  );
}
