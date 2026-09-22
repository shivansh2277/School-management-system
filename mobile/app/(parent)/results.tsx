import { useQuery } from "@tanstack/react-query";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api, money, tokenStore } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
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

type FeeSummary = {
  total_dues: number;
  balance: number;
};

export default function ParentResults() {
  const { selectedChildId, me, selectChild } = useAuth();
  const children = me?.children ?? [];
  const [openExam, setOpenExam] = useState<number | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const exams = useQuery({
    queryKey: ["parent-results-list", selectedChildId],
    queryFn: () => api.get<ExamHeader[]>(`/parent/children/${selectedChildId}/results`),
    enabled: selectedChildId !== null,
  });

  const card = useQuery({
    queryKey: ["parent-report-card", selectedChildId, openExam],
    queryFn: () => api.get<ReportCard>(`/parent/children/${selectedChildId}/results/${openExam}`),
    enabled: selectedChildId !== null && openExam !== null,
  });

  const feeSummary = useQuery({
    queryKey: ["parent-fee-summary", selectedChildId],
    queryFn: () => api.get<FeeSummary>(`/parent/children/${selectedChildId}/fees/summary`),
    enabled: selectedChildId !== null,
  });

  const dues = feeSummary.data?.total_dues ?? 0;
  const isWithheld = dues > 0;

  const downloadReportCard = async (examId: number) => {
    if (isWithheld) {
      setNote(`Report card is withheld due to pending fee dues of ${money(dues)}.`);
      return;
    }
    setDownloading(true);
    setNote(null);
    const dir = FileSystem.cacheDirectory;
    if (!dir) {
      setNote("No local cache directory available.");
      setDownloading(false);
      return;
    }
    const target = `${dir}report-card-${selectedChildId}-${examId}.pdf`;
    try {
      const { uri } = await FileSystem.downloadAsync(
        `${api.base}/parent/children/${selectedChildId}/report-card/${examId}`,
        target,
        { headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` } },
      );
      setDownloading(false);
      await Sharing.shareAsync(uri, { mimeType: "application/pdf" });
    } catch {
      setDownloading(false);
      setNote("Could not download report card. Please verify permissions or fee status.");
    }
  };

  if (!selectedChildId || exams.isLoading) return <Loading />;

  return (
    <Screen>
      {/* Child Switcher */}
      {children.length > 1 && (
        <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          {children.map((c) => (
            <Pressable
              key={c.id}
              onPress={() => {
                selectChild(c.id);
                setOpenExam(null);
              }}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: theme.radius.pill,
                backgroundColor: selectedChildId === c.id ? theme.primary : theme.surface,
              }}
            >
              <Text style={{ color: selectedChildId === c.id ? "#fff" : theme.inkSoft, fontSize: 13 }}>
                {c.name}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* Fee Dues Withholding Warning Banner */}
      {isWithheld && (
        <View
          style={{
            backgroundColor: "#FEF2F2",
            borderLeftWidth: 4,
            borderLeftColor: theme.danger,
            padding: 12,
            borderRadius: theme.radius.input,
            marginBottom: 12,
          }}
        >
          <Text style={{ fontSize: 13, fontWeight: "700", color: theme.danger }}>
            ⚠️ Report Card Withheld — Fee Dues Pending: {money(dues)}
          </Text>
          <Text style={{ fontSize: 12, color: theme.ink, marginTop: 2 }}>
            Official CBSE report cards are withheld pending settlement of outstanding dues. Please clear dues in the Fees tab to unlock downloads.
          </Text>
        </View>
      )}

      {note ? (
        <Card>
          <Text style={{ color: theme.danger, fontSize: 13 }}>{note}</Text>
        </Card>
      ) : null}

      <Card title="Completed Examinations">
        {(exams.data ?? []).length === 0 ? (
          <Empty text="No results published yet." />
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
                    <Text style={{ fontWeight: "700", color: theme.ink, fontSize: 15 }}>
                      {e.overall_percent === null ? "-" : `${e.overall_percent}%`}
                    </Text>
                    <Text style={{ fontSize: 11, color: theme.primary }}>
                      {openExam === e.exam_id ? "Hide Details" : "View Scorecard ›"}
                    </Text>
                  </View>
                }
              />
            </Pressable>
          ))
        )}
      </Card>

      {openExam !== null && card.data && (
        <Card title={`${card.data.exam_name} — Scorecard`}>
          <View style={{ marginBottom: 8, paddingBottom: 6, borderBottomWidth: 1, borderBottomColor: theme.rule }}>
            <Text style={s.meta}>
              Roll {card.data.roll_no} • {card.data.class_label} • Adm: {card.data.admission_no}
            </Text>
          </View>

          {card.data.rows.map((r) => (
            <Row
              key={r.subject}
              left={
                <>
                  <Text style={s.title}>{r.subject}</Text>
                  <Text style={s.meta}>
                    {r.marks_obtained === null
                      ? "Absent (excluded from total)"
                      : `${Number(r.marks_obtained)} / ${Number(r.max_marks)} marks`}
                  </Text>
                </>
              }
              right={
                r.grade ? (
                  <Pill status="paid" label={`${r.grade} (${r.percent}%)`} />
                ) : (
                  <Text style={s.meta}>-</Text>
                )
              }
            />
          ))}

          <View style={{ marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: theme.rule }}>
            <Row
              left={<Text style={{ fontWeight: "700", fontSize: 15 }}>Total Score</Text>}
              right={
                <Text style={{ fontWeight: "700", fontSize: 15, color: theme.ink }}>
                  {Number(card.data.total_obtained)} / {Number(card.data.total_max)}
                  {card.data.overall_percent !== null
                    ? `  (${card.data.overall_percent}% — ${card.data.overall_grade})`
                    : ""}
                </Text>
              }
            />
          </View>

          {/* 1-Click PDF Download / Fee Gate */}
          <View style={{ marginTop: 14 }}>
            {isWithheld ? (
              <Button
                label={`🔒 Report Card Locked (Dues: ${money(dues)})`}
                tone="ghost"
                disabled
                onPress={() => {}}
              />
            ) : (
              <Button
                label={downloading ? "Preparing Official PDF..." : "📄 Download CBSE A4 Report Card PDF"}
                onPress={() => downloadReportCard(openExam)}
                disabled={downloading}
              />
            )}
          </View>
        </Card>
      )}
    </Screen>
  );
}
