import AsyncStorage from "@react-native-async-storage/async-storage";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Button, Card, Empty, Loading, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

const OFFLINE_QUEUE_KEY = "@offline_attendance_queue";

interface QueuedAttendance {
  id: string;
  class_section_id: number;
  date: string;
  entries: { student_id: number; status: string }[];
  queued_at: string;
}

type ClassRow = { class_section_id: number; class_label: string; is_class_teacher?: boolean };
type Roll = {
  student_id: number;
  full_name: string;
  roll_no: number;
  status: string | null;
};

const STATUS_CHIPS = [
  { key: "present", badge: "P", label: "Present", color: "#059669", bg: "#ECFDF5", activeBg: "#059669" },
  { key: "absent", badge: "A", label: "Absent", color: "#E11D48", bg: "#FFF1F2", activeBg: "#E11D48" },
  { key: "late", badge: "L", label: "Late", color: "#D97706", bg: "#FFFBEB", activeBg: "#D97706" },
  { key: "leave", badge: "M", label: "Medical", color: "#7C3AED", bg: "#F5F3FF", activeBg: "#7C3AED" },
] as const;

type Status = (typeof STATUS_CHIPS)[number]["key"];

export default function TeacherAttendance() {
  const qc = useQueryClient();
  const today = new Date().toISOString().slice(0, 10);
  const [date] = useState(today);
  const [classId, setClassId] = useState<number | null>(null);
  const [marks, setMarks] = useState<Record<number, Status>>({});
  const [note, setNote] = useState<string | null>(null);
  const [offlinePendingCount, setOfflinePendingCount] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  const classes = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => api.get<ClassRow[]>("/teacher/classes"),
  });

  const classTeacherSections = (classes.data ?? []).filter((c) => c.is_class_teacher);
  const active = classId ?? classTeacherSections[0]?.class_section_id ?? null;

  const roll = useQuery({
    queryKey: ["teacher-roll", active, date],
    queryFn: () => api.get<Roll[]>(`/teacher/attendance?class_section_id=${active}&date=${date}`),
    enabled: active !== null,
  });

  // Re-opening a date that is already marked pre-fills the sheet.
  useEffect(() => {
    if (!roll.data) return;
    const next: Record<number, Status> = {};
    for (const r of roll.data) if (r.status) next[r.student_id] = r.status as Status;
    setMarks(next);
    setNote(null);
  }, [roll.data]);

  // Read current offline queue length
  const refreshQueueCount = async () => {
    try {
      const raw = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
      if (raw) {
        const queue: QueuedAttendance[] = JSON.parse(raw);
        setOfflinePendingCount(queue.length);
      } else {
        setOfflinePendingCount(0);
      }
    } catch {
      setOfflinePendingCount(0);
    }
  };

  // Automatically drain queued roll-calls to the backend
  const drainOfflineQueue = async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    try {
      const raw = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
      if (!raw) {
        setIsSyncing(false);
        return;
      }
      const queue: QueuedAttendance[] = JSON.parse(raw);
      if (queue.length === 0) {
        setIsSyncing(false);
        return;
      }

      const remaining: QueuedAttendance[] = [];
      let syncedCount = 0;

      for (const item of queue) {
        try {
          await api.post("/teacher/attendance", {
            class_section_id: item.class_section_id,
            date: item.date,
            entries: item.entries,
            idempotency_key: item.id,
          });
          syncedCount++;
        } catch {
          // Keep item in queue if request fails / network unavailable
          remaining.push(item);
        }
      }

      await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
      setOfflinePendingCount(remaining.length);

      if (syncedCount > 0) {
        setNote(`Attendance synced with server (${syncedCount} synced).`);
        qc.invalidateQueries({ queryKey: ["teacher-roll"] });
      }
    } catch {
      // Ignore background sync errors
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    refreshQueueCount();
    drainOfflineQueue();

    // Reconnection check every 15 seconds
    const interval = setInterval(() => {
      drainOfflineQueue();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const save = useMutation({
    mutationFn: async () => {
      if (!active) throw new Error("No active class selected");
      const payload = {
        class_section_id: active,
        date,
        entries: (roll.data ?? []).map((r) => ({
          student_id: r.student_id,
          status: marks[r.student_id] ?? "present",
        })),
      };

      try {
        const res = await api.post("/teacher/attendance", payload);
        return { online: true, res };
      } catch {
        // Enqueue offline if network times out or fails
        const queueItem: QueuedAttendance = {
          id: `offline-${active}-${date}-${Date.now()}`,
          class_section_id: active,
          date,
          entries: payload.entries,
          queued_at: new Date().toISOString(),
        };

        const raw = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
        const queue: QueuedAttendance[] = raw ? JSON.parse(raw) : [];
        const filtered = queue.filter(
          (q) => !(q.class_section_id === active && q.date === date)
        );
        filtered.push(queueItem);
        await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(filtered));
        setOfflinePendingCount(filtered.length);
        return { online: false, queued: queueItem };
      }
    },
    onSuccess: (data) => {
      if (data.online) {
        setNote("Attendance saved.");
        qc.invalidateQueries({ queryKey: ["teacher-roll"] });
      } else {
        setNote("Saved Locally (Offline - Will Sync When Connected)");
      }
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (classes.isLoading) return <Loading />;

  // Counter computations
  const total = (roll.data ?? []).length;
  const counts = {
    present: 0,
    absent: 0,
    late: 0,
    leave: 0,
  };
  for (const r of roll.data ?? []) {
    const st = marks[r.student_id];
    if (st && st in counts) counts[st as keyof typeof counts]++;
  }

  return (
    <Screen>
      {classTeacherSections.length === 0 ? (
        <Card>
          <Empty text="You are not currently assigned as a Class Teacher for any section. Daily attendance registration is reserved for designated class teachers." />
        </Card>
      ) : (
        <>
          <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
            {classTeacherSections.map((c) => {
              const isSelected = active === c.class_section_id;
              return (
                <Pressable
                  key={c.class_section_id}
                  onPress={() => setClassId(c.class_section_id)}
                  style={{
                    paddingHorizontal: 16,
                    paddingVertical: 10,
                    borderRadius: theme.radius.pill,
                    backgroundColor: isSelected ? theme.primary : theme.surface,
                    borderWidth: 1,
                    borderColor: isSelected ? theme.primary : theme.ruleStrong,
                    ...theme.shadow,
                  }}
                >
                  <Text
                    style={{
                      color: isSelected ? "#fff" : theme.ink,
                      fontWeight: isSelected ? "700" : "500",
                      fontSize: 13,
                    }}
                  >
                    {c.class_label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {offlinePendingCount > 0 && (
            <View
              style={{
                backgroundColor: theme.warningBg,
                borderColor: "#FDE68A",
                borderWidth: 1,
                borderRadius: theme.radius.card,
                padding: 12,
                marginBottom: 12,
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={{ color: "#92400E", fontSize: 13, fontWeight: "700" }}>
                  Saved Locally (Offline - Will Sync When Connected)
                </Text>
                <Text style={{ color: "#B45309", fontSize: 11, marginTop: 2 }}>
                  {offlinePendingCount} pending roll-call(s) queued
                </Text>
              </View>
              <Pressable
                onPress={() => drainOfflineQueue()}
                disabled={isSyncing}
                style={{
                  backgroundColor: theme.warning,
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: theme.radius.pill,
                  opacity: isSyncing ? 0.6 : 1,
                }}
              >
                <Text style={{ color: "#fff", fontSize: 12, fontWeight: "600" }}>
                  {isSyncing ? "Syncing..." : "Sync Now"}
                </Text>
              </Pressable>
            </View>
          )}

          <Card title={`Roll Sheet - ${formatDate(date)}`}>
            {(roll.data ?? []).length === 0 ? (
              <Empty text="No students in this section." />
            ) : (
              <>
                {/* Counter Metric Header */}
                <View
                  style={{
                    flexDirection: "row",
                    backgroundColor: theme.ground,
                    padding: 12,
                    borderRadius: theme.radius.card,
                    marginBottom: 14,
                    borderWidth: 1,
                    borderColor: theme.rule,
                  }}
                >
                  <View style={{ flex: 1, alignItems: "center" }}>
                    <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkFaint, textTransform: "uppercase" }}>Total</Text>
                    <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink, marginTop: 2 }}>{total}</Text>
                  </View>
                  <View style={{ width: 1, backgroundColor: theme.rule }} />
                  <View style={{ flex: 1, alignItems: "center" }}>
                    <Text style={{ fontSize: 11, fontWeight: "600", color: theme.success, textTransform: "uppercase" }}>Present</Text>
                    <Text style={{ fontSize: 18, fontWeight: "800", color: theme.success, marginTop: 2 }}>{counts.present}</Text>
                  </View>
                  <View style={{ width: 1, backgroundColor: theme.rule }} />
                  <View style={{ flex: 1, alignItems: "center" }}>
                    <Text style={{ fontSize: 11, fontWeight: "600", color: theme.danger, textTransform: "uppercase" }}>Absent</Text>
                    <Text style={{ fontSize: 18, fontWeight: "800", color: theme.danger, marginTop: 2 }}>{counts.absent}</Text>
                  </View>
                  <View style={{ width: 1, backgroundColor: theme.rule }} />
                  <View style={{ flex: 1, alignItems: "center" }}>
                    <Text style={{ fontSize: 11, fontWeight: "600", color: theme.warning, textTransform: "uppercase" }}>Late</Text>
                    <Text style={{ fontSize: 18, fontWeight: "800", color: theme.warning, marginTop: 2 }}>{counts.late}</Text>
                  </View>
                </View>

                <View style={{ marginBottom: 12 }}>
                  <Button
                    label="✓ Mark All Present"
                    tone="ghost"
                    onPress={() =>
                      setMarks(
                        Object.fromEntries(roll.data!.map((r) => [r.student_id, "present" as Status])),
                      )
                    }
                  />
                </View>

                {roll.data!.map((r) => {
                  const currentStatus = marks[r.student_id];
                  const initials = r.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase();

                  return (
                    <View
                      key={r.student_id}
                      style={{
                        paddingVertical: 12,
                        borderBottomWidth: 1,
                        borderBottomColor: theme.rule,
                      }}
                    >
                      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                        <View style={{ flexDirection: "row", alignItems: "center", gap: 10, flex: 1 }}>
                          <View
                            style={{
                              width: 36,
                              height: 36,
                              borderRadius: 18,
                              backgroundColor: theme.primarySoft,
                              alignItems: "center",
                              justifyContent: "center",
                              borderWidth: 1,
                              borderColor: theme.rule,
                            }}
                          >
                            <Text style={{ fontSize: 13, fontWeight: "700", color: theme.primary }}>{initials}</Text>
                          </View>
                          <View style={{ flex: 1 }}>
                            <Text style={[s.title, { fontSize: 14, color: theme.ink }]} numberOfLines={1}>
                              {r.full_name}
                            </Text>
                            <Text style={[s.meta, { fontSize: 11, color: theme.inkFaint }]}>Roll No. #{r.roll_no}</Text>
                          </View>
                        </View>
                        {currentStatus && (
                          <View
                            style={{
                              paddingHorizontal: 8,
                              paddingVertical: 3,
                              borderRadius: theme.radius.pill,
                              backgroundColor: STATUS_CHIPS.find((c) => c.key === currentStatus)?.bg,
                            }}
                          >
                            <Text
                              style={{
                                fontSize: 11,
                                fontWeight: "700",
                                textTransform: "capitalize",
                                color: STATUS_CHIPS.find((c) => c.key === currentStatus)?.color,
                              }}
                            >
                              {STATUS_CHIPS.find((c) => c.key === currentStatus)?.label}
                            </Text>
                          </View>
                        )}
                      </View>

                      {/* 4 Status Pills */}
                      <View style={{ flexDirection: "row", gap: 6 }}>
                        {STATUS_CHIPS.map((chip) => {
                          const on = (marks[r.student_id] ?? null) === chip.key;
                          return (
                            <Pressable
                              key={chip.key}
                              onPress={() => setMarks({ ...marks, [r.student_id]: chip.key })}
                              style={{
                                flex: 1,
                                paddingVertical: 8,
                                borderRadius: theme.radius.input,
                                alignItems: "center",
                                justifyContent: "center",
                                backgroundColor: on ? chip.activeBg : theme.ground,
                                borderWidth: 1,
                                borderColor: on ? chip.activeBg : theme.ruleStrong,
                              }}
                            >
                              <Text
                                style={{
                                  fontSize: 13,
                                  color: on ? "#ffffff" : theme.ink,
                                  fontWeight: on ? "800" : "600",
                                }}
                              >
                                {chip.badge}
                              </Text>
                              <Text
                                style={{
                                  fontSize: 10,
                                  color: on ? "#ffffff" : theme.inkFaint,
                                  fontWeight: on ? "600" : "400",
                                  marginTop: 1,
                                }}
                              >
                                {chip.label}
                              </Text>
                            </Pressable>
                          );
                        })}
                      </View>
                    </View>
                  );
                })}
                {note ? <Text style={[s.meta, { marginTop: 10, color: theme.primary, fontWeight: "600" }]}>{note}</Text> : null}
                <View style={{ marginTop: 16 }}>
                  <Button label="Save Attendance" onPress={() => save.mutate()} disabled={save.isPending} />
                </View>
              </>
            )}
          </Card>
        </>
      )}
    </Screen>
  );
}
