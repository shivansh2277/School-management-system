import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Linking, Pressable, Text, TextInput, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Item = {
  id: number;
  title: string;
  description: string | null;
  subject: string;
  due_date: string;
  attachment_url?: string | null;
  submitted: boolean;
  late: boolean;
  answer_text: string | null;
  marks?: number | string | null;
  remarks?: string | null;
  graded_at?: string | null;
};

const FILTERS = ["pending", "submitted", "graded", "all"] as const;
type Filter = (typeof FILTERS)[number];

export default function StudentHomework() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Filter>("pending");
  const [open, setOpen] = useState<Item | null>(null);
  const [answer, setAnswer] = useState("");
  const [attachmentUrl, setAttachmentUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["student-homework"],
    queryFn: () => api.get<Item[]>("/student/homework?status=all"),
  });

  const submit = useMutation({
    mutationFn: (id: number) =>
      api.post(`/student/homework/${id}/submit`, {
        answer_text: answer,
        attachment_url: attachmentUrl.trim() || undefined,
      }),
    onSuccess: () => {
      setOpen(null);
      setAnswer("");
      setAttachmentUrl("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["student-homework"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  if (isLoading) return <Loading />;

  const overdue = (item: Item) => !item.submitted && new Date(item.due_date) < new Date();

  const allItems = data ?? [];
  const filtered = allItems.filter((item) => {
    const isGraded = item.marks !== null && item.marks !== undefined;
    if (filter === "pending") return !item.submitted;
    if (filter === "submitted") return item.submitted && !isGraded;
    if (filter === "graded") return isGraded;
    return true;
  });

  return (
    <Screen>
      {/* Filter Tabs */}
      <View style={{ flexDirection: "row", gap: 6, marginBottom: 12 }}>
        {FILTERS.map((f) => {
          const on = filter === f;
          return (
            <Pressable
              key={f}
              onPress={() => setFilter(f)}
              style={{
                flex: 1,
                paddingVertical: 8,
                borderRadius: theme.radius.pill,
                alignItems: "center",
                backgroundColor: on ? theme.primary : theme.surface,
                borderWidth: 1,
                borderColor: on ? theme.primary : theme.rule,
                ...theme.shadow,
              }}
            >
              <Text
                style={{
                  color: on ? "#fff" : theme.inkSoft,
                  fontSize: 12,
                  fontWeight: on ? "700" : "500",
                  textTransform: "capitalize",
                }}
              >
                {f}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {filtered.length === 0 ? (
        <Card>
          <Empty text={`No ${filter !== "all" ? filter : ""} homework assignments.`} />
        </Card>
      ) : (
        filtered.map((item) => {
          const isGraded = item.marks !== null && item.marks !== undefined;
          return (
            <Card key={item.id}>
              <Pressable
                onPress={() => {
                  setOpen(open?.id === item.id ? null : item);
                  setAnswer(item.answer_text ?? "");
                  setAttachmentUrl("");
                  setError(null);
                }}
              >
                <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                  <View
                    style={{
                      paddingHorizontal: 8,
                      paddingVertical: 2,
                      borderRadius: theme.radius.pill,
                      backgroundColor: theme.primarySoft,
                    }}
                  >
                    <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>{item.subject}</Text>
                  </View>
                  <Text style={{ fontSize: 11, color: theme.inkFaint }}>Due {formatDate(item.due_date)}</Text>
                </View>

                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.title, { fontSize: 15, color: theme.ink }]}>{item.title}</Text>
                    {item.attachment_url && (
                      <Pressable onPress={() => item.attachment_url && Linking.openURL(item.attachment_url)} style={{ marginTop: 4 }}>
                        <Text style={[s.meta, { color: theme.primary, textDecorationLine: "underline" }]}>
                          📎 Teacher Attachment
                        </Text>
                      </Pressable>
                    )}
                  </View>
                  {isGraded ? (
                    <View
                      style={{
                        paddingHorizontal: 8,
                        paddingVertical: 3,
                        borderRadius: theme.radius.pill,
                        backgroundColor: "#ECFDF5",
                        borderWidth: 1,
                        borderColor: "#A7F3D0",
                      }}
                    >
                      <Text style={{ fontSize: 11, fontWeight: "700", color: "#059669" }}>
                        Score: {item.marks}
                      </Text>
                    </View>
                  ) : item.submitted ? (
                    <Pill status="submitted" label={item.late ? "Late" : "Submitted"} />
                  ) : (
                    <Pill status={overdue(item) ? "overdue" : "pending"} label={overdue(item) ? "Overdue" : "Pending"} />
                  )}
                </View>
              </Pressable>

              {/* Graded Feedback Box */}
              {isGraded && (
                <View
                  style={{
                    backgroundColor: theme.ground,
                    borderLeftWidth: 3,
                    borderLeftColor: theme.success,
                    padding: 10,
                    borderRadius: theme.radius.input,
                    marginTop: 10,
                  }}
                >
                  <Text style={{ fontSize: 13, fontWeight: "700", color: theme.success }}>
                    ✓ Score: {item.marks} marks
                  </Text>
                  {item.remarks && (
                    <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 2 }}>
                      Teacher Feedback: "{item.remarks}"
                    </Text>
                  )}
                  {item.graded_at && (
                    <Text style={{ fontSize: 11, color: theme.inkFaint, marginTop: 2 }}>
                      Graded on {formatDate(item.graded_at)}
                    </Text>
                  )}
                </View>
              )}

              {/* Digital Turn-in Drawer */}
              {open?.id === item.id && (
                <View style={{ gap: 10, marginTop: 10, borderTopWidth: 1, borderTopColor: theme.rule, paddingTop: 10 }}>
                  <Text style={{ color: theme.inkSoft, fontSize: 13 }}>
                    {item.description ?? "No description provided."}
                  </Text>

                  <Text style={s.meta}>Your Answer / Notes:</Text>
                  <TextInput
                    style={[s.input, { minHeight: 80, textAlignVertical: "top" }]}
                    multiline
                    placeholder="Type your answer or solution notes..."
                    placeholderTextColor={theme.inkFaint}
                    value={answer}
                    onChangeText={setAnswer}
                  />

                  <Text style={s.meta}>File Attachment (Google Drive / Cloud URL):</Text>
                  <TextInput
                    style={s.input}
                    placeholder="https://... (Optional PDF or Image link)"
                    placeholderTextColor={theme.inkFaint}
                    value={attachmentUrl}
                    onChangeText={setAttachmentUrl}
                  />

                  {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}

                  <Button
                    label={item.submitted ? "Update Submission" : "Submit Homework"}
                    onPress={() => submit.mutate(item.id)}
                    disabled={submit.isPending || answer.trim().length === 0}
                  />
                </View>
              )}
            </Card>
          );
        })
      )}
    </Screen>
  );
}
