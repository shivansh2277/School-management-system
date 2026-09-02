import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Paper = {
  id: number;
  exam_name: string;
  class_label: string;
  subject: string;
  exam_date: string;
  max_marks: string;
  marks_entered: boolean;
};

type RosterRow = {
  student_id: number;
  full_name: string;
  roll_no: number;
  marks_obtained: string | null;
};

export default function TeacherResults() {
  const qc = useQueryClient();
  const [open, setOpen] = useState<Paper | null>(null);
  const [values, setValues] = useState<Record<number, string>>({});
  const [note, setNote] = useState<string | null>(null);

  const papers = useQuery({
    queryKey: ["teacher-papers"],
    queryFn: () => api.get<Paper[]>("/teacher/exams"),
  });
  const roster = useQuery({
    queryKey: ["marks-roster", open?.id],
    queryFn: () => api.get<RosterRow[]>(`/teacher/marks?exam_schedule_id=${open!.id}`),
    enabled: open !== null,
  });

  useEffect(() => {
    if (!roster.data) return;
    setValues(
      Object.fromEntries(
        roster.data.map((r) => [r.student_id, r.marks_obtained === null ? "" : String(Number(r.marks_obtained))]),
      ),
    );
    setNote(null);
  }, [roster.data]);

  const save = useMutation({
    mutationFn: () =>
      api.post("/teacher/marks", {
        exam_schedule_id: open!.id,
        // A blank box means absent: no marks row is sent, so it stays out of the total.
        entries: Object.entries(values)
          .filter(([, v]) => v.trim() !== "")
          .map(([id, v]) => ({ student_id: Number(id), marks_obtained: v })),
      }),
    onSuccess: () => {
      setNote("Marks saved.");
      qc.invalidateQueries({ queryKey: ["teacher-papers"] });
      qc.invalidateQueries({ queryKey: ["marks-roster"] });
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (papers.isLoading) return <Loading />;

  const max = open ? Number(open.max_marks) : 0;
  const invalid = Object.values(values).some(
    (v) => v.trim() !== "" && (Number.isNaN(Number(v)) || Number(v) < 0 || Number(v) > max),
  );

  return (
    <Screen>
      {(papers.data ?? []).length === 0 ? (
        <Card>
          <Empty text="No exam papers scheduled for your subjects." />
        </Card>
      ) : (
        papers.data!.map((p) => (
          <Card key={p.id}>
            <Pressable onPress={() => setOpen(open?.id === p.id ? null : p)}>
              <Row
                left={
                  <>
                    <Text style={s.title}>
                      {p.subject} - {p.class_label}
                    </Text>
                    <Text style={s.meta}>
                      {p.exam_name} - {p.exam_date} - max {Number(p.max_marks)}
                    </Text>
                  </>
                }
                right={
                  <Pill status={p.marks_entered ? "paid" : "pending"} label={p.marks_entered ? "Entered" : "Pending"} />
                }
              />
            </Pressable>

            {open?.id === p.id && (
              <View style={{ gap: 8 }}>
                {(roster.data ?? []).map((r) => {
                  const raw = values[r.student_id] ?? "";
                  const bad = raw.trim() !== "" && (Number.isNaN(Number(raw)) || Number(raw) < 0 || Number(raw) > max);
                  return (
                    <View
                      key={r.student_id}
                      style={{ flexDirection: "row", alignItems: "center", gap: 10 }}
                    >
                      <Text style={[s.title, { flex: 1 }]}>
                        {r.roll_no}. {r.full_name}
                      </Text>
                      <TextInput
                        style={[
                          s.input,
                          { width: 90, textAlign: "right" },
                          bad && { borderColor: theme.danger },
                        ]}
                        keyboardType="numeric"
                        placeholder="-"
                        placeholderTextColor={theme.inkFaint}
                        value={raw}
                        onChangeText={(v) => setValues({ ...values, [r.student_id]: v })}
                      />
                    </View>
                  );
                })}
                {invalid ? (
                  <Text style={{ color: theme.danger }}>Marks must be between 0 and {max}.</Text>
                ) : null}
                {note ? <Text style={s.meta}>{note}</Text> : null}
                <Button
                  label="Save marks"
                  onPress={() => save.mutate()}
                  disabled={save.isPending || invalid}
                />
              </View>
            )}
          </Card>
        ))
      )}
    </Screen>
  );
}
