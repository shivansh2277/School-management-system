import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ClassRow = { class_section_id: number; class_label: string; is_class_teacher?: boolean };
type Roll = {
  student_id: number;
  full_name: string;
  roll_no: number;
  status: string | null;
};

const STATUS_CHIPS = [
  { key: "present", badge: "P", label: "Present", color: "#16A34A", bg: "#DCFCE7" },
  { key: "absent", badge: "A", label: "Absent", color: "#EF4444", bg: "#FEE2E2" },
  { key: "late", badge: "L", label: "Late", color: "#F59E0B", bg: "#FEF3C7" },
  { key: "leave", badge: "M", label: "Medical", color: "#8B5CF6", bg: "#EDE9FE" },
] as const;

type Status = (typeof STATUS_CHIPS)[number]["key"];

export default function TeacherAttendance() {
  const qc = useQueryClient();
  const today = new Date().toISOString().slice(0, 10);
  const [date] = useState(today);
  const [classId, setClassId] = useState<number | null>(null);
  const [marks, setMarks] = useState<Record<number, Status>>({});
  const [note, setNote] = useState<string | null>(null);

  const classes = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => api.get<ClassRow[]>("/teacher/classes"),
  });

  const classTeacherSections = (classes.data ?? []).filter((c) => c.is_class_teacher);
  const active = classId ?? classTeacherSections[0]?.class_section_id ?? null;

  const roll = useQuery({
    queryKey: ["teacher-roll", active, date],
    queryFn: () => api.get<Roll[]>(`/teacher/attendance?class_section_id=${active}&date=${date}`),
    enabled: active !== null,
  });

  // Re-opening a date that is already marked pre-fills the sheet.
  useEffect(() => {
    if (!roll.data) return;
    const next: Record<number, Status> = {};
    for (const r of roll.data) if (r.status) next[r.student_id] = r.status as Status;
    setMarks(next);
    setNote(null);
  }, [roll.data]);

  const save = useMutation({
    mutationFn: () =>
      api.post("/teacher/attendance", {
        class_section_id: active,
        date,
        entries: (roll.data ?? []).map((r) => ({
          student_id: r.student_id,
          status: marks[r.student_id] ?? "present",
        })),
      }),
    onSuccess: () => {
      setNote("Attendance saved.");
      qc.invalidateQueries({ queryKey: ["teacher-roll"] });
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (classes.isLoading) return <Loading />;

  // Counter computations
  const total = (roll.data ?? []).length;
  const counts = {
    present: 0,
    absent: 0,
    late: 0,
    leave: 0,
  };
  for (const r of roll.data ?? []) {
    const st = marks[r.student_id];
    if (st && st in counts) counts[st as keyof typeof counts]++;
  }

  return (
    <Screen>
      {classTeacherSections.length === 0 ? (
        <Card>
          <Empty text="You are not currently assigned as a Class Teacher for any section. Daily attendance registration is reserved for designated class teachers." />
        </Card>
      ) : (
        <>
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            {classTeacherSections.map((c) => (
              <Pressable
                key={c.class_section_id}
                onPress={() => setClassId(c.class_section_id)}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 8,
                  borderRadius: theme.radius.input,
                  backgroundColor: active === c.class_section_id ? theme.primary : theme.surface,
                }}
              >
                <Text
                  style={{ color: active === c.class_section_id ? "#fff" : theme.inkSoft, fontSize: 13 }}
                >
                  {c.class_label}
                </Text>
              </Pressable>
            ))}
          </View>

          <Card title={`Roll sheet - ${formatDate(date)}`}>
        {(roll.data ?? []).length === 0 ? (
          <Empty text="No students in this section." />
        ) : (
          <>
            {/* Counter Header */}
            <View
              style={{
                flexDirection: "row",
                justifyContent: "space-between",
                backgroundColor: theme.ground,
                padding: 10,
                borderRadius: theme.radius.input,
                marginBottom: 10,
              }}
            >
              <View style={{ alignItems: "center" }}>
                <Text style={{ fontSize: 11, color: theme.inkFaint }}>Total</Text>
                <Text style={{ fontSize: 15, fontWeight: "700", color: theme.ink }}>{total}</Text>
              </View>
              <View style={{ alignItems: "center" }}>
                <Text style={{ fontSize: 11, color: "#16A34A" }}>Present (P)</Text>
                <Text style={{ fontSize: 15, fontWeight: "700", color: "#16A34A" }}>{counts.present}</Text>
              </View>
              <View style={{ alignItems: "center" }}>
                <Text style={{ fontSize: 11, color: "#EF4444" }}>Absent (A)</Text>
                <Text style={{ fontSize: 15, fontWeight: "700", color: "#EF4444" }}>{counts.absent}</Text>
              </View>
              <View style={{ alignItems: "center" }}>
                <Text style={{ fontSize: 11, color: "#F59E0B" }}>Late (L)</Text>
                <Text style={{ fontSize: 15, fontWeight: "700", color: "#F59E0B" }}>{counts.late}</Text>
              </View>
              <View style={{ alignItems: "center" }}>
                <Text style={{ fontSize: 11, color: "#8B5CF6" }}>Med/Leave (M)</Text>
                <Text style={{ fontSize: 15, fontWeight: "700", color: "#8B5CF6" }}>{counts.leave}</Text>
              </View>
            </View>

            <Button
              label="Mark all present"
              tone="ghost"
              onPress={() =>
                setMarks(
                  Object.fromEntries(roll.data!.map((r) => [r.student_id, "present" as Status])),
                )
              }
            />
            {roll.data!.map((r) => (
              <View
                key={r.student_id}
                style={{
                  paddingVertical: 10,
                  borderBottomWidth: 1,
                  borderBottomColor: theme.rule,
                }}
              >
                <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 6 }}>
                  <Text style={[s.title, { fontSize: 14 }]}>
                    {r.roll_no}. {r.full_name}
                  </Text>
                  {marks[r.student_id] && (
                    <Text
                      style={{
                        fontSize: 12,
                        fontWeight: "600",
                        textTransform: "capitalize",
                        color: STATUS_CHIPS.find((c) => c.key === marks[r.student_id])?.color,
                      }}
                    >
                      {STATUS_CHIPS.find((c) => c.key === marks[r.student_id])?.label}
                    </Text>
                  )}
                </View>
                <View style={{ flexDirection: "row", gap: 8 }}>
                  {STATUS_CHIPS.map((chip) => {
                    const on = (marks[r.student_id] ?? null) === chip.key;
                    return (
                      <Pressable
                        key={chip.key}
                        onPress={() => setMarks({ ...marks, [r.student_id]: chip.key })}
                        style={{
                          flex: 1,
                          paddingVertical: 7,
                          borderRadius: theme.radius.input,
                          alignItems: "center",
                          backgroundColor: on ? chip.bg : theme.ground,
                          borderWidth: 1.5,
                          borderColor: on ? chip.color : "transparent",
                        }}
                      >
                        <Text
                          style={{
                            fontSize: 13,
                            color: on ? chip.color : theme.inkSoft,
                            fontWeight: on ? "700" : "500",
                          }}
                        >
                          {chip.badge}
                        </Text>
                        <Text
                          style={{
                            fontSize: 10,
                            color: on ? chip.color : theme.inkFaint,
                            fontWeight: on ? "600" : "400",
                          }}
                        >
                          {chip.label}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            ))}
            {note ? <Text style={[s.meta, { marginTop: 8 }]}>{note}</Text> : null}
            <View style={{ marginTop: 12 }}>
              <Button label="Save Attendance" onPress={() => save.mutate()} disabled={save.isPending} />
            </View>
          </>
        )}
      </Card>
        </>
      )}
    </Screen>
  );
}
