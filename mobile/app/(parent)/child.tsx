import { useQuery } from "@tanstack/react-query";
import { Text } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Loading, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";

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
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ["child-profile", selectedChildId],
    queryFn: () => api.get<Profile>(`/parent/children/${selectedChildId}/profile`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  const show = (v: unknown) => (v === null || v === undefined || v === "" ? "-" : String(v));

  return (
    <Screen>
      <Card title={t("child_details")}>
        {(
          [
            [t("prof_name"), data.full_name],
            [t("child_admission_no"), data.admission_no],
            [t("child_class"), data.class_label],
            [t("child_roll_no"), data.roll_no],
            [t("child_dob"), data.dob],
            [t("child_gender"), data.gender],
            [t("prof_address"), data.address],
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

      <Card title="Class Teacher">
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
