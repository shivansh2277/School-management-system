import { useAuth } from "../../src/auth/AuthContext";
import { AttendanceView } from "../../src/components/views";
import { Loading } from "../../src/components/ui";

export default function ParentAttendance() {
  const { selectedChildId } = useAuth();
  if (!selectedChildId) return <Loading />;
  return <AttendanceView path={`/parent/children/${selectedChildId}/attendance`} />;
}
