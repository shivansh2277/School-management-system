import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Linking, Modal, Pressable, Text, TextInput, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

function formatLocalDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function getTodayStr(): string {
  return formatLocalDate(new Date());
}

function isDateInPast(dStr: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dStr.trim())) return false;
  return dStr.trim() < getTodayStr();
}

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
  const [datePickerVisible, setDatePickerVisible] = useState(false);
  const [pickerMonth, setPickerMonth] = useState(() => new Date());

  const isPast = composing && Boolean(form.due_date && isDateInPast(form.due_date));

  const quickSelect = (daysOffset: number) => {
    const d = new Date();
    d.setDate(d.getDate() + daysOffset);
    const dateStr = formatLocalDate(d);
    setForm((prev) => ({ ...prev, due_date: dateStr }));
    setDatePickerVisible(false);
    setError(null);
  };

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
          <Text style={s.meta}>Due Date</Text>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <TextInput
              style={[s.input, { flex: 1, marginBottom: 0 }]}
              placeholder="Due date (YYYY-MM-DD)"
              placeholderTextColor={theme.inkFaint}
              value={form.due_date}
              onChangeText={(v) => {
                setForm({ ...form, due_date: v });
                setError(null);
              }}
            />
            <Pressable
              onPress={() => setDatePickerVisible(true)}
              accessibilityRole="button"
              accessibilityLabel="Open calendar date picker"
              style={{
                width: 44,
                height: 44,
                borderRadius: theme.radius.input,
                backgroundColor: theme.primarySoft,
                alignItems: "center",
                justifyContent: "center",
                borderWidth: 1,
                borderColor: theme.rule,
              }}
            >
              <Ionicons name="calendar-outline" size={22} color={theme.primary} />
            </Pressable>
          </View>

          {/* Quick chips directly under due date input */}
          <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap", marginTop: 4, marginBottom: 8 }}>
            <Pressable
              onPress={() => quickSelect(0)}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: form.due_date === getTodayStr() ? theme.primary : theme.ground,
              }}
            >
              <Text style={{ fontSize: 12, color: form.due_date === getTodayStr() ? "#fff" : theme.inkSoft }}>Today</Text>
            </Pressable>
            <Pressable
              onPress={() => quickSelect(1)}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.ground,
              }}
            >
              <Text style={{ fontSize: 12, color: theme.inkSoft }}>Tomorrow</Text>
            </Pressable>
            <Pressable
              onPress={() => quickSelect(3)}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.ground,
              }}
            >
              <Text style={{ fontSize: 12, color: theme.inkSoft }}>In 3 Days</Text>
            </Pressable>
            <Pressable
              onPress={() => quickSelect(7)}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 5,
                borderRadius: theme.radius.pill,
                backgroundColor: theme.ground,
              }}
            >
              <Text style={{ fontSize: 12, color: theme.inkSoft }}>In 1 Week</Text>
            </Pressable>
          </View>

          {isPast && (
            <Text style={{ color: theme.danger, fontSize: 12, marginTop: -4, marginBottom: 4 }}>
              Due date cannot be set in the past for new homework assignments.
            </Text>
          )}

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
            disabled={create.isPending || !form.title || !form.due_date || isPast}
          />
        </Card>
      )}

      {/* Calendar Date Picker Modal */}
      <Modal
        visible={datePickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setDatePickerVisible(false)}
      >
        <View
          style={{
            flex: 1,
            backgroundColor: "rgba(0,0,0,0.5)",
            justifyContent: "center",
            alignItems: "center",
            padding: 16,
          }}
        >
          <View
            style={{
              width: "100%",
              maxWidth: 360,
              backgroundColor: theme.surface,
              borderRadius: theme.radius.card,
              padding: 16,
              shadowColor: "#000",
              shadowOpacity: 0.15,
              shadowRadius: 10,
              elevation: 5,
            }}
          >
            {/* Header: Month / Year with arrows */}
            <View
              style={{
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Previous month"
                onPress={() => setPickerMonth(new Date(pickerMonth.getFullYear(), pickerMonth.getMonth() - 1, 1))}
                style={{ padding: 6, borderRadius: 6, backgroundColor: theme.ground }}
              >
                <Ionicons name="chevron-back" size={20} color={theme.ink} />
              </Pressable>
              <Text style={{ fontSize: 16, fontWeight: "600", color: theme.ink }}>
                {pickerMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
              </Text>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Next month"
                onPress={() => setPickerMonth(new Date(pickerMonth.getFullYear(), pickerMonth.getMonth() + 1, 1))}
                style={{ padding: 6, borderRadius: 6, backgroundColor: theme.ground }}
              >
                <Ionicons name="chevron-forward" size={20} color={theme.ink} />
              </Pressable>
            </View>

            {/* Quick Chips inside modal */}
            <Text style={[s.meta, { marginBottom: 6 }]}>Quick select:</Text>
            <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
              <Pressable
                onPress={() => quickSelect(0)}
                style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: theme.radius.pill, backgroundColor: theme.ground }}
              >
                <Text style={{ fontSize: 12, color: theme.inkSoft }}>Today</Text>
              </Pressable>
              <Pressable
                onPress={() => quickSelect(1)}
                style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: theme.radius.pill, backgroundColor: theme.ground }}
              >
                <Text style={{ fontSize: 12, color: theme.inkSoft }}>Tomorrow</Text>
              </Pressable>
              <Pressable
                onPress={() => quickSelect(3)}
                style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: theme.radius.pill, backgroundColor: theme.ground }}
              >
                <Text style={{ fontSize: 12, color: theme.inkSoft }}>In 3 Days</Text>
              </Pressable>
              <Pressable
                onPress={() => quickSelect(7)}
                style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: theme.radius.pill, backgroundColor: theme.ground }}
              >
                <Text style={{ fontSize: 12, color: theme.inkSoft }}>In 1 Week</Text>
              </Pressable>
            </View>

            {/* Day of week headers */}
            <View style={{ flexDirection: "row", marginBottom: 6 }}>
              {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((dayName) => (
                <Text key={dayName} style={{ flex: 1, textAlign: "center", fontSize: 12, fontWeight: "600", color: theme.inkFaint }}>
                  {dayName}
                </Text>
              ))}
            </View>

            {/* Calendar days grid */}
            <View style={{ flexDirection: "row", flexWrap: "wrap" }}>
              {Array.from({ length: new Date(pickerMonth.getFullYear(), pickerMonth.getMonth(), 1).getDay() }).map((_, i) => (
                <View key={`filler-${i}`} style={{ width: "14.28%", height: 38 }} />
              ))}
              {Array.from({ length: new Date(pickerMonth.getFullYear(), pickerMonth.getMonth() + 1, 0).getDate() }).map((_, i) => {
                const dayNum = i + 1;
                const currentDayDate = new Date(pickerMonth.getFullYear(), pickerMonth.getMonth(), dayNum);
                const dateStr = formatLocalDate(currentDayDate);
                const isSelected = form.due_date === dateStr;
                const isToday = dateStr === getTodayStr();
                const past = isDateInPast(dateStr);

                return (
                  <Pressable
                    key={`day-${dayNum}`}
                    onPress={() => {
                      setForm((prev) => ({ ...prev, due_date: dateStr }));
                      setDatePickerVisible(false);
                      setError(null);
                    }}
                    accessibilityRole="button"
                    accessibilityLabel={`Select ${dateStr}`}
                    style={{
                      width: "14.28%",
                      height: 38,
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: 19,
                      backgroundColor: isSelected ? theme.primary : isToday ? theme.primarySoft : "transparent",
                    }}
                  >
                    <Text
                      style={{
                        fontSize: 13,
                        fontWeight: isSelected || isToday ? "700" : "400",
                        color: isSelected ? "#ffffff" : past ? theme.inkFaint : theme.ink,
                      }}
                    >
                      {dayNum}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            {/* Close Button */}
            <View style={{ marginTop: 14 }}>
              <Button label="Close" tone="ghost" onPress={() => setDatePickerVisible(false)} />
            </View>
          </View>
        </View>
      </Modal>

      {(list.data ?? []).length === 0 ? (
        <Card>
          <Empty text="You have not assigned any homework yet." />
        </Card>
      ) : (
        list.data!.map((item) => {
          const ratio = item.total_students > 0 ? (item.submitted_count / item.total_students) * 100 : 0;
          const isExpanded = open === item.id;

          return (
            <Card key={item.id}>
              <Pressable onPress={() => setOpen(isExpanded ? null : item.id)}>
                {/* Header Pills: Subject, Class, Due Date */}
                <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                  <View style={{ flexDirection: "row", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                    <View
                      style={{
                        paddingHorizontal: 8,
                        paddingVertical: 3,
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.primarySoft,
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>{item.subject}</Text>
                    </View>
                    <View
                      style={{
                        paddingHorizontal: 8,
                        paddingVertical: 3,
                        borderRadius: theme.radius.pill,
                        backgroundColor: theme.ground,
                        borderWidth: 1,
                        borderColor: theme.rule,
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft }}>{item.class_label}</Text>
                    </View>
                  </View>
                  <Text style={{ fontSize: 11, color: theme.inkFaint }}>Due {formatDate(item.due_date)}</Text>
                </View>

                {/* Title */}
                <Text style={[s.title, { fontSize: 15, color: theme.ink, marginBottom: 8 }]}>{item.title}</Text>

                {item.attachment_url ? (
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 8 }}>
                    <Ionicons name="attach" size={14} color={theme.primary} />
                    <Text style={{ fontSize: 11, color: theme.primary, fontWeight: "500" }}>Attachment attached</Text>
                  </View>
                ) : null}

                {/* Submission Progress Bar */}
                <View style={{ marginTop: 4 }}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                    <Text style={{ fontSize: 11, color: theme.inkFaint }}>Submissions</Text>
                    <Text style={{ fontSize: 12, fontWeight: "700", color: theme.ink }}>
                      {item.submitted_count} / {item.total_students} ({Math.round(ratio)}%)
                    </Text>
                  </View>
                  <View style={{ height: 6, borderRadius: 3, backgroundColor: theme.rule, overflow: "hidden" }}>
                    <View
                      style={{
                        width: `${Math.min(100, ratio)}%`,
                        height: "100%",
                        backgroundColor: ratio === 100 ? theme.success : theme.primary,
                        borderRadius: 3,
                      }}
                    />
                  </View>
                </View>

                <View style={{ flexDirection: "row", justifyContent: "flex-end", alignItems: "center", gap: 4, marginTop: 10 }}>
                  <Text style={{ fontSize: 12, fontWeight: "600", color: theme.primary }}>
                    {isExpanded ? "Hide Submissions" : "View Submissions"}
                  </Text>
                  <Ionicons name={isExpanded ? "chevron-up" : "chevron-down"} size={14} color={theme.primary} />
                </View>
              </Pressable>

              {isExpanded && (
                <View style={{ marginTop: 12, borderTopWidth: 1, borderTopColor: theme.rule, paddingTop: 10 }}>
                  <Text style={[s.meta, { fontWeight: "700", color: theme.ink, marginBottom: 8 }]}>Student Submissions & Grading</Text>
                  {(submissions.data ?? []).map((sub) => {
                    const subIdentifier = sub.id ?? sub.enrolment_id ?? sub.student_id;
                    const isGradingThis = gradingSubId === subIdentifier;
                    return (
                      <View
                        key={sub.student_id}
                        style={{
                          paddingVertical: 10,
                          borderBottomWidth: 1,
                          borderBottomColor: theme.rule,
                        }}
                      >
                        <Row
                          left={
                            <View style={{ flex: 1, marginRight: 8 }}>
                              <Text style={[s.title, { fontSize: 13, color: theme.ink }]}>
                                {sub.roll_no}. {sub.full_name}
                              </Text>
                              {sub.answer_text ? (
                                <Text style={[s.meta, { marginTop: 2 }]} numberOfLines={2}>
                                  {sub.answer_text}
                                </Text>
                              ) : null}
                              {sub.attachment_url ? (
                                <Pressable onPress={() => sub.attachment_url && Linking.openURL(sub.attachment_url)} style={{ marginTop: 4 }}>
                                  <Text style={[s.meta, { color: theme.primary, textDecorationLine: "underline" }]}>
                                    📎 View submitted work
                                  </Text>
                                </Pressable>
                              ) : null}
                              {sub.marks !== null && sub.marks !== undefined ? (
                                <Text style={{ fontSize: 11, color: theme.success, fontWeight: "700", marginTop: 4 }}>
                                  ✓ Graded: {Number(sub.marks)} marks {sub.remarks ? `(${sub.remarks})` : ""}
                                </Text>
                              ) : null}
                            </View>
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
                                    paddingHorizontal: 10,
                                    paddingVertical: 4,
                                    borderRadius: theme.radius.pill,
                                    backgroundColor: theme.primarySoft,
                                  }}
                                >
                                  <Text style={{ fontSize: 11, color: theme.primary, fontWeight: "700" }}>
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
                              padding: 12,
                              backgroundColor: theme.ground,
                              borderRadius: theme.radius.input,
                              borderWidth: 1,
                              borderColor: theme.rule,
                              gap: 8,
                            }}
                          >
                            <Text style={{ fontSize: 12, fontWeight: "700", color: theme.ink }}>
                              Evaluate {sub.full_name}'s Submission
                            </Text>
                            <TextInput
                              style={[s.input, { backgroundColor: theme.surface, marginBottom: 0 }]}
                              placeholder="Marks (e.g. 8.5)"
                              placeholderTextColor={theme.inkFaint}
                              keyboardType="numeric"
                              value={gradeMarks}
                              onChangeText={setGradeMarks}
                            />
                            <TextInput
                              style={[s.input, { backgroundColor: theme.surface, marginBottom: 0 }]}
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
          );
        })
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
