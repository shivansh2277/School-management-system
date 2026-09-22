import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

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

function getGradeColor(grade: string | null): string {
  if (!grade) return theme.inkFaint;
  if (grade.startsWith("A")) return "#16A34A";
  if (grade.startsWith("B")) return "#2563EB";
  if (grade.startsWith("C")) return "#D97706";
  if (grade === "D") return "#EA580C";
  return "#DC2626";
}

function getPerformanceRemark(grade: string | null): string {
  if (!grade) return "";
  if (grade === "A1") return "Outstanding Achievement";
  if (grade === "A2") return "Excellent Performance";
  if (grade === "B1") return "Very Good";
  if (grade === "B2") return "Good Effort";
  if (grade === "C1") return "Above Average";
  if (grade === "C2") return "Average";
  if (grade === "D") return "Passing Grade";
  return "Needs Improvement";
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
      <Card title="My Examination Results">
        {(exams.data ?? []).length === 0 ? (
          <Empty text="No published results available yet." />
        ) : (
          exams.data!.map((e) => (
            <Pressable
              key={e.exam_id}
              onPress={() => setOpenExam(openExam === e.exam_id ? null : e.exam_id)}
              style={{ paddingVertical: 8 }}
            >
              <Row
                left={
                  <>
                    <Text style={s.title}>{e.name}</Text>
                    <Text style={s.meta}>{e.term}</Text>
                  </>
                }
                right={
                  <View style={{ alignItems: "flex-end", gap: 2 }}>
                    <Text style={{ fontWeight: "700", color: theme.ink, fontSize: 16 }}>
                      {e.overall_percent === null ? "-" : `${e.overall_percent}%`}
                    </Text>
                    <Text style={{ fontSize: 11, color: theme.primary }}>
                      {openExam === e.exam_id ? "Hide Details" : "View Breakdown ›"}
                    </Text>
                  </View>
                }
              />
            </Pressable>
          ))
        )}
      </Card>

      {openExam !== null && card.data && (
        <Card title={`${card.data.exam_name} Performance`}>
          {/* Overall Badge Header */}
          <View
            style={{
              backgroundColor: theme.ground,
              padding: 12,
              borderRadius: theme.radius.input,
              marginBottom: 12,
              alignItems: "center",
              gap: 4,
            }}
          >
            <Text style={{ fontSize: 12, color: theme.inkFaint }}>OVERALL RESULT</Text>
            <Text style={{ fontSize: 24, fontWeight: "800", color: theme.ink }}>
              {card.data.overall_percent !== null ? `${card.data.overall_percent}%` : "-"}
            </Text>
            {card.data.overall_grade && (
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Pill status="paid" label={`Grade: ${card.data.overall_grade}`} />
                <Text style={{ fontSize: 12, fontWeight: "600", color: getGradeColor(card.data.overall_grade) }}>
                  {getPerformanceRemark(card.data.overall_grade)}
                </Text>
              </View>
            )}
            <Text style={s.meta}>
              Total Score: {Number(card.data.total_obtained)} / {Number(card.data.total_max)}
            </Text>
          </View>

          {/* Subject Breakdown with Visual Progress Bars */}
          <Text style={[s.title, { marginBottom: 8 }]}>Subject Scores & Grade Points</Text>

          {card.data.rows.map((r) => {
            const pct = r.percent ?? 0;
            const barColor = getGradeColor(r.grade);

            return (
              <View
                key={r.subject}
                style={{
                  paddingVertical: 10,
                  borderBottomWidth: 1,
                  borderBottomColor: theme.rule,
                  gap: 6,
                }}
              >
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={[s.title, { fontSize: 14 }]}>{r.subject}</Text>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Text style={{ fontSize: 13, fontWeight: "700", color: theme.ink }}>
                      {r.marks_obtained !== null ? `${Number(r.marks_obtained)}/${Number(r.max_marks)}` : "Absent"}
                    </Text>
                    {r.grade && <Pill label={r.grade} />}
                  </View>
                </View>

                {/* Visual Progress Bar */}
                {r.marks_obtained !== null && (
                  <View style={{ gap: 2 }}>
                    <View
                      style={{
                        height: 7,
                        backgroundColor: theme.ground,
                        borderRadius: 999,
                        overflow: "hidden",
                      }}
                    >
                      <View
                        style={{
                          height: "100%",
                          width: `${Math.min(Math.max(pct, 0), 100)}%`,
                          backgroundColor: barColor,
                          borderRadius: 999,
                        }}
                      />
                    </View>
                    <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                      <Text style={{ fontSize: 10, color: theme.inkFaint }}>0%</Text>
                      <Text style={{ fontSize: 10, fontWeight: "600", color: barColor }}>{pct}%</Text>
                      <Text style={{ fontSize: 10, color: theme.inkFaint }}>100%</Text>
                    </View>
                  </View>
                )}
              </View>
            );
          })}
        </Card>
      )}
    </Screen>
  );
}
