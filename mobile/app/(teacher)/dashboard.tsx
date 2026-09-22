import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Dashboard = {
  today_schedule: {
    period: number;
    time: string;
    class_label: string;
    subject: string;
    room: string | null;
  }[];
  sections: string[];
  pending_marks_entry: number;
  homework_awaiting_submissions: number;
  attendance: { present: number; absent: number; leave: number; percent: number | null } | null;
};

type SubstitutionDuty = {
  id: number;
  date: string;
  period_no: number;
  time: string;
  class_label: string;
  subject: string;
  room: string | null;
  absent_teacher_name: string;
  status: string;
};

export default function TeacherDashboard() {
  const router = useRouter();
  const { me } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["teacher-dashboard"],
    queryFn: () => api.get<Dashboard>("/teacher/dashboard"),
  });

  const { data: duties } = useQuery({
    queryKey: ["teacher-substitution-duties"],
    queryFn: () => api.get<SubstitutionDuty[]>("/teacher/substitutions/duties"),
  });

  const todayStr = new Date().toISOString().slice(0, 10);
  const todayDuties = (duties ?? []).filter((d) => d.date === todayStr);

  if (isLoading || !data) return <Loading />;

  return (
    <Screen>
      <Card>
        <Text style={{ fontSize: 18, fontWeight: "700", color: theme.ink }}>
          {me?.user.full_name}
        </Text>
        <Text style={s.meta}>
          {me?.employee_id} - {data.sections.join(", ") || "No sections"}
        </Text>
      </Card>

      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat label="Marks pending" value={data.pending_marks_entry} />
          <Stat label="Homework open" value={data.homework_awaiting_submissions} />
          <Stat
            label="Attendance"
            value={
              data.attendance?.percent === null || data.attendance === null
                ? "-"
                : `${data.attendance.percent}%`
            }
          />
        </View>
      </Card>

      {/* Today's Substitution Duties Alert Card */}
      {todayDuties.length > 0 && (
        <Card title={`Today's Substitution Duties (${todayDuties.length})`}>
          {todayDuties.map((duty) => (
            <Row
              key={duty.id}
              left={
                <>
                  <Text style={[s.title, { color: theme.primary, fontWeight: "600" }]}>
                    Period {duty.period_no} • {duty.subject} ({duty.class_label})
                  </Text>
                  <Text style={s.meta}>
                    Covering for: {duty.absent_teacher_name} {duty.room ? `• Room ${duty.room}` : ""}
                  </Text>
                </>
              }
              right={<Text style={s.meta}>{duty.time}</Text>}
            />
          ))}
        </Card>
      )}

      {/* Quick Actions */}
      <Card title="Quick Actions">
        <View style={{ flexDirection: "row", gap: 8 }}>
          <Pressable
            onPress={() => router.push("/(teacher)/leave")}
            style={{
              flex: 1,
              backgroundColor: `${theme.primary}15`,
              borderWidth: 1,
              borderColor: theme.primary,
              borderRadius: theme.radius.input,
              paddingVertical: 10,
              alignItems: "center",
            }}
          >
            <Text style={{ color: theme.primary, fontWeight: "600", fontSize: 13 }}>
              Apply Leave
            </Text>
          </Pressable>
          <Pressable
            onPress={() => router.push("/(teacher)/timetable")}
            style={{
              flex: 1,
              backgroundColor: theme.surface,
              borderWidth: 1,
              borderColor: theme.rule,
              borderRadius: theme.radius.input,
              paddingVertical: 10,
              alignItems: "center",
            }}
          >
            <Text style={{ color: theme.inkSoft, fontWeight: "600", fontSize: 13 }}>
              My Timetable
            </Text>
          </Pressable>
        </View>
      </Card>

      <Card title="Today's periods">
        {data.today_schedule.length === 0 ? (
          <Empty text="No periods today." />
        ) : (
          data.today_schedule.map((slot, i) => (
            <Row
              key={i}
              left={
                <>
                  <Text style={s.title}>
                    {slot.subject} - {slot.class_label}
                  </Text>
                  <Text style={s.meta}>{slot.room ?? ""}</Text>
                </>
              }
              right={<Text style={s.meta}>{slot.time}</Text>}
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
