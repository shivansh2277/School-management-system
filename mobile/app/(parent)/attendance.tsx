import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { statusColor, theme } from "../../src/theme";

type AttendanceMonth = {
  days: { date: string; status: string }[];
  summary: { present: number; absent: number; leave: number; percent: number | null };
};

type LeaveRequest = {
  id: number;
  from_date: string;
  to_date: string;
  type: string;
  reason: string;
  status: string;
};

const STATUS_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  present: { bg: "#ECFDF5", text: "#059669", label: "P" },
  absent: { bg: "#FFF1F2", text: "#E11D48", label: "A" },
  late: { bg: "#FFFBEB", text: "#D97706", label: "L" },
  leave: { bg: "#F5F3FF", text: "#7C3AED", label: "M" },
  half_day: { bg: "#FFFBEB", text: "#D97706", label: "H" },
};

export default function ParentAttendance() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { selectedChildId, me, selectChild } = useAuth();
  const children = me?.children ?? [];
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const year = now.getFullYear();
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    from_date: new Date().toISOString().slice(0, 10),
    to_date: new Date().toISOString().slice(0, 10),
    type: "sick",
    reason: "",
  });
  const [note, setNote] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["attendance-parent", selectedChildId, month, year],
    queryFn: () =>
      api.get<AttendanceMonth>(`/parent/children/${selectedChildId}/attendance?month=${month}&year=${year}`),
    enabled: selectedChildId !== null,
  });

  const leaveRequests = useQuery({
    queryKey: ["parent-leave-requests", selectedChildId],
    queryFn: () =>
      api.get<LeaveRequest[]>(`/parent/leave-requests?student_id=${selectedChildId}`),
    enabled: selectedChildId !== null,
  });

  const applyLeave = useMutation({
    mutationFn: () =>
      api.post("/parent/leave", {
        student_id: selectedChildId,
        from_date: leaveForm.from_date,
        to_date: leaveForm.to_date,
        type: leaveForm.type,
        reason: leaveForm.reason,
      }),
    onSuccess: () => {
      setShowLeaveModal(false);
      setLeaveForm({
        from_date: new Date().toISOString().slice(0, 10),
        to_date: new Date().toISOString().slice(0, 10),
        type: "sick",
        reason: "",
      });
      setNote("Leave application submitted successfully.");
      qc.invalidateQueries({ queryKey: ["parent-leave-requests", selectedChildId] });
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (!selectedChildId || isLoading) return <Loading />;

  const byDay = new Map((data?.days ?? []).map((d) => [Number(d.date.slice(8, 10)), d.status]));
  const daysInMonth = new Date(year, month, 0).getDate();
  const percent = data?.summary.percent ?? null;
  const isShortage = percent !== null && percent < 75;

  return (
    <Screen>
      {/* Child Selector */}
      {children.length > 1 && (
        <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          {children.map((c) => (
            <Pressable
              key={c.id}
              onPress={() => selectChild(c.id)}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: theme.radius.pill,
                backgroundColor: selectedChildId === c.id ? theme.primary : theme.surface,
              }}
            >
              <Text style={{ color: selectedChildId === c.id ? "#fff" : theme.inkSoft, fontSize: 13 }}>
                {c.name}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* Shortage Alert Banner */}
      {isShortage && (
        <View
          style={{
            backgroundColor: "#FEF2F2",
            borderLeftWidth: 4,
            borderLeftColor: theme.danger,
            padding: 12,
            borderRadius: theme.radius.input,
            marginBottom: 12,
          }}
        >
          <Text style={{ fontSize: 13, fontWeight: "700", color: theme.danger }}>
            ⚠️ {t("att_shortage_alert")}: {percent}%
          </Text>
          <Text style={{ fontSize: 12, color: theme.ink, marginTop: 2 }}>
            {t("att_cbSE_norm")}
          </Text>
        </View>
      )}

      {/* Summary Card */}
      {data && (
        <Card title={t("att_monthly_summary")}>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#059669", textTransform: "uppercase" }}>{t("status_present")}</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#059669", marginTop: 2 }}>{data.summary.present}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#E11D48", textTransform: "uppercase" }}>{t("status_absent")}</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#E11D48", marginTop: 2 }}>{data.summary.absent}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: "#7C3AED", textTransform: "uppercase" }}>{t("status_leave")}</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: "#7C3AED", marginTop: 2 }}>{data.summary.leave}</Text>
            </View>
            <View style={{ width: 1, height: 28, backgroundColor: theme.rule }} />
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkFaint, textTransform: "uppercase" }}>{t("att_overall")}</Text>
              <Text style={{ fontSize: 20, fontWeight: "800", color: isShortage ? theme.danger : theme.success, marginTop: 2 }}>
                {percent === null ? "-" : `${percent}%`}
              </Text>
            </View>
          </View>
        </Card>
      )}

      {/* Calendar Card */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <Pressable
            onPress={() => setMonth((m) => (m === 1 ? 12 : m - 1))}
            style={{
              paddingHorizontal: 10,
              paddingVertical: 6,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Text style={{ color: theme.primary, fontWeight: "700", fontSize: 12 }}>← {t("att_prev_month")}</Text>
          </Pressable>
          <Text style={{ fontWeight: "800", fontSize: 15, color: theme.ink }}>
            {new Date(year, month - 1).toLocaleString("en", { month: "long" })} {year}
          </Text>
          <Pressable
            onPress={() => setMonth((m) => (m === 12 ? 1 : m + 1))}
            style={{
              paddingHorizontal: 10,
              paddingVertical: 6,
              borderRadius: theme.radius.pill,
              backgroundColor: theme.ground,
            }}
          >
            <Text style={{ color: theme.primary, fontWeight: "700", fontSize: 12 }}>{t("att_next_month")} →</Text>
          </Pressable>
        </View>

        {byDay.size === 0 ? (
          <Empty text={t("att_no_records")} />
        ) : (
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((d) => {
              const status = byDay.get(d);
              const conf = status ? STATUS_COLORS[status] : null;
              return (
                <View
                  key={d}
                  style={{
                    width: 38,
                    height: 42,
                    borderRadius: theme.radius.input,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: conf ? conf.bg : theme.ground,
                    borderWidth: 1,
                    borderColor: conf ? conf.text : theme.rule,
                  }}
                >
                  <Text style={{ fontSize: 12, color: theme.ink, fontWeight: "700" }}>{d}</Text>
                  {conf ? (
                    <Text style={{ fontSize: 9, color: conf.text, fontWeight: "800", marginTop: 1 }}>{conf.label}</Text>
                  ) : null}
                </View>
              );
            })}
          </View>
        )}

        {/* Legend */}
        <View style={{ flexDirection: "row", gap: 12, marginTop: 14, paddingTop: 10, borderTopWidth: 1, borderTopColor: theme.rule, flexWrap: "wrap" }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#059669" }} />
            <Text style={{ fontSize: 11, color: "#059669", fontWeight: "600" }}>{t("att_legend_present")}</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#E11D48" }} />
            <Text style={{ fontSize: 11, color: "#E11D48", fontWeight: "600" }}>{t("att_legend_absent")}</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#D97706" }} />
            <Text style={{ fontSize: 11, color: "#D97706", fontWeight: "600" }}>{t("att_legend_late")}</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#7C3AED" }} />
            <Text style={{ fontSize: 11, color: "#7C3AED", fontWeight: "600" }}>{t("att_legend_leave")}</Text>
          </View>
        </View>
      </Card>

      {/* Apply for Leave Action */}
      <View style={{ marginVertical: 8 }}>
        <Button
          label={showLeaveModal ? t("att_cancel_leave_btn") : t("att_apply_leave_btn")}
          tone={showLeaveModal ? "ghost" : "primary"}
          onPress={() => setShowLeaveModal(!showLeaveModal)}
        />
      </View>

      {showLeaveModal && (
        <Card title={t("att_apply_leave_title")}>
          <Text style={s.meta}>{t("att_from_date")}</Text>
          <TextInput
            style={s.input}
            value={leaveForm.from_date}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, from_date: v })}
            placeholder="YYYY-MM-DD"
          />

          <Text style={s.meta}>{t("att_to_date")}</Text>
          <TextInput
            style={s.input}
            value={leaveForm.to_date}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, to_date: v })}
            placeholder="YYYY-MM-DD"
          />

          <Text style={s.meta}>{t("att_leave_type")}</Text>
          <View style={{ flexDirection: "row", gap: 8, marginBottom: 8 }}>
            {[
              { key: "sick", label: t("att_sick") },
              { key: "casual", label: t("att_casual") },
              { key: "medical", label: t("att_medical") },
            ].map(({ key, label }) => (
              <Pressable
                key={key}
                onPress={() => setLeaveForm({ ...leaveForm, type: key })}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: theme.radius.pill,
                  backgroundColor: leaveForm.type === key ? theme.primary : theme.ground,
                }}
              >
                <Text style={{ fontSize: 12, color: leaveForm.type === key ? "#fff" : theme.inkSoft, textTransform: "capitalize" }}>
                  {label}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text style={s.meta}>{t("att_reason_for_absence")}</Text>
          <TextInput
            style={[s.input, { minHeight: 60, textAlignVertical: "top" }]}
            multiline
            value={leaveForm.reason}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, reason: v })}
            placeholder={t("att_reason_placeholder")}
          />

          {note ? <Text style={{ color: theme.danger, marginBottom: 8 }}>{note}</Text> : null}

          <Button
            label={applyLeave.isPending ? t("att_submitting") : t("att_submit_application")}
            onPress={() => applyLeave.mutate()}
            disabled={applyLeave.isPending || leaveForm.reason.length < 3}
          />
        </Card>
      )}

      {/* Leave History */}
      {(leaveRequests.data ?? []).length > 0 && (
        <Card title={t("att_recent_leaves")}>
          {leaveRequests.data!.map((req) => (
            <Row
              key={req.id}
              left={
                <>
                  <Text style={s.title}>
                    {formatDate(req.from_date)} to {formatDate(req.to_date)} ({req.type})
                  </Text>
                  <Text style={s.meta}>{req.reason}</Text>
                </>
              }
              right={
                <Pill
                  status={req.status === "approved" ? "paid" : req.status === "rejected" ? "absent" : "pending"}
                  label={req.status}
                />
              }
            />
          ))}
        </Card>
      )}
    </Screen>
  );
}
