import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
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
  present: { bg: "#DCFCE7", text: "#16A34A", label: "P" },
  absent: { bg: "#FEE2E2", text: "#EF4444", label: "A" },
  late: { bg: "#FEF3C7", text: "#F59E0B", label: "L" },
  leave: { bg: "#EDE9FE", text: "#8B5CF6", label: "M" },
  half_day: { bg: "#FEF3C7", text: "#D97706", label: "H" },
};

export default function ParentAttendance() {
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
            ⚠️ Attendance Shortage Alert: {percent}%
          </Text>
          <Text style={{ fontSize: 12, color: theme.ink, marginTop: 2 }}>
            CBSE norms mandate a minimum of 75% attendance to be eligible for terminal examinations.
          </Text>
        </View>
      )}

      {/* Calendar Card */}
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <Pressable onPress={() => setMonth((m) => (m === 1 ? 12 : m - 1))}>
            <Text style={{ color: theme.primary, fontWeight: "600" }}>‹ Previous</Text>
          </Pressable>
          <Text style={{ fontWeight: "700", fontSize: 15, color: theme.ink }}>
            {new Date(year, month - 1).toLocaleString("en", { month: "long" })} {year}
          </Text>
          <Pressable onPress={() => setMonth((m) => (m === 12 ? 1 : m + 1))}>
            <Text style={{ color: theme.primary, fontWeight: "600" }}>Next ›</Text>
          </Pressable>
        </View>

        {byDay.size === 0 ? (
          <Empty text="No attendance recorded for this month." />
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
                    borderRadius: 8,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: conf ? conf.bg : theme.ground,
                    borderWidth: 1,
                    borderColor: conf ? conf.text : "transparent",
                  }}
                >
                  <Text style={{ fontSize: 12, color: theme.ink, fontWeight: "600" }}>{d}</Text>
                  {conf ? (
                    <Text style={{ fontSize: 10, color: conf.text, fontWeight: "700" }}>{conf.label}</Text>
                  ) : null}
                </View>
              );
            })}
          </View>
        )}

        {/* Legend */}
        <View style={{ flexDirection: "row", gap: 12, marginTop: 12, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.rule }}>
          <Text style={{ fontSize: 11, color: "#16A34A" }}>● Present (P)</Text>
          <Text style={{ fontSize: 11, color: "#EF4444" }}>● Absent (A)</Text>
          <Text style={{ fontSize: 11, color: "#F59E0B" }}>● Late (L)</Text>
          <Text style={{ fontSize: 11, color: "#8B5CF6" }}>● Medical (M)</Text>
        </View>
      </Card>

      {/* Summary Card */}
      {data && (
        <Card title="Monthly Summary">
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={s.meta}>Present</Text>
              <Text style={{ fontSize: 18, fontWeight: "700", color: "#16A34A" }}>{data.summary.present}</Text>
            </View>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={s.meta}>Absent</Text>
              <Text style={{ fontSize: 18, fontWeight: "700", color: "#EF4444" }}>{data.summary.absent}</Text>
            </View>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={s.meta}>Leave</Text>
              <Text style={{ fontSize: 18, fontWeight: "700", color: "#8B5CF6" }}>{data.summary.leave}</Text>
            </View>
            <View style={{ alignItems: "center", flex: 1 }}>
              <Text style={s.meta}>Overall</Text>
              <Text style={{ fontSize: 18, fontWeight: "700", color: isShortage ? theme.danger : theme.ink }}>
                {percent === null ? "-" : `${percent}%`}
              </Text>
            </View>
          </View>
        </Card>
      )}

      {/* Apply for Leave Action */}
      <View style={{ marginVertical: 8 }}>
        <Button
          label={showLeaveModal ? "Cancel Leave Application" : "+ Apply for Student Leave"}
          tone={showLeaveModal ? "ghost" : "primary"}
          onPress={() => setShowLeaveModal(!showLeaveModal)}
        />
      </View>

      {showLeaveModal && (
        <Card title="Apply for Leave">
          <Text style={s.meta}>From Date (YYYY-MM-DD)</Text>
          <TextInput
            style={s.input}
            value={leaveForm.from_date}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, from_date: v })}
            placeholder="YYYY-MM-DD"
          />

          <Text style={s.meta}>To Date (YYYY-MM-DD)</Text>
          <TextInput
            style={s.input}
            value={leaveForm.to_date}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, to_date: v })}
            placeholder="YYYY-MM-DD"
          />

          <Text style={s.meta}>Leave Type</Text>
          <View style={{ flexDirection: "row", gap: 8, marginBottom: 8 }}>
            {["sick", "casual", "medical"].map((t) => (
              <Pressable
                key={t}
                onPress={() => setLeaveForm({ ...leaveForm, type: t })}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: theme.radius.pill,
                  backgroundColor: leaveForm.type === t ? theme.primary : theme.ground,
                }}
              >
                <Text style={{ fontSize: 12, color: leaveForm.type === t ? "#fff" : theme.inkSoft, textTransform: "capitalize" }}>
                  {t}
                </Text>
              </Pressable>
            ))}
          </View>

          <Text style={s.meta}>Reason for Absence</Text>
          <TextInput
            style={[s.input, { minHeight: 60, textAlignVertical: "top" }]}
            multiline
            value={leaveForm.reason}
            onChangeText={(v) => setLeaveForm({ ...leaveForm, reason: v })}
            placeholder="Detailed reason for absence..."
          />

          {note ? <Text style={{ color: theme.danger, marginBottom: 8 }}>{note}</Text> : null}

          <Button
            label={applyLeave.isPending ? "Submitting..." : "Submit Application"}
            onPress={() => applyLeave.mutate()}
            disabled={applyLeave.isPending || leaveForm.reason.length < 3}
          />
        </Card>
      )}

      {/* Leave History */}
      {(leaveRequests.data ?? []).length > 0 && (
        <Card title="Recent Leave Applications">
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
