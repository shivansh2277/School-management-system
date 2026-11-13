import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ExamHeader = {
  exam_id: number;
  name: string;
  term: string;
  overall_percent: number | null;
};

type ReportCard = {
  student_name: string;
  admission_no: string;
  class_label: string;
  roll_no: number;
  exam_name: string;
  term: string;
  rows: {
    subject: string;
    marks_obtained: number | null;
    max_marks: number;
    percent: number | null;
    grade: string | null;
  }[];
  total_obtained: number;
  total_max: number;
  overall_percent: number | null;
  overall_grade: string | null;
};

function getGradeBadgeStyle(grade: string | null) {
  if (!grade) return { bg: "#F1F5F9", text: "#64748B", border: "#E2E8F0" };
  if (grade.startsWith("A")) return { bg: "#ECFDF5", text: "#059669", border: "#A7F3D0" };
  if (grade.startsWith("B")) return { bg: "#EEF2FF", text: "#4338CA", border: "#C7D2FE" };
  if (grade.startsWith("C")) return { bg: "#FFFBEB", text: "#D97706", border: "#FDE68A" };
  if (grade === "D") return { bg: "#FFF7ED", text: "#EA580C", border: "#FFEDD5" };
  return { bg: "#FFF1F2", text: "#E11D48", border: "#FECDD3" };
}

export default function StudentResults() {
  const [openExam, setOpenExam] = useState<number | null>(null);

  const exams = useQuery({
    queryKey: ["student-results-list"],
    queryFn: () => api.get<ExamHeader[]>("/student/results"),
  });

  const card = useQuery({
    queryKey: ["student-report-card", openExam],
    queryFn: () => api.get<ReportCard>(`/student/results/${openExam}`),
    enabled: openExam !== null,
  });

  if (exams.isLoading) return <Loading />;

  return (
    <Screen>
      {/* Stitch Examinations List Card */}
      <View style={styles.examsCard}>
        <Text style={styles.examsCardTitle}>My Examination Results</Text>

        {(exams.data ?? []).length === 0 ? (
          <Empty text="No published results available yet." />
        ) : (
          <View>
            {exams.data!.map((e, index) => {
              const isOpen = openExam === e.exam_id;
              return (
                <Pressable
                  key={e.exam_id}
                  onPress={() => setOpenExam(isOpen ? null : e.exam_id)}
                  style={[
                    styles.examItem,
                    index > 0 && { borderTopWidth: 1, borderTopColor: "#F1F5F9" },
                  ]}
                >
                  <View style={{ flex: 1, paddingRight: 8 }}>
                    <Text style={styles.examName}>{e.name}</Text>
                    <View style={styles.examTermChip}>
                      <Text style={styles.examTermText}>{e.term}</Text>
                    </View>
                  </View>

                  <View style={{ alignItems: "flex-end", gap: 3 }}>
                    <Text style={styles.examPercent}>
                      {e.overall_percent === null ? "-" : `${e.overall_percent}%`}
                    </Text>
                    <Text style={styles.examActionText}>
                      {isOpen ? "Hide Details" : "View Breakdown ›"}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
        )}
      </View>

      {/* Stitch Scorecard Details */}
      {openExam !== null && card.data && (
        <View style={styles.scorecardCard}>
          {/* Overall Result Banner */}
          <View style={styles.overallBanner}>
            <Text style={styles.overallLabel}>OVERALL RESULT</Text>
            <Text style={styles.overallPercentText}>
              {card.data.overall_percent !== null ? `${card.data.overall_percent}%` : "-"}
            </Text>
            {card.data.overall_grade && (
              <View style={styles.gradeContainer}>
                <View style={styles.overallGradeBadge}>
                  <Text style={styles.overallGradeText}>Grade: {card.data.overall_grade}</Text>
                </View>
              </View>
            )}
            <Text style={styles.totalScoreSubtext}>
              Total Score: {Number(card.data.total_obtained)} / {Number(card.data.total_max)}
            </Text>
          </View>

          {/* Subject Rows */}
          <Text style={styles.subjectSectionHeading}>Subject Scores & Grade Points</Text>

          <View style={{ gap: 10 }}>
            {card.data.rows.map((r) => {
              const badgeStyle = getGradeBadgeStyle(r.grade);
              return (
                <View key={r.subject} style={styles.subjectRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.subjectName}>{r.subject}</Text>
                    <Text style={styles.subjectMarks}>
                      {r.marks_obtained === null
                        ? "Absent / Excluded"
                        : `${Number(r.marks_obtained)} / ${Number(r.max_marks)} marks`}
                    </Text>
                  </View>

                  {r.grade ? (
                    <View
                      style={[
                        styles.gradeBadge,
                        {
                          backgroundColor: badgeStyle.bg,
                          borderColor: badgeStyle.border,
                        },
                      ]}
                    >
                      <Text style={[styles.gradeBadgeText, { color: badgeStyle.text }]}>
                        {r.grade} {r.percent !== null ? `(${r.percent}%)` : ""}
                      </Text>
                    </View>
                  ) : (
                    <Text style={s.meta}>-</Text>
                  )}
                </View>
              );
            })}
          </View>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  examsCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 12,
  },
  examsCardTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0F172A",
    letterSpacing: -0.2,
    marginBottom: 12,
  },
  examItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
  },
  examName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#0F172A",
  },
  examTermChip: {
    alignSelf: "flex-start",
    backgroundColor: "#EEF2FF",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 4,
  },
  examTermText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#4338CA",
  },
  examPercent: {
    fontSize: 17,
    fontWeight: "800",
    color: "#0F172A",
  },
  examActionText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#4338CA",
  },
  scorecardCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 20,
  },
  overallBanner: {
    backgroundColor: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 16,
    padding: 16,
    alignItems: "center",
    gap: 4,
    marginBottom: 16,
  },
  overallLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#94A3B8",
    letterSpacing: 0.6,
  },
  overallPercentText: {
    fontSize: 26,
    fontWeight: "900",
    color: "#0F172A",
  },
  gradeContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 2,
  },
  overallGradeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 10,
    backgroundColor: "#ECFDF5",
    borderWidth: 1,
    borderColor: "#A7F3D0",
  },
  overallGradeText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#059669",
  },
  totalScoreSubtext: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 4,
  },
  subjectSectionHeading: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0F172A",
    marginBottom: 10,
    letterSpacing: -0.1,
  },
  subjectRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 6,
  },
  subjectName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1E293B",
  },
  subjectMarks: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  gradeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
    borderWidth: 1,
  },
  gradeBadgeText: {
    fontSize: 11,
    fontWeight: "800",
  },
});
