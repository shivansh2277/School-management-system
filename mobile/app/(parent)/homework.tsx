import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Pill, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

type Item = {
  id: number;
  title: string;
  subject: string;
  due_date: string;
  submitted: boolean;
  late: boolean;
};

export default function ParentHomework() {
  const { t } = useTranslation();
  const { selectedChildId } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["parent-homework", selectedChildId],
    queryFn: () => api.get<Item[]>(`/parent/children/${selectedChildId}/homework`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  const submitted = data.filter((h) => h.submitted).length;
  const pending = data.length - submitted;

  return (
    <Screen>
      {/* 2-Metric Summary Card */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-around", alignItems: "center" }}>
          <View style={{ alignItems: "center", flex: 1 }}>
            <Text style={{ fontSize: 11, fontWeight: "600", color: theme.success, textTransform: "uppercase" }}>
              {t("hw_submitted")}
            </Text>
            <Text style={{ fontSize: 24, fontWeight: "800", color: theme.success, marginTop: 2 }}>{submitted}</Text>
          </View>
          <View style={{ width: 1, height: 32, backgroundColor: theme.rule }} />
          <View style={{ alignItems: "center", flex: 1 }}>
            <Text style={{ fontSize: 11, fontWeight: "600", color: pending > 0 ? theme.warning : theme.inkFaint, textTransform: "uppercase" }}>
              {t("hw_pending")}
            </Text>
            <Text style={{ fontSize: 24, fontWeight: "800", color: pending > 0 ? theme.warning : theme.ink, marginTop: 2 }}>
              {pending}
            </Text>
          </View>
        </View>
        <Text style={[s.meta, { textAlign: "center", marginTop: 8, fontSize: 11 }]}>{t("hw_readonly_note")}</Text>
      </Card>

      <Card title={t("hw_assignments")}>
        {data.length === 0 ? (
          <Empty text={t("hw_no_homework")} />
        ) : (
          data.map((item) => (
            <View
              key={item.id}
              style={{
                paddingVertical: 12,
                borderBottomWidth: 1,
                borderBottomColor: theme.rule,
              }}
            >
              <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <View
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                    borderRadius: theme.radius.pill,
                    backgroundColor: theme.primarySoft,
                  }}
                >
                  <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>{item.subject}</Text>
                </View>
                <Text style={{ fontSize: 11, color: theme.inkFaint }}>{t("hw_due")} {formatDate(item.due_date)}</Text>
              </View>

              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <Text style={[s.title, { fontSize: 14, color: theme.ink, flex: 1 }]}>{item.title}</Text>
                {item.submitted ? (
                  <Pill status="submitted" label={item.late ? t("hw_late") : t("hw_submitted")} />
                ) : (
                  <Pill status="pending" label={t("hw_pending")} />
                )}
              </View>
            </View>
          ))
        )}
      </Card>
    </Screen>
  );
}
