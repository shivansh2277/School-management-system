import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type LeaveApplication = {
  id: number;
  from_date: string;
  to_date: string;
  days: number;
  is_half_day: boolean;
  reason: string;
  status: "applied" | "approved" | "rejected" | "cancelled";
  decision_note: string | null;
  decided_at: string | null;
  created_at: string;
};

type SubstitutionDuty = {
  id: number;
  date: string;
  period_no: number;
  time: string;
  class_label: string;
  subject: string;
  room: string | null;
  absent_teacher_name: string;
  status: string;
};

export default function TeacherLeave() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"apply" | "history" | "duties">("apply");

  // Format today's and tomorrow's date as YYYY-MM-DD
  const todayStr = new Date().toISOString().slice(0, 10);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().slice(0, 10);

  // Form State
  const [isRange, setIsRange] = useState(false);
  const [fromDate, setFromDate] = useState(tomorrowStr);
  const [toDate, setToDate] = useState(tomorrowStr);
  const [isHalfDay, setIsHalfDay] = useState(false);
  const [halfDayPeriod, setHalfDayPeriod] = useState<"morning" | "afternoon">("morning");
  const [reason, setReason] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Queries
  const historyQuery = useQuery({
    queryKey: ["teacher-leave-history"],
    queryFn: () => api.get<LeaveApplication[]>("/teacher/leave/history"),
  });

  const dutiesQuery = useQuery({
    queryKey: ["teacher-substitution-duties"],
    queryFn: () => api.get<SubstitutionDuty[]>("/teacher/substitutions/duties"),
  });

  // Apply Mutation
  const applyMutation = useMutation({
    mutationFn: () =>
      api.post("/teacher/leave/apply", {
        from_date: fromDate,
        to_date: isRange ? toDate : fromDate,
        reason: reason.trim(),
        is_half_day: isHalfDay,
        half_day_period: isHalfDay ? halfDayPeriod : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-leave-history"] });
      setReason("");
      setErrorMsg(null);
      if (Platform.OS === "web") {
        if (typeof window !== "undefined" && window.alert) {
          window.alert(
            "Your leave application has been submitted to school administration. You will be notified once reviewed."
          );
        }
        setActiveTab("history");
        return;
      }
      Alert.alert(
        "Application Submitted",
        "Your leave application has been submitted to school administration. You will be notified once reviewed.",
        [{ text: "View Leaves", onPress: () => setActiveTab("history") }]
      );
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Could not submit leave application.");
    },
  });

  const handleApplyPress = () => {
    setErrorMsg(null);
    if (!reason.trim() || reason.trim().length < 3) {
      setErrorMsg("Please enter a valid reason for leave (minimum 3 characters).");
      return;
    }
    if (isRange && toDate < fromDate) {
      setErrorMsg("End date cannot be earlier than start date.");
      return;
    }

    if (Platform.OS === "web") {
      const confirmed =
        typeof window !== "undefined" && window.confirm
          ? window.confirm(
              `Are you sure you want to apply for leave from ${fromDate}${isRange ? ` to ${toDate}` : ""}? \n\nApplications cannot be withdrawn once submitted.`
            )
          : true;
      if (confirmed) {
        applyMutation.mutate();
      }
      return;
    }

    Alert.alert(
      "Confirm Leave Application",
      `Are you sure you want to apply for leave from ${fromDate}${isRange ? ` to ${toDate}` : ""}? \n\nApplications cannot be withdrawn once submitted.`,
      [
        { text: "Cancel", style: "cancel" },
        { text: "Submit Application", onPress: () => applyMutation.mutate() },
      ]
    );
  };

  const history = historyQuery.data ?? [];
  const duties = dutiesQuery.data ?? [];
  const todayDuties = duties.filter((d) => d.date === todayStr);

  return (
    <Screen>
      {/* Top Segment Control */}
      <View style={styles.segmentContainer}>
        <Pressable
          onPress={() => setActiveTab("apply")}
          style={[styles.segmentBtn, activeTab === "apply" && styles.segmentBtnActive]}
        >
          <Text style={[styles.segmentText, activeTab === "apply" && styles.segmentTextActive]}>
            Apply Leave
          </Text>
        </Pressable>

        <Pressable
          onPress={() => setActiveTab("history")}
          style={[styles.segmentBtn, activeTab === "history" && styles.segmentBtnActive]}
        >
          <Text style={[styles.segmentText, activeTab === "history" && styles.segmentTextActive]}>
            My Leaves ({history.length})
          </Text>
        </Pressable>

        <Pressable
          onPress={() => setActiveTab("duties")}
          style={[styles.segmentBtn, activeTab === "duties" && styles.segmentBtnActive]}
        >
          <Text style={[styles.segmentText, activeTab === "duties" && styles.segmentTextActive]}>
            Duties ({duties.length})
          </Text>
        </Pressable>
      </View>

      {/* Tab 1: Apply Leave Form */}
      {activeTab === "apply" && (
        <>
          {/* Policy Information Box */}
          <Card>
            <View style={styles.policyNotice}>
              <Text style={styles.policyTitle}>Teacher Leave Policy Notice</Text>
              <Text style={styles.policyText}>
                • Teachers may only apply for leave for themselves.{"\n"}
                • Applications cannot be cancelled or withdrawn once submitted.{"\n"}
                • Timetable substitutions are arranged by admin before final approval.
              </Text>
            </View>
          </Card>

          {/* Form Fields Card */}
          <Card title="New Leave Application">
            {/* Range vs Single Day Toggle */}
            <Text style={styles.label}>Leave Duration Type</Text>
            <View style={styles.rowToggle}>
              <Pressable
                onPress={() => {
                  setIsRange(false);
                  setToDate(fromDate);
                }}
                style={[styles.toggleBtn, !isRange && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, !isRange && styles.toggleTextActive]}>
                  Single Day
                </Text>
              </Pressable>
              <Pressable
                onPress={() => setIsRange(true)}
                style={[styles.toggleBtn, isRange && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, isRange && styles.toggleTextActive]}>
                  Multiple Consecutive Days
                </Text>
              </Pressable>
            </View>

            {/* Date Inputs */}
            <View style={{ gap: 8, marginTop: 4 }}>
              <Text style={styles.label}>Start Date (YYYY-MM-DD)</Text>
              <TextInput
                style={s.input}
                value={fromDate}
                onChangeText={(val) => {
                  setFromDate(val);
                  if (!isRange) setToDate(val);
                }}
                placeholder="YYYY-MM-DD"
              />

              {isRange && (
                <>
                  <Text style={styles.label}>End Date (YYYY-MM-DD)</Text>
                  <TextInput
                    style={s.input}
                    value={toDate}
                    onChangeText={setToDate}
                    placeholder="YYYY-MM-DD"
                  />
                </>
              )}
            </View>

            {/* Half Day Option */}
            {!isRange && (
              <View style={{ marginTop: 6 }}>
                <Text style={styles.label}>Day Portion</Text>
                <View style={styles.rowToggle}>
                  <Pressable
                    onPress={() => setIsHalfDay(false)}
                    style={[styles.toggleBtn, !isHalfDay && styles.toggleBtnActive]}
                  >
                    <Text style={[styles.toggleText, !isHalfDay && styles.toggleTextActive]}>
                      Full Day
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setIsHalfDay(true)}
                    style={[styles.toggleBtn, isHalfDay && styles.toggleBtnActive]}
                  >
                    <Text style={[styles.toggleText, isHalfDay && styles.toggleTextActive]}>
                      Half Day
                    </Text>
                  </Pressable>
                </View>

                {isHalfDay && (
                  <View style={[styles.rowToggle, { marginTop: 8 }]}>
                    <Pressable
                      onPress={() => setHalfDayPeriod("morning")}
                      style={[styles.toggleBtn, halfDayPeriod === "morning" && styles.toggleBtnActive]}
                    >
                      <Text style={[styles.toggleText, halfDayPeriod === "morning" && styles.toggleTextActive]}>
                        Morning Session
                      </Text>
                    </Pressable>
                    <Pressable
                      onPress={() => setHalfDayPeriod("afternoon")}
                      style={[styles.toggleBtn, halfDayPeriod === "afternoon" && styles.toggleBtnActive]}
                    >
                      <Text style={[styles.toggleText, halfDayPeriod === "afternoon" && styles.toggleTextActive]}>
                        Afternoon Session
                      </Text>
                    </Pressable>
                  </View>
                )}
              </View>
            )}

            {/* Reason for Leave */}
            <View style={{ marginTop: 6 }}>
              <Text style={styles.label}>Reason for Leave *</Text>
              <TextInput
                style={[s.input, { height: 80, textAlignVertical: "top" }]}
                multiline
                numberOfLines={3}
                placeholder="State your personal reason for leave (medical, urgent work, etc.)..."
                value={reason}
                onChangeText={setReason}
              />
            </View>

            {/* Error message */}
            {errorMsg && (
              <Text style={{ color: theme.danger, fontSize: 12, marginTop: 4 }}>
                {errorMsg}
              </Text>
            )}

            {/* Submit Button */}
            <View style={{ marginTop: 8 }}>
              <Button
                label={applyMutation.isPending ? "Submitting..." : "Apply for Leave"}
                disabled={applyMutation.isPending}
                onPress={handleApplyPress}
              />
            </View>
          </Card>
        </>
      )}

      {/* Tab 2: My Leave History */}
      {activeTab === "history" && (
        <Card title="Submitted Applications">
          {historyQuery.isLoading ? (
            <Loading />
          ) : history.length === 0 ? (
            <Empty text="You have not submitted any leave applications yet." />
          ) : (
            history.map((app) => {
              const statusPill: Record<LeaveApplication["status"], { label: string; tone: string }> = {
                applied: { label: "Pending Review", tone: "pending" },
                approved: { label: "Approved", tone: "paid" },
                rejected: { label: "Rejected", tone: "overdue" },
                cancelled: { label: "Cancelled", tone: "overdue" },
              };
              const sp = statusPill[app.status] ?? { label: app.status, tone: "pending" };

              return (
                <View key={app.id} style={styles.historyCard}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                    <Text style={{ fontSize: 15, fontWeight: "700", color: theme.ink }}>
                      {formatDate(app.from_date)} {app.from_date !== app.to_date ? `to ${formatDate(app.to_date)}` : ""}
                    </Text>
                    <Pill status={sp.tone} label={sp.label} />
                  </View>

                  <Text style={{ fontSize: 12, color: theme.inkFaint, marginTop: 2 }}>
                    Duration: {app.days} day{app.days === 1 ? "" : "s"} {app.is_half_day ? "(Half Day)" : ""}
                  </Text>

                  <Text style={{ fontSize: 13, color: theme.ink, marginTop: 6, lineHeight: 18 }}>
                    <Text style={{ fontWeight: "600" }}>Reason: </Text>
                    {app.reason}
                  </Text>

                  {app.decision_note && (
                    <View style={styles.decisionBox}>
                      <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft }}>
                        Admin Remarks:
                      </Text>
                      <Text style={{ fontSize: 12, color: theme.ink, marginTop: 2 }}>
                        {app.decision_note}
                      </Text>
                    </View>
                  )}
                </View>
              );
            })
          )}
        </Card>
      )}

      {/* Tab 3: Substitution Duties */}
      {activeTab === "duties" && (
        <>
          {/* Today's duties alert banner */}
          {todayDuties.length > 0 && (
            <View style={styles.todayAlert}>
              <Text style={styles.todayAlertTitle}>
                Today's Substitution Duties ({todayDuties.length})
              </Text>
              <Text style={styles.todayAlertText}>
                You have active substitution classes scheduled for today. Please check periods below.
              </Text>
            </View>
          )}

          <Card title="Assigned Substitution Duties">
            {dutiesQuery.isLoading ? (
              <Loading />
            ) : duties.length === 0 ? (
              <Empty text="No substitution duties assigned to you." />
            ) : (
              duties.map((duty) => (
                <View key={duty.id} style={styles.dutyCard}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                    <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                      <Text style={{ fontSize: 14, fontWeight: "700", color: theme.ink }}>
                        Period {duty.period_no} ({duty.time})
                      </Text>
                      {duty.date === todayStr && (
                        <Pill status="pending" label="Today" />
                      )}
                    </View>
                    <Text style={{ fontSize: 12, fontWeight: "600", color: theme.primary }}>
                      {formatDate(duty.date)}
                    </Text>
                  </View>

                  <View style={{ marginTop: 6, gap: 2 }}>
                    <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
                      Class: {duty.class_label} • Subject: {duty.subject}
                    </Text>
                    {duty.room ? (
                      <Text style={{ fontSize: 12, color: theme.inkFaint }}>Room: {duty.room}</Text>
                    ) : null}
                    <Text style={{ fontSize: 12, color: theme.primary, fontWeight: "500" }}>
                      Covering for: {duty.absent_teacher_name}
                    </Text>
                  </View>
                </View>
              ))
            )}
          </Card>
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  segmentContainer: {
    flexDirection: "row",
    backgroundColor: theme.surface,
    borderRadius: theme.radius.input,
    padding: 4,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: theme.radius.input - 2,
  },
  segmentBtnActive: {
    backgroundColor: theme.primary,
  },
  segmentText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
  },
  segmentTextActive: {
    color: "#fff",
  },
  policyNotice: {
    backgroundColor: `${theme.primary}10`,
    borderLeftWidth: 4,
    borderLeftColor: theme.primary,
    padding: 10,
    borderRadius: 4,
  },
  policyTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: theme.primary,
    marginBottom: 4,
  },
  policyText: {
    fontSize: 11,
    color: theme.inkSoft,
    lineHeight: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
    marginBottom: 4,
  },
  rowToggle: {
    flexDirection: "row",
    gap: 8,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: theme.radius.input,
    borderWidth: 1,
    borderColor: theme.rule,
    backgroundColor: theme.surface,
  },
  toggleBtnActive: {
    backgroundColor: `${theme.primary}15`,
    borderColor: theme.primary,
  },
  toggleText: {
    fontSize: 12,
    fontWeight: "500",
    color: theme.inkSoft,
  },
  toggleTextActive: {
    fontWeight: "700",
    color: theme.primary,
  },
  historyCard: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  decisionBox: {
    marginTop: 6,
    backgroundColor: `${theme.inkFaint}15`,
    padding: 8,
    borderRadius: 4,
  },
  todayAlert: {
    backgroundColor: `${theme.primary}15`,
    borderWidth: 1,
    borderColor: `${theme.primary}40`,
    padding: 12,
    borderRadius: theme.radius.card,
  },
  todayAlertTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: theme.primary,
  },
  todayAlertText: {
    fontSize: 12,
    color: theme.inkSoft,
    marginTop: 2,
  },
  dutyCard: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
});
