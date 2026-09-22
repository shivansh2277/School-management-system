import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  Alert,
  Modal,
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

type Grievance = {
  id: number;
  school_id: number;
  title: string;
  description: string;
  category: string;
  raised_by_id: number;
  raised_by_role: string;
  raised_by_name: string;
  student_id?: number | null;
  student_name?: string | null;
  status: "open" | "in_progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "urgent";
  assigned_to_id?: number | null;
  assigned_to_name?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
  replies_count: number;
  replies?: GrievanceReply[];
};

type GrievanceReply = {
  id: number;
  grievance_id: number;
  author_id: number;
  author_name: string;
  author_role: string;
  message: string;
  is_internal: boolean;
  created_at: string;
};

export default function TeacherGrievances() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"all" | "mine" | "assigned">("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGrievance, setSelectedGrievance] = useState<Grievance | null>(null);

  // New Grievance Form
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCategory, setNewCategory] = useState("facilities");
  const [newPriority, setNewPriority] = useState<"low" | "medium" | "high" | "urgent">("medium");

  // Reply Form
  const [replyText, setReplyText] = useState("");

  const { data: grievances = [], isLoading } = useQuery({
    queryKey: ["teacher-grievances", activeTab],
    queryFn: () => api.get<Grievance[]>(`/teacher/grievances?tab=${activeTab}`),
  });

  const createMutation = useMutation({
    mutationFn: (body: {
      title: string;
      description: string;
      category: string;
      priority: string;
    }) => api.post("/teacher/grievances", body),
    onSuccess: () => {
      Alert.alert("Grievance Submitted", "Your issue has been logged and sent to administration.");
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewCategory("facilities");
      setNewPriority("medium");
      queryClient.invalidateQueries({ queryKey: ["teacher-grievances"] });
    },
    onError: (err: any) => {
      Alert.alert("Submission Failed", err?.message || "Could not submit grievance.");
    },
  });

  const replyMutation = useMutation({
    mutationFn: ({ id, message }: { id: number; message: string }) =>
      api.post(`/teacher/grievances/${id}/reply`, { message }),
    onSuccess: () => {
      setReplyText("");
      queryClient.invalidateQueries({ queryKey: ["teacher-grievances"] });
      // update selected grievance replies locally if open
      if (selectedGrievance) {
        api.get<Grievance>(`/teacher/grievances/${selectedGrievance.id}`).then((updated) => {
          setSelectedGrievance(updated);
        });
      }
    },
    onError: (err: any) => {
      Alert.alert("Reply Failed", err?.message || "Could not post reply.");
    },
  });

  const handleCreate = () => {
    if (!newTitle.trim() || !newDescription.trim()) {
      Alert.alert("Missing Details", "Please provide a title and detailed description.");
      return;
    }
    createMutation.mutate({
      title: newTitle.trim(),
      description: newDescription.trim(),
      category: newCategory,
      priority: newPriority,
    });
  };

  if (isLoading) return <Loading />;

  return (
    <Screen>
      {/* Top Controls: Tabs & Submit Button */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
          <View style={{ flexDirection: "row", gap: 6 }}>
            {(["all", "mine", "assigned"] as const).map((t) => (
              <Pressable
                key={t}
                onPress={() => setActiveTab(t)}
                style={[styles.tabBtn, activeTab === t && styles.tabBtnActive]}
              >
                <Text style={[styles.tabText, activeTab === t && styles.tabTextActive]}>
                  {t === "all" ? "All" : t === "mine" ? "My Issues" : "Assigned to Me"}
                </Text>
              </Pressable>
            ))}
          </View>
          <Pressable
            onPress={() => setShowCreateModal(true)}
            style={styles.newGrievanceBtn}
          >
            <Text style={styles.newGrievanceBtnText}>+ New Issue</Text>
          </Pressable>
        </View>
      </Card>

      {/* Grievances List */}
      {grievances.length === 0 ? (
        <Card>
          <Empty text="No grievances found in this tab." />
        </Card>
      ) : (
        grievances.map((g) => (
          <Card key={g.id}>
            <Pressable onPress={() => setSelectedGrievance(g)}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <View style={{ flexDirection: "row", gap: 6, alignItems: "center" }}>
                  <Pill
                    status={
                      g.status === "open"
                        ? "absent"
                        : g.status === "in_progress"
                        ? "leave"
                        : "present"
                    }
                    label={g.status.replace("_", " ")}
                  />
                  <Text style={[styles.priorityTag, { color: g.priority === "urgent" ? theme.danger : theme.inkSoft }]}>
                    {g.priority.toUpperCase()}
                  </Text>
                </View>
                <Text style={s.meta}>{formatDate(g.created_at)}</Text>
              </View>

              <Text style={{ fontSize: 15, fontWeight: "600", color: theme.ink }}>{g.title}</Text>
              <Text style={[s.meta, { marginTop: 2 }]} numberOfLines={2}>
                {g.description}
              </Text>

              <View style={styles.cardFooter}>
                <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                  By: {g.raised_by_name} ({g.raised_by_role})
                </Text>
                <Text style={{ fontSize: 11, color: theme.primary, fontWeight: "600" }}>
                  {g.replies_count > 0 ? `${g.replies_count} replies` : "View Thread"} &rarr;
                </Text>
              </View>
            </Pressable>
          </Card>
        ))
      )}

      {/* New Grievance Modal */}
      {showCreateModal && (
        <Modal visible={true} transparent={true} animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.modalTitle}>Submit New Grievance</Text>
                  <Text style={styles.modalSubtitle}>Report a classroom, lab, or administrative concern</Text>
                </View>
                <Pressable
                  onPress={() => setShowCreateModal(false)}
                  style={{
                    padding: 6,
                    borderRadius: 20,
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                  accessibilityRole="button"
                  accessibilityLabel="Close"
                >
                  <Ionicons name="close" size={22} color="#ef4444" />
                </Pressable>
              </View>

              <View style={{ gap: 10, marginTop: 12 }}>
                <View>
                  <Text style={styles.inputLabel}>Subject / Title</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Brief summary of the problem"
                    placeholderTextColor={theme.inkFaint}
                    value={newTitle}
                    onChangeText={setNewTitle}
                  />
                </View>

                <View>
                  <Text style={styles.inputLabel}>Category</Text>
                  <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
                    {["facilities", "academic", "discipline", "general"].map((cat) => (
                      <Pressable
                        key={cat}
                        onPress={() => setNewCategory(cat)}
                        style={[styles.chip, newCategory === cat && styles.chipActive]}
                      >
                        <Text style={[styles.chipText, newCategory === cat && styles.chipTextActive]}>
                          {cat}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                <View>
                  <Text style={styles.inputLabel}>Priority</Text>
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    {(["low", "medium", "high", "urgent"] as const).map((pri) => (
                      <Pressable
                        key={pri}
                        onPress={() => setNewPriority(pri)}
                        style={[styles.chip, newPriority === pri && styles.chipActive, { flex: 1, alignItems: "center" }]}
                      >
                        <Text style={[styles.chipText, newPriority === pri && styles.chipTextActive]}>
                          {pri}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                <View>
                  <Text style={styles.inputLabel}>Detailed Description</Text>
                  <TextInput
                    style={[styles.input, { height: 80, textAlignVertical: "top" }]}
                    placeholder="Describe the issue in detail..."
                    placeholderTextColor={theme.inkFaint}
                    multiline={true}
                    value={newDescription}
                    onChangeText={setNewDescription}
                  />
                </View>

                <View style={{ flexDirection: "row", gap: 10, marginTop: 10 }}>
                  <Pressable
                    onPress={() => setShowCreateModal(false)}
                    style={[styles.actionBtn, { backgroundColor: theme.ground }]}
                  >
                    <Text style={{ color: theme.inkSoft, fontWeight: "600" }}>Cancel</Text>
                  </Pressable>
                  <Pressable
                    onPress={handleCreate}
                    disabled={createMutation.isPending}
                    style={[styles.actionBtn, { backgroundColor: theme.primary, flex: 2 }]}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700" }}>
                      {createMutation.isPending ? "Submitting..." : "Submit Grievance"}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>
        </Modal>
      )}

      {/* Grievance Detail & Reply Modal */}
      {selectedGrievance && (
        <Modal visible={true} transparent={true} animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { maxHeight: "85%" }]}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.modalTitle}>{selectedGrievance.title}</Text>
                  <Text style={styles.modalSubtitle}>
                    Category: {selectedGrievance.category} • Raised by: {selectedGrievance.raised_by_name}
                  </Text>
                </View>
                <Pressable
                  onPress={() => setSelectedGrievance(null)}
                  style={{
                    padding: 6,
                    borderRadius: 20,
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                  accessibilityRole="button"
                  accessibilityLabel="Close"
                >
                  <Ionicons name="close" size={22} color="#ef4444" />
                </Pressable>
              </View>

              <ScrollView style={{ marginTop: 10, flexGrow: 0, maxHeight: 180 }}>
                <View style={{ backgroundColor: theme.ground, padding: 10, borderRadius: 8 }}>
                  <Text style={{ fontSize: 13, color: theme.ink, lineHeight: 18 }}>
                    {selectedGrievance.description}
                  </Text>
                  {selectedGrievance.resolution_notes ? (
                    <View style={{ marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.rule }}>
                      <Text style={{ fontSize: 11, fontWeight: "700", color: theme.success }}>
                        Resolution Notes:
                      </Text>
                      <Text style={{ fontSize: 12, color: theme.inkSoft }}>
                        {selectedGrievance.resolution_notes}
                      </Text>
                    </View>
                  ) : null}
                </View>
              </ScrollView>

              {/* Replies History */}
              <Text style={[styles.inputLabel, { marginTop: 12, marginBottom: 4 }]}>Replies & Updates</Text>
              <ScrollView style={{ maxHeight: 140, flexGrow: 0 }}>
                {selectedGrievance.replies && selectedGrievance.replies.length > 0 ? (
                  selectedGrievance.replies.map((r) => (
                    <View
                      key={r.id}
                      style={[
                        styles.replyBox,
                        r.author_role === "admin" && { backgroundColor: `${theme.primary}10` },
                      ]}
                    >
                      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                        <Text style={{ fontSize: 11, fontWeight: "700", color: theme.ink }}>
                          {r.author_name} ({r.author_role})
                        </Text>
                        <Text style={{ fontSize: 10, color: theme.inkFaint }}>
                          {formatDate(r.created_at)}
                        </Text>
                      </View>
                      <Text style={{ fontSize: 12, color: theme.ink, marginTop: 2 }}>{r.message}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={{ fontSize: 12, color: theme.inkFaint, fontStyle: "italic", paddingVertical: 6 }}>
                    No replies yet.
                  </Text>
                )}
              </ScrollView>

              {/* Reply Input */}
              <View style={{ flexDirection: "row", gap: 8, marginTop: 10, alignItems: "center" }}>
                <TextInput
                  style={[styles.input, { flex: 1, height: 40 }]}
                  placeholder="Type a reply..."
                  placeholderTextColor={theme.inkFaint}
                  value={replyText}
                  onChangeText={setReplyText}
                />
                <Pressable
                  onPress={() => {
                    if (replyText.trim()) {
                      replyMutation.mutate({
                        id: selectedGrievance.id,
                        message: replyText.trim(),
                      });
                    }
                  }}
                  disabled={!replyText.trim() || replyMutation.isPending}
                  style={[styles.actionBtn, { backgroundColor: theme.primary, paddingHorizontal: 16 }]}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 12 }}>
                    {replyMutation.isPending ? "..." : "Reply"}
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
  tabBtn: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: theme.ground,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  tabBtnActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  tabText: {
    fontSize: 11,
    fontWeight: "600",
    color: theme.inkSoft,
  },
  tabTextActive: {
    color: "#fff",
  },
  newGrievanceBtn: {
    backgroundColor: `${theme.primary}15`,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  newGrievanceBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.primary,
  },
  priorityTag: {
    fontSize: 10,
    fontWeight: "700",
  },
  cardFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: theme.rule,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: theme.ground,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  chipActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  chipText: {
    fontSize: 11,
    color: theme.inkSoft,
    textTransform: "capitalize",
  },
  chipTextActive: {
    color: "#fff",
    fontWeight: "600",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 16,
  },
  modalContent: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 18,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
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
    marginTop: 2,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    color: theme.ink,
    backgroundColor: theme.ground,
  },
  actionBtn: {
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  replyBox: {
    backgroundColor: theme.ground,
    padding: 8,
    borderRadius: 6,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: theme.rule,
  },
});
