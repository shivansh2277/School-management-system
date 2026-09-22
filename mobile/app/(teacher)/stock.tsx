import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useMemo } from "react";
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

import { api } from "../../src/api/client";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type StockItem = {
  id: number;
  school_id: number;
  name: string;
  category: string;
  location: string;
  unit: string;
  current_quantity: number;
  min_quantity: number;
  unit_cost?: string | number | null;
  is_critical: boolean;
  has_discrepancy: boolean;
  is_low_stock: boolean;
};

export default function TeacherStock() {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [flagItem, setFlagItem] = useState<StockItem | null>(null);
  const [consumeItem, setConsumeItem] = useState<StockItem | null>(null);

  // Form State
  const [quantity, setQuantity] = useState("1");
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "critical">("normal");
  const [reason, setReason] = useState("");

  // Consume Form State
  const [consumeQuantity, setConsumeQuantity] = useState("1");
  const [consumeReason, setConsumeReason] = useState("");

  const { data: items = [], isLoading, error } = useQuery({
    queryKey: ["teacher-stock-items"],
    queryFn: () => api.get<StockItem[]>("/teacher/stock/items"),
  });

  const categories = useMemo(() => {
    const set = new Set<string>();
    items.forEach((it) => set.add(it.category));
    return ["all", ...Array.from(set).sort()];
  }, [items]);

  const filtered = useMemo(() => {
    return items.filter((it) => {
      const matchCat = selectedCategory === "all" || it.category === selectedCategory;
      const matchSearch =
        search === "" ||
        it.name.toLowerCase().includes(search.toLowerCase()) ||
        it.location.toLowerCase().includes(search.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [items, selectedCategory, search]);

  const flagMutation = useMutation({
    mutationFn: (body: {
      item_id: number;
      item_name: string;
      category: string;
      location: string;
      quantity_requested: number;
      urgency: string;
      reason: string;
      flag_type: string;
    }) => api.post("/teacher/stock/flag", body),
    onSuccess: () => {
      Alert.alert("Stock Flagged", "Your replenishment request has been submitted to the admin office.");
      setFlagItem(null);
      setQuantity("1");
      setReason("");
      setUrgency("normal");
      queryClient.invalidateQueries({ queryKey: ["teacher-stock-items"] });
    },
    onError: (err: any) => {
      Alert.alert("Submission Failed", err?.message || "Could not submit stock flag.");
    },
  });

  const consumeMutation = useMutation({
    mutationFn: ({
      itemId,
      quantity: qty,
      reason: rsn,
    }: {
      itemId: number;
      quantity: number;
      reason?: string;
    }) =>
      api.post<StockItem>(`/teacher/stock/${itemId}/consume`, {
        quantity: qty,
        reason: rsn,
      }),
    onSuccess: (updated) => {
      Alert.alert(
        "Stock Updated",
        `Successfully logged usage of ${updated.name}. Remaining: ${updated.current_quantity} ${updated.unit}${
          updated.is_low_stock ? " (Low Stock Threshold Reached!)" : ""
        }`
      );
      setConsumeItem(null);
      setConsumeQuantity("1");
      setConsumeReason("");
      queryClient.invalidateQueries({ queryKey: ["teacher-stock-items"] });
    },
    onError: (err: any) => {
      Alert.alert("Consumption Failed", err?.message || "Could not record stock consumption.");
    },
  });

  const handleOpenConsume = (item: StockItem) => {
    setConsumeItem(item);
    setConsumeQuantity("1");
    setConsumeReason("");
  };

  const handleConfirmConsume = () => {
    if (!consumeItem) return;
    const qty = parseInt(consumeQuantity, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("Invalid Quantity", "Please enter a valid positive quantity.");
      return;
    }
    if (qty > consumeItem.current_quantity) {
      Alert.alert(
        "Insufficient Stock",
        `Cannot consume ${qty} units. Only ${consumeItem.current_quantity} ${consumeItem.unit} currently available.`
      );
      return;
    }
    consumeMutation.mutate({
      itemId: consumeItem.id,
      quantity: qty,
      reason: consumeReason.trim() || undefined,
    });
  };

  const handleOpenFlag = (item: StockItem) => {
    setFlagItem(item);
    setQuantity("2");
    setReason("");
    setUrgency(item.is_low_stock ? "urgent" : "normal");
  };

  const handleSubmitFlag = () => {
    if (!flagItem) return;
    if (!reason.trim()) {
      Alert.alert("Reason Required", "Please describe why this item is diminishing or needed.");
      return;
    }
    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("Invalid Quantity", "Please enter a valid positive number.");
      return;
    }

    flagMutation.mutate({
      item_id: flagItem.id,
      item_name: flagItem.name,
      category: flagItem.category,
      location: flagItem.location,
      quantity_requested: qty,
      urgency,
      reason: reason.trim(),
      flag_type: "diminishing",
    });
  };

  if (isLoading) return <Loading />;

  return (
    <Screen>
      {/* Header Info */}
      <Card>
        <Text style={{ fontSize: 16, fontWeight: "700", color: theme.ink }}>
          Classroom & Lab Supplies
        </Text>
        <Text style={s.meta}>
          Check availability of lab chemicals, glassware, art materials, and stationery. Flag
          depleting items to notify the admin store.
        </Text>
        {/* Search Bar */}
        <TextInput
          style={styles.searchInput}
          placeholder="Search items or location..."
          value={search}
          onChangeText={setSearch}
          placeholderTextColor={theme.inkFaint}
        />
        {/* Category Pills Scroll */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 6 }}>
          <View style={{ flexDirection: "row", gap: 6 }}>
            {categories.map((c) => (
              <Pressable
                key={c}
                onPress={() => setSelectedCategory(c)}
                style={[
                  styles.categoryPill,
                  selectedCategory === c && styles.categoryPillActive,
                ]}
              >
                <Text
                  style={[
                    styles.categoryPillText,
                    selectedCategory === c && styles.categoryPillTextActive,
                  ]}
                >
                  {c === "all" ? "All Supplies" : c}
                </Text>
              </Pressable>
            ))}
          </View>
        </ScrollView>
      </Card>

      {/* Items List */}
      {filtered.length === 0 ? (
        <Card>
          <Empty text="No supplies match your search criteria." />
        </Card>
      ) : (
        filtered.map((item) => {
          const isLow = item.current_quantity <= item.min_quantity;
          return (
            <Card key={item.id}>
              <Row
                left={
                  <View style={{ gap: 2 }}>
                    <Text style={{ fontSize: 15, fontWeight: "600", color: theme.ink }}>
                      {item.name}
                    </Text>
                    <Text style={s.meta}>
                      {item.category} • {item.location}
                    </Text>
                  </View>
                }
                right={
                  <View style={{ alignItems: "flex-end", gap: 4 }}>
                    <Pill
                      status={isLow ? "absent" : "present"}
                      label={isLow ? "Low Stock" : "In Stock"}
                    />
                    <Text style={{ fontSize: 12, fontWeight: "600", color: theme.inkSoft }}>
                      {item.current_quantity} {item.unit}
                    </Text>
                  </View>
                }
              />
              <View style={styles.itemFooter}>
                <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                  Min: {item.min_quantity} {item.unit}
                </Text>
                <View style={{ flexDirection: "row", gap: 8 }}>
                  <Pressable
                    onPress={() => handleOpenConsume(item)}
                    disabled={item.current_quantity <= 0}
                    style={[styles.consumeBtn, item.current_quantity <= 0 && { opacity: 0.5 }]}
                  >
                    <Text style={styles.consumeBtnText}>Use / Consume</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => handleOpenFlag(item)}
                    style={[styles.flagBtn, isLow && styles.flagBtnUrgent]}
                  >
                    <Text style={[styles.flagBtnText, isLow && styles.flagBtnTextUrgent]}>
                      Flag &rarr;
                    </Text>
                  </Pressable>
                </View>
              </View>
            </Card>
          );
        })
      )}

      {/* Flag Modal */}
      {flagItem && (
        <Modal visible={true} transparent={true} animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.modalTitle}>Flag Diminishing Stock</Text>
                  <Text style={styles.modalSubtitle}>
                    {flagItem.name} ({flagItem.location})
                  </Text>
                </View>
                <Pressable
                  onPress={() => setFlagItem(null)}
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
              <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 4 }}>
                Current quantity: {flagItem.current_quantity} {flagItem.unit} (Min: {flagItem.min_quantity})
              </Text>

              <View style={{ gap: 10, marginTop: 14 }}>
                <View>
                  <Text style={styles.inputLabel}>Quantity Needed ({flagItem.unit})</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    value={quantity}
                    onChangeText={setQuantity}
                  />
                </View>

                <View>
                  <Text style={styles.inputLabel}>Urgency Level</Text>
                  <View style={{ flexDirection: "row", gap: 8, marginTop: 4 }}>
                    {(["normal", "urgent", "critical"] as const).map((u) => (
                      <Pressable
                        key={u}
                        onPress={() => setUrgency(u)}
                        style={[
                          styles.urgencyOption,
                          urgency === u && styles.urgencyOptionActive,
                        ]}
                      >
                        <Text
                          style={[
                            styles.urgencyText,
                            urgency === u && styles.urgencyTextActive,
                          ]}
                        >
                          {u.toUpperCase()}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                <View>
                  <Text style={styles.inputLabel}>Reason / Classroom Context</Text>
                  <TextInput
                    style={[styles.input, { height: 70, textAlignVertical: "top" }]}
                    placeholder="e.g., Practical exam batches start on Monday..."
                    placeholderTextColor={theme.inkFaint}
                    multiline={true}
                    value={reason}
                    onChangeText={setReason}
                  />
                </View>

                <View style={{ flexDirection: "row", gap: 10, marginTop: 12 }}>
                  <Pressable
                    onPress={() => setFlagItem(null)}
                    style={[styles.actionBtn, { backgroundColor: theme.ground }]}
                  >
                    <Text style={{ color: theme.inkSoft, fontWeight: "600" }}>Cancel</Text>
                  </Pressable>
                  <Pressable
                    onPress={handleSubmitFlag}
                    disabled={flagMutation.isPending}
                    style={[styles.actionBtn, { backgroundColor: theme.primary, flex: 2 }]}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700" }}>
                      {flagMutation.isPending ? "Submitting..." : "Submit Flag"}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>
        </Modal>
      )}

      {/* Consume Modal */}
      {consumeItem && (
        <Modal visible={true} transparent={true} animationType="slide">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, paddingRight: 8 }}>
                  <Text style={styles.modalTitle}>Record Stock Consumption</Text>
                  <Text style={styles.modalSubtitle}>
                    {consumeItem.name} ({consumeItem.location})
                  </Text>
                </View>
                <Pressable
                  onPress={() => setConsumeItem(null)}
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
              <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 4 }}>
                Available in store: {consumeItem.current_quantity} {consumeItem.unit} (Min: {consumeItem.min_quantity})
              </Text>

              <View style={{ gap: 10, marginTop: 14 }}>
                <View>
                  <Text style={styles.inputLabel}>
                    Quantity Consumed ({consumeItem.unit})
                  </Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    value={consumeQuantity}
                    onChangeText={setConsumeQuantity}
                    placeholder="e.g., 5"
                  />
                  {parseInt(consumeQuantity, 10) > consumeItem.current_quantity && (
                    <Text style={{ fontSize: 11, color: theme.danger, marginTop: 4 }}>
                      ⚠️ Cannot consume more than {consumeItem.current_quantity} {consumeItem.unit} available.
                    </Text>
                  )}
                  {parseInt(consumeQuantity, 10) > 0 &&
                    consumeItem.current_quantity - parseInt(consumeQuantity, 10) <= consumeItem.min_quantity &&
                    consumeItem.current_quantity - parseInt(consumeQuantity, 10) >= 0 && (
                      <Text style={{ fontSize: 11, color: "#D97706", marginTop: 4 }}>
                        ⚠️ Low stock threshold will be reached! Remaining:{" "}
                        {consumeItem.current_quantity - parseInt(consumeQuantity, 10)} {consumeItem.unit}
                      </Text>
                    )}
                </View>

                <View>
                  <Text style={styles.inputLabel}>Purpose / Classroom Context</Text>
                  <TextInput
                    style={[styles.input, { height: 70, textAlignVertical: "top" }]}
                    placeholder="e.g., Used in practical session..."
                    placeholderTextColor={theme.inkFaint}
                    multiline={true}
                    value={consumeReason}
                    onChangeText={setConsumeReason}
                  />
                </View>

                <View style={{ flexDirection: "row", gap: 10, marginTop: 12 }}>
                  <Pressable
                    onPress={() => setConsumeItem(null)}
                    style={[styles.actionBtn, { backgroundColor: theme.ground }]}
                  >
                    <Text style={{ color: theme.inkSoft, fontWeight: "600" }}>Cancel</Text>
                  </Pressable>
                  <Pressable
                    onPress={handleConfirmConsume}
                    disabled={
                      consumeMutation.isPending ||
                      !consumeQuantity ||
                      parseInt(consumeQuantity, 10) <= 0 ||
                      parseInt(consumeQuantity, 10) > consumeItem.current_quantity
                    }
                    style={[
                      styles.actionBtn,
                      {
                        backgroundColor:
                          consumeMutation.isPending ||
                          !consumeQuantity ||
                          parseInt(consumeQuantity, 10) <= 0 ||
                          parseInt(consumeQuantity, 10) > consumeItem.current_quantity
                            ? theme.inkFaint
                            : theme.primary,
                        flex: 2,
                      },
                    ]}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700" }}>
                      {consumeMutation.isPending ? "Updating..." : "Confirm Consumption"}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>
        </Modal>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  searchInput: {
    backgroundColor: theme.ground,
    borderColor: theme.rule,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    color: theme.ink,
    marginTop: 8,
  },
  categoryPill: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 16,
    backgroundColor: theme.ground,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  categoryPillActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  categoryPillText: {
    fontSize: 12,
    color: theme.inkSoft,
    fontWeight: "500",
  },
  categoryPillTextActive: {
    color: "#fff",
    fontWeight: "600",
  },
  itemFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: theme.rule,
  },
  consumeBtn: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: theme.primary,
  },
  consumeBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#fff",
  },
  flagBtn: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: `${theme.primary}15`,
  },
  flagBtnUrgent: {
    backgroundColor: `${theme.danger}15`,
  },
  flagBtnText: {
    fontSize: 11,
    fontWeight: "600",
    color: theme.primary,
  },
  flagBtnTextUrgent: {
    color: theme.danger,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 20,
  },
  modalContent: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: theme.ink,
  },
  modalSubtitle: {
    fontSize: 13,
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
  urgencyOption: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: theme.rule,
    alignItems: "center",
    backgroundColor: theme.ground,
  },
  urgencyOptionActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  urgencyText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.inkSoft,
  },
  urgencyTextActive: {
    color: "#fff",
  },
  actionBtn: {
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    flex: 1,
  },
});
