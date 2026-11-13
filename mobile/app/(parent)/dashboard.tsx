import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, Text, View } from "react-native";

import { api, money } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { AlertItem, ImportantAlerts } from "../../src/components/ImportantAlerts";
import { Card, Empty, Loading, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

type Summary = {
  name: string;
  class_label: string;
  attendance_percent: number | null;
  homework_submitted: number;
  homework_pending: number;
  latest_result_percent: number | null;
  fee_dues: number;
  fee_due_amount?: number;
  latest_report_card?: { exam_id: number; title: string } | null;
  latest_periodic_test?: { exam_id: number; title: string } | null;
  alerts?: AlertItem[];
  recent_notices: { id: number; title: string; published_at: string }[];
};

export default function ParentDashboard() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { selectedChildId, selectChild, me } = useAuth();
  const { t } = useTranslation();

  const { data, isLoading } = useQuery({
    queryKey: ["parent-summary", selectedChildId],
    queryFn: () => api.get<Summary>(`/parent/children/${selectedChildId}/summary`),
    enabled: selectedChildId !== null,
  });

  const feesSummaryQuery = useQuery({
    queryKey: ["parent-fees-summary", selectedChildId],
    queryFn: () =>
      api.get<{
        total_invoiced: number;
        total_paid: number;
        total_dues: number;
        balance: number;
      }>(`/parent/children/${selectedChildId}/fees/summary`),
    enabled: selectedChildId !== null,
  });

  const alertsQuery = useQuery({
    queryKey: ["parent-alerts"],
    queryFn: () => api.get<AlertItem[]>("/parent/alerts"),
  });

  if (isLoading || !data) return <Loading />;

  const handleAlertPress = async (alert: AlertItem) => {
    if (alert.child_id) {
      selectChild(alert.child_id);
    }
    // Attendance, report card, and periodic test alerts disappear after viewing.
    // Fee alerts NEVER dismiss by viewing (must remain visible until balance is 0).
    // Multi-child: tracked per child and per alert independently.
    if (alert.type !== "fee" && alert.event_key && alert.child_id) {
      try {
        await api.post("/parent/alerts/view", {
          child_id: alert.child_id,
          alert_type: alert.type,
          event_key: alert.event_key,
          exam_id: alert.exam_id,
        });
        queryClient.invalidateQueries({ queryKey: ["parent-alerts"] });
        queryClient.invalidateQueries({ queryKey: ["parent-summary"] });
      } catch (err) {
        console.warn("Failed to mark alert viewed:", err);
      }
    }
    if (alert.route) {
      router.push(alert.route as any);
    }
  };

  const initials = (data.name || "Student")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  // True monetary outstanding balance:
  // Prefer /fees/summary balance, then total_dues, then summary fee_due_amount.
  // Never fallback to raw fee_dues integer count as currency.
  const feeAmount =
    feesSummaryQuery.data?.balance ??
    feesSummaryQuery.data?.total_dues ??
    data.fee_due_amount ??
    0;
  const overdueInvoiceCount = data.fee_dues ?? 0;
  const hasFeeDue = feeAmount > 0 || overdueInvoiceCount > 0;
  const attPct = data.attendance_percent;
  const attColor = attPct === null ? theme.ink : attPct >= 75 ? theme.success : theme.danger;

  // Consolidate backend alerts with context-aware critical alerts
  const consolidatedAlerts: AlertItem[] = [...(alertsQuery.data || data.alerts || [])];

  // Outstanding fee alert (CRITICAL: never dismiss until balance is paid)
  if (hasFeeDue && !consolidatedAlerts.some((a) => a.type === "fee")) {
    consolidatedAlerts.unshift({
      id: `fee-due-${selectedChildId}`,
      child_id: selectedChildId ?? undefined,
      type: "fee",
      title: "Fee Payment Pending",
      message: `Pending fee balance of ${money(feeAmount)}${
        overdueInvoiceCount > 0
          ? ` across ${overdueInvoiceCount} overdue invoice${overdueInvoiceCount > 1 ? "s" : ""}`
          : ""
      }. Tap to pay via Direct UPI.`,
      route: "/(parent)/fees",
      amount: feeAmount,
      severity: "danger",
    });
  }

  // Attendance shortage alert if < 75%
  if (
    attPct !== null &&
    attPct < 75 &&
    !consolidatedAlerts.some((a) => a.type === "attendance")
  ) {
    consolidatedAlerts.push({
      id: `att-shortage-${selectedChildId}`,
      child_id: selectedChildId ?? undefined,
      type: "attendance",
      title: "Low Attendance Warning",
      message: `Current attendance is ${attPct}%, which falls below the mandatory 75% CBSE requirement.`,
      route: "/(parent)/attendance",
      severity: "warning",
    });
  }

  return (
    <Screen>
      {/* Child Profile Hero Card */}
      <Card>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
            <View
              style={{
                width: 48,
                height: 48,
                borderRadius: 24,
                backgroundColor: theme.primarySoft,
                alignItems: "center",
                justifyContent: "center",
                borderWidth: 2,
                borderColor: theme.primary,
              }}
            >
              <Text style={{ fontSize: 18, fontWeight: "800", color: theme.primary }}>{initials}</Text>
            </View>
            <View>
              <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink }}>{data.name}</Text>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4 }}>
                <View
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                    borderRadius: theme.radius.pill,
                    backgroundColor: theme.primarySoft,
                  }}
                >
                  <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                    {t("child_class")} {data.class_label}
                  </Text>
                </View>
                <View
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                    borderRadius: theme.radius.pill,
                    backgroundColor: theme.ground,
                    borderWidth: 1,
                    borderColor: theme.rule,
                  }}
                >
                  <Text style={{ fontSize: 11, fontWeight: "600", color: theme.success }}>
                    ● Enrolled
                  </Text>
                </View>
              </View>
            </View>
          </View>

          <Pressable
            onPress={() => router.push("/(parent)/child" as any)}
            style={{
              padding: 8,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Ionicons name="chevron-forward" size={18} color={theme.inkFaint} />
          </Pressable>
        </View>
      </Card>

      {/* Outstanding Fees Alert Banner (if dues present) */}
      {hasFeeDue && (
        <Pressable onPress={() => router.push("/(parent)/fees" as any)}>
          <View
            style={{
              backgroundColor: theme.warningBg,
              borderRadius: theme.radius.card,
              padding: 14,
              borderWidth: 1,
              borderColor: "#FDE68A",
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "space-between",
              ...theme.shadow,
            }}
          >
            <View style={{ flexDirection: "row", alignItems: "center", gap: 10, flex: 1 }}>
              <View
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 19,
                  backgroundColor: "#FEF3C7",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Ionicons name="warning" size={20} color={theme.warning} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 13, fontWeight: "700", color: "#92400E" }}>
                  Outstanding Fees Due
                </Text>
                <Text style={{ fontSize: 11, color: "#B45309", marginTop: 1 }}>
                  Pending balance: {money(feeAmount)}
                  {overdueInvoiceCount > 0 ? ` (${overdueInvoiceCount} invoice${overdueInvoiceCount > 1 ? "s" : ""})` : ""}
                </Text>
              </View>
            </View>
            <View
              style={{
                backgroundColor: theme.warning,
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: theme.radius.pill,
              }}
            >
              <Text style={{ fontSize: 11, fontWeight: "700", color: "#fff" }}>Pay Now →</Text>
            </View>
          </View>
        </Pressable>
      )}

      {/* 3 Key Metrics Cards */}
      <View style={{ flexDirection: "row", gap: 8 }}>
        {/* Attendance */}
        <Pressable
          onPress={() => router.push("/(parent)/attendance" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            {t("nav_attendance")}
          </Text>
          <Text style={{ fontSize: 20, fontWeight: "800", color: attColor, marginTop: 4 }}>
            {attPct === null ? "-" : `${attPct}%`}
          </Text>
          <Text style={{ fontSize: 10, color: attColor, fontWeight: "600", marginTop: 2 }}>
            {attPct === null ? "No data" : attPct >= 75 ? "Above 75%" : "Shortage (<75%)"}
          </Text>
        </Pressable>

        {/* Academic Score */}
        <Pressable
          onPress={() => router.push("/(parent)/results" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            {t("nav_results")}
          </Text>
          <Text style={{ fontSize: 20, fontWeight: "800", color: theme.primary, marginTop: 4 }}>
            {data.latest_result_percent === null ? "-" : `${data.latest_result_percent}%`}
          </Text>
          <Text style={{ fontSize: 10, color: theme.inkFaint, marginTop: 2 }}>Latest Exam</Text>
        </Pressable>

        {/* Homework */}
        <Pressable
          onPress={() => router.push("/(parent)/homework" as any)}
          style={{
            flex: 1,
            backgroundColor: theme.surface,
            borderRadius: theme.radius.card,
            padding: 12,
            borderWidth: 1,
            borderColor: theme.rule,
            ...theme.shadow,
          }}
        >
          <Text style={{ fontSize: 11, fontWeight: "700", color: theme.inkFaint, textTransform: "uppercase" }}>
            {t("nav_homework")}
          </Text>
          <Text
            style={{
              fontSize: 20,
              fontWeight: "800",
              color: data.homework_pending > 0 ? theme.warning : theme.success,
              marginTop: 4,
            }}
          >
            {data.homework_pending}
          </Text>
          <Text style={{ fontSize: 10, color: theme.inkFaint, marginTop: 2 }}>Pending</Text>
        </Pressable>
      </View>

      {/* Quick Actions Shortcuts */}
      <Card title="Quick Services">
        <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 8 }}>
          {[
            { label: "Pay Fees", icon: "card-outline" as const, color: "#4338CA", route: "/(parent)/fees" },
            { label: "Attendance", icon: "checkbox-outline" as const, color: "#059669", route: "/(parent)/attendance" },
            { label: "Timetable", icon: "calendar-outline" as const, color: "#0284C7", route: "/(parent)/timetable" },
            { label: "Results", icon: "school-outline" as const, color: "#7C3AED", route: "/(parent)/results" },
          ].map((action) => (
            <Pressable
              key={action.label}
              onPress={() => router.push(action.route as any)}
              style={{
                flex: 1,
                alignItems: "center",
                paddingVertical: 10,
                borderRadius: theme.radius.input,
                backgroundColor: theme.ground,
              }}
            >
              <View
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 18,
                  backgroundColor: `${action.color}15`,
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 6,
                }}
              >
                <Ionicons name={action.icon} size={18} color={action.color} />
              </View>
              <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft, textAlign: "center" }}>
                {action.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </Card>

      {/* Important Alerts */}
      <ImportantAlerts
        alerts={consolidatedAlerts}
        onAlertPress={handleAlertPress}
        sectionTitle={t("dash_important_alerts")}
      />

      {/* Recent Notices */}
      <Card title={t("dash_recent_notices")}>
        {data.recent_notices.length === 0 ? (
          <Empty text={t("dash_no_notices")} />
        ) : (
          data.recent_notices.map((n) => (
            <Row
              key={n.id}
              left={
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={[s.title, { fontSize: 13, color: theme.ink }]}>{n.title}</Text>
                  <Text style={[s.meta, { fontSize: 11 }]}>{new Date(n.published_at).toLocaleDateString()}</Text>
                </View>
              }
              right={<Ionicons name="chevron-forward" size={16} color={theme.inkFaint} />}
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
