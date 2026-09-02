import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Screen, s } from "../../src/components/ui";
import { statusColor, theme } from "../../src/theme";

type ClassRow = { class_section_id: number; class_label: string };
type Roll = {
  student_id: number;
  full_name: string;
  roll_no: number;
  status: string | null;
};

const STATUSES = ["present", "absent", "leave"] as const;
type Status = (typeof STATUSES)[number];

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

  const active = classId ?? classes.data?.[0]?.class_section_id ?? null;

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

  return (
    <Screen>
      <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
        {(classes.data ?? []).map((c) => (
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

      <Card title={`Roll sheet - ${date}`}>
        {(roll.data ?? []).length === 0 ? (
          <Empty text="No students in this section." />
        ) : (
          <>
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
              <View key={r.student_id} style={{ gap: 6, paddingVertical: 8 }}>
                <Text style={s.title}>
                  {r.roll_no}. {r.full_name}
                </Text>
                <View style={{ flexDirection: "row", gap: 8 }}>
                  {STATUSES.map((status) => {
                    const on = (marks[r.student_id] ?? null) === status;
                    return (
                      <Pressable
                        key={status}
                        onPress={() => setMarks({ ...marks, [r.student_id]: status })}
                        style={{
                          flex: 1,
                          paddingVertical: 8,
                          borderRadius: theme.radius.input,
                          alignItems: "center",
                          backgroundColor: on ? `${statusColor[status]}22` : theme.ground,
                          borderWidth: 1,
                          borderColor: on ? statusColor[status] : "transparent",
                        }}
                      >
                        <Text
                          style={{
                            fontSize: 12,
                            textTransform: "capitalize",
                            color: on ? statusColor[status] : theme.inkSoft,
                            fontWeight: on ? "600" : "400",
                          }}
                        >
                          {status}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>
            ))}
            {note ? <Text style={s.meta}>{note}</Text> : null}
            <Button label="Save" onPress={() => save.mutate()} disabled={save.isPending} />
          </>
        )}
      </Card>
    </Screen>
  );
}
