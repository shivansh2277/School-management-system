import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
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

const DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat"] as const;

export default function ParentTimetable() {
  const { t } = useTranslation();
  const { me, selectedChildId } = useAuth();
  const currentChildId = selectedChildId ?? me?.children?.[0]?.id;
  const currentChild = me?.children?.find((c) => c.id === currentChildId) ?? me?.children?.[0];

  const days = [
    { key: "mon", label: t("tt_mon") },
    { key: "tue", label: t("tt_tue") },
    { key: "wed", label: t("tt_wed") },
    { key: "thu", label: t("tt_thu") },
    { key: "fri", label: t("tt_fri") },
    { key: "sat", label: t("tt_sat") },
  ];

  const currentDayIndex = Math.min(new Date().getDay() - 1, 5);
  const defaultDay = currentDayIndex >= 0 ? DAY_KEYS[currentDayIndex] : "mon";
  const [day, setDay] = useState(defaultDay);

  const { data, isLoading } = useQuery({
    queryKey: ["parent-timetable", currentChildId],
    queryFn: () => api.get<Slot[]>(`/parent/children/${currentChildId}/timetable`),
    enabled: Boolean(currentChildId),
  });

  if (isLoading) return <Loading />;

  const slots = (data ?? [])
    .filter((s) => (s.day_of_week || "").toLowerCase() === day.toLowerCase())
    .sort((a, b) => a.period - b.period);

  return (
    <Screen>
      {/* Active Child Summary */}
      {currentChild && (
        <View style={{ marginBottom: 12, paddingHorizontal: 4 }}>
          <Text style={{ fontSize: 13, color: theme.inkSoft }}>
            {t("tt_viewing_for")}{" "}
            <Text style={{ fontWeight: "700", color: theme.primary }}>
              {currentChild.name}
            </Text>{" "}
            {currentChild.class_label ? `(${currentChild.class_label})` : ""}
          </Text>
        </View>
      )}

      {/* Weekly Day Switcher */}
      <View style={{ flexDirection: "row", gap: 6, marginBottom: 12 }}>
        {days.map((d) => {
          const on = day === d.key;
          return (
            <Pressable
              key={d.key}
              onPress={() => setDay(d.key as any)}
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
          <Empty text={t("tt_no_slots")} />
        </Card>
      ) : (
        slots.map((slot) => {
          const isRelief = slot.is_relief || Boolean(slot.relief_teacher);
          const teacherDisplay = isRelief && slot.relief_teacher ? slot.relief_teacher : slot.teacher;
          const periodNum = String(slot.period).padStart(2, "0");

          return (
            <Card key={`${slot.day_of_week}-${slot.period}`}>
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

                  <Text style={{ fontSize: 12, color: theme.inkSoft }}>
                    {t("tt_teacher")}: <Text style={{ fontWeight: "700", color: theme.ink }}>{teacherDisplay}</Text>
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
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.warningBg,
                        borderWidth: 1,
                        borderColor: "#FDE68A",
                        alignSelf: "flex-start",
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "700", color: theme.warning }}>
                        {t("tt_relief_cover")} {slot.relief_teacher ? `(${slot.relief_teacher})` : ""}
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
