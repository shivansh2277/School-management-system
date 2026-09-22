import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Dashboard = {
  attendance_percent: number | null;
  homework_pending: number;
  next_exam: { subject: string; exam_date: string } | null;
  latest_result_percent: number | null;
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
  const { me } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["student-dashboard"],
    queryFn: () => api.get<Dashboard>("/student/dashboard"),
  });

  if (isLoading || !data) return <Loading />;

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
