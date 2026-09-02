import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ClassRow = { class_section_id: number; class_label: string };
type Notice = {
  id: number;
  title: string;
  body: string;
  class_label: string | null;
  published_at: string;
};

export default function TeacherAnnouncements() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ title: "", body: "", class_section_id: "" });
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const classes = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => api.get<ClassRow[]>("/teacher/classes"),
  });
  const mine = useQuery({
    queryKey: ["teacher-announcements"],
    queryFn: () => api.get<Notice[]>("/teacher/announcements"),
  });

  const publish = useMutation({
    mutationFn: () =>
      api.post("/teacher/announcements", {
        title: form.title,
        body: form.body,
        class_section_id: Number(form.class_section_id),
      }),
    onSuccess: () => {
      // Keep the selected class: publishing again to the same section is the
      // normal next action, and clearing it silently disabled the button.
      setForm((f) => ({ ...f, title: "", body: "" }));
      setError(null);
      setNote("Published.");
      qc.invalidateQueries({ queryKey: ["teacher-announcements"] });
    },
    onError: (e: Error) => {
      setNote(null);
      setError(e.message);
    },
  });

  if (mine.isLoading) return <Loading />;

  return (
    <Screen>
      <Card title="New announcement">
        <Text style={s.meta}>
          Reaches the students of the section you pick and their parents. School-wide notices are
          published by the office.
        </Text>
        <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
          {(classes.data ?? []).map((c) => {
            const on = form.class_section_id === String(c.class_section_id);
            return (
              <Pressable
                key={c.class_section_id}
                onPress={() => setForm({ ...form, class_section_id: String(c.class_section_id) })}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: theme.radius.pill,
                  backgroundColor: on ? theme.primary : theme.ground,
                }}
              >
                <Text style={{ fontSize: 12, color: on ? "#fff" : theme.inkSoft }}>
                  {c.class_label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <TextInput
          style={s.input}
          placeholder="Title"
          placeholderTextColor={theme.inkFaint}
          value={form.title}
          onChangeText={(v) => {
            setNote(null);
            setForm({ ...form, title: v });
          }}
        />
        <TextInput
          style={[s.input, { minHeight: 80, textAlignVertical: "top" }]}
          multiline
          placeholder="Message"
          placeholderTextColor={theme.inkFaint}
          value={form.body}
          onChangeText={(v) => setForm({ ...form, body: v })}
        />
        {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}
        {note ? <Text style={{ color: theme.success }}>{note}</Text> : null}
        <Button
          label="Publish"
          onPress={() => publish.mutate()}
          disabled={publish.isPending || !form.title || !form.body || !form.class_section_id}
        />
      </Card>

      <Card title="Published">
        {(mine.data ?? []).length === 0 ? (
          <Empty text="You have not published anything yet." />
        ) : (
          mine.data!.map((n) => (
            <Row
              key={n.id}
              left={
                <>
                  <Text style={s.title}>{n.title}</Text>
                  <Text style={s.meta}>{n.class_label}</Text>
                </>
              }
              right={<Text style={s.meta}>{new Date(n.published_at).toLocaleDateString()}</Text>}
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
