import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";

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
        classes.data!.map((c) => (
          <Card key={c.class_section_id}>
            <Pressable
              onPress={() => setOpen(open === c.class_section_id ? null : c.class_section_id)}
            >
              <Row
                left={
                  <>
                    <Text style={{ fontSize: 17, fontWeight: "700" }}>{c.class_label}</Text>
                    <Text style={s.meta}>{c.subjects.join(", ") || "No subject assigned"}</Text>
                  </>
                }
                right={
                  <View style={{ alignItems: "flex-end", gap: 4 }}>
                    {c.is_class_teacher ? <Pill status="present" label="Class teacher" /> : null}
                    <Text style={s.meta}>{c.student_count} students</Text>
                  </View>
                }
              />
            </Pressable>

            {open === c.class_section_id &&
              (roster.data ?? []).map((student) => (
                <Row
                  key={student.id}
                  left={
                    <>
                      <Text style={s.title}>{student.full_name}</Text>
                      <Text style={s.meta}>{student.admission_no}</Text>
                    </>
                  }
                  right={<Text style={s.meta}>Roll {student.roll_no}</Text>}
                />
              ))}
          </Card>
        ))
      )}
    </Screen>
  );
}
