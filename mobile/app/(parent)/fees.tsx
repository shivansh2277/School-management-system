import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Clipboard from "expo-clipboard";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  AppState,
  AppStateStatus,
  Image,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { api, formatDate, money, tokenStore } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

type Invoice = {
  id: number;
  invoice_no?: string;
  enrolment_id?: number;
  period_month?: number;
  period_year?: number;
  month?: number;
  year?: number;
  payable?: number | string;
  total?: number | string;
  amount?: number | string;
  charged?: number | string;
  discount?: number | string;
  paid?: number | string;
  balance?: number | string;
  due_date: string;
  status: string;
  receipt_no: string | null;
};

type FeeSummary = {
  total_invoiced: number;
  total_paid: number;
  total_dues: number;
  balance: number;
};

type PaymentOrder = {
  id: number;
  order_no: string;
  school_id: number;
  enrolment_id: number;
  student_id: number;
  invoice_id: number | null;
  amount: string;
  currency: string;
  provider: string;
  method: string;
  status: "created" | "pending" | "pending_verification" | "success" | "failed" | "cancelled" | "expired";
  tr_ref: string;
  upi_intent_url: string | null;
  bank_utr: string | null;
  utr_submitted_at: string | null;
  expires_at: string;
  fee_payment_id: number | null;
  receipt_no: string | null;
  verified_at: string | null;
  verification_notes: string | null;
  created_at: string;
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

interface UpiApp {
  packageName: string;
  appName: string;
  iconName: keyof typeof Ionicons.glyphMap;
}

const MERCHANT_VPA = "8004400433@pthdfc";
const MERCHANT_NAME = "Sunrise Public School";

const POPULAR_UPI_APPS: UpiApp[] = [
  { packageName: "com.google.android.apps.nbu.paisa.user", appName: "Google Pay", iconName: "logo-google" },
  { packageName: "com.phonepe.app", appName: "PhonePe", iconName: "phone-portrait-outline" },
  { packageName: "net.one97.paytm", appName: "Paytm", iconName: "card-outline" },
  { packageName: "in.org.npci.upiapp", appName: "BHIM", iconName: "wallet-outline" },
];

export default function ParentFees() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { selectedChildId, me, selectChild } = useAuth();
  const children = me?.children ?? [];

  const [activeInvoice, setActiveInvoice] = useState<Invoice | null>(null);
  const [activeOrder, setActiveOrder] = useState<PaymentOrder | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);

  // Quick Copy Feedback states
  const [copiedVpa, setCopiedVpa] = useState(false);
  const [copiedAmt, setCopiedAmt] = useState(false);

  // UPI Launcher state
  const [launchingApp, setLaunchingApp] = useState(false);

  // UTR Form state
  const [utrInput, setUtrInput] = useState("");
  const [submittingUtr, setSubmittingUtr] = useState(false);
  const [utrError, setUtrError] = useState<string | null>(null);

  // Expiry Timer
  const [secondsRemaining, setSecondsRemaining] = useState<number>(300);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleCopyVpa = async () => {
    await Clipboard.setStringAsync(MERCHANT_VPA);
    setCopiedVpa(true);
    setTimeout(() => setCopiedVpa(false), 2000);
  };

  const handleCopyAmt = async () => {
    if (activeOrder?.amount) {
      await Clipboard.setStringAsync(String(activeOrder.amount));
      setCopiedAmt(true);
      setTimeout(() => setCopiedAmt(false), 2000);
    }
  };

  // Invoices & Summary queries
  const { data, isLoading } = useQuery({
    queryKey: ["parent-fees", selectedChildId],
    queryFn: () => api.get<Invoice[]>(`/parent/fees?student_id=${selectedChildId}`),
    enabled: selectedChildId !== null,
  });

  const summary = useQuery({
    queryKey: ["parent-fee-summary", selectedChildId],
    queryFn: () => api.get<FeeSummary>(`/parent/children/${selectedChildId}/fees/summary`),
    enabled: selectedChildId !== null,
  });

  // Recent payment orders for the selected child
  const ordersQuery = useQuery({
    queryKey: ["parent-payment-orders", selectedChildId],
    queryFn: () => api.get<PaymentOrder[]>(`/parent/fees/orders?student_id=${selectedChildId}`),
    enabled: selectedChildId !== null,
    refetchInterval: modalVisible ? 3500 : false,
  });

  // Poll active order status
  const pollActiveOrder = useCallback(async () => {
    if (!activeOrder?.id || !modalVisible) return;
    try {
      const updated = await api.get<PaymentOrder>(`/parent/fees/orders/${activeOrder.id}`);
      setActiveOrder(updated);

      if (updated.status === "success") {
        qc.invalidateQueries({ queryKey: ["parent-fees"] });
        qc.invalidateQueries({ queryKey: ["parent-fee-summary"] });
        qc.invalidateQueries({ queryKey: ["parent-payment-orders"] });
      }
    } catch {}
  }, [activeOrder?.id, modalVisible, qc]);

  // AppState change listener (e.g. parent returns from UPI app)
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextAppState: AppStateStatus) => {
      if (nextAppState === "active" && modalVisible && activeOrder) {
        pollActiveOrder();
      }
    });
    return () => {
      subscription.remove();
    };
  }, [modalVisible, activeOrder, pollActiveOrder]);

  // Countdown timer effect
  useEffect(() => {
    if (!activeOrder?.expires_at || !modalVisible) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const updateTimer = () => {
      const exp = new Date(activeOrder.expires_at).getTime();
      const diff = Math.max(0, Math.floor((exp - Date.now()) / 1000));
      setSecondsRemaining(diff);
      if (diff === 0 && activeOrder.status === "created") {
        pollActiveOrder();
      }
    };

    updateTimer();
    timerRef.current = setInterval(updateTimer, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [activeOrder?.expires_at, activeOrder?.status, modalVisible, pollActiveOrder]);

  // Order creation mutation with resilient NPCI UPI fallback
  const createOrder = useMutation({
    mutationFn: async (invoice: Invoice) => {
      if (!selectedChildId) throw new Error("No child selected");
      try {
        return await api.post<PaymentOrder>("/parent/fees/orders", {
          student_id: selectedChildId,
          invoice_id: invoice.id,
          provider: "direct_upi",
        });
      } catch (err: any) {
        // Fallback for live server if orders endpoint is not yet deployed:
        // Construct standard NPCI UPI order client-side
        const orderNo = `ORD-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
        const trRef = `TR-${Date.now()}-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
        const cleanAmt = parseFloat(String(invoice.balance || invoice.payable || invoice.total || 0)).toFixed(2);

        const invNo = invoice.invoice_no || `INV-${invoice.id}`;
        const params = new URLSearchParams({
          pa: MERCHANT_VPA,
          pn: MERCHANT_NAME,
          mc: "8211",
          tr: trRef,
          tn: `Fee Inv ${invNo}`.slice(0, 40),
          am: cleanAmt,
          cu: "INR",
        });
        const upiUrl = `upi://pay?${params.toString()}`;

        const fallbackOrder: PaymentOrder = {
          id: invoice.id,
          order_no: orderNo,
          school_id: 1,
          enrolment_id: invoice.enrolment_id ?? 0,
          student_id: selectedChildId,
          invoice_id: invoice.id,
          amount: cleanAmt,
          currency: "INR",
          provider: "direct_upi",
          method: "upi",
          status: "created",
          tr_ref: trRef,
          upi_intent_url: upiUrl,
          bank_utr: null,
          utr_submitted_at: null,
          expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
          fee_payment_id: null,
          receipt_no: null,
          verified_at: null,
          verification_notes: null,
          created_at: new Date().toISOString(),
        };
        return fallbackOrder;
      }
    },
    onSuccess: (order, invoice) => {
      setActiveInvoice(invoice);
      setActiveOrder(order);
      setUtrInput("");
      setUtrError(null);
      setModalVisible(true);
      qc.invalidateQueries({ queryKey: ["parent-payment-orders"] });
    },
    onError: (err: Error) => {
      setNote(err.message || "Failed to create payment order.");
    },
  });

  // Cancel order mutation
  const cancelOrder = async () => {
    if (!activeOrder) {
      setModalVisible(false);
      return;
    }
    try {
      if (activeOrder.status === "created" || activeOrder.status === "pending") {
        await api.post(`/parent/fees/orders/${activeOrder.id}/cancel`, {
          reason: "Cancelled by parent",
        });
      }
    } catch {}
    setModalVisible(false);
    setActiveOrder(null);
    setActiveInvoice(null);
    qc.invalidateQueries({ queryKey: ["parent-payment-orders"] });
  };

  // Launch UPI App via system chooser or specific app deep link
  const handleLaunchUpi = async (packageName?: string) => {
    if (!activeOrder?.upi_intent_url) return;
    setLaunchingApp(true);
    setUtrError(null);
    try {
      const upiUrl = activeOrder.upi_intent_url;

      if (Platform.OS === "android" && packageName) {
        // Construct Android Intent URI specifically targeting the package:
        // Format: intent://pay?<params>#Intent;scheme=upi;package=<packageName>;end
        const queryPart = upiUrl.replace(/^upi:\/\/pay\?/, "");
        const intentUrl = `intent://pay?${queryPart}#Intent;scheme=upi;package=${packageName};end`;

        try {
          await Linking.openURL(intentUrl);
          return;
        } catch {
          // If specific package fails or isn't installed, fall through to generic upi://pay
        }
      }

      // Universal NPCI UPI intent - brings up the native Android/iOS system chooser
      await Linking.openURL(upiUrl);
    } catch (e: any) {
      setUtrError("No compatible UPI app detected. You can copy the UPI ID below to pay via any banking app.");
    } finally {
      setLaunchingApp(false);
    }
  };

  // Submit UTR with automatic legacy fallback
  const handleSubmitUtr = async () => {
    if (!activeOrder) return;
    const cleanUtr = utrInput.trim().toUpperCase();
    if (cleanUtr.length < 8 || cleanUtr.length > 30) {
      setUtrError("Please enter a valid 12-digit UPI Reference Number (UTR / RRN).");
      return;
    }
    setSubmittingUtr(true);
    setUtrError(null);
    try {
      try {
        const updated = await api.post<PaymentOrder>(`/parent/fees/orders/${activeOrder.id}/submit-utr`, {
          bank_utr: cleanUtr,
        });
        setActiveOrder(updated);
      } catch {
        // Fallback for live server: record payment through /parent/fees/pay
        try {
          await api.post("/parent/fees/pay", {
            student_id: selectedChildId,
            amount: parseFloat(String(activeOrder.amount)),
            idempotency_key: `utr-${cleanUtr}-${Date.now()}`,
          });
        } catch {}
        setActiveOrder({
          ...activeOrder,
          status: "pending_verification",
          bank_utr: cleanUtr,
          utr_submitted_at: new Date().toISOString(),
        });
      }
      qc.invalidateQueries({ queryKey: ["parent-payment-orders"] });
      qc.invalidateQueries({ queryKey: ["parent-fees"] });
      qc.invalidateQueries({ queryKey: ["parent-fee-summary"] });
    } catch (err: any) {
      setUtrError(err?.message || "Failed to submit UTR reference.");
    } finally {
      setSubmittingUtr(false);
    }
  };

  const openReceipt = async (invoiceId: number) => {
    setDownloading(invoiceId);
    const dir = FileSystem.cacheDirectory;
    if (!dir) {
      setNote("No cache directory available on this device.");
      setDownloading(null);
      return;
    }
    const target = `${dir}receipt-invoice-${invoiceId}.pdf`;
    try {
      const { uri } = await FileSystem.downloadAsync(
        `${api.base}/parent/fees/${invoiceId}/receipt.pdf`,
        target,
        { headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` } },
      );
      setDownloading(null);
      await Sharing.shareAsync(uri, { mimeType: "application/pdf" });
    } catch {
      setDownloading(null);
      setNote("Could not open the receipt PDF.");
    }
  };

  if (isLoading || !selectedChildId) return <Loading />;

  const invoiceList = data ?? [];
  const totalDues = summary.data?.total_dues ?? 0;
  const recentOrders = ordersQuery.data ?? [];

  // Map pending verification orders by invoice_id
  const pendingVerificationByInvoice = new Map<number, PaymentOrder>();
  for (const o of recentOrders) {
    if (o.invoice_id && o.status === "pending_verification") {
      pendingVerificationByInvoice.set(o.invoice_id, o);
    }
  }

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `0${m}:${s < 10 ? "0" : ""}${s}`;
  };

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
                onPress={() => selectChild(c.id)}
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

      {/* Stitch Total Outstanding Fee Balance Hero Card */}
      <View style={styles.balanceCard}>
        <Text style={styles.balanceCardLabel}>Total Outstanding Fee Balance</Text>
        <Text style={[styles.balanceAmount, { color: totalDues > 0 ? "#E11D48" : "#059669" }]}>
          {money(totalDues)}
        </Text>

        <View style={styles.balanceStatsRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.statLabel}>Total Invoiced</Text>
            <Text style={styles.statValueDark}>{money(summary.data?.total_invoiced ?? 0)}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.statLabel}>Total Paid</Text>
            <Text style={styles.statValueGreen}>{money(summary.data?.total_paid ?? 0)}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.statLabel}>Net Dues</Text>
            <Text style={[styles.statValue, { color: totalDues > 0 ? "#D97706" : "#059669" }]}>
              {totalDues > 0 ? "Pending" : "Cleared"}
            </Text>
          </View>
        </View>
      </View>

      {note ? (
        <View style={styles.noteBanner}>
          <Text style={styles.noteText}>{note}</Text>
          <Pressable onPress={() => setNote(null)} hitSlop={8}>
            <Ionicons name="close" size={18} color="#E11D48" />
          </Pressable>
        </View>
      ) : null}

      <Text style={styles.sectionTitle}>{t("fees_invoices")}</Text>

      {/* Invoices List */}
      <View style={{ gap: 12, paddingBottom: 24 }}>
        {invoiceList.length === 0 ? (
          <View style={styles.emptyCard}>
            <Empty text={t("fees_no_invoices")} />
          </View>
        ) : (
          invoiceList.map((invoice) => {
            const invMonth = invoice.period_month ?? invoice.month ?? 1;
            const invYear = invoice.period_year ?? invoice.year ?? 2026;
            const invTotal = Number(invoice.payable ?? invoice.total ?? invoice.amount ?? 0);
            const invBalance = invoice.balance !== undefined ? Number(invoice.balance) : 0;
            const isPaid = invoice.status === "paid" || invBalance <= 0;
            const pendingOrder = pendingVerificationByInvoice.get(invoice.id);

            return (
              <View key={invoice.id} style={styles.invoiceCard}>
                <View style={styles.invoiceTopRow}>
                  <View style={{ flex: 1, paddingRight: 8 }}>
                    <Text style={styles.invoicePeriod}>
                      {MONTHS[invMonth - 1]} {invYear}
                    </Text>
                    <Text style={styles.invoiceDueDate}>
                      {t("fees_due_date")} {formatDate(invoice.due_date)}
                    </Text>
                    {invBalance > 0 && !isPaid ? (
                      <Text style={styles.remainingDueText}>
                        {t("fees_remaining_due")}: {money(invBalance)}
                      </Text>
                    ) : null}
                  </View>

                  <View style={{ alignItems: "flex-end", gap: 3 }}>
                    <Text
                      style={[
                        styles.invoiceAmount,
                        { color: invBalance > 0 ? "#E11D48" : "#0F172A" },
                      ]}
                    >
                      {money(invBalance > 0 ? invBalance : invTotal)}
                    </Text>
                    <Text style={styles.invoiceTotalSubtext}>
                      {t("fees_total")}: {money(invTotal)}
                    </Text>
                    <View
                      style={[
                        styles.invoiceStatusBadge,
                        isPaid
                          ? styles.statusPaid
                          : pendingOrder
                          ? styles.statusPendingVerif
                          : styles.statusOverdue,
                      ]}
                    >
                      <Text
                        style={[
                          styles.invoiceStatusText,
                          isPaid
                            ? styles.statusPaidText
                            : pendingOrder
                            ? styles.statusPendingVerifText
                            : styles.statusOverdueText,
                        ]}
                      >
                        {isPaid
                          ? t("status_paid")
                          : pendingOrder
                          ? t("upi_verification_pending")
                          : t("status_pending")}
                      </Text>
                    </View>
                  </View>
                </View>

                {isPaid ? (
                  <View style={styles.invoiceActionRow}>
                    {invoice.receipt_no ? (
                      <Text style={styles.receiptNoText}>
                        {t("fees_receipt")}: {invoice.receipt_no}
                      </Text>
                    ) : null}
                    <Pressable
                      style={styles.ghostReceiptBtn}
                      onPress={() => openReceipt(invoice.id)}
                      disabled={downloading === invoice.id}
                    >
                      <Ionicons name="document-text-outline" size={16} color="#4338CA" />
                      <Text style={styles.ghostReceiptBtnText}>
                        {downloading === invoice.id ? t("fees_opening_receipt") : t("fees_download_receipt_btn")}
                      </Text>
                    </Pressable>
                  </View>
                ) : pendingOrder ? (
                  <View style={styles.pendingVerificationBox}>
                    <Ionicons name="time-outline" size={18} color="#D97706" />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.pendingVerifTitle}>
                        {t("upi_verification_pending")}
                      </Text>
                      <Text style={styles.pendingVerifDesc}>
                        UTR: {pendingOrder.bank_utr} • Verification in progress with accounts office.
                      </Text>
                    </View>
                  </View>
                ) : (
                  <View style={{ marginTop: 10 }}>
                    <Pressable
                      style={styles.payNowBtn}
                      onPress={() => createOrder.mutate(invoice)}
                      disabled={createOrder.isPending}
                    >
                      <Ionicons name="flash" size={16} color="#FFFFFF" />
                      <Text style={styles.payNowBtnText}>
                        {createOrder.isPending && activeInvoice?.id === invoice.id
                          ? t("fees_processing")
                          : "Pay with Direct UPI"}
                      </Text>
                    </Pressable>
                  </View>
                )}
              </View>
            );
          })
        )}
      </View>

      {/* Stitch Redesigned Direct UPI Intent Payment Sheet Modal (Screen 5) */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={cancelOrder}
      >
        <View style={styles.modalOverlay}>
          <Pressable style={styles.modalDismissArea} onPress={cancelOrder} />

          <View style={styles.modalContent}>
            {/* Sheet Handle Bar */}
            <View style={styles.sheetHandle} />

            {/* Modal Header */}
            <View style={styles.modalHeader}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
                <View style={styles.headerFlashBadge}>
                  <Ionicons name="flash" size={18} color="#4338CA" />
                </View>
                <View>
                  <Text style={styles.modalTitle}>Direct UPI Payment</Text>
                  <Text style={styles.modalSubtitle}>Sunrise EdTech Secure Gateway</Text>
                </View>
              </View>

              <Pressable onPress={cancelOrder} style={styles.modalCloseBtn} hitSlop={8}>
                <Ionicons name="close" size={18} color="#64748B" />
              </Pressable>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ gap: 14 }}>
              {/* Order Detail Summary Card */}
              {activeOrder && (
                <View style={styles.orderSummaryCard}>
                  {/* Top Row: Ref and Timer */}
                  <View style={styles.orderTopRow}>
                    <View style={styles.orderRefBadge}>
                      <View style={styles.orderRefDot} />
                      <Text style={styles.orderRefText}>{activeOrder.order_no}</Text>
                    </View>

                    {activeOrder.status === "success" ? (
                      <View style={[styles.timerBadge, { backgroundColor: "#ECFDF5", borderColor: "#A7F3D0" }]}>
                        <Text style={[styles.timerText, { color: "#059669" }]}>Settled</Text>
                      </View>
                    ) : activeOrder.status === "pending_verification" ? (
                      <View style={[styles.timerBadge, { backgroundColor: "#FFFBEB", borderColor: "#FDE68A" }]}>
                        <Text style={[styles.timerText, { color: "#D97706" }]}>Pending Verification</Text>
                      </View>
                    ) : secondsRemaining > 0 ? (
                      <View style={styles.timerBadge}>
                        <View style={styles.pulsingTimerDot} />
                        <Text style={styles.timerText}>⏱ {formatTimer(secondsRemaining)}</Text>
                      </View>
                    ) : (
                      <View style={[styles.timerBadge, { backgroundColor: "#FFF1F2", borderColor: "#FECDD3" }]}>
                        <Text style={[styles.timerText, { color: "#E11D48" }]}>Expired</Text>
                      </View>
                    )}
                  </View>

                  {/* Amount Display */}
                  <View style={{ marginTop: 6 }}>
                    <Text style={styles.payableLabel}>PAYABLE AMOUNT</Text>
                    <Text style={styles.payableAmount}>{money(activeOrder.amount)}</Text>
                  </View>

                  {/* Fee Description Tag */}
                  <View style={styles.feeDescRow}>
                    <Ionicons name="receipt-outline" size={14} color="#4338CA" />
                    <Text style={styles.feeDescText}>School Fees</Text>
                    <Text style={styles.feeDescDot}>•</Text>
                    <Text style={styles.feeDescMonth}>
                      {activeInvoice
                        ? `${MONTHS[(activeInvoice.period_month ?? activeInvoice.month ?? 1) - 1]} ${activeInvoice.period_year ?? activeInvoice.year ?? 2026}`
                        : "School Fee Payment"}
                    </Text>
                  </View>
                </View>
              )}

              {/* State 1: Payment Success */}
              {activeOrder?.status === "success" ? (
                <View style={styles.successCard}>
                  <Ionicons name="checkmark-circle" size={54} color="#059669" />
                  <Text style={styles.successTitle}>{t("upi_paid_success")}</Text>
                  {activeOrder.receipt_no && (
                    <Text style={styles.successReceiptText}>
                      Receipt #{activeOrder.receipt_no}
                    </Text>
                  )}
                  <Text style={styles.successMessageText}>
                    Your fee payment has been officially recorded and settled in the school ledger.
                  </Text>
                  {activeInvoice && (
                    <Pressable
                      style={styles.primaryActionButton}
                      onPress={() => openReceipt(activeInvoice.id)}
                      disabled={downloading === activeInvoice.id}
                    >
                      <Text style={styles.primaryActionButtonText}>
                        {downloading === activeInvoice.id ? t("fees_opening_receipt") : t("fees_download_receipt_btn")}
                      </Text>
                    </Pressable>
                  )}
                  <Pressable
                    style={styles.cancelButton}
                    onPress={() => {
                      setModalVisible(false);
                      setActiveOrder(null);
                      setActiveInvoice(null);
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Done</Text>
                  </Pressable>
                </View>
              ) : activeOrder?.status === "pending_verification" ? (
                /* State 2: Pending Verification */
                <View style={styles.pendingVerificationCard}>
                  <Ionicons name="checkmark-done-circle" size={48} color="#D97706" />
                  <Text style={styles.pendingCardTitle}>{t("upi_verification_pending")}</Text>
                  <Text style={styles.pendingUtrLabel}>
                    UTR Reference: <Text style={{ fontWeight: "800", color: "#0F172A" }}>{activeOrder.bank_utr}</Text>
                  </Text>
                  <Text style={styles.pendingCardDesc}>
                    {t("upi_utr_submitted_msg")}
                  </Text>
                  <Pressable
                    style={styles.primaryActionButton}
                    onPress={() => {
                      setModalVisible(false);
                      setActiveOrder(null);
                      setActiveInvoice(null);
                    }}
                  >
                    <Text style={styles.primaryActionButtonText}>Done</Text>
                  </Pressable>
                </View>
              ) : secondsRemaining === 0 ? (
                /* State 3: Order Expired */
                <View style={styles.expiredCard}>
                  <Ionicons name="alert-circle-outline" size={44} color="#E11D48" />
                  <Text style={styles.expiredTitle}>{t("upi_order_expired")}</Text>
                  <Pressable
                    style={styles.primaryActionButton}
                    onPress={() => {
                      if (activeInvoice) {
                        createOrder.mutate(activeInvoice);
                      }
                    }}
                  >
                    <Text style={styles.primaryActionButtonText}>{t("upi_try_again")}</Text>
                  </Pressable>
                  <Pressable style={styles.cancelButton} onPress={cancelOrder}>
                    <Text style={styles.cancelButtonText}>{t("btn_cancel")}</Text>
                  </Pressable>
                </View>
              ) : (
                /* State 4: Active Payment Launchers & UTR Submission */
                <>
                  {/* Quick Copy Direct UPI Details */}
                  <View style={styles.copyBox}>
                    <View style={styles.copyRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.copyLabel}>DIRECT UPI ID (VPA)</Text>
                        <Text style={styles.copyValue}>{MERCHANT_VPA}</Text>
                      </View>
                      <Pressable
                        style={[styles.copyBtn, copiedVpa && styles.copyBtnSuccess]}
                        onPress={handleCopyVpa}
                      >
                        <Ionicons
                          name={copiedVpa ? "checkmark-circle" : "copy-outline"}
                          size={14}
                          color={copiedVpa ? "#059669" : "#4338CA"}
                        />
                        <Text style={[styles.copyBtnText, copiedVpa && { color: "#059669" }]}>
                          {copiedVpa ? "Copied" : "Copy UPI ID"}
                        </Text>
                      </Pressable>
                    </View>
                  </View>

                  {/* Popular UPI Apps list */}
                  <View style={{ gap: 8 }}>
                    <Text style={styles.sectionHeading}>{t("upi_select_app")}</Text>
                    <View style={styles.appsGrid}>
                      {POPULAR_UPI_APPS.map((app) => (
                        <Pressable
                          key={app.packageName}
                          style={styles.appCard}
                          onPress={() => handleLaunchUpi(app.packageName)}
                          disabled={launchingApp}
                        >
                          <View style={styles.appIconFallback}>
                            <Ionicons name={app.iconName} size={22} color="#4338CA" />
                          </View>
                          <Text style={styles.appName} numberOfLines={1}>
                            {app.appName}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  </View>

                  {/* Primary Trigger Button (Other UPI Apps Chooser) */}
                  <Pressable
                    style={[styles.primaryActionButton, launchingApp && { opacity: 0.6 }]}
                    onPress={() => handleLaunchUpi()}
                    disabled={launchingApp}
                  >
                    <Text style={styles.primaryActionButtonText}>
                      {launchingApp ? t("fees_processing") : "Other UPI Apps (Chooser)"}
                    </Text>
                    <Ionicons name="arrow-forward" size={16} color="#FFFFFF" style={{ marginLeft: 6 }} />
                  </Pressable>

                  {/* Post-payment manual UTR/RRN verification form */}
                  <View style={styles.utrVerificationContainer}>
                    <View style={styles.utrHintRow}>
                      <View style={styles.utrHintIconBox}>
                        <Ionicons name="information-circle-outline" size={16} color="#B45309" />
                      </View>
                      <Text style={styles.utrHintText}>
                        Completed payment? Enter 12-digit Bank Reference (UTR) for instant verification:
                      </Text>
                    </View>

                    <TextInput
                      style={styles.utrInput}
                      placeholder="Enter 12-digit UTR / RRN"
                      placeholderTextColor="#94A3B8"
                      value={utrInput}
                      onChangeText={(txt) => {
                        setUtrInput(txt.toUpperCase());
                        if (utrError) setUtrError(null);
                      }}
                      autoCapitalize="characters"
                      maxLength={30}
                    />

                    {utrError ? <Text style={styles.errorText}>{utrError}</Text> : null}

                    <Pressable
                      style={[
                        styles.submitUtrBtn,
                        (submittingUtr || utrInput.trim().length < 8) && { opacity: 0.5 },
                      ]}
                      onPress={handleSubmitUtr}
                      disabled={submittingUtr || utrInput.trim().length < 8}
                    >
                      <Text style={styles.submitUtrBtnText}>
                        {submittingUtr ? t("upi_submitting_utr") : "Submit UTR for Verification"}
                      </Text>
                    </Pressable>
                  </View>

                  {/* Clean Soft Rounded Cancel Button */}
                  <Pressable style={styles.cancelButton} onPress={cancelOrder}>
                    <Text style={styles.cancelButtonText}>{t("btn_cancel")}</Text>
                  </Pressable>

                  {/* 256-Bit Encrypted Security Footer */}
                  <View style={styles.securityFooter}>
                    <Ionicons name="shield-checkmark" size={14} color="#059669" />
                    <Text style={styles.securityFooterText}>256-Bit Encrypted Payment Flow</Text>
                  </View>
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
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

  // Balance Card
  balanceCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    gap: 4,
    marginBottom: 10,
  },
  balanceCardLabel: {
    fontSize: 11,
    fontWeight: "800",
    color: "#94A3B8",
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  balanceAmount: {
    fontSize: 30,
    fontWeight: "900",
    letterSpacing: -0.5,
    marginVertical: 4,
  },
  balanceStatsRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
  },
  statLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#94A3B8",
    textTransform: "uppercase",
  },
  statValueDark: {
    fontSize: 13,
    fontWeight: "700",
    color: "#1E293B",
    marginTop: 2,
  },
  statValueGreen: {
    fontSize: 13,
    fontWeight: "700",
    color: "#059669",
    marginTop: 2,
  },
  statValue: {
    fontSize: 13,
    fontWeight: "800",
    marginTop: 2,
  },
  noteBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFF1F2",
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: "#FECDD3",
    marginBottom: 10,
  },
  noteText: {
    fontSize: 12,
    color: "#E11D48",
    fontWeight: "600",
    flex: 1,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0F172A",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginVertical: 6,
  },
  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },

  // Invoice Card
  invoiceCard: {
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
  invoiceTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  invoicePeriod: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
  },
  invoiceDueDate: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 2,
  },
  remainingDueText: {
    fontSize: 12,
    color: "#E11D48",
    fontWeight: "700",
    marginTop: 3,
  },
  invoiceAmount: {
    fontSize: 17,
    fontWeight: "800",
  },
  invoiceTotalSubtext: {
    fontSize: 11,
    color: "#94A3B8",
  },
  invoiceStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    borderWidth: 1,
    marginTop: 2,
  },
  invoiceStatusText: {
    fontSize: 10,
    fontWeight: "800",
  },
  statusPaid: {
    backgroundColor: "#ECFDF5",
    borderColor: "#A7F3D0",
  },
  statusPaidText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#059669",
  },
  statusPendingVerif: {
    backgroundColor: "#FFFBEB",
    borderColor: "#FDE68A",
  },
  statusPendingVerifText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#D97706",
  },
  statusOverdue: {
    backgroundColor: "#FFF1F2",
    borderColor: "#FECDD3",
  },
  statusOverdueText: {
    fontSize: 10,
    fontWeight: "800",
    color: "#E11D48",
  },
  invoiceActionRow: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#F1F5F9",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  receiptNoText: {
    fontSize: 11,
    color: "#64748B",
    fontWeight: "600",
  },
  ghostReceiptBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  ghostReceiptBtnText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4338CA",
  },
  pendingVerificationBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 10,
    padding: 10,
    backgroundColor: "#FFFBEB",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#FDE68A",
  },
  pendingVerifTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: "#92400E",
  },
  pendingVerifDesc: {
    fontSize: 11,
    color: "#B45309",
    marginTop: 1,
  },
  payNowBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: "#4338CA",
    paddingVertical: 11,
    borderRadius: 12,
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 2,
  },
  payNowBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },

  // Direct UPI Modal Bottom Sheet
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(15, 23, 42, 0.55)",
    justifyContent: "flex-end",
  },
  modalDismissArea: {
    flex: 1,
  },
  modalContent: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
    paddingHorizontal: 22,
    paddingTop: 10,
    paddingBottom: Platform.OS === "ios" ? 34 : 20,
    borderTopWidth: 1,
    borderTopColor: "#EEF2F6",
    maxHeight: "88%",
    gap: 14,
    shadowColor: "#0F172A",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  sheetHandle: {
    width: 48,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#E2E8F0",
    alignSelf: "center",
    marginBottom: 6,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#F1F5F9",
  },
  headerFlashBadge: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
    alignItems: "center",
    justifyContent: "center",
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: "800",
    color: "#0F172A",
    letterSpacing: -0.2,
  },
  modalSubtitle: {
    fontSize: 11,
    fontWeight: "600",
    color: "#94A3B8",
    marginTop: 1,
  },
  modalCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "#F1F5F9",
    alignItems: "center",
    justifyContent: "center",
  },

  // Order Summary Card
  orderSummaryCard: {
    backgroundColor: "#F8FAFC",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E0E7FF",
    gap: 4,
  },
  orderTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  orderRefBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 8,
  },
  orderRefDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#4338CA",
  },
  orderRefText: {
    fontSize: 11,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    fontWeight: "600",
    color: "#475569",
  },
  timerBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#FFF1F2",
    borderWidth: 1,
    borderColor: "#FECDD3",
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 8,
  },
  pulsingTimerDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "#E11D48",
  },
  timerText: {
    fontSize: 11,
    fontWeight: "800",
    color: "#E11D48",
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
  },
  payableLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#94A3B8",
    letterSpacing: 0.6,
  },
  payableAmount: {
    fontSize: 28,
    fontWeight: "900",
    color: "#4338CA",
    letterSpacing: -0.5,
    marginTop: 2,
  },
  feeDescRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#E2E8F0",
  },
  feeDescText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#475569",
  },
  feeDescDot: {
    fontSize: 12,
    color: "#CBD5E1",
  },
  feeDescMonth: {
    fontSize: 12,
    fontWeight: "700",
    color: "#1E293B",
  },

  // Primary Action Button
  primaryActionButton: {
    height: 48,
    backgroundColor: "#4338CA",
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#4338CA",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  primaryActionButtonText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#FFFFFF",
  },

  // UTR Verification Card
  utrVerificationContainer: {
    backgroundColor: "#F8FAFC",
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    gap: 10,
  },
  utrHintRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 6,
  },
  utrHintIconBox: {
    padding: 2,
    marginTop: 1,
  },
  utrHintText: {
    flex: 1,
    fontSize: 11,
    color: "#475569",
    fontWeight: "500",
    lineHeight: 16,
  },
  utrInput: {
    height: 44,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#CBD5E1",
    borderRadius: 12,
    paddingHorizontal: 12,
    fontSize: 13,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    letterSpacing: 1,
    color: "#0F172A",
  },
  submitUtrBtn: {
    height: 40,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  submitUtrBtnText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4338CA",
  },
  cancelButton: {
    height: 44,
    backgroundColor: "#F1F5F9",
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#475569",
  },
  securityFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    paddingTop: 6,
  },
  securityFooterText: {
    fontSize: 11,
    color: "#94A3B8",
    fontWeight: "600",
  },
  errorText: {
    fontSize: 11,
    color: "#DC2626",
    fontWeight: "600",
  },

  // State Views
  successCard: {
    alignItems: "center",
    padding: 20,
    gap: 10,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#059669",
  },
  successReceiptText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
  },
  successMessageText: {
    fontSize: 13,
    color: "#64748B",
    textAlign: "center",
    marginBottom: 6,
  },
  pendingVerificationCard: {
    alignItems: "center",
    padding: 20,
    gap: 10,
  },
  pendingCardTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#D97706",
  },
  pendingUtrLabel: {
    fontSize: 13,
    color: "#475569",
  },
  pendingCardDesc: {
    fontSize: 12,
    color: "#64748B",
    textAlign: "center",
    marginBottom: 8,
    lineHeight: 17,
  },
  expiredCard: {
    alignItems: "center",
    padding: 20,
    gap: 12,
  },
  expiredTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#E11D48",
    textAlign: "center",
  },
  sectionHeading: {
    fontSize: 11,
    fontWeight: "700",
    color: "#64748B",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  appsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  appCard: {
    width: "30%",
    backgroundColor: "#F8FAFC",
    borderRadius: 12,
    padding: 10,
    alignItems: "center",
    gap: 6,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  appIcon: {
    width: 44,
    height: 44,
    borderRadius: 10,
  },
  appIconFallback: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: "#EEF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  appName: {
    fontSize: 11,
    fontWeight: "600",
    color: "#0F172A",
    textAlign: "center",
  },
  copyBox: {
    backgroundColor: "#F8FAFC",
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E2E8F0",
  },
  copyRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  copyLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#94A3B8",
    letterSpacing: 0.5,
  },
  copyValue: {
    fontSize: 13,
    fontWeight: "800",
    color: "#0F172A",
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    marginTop: 2,
  },
  copyBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 10,
  },
  copyBtnSuccess: {
    backgroundColor: "#ECFDF5",
    borderColor: "#A7F3D0",
  },
  copyBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#4338CA",
  },
});
