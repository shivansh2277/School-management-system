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
  enrolment_id?: number;
  full_name: string;
  roll_no: number;
  marks_obtained: string | number | null;
  is_absent?: boolean;
  is_exempted?: boolean;
};

function getCbseGrade(marks: number, max: number): { grade: string; color: string } {
  if (max <= 0) return { grade: "-", color: theme.inkFaint };
  const pct = (marks / max) * 100;
  if (pct >= 91) return { grade: "A1", color: "#15803D" };
  if (pct >= 81) return { grade: "A2", color: "#16A34A" };
  if (pct >= 71) return { grade: "B1", color: "#0D9488" };
  if (pct >= 61) return { grade: "B2", color: "#2563EB" };
  if (pct >= 51) return { grade: "C1", color: "#D97706" };
  if (pct >= 41) return { grade: "C2", color: "#EA580C" };
  if (pct >= 33) return { grade: "D", color: "#E11D48" };
  return { grade: "E", color: "#DC2626" };
}

export default function TeacherResults() {
  const qc = useQueryClient();
  const [open, setOpen] = useState<Paper | null>(null);
  const [values, setValues] = useState<Record<number, string>>({});
  const [absentMap, setAbsentMap] = useState<Record<number, boolean>>({});
  const [exemptMap, setExemptMap] = useState<Record<number, boolean>>({});
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
    const vMap: Record<number, string> = {};
    const aMap: Record<number, boolean> = {};
    const eMap: Record<number, boolean> = {};
    for (const r of roster.data) {
      const id = r.enrolment_id ?? r.student_id;
      vMap[id] = r.marks_obtained === null ? "" : String(Number(r.marks_obtained));
      aMap[id] = Boolean(r.is_absent);
      eMap[id] = Boolean(r.is_exempted);
    }
    setValues(vMap);
    setAbsentMap(aMap);
    setExemptMap(eMap);
    setNote(null);
  }, [roster.data]);

  const save = useMutation({
    mutationFn: () =>
      api.post("/teacher/marks", {
        exam_schedule_id: open!.id,
        entries: (roster.data ?? []).map((r) => {
          const id = r.enrolment_id ?? r.student_id;
          const isAbs = Boolean(absentMap[id]);
          const isEx = Boolean(exemptMap[id]);
          const raw = values[id] ?? "";
          return {
            enrolment_id: r.enrolment_id,
            student_id: r.student_id,
            marks_obtained: isAbs || isEx || raw.trim() === "" ? null : Number(raw),
            is_absent: isAbs,
            is_exempted: isEx,
          };
        }),
      }),
    onSuccess: () => {
      setNote("Marks successfully recorded.");
      qc.invalidateQueries({ queryKey: ["teacher-papers"] });
      qc.invalidateQueries({ queryKey: ["marks-roster"] });
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (papers.isLoading) return <Loading />;

  const max = open ? Number(open.max_marks) : 0;
  const invalid = Object.entries(values).some(([id, v]) => {
    const numId = Number(id);
    if (absentMap[numId] || exemptMap[numId]) return false;
    return v.trim() !== "" && (Number.isNaN(Number(v)) || Number(v) < 0 || Number(v) > max);
  });

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
                      {p.exam_name} - {p.exam_date} - Max marks: {Number(p.max_marks)}
                    </Text>
                  </>
                }
                right={
                  <Pill status={p.marks_entered ? "paid" : "pending"} label={p.marks_entered ? "Entered" : "Pending"} />
                }
              />
            </Pressable>

            {open?.id === p.id && (
              <View style={{ gap: 10, marginTop: 10, borderTopWidth: 1, borderTopColor: theme.rule, paddingTop: 10 }}>
                {(roster.data ?? []).map((r) => {
                  const id = r.enrolment_id ?? r.student_id;
                  const raw = values[id] ?? "";
                  const isAbs = Boolean(absentMap[id]);
                  const isEx = Boolean(exemptMap[id]);
                  const num = Number(raw);
                  const bad = !isAbs && !isEx && raw.trim() !== "" && (Number.isNaN(num) || num < 0 || num > max);
                  const cbse = !isAbs && !isEx && raw.trim() !== "" && !bad ? getCbseGrade(num, max) : null;

                  return (
                    <View
                      key={id}
                      style={{
                        paddingVertical: 8,
                        borderBottomWidth: 1,
                        borderBottomColor: theme.rule,
                      }}
                    >
                      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                        <Text style={[s.title, { flex: 1 }]}>
                          {r.roll_no}. {r.full_name}
                        </Text>
                        {cbse && (
                          <View
                            style={{
                              paddingHorizontal: 8,
                              paddingVertical: 2,
                              borderRadius: 4,
                              backgroundColor: `${cbse.color}20`,
                              marginRight: 8,
                            }}
                          >
                            <Text style={{ fontSize: 11, fontWeight: "700", color: cbse.color }}>
                              CBSE: {cbse.grade}
                            </Text>
                          </View>
                        )}
                      </View>

                      <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 6 }}>
                        {/* Status chips */}
                        <Pressable
                          onPress={() => {
                            setAbsentMap({ ...absentMap, [id]: false });
                            setExemptMap({ ...exemptMap, [id]: false });
                          }}
                          style={{
                            paddingHorizontal: 8,
                            paddingVertical: 4,
                            borderRadius: 4,
                            backgroundColor: !isAbs && !isEx ? theme.primary : theme.ground,
                          }}
                        >
                          <Text style={{ fontSize: 11, color: !isAbs && !isEx ? "#fff" : theme.inkSoft }}>Present</Text>
                        </Pressable>

                        <Pressable
                          onPress={() => {
                            setAbsentMap({ ...absentMap, [id]: true });
                            setExemptMap({ ...exemptMap, [id]: false });
                          }}
                          style={{
                            paddingHorizontal: 8,
                            paddingVertical: 4,
                            borderRadius: 4,
                            backgroundColor: isAbs ? theme.danger : theme.ground,
                          }}
                        >
                          <Text style={{ fontSize: 11, color: isAbs ? "#fff" : theme.inkSoft }}>Absent (A)</Text>
                        </Pressable>

                        <Pressable
                          onPress={() => {
                            setAbsentMap({ ...absentMap, [id]: false });
                            setExemptMap({ ...exemptMap, [id]: true });
                          }}
                          style={{
                            paddingHorizontal: 8,
                            paddingVertical: 4,
                            borderRadius: 4,
                            backgroundColor: isEx ? "#8B5CF6" : theme.ground,
                          }}
                        >
                          <Text style={{ fontSize: 11, color: isEx ? "#fff" : theme.inkSoft }}>Exempted</Text>
                        </Pressable>

                        <View style={{ flex: 1, alignItems: "flex-end" }}>
                          {!isAbs && !isEx ? (
                            <TextInput
                              style={[
                                s.input,
                                { width: 80, textAlign: "right", paddingVertical: 4 },
                                bad && { borderColor: theme.danger },
                              ]}
                              keyboardType="numeric"
                              placeholder={`0-${max}`}
                              placeholderTextColor={theme.inkFaint}
                              value={raw}
                              onChangeText={(v) => setValues({ ...values, [id]: v })}
                            />
                          ) : (
                            <Text style={{ fontSize: 12, fontWeight: "600", color: isAbs ? theme.danger : "#8B5CF6" }}>
                              {isAbs ? "ABSENT" : "EXEMPTED"}
                            </Text>
                          )}
                        </View>
                      </View>
                    </View>
                  );
                })}
                {invalid ? (
                  <Text style={{ color: theme.danger }}>Each mark must be a valid number between 0 and {max}.</Text>
                ) : null}
                {note ? <Text style={[s.meta, { color: theme.success }]}>{note}</Text> : null}
                <Button
                  label="Save Marks"
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
