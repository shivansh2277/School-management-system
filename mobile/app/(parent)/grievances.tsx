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
import { useAuth } from "../../src/auth/AuthContext";
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

export default function ParentGrievances() {
  const queryClient = useQueryClient();
  const { me, selectedChildId } = useAuth();
  const children = me?.children ?? [];

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGrievance, setSelectedGrievance] = useState<Grievance | null>(null);

  // New Grievance Form
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCategory, setNewCategory] = useState("general");
  const [newPriority, setNewPriority] = useState<"low" | "medium" | "high" | "urgent">("medium");
  const [targetStudentId, setTargetStudentId] = useState<number | null>(selectedChildId || (children[0]?.id ?? null));

  // Reply Form
  const [replyText, setReplyText] = useState("");

  const { data: grievances = [], isLoading } = useQuery({
    queryKey: ["parent-grievances"],
    queryFn: () => api.get<Grievance[]>("/parent/grievances"),
  });

  const createMutation = useMutation({
    mutationFn: (body: {
      title: string;
      description: string;
      category: string;
      priority: string;
      student_id?: number | null;
    }) => api.post("/parent/grievances", body),
    onSuccess: () => {
      Alert.alert("Grievance Submitted", "Your issue has been received by the school administration.");
      setShowCreateModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewCategory("general");
      setNewPriority("medium");
      queryClient.invalidateQueries({ queryKey: ["parent-grievances"] });
    },
    onError: (err: any) => {
      Alert.alert("Submission Failed", err?.message || "Could not submit grievance.");
    },
  });

  const replyMutation = useMutation({
    mutationFn: ({ id, message }: { id: number; message: string }) =>
      api.post(`/parent/grievances/${id}/reply`, { message }),
    onSuccess: () => {
      setReplyText("");
      queryClient.invalidateQueries({ queryKey: ["parent-grievances"] });
      if (selectedGrievance) {
        api.get<Grievance>(`/parent/grievances/${selectedGrievance.id}`).then((updated) => {
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
      Alert.alert("Missing Details", "Please provide a subject title and detailed explanation.");
      return;
    }
    createMutation.mutate({
      title: newTitle.trim(),
      description: newDescription.trim(),
      category: newCategory,
      priority: newPriority,
      student_id: targetStudentId,
    });
  };

  if (isLoading) return <Loading />;

  return (
    <Screen>
      {/* Header Info & Submit Action */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
          <View style={{ flex: 1, paddingRight: 8 }}>
            <Text style={{ fontSize: 16, fontWeight: "700", color: theme.ink }}>
              Helpdesk & Grievances
            </Text>
            <Text style={s.meta}>
              Submit concerns regarding transport, fees, academics, or facilities directly to school leadership.
            </Text>
          </View>
          <Pressable
            onPress={() => {
              setTargetStudentId(selectedChildId || (children[0]?.id ?? null));
              setShowCreateModal(true);
            }}
            style={styles.newBtn}
          >
            <Text style={styles.newBtnText}>+ New Problem</Text>
          </Pressable>
        </View>
      </Card>

      {/* Grievances List */}
      {grievances.length === 0 ? (
        <Card>
          <Empty text="You haven't submitted any grievances yet." />
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
                  {g.student_name ? `Child: ${g.student_name}` : `Category: ${g.category}`}
                </Text>
                <Text style={{ fontSize: 11, color: theme.primary, fontWeight: "600" }}>
                  {g.replies_count > 0 ? `${g.replies_count} messages` : "View Details"} &rarr;
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
                  <Text style={styles.modalTitle}>Submit Concern / Grievance</Text>
                  <Text style={styles.modalSubtitle}>Direct communication with school administrators</Text>
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
                {/* Child selector if multiple children */}
                {children.length > 0 && (
                  <View>
                    <Text style={styles.inputLabel}>Relates to Child</Text>
                    <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
                      {children.map((c) => (
                        <Pressable
                          key={c.id}
                          onPress={() => setTargetStudentId(c.id)}
                          style={[styles.chip, targetStudentId === c.id && styles.chipActive]}
                        >
                          <Text style={[styles.chipText, targetStudentId === c.id && styles.chipTextActive]}>
                            {c.name} ({c.class_label})
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  </View>
                )}

                <View>
                  <Text style={styles.inputLabel}>Subject</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Brief description of the problem"
                    placeholderTextColor={theme.inkFaint}
                    value={newTitle}
                    onChangeText={setNewTitle}
                  />
                </View>

                <View>
                  <Text style={styles.inputLabel}>Category</Text>
                  <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
                    {["transport", "fees", "academic", "facilities", "general"].map((cat) => (
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
                  <Text style={styles.inputLabel}>Urgency</Text>
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
                  <Text style={styles.inputLabel}>Description of Problem</Text>
                  <TextInput
                    style={[styles.input, { height: 80, textAlignVertical: "top" }]}
                    placeholder="Please explain the details of the issue..."
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
                      {createMutation.isPending ? "Submitting..." : "Submit Concern"}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>
        </Modal>
      )}

      {/* Grievance Detail & Message Thread Modal */}
      {selectedGrievance && (
        <Modal visible={true} transparent={true} animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { maxHeight: "85%" }]}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.modalTitle}>{selectedGrievance.title}</Text>
                  <Text style={styles.modalSubtitle}>
                    Category: {selectedGrievance.category}
                    {selectedGrievance.student_name ? ` • Child: ${selectedGrievance.student_name}` : ""}
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
                        School Resolution:
                      </Text>
                      <Text style={{ fontSize: 12, color: theme.inkSoft }}>
                        {selectedGrievance.resolution_notes}
                      </Text>
                    </View>
                  ) : null}
                </View>
              </ScrollView>

              {/* Messages Thread */}
              <Text style={[styles.inputLabel, { marginTop: 12, marginBottom: 4 }]}>Communication Thread</Text>
              <ScrollView style={{ maxHeight: 140, flexGrow: 0 }}>
                {selectedGrievance.replies && selectedGrievance.replies.length > 0 ? (
                  selectedGrievance.replies.map((r) => (
                    <View
                      key={r.id}
                      style={[
                        styles.replyBox,
                        r.author_role === "admin" || r.author_role === "teacher"
                          ? { backgroundColor: `${theme.primary}10`, borderColor: `${theme.primary}20` }
                          : {},
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
                    No messages yet. School staff will review your submission shortly.
                  </Text>
                )}
              </ScrollView>

              {/* Reply Input */}
              <View style={{ flexDirection: "row", gap: 8, marginTop: 10, alignItems: "center" }}>
                <TextInput
                  style={[styles.input, { flex: 1, height: 40 }]}
                  placeholder="Send a response..."
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
                    {replyMutation.isPending ? "..." : "Send"}
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
  newBtn: {
    backgroundColor: `${theme.primary}15`,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
  },
  newBtnText: {
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
