import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Pill, Row, Screen, Stat, s } from "../../src/components/ui";

type Item = {
  id: number;
  title: string;
  subject: string;
  due_date: string;
  submitted: boolean;
  late: boolean;
};

export default function ParentHomework() {
  const { selectedChildId } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["parent-homework", selectedChildId],
    queryFn: () => api.get<Item[]>(`/parent/children/${selectedChildId}/homework`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  const submitted = data.filter((h) => h.submitted).length;

  return (
    <Screen>
      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat label="Submitted" value={submitted} />
          <Stat label="Pending" value={data.length - submitted} />
        </View>
        <Text style={s.meta}>Read only. Homework is submitted by the student.</Text>
      </Card>

      <Card title="Assignments">
        {data.length === 0 ? (
          <Empty text="No homework assigned." />
        ) : (
          data.map((item) => (
            <Row
              key={item.id}
              left={
                <>
                  <Text style={s.title}>{item.title}</Text>
                  <Text style={s.meta}>
                    {item.subject} - due {item.due_date}
                  </Text>
                </>
              }
              right={
                item.submitted ? (
                  <Pill status="submitted" label={item.late ? "Late" : "Submitted"} />
                ) : (
                  <Pill status="pending" label="Pending" />
                )
              }
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
