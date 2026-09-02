import { useQuery } from "@tanstack/react-query";
import { Text } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Loading, Row, Screen, s } from "../../src/components/ui";

type Profile = {
  full_name: string;
  admission_no: string;
  class_label: string;
  roll_no: number;
  dob: string | null;
  gender: string | null;
  address: string | null;
  admission_date: string | null;
  class_teacher: { full_name: string; phone: string | null } | null;
};

export default function ChildProfile() {
  const { selectedChildId } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["child-profile", selectedChildId],
    queryFn: () => api.get<Profile>(`/parent/children/${selectedChildId}/profile`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  const show = (v: unknown) => (v === null || v === undefined || v === "" ? "-" : String(v));

  return (
    <Screen>
      <Card title="Student">
        {(
          [
            ["Name", data.full_name],
            ["Admission No.", data.admission_no],
            ["Class", data.class_label],
            ["Roll No.", data.roll_no],
            ["Date of birth", data.dob],
            ["Gender", data.gender],
            ["Address", data.address],
            ["Admitted on", data.admission_date],
          ] as [string, unknown][]
        ).map(([label, value]) => (
          <Row
            key={label}
            left={<Text style={s.meta}>{label}</Text>}
            right={<Text style={s.title}>{show(value)}</Text>}
          />
        ))}
      </Card>

      <Card title="Class teacher">
        {data.class_teacher ? (
          <Row
            left={<Text style={s.title}>{data.class_teacher.full_name}</Text>}
            right={<Text style={s.meta}>{show(data.class_teacher.phone)}</Text>}
          />
        ) : (
          <Text style={s.meta}>No class teacher assigned.</Text>
        )}
      </Card>
    </Screen>
  );
}
