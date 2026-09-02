import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ClassRow = { class_section_id: number; class_label: string; subjects: string[] };
type Subject = { id: number; name: string };
type Item = {
  id: number;
  title: string;
  subject: string;
  subject_id: number;
  class_label: string;
  class_section_id: number;
  due_date: string;
  submitted_count: number;
  total_students: number;
};
type Submission = {
  student_id: number;
  full_name: string;
  roll_no: number;
  submitted: boolean;
  late: boolean;
  answer_text: string | null;
};

export default function TeacherHomework() {
  const qc = useQueryClient();
  const [open, setOpen] = useState<number | null>(null);
  const [composing, setComposing] = useState(false);
  const [form, setForm] = useState({
    class_section_id: "",
    subject_id: "",
    title: "",
    description: "",
    due_date: "",
  });
  const [error, setError] = useState<string | null>(null);

  const classes = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => api.get<ClassRow[]>("/teacher/classes"),
  });
  const list = useQuery({
    queryKey: ["teacher-homework"],
    queryFn: () => api.get<Item[]>("/teacher/homework"),
  });
  const submissions = useQuery({
    queryKey: ["teacher-submissions", open],
    queryFn: () => api.get<Submission[]>(`/teacher/homework/${open}/submissions`),
    enabled: open !== null,
  });

  const create = useMutation({
    mutationFn: () =>
      api.post("/teacher/homework", {
        class_section_id: Number(form.class_section_id),
        subject_id: Number(form.subject_id),
        title: form.title,
        description: form.description,
        due_date: form.due_date,
      }),
    onSuccess: () => {
      setComposing(false);
      setError(null);
      setForm({ class_section_id: "", subject_id: "", title: "", description: "", due_date: "" });
      qc.invalidateQueries({ queryKey: ["teacher-homework"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  // Only the subjects this teacher owns in the chosen section can be picked.
  const subjectsForSection = useQuery({
    queryKey: ["subjects-all"],
    queryFn: () => api.get<Subject[]>("/teacher/subjects"),
  });

  if (list.isLoading) return <Loading />;

  return (
    <Screen>
      <Button
        label={composing ? "Cancel" : "New assignment"}
        tone={composing ? "ghost" : "primary"}
        onPress={() => setComposing(!composing)}
      />

      {composing && (
        <Card title="Create homework">
          <Text style={s.meta}>Class</Text>
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            {(classes.data ?? []).map((c) => (
              <Chip
                key={c.class_section_id}
                label={c.class_label}
                on={form.class_section_id === String(c.class_section_id)}
                onPress={() => setForm({ ...form, class_section_id: String(c.class_section_id) })}
              />
            ))}
          </View>

          <Text style={s.meta}>Subject</Text>
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
            {(subjectsForSection.data ?? []).map((sub) => (
              <Chip
                key={sub.id}
                label={sub.name}
                on={form.subject_id === String(sub.id)}
                onPress={() => setForm({ ...form, subject_id: String(sub.id) })}
              />
            ))}
          </View>

          <TextInput
            style={s.input}
            placeholder="Title"
            placeholderTextColor={theme.inkFaint}
            value={form.title}
            onChangeText={(v) => setForm({ ...form, title: v })}
          />
          <TextInput
            style={[s.input, { minHeight: 80, textAlignVertical: "top" }]}
            multiline
            placeholder="Description"
            placeholderTextColor={theme.inkFaint}
            value={form.description}
            onChangeText={(v) => setForm({ ...form, description: v })}
          />
          <TextInput
            style={s.input}
            placeholder="Due date (YYYY-MM-DD)"
            placeholderTextColor={theme.inkFaint}
            value={form.due_date}
            onChangeText={(v) => setForm({ ...form, due_date: v })}
          />
          {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}
          <Button
            label="Assign"
            onPress={() => create.mutate()}
            disabled={create.isPending || !form.title || !form.due_date}
          />
        </Card>
      )}

      {(list.data ?? []).length === 0 ? (
        <Card>
          <Empty text="You have not assigned any homework yet." />
        </Card>
      ) : (
        list.data!.map((item) => (
          <Card key={item.id}>
            <Pressable onPress={() => setOpen(open === item.id ? null : item.id)}>
              <Row
                left={
                  <>
                    <Pill label={`${item.subject} - ${item.class_label}`} />
                    <Text style={[s.title, { marginTop: 4 }]}>{item.title}</Text>
                    <Text style={s.meta}>Due {item.due_date}</Text>
                  </>
                }
                right={
                  <Text style={{ fontWeight: "600" }}>
                    {item.submitted_count}/{item.total_students}
                  </Text>
                }
              />
            </Pressable>

            {open === item.id &&
              (submissions.data ?? []).map((sub) => (
                <Row
                  key={sub.student_id}
                  left={
                    <>
                      <Text style={s.title}>
                        {sub.roll_no}. {sub.full_name}
                      </Text>
                      {sub.answer_text ? (
                        <Text style={s.meta} numberOfLines={2}>
                          {sub.answer_text}
                        </Text>
                      ) : null}
                    </>
                  }
                  right={
                    sub.submitted ? (
                      <Pill status={sub.late ? "pending" : "submitted"} label={sub.late ? "Late" : "Submitted"} />
                    ) : (
                      <Pill status="absent" label="Not submitted" />
                    )
                  }
                />
              ))}
          </Card>
        ))
      )}
    </Screen>
  );
}

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={{
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: theme.radius.pill,
        backgroundColor: on ? theme.primary : theme.ground,
      }}
    >
      <Text style={{ fontSize: 12, color: on ? "#fff" : theme.inkSoft }}>{label}</Text>
    </Pressable>
  );
}
