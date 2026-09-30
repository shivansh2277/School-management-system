import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  Alert,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type LeaveType = {
  id: number;
  code: string;
  name: string;
  annual_quota: number;
  is_paid: boolean;
  is_casual: boolean;
};

type RankedSubstitute = {
  teacher_id: number;
  teacher_name: string;
  employee_code: string;
  rank: number;
  rank_label: string;
  reason: string;
};

type InspectedPeriod = {
  date: string;
  slot_id: number;
  period_id: number;
  period_no: number;
  start_time: string;
  end_time: string;
  time: string;
  class_section_id: number;
  class_label: string;
  subject_id: number;
  subject_name: string;
  room: string | null;
  ranked_substitutes: RankedSubstitute[];
};

type LeaveApplication = {
  id: number;
  from_date: string;
  to_date: string;
  days: number;
  is_half_day: boolean;
  reason: string;
  status: "applied" | "approved" | "rejected" | "cancelled";
  leave_type: string | null;
  leave_type_name: string;
  decision_note: string | null;
  decided_at: string | null;
  created_at: string;
};

type SubstitutionRequest = {
  id: number;
  date: string;
  is_today: boolean;
  slot_id: number;
  period_no: number;
  start_time: string;
  end_time: string;
  time: string;
  class_section_id: number;
  class_label: string;
  subject_name: string;
  room: string | null;
  absent_teacher_id: number;
  absent_teacher_name: string;
  leave_request_id: number | null;
  reason: string;
  status: string;
};

type SubstitutionDuty = {
  id: number;
  date: string;
  period_no: number;
  time: string;
  class_label: string;
  subject_name: string;
  room: string | null;
  absent_teacher_name: string;
  status: string;
};

type ApplicationPeriod = {
  date: string;
  slot_id: number;
  period_id: number;
  period_no: number;
  time: string;
  class_section_id: number;
  class_label: string;
  subject_id: number;
  subject_name: string;
  room: string | null;
  substitution_id: number | null;
  substitute_teacher_id: number | null;
  substitute_teacher_name: string | null;
  status: "pending" | "assigned" | "rejected" | "unassigned";
  can_reassign: boolean;
  ranked_substitutes: RankedSubstitute[];
};

type ApplicationSubstitutionsResponse = {
  leave_request_id: number;
  status: string;
  leave_type_name: string;
  from_date: string;
  to_date: string;
  days: number;
  is_fully_accepted: boolean;
  total_periods: number;
  periods: ApplicationPeriod[];
};

function getRankBadgeStyle(rank: number) {
  switch (rank) {
    case 1:
      return { bg: "#DCFCE7", text: "#166534" }; // emerald / green
    case 2:
      return { bg: "#DBEAFE", text: "#1E40AF" }; // blue
    case 3:
      return { bg: "#FEF3C7", text: "#92400E" }; // amber
    default:
      return { bg: "#F1F5F9", text: "#475569" }; // slate
  }
}

