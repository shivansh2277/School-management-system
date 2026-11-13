/** Views shared by more than one role, so the student and parent tab sets stay in step. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../api/client";
import { statusColor, theme } from "../theme";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "./ui";

type AttendanceMonth = {
  days: { date: string; status: string }[];
  summary: { present: number; absent: number; leave: number; percent: number | null };
};

const STATUS_CONF: Record<string, { bg: string; text: string; label: string }> = {
  present: { bg: "#ECFDF5", text: "#059669", label: "P" },
  absent: { bg: "#FFF1F2", text: "#E11D48", label: "A" },
  late: { bg: "#FFFBEB", text: "#D97706", label: "L" },
  leave: { bg: "#F5F3FF", text: "#7C3AED", label: "M" },
  half_day: { bg: "#FFFBEB", text: "#D97706", label: "H" },
};

export function AttendanceView({ path }: { path: string }) {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const year = now.getFullYear();

  const { data, isLoading } = useQuery({
    queryKey: ["attendance", path, month, year],
    queryFn: () => api.get<AttendanceMonth>(`${path}?month=${month}&year=${year}`),
  });

  if (isLoading) return <Loading />;

  const byDay = new Map((data?.days ?? []).map((d) => [Number(d.date.slice(8, 10)), d.status]));
  const daysInMonth = new Date(year, month, 0).getDate();
  const pct = data?.summary.percent ?? null;
  const isShortage = pct !== null && pct < 75;

  return (
    <Screen>
      {/* 4-Stat Monthly Metric Breakdown */}
      {data && (
        <Card title="Monthly Summary">
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#059669", textTransform: "uppercase" }}>Present</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#059669", marginTop: 2 }}>{data.summary.present}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#E11D48", textTransform: "uppercase" }}>Absent</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#E11D48", marginTop: 2 }}>{data.summary.absent}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#7C3AED", textTransform: "uppercase" }}>Leave</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#7C3AED", marginTop: 2 }}>{data.summary.leave}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkFaint, textTransform: "uppercase" }}>Overall</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: isShortage ? theme.danger : theme.success, marginTop: 2 }}>
                {pct === null ? "-" : `${pct}%`}
              </Text>
            </View>
          </View>
        </Card>
      )}

      {/* Calendar Card */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <Pressable
            onPress={() => setMonth((m) => (m === 1 ? 12 : m - 1))}
            style={{
              paddingHorizontal: 10,
              paddingVertical: 6,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Text style={{ color: theme.primary, fontWeight: "700", fontSize: 12 }}>← Prev</Text>
          </Pressable>
          <Text style={{ fontWeight: "800", fontSize: 15, color: theme.ink }}>
            {new Date(year, month - 1).toLocaleString("en", { month: "long" })} {year}
          </Text>
          <Pressable
            onPress={() => setMonth((m) => (m === 12 ? 1 : m + 1))}
            style={{
              paddingHorizontal: 10,
              paddingVertical: 6,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Text style={{ color: theme.primary, fontWeight: "700", fontSize: 12 }}>Next →</Text>
          </Pressable>
        </View>

        {byDay.size === 0 ? (
          <Empty text="No attendance recorded for this month." />
        ) : (
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((d) => {
              const status = byDay.get(d);
              const conf = status ? STATUS_CONF[status] : null;
              return (
                <View
                  key={d}
                  style={{
                    width: 38,
                    height: 42,
                    borderRadius: theme.radius.input,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: conf ? conf.bg : theme.ground,
                    borderWidth: 1,
                    borderColor: conf ? conf.text : theme.rule,
                  }}
                >
                  <Text style={{ fontSize: 12, color: theme.ink, fontWeight: "700" }}>{d}</Text>
                  {conf ? (
                    <Text style={{ fontSize: 9, color: conf.text, fontWeight: "800", marginTop: 1 }}>{conf.label}</Text>
                  ) : null}
                </View>
              );
            })}
          </View>
        )}

        {/* Legend */}
        <View style={{ flexDirection: "row", gap: 12, marginTop: 14, paddingTop: 10, borderTopWidth: 1, borderTopColor: theme.rule, flexWrap: "wrap" }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#059669" }} />
            <Text style={{ fontSize: 11, color: "#059669", fontWeight: "600" }}>Present</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#E11D48" }} />
            <Text style={{ fontSize: 11, color: "#E11D48", fontWeight: "600" }}>Absent</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#D97706" }} />
            <Text style={{ fontSize: 11, color: "#D97706", fontWeight: "600" }}>Late</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#7C3AED" }} />
            <Text style={{ fontSize: 11, color: "#7C3AED", fontWeight: "600" }}>Leave</Text>
          </View>
        </View>
      </Card>
    </Screen>
  );
}

type Notice = {
  id: number;
  title: string;
  body: string;
  audience: string;
  class_label: string | null;
  published_at: string;
};

export function NoticesView({ path }: { path: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["notices", path],
    queryFn: () => api.get<Notice[]>(path),
  });
  if (isLoading) return <Loading />;

  return (
    <Screen>
      {(data ?? []).length === 0 ? (
        <Card>
          <Empty text="No circulars or notices for you yet." />
        </Card>
      ) : (
        data!.map((n) => (
          <Card key={n.id}>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.primarySoft,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary, textTransform: "capitalize" }}>
                  {n.audience}
                  {n.class_label ? ` • ${n.class_label}` : ""}
                </Text>
              </View>
              <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                {new Date(n.published_at).toLocaleDateString()}
              </Text>
            </View>
            <Text style={[s.title, { fontSize: 15, color: theme.ink, marginBottom: 4 }]}>{n.title}</Text>
            <Text style={{ color: theme.inkSoft, fontSize: 13, lineHeight: 18 }}>{n.body}</Text>
          </Card>
        ))
      )}
    </Screen>
  );
}
