import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import { Linking, Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Loading, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

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

  const initials = (data.full_name || "Child")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <Screen>
      {/* Student Identity Hero Card */}
      <Card>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 28,
              backgroundColor: theme.primarySoft,
              alignItems: "center",
              justifyContent: "center",
              borderWidth: 2,
              borderColor: theme.primary,
            }}
          >
            <Text style={{ fontSize: 20, fontWeight: "800", color: theme.primary }}>{initials}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink }}>{data.full_name}</Text>
            <View style={{ flexDirection: "row", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.primarySoft,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                  Class {data.class_label}
                </Text>
              </View>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.ground,
                  borderWidth: 1,
                  borderColor: theme.rule,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft }}>
                  Roll #{data.roll_no}
                </Text>
              </View>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.ground,
                  borderWidth: 1,
                  borderColor: theme.rule,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkFaint }}>
                  Adm #{data.admission_no}
                </Text>
              </View>
            </View>
          </View>
        </View>
      </Card>

      {/* Class Teacher Card */}
      <Card title="Designated Class Teacher">
        {data.class_teacher ? (
          <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
              <View
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 20,
                  backgroundColor: theme.primarySoft,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Ionicons name="person" size={20} color={theme.primary} />
              </View>
              <View>
                <Text style={[s.title, { fontSize: 14, color: theme.ink }]}>{data.class_teacher.full_name}</Text>
                <Text style={[s.meta, { fontSize: 12 }]}>{show(data.class_teacher.phone)}</Text>
              </View>
            </View>

            {data.class_teacher.phone ? (
              <Pressable
                onPress={() => Linking.openURL(`tel:${data.class_teacher!.phone}`)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: 4,
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.primarySoft,
                }}
              >
                <Ionicons name="call" size={14} color={theme.primary} />
                <Text style={{ fontSize: 12, fontWeight: "700", color: theme.primary }}>Call</Text>
              </Pressable>
            ) : null}
          </View>
        ) : (
          <Text style={s.meta}>No class teacher assigned.</Text>
        )}
      </Card>

      {/* Academic Details Card */}
      <Card title={t("child_details")}>
        {[
          [t("prof_name"), data.full_name],
          [t("child_admission_no"), data.admission_no],
          [t("child_class"), data.class_label],
          [t("child_roll_no"), data.roll_no],
          [t("child_dob"), data.dob],
          [t("child_gender"), data.gender],
          [t("prof_address"), data.address],
          ["Admitted On", data.admission_date],
        ].map(([label, value]) => (
          <Row
            key={String(label)}
            left={<Text style={s.meta}>{label}</Text>}
            right={<Text style={[s.title, { fontSize: 13 }]}>{show(value)}</Text>}
          />
        ))}
      </Card>
    </Screen>
  );
}