export default function TeacherLeave() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"apply" | "requests" | "history" | "duties">("apply");

  const todayStr = new Date().toISOString().slice(0, 10);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().slice(0, 10);

  // Form State
  const [selectedTypeId, setSelectedTypeId] = useState<number | null>(null);
  const [isRange, setIsRange] = useState(false);
  const [fromDate, setFromDate] = useState(tomorrowStr);
  const [toDate, setToDate] = useState(tomorrowStr);
  const [isHalfDay, setIsHalfDay] = useState(false);
  const [halfDayPeriod, setHalfDayPeriod] = useState<"morning" | "afternoon">("morning");
  const [reason, setReason] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Casual Leave Inspection State
  const [inspectedPeriods, setInspectedPeriods] = useState<InspectedPeriod[] | null>(null);
  const [selectedSubs, setSelectedSubs] = useState<Record<string, RankedSubstitute>>({});
  const [expandedPeriodKey, setExpandedPeriodKey] = useState<string | null>(null);

  // Reassignment Modal State
  const [reassignModal, setReassignModal] = useState<{
    appId: number;
    period: ApplicationPeriod;
  } | null>(null);

  // Active expanded leave item in history
  const [expandedAppId, setExpandedAppId] = useState<number | null>(null);

  // Queries
  const leaveTypesQuery = useQuery({
    queryKey: ["teacher-leave-types"],
    queryFn: () => api.get<LeaveType[]>("/teacher/leave/types"),
  });

  const historyQuery = useQuery({
    queryKey: ["teacher-leave-history"],
    queryFn: () => api.get<LeaveApplication[]>("/teacher/leave/history"),
  });

  const requestsQuery = useQuery({
    queryKey: ["teacher-substitution-requests"],
    queryFn: () => api.get<SubstitutionRequest[]>("/teacher/substitutions/requests"),
  });

  const dutiesQuery = useQuery({
    queryKey: ["teacher-substitution-duties"],
    queryFn: () => api.get<SubstitutionDuty[]>("/teacher/substitutions/duties"),
  });

  const leaveTypes = leaveTypesQuery.data ?? [];
  const selectedType = leaveTypes.find((t) => t.id === selectedTypeId) ?? leaveTypes[0];

  useEffect(() => {
    if (!selectedTypeId && leaveTypes.length > 0) {
      const casual = leaveTypes.find((t) => t.is_casual);
      setSelectedTypeId(casual ? casual.id : leaveTypes[0].id);
    }
  }, [leaveTypes, selectedTypeId]);

  // Reset inspected periods whenever dates or duration changes
  const resetInspection = () => {
    setInspectedPeriods(null);
    setSelectedSubs({});
    setExpandedPeriodKey(null);
  };

  // Inspect Periods Mutation
  const inspectMutation = useMutation({
    mutationFn: () =>
      api.post<{ periods: InspectedPeriod[]; total_periods: number }>("/teacher/leave/inspect", {
        from_date: fromDate,
        to_date: isRange ? toDate : fromDate,
        is_half_day: isHalfDay,
        half_day_period: isHalfDay ? halfDayPeriod : null,
      }),
    onSuccess: (data) => {
      setInspectedPeriods(data.periods);
      setErrorMsg(null);
      // Auto-assign top ranked substitute if unique and available
      const autoAssigned: Record<string, RankedSubstitute> = {};
      data.periods.forEach((p) => {
        if (p.ranked_substitutes.length > 0) {
          autoAssigned[`${p.date}_${p.slot_id}`] = p.ranked_substitutes[0];
        }
      });
      setSelectedSubs(autoAssigned);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Failed to inspect periods for selected dates.");
    },
  });

  // Apply Leave Mutation
  const applyMutation = useMutation({
    mutationFn: () => {
      const isCasual = selectedType?.is_casual ?? false;
      const substitutions = isCasual && inspectedPeriods
        ? inspectedPeriods.map((p) => {
            const key = `${p.date}_${p.slot_id}`;
            const sub = selectedSubs[key];
            return {
              slot_id: p.slot_id,
              date: p.date,
              substitute_teacher_id: sub ? sub.teacher_id : 0,
            };
          })
        : [];

      return api.post("/teacher/leave/apply", {
        leave_type_id: selectedType?.id ?? null,
        from_date: fromDate,
        to_date: isRange ? toDate : fromDate,
        reason: reason.trim(),
        is_half_day: isHalfDay,
        half_day_period: isHalfDay ? halfDayPeriod : null,
        substitutions,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-leave-history"] });
      setReason("");
      resetInspection();
      setErrorMsg(null);
      const msg = selectedType?.is_casual
        ? "Your Casual Leave application has been submitted and substitution requests have been sent to your selected colleagues."
        : "Your leave application has been submitted to school administration.";

      if (Platform.OS === "web") {
        if (typeof window !== "undefined" && window.alert) {
          window.alert(msg);
        }
        setActiveTab("history");
        return;
      }
      Alert.alert("Application Submitted", msg, [
        { text: "View Leaves", onPress: () => setActiveTab("history") },
      ]);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || "Could not submit leave application.");
    },
  });

  // Respond to substitution request (Accept / Decline)
  const respondMutation = useMutation({
    mutationFn: ({ id, action, rejReason }: { id: number; action: "accept" | "reject"; rejReason?: string }) =>
      api.post(`/teacher/substitutions/${id}/respond`, {
        action,
        reason: rejReason || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-substitution-requests"] });
      queryClient.invalidateQueries({ queryKey: ["teacher-substitution-duties"] });
    },
    onError: (err: any) => {
      Alert.alert("Action Failed", err.message || "Could not update substitution status.");
    },
  });

  // Reassign Substitute Mutation
  const reassignMutation = useMutation({
    mutationFn: ({ appId, slotId, date, newTeacherId }: { appId: number; slotId: number; date: string; newTeacherId: number }) =>
      api.post(`/teacher/leave/applications/${appId}/reassign`, {
        slot_id: slotId,
        date,
        new_substitute_teacher_id: newTeacherId,
      }),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["teacher-application-substitutions", vars.appId] });
      setReassignModal(null);
      if (Platform.OS === "web" && typeof window !== "undefined" && window.alert) {
        window.alert("Substitution request sent to new teacher.");
      } else {
        Alert.alert("Reassigned", "Substitution request sent to new teacher.");
      }
    },
    onError: (err: any) => {
      Alert.alert("Reassign Failed", err.message || "Could not reassign substitute.");
    },
  });

  // Validation & Handlers
  const isCasual = selectedType?.is_casual ?? false;
  const allCasualPeriodsCovered =
    !isCasual ||
    (inspectedPeriods !== null &&
      inspectedPeriods.every((p) => !!selectedSubs[`${p.date}_${p.slot_id}`]));

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
    if (isCasual && inspectedPeriods === null) {
      setErrorMsg("Please inspect affected periods and assign substitutes before applying.");
      return;
    }
    if (isCasual && !allCasualPeriodsCovered) {
      setErrorMsg("Please assign a substitute teacher for every affected period.");
      return;
    }

    const confirmText = `Are you sure you want to apply for ${selectedType?.name || "leave"} from ${fromDate}${isRange ? ` to ${toDate}` : ""}?`;

    if (Platform.OS === "web") {
      const confirmed =
        typeof window !== "undefined" && window.confirm ? window.confirm(confirmText) : true;
      if (confirmed) applyMutation.mutate();
      return;
    }

    Alert.alert("Confirm Leave Application", confirmText, [
      { text: "Cancel", style: "cancel" },
      { text: "Submit Application", onPress: () => applyMutation.mutate() },
    ]);
  };

  const handleRespond = (req: SubstitutionRequest, action: "accept" | "reject") => {
    if (action === "accept") {
      respondMutation.mutate({ id: req.id, action: "accept" });
      return;
    }

    if (Platform.OS === "web") {
      const rejReason = typeof window !== "undefined" ? window.prompt("Optional reason for declining:") : null;
      respondMutation.mutate({ id: req.id, action: "reject", rejReason: rejReason || undefined });
      return;
    }

    Alert.prompt
      ? Alert.prompt(
          "Decline Request",
          "Please enter reason for declining this substitution duty (optional):",
          [
            { text: "Cancel", style: "cancel" },
            {
              text: "Decline",
              style: "destructive",
              onPress: (val?: string) =>
                respondMutation.mutate({ id: req.id, action: "reject", rejReason: val }),
            },
          ]
        )
      : Alert.alert("Decline Request", "Are you sure you want to decline this request?", [
          { text: "Cancel", style: "cancel" },
          {
            text: "Decline",
            style: "destructive",
            onPress: () => respondMutation.mutate({ id: req.id, action: "reject" }),
          },
        ]);
  };

  const history = historyQuery.data ?? [];
  const requests = requestsQuery.data ?? [];
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
            Apply
          </Text>
        </Pressable>

        <Pressable
          onPress={() => setActiveTab("requests")}
          style={[styles.segmentBtn, activeTab === "requests" && styles.segmentBtnActive]}
        >
          <Text style={[styles.segmentText, activeTab === "requests" && styles.segmentTextActive]}>
            Requests {requests.length > 0 ? `(${requests.length})` : ""}
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
              <Text style={styles.policyTitle}>Teacher Leave & Substitution Policy</Text>
              <Text style={styles.policyText}>
                {isCasual
                  ? "• Casual Leave (CL) requires arranging substitutes for 100% of affected periods before administration approval.\n• Select ranked substitutes recommended based on subject and grade suitability."
                  : "• Non-casual leave (Sick Leave, Medical, etc.) is submitted directly. Administration arranges substitutions as needed."}
              </Text>
            </View>
          </Card>

          {/* Form Fields Card */}
          <Card title="New Leave Application">
            {/* Leave Type Selector */}
            <Text style={styles.label}>Select Leave Type</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingVertical: 4 }}>
              {leaveTypes.map((t) => {
                const isSelected = t.id === selectedType?.id;
                return (
                  <Pressable
                    key={t.id}
                    onPress={() => {
                      setSelectedTypeId(t.id);
                      resetInspection();
                    }}
                    style={[
                      styles.typeChip,
                      isSelected && styles.typeChipActive,
                    ]}
                  >
                    <Text style={[styles.typeChipCode, isSelected && styles.typeChipCodeActive]}>
                      {t.code}
                    </Text>
                    <Text style={[styles.typeChipName, isSelected && styles.typeChipNameActive]}>
                      {t.name}
                    </Text>
                    <Text style={[styles.typeChipQuota, isSelected && styles.typeChipQuotaActive]}>
                      {t.annual_quota}d quota • {t.is_paid ? "Paid" : "Unpaid"}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            {/* Range vs Single Day Toggle */}
            <Text style={[styles.label, { marginTop: 10 }]}>Leave Duration</Text>
            <View style={styles.rowToggle}>
              <Pressable
                onPress={() => {
                  setIsRange(false);
                  setToDate(fromDate);
                  resetInspection();
                }}
                style={[styles.toggleBtn, !isRange && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, !isRange && styles.toggleTextActive]}>
                  Single Day
                </Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  setIsRange(true);
                  resetInspection();
                }}
                style={[styles.toggleBtn, isRange && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, isRange && styles.toggleTextActive]}>
                  Multiple Days
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
                  resetInspection();
                }}
                placeholder="YYYY-MM-DD"
              />

              {isRange && (
                <>
                  <Text style={styles.label}>End Date (YYYY-MM-DD)</Text>
                  <TextInput
                    style={s.input}
                    value={toDate}
                    onChangeText={(val) => {
                      setToDate(val);
                      resetInspection();
                    }}
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
                    onPress={() => {
                      setIsHalfDay(false);
                      resetInspection();
                    }}
                    style={[styles.toggleBtn, !isHalfDay && styles.toggleBtnActive]}
                  >
                    <Text style={[styles.toggleText, !isHalfDay && styles.toggleTextActive]}>
                      Full Day
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => {
                      setIsHalfDay(true);
                      resetInspection();
                    }}
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
                      onPress={() => {
                        setHalfDayPeriod("morning");
                        resetInspection();
                      }}
                      style={[styles.toggleBtn, halfDayPeriod === "morning" && styles.toggleBtnActive]}
                    >
                      <Text style={[styles.toggleText, halfDayPeriod === "morning" && styles.toggleTextActive]}>
                        Morning Session
                      </Text>
                    </Pressable>
                    <Pressable
                      onPress={() => {
                        setHalfDayPeriod("afternoon");
                        resetInspection();
                      }}
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
                style={[s.input, { height: 70, textAlignVertical: "top" }]}
                multiline
                numberOfLines={3}
                placeholder="State reason for leave..."
                value={reason}
                onChangeText={setReason}
              />
            </View>

            {/* Casual Leave Substitutions Step */}
            {isCasual && (
              <View style={{ marginTop: 12 }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={[styles.label, { fontSize: 13 }]}>Timetable Substitutions</Text>
                  {inspectedPeriods !== null && (
                    <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                      {inspectedPeriods.length} period(s) affected
                    </Text>
                  )}
                </View>

                {inspectedPeriods === null ? (
                  <Button
                    label={inspectMutation.isPending ? "Inspecting Timetable..." : "Check Affected Periods & Substitutes"}
                    disabled={inspectMutation.isPending}
                    tone="ghost"
                    onPress={() => inspectMutation.mutate()}
                  />
                ) : inspectedPeriods.length === 0 ? (
                  <View style={styles.emptyNoticeBox}>
                    <Text style={styles.emptyNoticeText}>
                      ✓ No teaching periods scheduled on these dates. You can submit directly.
                    </Text>
                  </View>
                ) : (
                  <View style={{ gap: 10, marginTop: 6 }}>
                    {inspectedPeriods.map((p) => {
                      const pKey = `${p.date}_${p.slot_id}`;
                      const chosenSub = selectedSubs[pKey];
                      const isExpanded = expandedPeriodKey === pKey;

                      return (
                        <View key={pKey} style={styles.periodCoverCard}>
                          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                            <Text style={{ fontSize: 13, fontWeight: "700", color: theme.ink }}>
                              {p.date} • Period {p.period_no} ({p.time})
                            </Text>
                            {chosenSub ? (
                              <Pill status="paid" label="Cover Assigned" />
                            ) : (
                              <Pill status="overdue" label="Cover Needed" />
                            )}
                          </View>

                          <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 2 }}>
                            Class {p.class_label} • {p.subject_name} {p.room ? `(${p.room})` : ""}
                          </Text>

                          {chosenSub ? (
                            <View style={styles.assignedSubBox}>
                              <View style={{ flex: 1 }}>
                                <Text style={{ fontSize: 12, fontWeight: "600", color: theme.ink }}>
                                  Substitute: {chosenSub.teacher_name} ({chosenSub.employee_code})
                                </Text>
                                <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                                  {chosenSub.rank_label} • {chosenSub.reason}
                                </Text>
                              </View>
                              <Pressable
                                onPress={() => setExpandedPeriodKey(isExpanded ? null : pKey)}
                                style={styles.changeSubBtn}
                              >
                                <Text style={styles.changeSubBtnText}>
                                  {isExpanded ? "Close" : "Change"}
                                </Text>
                              </Pressable>
                            </View>
                          ) : (
                            <Pressable
                              onPress={() => setExpandedPeriodKey(isExpanded ? null : pKey)}
                              style={styles.selectSubBtn}
                            >
                              <Text style={styles.selectSubBtnText}>
                                {isExpanded ? "Close Candidates" : "Select Ranked Substitute ▾"}
                              </Text>
                            </Pressable>
                          )}

                          {/* Expanded Substitute Suggestions List */}
                          {isExpanded && (
                            <View style={styles.candidatesContainer}>
                              <Text style={styles.candidatesHeading}>
                                Available Substitutes (Ranked):
                              </Text>
                              {p.ranked_substitutes.length === 0 ? (
                                <Text style={{ fontSize: 12, color: theme.inkFaint }}>
                                  No available teachers found for this period.
                                </Text>
                              ) : (
                                p.ranked_substitutes.map((cand) => {
                                  const isCandidateSelected = chosenSub?.teacher_id === cand.teacher_id;
                                  const badge = getRankBadgeStyle(cand.rank);

                                  return (
                                    <Pressable
                                      key={cand.teacher_id}
                                      onPress={() => {
                                        setSelectedSubs((prev) => ({ ...prev, [pKey]: cand }));
                                        setExpandedPeriodKey(null);
                                      }}
                                      style={[
                                        styles.candidateItem,
                                        isCandidateSelected && styles.candidateItemSelected,
                                      ]}
                                    >
                                      <View style={{ flex: 1 }}>
                                        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                                          <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
                                            {cand.teacher_name}
                                          </Text>
                                          <View style={[styles.rankBadge, { backgroundColor: badge.bg }]}>
                                            <Text style={[styles.rankBadgeText, { color: badge.text }]}>
                                              {cand.rank_label}
                                            </Text>
                                          </View>
                                        </View>
                                        <Text style={{ fontSize: 11, color: theme.inkFaint, marginTop: 1 }}>
                                          {cand.reason}
                                        </Text>
                                      </View>
                                      {isCandidateSelected && (
                                        <Text style={{ fontSize: 16, color: theme.primary }}>✓</Text>
                                      )}
                                    </Pressable>
                                  );
                                })
                              )}
                            </View>
                          )}
                        </View>
                      );
                    })}
                  </View>
                )}
              </View>
            )}

            {/* Error message */}
            {errorMsg && (
              <Text style={{ color: theme.danger, fontSize: 12, marginTop: 6 }}>
                {errorMsg}
              </Text>
            )}

            {/* Submit Button */}
            <View style={{ marginTop: 12 }}>
              <Button
                label={applyMutation.isPending ? "Submitting Application..." : "Submit Leave Application"}
                disabled={applyMutation.isPending}
                onPress={handleApplyPress}
              />
            </View>
          </Card>
        </>
      )}

      {/* Tab 2: Substitution Requests Awaiting Response */}
      {activeTab === "requests" && (
        <Card title={`Pending Substitution Requests (${requests.length})`}>
          {requestsQuery.isLoading ? (
            <Loading />
          ) : requests.length === 0 ? (
            <Empty text="You have no pending substitution requests." />
          ) : (
            requests.map((req) => (
              <View key={req.id} style={styles.requestCard}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={{ fontSize: 14, fontWeight: "700", color: theme.ink }}>
                    {formatDate(req.date)} • Period {req.period_no} ({req.time})
                  </Text>
                  {req.is_today && <Pill status="pending" label="Today" />}
                </View>

                <Text style={{ fontSize: 13, fontWeight: "600", color: theme.inkSoft, marginTop: 4 }}>
                  Class {req.class_label} • {req.subject_name} {req.room ? `(Room: ${req.room})` : ""}
                </Text>

                <Text style={{ fontSize: 12, color: theme.ink, marginTop: 4 }}>
                  <Text style={{ fontWeight: "600" }}>Covering for: </Text>
                  {req.absent_teacher_name}
                </Text>

                {req.reason ? (
                  <Text style={{ fontSize: 12, color: theme.inkFaint, marginTop: 2, fontStyle: "italic" }}>
                    "{req.reason}"
                  </Text>
                ) : null}

                <View style={styles.requestActions}>
                  <Pressable
                    onPress={() => handleRespond(req, "accept")}
                    disabled={respondMutation.isPending}
                    style={styles.acceptBtn}
                  >
                    <Text style={styles.acceptBtnText}>Accept Duty</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => handleRespond(req, "reject")}
                    disabled={respondMutation.isPending}
                    style={styles.declineBtn}
                  >
                    <Text style={styles.declineBtnText}>Decline</Text>
                  </Pressable>
                </View>
              </View>
            ))
          )}
        </Card>
      )}

      {/* Tab 3: My Leaves History */}
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
              const isDetailsOpen = expandedAppId === app.id;

              return (
                <View key={app.id} style={styles.historyCard}>
                  <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                    <Text style={{ fontSize: 15, fontWeight: "700", color: theme.ink }}>
                      {formatDate(app.from_date)} {app.from_date !== app.to_date ? `to ${formatDate(app.to_date)}` : ""}
                    </Text>
                    <Pill status={sp.tone} label={sp.label} />
                  </View>

                  <View style={{ flexDirection: "row", gap: 8, marginTop: 2 }}>
                    <Text style={{ fontSize: 12, fontWeight: "600", color: theme.primary }}>
                      {app.leave_type_name || "Teacher Leave"}
                    </Text>
                    <Text style={{ fontSize: 12, color: theme.inkFaint }}>•</Text>
                    <Text style={{ fontSize: 12, color: theme.inkFaint }}>
                      {app.days} day{app.days === 1 ? "" : "s"} {app.is_half_day ? "(Half Day)" : ""}
                    </Text>
                  </View>

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

                  {/* Toggle Substitutions Breakdown */}
                  <Pressable
                    onPress={() => setExpandedAppId(isDetailsOpen ? null : app.id)}
                    style={styles.toggleSubsDetailsBtn}
                  >
                    <Text style={styles.toggleSubsDetailsText}>
                      {isDetailsOpen ? "Hide Period Cover Details ▴" : "View Period Substitutions ▾"}
                    </Text>
                  </Pressable>

                  {isDetailsOpen && (
                    <LeaveSubstitutionsViewer
                      applicationId={app.id}
                      onReassign={(period) => setReassignModal({ appId: app.id, period })}
                    />
                  )}
                </View>
              );
            })
          )}
        </Card>
      )}

      {/* Tab 4: Substitution Duties */}
      {activeTab === "duties" && (
        <>
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

          <Card title="Confirmed Substitution Duties">
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
                      {duty.date === todayStr && <Pill status="pending" label="Today" />}
                    </View>
                    <Text style={{ fontSize: 12, fontWeight: "600", color: theme.primary }}>
                      {formatDate(duty.date)}
                    </Text>
                  </View>

                  <View style={{ marginTop: 6, gap: 2 }}>
                    <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
                      Class: {duty.class_label} • Subject: {duty.subject_name}
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

      {/* Reassign Modal */}
      {reassignModal && (
        <Modal
          visible={true}
          transparent
          animationType="fade"
          onRequestClose={() => setReassignModal(null)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Reassign Substitute</Text>
              <Text style={styles.modalSubtitle}>
                {reassignModal.period.date} • Period {reassignModal.period.period_no} ({reassignModal.period.time})
                {"\n"}Class {reassignModal.period.class_label} • {reassignModal.period.subject_name}
              </Text>

              <Text style={[styles.label, { marginTop: 12 }]}>Select New Substitute:</Text>
              <ScrollView style={{ maxHeight: 260, marginTop: 4 }}>
                {reassignModal.period.ranked_substitutes.length === 0 ? (
                  <Text style={{ fontSize: 12, color: theme.inkFaint, padding: 8 }}>
                    No other eligible candidates available for this period.
                  </Text>
                ) : (
                  reassignModal.period.ranked_substitutes.map((cand) => {
                    const badge = getRankBadgeStyle(cand.rank);
                    return (
                      <Pressable
                        key={cand.teacher_id}
                        onPress={() =>
                          reassignMutation.mutate({
                            appId: reassignModal.appId,
                            slotId: reassignModal.period.slot_id,
                            date: reassignModal.period.date,
                            newTeacherId: cand.teacher_id,
                          })
                        }
                        disabled={reassignMutation.isPending}
                        style={styles.candidateItem}
                      >
                        <View style={{ flex: 1 }}>
                          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                            <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
                              {cand.teacher_name}
                            </Text>
                            <View style={[styles.rankBadge, { backgroundColor: badge.bg }]}>
                              <Text style={[styles.rankBadgeText, { color: badge.text }]}>
                                {cand.rank_label}
                              </Text>
                            </View>
                          </View>
                          <Text style={{ fontSize: 11, color: theme.inkFaint, marginTop: 1 }}>
                            {cand.reason}
                          </Text>
                        </View>
                      </Pressable>
                    );
                  })
                )}
              </ScrollView>

              <View style={{ marginTop: 14 }}>
                <Button label="Cancel" tone="ghost" onPress={() => setReassignModal(null)} />
              </View>
            </View>
          </View>
        </Modal>
      )}
    </Screen>
  );
}

/** Component to display per-period substitution breakdown within a leave application card. */
function LeaveSubstitutionsViewer({
  applicationId,
  onReassign,
}: {
  applicationId: number;
  onReassign: (period: ApplicationPeriod) => void;
}) {
  const query = useQuery({
    queryKey: ["teacher-application-substitutions", applicationId],
    queryFn: () =>
      api.get<ApplicationSubstitutionsResponse>(
        `/teacher/leave/applications/${applicationId}/substitutions`
      ),
  });

  if (query.isLoading) return <Loading />;
  if (query.isError || !query.data) {
    return <Text style={{ fontSize: 12, color: theme.danger, marginTop: 6 }}>Could not load substitution details.</Text>;
  }

  const { periods, is_fully_accepted } = query.data;

  if (periods.length === 0) {
    return (
      <View style={{ marginTop: 8, padding: 8, backgroundColor: theme.ground, borderRadius: 6 }}>
        <Text style={{ fontSize: 12, color: theme.inkFaint }}>
          No timetable periods required substitution for this application.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.subsViewerContainer}>
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <Text style={{ fontSize: 12, fontWeight: "700", color: theme.inkSoft }}>
          Period Cover Breakdown:
        </Text>
        <Pill
          status={is_fully_accepted ? "paid" : "pending"}
          label={is_fully_accepted ? "100% Accepted" : "Awaiting Confirmations"}
        />
      </View>

      {periods.map((p, idx) => {
        const statusMap: Record<string, { label: string; tone: string }> = {
          assigned: { label: "Accepted", tone: "paid" },
          pending: { label: "Pending", tone: "pending" },
          rejected: { label: "Declined", tone: "overdue" },
          unassigned: { label: "Unassigned", tone: "overdue" },
        };
        const statusInfo = statusMap[p.status] ?? { label: p.status, tone: "pending" };

        return (
          <View key={`${p.date}_${p.slot_id}_${idx}`} style={styles.subViewerRow}>
            <View style={{ flex: 1 }}>
              <Text style={{ fontSize: 12, fontWeight: "600", color: theme.ink }}>
                {p.date} • P{p.period_no} ({p.time}) • {p.class_label}
              </Text>
              <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                {p.subject_name} • Sub: {p.substitute_teacher_name || "None"}
              </Text>
            </View>

            <View style={{ alignItems: "flex-end", gap: 4 }}>
              <Pill status={statusInfo.tone} label={statusInfo.label} />
              {p.can_reassign && (
                <Pressable onPress={() => onReassign(p)} style={styles.reassignBtn}>
                  <Text style={styles.reassignBtnText}>Reassign</Text>
                </Pressable>
              )}
            </View>
          </View>
        );
      })}
    </View>
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
  typeChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: theme.radius.input,
    borderWidth: 1,
    borderColor: theme.rule,
    backgroundColor: theme.surface,
    minWidth: 100,
  },
  typeChipActive: {
    borderColor: theme.primary,
    backgroundColor: `${theme.primary}12`,
  },
  typeChipCode: {
    fontSize: 12,
    fontWeight: "700",
    color: theme.inkSoft,
  },
  typeChipCodeActive: {
    color: theme.primary,
  },
  typeChipName: {
    fontSize: 11,
    color: theme.ink,
    marginTop: 1,
  },
  typeChipNameActive: {
    fontWeight: "600",
    color: theme.primary,
  },
  typeChipQuota: {
    fontSize: 10,
    color: theme.inkFaint,
    marginTop: 2,
  },
  typeChipQuotaActive: {
    color: theme.primary,
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
  emptyNoticeBox: {
    backgroundColor: `${theme.primary}10`,
    padding: 10,
    borderRadius: 6,
    marginTop: 4,
  },
  emptyNoticeText: {
    fontSize: 12,
    color: theme.primary,
    fontWeight: "500",
  },
  periodCoverCard: {
    backgroundColor: theme.ground,
    borderRadius: 6,
    padding: 10,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  assignedSubBox: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: theme.surface,
    padding: 8,
    borderRadius: 4,
    marginTop: 6,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  changeSubBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  changeSubBtnText: {
    fontSize: 11,
    fontWeight: "600",
    color: theme.primary,
  },
  selectSubBtn: {
    backgroundColor: `${theme.primary}15`,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 4,
    alignItems: "center",
    marginTop: 6,
  },
  selectSubBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.primary,
  },
  candidatesContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: theme.rule,
    gap: 6,
  },
  candidatesHeading: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.inkSoft,
    marginBottom: 2,
  },
  candidateItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 8,
    backgroundColor: theme.surface,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  candidateItemSelected: {
    borderColor: theme.primary,
    backgroundColor: `${theme.primary}10`,
  },
  rankBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  rankBadgeText: {
    fontSize: 10,
    fontWeight: "700",
  },
  requestCard: {
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  requestActions: {
    flexDirection: "row",
    gap: 8,
    marginTop: 10,
  },
  acceptBtn: {
    flex: 1,
    backgroundColor: theme.primary,
    paddingVertical: 8,
    borderRadius: theme.radius.input,
    alignItems: "center",
  },
  acceptBtnText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  declineBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: theme.radius.input,
    alignItems: "center",
    borderWidth: 1,
    borderColor: theme.danger,
  },
  declineBtnText: {
    color: theme.danger,
    fontSize: 12,
    fontWeight: "600",
  },
  historyCard: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  decisionBox: {
    marginTop: 6,
    backgroundColor: `${theme.inkFaint}15`,
    padding: 8,
    borderRadius: 4,
  },
  toggleSubsDetailsBtn: {
    marginTop: 8,
    paddingVertical: 4,
  },
  toggleSubsDetailsText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.primary,
  },
  subsViewerContainer: {
    marginTop: 8,
    padding: 10,
    backgroundColor: theme.ground,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: theme.rule,
    gap: 6,
  },
  subViewerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  reassignBtn: {
    backgroundColor: `${theme.primary}15`,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  reassignBtnText: {
    fontSize: 10,
    fontWeight: "600",
    color: theme.primary,
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
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    padding: 16,
    width: "100%",
    maxWidth: 420,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: theme.ink,
  },
  modalSubtitle: {
    fontSize: 12,
    color: theme.inkSoft,
    marginTop: 4,
    lineHeight: 16,
  },
});
