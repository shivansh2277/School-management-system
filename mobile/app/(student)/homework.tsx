import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Item = {
  id: number;
  title: string;
  description: string | null;
  subject: string;
  due_date: string;
  submitted: boolean;
  late: boolean;
  answer_text: string | null;
};

const FILTERS = ["pending", "submitted", "all"] as const;

export default function StudentHomework() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("pending");
  const [open, setOpen] = useState<Item | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["student-homework", filter],
    queryFn: () => api.get<Item[]>(`/student/homework?status=${filter}`),
  });

  const submit = useMutation({
    mutationFn: (id: number) => api.post(`/student/homework/${id}/submit`, { answer_text: answer }),
    onSuccess: () => {
      setOpen(null);
      setAnswer("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["student-homework"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  if (isLoading) return <Loading />;

  const overdue = (item: Item) => !item.submitted && new Date(item.due_date) < new Date();

  return (
    <Screen>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {FILTERS.map((f) => (
          <Pressable
            key={f}
            onPress={() => setFilter(f)}
            style={{
              flex: 1,
              paddingVertical: 8,
              borderRadius: theme.radius.input,
              alignItems: "center",
              backgroundColor: filter === f ? theme.primary : theme.surface,
            }}
          >
            <Text
              style={{
                color: filter === f ? "#fff" : theme.inkSoft,
                fontSize: 12,
                textTransform: "capitalize",
              }}
            >
              {f}
            </Text>
          </Pressable>
        ))}
      </View>

      {(data ?? []).length === 0 ? (
        <Card>
          <Empty text="Nothing here." />
        </Card>
      ) : (
        data!.map((item) => (
          <Card key={item.id}>
            <Pressable
              onPress={() => {
                setOpen(open?.id === item.id ? null : item);
                setAnswer(item.answer_text ?? "");
                setError(null);
              }}
            >
              <Row
                left={
                  <>
                    <Pill label={item.subject} />
                    <Text style={[s.title, { marginTop: 4 }]}>{item.title}</Text>
                    <Text style={s.meta}>Due {item.due_date}</Text>
                  </>
                }
                right={
                  item.submitted ? (
                    <Pill status="submitted" label={item.late ? "Late" : "Submitted"} />
                  ) : (
                    <Pill status={overdue(item) ? "overdue" : "pending"} label={overdue(item) ? "Overdue" : "Pending"} />
                  )
                }
              />
            </Pressable>

            {open?.id === item.id && (
              <View style={{ gap: 10 }}>
                <Text style={{ color: theme.inkSoft, fontSize: 13 }}>
                  {item.description ?? "No description."}
                </Text>
                <TextInput
                  style={[s.input, { minHeight: 90, textAlignVertical: "top" }]}
                  multiline
                  placeholder="Type your answer"
                  placeholderTextColor={theme.inkFaint}
                  value={answer}
                  onChangeText={setAnswer}
                />
                {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}
                <Button
                  label={item.submitted ? "Update answer" : "Submit"}
                  onPress={() => submit.mutate(item.id)}
                  disabled={submit.isPending || answer.trim().length === 0}
                />
              </View>
            )}
          </Card>
        ))
      )}
    </Screen>
  );
}
