import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useMemo } from "react";
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

const FLAG_REASONS = ["Depleted", "Damaged", "Urgent Reorder"] as const;
const CONSUME_REASONS = ["Practical Session", "Class Activity", "Lab Usage"] as const;

export default function TeacherStock() {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [flagItem, setFlagItem] = useState<StockItem | null>(null);
  const [consumeItem, setConsumeItem] = useState<StockItem | null>(null);

  // Flag Form State
  const [quantity, setQuantity] = useState("1");
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "critical">("normal");
  const [selectedFlagReason, setSelectedFlagReason] = useState<string>("Depleted");
  const [reason, setReason] = useState("");

  // Consume Form State
  const [consumeQuantity, setConsumeQuantity] = useState("1");
  const [selectedConsumeReason, setSelectedConsumeReason] = useState<string>("Practical Session");
  const [consumeReason, setConsumeReason] = useState("");

  const { data: items = [], isLoading } = useQuery({
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
    setSelectedConsumeReason("Practical Session");
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
    const finalReason = consumeReason.trim()
      ? `${selectedConsumeReason}: ${consumeReason.trim()}`
      : selectedConsumeReason;

    consumeMutation.mutate({
      itemId: consumeItem.id,
      quantity: qty,
      reason: finalReason,
    });
  };

  const handleOpenFlag = (item: StockItem) => {
    setFlagItem(item);
    setQuantity("2");
    setSelectedFlagReason(item.is_low_stock ? "Depleted" : "Urgent Reorder");
    setReason("");
    setUrgency(item.is_low_stock ? "urgent" : "normal");
  };

  const handleSubmitFlag = () => {
    if (!flagItem) return;
    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("Invalid Quantity", "Please enter a valid positive number.");
      return;
    }
    const finalReason = reason.trim()
      ? `${selectedFlagReason}: ${reason.trim()}`
      : selectedFlagReason;

    flagMutation.mutate({
      item_id: flagItem.id,
      item_name: flagItem.name,
      category: flagItem.category,
      location: flagItem.location,
      quantity_requested: qty,
      urgency,
      reason: finalReason,
      flag_type: "diminishing",
    });
  };

  // Stepper handlers
  const adjustFlagQty = (delta: number) => {
    const cur = parseInt(quantity, 10) || 1;
    const next = Math.max(1, cur + delta);
    setQuantity(String(next));
  };

  const adjustConsumeQty = (delta: number) => {
    if (!consumeItem) return;
    const cur = parseInt(consumeQuantity, 10) || 1;
    const next = Math.max(1, Math.min(consumeItem.current_quantity, cur + delta));
    setConsumeQuantity(String(next));
  };

  if (isLoading) return <Loading />;

  return (
    <Screen>
      {/* Stitch Hero Info & Search Card */}
      <View style={styles.heroCard}>
        <View style={styles.heroTitleRow}>
          <View style={styles.heroIconBox}>
            <Ionicons name="cube-outline" size={18} color={theme.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={styles.heroTitle}>Classroom & Lab Supplies</Text>
              <View style={styles.storeErpBadge}>
                <Text style={styles.storeErpText}>Store ERP</Text>
              </View>
            </View>
          </View>
        </View>

        <Text style={styles.heroDesc}>
          Check availability of lab chemicals, glassware, art materials, and stationery. Flag depleting
          items to notify the admin store.
        </Text>

        {/* Search Bar Input */}
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={16} color="#94A3B8" style={{ marginRight: 8 }} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search items or location..."
            value={search}
            onChangeText={setSearch}
            placeholderTextColor="#94A3B8"
          />
          {search ? (
            <Pressable onPress={() => setSearch("")} hitSlop={8}>
              <Ionicons name="close-circle" size={16} color="#94A3B8" />
            </Pressable>
          ) : null}
        </View>

        {/* Horizontal Scrollable Category Filter Pills */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 4 }}>
          <View style={{ flexDirection: "row", gap: 6, paddingVertical: 2 }}>
            {categories.map((c) => {
              const active = selectedCategory === c;
              return (
                <Pressable
                  key={c}
                  onPress={() => setSelectedCategory(c)}
                  style={[styles.categoryPill, active && styles.categoryPillActive]}
                >
                  <Text style={[styles.categoryPillText, active && styles.categoryPillTextActive]}>
                    {c === "all" ? "All Supplies" : c}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </ScrollView>
      </View>

      {/* Supplies Inventory List */}
      <View style={{ gap: 12, marginTop: 4, paddingBottom: 24 }}>
        {filtered.length === 0 ? (
          <View style={styles.emptyCard}>
            <Empty text="No supplies match your search criteria." />
          </View>
        ) : (
          filtered.map((item) => {
            const isLow = item.current_quantity <= item.min_quantity;
            return (
              <View key={item.id} style={styles.itemCard}>
                {/* Header & Status Badge */}
                <View style={styles.itemHeaderRow}>
                  <View style={{ flex: 1, paddingRight: 8 }}>
                    <Text style={styles.itemName}>{item.name}</Text>
                    <View style={styles.itemMetaRow}>
                      <Text style={styles.itemMetaText}>{item.category}</Text>
                      <View style={styles.metaDot} />
                      <Text style={styles.itemMetaLocation}>{item.location}</Text>
                    </View>
                  </View>

                  {/* Stitch Status Badge */}
                  <View style={isLow ? styles.statusBadgeLow : styles.statusBadgeNormal}>
                    <View style={isLow ? styles.badgeDotLow : styles.badgeDotNormal} />
                    <Text style={isLow ? styles.statusTextLow : styles.statusTextNormal}>
                      {isLow ? "Low Stock" : "In Stock"}
                    </Text>
                  </View>
                </View>

                {/* Divider */}
                <View style={styles.itemDivider} />

                {/* Footer & Actions */}
                <View style={styles.itemFooterRow}>
                  <View>
                    <Text style={styles.minText}>
                      Min: <Text style={styles.minVal}>{item.min_quantity} {item.unit}</Text>
                    </Text>
                    <Text style={styles.qtyText}>
                      <Text style={styles.qtyBold}>{item.current_quantity}</Text> {item.unit} left
                    </Text>
                  </View>

                  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                    <Pressable
                      onPress={() => handleOpenConsume(item)}
                      disabled={item.current_quantity <= 0}
                      style={[
                        styles.consumeBtn,
                        item.current_quantity <= 0 && { opacity: 0.4 },
                      ]}
                    >
                      <Text style={styles.consumeBtnText}>Use / Consume</Text>
                    </Pressable>

                    <Pressable
                      onPress={() => handleOpenFlag(item)}
                      style={[styles.flagBtn, isLow ? styles.flagBtnLow : styles.flagBtnNormal]}
                    >
                      <Text style={[styles.flagBtnText, isLow ? styles.flagBtnTextLow : styles.flagBtnTextNormal]}>
                        Flag →
                      </Text>
                    </Pressable>
                  </View>
                </View>
              </View>
            );
          })
        )}
      </View>

      {/* Redesigned Stitch Bottom Sheet Modal: Flag Stock */}
      {flagItem && (
        <Modal visible={true} transparent={true} animationType="fade">
          <View style={styles.modalBackdrop}>
            <Pressable style={styles.modalDismissArea} onPress={() => setFlagItem(null)} />
            <View style={styles.bottomSheetContainer}>
              {/* Sheet Drag Handle */}
              <View style={styles.sheetHandle} />

              {/* Modal Header */}
              <View style={styles.sheetHeader}>
                <View style={{ flex: 1 }}>
                  <View style={styles.modalBadge}>
                    <View style={styles.modalBadgeDot} />
                    <Text style={styles.modalBadgeText}>Flag Depleted Item</Text>
                  </View>
                  <Text style={styles.sheetTitle}>{flagItem.name}</Text>
                  <Text style={styles.sheetSubtitle}>
                    Currently Available: {flagItem.current_quantity} {flagItem.unit} (Min: {flagItem.min_quantity})
                  </Text>
                </View>
                <Pressable
                  onPress={() => setFlagItem(null)}
                  style={styles.sheetCloseBtn}
                  hitSlop={8}
                >
                  <Ionicons name="close" size={18} color="#64748B" />
                </Pressable>
              </View>

              {/* Stepper Quantity Selector */}
              <View style={styles.stepperContainer}>
                <View>
                  <Text style={styles.stepperLabel}>Quantity to Deduct / Restock</Text>
                  <Text style={styles.stepperSublabel}>Specify count needed today</Text>
                </View>
                <View style={styles.stepperControl}>
                  <Pressable
                    style={styles.stepperBtn}
                    onPress={() => adjustFlagQty(-1)}
                  >
                    <Text style={styles.stepperBtnText}>−</Text>
                  </Pressable>
                  <Text style={styles.stepperValue}>{quantity}</Text>
                  <Pressable
                    style={[styles.stepperBtn, styles.stepperBtnPrimary]}
                    onPress={() => adjustFlagQty(1)}
                  >
                    <Text style={styles.stepperBtnPrimaryText}>+</Text>
                  </Pressable>
                </View>
              </View>

              {/* Quick Reason Selector */}
              <View style={{ gap: 6 }}>
                <Text style={styles.fieldLabel}>Flag Reason</Text>
                <View style={styles.reasonsGrid}>
                  {FLAG_REASONS.map((r) => {
                    const active = selectedFlagReason === r;
                    return (
                      <Pressable
                        key={r}
                        onPress={() => setSelectedFlagReason(r)}
                        style={[styles.reasonPill, active && styles.reasonPillActive]}
                      >
                        <Text style={[styles.reasonPillText, active && styles.reasonPillTextActive]}>
                          {r}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>

              {/* Urgency Level Selector */}
              <View style={{ gap: 6 }}>
                <Text style={styles.fieldLabel}>Urgency Level</Text>
                <View style={{ flexDirection: "row", gap: 6 }}>
                  {(["normal", "urgent", "critical"] as const).map((u) => {
                    const active = urgency === u;
                    return (
                      <Pressable
                        key={u}
                        onPress={() => setUrgency(u)}
                        style={[styles.urgencyPill, active && styles.urgencyPillActive]}
                      >
                        <Text style={[styles.urgencyPillText, active && styles.urgencyPillTextActive]}>
                          {u.toUpperCase()}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>

              {/* Remarks Textarea */}
              <View style={{ gap: 6 }}>
                <Text style={styles.fieldLabel}>Teacher Remarks & Context</Text>
                <TextInput
                  style={styles.sheetTextarea}
                  placeholder="e.g., Practical exam batches start on Monday..."
                  placeholderTextColor="#94A3B8"
                  multiline={true}
                  numberOfLines={2}
                  value={reason}
                  onChangeText={setReason}
                />
              </View>

              {/* Actions */}
              <View style={styles.sheetActionRow}>
                <Pressable
                  style={styles.sheetCancelBtn}
                  onPress={() => setFlagItem(null)}
                >
                  <Text style={styles.sheetCancelText}>Cancel</Text>
                </Pressable>
                <Pressable
                  style={[styles.sheetSubmitBtn, flagMutation.isPending && { opacity: 0.6 }]}
                  onPress={handleSubmitFlag}
                  disabled={flagMutation.isPending}
                >
                  <Text style={styles.sheetSubmitText}>
                    {flagMutation.isPending ? "Submitting..." : "Submit Flag"}
                  </Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
      )}

      {/* Redesigned Stitch Bottom Sheet Modal: Consume Stock */}
      {consumeItem && (
        <Modal visible={true} transparent={true} animationType="fade">
          <View style={styles.modalBackdrop}>
            <Pressable style={styles.modalDismissArea} onPress={() => setConsumeItem(null)} />
            <View style={styles.bottomSheetContainer}>
              {/* Sheet Drag Handle */}
              <View style={styles.sheetHandle} />

              {/* Modal Header */}
              <View style={styles.sheetHeader}>
                <View style={{ flex: 1 }}>
                  <View style={[styles.modalBadge, { backgroundColor: "#ECFDF5", borderColor: "#A7F3D0" }]}>
                    <View style={[styles.modalBadgeDot, { backgroundColor: "#059669" }]} />
                    <Text style={[styles.modalBadgeText, { color: "#059669" }]}>Consume Supply</Text>
                  </View>
                  <Text style={styles.sheetTitle}>{consumeItem.name}</Text>
                  <Text style={styles.sheetSubtitle}>
                    Available in store: {consumeItem.current_quantity} {consumeItem.unit} (Min: {consumeItem.min_quantity})
                  </Text>
                </View>
                <Pressable
                  onPress={() => setConsumeItem(null)}
                  style={styles.sheetCloseBtn}
                  hitSlop={8}
                >
                  <Ionicons name="close" size={18} color="#64748B" />
                </Pressable>
              </View>

              {/* Stepper Quantity Selector */}
              <View style={styles.stepperContainer}>
                <View>
                  <Text style={styles.stepperLabel}>Quantity to Deduct / Consume</Text>
                  <Text style={styles.stepperSublabel}>Max available: {consumeItem.current_quantity} {consumeItem.unit}</Text>
                </View>
                <View style={styles.stepperControl}>
                  <Pressable
                    style={styles.stepperBtn}
                    onPress={() => adjustConsumeQty(-1)}
                  >
                    <Text style={styles.stepperBtnText}>−</Text>
                  </Pressable>
                  <Text style={styles.stepperValue}>{consumeQuantity}</Text>
                  <Pressable
                    style={[styles.stepperBtn, styles.stepperBtnPrimary]}
                    onPress={() => adjustConsumeQty(1)}
                  >
                    <Text style={styles.stepperBtnPrimaryText}>+</Text>
                  </Pressable>
                </View>
              </View>

              {/* Warning if stock will deplete below threshold */}
              {parseInt(consumeQuantity, 10) > 0 &&
                consumeItem.current_quantity - parseInt(consumeQuantity, 10) <= consumeItem.min_quantity && (
                  <View style={styles.warningBanner}>
                    <Ionicons name="warning-outline" size={16} color="#D97706" style={{ marginTop: 1 }} />
                    <Text style={styles.warningText}>
                      Low stock threshold will be reached! Remaining:{" "}
                      {consumeItem.current_quantity - parseInt(consumeQuantity, 10)} {consumeItem.unit}
                    </Text>
                  </View>
                )}

              {/* Quick Reason Selector */}
              <View style={{ gap: 6 }}>
                <Text style={styles.fieldLabel}>Consumption Purpose</Text>
                <View style={styles.reasonsGrid}>
                  {CONSUME_REASONS.map((r) => {
                    const active = selectedConsumeReason === r;
                    return (
                      <Pressable
                        key={r}
                        onPress={() => setSelectedConsumeReason(r)}
                        style={[styles.reasonPill, active && styles.reasonPillActive]}
                      >
                        <Text style={[styles.reasonPillText, active && styles.reasonPillTextActive]}>
                          {r}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>

              {/* Remarks Textarea */}
              <View style={{ gap: 6 }}>
                <Text style={styles.fieldLabel}>Teacher Remarks & Destination</Text>
                <TextInput
                  style={styles.sheetTextarea}
                  placeholder="e.g., Practical exam batches for Grade 10-A..."
                  placeholderTextColor="#94A3B8"
                  multiline={true}
                  numberOfLines={2}
                  value={consumeReason}
                  onChangeText={setConsumeReason}
                />
              </View>

              {/* Actions */}
              <View style={styles.sheetActionRow}>
                <Pressable
                  style={styles.sheetCancelBtn}
                  onPress={() => setConsumeItem(null)}
                >
                  <Text style={styles.sheetCancelText}>Cancel</Text>
                </Pressable>
                <Pressable
                  style={[
                    styles.sheetSubmitBtn,
                    (consumeMutation.isPending || parseInt(consumeQuantity, 10) <= 0) && { opacity: 0.6 },
                  ]}
                  onPress={handleConfirmConsume}
                  disabled={consumeMutation.isPending || parseInt(consumeQuantity, 10) <= 0}
                >
                  <Text style={styles.sheetSubmitText}>
                    {consumeMutation.isPending ? "Updating..." : "Confirm Consumption"}
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
  // Hero Card
  heroCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    gap: 10,
    marginBottom: 4,
  },
  heroTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  heroIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: "#EEF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  heroTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0F172A",
    letterSpacing: -0.2,
  },
  storeErpBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
  },
  storeErpText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#4338CA",
  },
  heroDesc: {
    fontSize: 12,
    color: "#64748B",
    lineHeight: 17,
  },
  searchWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F8FAFC",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === "ios" ? 8 : 4,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: "#0F172A",
    padding: 0,
  },
  categoryPill: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 16,
    backgroundColor: "#F1F5F9",
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  categoryPillActive: {
    backgroundColor: "#4338CA",
    borderColor: "#4338CA",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  categoryPillText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#475569",
  },
  categoryPillTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },

  // Item Card
  itemCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  itemHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  itemName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
    lineHeight: 20,
  },
  itemMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 3,
  },
  itemMetaText: {
    fontSize: 12,
    color: "#64748B",
    fontWeight: "500",
  },
  metaDot: {
    width: 3.5,
    height: 3.5,
    borderRadius: 2,
    backgroundColor: "#CBD5E1",
  },
  itemMetaLocation: {
    fontSize: 12,
    color: "#475569",
    fontWeight: "600",
  },
  statusBadgeLow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: "#FFF1F2",
    borderWidth: 1,
    borderColor: "#FECDD3",
  },
  statusBadgeNormal: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: "#ECFDF5",
    borderWidth: 1,
    borderColor: "#A7F3D0",
  },
  badgeDotLow: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#E11D48",
  },
  badgeDotNormal: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#059669",
  },
  statusTextLow: {
    fontSize: 11,
    fontWeight: "700",
    color: "#E11D48",
  },
  statusTextNormal: {
    fontSize: 11,
    fontWeight: "700",
    color: "#059669",
  },
  itemDivider: {
    height: 1,
    backgroundColor: "#F1F5F9",
    marginVertical: 12,
  },
  itemFooterRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  minText: {
    fontSize: 11,
    color: "#64748B",
  },
  minVal: {
    fontWeight: "700",
    color: "#334155",
  },
  qtyText: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  qtyBold: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0F172A",
  },
  consumeBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: "#4338CA",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 1,
  },
  consumeBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  flagBtn: {
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },
  flagBtnLow: {
    backgroundColor: "#FFF1F2",
    borderColor: "#FECDD3",
  },
  flagBtnNormal: {
    backgroundColor: "#F8FAFC",
    borderColor: "#E2E8F0",
  },
  flagBtnText: {
    fontSize: 11,
    fontWeight: "700",
  },
  flagBtnTextLow: {
    color: "#E11D48",
  },
  flagBtnTextNormal: {
    color: "#475569",
  },
  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },

  // Modal / Bottom Sheet
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(15, 23, 42, 0.55)",
    justifyContent: "flex-end",
  },
  modalDismissArea: {
    flex: 1,
  },
  bottomSheetContainer: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: Platform.OS === "ios" ? 34 : 20,
    borderTopWidth: 1,
    borderTopColor: "#EEF2F6",
    gap: 14,
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  sheetHandle: {
    width: 44,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#E2E8F0",
    alignSelf: "center",
    marginBottom: 4,
  },
  sheetHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  modalBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
    alignSelf: "flex-start",
    marginBottom: 4,
  },
  modalBadgeDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#4338CA",
  },
  modalBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#4338CA",
  },
  sheetTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: "#0F172A",
    letterSpacing: -0.2,
  },
  sheetSubtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 2,
  },
  sheetCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#F1F5F9",
    alignItems: "center",
    justifyContent: "center",
  },
  stepperContainer: {
    backgroundColor: "#F8FAFC",
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  stepperLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#334155",
  },
  stepperSublabel: {
    fontSize: 10,
    color: "#94A3B8",
    marginTop: 1,
  },
  stepperControl: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    padding: 2,
    gap: 4,
  },
  stepperBtn: {
    width: 28,
    height: 28,
    borderRadius: 6,
    backgroundColor: "#F1F5F9",
    alignItems: "center",
    justifyContent: "center",
  },
  stepperBtnPrimary: {
    backgroundColor: "#4338CA",
  },
  stepperBtnText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#334155",
  },
  stepperBtnPrimaryText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  stepperValue: {
    minWidth: 26,
    textAlign: "center",
    fontSize: 14,
    fontWeight: "800",
    color: "#0F172A",
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#475569",
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  reasonsGrid: {
    flexDirection: "row",
    gap: 6,
  },
  reasonPill: {
    flex: 1,
    paddingVertical: 7,
    paddingHorizontal: 4,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
  },
  reasonPillActive: {
    backgroundColor: "#EEF2FF",
    borderColor: "#4338CA",
  },
  reasonPillText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#64748B",
    textAlign: "center",
  },
  reasonPillTextActive: {
    color: "#4338CA",
    fontWeight: "700",
  },
  urgencyPill: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    backgroundColor: "#F8FAFC",
    alignItems: "center",
  },
  urgencyPillActive: {
    backgroundColor: "#4338CA",
    borderColor: "#4338CA",
  },
  urgencyPillText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#64748B",
  },
  urgencyPillTextActive: {
    color: "#FFFFFF",
  },
  sheetTextarea: {
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 12,
    backgroundColor: "#F8FAFC",
    padding: 10,
    fontSize: 12,
    color: "#0F172A",
    textAlignVertical: "top",
    minHeight: 56,
  },
  warningBanner: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    backgroundColor: "#FFFBEB",
    borderWidth: 1,
    borderColor: "#FDE68A",
    borderRadius: 10,
    padding: 8,
  },
  warningText: {
    flex: 1,
    fontSize: 11,
    color: "#B45309",
    lineHeight: 15,
  },
  sheetActionRow: {
    flexDirection: "row",
    gap: 10,
    marginTop: 4,
  },
  sheetCancelBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#F1F5F9",
    alignItems: "center",
    justifyContent: "center",
  },
  sheetCancelText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#475569",
  },
  sheetSubmitBtn: {
    flex: 2,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#4338CA",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  sheetSubmitText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
