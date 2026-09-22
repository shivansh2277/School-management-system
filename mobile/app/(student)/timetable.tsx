import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Slot = {
  id?: number;
  period: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject: string;
  teacher: string;
  room: string | null;
  class_label: string;
  is_relief?: boolean;
  relief_teacher?: string | null;
};

const DAYS = [
  { key: "mon", label: "Mon" },
  { key: "tue", label: "Tue" },
  { key: "wed", label: "Wed" },
  { key: "thu", label: "Thu" },
  { key: "fri", label: "Fri" },
  { key: "sat", label: "Sat" },
];

export default function StudentTimetable() {
  const currentDayIndex = Math.min(new Date().getDay() - 1, 5);
  const defaultDay = currentDayIndex >= 0 ? DAYS[currentDayIndex].key : "mon";
  const [day, setDay] = useState(defaultDay);

  const { data, isLoading } = useQuery({
    queryKey: ["student-timetable"],
    queryFn: () => api.get<Slot[]>("/student/timetable"),
  });

  if (isLoading) return <Loading />;

  const slots = (data ?? [])
    .filter((s) => s.day_of_week.toLowerCase() === day.toLowerCase())
    .sort((a, b) => a.period - b.period);

  return (
    <Screen>
      {/* Weekly Day Switcher */}
      <View style={{ flexDirection: "row", gap: 6, marginBottom: 12 }}>
        {DAYS.map((d) => {
          const on = day === d.key;
          return (
            <Pressable
              key={d.key}
              onPress={() => setDay(d.key)}
              style={{
                flex: 1,
                paddingVertical: 8,
                borderRadius: theme.radius.input,
                alignItems: "center",
                backgroundColor: on ? theme.primary : theme.surface,
                borderWidth: 1,
                borderColor: on ? theme.primary : theme.rule,
              }}
            >
              <Text
                style={{
                  fontSize: 13,
                  fontWeight: on ? "700" : "500",
                  color: on ? "#fff" : theme.inkSoft,
                }}
              >
                {d.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {/* Slots List */}
      {slots.length === 0 ? (
        <Card>
          <Empty text={`No classes scheduled for ${day.toUpperCase()}.`} />
        </Card>
      ) : (
        slots.map((slot) => {
          const isRelief = slot.is_relief || Boolean(slot.relief_teacher);
          const teacherDisplay = isRelief && slot.relief_teacher ? slot.relief_teacher : slot.teacher;

          return (
            <Card key={`${slot.day_of_week}-${slot.period}`}>
              <Row
                left={
                  <View style={{ gap: 4 }}>
                    <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                      <View
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: 6,
                          backgroundColor: theme.primarySoft,
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <Text style={{ fontSize: 13, fontWeight: "700", color: theme.primary }}>
                          {slot.period}
                        </Text>
                      </View>
                      <Text style={[s.title, { fontSize: 16 }]}>{slot.subject}</Text>
                    </View>

                    <Text style={s.meta}>
                      {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)}
                      {slot.room ? ` • Room: ${slot.room}` : ""}
                    </Text>

                    <Text style={{ fontSize: 13, color: theme.inkSoft, marginTop: 2 }}>
                      Teacher: <Text style={{ fontWeight: "600", color: theme.ink }}>{teacherDisplay}</Text>
                    </Text>

                    {isRelief && (
                      <View
                        style={{
                          flexDirection: "row",
                          alignItems: "center",
                          gap: 6,
                          marginTop: 4,
                          paddingHorizontal: 8,
                          paddingVertical: 3,
                          borderRadius: 4,
                          backgroundColor: "#FEF3C7",
                          alignSelf: "flex-start",
                        }}
                      >
                        <Text style={{ fontSize: 11, fontWeight: "700", color: "#D97706" }}>
                          🔄 Relief Substitute Cover
                        </Text>
                        {slot.relief_teacher && (
                          <Text style={{ fontSize: 11, color: "#92400E" }}>
                            (Covered by {slot.relief_teacher})
                          </Text>
                        )}
                      </View>
                    )}
                  </View>
                }
                right={
                  <Pill label={`Period ${slot.period}`} />
                }
              />
            </Card>
          );
        })
      )}
    </Screen>
  );
}
