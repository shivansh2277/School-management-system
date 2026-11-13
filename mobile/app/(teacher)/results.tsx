import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

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

function getCbseGrade(marks: number, max: number): { grade: string; color: string; bg: string; border: string } {
  if (max <= 0) return { grade: "-", color: "#64748B", bg: "#F1F5F9", border: "#E2E8F0" };
  const pct = (marks / max) * 100;
  if (pct >= 91) return { grade: "A1", color: "#059669", bg: "#ECFDF5", border: "#A7F3D0" };
  if (pct >= 81) return { grade: "A2", color: "#16A34A", bg: "#ECFDF5", border: "#BBF7D0" };
  if (pct >= 71) return { grade: "B1", color: "#0D9488", bg: "#F0FDFA", border: "#99F6E4" };
  if (pct >= 61) return { grade: "B2", color: "#4338CA", bg: "#EEF2FF", border: "#C7D2FE" };
  if (pct >= 51) return { grade: "C1", color: "#D97706", bg: "#FFFBEB", border: "#FDE68A" };
  if (pct >= 41) return { grade: "C2", color: "#EA580C", bg: "#FFF7ED", border: "#FFEDD5" };
  if (pct >= 33) return { grade: "D", color: "#E11D48", bg: "#FFF1F2", border: "#FECDD3" };
  return { grade: "E", color: "#DC2626", bg: "#FFF1F2", border: "#FECDD3" };
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
      <View style={{ gap: 12, paddingBottom: 24 }}>
        {(papers.data ?? []).length === 0 ? (
          <Card>
            <Empty text="No exam papers scheduled for your subjects." />
          </Card>
        ) : (
          papers.data!.map((p) => {
            const isExpanded = open?.id === p.id;

            if (isExpanded) {
              return (
                <View key={p.id} style={styles.expandedContainer}>
                  {/* Class Section Header */}
                  <Pressable
                    onPress={() => setOpen(null)}
                    style={styles.expandedHeader}
                  >
                    <View style={{ flex: 1, paddingRight: 8 }}>
                      <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                        <View style={styles.activeDot} />
                        <Text style={styles.expandedTitle}>
                          {p.subject} - {p.class_label}
                        </Text>
                      </View>
                      <Text style={styles.expandedSubtitle}>
                        {p.exam_name} • {p.exam_date} • Max marks: {Number(p.max_marks)}
                      </Text>
                    </View>

                    <View style={p.marks_entered ? styles.badgeEntered : styles.badgePending}>
                      <Text style={p.marks_entered ? styles.badgeTextEntered : styles.badgeTextPending}>
                        {p.marks_entered ? "Entered" : "Pending"}
                      </Text>
                    </View>
                  </Pressable>

                  {/* Student Marks Entry Roster List */}
                  <View style={styles.rosterContainer}>
                    {(roster.data ?? []).map((r, index) => {
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
                          style={[
                            styles.studentRow,
                            index > 0 && { borderTopWidth: 1, borderTopColor: "#F1F5F9" },
                          ]}
                        >
                          {/* Student Info & CBSE Grade */}
                          <View style={styles.studentInfoRow}>
                            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                              <View style={styles.rollBadge}>
                                <Text style={styles.rollBadgeText}>{r.roll_no}</Text>
                              </View>
                              <Text style={styles.studentName}>{r.full_name}</Text>
                            </View>

                            {cbse && (
                              <View
                                style={[
                                  styles.cbseBadge,
                                  {
                                    backgroundColor: cbse.bg,
                                    borderColor: cbse.border,
                                  },
                                ]}
                              >
                                <Text style={[styles.cbseBadgeText, { color: cbse.color }]}>
                                  CBSE: {cbse.grade}
                                </Text>
                              </View>
                            )}
                          </View>

                          {/* Attendance Segmented Controls & Marks Input */}
                          <View style={styles.controlsRow}>
                            <View style={styles.segmentedContainer}>
                              {/* Present */}
                              <Pressable
                                onPress={() => {
                                  setAbsentMap({ ...absentMap, [id]: false });
                                  setExemptMap({ ...exemptMap, [id]: false });
                                }}
                                style={[
                                  styles.segmentBtn,
                                  !isAbs && !isEx && styles.segmentBtnActivePrimary,
                                ]}
                              >
                                <Text
                                  style={[
                                    styles.segmentBtnText,
                                    !isAbs && !isEx && styles.segmentBtnTextActive,
                                  ]}
                                >
                                  Present
                                </Text>
                              </Pressable>

                              {/* Absent */}
                              <Pressable
                                onPress={() => {
                                  setAbsentMap({ ...absentMap, [id]: true });
                                  setExemptMap({ ...exemptMap, [id]: false });
                                }}
                                style={[
                                  styles.segmentBtn,
                                  isAbs && styles.segmentBtnActiveDanger,
                                ]}
                              >
                                <Text
                                  style={[
                                    styles.segmentBtnText,
                                    isAbs && styles.segmentBtnTextActive,
                                  ]}
                                >
                                  Absent (A)
                                </Text>
                              </Pressable>

                              {/* Exempted */}
                              <Pressable
                                onPress={() => {
                                  setAbsentMap({ ...absentMap, [id]: false });
                                  setExemptMap({ ...exemptMap, [id]: true });
                                }}
                                style={[
                                  styles.segmentBtn,
                                  isEx && styles.segmentBtnActiveExempt,
                                ]}
                              >
                                <Text
                                  style={[
                                    styles.segmentBtnText,
                                    isEx && styles.segmentBtnTextActive,
                                  ]}
                                  numberOfLines={1}
                                >
                                  Exempted
                                </Text>
                              </Pressable>
                            </View>

                            {/* Marks Input / Status pill */}
                            <View style={styles.marksInputWrapper}>
                              {!isAbs && !isEx ? (
                                <TextInput
                                  style={[
                                    styles.marksInput,
                                    bad && styles.marksInputBad,
                                  ]}
                                  keyboardType="numeric"
                                  placeholder={`0-${max}`}
                                  placeholderTextColor="#94A3B8"
                                  value={raw}
                                  onChangeText={(v) => setValues({ ...values, [id]: v })}
                                />
                              ) : (
                                <View
                                  style={[
                                    styles.statusFixedBox,
                                    { backgroundColor: isAbs ? "#FFF1F2" : "#F5F3FF" },
                                  ]}
                                >
                                  <Text
                                    style={[
                                      styles.statusFixedText,
                                      { color: isAbs ? "#E11D48" : "#7C3AED" },
                                    ]}
                                  >
                                    {isAbs ? "ABSENT" : "EXEMPT"}
                                  </Text>
                                </View>
                              )}
                            </View>
                          </View>
                        </View>
                      );
                    })}
                  </View>

                  {/* Error & Feedback Banner */}
                  {invalid && (
                    <View style={styles.errorBox}>
                      <Ionicons name="alert-circle" size={16} color="#DC2626" />
                      <Text style={styles.errorBoxText}>
                        Each mark must be a valid number between 0 and {max}.
                      </Text>
                    </View>
                  )}

                  {note && (
                    <View style={styles.successBox}>
                      <Ionicons name="checkmark-circle" size={16} color="#059669" />
                      <Text style={styles.successBoxText}>{note}</Text>
                    </View>
                  )}

                  {/* Save Button */}
                  <View style={styles.saveContainer}>
                    <Pressable
                      onPress={() => save.mutate()}
                      disabled={save.isPending || invalid}
                      style={[
                        styles.saveBtn,
                        (save.isPending || invalid) && { opacity: 0.5 },
                      ]}
                    >
                      <Ionicons name="save-outline" size={18} color="#FFFFFF" />
                      <Text style={styles.saveBtnText}>
                        {save.isPending ? "Saving Marks..." : "Save Marks Sheet"}
                      </Text>
                    </Pressable>
                  </View>
                </View>
              );
            }

            // Normal Collapsed Item
            return (
              <Pressable
                key={p.id}
                onPress={() => setOpen(p)}
                style={styles.collapsedCard}
              >
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.collapsedTitle}>
                    {p.subject} - {p.class_label}
                  </Text>
                  <Text style={styles.collapsedSubtitle}>
                    {p.exam_name} • {p.exam_date} • Max marks: {Number(p.max_marks)}
                  </Text>
                </View>

                <View style={p.marks_entered ? styles.badgeEntered : styles.badgePending}>
                  <Text style={p.marks_entered ? styles.badgeTextEntered : styles.badgeTextPending}>
                    {p.marks_entered ? "Entered" : "Pending"}
                  </Text>
                </View>
              </Pressable>
            );
          })
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  // Collapsed Paper Card
  collapsedCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  collapsedTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
    lineHeight: 20,
  },
  collapsedSubtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 2,
    fontWeight: "500",
  },

  // Badges
  badgeEntered: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: "#ECFDF5",
    borderWidth: 1,
    borderColor: "#A7F3D0",
  },
  badgeTextEntered: {
    fontSize: 11,
    fontWeight: "700",
    color: "#059669",
  },
  badgePending: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: "#FFFBEB",
    borderWidth: 1,
    borderColor: "#FDE68A",
  },
  badgeTextPending: {
    fontSize: 11,
    fontWeight: "700",
    color: "#D97706",
  },

  // Expanded Section
  expandedContainer: {
    backgroundColor: "#FFFFFF",
    borderRadius: 22,
    borderWidth: 2,
    borderColor: "rgba(67, 56, 202, 0.25)",
    shadowColor: "#1E1B4B",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 4,
    overflow: "hidden",
  },
  expandedHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: 16,
    backgroundColor: "rgba(238, 242, 255, 0.6)",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(199, 210, 254, 0.6)",
  },
  activeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#4338CA",
  },
  expandedTitle: {
    fontSize: 17,
    fontWeight: "900",
    color: "#0F172A",
    letterSpacing: -0.2,
  },
  expandedSubtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 3,
    fontWeight: "500",
  },
  rosterContainer: {
    paddingHorizontal: 16,
  },
  studentRow: {
    paddingVertical: 14,
    gap: 10,
  },
  studentInfoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  rollBadge: {
    width: 24,
    height: 24,
    borderRadius: 8,
    backgroundColor: "#EEF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  rollBadgeText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#4338CA",
  },
  studentName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#0F172A",
  },
  cbseBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  cbseBadgeText: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.2,
  },

  // Attendance & Marks Controls
  controlsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  segmentedContainer: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: "#F1F5F9",
    borderRadius: 12,
    padding: 3,
    gap: 2,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 6,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
  },
  segmentBtnActivePrimary: {
    backgroundColor: "#4338CA",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 1,
  },
  segmentBtnActiveDanger: {
    backgroundColor: "#E11D48",
    shadowColor: "#E11D48",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 1,
  },
  segmentBtnActiveExempt: {
    backgroundColor: "#7C3AED",
    shadowColor: "#7C3AED",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 1,
  },
  segmentBtnText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#64748B",
  },
  segmentBtnTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  marksInputWrapper: {
    width: 76,
    alignItems: "center",
  },
  marksInput: {
    width: "100%",
    backgroundColor: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#CBD5E1",
    borderRadius: 10,
    paddingVertical: 6,
    paddingHorizontal: 8,
    fontSize: 14,
    fontWeight: "800",
    color: "#0F172A",
    textAlign: "center",
  },
  marksInputBad: {
    borderColor: "#E11D48",
    backgroundColor: "#FFF1F2",
  },
  statusFixedBox: {
    width: "100%",
    paddingVertical: 7,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  statusFixedText: {
    fontSize: 11,
    fontWeight: "800",
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#FFF1F2",
    padding: 10,
    marginHorizontal: 16,
    marginTop: 10,
    borderRadius: 10,
  },
  errorBoxText: {
    fontSize: 12,
    color: "#DC2626",
    fontWeight: "600",
    flex: 1,
  },
  successBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#ECFDF5",
    padding: 10,
    marginHorizontal: 16,
    marginTop: 10,
    borderRadius: 10,
  },
  successBoxText: {
    fontSize: 12,
    color: "#059669",
    fontWeight: "700",
    flex: 1,
  },
  saveContainer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
    marginTop: 8,
  },
  saveBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#4338CA",
    paddingVertical: 13,
    borderRadius: 14,
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  saveBtnText: {
    fontSize: 14,
    fontWeight: "800",
    color: "#FFFFFF",
  },
});
