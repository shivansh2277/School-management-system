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

export default function TeacherTimetable() {
  const currentDayIndex = Math.min(new Date().getDay() - 1, 5);
  const defaultDay = currentDayIndex >= 0 ? DAYS[currentDayIndex].key : "mon";
  const [day, setDay] = useState(defaultDay);

  const { data, isLoading } = useQuery({
    queryKey: ["teacher-timetable"],
    queryFn: () => api.get<Slot[]>("/teacher/timetable"),
  });

  if (isLoading) return <Loading />;

  const slots = (data ?? [])
    .filter((s) => (s.day_of_week || "").toLowerCase() === day.toLowerCase())
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
          <Empty text={`No classes scheduled for you on ${day.toUpperCase()}.`} />
        </Card>
      ) : (
        slots.map((slot) => {
          const isRelief = slot.is_relief || Boolean(slot.relief_teacher);
          const periodNum = String(slot.period).padStart(2, "0");

          return (
            <Card key={`${slot.day_of_week}-${slot.period}-${slot.class_label}`}>
              <View style={{ flexDirection: "row", alignItems: "flex-start", gap: 12 }}>
                {/* Timeline Column */}
                <View style={{ alignItems: "center", width: 56 }}>
                  <View
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 20,
                      backgroundColor: theme.primarySoft,
                      alignItems: "center",
                      justifyContent: "center",
                      borderWidth: 1,
                      borderColor: theme.rule,
                    }}
                  >
                    <Text style={{ fontSize: 14, fontWeight: "800", color: theme.primary }}>
                      {periodNum}
                    </Text>
                  </View>
                  <Text style={{ fontSize: 10, color: theme.inkFaint, marginTop: 4, textAlign: "center" }}>
                    {slot.start_time?.slice(0, 5)}
                  </Text>
                  <Text style={{ fontSize: 9, color: theme.inkFaint, textAlign: "center" }}>
                    to {slot.end_time?.slice(0, 5)}
                  </Text>
                </View>

                {/* Content Column */}
                <View style={{ flex: 1, gap: 4 }}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                    <Text style={[s.title, { fontSize: 16, color: theme.ink }]}>{slot.subject}</Text>
                    {slot.room ? (
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
                          {slot.room}
                        </Text>
                      </View>
                    ) : null}
                  </View>

                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                    <View
                      style={{
                        paddingHorizontal: 8,
                        paddingVertical: 2,
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.primarySoft,
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                        {slot.class_label || "General"}
                      </Text>
                    </View>
                  </View>

                  {isRelief && (
                    <View
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        gap: 6,
                        marginTop: 4,
                        paddingHorizontal: 8,
                        paddingVertical: 3,
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.warningBg,
                        borderWidth: 1,
                        borderColor: "#FDE68A",
                        alignSelf: "flex-start",
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "700", color: theme.warning }}>
                        🔄 Relief Duty {slot.relief_teacher ? `(${slot.relief_teacher})` : ""}
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            </Card>
          );
        })
      )}
    </Screen>
  );
}
