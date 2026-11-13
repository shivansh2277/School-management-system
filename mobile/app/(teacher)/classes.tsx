import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { Card, Empty, Loading, Pill, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ClassRow = {
  class_section_id: number;
  class_label: string;
  is_class_teacher: boolean;
  subjects: string[];
  student_count: number;
};

type Student = { id: number; full_name: string; roll_no: number; admission_no: string };

export default function TeacherClasses() {
  const [open, setOpen] = useState<number | null>(null);
  const classes = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => api.get<ClassRow[]>("/teacher/classes"),
  });
  const roster = useQuery({
    queryKey: ["teacher-roster", open],
    queryFn: () => api.get<Student[]>(`/teacher/classes/${open}/students`),
    enabled: open !== null,
  });

  if (classes.isLoading) return <Loading />;

  return (
    <Screen>
      {(classes.data ?? []).length === 0 ? (
        <Card>
          <Empty text="You are not assigned to any section." />
        </Card>
      ) : (
        classes.data!.map((c) => {
          const isExpanded = open === c.class_section_id;

          return (
            <Card key={c.class_section_id}>
              <Pressable
                onPress={() => setOpen(isExpanded ? null : c.class_section_id)}
              >
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <View style={{ flex: 1, marginRight: 8 }}>
                    <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink }}>{c.class_label}</Text>
                      {c.is_class_teacher && (
                        <View
                          style={{
                            paddingHorizontal: 8,
                            paddingVertical: 2,
                            borderRadius: theme.radius.pill,
                            backgroundColor: theme.primarySoft,
                          }}
                        >
                          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>Class Teacher</Text>
                        </View>
                      )}
                    </View>
                    <Text style={[s.meta, { color: theme.inkSoft }]}>
                      {c.subjects.join(", ") || "General Faculty"}
                    </Text>
                  </View>

                  <View style={{ alignItems: "flex-end", gap: 6 }}>
                    <View
                      style={{
                        paddingHorizontal: 10,
                        paddingVertical: 4,
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.ground,
                        borderWidth: 1,
                        borderColor: theme.rule,
                      }}
                    >
                      <Text style={{ fontSize: 12, fontWeight: "600", color: theme.ink }}>
                        {c.student_count} students
                      </Text>
                    </View>
                    <Ionicons name={isExpanded ? "chevron-up" : "chevron-down"} size={16} color={theme.inkFaint} />
                  </View>
                </View>
              </Pressable>

              {isExpanded && (
                <View style={{ marginTop: 14, borderTopWidth: 1, borderTopColor: theme.rule, paddingTop: 10 }}>
                  <Text style={[s.meta, { fontWeight: "700", color: theme.ink, marginBottom: 8 }]}>Student Roster</Text>
                  {roster.isLoading ? (
                    <Text style={s.meta}>Loading students...</Text>
                  ) : (roster.data ?? []).length === 0 ? (
                    <Text style={s.meta}>No students enrolled in this section.</Text>
                  ) : (
                    (roster.data ?? []).map((student) => {
                      const initials = student.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .slice(0, 2)
                        .toUpperCase();

                      return (
                        <View
                          key={student.id}
                          style={{
                            flexDirection: "row",
                            alignItems: "center",
                            justifyContent: "space-between",
                            paddingVertical: 8,
                            borderBottomWidth: 1,
                            borderBottomColor: theme.rule,
                          }}
                        >
                          <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
                            <View
                              style={{
                                width: 32,
                                height: 32,
                                borderRadius: 16,
                                backgroundColor: theme.primarySoft,
                                alignItems: "center",
                                justifyContent: "center",
                              }}
                            >
                              <Text style={{ fontSize: 12, fontWeight: "700", color: theme.primary }}>{initials}</Text>
                            </View>
                            <View>
                              <Text style={[s.title, { fontSize: 13, color: theme.ink }]}>{student.full_name}</Text>
                              <Text style={[s.meta, { fontSize: 11 }]}>{student.admission_no}</Text>
                            </View>
                          </View>
                          <View
                            style={{
                              paddingHorizontal: 8,
                              paddingVertical: 2,
                              borderRadius: theme.radius.pill,
                              backgroundColor: theme.ground,
                            }}
                          >
                            <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkFaint }}>
                              Roll #{student.roll_no}
                            </Text>
                          </View>
                        </View>
                      );
                    })
                  )}
                </View>
              )}
            </Card>
          );
        })
      )}
    </Screen>
  );
}
