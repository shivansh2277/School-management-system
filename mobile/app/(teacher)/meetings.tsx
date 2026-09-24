import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
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
import { Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type TeacherMeeting = {
  id: number;
  school_id: number;
  slip_code: string;
  teacher_id: number;
  teacher_name: string;
  visitor_name: string;
  visitor_phone: string;
  visitor_relation: string | null;
  student_name: string | null;
  student_admission_no: string | null;
  reason: string;
  meeting_date: string;
  meeting_time: string;
  status: "pending" | "accepted" | "declined" | "completed" | "cancelled";
  response_notes: string | null;
  responded_at: string | null;
  created_at: string;
};

export default function TeacherMeetingsScreen() {
  const queryClient = useQueryClient();
  const [filterTab, setFilterTab] = useState<"pending" | "all">("pending");
  const [targetMeeting, setTargetMeeting] = useState<TeacherMeeting | null>(null);
  const [decision, setDecision] = useState<"accepted" | "declined">("accepted");
  const [notes, setNotes] = useState("");

  const meetingsQuery = useQuery({
    queryKey: ["teacher-meetings"],
    queryFn: () => api.get<TeacherMeeting[]>("/teacher/meetings"),
  });

  const respondMutation = useMutation({
    mutationFn: ({ id, status, responseNotes }: { id: number; status: string; responseNotes: string }) =>
      api.post(`/teacher/meetings/${id}/respond`, {
        status,
        response_notes: responseNotes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-meetings"] });
      setTargetMeeting(null);
      setNotes("");
      Alert.alert("Success", "Response recorded and front desk notified.");
    },
    onError: (err: any) => {
      Alert.alert("Error", err?.message || "Failed to record response. Please try again.");
    },
  });

  if (meetingsQuery.isLoading) return <Loading />;

  const allMeetings = meetingsQuery.data || [];
  const pendingMeetings = allMeetings.filter((m) => m.status === "pending");
  const displayedMeetings = filterTab === "pending" ? pendingMeetings : allMeetings;

  const openRespondModal = (meeting: TeacherMeeting, initialDecision: "accepted" | "declined") => {
    setTargetMeeting(meeting);
    setDecision(initialDecision);
    setNotes(
      initialDecision === "accepted"
        ? "Available during free period in Staff Room."
        : "Occupied with class duties during this time."
    );
  };

  const submitResponse = () => {
    if (!targetMeeting) return;
    respondMutation.mutate({
      id: targetMeeting.id,
      status: decision,
      responseNotes: notes.trim(),
    });
  };

  return (
    <Screen>
      {/* Header Cards */}
      <View style={styles.statsRow}>
        <View style={[styles.statBox, { borderColor: theme.primary }]}>
          <Text style={styles.statNumber}>{pendingMeetings.length}</Text>
          <Text style={styles.statLabel}>Pending Requests</Text>
        </View>
        <View style={[styles.statBox, { borderColor: theme.rule }]}>
          <Text style={styles.statNumber}>{allMeetings.length}</Text>
          <Text style={styles.statLabel}>Total Slips</Text>
        </View>
      </View>

      {/* Tab Filter */}
      <View style={styles.tabContainer}>
        <Pressable
          onPress={() => setFilterTab("pending")}
          style={[styles.tabButton, filterTab === "pending" && styles.tabButtonActive]}
        >
          <Text style={[styles.tabText, filterTab === "pending" && styles.tabTextActive]}>
            Pending ({pendingMeetings.length})
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setFilterTab("all")}
          style={[styles.tabButton, filterTab === "all" && styles.tabButtonActive]}
        >
          <Text style={[styles.tabText, filterTab === "all" && styles.tabTextActive]}>
            All Slips ({allMeetings.length})
          </Text>
        </Pressable>
      </View>

      {/* List of Meetings */}
      {displayedMeetings.length === 0 ? (
        <Empty
          text={
            filterTab === "pending"
              ? "You have answered all incoming visitor meeting slips."
              : "No meeting requests have been logged by the front desk."
          }
        />
      ) : (
        displayedMeetings.map((item) => {
          const isPending = item.status === "pending";
          const isAccepted = item.status === "accepted";
          const isDeclined = item.status === "declined";

          return (
            <Card key={item.id}>
              {/* Header row */}
              <View style={styles.cardHeader}>
                <View style={styles.badgeRow}>
                  <Text style={styles.slipCode}>{item.slip_code}</Text>
                  <Text style={styles.dateTime}>
                    {formatDate(item.meeting_date)} • {item.meeting_time}
                  </Text>
                </View>
                <Pill
                  status={
                    isAccepted
                      ? "paid"
                      : isDeclined
                      ? "overdue"
                      : "pending"
                  }
                  label={item.status.toUpperCase()}
                />
              </View>

              {/* Visitor Information */}
              <View style={styles.infoSection}>
                <Row
                  left={<Text style={styles.metaLabel}>Visitor</Text>}
                  right={
                    <Text style={styles.boldText}>
                      {item.visitor_name} ({item.visitor_relation || "Visitor"})
                    </Text>
                  }
                />
                <Row
                  left={<Text style={styles.metaLabel}>Phone</Text>}
                  right={<Text style={styles.monoText}>{item.visitor_phone}</Text>}
                />
                {item.student_name && (
                  <Row
                    left={<Text style={styles.metaLabel}>Student Ward</Text>}
                    right={
                      <Text style={styles.valueText}>
                        {item.student_name} {item.student_admission_no ? `(${item.student_admission_no})` : ""}
                      </Text>
                    }
                  />
                )}
                <Row
                  left={<Text style={styles.metaLabel}>Topic / Agenda</Text>}
                  right={<Text style={styles.reasonText}>{item.reason}</Text>}
                />
              </View>

              {/* Response Notes if already responded */}
              {item.response_notes && (
                <View style={styles.notesBox}>
                  <Text style={styles.notesLabel}>Your Response Notes:</Text>
                  <Text style={styles.notesText}>{item.response_notes}</Text>
                </View>
              )}

              {/* Action Buttons for Pending */}
              {isPending && (
                <View style={styles.actionsRow}>
                  <Pressable
                    onPress={() => openRespondModal(item, "accepted")}
                    style={[styles.actionBtn, styles.acceptBtn]}
                  >
                    <Ionicons name="checkmark-circle-outline" size={16} color="#ffffff" />
                    <Text style={styles.actionBtnText}>Accept Meeting</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => openRespondModal(item, "declined")}
                    style={[styles.actionBtn, styles.declineBtn]}
                  >
                    <Ionicons name="close-circle-outline" size={16} color="#ffffff" />
                    <Text style={styles.actionBtnText}>Decline</Text>
                  </Pressable>
                </View>
              )}
            </Card>
          );
        })
      )}

      {/* Response Modal */}
      {targetMeeting && (
        <Modal
          visible={!!targetMeeting}
          transparent
          animationType="fade"
          onRequestClose={() => setTargetMeeting(null)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              {/* Modal Header with Standard Red-X dismiss */}
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Respond to Meeting Slip</Text>
                <Pressable
                  onPress={() => setTargetMeeting(null)}
                  style={styles.closeBtn}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Ionicons name="close" size={22} color={theme.danger} />
                </Pressable>
              </View>

              <ScrollView style={styles.modalBody}>
                <View style={styles.visitorSummary}>
                  <Text style={styles.visitorTitle}>
                    {targetMeeting.visitor_name} ({targetMeeting.visitor_relation || "Visitor"})
                  </Text>
                  <Text style={styles.visitorTopic}>Topic: {targetMeeting.reason}</Text>
                  <Text style={styles.visitorTime}>
                    Requested: {formatDate(targetMeeting.meeting_date)} at {targetMeeting.meeting_time}
                  </Text>
                </View>

                {/* Decision Toggle */}
                <Text style={styles.inputLabel}>Decision</Text>
                <View style={styles.decisionRow}>
                  <Pressable
                    onPress={() => setDecision("accepted")}
                    style={[styles.decisionBtn, decision === "accepted" && styles.decisionBtnAccepted]}
                  >
                    <Ionicons
                      name="checkmark-circle"
                      size={18}
                      color={decision === "accepted" ? "#ffffff" : theme.inkFaint}
                    />
                    <Text
                      style={[
                        styles.decisionText,
                        decision === "accepted" && styles.decisionTextActive,
                      ]}
                    >
                      Accept
                    </Text>
                  </Pressable>

                  <Pressable
                    onPress={() => setDecision("declined")}
                    style={[styles.decisionBtn, decision === "declined" && styles.decisionBtnDeclined]}
                  >
                    <Ionicons
                      name="close-circle"
                      size={18}
                      color={decision === "declined" ? "#ffffff" : theme.inkFaint}
                    />
                    <Text
                      style={[
                        styles.decisionText,
                        decision === "declined" && styles.decisionTextActive,
                      ]}
                    >
                      Decline
                    </Text>
                  </Pressable>
                </View>

                {/* Notes Input */}
                <Text style={styles.inputLabel}>
                  {decision === "accepted" ? "Timing / Staff Room Notes" : "Reason for Declining"}
                </Text>
                <TextInput
                  value={notes}
                  onChangeText={setNotes}
                  multiline
                  numberOfLines={3}
                  placeholder={
                    decision === "accepted"
                      ? "e.g. Free after period 4 at 01:30 PM in Staff Room."
                      : "e.g. Scheduled examination supervision duties."
                  }
                  placeholderTextColor={theme.inkFaint}
                  style={styles.textInput}
                />
              </ScrollView>

              {/* Modal Footer */}
              <View style={styles.modalFooter}>
                <Pressable
                  onPress={() => setTargetMeeting(null)}
                  style={styles.cancelBtn}
                >
                  <Text style={styles.cancelBtnText}>Cancel</Text>
                </Pressable>

                <Pressable
                  onPress={submitResponse}
                  disabled={respondMutation.isPending}
                  style={[
                    styles.submitBtn,
                    decision === "accepted" ? { backgroundColor: theme.primary } : { backgroundColor: theme.danger },
                  ]}
                >
                  <Text style={styles.submitBtnText}>
                    {respondMutation.isPending ? "Submitting..." : "Send Decision"}
                  </Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  statsRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 8,
  },
  statBox: {
    flex: 1,
    backgroundColor: theme.surface,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    alignItems: "center",
  },
  statNumber: {
    fontSize: 22,
    fontWeight: "700",
    color: theme.ink,
  },
  statLabel: {
    fontSize: 11,
    color: theme.inkFaint,
    marginTop: 2,
    fontWeight: "500",
  },
  metaLabel: {
    fontSize: 12,
    color: theme.inkFaint,
    fontWeight: "500",
  },
  tabContainer: {
    flexDirection: "row",
    backgroundColor: theme.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 4,
    marginBottom: 4,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: "center",
  },
  tabButtonActive: {
    backgroundColor: theme.primary,
  },
  tabText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkFaint,
  },
  tabTextActive: {
    color: "#ffffff",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 6,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  badgeRow: {
    flex: 1,
    marginRight: 8,
  },
  slipCode: {
    fontSize: 13,
    fontWeight: "700",
    color: theme.ink,
  },
  dateTime: {
    fontSize: 11,
    color: theme.inkFaint,
    marginTop: 2,
  },
  infoSection: {
    gap: 2,
  },
  boldText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.ink,
  },
  monoText: {
    fontSize: 12,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    color: theme.ink,
  },
  valueText: {
    fontSize: 12,
    color: theme.ink,
  },
  reasonText: {
    fontSize: 12,
    color: theme.ink,
    fontStyle: "italic",
  },
  notesBox: {
    marginTop: 10,
    padding: 8,
    backgroundColor: "#f0fdf4",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#bbf7d0",
  },
  notesLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#166534",
    textTransform: "uppercase",
  },
  notesText: {
    fontSize: 11,
    color: "#14532d",
    marginTop: 2,
  },
  actionsRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.rule,
  },
  actionBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 9,
    borderRadius: 8,
    gap: 6,
  },
  acceptBtn: {
    backgroundColor: "#16a34a",
  },
  declineBtn: {
    backgroundColor: "#dc2626",
  },
  actionBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: theme.surface,
    borderRadius: 16,
    maxHeight: "80%",
    overflow: "hidden",
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  modalTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: theme.ink,
  },
  closeBtn: {
    padding: 4,
  },
  modalBody: {
    padding: 16,
  },
  visitorSummary: {
    backgroundColor: "#f8fafc",
    padding: 10,
    borderRadius: 8,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  visitorTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: theme.ink,
  },
  visitorTopic: {
    fontSize: 12,
    color: theme.inkFaint,
    marginTop: 2,
  },
  visitorTime: {
    fontSize: 11,
    color: theme.inkFaint,
    marginTop: 2,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.inkFaint,
    textTransform: "uppercase",
    marginBottom: 6,
  },
  decisionRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 14,
  },
  decisionBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: theme.rule,
    backgroundColor: theme.surface,
    gap: 6,
  },
  decisionBtnAccepted: {
    backgroundColor: "#16a34a",
    borderColor: "#16a34a",
  },
  decisionBtnDeclined: {
    backgroundColor: "#dc2626",
    borderColor: "#dc2626",
  },
  decisionText: {
    fontSize: 12,
    fontWeight: "700",
    color: theme.ink,
  },
  decisionTextActive: {
    color: "#ffffff",
  },
  textInput: {
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 8,
    padding: 10,
    fontSize: 12,
    color: theme.ink,
    backgroundColor: "#ffffff",
    textAlignVertical: "top",
    minHeight: 70,
  },
  modalFooter: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 10,
    padding: 14,
    borderTopWidth: 1,
    borderTopColor: theme.rule,
  },
  cancelBtn: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    justifyContent: "center",
  },
  cancelBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkFaint,
  },
  submitBtn: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 8,
    justifyContent: "center",
  },
  submitBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700",
  },
});
