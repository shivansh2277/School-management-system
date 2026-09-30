import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Alert, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AlertItem, ImportantAlerts } from "../../src/components/ImportantAlerts";
import { Card, Empty, Loading, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Dashboard = {
  attendance_percent: number | null;
  homework_pending: number;
  next_exam: { subject: string; exam_date: string } | null;
  latest_result_percent: number | null;
  fee_due_amount?: number;
  latest_report_card?: { exam_id: number; title: string } | null;
  latest_periodic_test?: { exam_id: number; title: string } | null;
  alerts?: AlertItem[];
  recent_notices: { id: number; title: string; published_at: string }[];
  today_schedule: {
    period: number;
    subject: string;
    teacher: string;
    start_time: string;
    end_time: string;
    room: string | null;
  }[];
};

export default function StudentDashboard() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { me } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["student-dashboard"],
    queryFn: () => api.get<Dashboard>("/student/dashboard"),
  });

  if (isLoading || !data) return <Loading />;

  const handleAlertPress = async (alert: AlertItem) => {
    // Attendance, report card, and periodic test alerts disappear after viewing.
    // Fee alerts NEVER dismiss by viewing (must remain visible until balance is 0).
    if (alert.type !== "fee" && alert.event_key) {
      try {
        await api.post("/student/alerts/view", {
          alert_type: alert.type,
          event_key: alert.event_key,
          exam_id: alert.exam_id,
        });
        queryClient.invalidateQueries({ queryKey: ["student-dashboard"] });
      } catch (err) {
        console.warn("Failed to mark alert viewed:", err);
      }
    }
    if (alert.route) {
      router.push(alert.route as any);
    } else if (alert.type === "fee") {
      Alert.alert(
        "Fee Due",
        `${alert.message}\n\nPlease ask your parent or guardian to clear outstanding fees.`
      );
    }
  };

  return (
    <Screen>
      <Card>
        <Text style={{ fontSize: 18, fontWeight: "700", color: theme.ink }}>
          Hello, {me?.user.full_name}
        </Text>
        <Text style={s.meta}>
          Class {me?.class_label} - Roll {me?.roll_no} - {me?.admission_no}
        </Text>
      </Card>

      <ImportantAlerts alerts={data.alerts} onAlertPress={handleAlertPress} />

      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat
            label="Attendance"
            value={data.attendance_percent === null ? "-" : `${data.attendance_percent}%`}
          />
          <Stat label="Homework due" value={data.homework_pending} />
          <Stat
            label="Latest result"
            value={data.latest_result_percent === null ? "-" : `${data.latest_result_percent}%`}
          />
        </View>
      </Card>

      <Card title="Next exam">
        {data.next_exam ? (
          <Row
            left={<Text style={s.title}>{data.next_exam.subject}</Text>}
            right={<Text style={s.meta}>{formatDate(data.next_exam.exam_date)}</Text>}
          />
        ) : (
          <Empty text="No exams scheduled." />
        )}
      </Card>
    </Screen>
  );
}
