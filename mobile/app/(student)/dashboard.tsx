import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Alert, Pressable, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AlertItem, ImportantAlerts } from "../../src/components/ImportantAlerts";
import { Card, Empty, Loading, Row, Screen, s } from "../../src/components/ui";
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

  const fullName = me?.user.full_name || "Student";
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const attPct = data.attendance_percent;
  const attColor = attPct === null ? theme.ink : attPct >= 75 ? theme.success : theme.danger;

  return (
    <Screen>
      {/* Student Profile Hero Card */}
      <Card>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
            <View
              style={{
                width: 48,
                height: 48,
                borderRadius: 24,
                backgroundColor: theme.primarySoft,
                alignItems: "center",
                justifyContent: "center",
                borderWidth: 2,
                borderColor: theme.primary,
              }}
            >
              <Text style={{ fontSize: 18, fontWeight: "800", color: theme.primary }}>{initials}</Text>
            </View>
            <View>
              <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink }}>{fullName}</Text>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
                <View
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                    borderRadius: theme.radius.pill,
                    backgroundColor: theme.primarySoft,
                  }}
                >
                  <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                    Class {me?.class_label}
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
                    Roll #{me?.roll_no}
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
                    Adm #{me?.admission_no}
                  </Text>
                </View>
              </View>
            </View>
          </View>

          <Pressable
            onPress={() => router.push("/(student)/profile" as any)}
            style={{
              padding: 8,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Ionicons name="chevron-forward" size={18} color={theme.inkFaint} />
          </Pressable>
        </View>
      </Card>

      {/* 3 Key Metrics Cards */}
      <View style={{ flexDirection: "row", gap: 8 }}>
        {/* Attendance */}
        <Pressable
          onPress={() => router.push("/(student)/attendance" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            Attendance
          </Text>
          <Text style={{ fontSize: 20, fontWeight: "800", color: attColor, marginTop: 4 }}>
            {attPct === null ? "-" : `${attPct}%`}
          </Text>
          <Text style={{ fontSize: 10, color: attColor, fontWeight: "600", marginTop: 2 }}>
            {attPct === null ? "No data" : attPct >= 75 ? "Above 75%" : "Shortage (<75%)"}
          </Text>
        </Pressable>

        {/* Homework Pending */}
        <Pressable
          onPress={() => router.push("/(student)/homework" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            Homework
          </Text>
          <Text
            style={{
              fontSize: 20,
              fontWeight: "800",
              color: data.homework_pending > 0 ? theme.warning : theme.success,
              marginTop: 4,
            }}
          >
            {data.homework_pending}
          </Text>
          <Text style={{ fontSize: 10, color: theme.inkFaint, marginTop: 2 }}>Pending Tasks</Text>
        </Pressable>

        {/* Latest Result */}
        <Pressable
          onPress={() => router.push("/(student)/results" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            Results
          </Text>
          <Text style={{ fontSize: 20, fontWeight: "800", color: theme.primary, marginTop: 4 }}>
            {data.latest_result_percent === null ? "-" : `${data.latest_result_percent}%`}
          </Text>
          <Text style={{ fontSize: 10, color: theme.inkFaint, marginTop: 2 }}>Latest Score</Text>
        </Pressable>
      </View>

      {/* Quick Services Row */}
      <Card title="Quick Services">
        <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 8 }}>
          {[
            { label: "Homework", icon: "book-outline" as const, color: "#4338CA", route: "/(student)/homework" },
            { label: "Timetable", icon: "calendar-outline" as const, color: "#0284C7", route: "/(student)/timetable" },
            { label: "Results", icon: "school-outline" as const, color: "#7C3AED", route: "/(student)/results" },
            { label: "Notices", icon: "megaphone-outline" as const, color: "#059669", route: "/(student)/notices" },
          ].map((action) => (
            <Pressable
              key={action.label}
              onPress={() => router.push(action.route as any)}
              style={{
                flex: 1,
                alignItems: "center",
                paddingVertical: 10,
                borderRadius: theme.radius.input,
                backgroundColor: theme.ground,
              }}
            >
              <View
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 18,
                  backgroundColor: `${action.color}15`,
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 6,
                }}
              >
                <Ionicons name={action.icon} size={18} color={action.color} />
              </View>
              <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft, textAlign: "center" }}>
                {action.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </Card>

      {/* Important Alerts */}
      <ImportantAlerts alerts={data.alerts} onAlertPress={handleAlertPress} />

      {/* Today's Schedule Timeline */}
      {data.today_schedule && data.today_schedule.length > 0 && (
        <Card title="Today's Classes">
          {data.today_schedule.map((slot) => {
            const periodNum = String(slot.period).padStart(2, "0");
            return (
              <View
                key={slot.period}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: 12,
                  paddingVertical: 10,
                  borderBottomWidth: 1,
                  borderBottomColor: theme.rule,
                }}
              >
                <View
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 18,
                    backgroundColor: theme.primarySoft,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Text style={{ fontSize: 13, fontWeight: "800", color: theme.primary }}>{periodNum}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[s.title, { fontSize: 14, color: theme.ink }]}>{slot.subject}</Text>
                  <Text style={[s.meta, { fontSize: 11 }]}>
                    {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)} • {slot.teacher}
                  </Text>
                </View>
                {slot.room ? (
                  <View
                    style={{
                      paddingHorizontal: 8,
                      paddingVertical: 2,
                      borderRadius: theme.radius.pill,
                      backgroundColor: theme.ground,
                    }}
                  >
                    <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft }}>{slot.room}</Text>
                  </View>
                ) : null}
              </View>
            );
          })}
        </Card>
      )}

      {/* Upcoming Exam */}
      <Card title="Next Upcoming Exam">
        {data.next_exam ? (
          <Row
            left={
              <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
                <View
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 19,
                    backgroundColor: theme.primarySoft,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Ionicons name="calendar" size={18} color={theme.primary} />
                </View>
                <View>
                  <Text style={[s.title, { fontSize: 14, color: theme.ink }]}>{data.next_exam.subject}</Text>
                  <Text style={[s.meta, { fontSize: 11 }]}>Class Assessment</Text>
                </View>
              </View>
            }
            right={
              <View
                style={{
                  paddingHorizontal: 10,
                  paddingVertical: 4,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.ground,
                  borderWidth: 1,
                  borderColor: theme.rule,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                  {formatDate(data.next_exam.exam_date)}
                </Text>
              </View>
            }
          />
        ) : (
          <Empty text="No upcoming exams scheduled." />
        )}
      </Card>
    </Screen>
  );
}
