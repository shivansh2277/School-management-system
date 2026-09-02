import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Summary = {
  name: string;
  class_label: string;
  attendance_percent: number | null;
  homework_submitted: number;
  homework_pending: number;
  latest_result_percent: number | null;
  fee_dues: number;
  recent_notices: { id: number; title: string; published_at: string }[];
};

export default function ParentDashboard() {
  const { selectedChildId } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["parent-summary", selectedChildId],
    queryFn: () => api.get<Summary>(`/parent/children/${selectedChildId}/summary`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  return (
    <Screen>
      <Card>
        <Text style={{ fontSize: 18, fontWeight: "700", color: theme.ink }}>{data.name}</Text>
        <Text style={s.meta}>Class {data.class_label}</Text>
      </Card>

      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat
            label="Attendance"
            value={data.attendance_percent === null ? "-" : `${data.attendance_percent}%`}
          />
          <Stat
            label="Latest result"
            value={data.latest_result_percent === null ? "-" : `${data.latest_result_percent}%`}
          />
          <Stat label="Fee dues" value={data.fee_dues} />
        </View>
      </Card>

      <Card title="Homework">
        <View style={{ flexDirection: "row" }}>
          <Stat label="Submitted" value={data.homework_submitted} />
          <Stat label="Pending" value={data.homework_pending} />
        </View>
      </Card>

      <Card title="Recent notices">
        {data.recent_notices.length === 0 ? (
          <Empty text="Nothing new." />
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
