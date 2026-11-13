import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useState } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";

import { api, money, tokenStore } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
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

function getGradeBadgeStyle(grade: string | null) {
  if (!grade) return { bg: "#F1F5F9", text: "#64748B", border: "#E2E8F0" };
  if (grade.startsWith("A")) return { bg: "#ECFDF5", text: "#059669", border: "#A7F3D0" };
  if (grade.startsWith("B")) return { bg: "#EEF2FF", text: "#4338CA", border: "#C7D2FE" };
  if (grade.startsWith("C")) return { bg: "#FFFBEB", text: "#D97706", border: "#FDE68A" };
  if (grade === "D") return { bg: "#FFF7ED", text: "#EA580C", border: "#FFEDD5" };
  return { bg: "#FFF1F2", text: "#E11D48", border: "#FECDD3" };
}

export default function ParentResults() {
  const { t } = useTranslation();
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
      {/* Stitch Child Switcher Pills */}
      {children.length > 1 && (
        <View style={styles.childSwitcher}>
          {children.map((c) => {
            const active = selectedChildId === c.id;
            return (
              <Pressable
                key={c.id}
                onPress={() => {
                  selectChild(c.id);
                  setOpenExam(null);
                }}
                style={[styles.childPill, active && styles.childPillActive]}
              >
                {active && <View style={styles.childActiveDot} />}
                <Text style={[styles.childPillText, active && styles.childPillTextActive]}>
                  {c.name} {c.class_label ? `(${c.class_label})` : ""}
                </Text>
              </Pressable>
            );
          })}
        </View>
      )}

      {/* Stitch Fee Dues Withholding Warning Banner */}
      {isWithheld && (
        <View style={styles.alertBanner}>
          <View style={styles.alertIndicatorBar} />
          <View style={styles.alertContent}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Ionicons name="warning" size={16} color="#E11D48" />
              <Text style={styles.alertTitle}>
                Report Card Withheld — Fee Dues Pending:{" "}
                <Text style={styles.alertAmount}>{money(dues)}</Text>
              </Text>
            </View>
            <Text style={styles.alertDesc}>
              Official CBSE report cards are withheld pending settlement of outstanding dues. Please clear
              dues in the Fees tab to unlock downloads.
            </Text>
          </View>
        </View>
      )}

      {note ? (
        <View style={[styles.alertBanner, { backgroundColor: "#FFF1F2", borderColor: "#FECDD3" }]}>
          <Text style={{ color: "#E11D48", fontSize: 13, fontWeight: "600" }}>{note}</Text>
        </View>
      ) : null}

      {/* Stitch Completed Examinations Section */}
      <View style={styles.examsCard}>
        <Text style={styles.examsCardTitle}>{t("res_completed_exams")}</Text>

        {(exams.data ?? []).length === 0 ? (
          <Empty text={t("res_no_results")} />
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
                      {isOpen ? t("res_hide_details") : `${t("res_view_scorecard")} ›`}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
        )}
      </View>

      {/* Stitch Expanded Scorecard Section */}
      {openExam !== null && card.data && (
        <View style={styles.scorecardCard}>
          {/* Header & Metadata */}
          <View style={styles.scorecardHeader}>
            <Text style={styles.scorecardTitle}>
              {card.data.exam_name} — {t("res_scorecard")}
            </Text>
            <Text style={styles.scorecardMeta}>
              {t("res_roll")} #{card.data.roll_no} • {card.data.class_label} • {t("res_adm")}: {card.data.admission_no}
            </Text>
          </View>

          {/* Subject Rows */}
          <View style={{ gap: 10, paddingTop: 12 }}>
            {card.data.rows.map((r) => {
              const badgeStyle = getGradeBadgeStyle(r.grade);
              return (
                <View key={r.subject} style={styles.subjectRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.subjectName}>{r.subject}</Text>
                    <Text style={styles.subjectMarks}>
                      {r.marks_obtained === null
                        ? t("res_absent_excluded")
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

          {/* Total Score Summary Card */}
          <View style={styles.totalScoreBox}>
            <View>
              <Text style={styles.totalScoreLabel}>{t("res_total_score")}</Text>
              <Text style={styles.totalScoreValues}>
                {Number(card.data.total_obtained)} / {Number(card.data.total_max)}
              </Text>
            </View>

            {card.data.overall_percent !== null && (
              <View style={styles.overallResultPill}>
                <Text style={styles.overallResultText}>
                  {card.data.overall_percent}% • Grade {card.data.overall_grade ?? "-"}
                </Text>
              </View>
            )}
          </View>

          {/* 1-Click PDF Download / Fee Gate */}
          <View style={{ marginTop: 14 }}>
            {isWithheld ? (
              <View style={styles.lockedBtn}>
                <Ionicons name="lock-closed" size={16} color="#94A3B8" />
                <Text style={styles.lockedBtnText}>
                  Report Card Locked — Clear Dues ({money(dues)})
                </Text>
              </View>
            ) : (
              <Pressable
                onPress={() => downloadReportCard(openExam)}
                disabled={downloading}
                style={[styles.downloadBtn, downloading && { opacity: 0.6 }]}
              >
                <Ionicons name="cloud-download-outline" size={18} color="#FFFFFF" />
                <Text style={styles.downloadBtnText}>
                  {downloading ? t("res_preparing_pdf") : t("res_download_pdf")}
                </Text>
              </Pressable>
            )}
          </View>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  childSwitcher: {
    flexDirection: "row",
    gap: 8,
    flexWrap: "wrap",
    marginBottom: 8,
  },
  childPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#F1F5F9",
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  childPillActive: {
    backgroundColor: "#4338CA",
    borderColor: "#4338CA",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  childActiveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#34D399",
  },
  childPillText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#475569",
  },
  childPillTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },

  // Alert Banner
  alertBanner: {
    position: "relative",
    overflow: "hidden",
    borderRadius: 16,
    backgroundColor: "rgba(255, 241, 242, 0.8)",
    borderWidth: 1,
    borderColor: "#FECDD3",
    padding: 14,
    paddingLeft: 18,
    marginBottom: 12,
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  alertIndicatorBar: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    width: 5,
    backgroundColor: "#E11D48",
    borderTopLeftRadius: 16,
    borderBottomLeftRadius: 16,
  },
  alertContent: {
    gap: 4,
  },
  alertTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: "#BE123C",
    flex: 1,
  },
  alertAmount: {
    fontWeight: "800",
    color: "#9F1239",
  },
  alertDesc: {
    fontSize: 11,
    color: "#475569",
    lineHeight: 16,
  },

  // Examinations Section Card
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
    lineHeight: 19,
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

  // Scorecard Card
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
  scorecardHeader: {
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
    paddingBottom: 10,
  },
  scorecardTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: "#0F172A",
  },
  scorecardMeta: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 2,
    fontWeight: "500",
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
  totalScoreBox: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
    borderRadius: 14,
    padding: 12,
    marginTop: 14,
  },
  totalScoreLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#64748B",
    textTransform: "uppercase",
  },
  totalScoreValues: {
    fontSize: 16,
    fontWeight: "800",
    color: "#4338CA",
    marginTop: 1,
  },
  overallResultPill: {
    backgroundColor: "#4338CA",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
  },
  overallResultText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#FFFFFF",
  },
  downloadBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#4338CA",
    paddingVertical: 12,
    borderRadius: 14,
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  downloadBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  lockedBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#F1F5F9",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    paddingVertical: 12,
    borderRadius: 14,
  },
  lockedBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#94A3B8",
  },
});
