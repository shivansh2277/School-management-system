import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Linking, Pressable, Text, TextInput, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
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
  attachment_url?: string | null;
  submitted_count: number;
  total_students: number;
};
type Submission = {
  id?: number | null;
  student_id: number;
  enrolment_id?: number | null;
  full_name: string;
  roll_no: number;
  submitted: boolean;
  late: boolean;
  answer_text: string | null;
  marks?: number | string | null;
  remarks?: string | null;
  graded_at?: string | null;
  attachment_url?: string | null;
};

export default function TeacherHomework() {
  const qc = useQueryClient();
  const [open, setOpen] = useState<number | null>(null);
  const [composing, setComposing] = useState(false);
  const [gradingSubId, setGradingSubId] = useState<number | null>(null);
  const [gradeMarks, setGradeMarks] = useState<string>("");
  const [gradeRemarks, setGradeRemarks] = useState<string>("");
  const [form, setForm] = useState({
    class_section_id: "",
    subject_id: "",
    title: "",
    description: "",
    due_date: "",
    attachment_url: "",
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
        attachment_url: form.attachment_url.trim() || undefined,
      }),
    onSuccess: () => {
      setComposing(false);
      setError(null);
      setForm({ class_section_id: "", subject_id: "", title: "", description: "", due_date: "", attachment_url: "" });
      qc.invalidateQueries({ queryKey: ["teacher-homework"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const saveGrade = useMutation({
    mutationFn: ({ subId, marks, remarks }: { subId: number; marks: number | null; remarks: string | null }) =>
      api.patch(`/teacher/homework/submissions/${subId}`, {
        marks,
        remarks,
      }),
    onSuccess: () => {
      setGradingSubId(null);
      setGradeMarks("");
      setGradeRemarks("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["teacher-submissions", open] });
    },
    onError: (e: Error) => setError(e.message),
  });

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
            placeholder="Description / instructions"
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
          <TextInput
            style={s.input}
            placeholder="Attachment URL (optional PDF / Worksheet)"
            placeholderTextColor={theme.inkFaint}
            value={form.attachment_url}
            onChangeText={(v) => setForm({ ...form, attachment_url: v })}
          />
          {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}
          <Button
            label="Assign Homework"
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
                    <Text style={s.meta}>Due {formatDate(item.due_date)}</Text>
                    {item.attachment_url ? (
                      <Text style={[s.meta, { color: theme.primary }]}>📎 Attachment attached</Text>
                    ) : null}
                  </>
                }
                right={
                  <Text style={{ fontWeight: "600" }}>
                    {item.submitted_count}/{item.total_students}
                  </Text>
                }
              />
            </Pressable>

            {open === item.id && (
              <View style={{ marginTop: 12, borderTopWidth: 1, borderTopColor: theme.rule, paddingTop: 10 }}>
                <Text style={[s.meta, { fontWeight: "600", marginBottom: 8 }]}>Student Submissions & Grading</Text>
                {(submissions.data ?? []).map((sub) => {
                  const subIdentifier = sub.id ?? sub.enrolment_id ?? sub.student_id;
                  const isGradingThis = gradingSubId === subIdentifier;
                  return (
                    <View
                      key={sub.student_id}
                      style={{
                        paddingVertical: 8,
                        borderBottomWidth: 1,
                        borderBottomColor: theme.rule,
                      }}
                    >
                      <Row
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
                            {sub.attachment_url ? (
                              <Pressable onPress={() => sub.attachment_url && Linking.openURL(sub.attachment_url)}>
                                <Text style={[s.meta, { color: theme.primary, textDecorationLine: "underline" }]}>
                                  📎 View submitted work
                                </Text>
                              </Pressable>
                            ) : null}
                            {sub.marks !== null && sub.marks !== undefined ? (
                              <Text style={{ fontSize: 12, color: theme.success, fontWeight: "600", marginTop: 2 }}>
                                Graded: {Number(sub.marks)} marks {sub.remarks ? `(${sub.remarks})` : ""}
                              </Text>
                            ) : null}
                          </>
                        }
                        right={
                          <View style={{ alignItems: "flex-end", gap: 4 }}>
                            {sub.submitted ? (
                              <Pill status={sub.late ? "pending" : "submitted"} label={sub.late ? "Late" : "Submitted"} />
                            ) : (
                              <Pill status="absent" label="Not submitted" />
                            )}
                            {sub.submitted && (
                              <Pressable
                                onPress={() => {
                                  if (isGradingThis) {
                                    setGradingSubId(null);
                                  } else {
                                    setGradingSubId(subIdentifier);
                                    setGradeMarks(sub.marks !== null && sub.marks !== undefined ? String(sub.marks) : "");
                                    setGradeRemarks(sub.remarks ?? "");
                                  }
                                }}
                                style={{
                                  paddingHorizontal: 8,
                                  paddingVertical: 3,
                                  borderRadius: 4,
                                  backgroundColor: theme.ground,
                                }}
                              >
                                <Text style={{ fontSize: 11, color: theme.primary, fontWeight: "600" }}>
                                  {isGradingThis ? "Cancel" : sub.marks != null ? "Edit Grade" : "Grade"}
                                </Text>
                              </Pressable>
                            )}
                          </View>
                        }
                      />

                      {isGradingThis && (
                        <View
                          style={{
                            marginTop: 8,
                            padding: 10,
                            backgroundColor: theme.ground,
                            borderRadius: theme.radius.input,
                            gap: 8,
                          }}
                        >
                          <Text style={{ fontSize: 12, fontWeight: "600", color: theme.ink }}>
                            Evaluate {sub.full_name}'s Submission
                          </Text>
                          <TextInput
                            style={[s.input, { backgroundColor: theme.surface }]}
                            placeholder="Marks (e.g. 8.5)"
                            placeholderTextColor={theme.inkFaint}
                            keyboardType="numeric"
                            value={gradeMarks}
                            onChangeText={setGradeMarks}
                          />
                          <TextInput
                            style={[s.input, { backgroundColor: theme.surface }]}
                            placeholder="Teacher Remarks / Feedback"
                            placeholderTextColor={theme.inkFaint}
                            value={gradeRemarks}
                            onChangeText={setGradeRemarks}
                          />
                          <Button
                            label={saveGrade.isPending ? "Saving..." : "Save Grade"}
                            onPress={() =>
                              saveGrade.mutate({
                                subId: subIdentifier,
                                marks: gradeMarks.trim() !== "" ? Number(gradeMarks) : null,
                                remarks: gradeRemarks.trim() || null,
                              })
                            }
                            disabled={saveGrade.isPending}
                          />
                        </View>
                      )}
                    </View>
                  );
                })}
              </View>
            )}
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
