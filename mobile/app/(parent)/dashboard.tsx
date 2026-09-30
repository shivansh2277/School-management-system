import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AlertItem, ImportantAlerts } from "../../src/components/ImportantAlerts";
import { Card, Empty, Loading, Row, Screen, Stat, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

type Summary = {
  name: string;
  class_label: string;
  attendance_percent: number | null;
  homework_submitted: number;
  homework_pending: number;
  latest_result_percent: number | null;
  fee_dues: number;
  fee_due_amount?: number;
  latest_report_card?: { exam_id: number; title: string } | null;
  latest_periodic_test?: { exam_id: number; title: string } | null;
  alerts?: AlertItem[];
  recent_notices: { id: number; title: string; published_at: string }[];
};

export default function ParentDashboard() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { selectedChildId, selectChild } = useAuth();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ["parent-summary", selectedChildId],
    queryFn: () => api.get<Summary>(`/parent/children/${selectedChildId}/summary`),
    enabled: selectedChildId !== null,
  });

  const alertsQuery = useQuery({
    queryKey: ["parent-alerts"],
    queryFn: () => api.get<AlertItem[]>("/parent/alerts"),
  });

  if (isLoading || !data) return <Loading />;

  const handleAlertPress = async (alert: AlertItem) => {
    if (alert.child_id) {
      selectChild(alert.child_id);
    }
    // Attendance, report card, and periodic test alerts disappear after viewing.
    // Fee alerts NEVER dismiss by viewing (must remain visible until balance is 0).
    // Multi-child: tracked per child and per alert independently.
    if (alert.type !== "fee" && alert.event_key && alert.child_id) {
      try {
        await api.post("/parent/alerts/view", {
          child_id: alert.child_id,
          alert_type: alert.type,
          event_key: alert.event_key,
          exam_id: alert.exam_id,
        });
        queryClient.invalidateQueries({ queryKey: ["parent-alerts"] });
        queryClient.invalidateQueries({ queryKey: ["parent-summary"] });
      } catch (err) {
        console.warn("Failed to mark alert viewed:", err);
      }
    }
    if (alert.route) {
      router.push(alert.route as any);
    }
  };

  return (
    <Screen>
      <Card>
        <Text style={{ fontSize: 18, fontWeight: "700", color: theme.ink }}>{data.name}</Text>
        <Text style={s.meta}>{t("child_class")} {data.class_label}</Text>
      </Card>

      <ImportantAlerts
        alerts={alertsQuery.data}
        onAlertPress={handleAlertPress}
        sectionTitle={t("dash_important_alerts")}
      />

      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat
            label={t("nav_attendance")}
            value={data.attendance_percent === null ? "-" : `${data.attendance_percent}%`}
          />
          <Stat
            label={t("nav_results")}
            value={data.latest_result_percent === null ? "-" : `${data.latest_result_percent}%`}
          />
          <Stat label={t("dash_pending_fees")} value={data.fee_dues} />
        </View>
      </Card>

      <Card title={t("nav_homework")}>
        <View style={{ flexDirection: "row" }}>
          <Stat label={t("hw_submitted")} value={data.homework_submitted} />
          <Stat label={t("hw_pending")} value={data.homework_pending} />
        </View>
      </Card>

      <Card title={t("dash_recent_notices")}>
        {data.recent_notices.length === 0 ? (
          <Empty text={t("dash_no_notices")} />
        ) : (
          data.recent_notices.map((n) => (
            <Row
              key={n.id}
              left={<Text style={s.title}>{n.title}</Text>}
              right={<Text style={s.meta}>{new Date(n.published_at).toLocaleDateString()}</Text>}
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
