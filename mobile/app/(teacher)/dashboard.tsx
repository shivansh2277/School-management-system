import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

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

export default function TeacherDashboard() {
  const { me } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["teacher-dashboard"],
    queryFn: () => api.get<Dashboard>("/teacher/dashboard"),
  });

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
