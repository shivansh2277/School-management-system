import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Empty, Loading, Screen } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Dashboard = {
  today_schedule: {
    period: number;
    time: string;
    class_label: string;
    subject: string;
    room: string | null;
  }[];
  sections: string[];
  pending_marks_entry: number;
  homework_awaiting_submissions: number;
  attendance: { present: number; absent: number; leave: number; percent: number | null } | null;
};

type SubstitutionDuty = {
  id: number;
  date: string;
  period_no: number;
  time: string;
  class_label: string;
  subject: string;
  room: string | null;
  absent_teacher_name: string;
  status: string;
};

function getInitials(name?: string): string {
  if (!name) return "AS";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (name[0] ?? "A").toUpperCase();
}

export default function TeacherDashboard() {
  const router = useRouter();
  const { me } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ["teacher-dashboard"],
    queryFn: () => api.get<Dashboard>("/teacher/dashboard"),
  });

  const { data: duties } = useQuery({
    queryKey: ["teacher-substitution-duties"],
    queryFn: () => api.get<SubstitutionDuty[]>("/teacher/substitutions/duties"),
  });

  const todayStr = new Date().toISOString().slice(0, 10);
  const todayDuties = (duties ?? []).filter((d) => d.date === todayStr);

  if (isLoading || !data) return <Loading />;

  const initials = getInitials(me?.user.full_name);

  return (
    <Screen>
      {/* Teacher Profile Card matching Stitch Screen 24 */}
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
        <View style={styles.profileDetails}>
          <View style={styles.nameRow}>
            <Text style={styles.teacherName} numberOfLines={1}>
              {me?.user.full_name ?? "Faculty Member"}
            </Text>
            <View style={styles.facultyBadge}>
              <Text style={styles.facultyBadgeText}>Faculty</Text>
            </View>
          </View>
          <Text style={styles.schoolLabel}>Sunrise Public School</Text>
          <Text style={styles.sectionSubtitle} numberOfLines={1}>
            <Text style={{ color: theme.primary, fontWeight: "700" }}>{me?.employee_id ?? "TCH"}</Text>
            <Text style={{ color: theme.inkFaint }}> • </Text>
            {data.sections.join(", ") || "No assigned sections"}
          </Text>
        </View>
      </View>

      {/* 3-Column KPI Metrics Grid */}
      <View style={styles.kpiGrid}>
        {/* Metric 1: Marks Pending */}
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>MARKS PENDING</Text>
          <Text style={styles.kpiValue}>{data.pending_marks_entry}</Text>
          <View style={styles.kpiStatusRow}>
            <View
              style={[
                styles.kpiDot,
                {
                  backgroundColor:
                    data.pending_marks_entry === 0 ? theme.successCore : theme.warningCore,
                },
              ]}
            />
            <Text
              style={[
                styles.kpiStatusText,
                {
                  color:
                    data.pending_marks_entry === 0 ? theme.success : theme.warning,
                },
              ]}
            >
              {data.pending_marks_entry === 0 ? "Up to date" : "Needs Entry"}
            </Text>
          </View>
        </View>

        {/* Metric 2: Homework Open */}
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>HOMEWORK OPEN</Text>
          <Text style={[styles.kpiValue, { color: theme.primary }]}>
            {data.homework_awaiting_submissions}
          </Text>
          <View style={styles.kpiStatusRow}>
            <View style={[styles.kpiDot, { backgroundColor: theme.warningCore }]} />
            <Text style={[styles.kpiStatusText, { color: theme.warning }]}>Active</Text>
          </View>
        </View>

        {/* Metric 3: Attendance */}
        <View style={styles.kpiCard}>
          <Text style={styles.kpiLabel}>ATTENDANCE</Text>
          <Text style={styles.kpiValue}>
            {data.attendance?.percent === null || data.attendance === null
              ? "—"
              : `${data.attendance.percent}%`}
          </Text>
          <View style={styles.kpiStatusRow}>
            <View
              style={[
                styles.kpiDot,
                {
                  backgroundColor:
                    data.attendance?.percent ? theme.successCore : theme.inkFaint,
                },
              ]}
            />
            <Text style={styles.kpiStatusText}>
              {data.attendance?.percent ? "Recorded" : "Not marked"}
            </Text>
          </View>
        </View>
      </View>

      {/* Substitution Duties Alert Card */}
      {todayDuties.length > 0 && (
        <View style={styles.dutyCard}>
          <View style={styles.cardHeader}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <View style={styles.warningIconBox}>
                <Ionicons name="calendar" size={16} color={theme.warning} />
              </View>
              <Text style={styles.cardTitle}>
                Today's Substitution Duties ({todayDuties.length})
              </Text>
            </View>
          </View>

          <View style={styles.dutyList}>
            {todayDuties.map((duty) => (
              <View key={duty.id} style={styles.dutyRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.dutyHeading}>
                    Period {duty.period_no} • {duty.subject} ({duty.class_label})
                  </Text>
                  <Text style={styles.dutySub}>
                    Covering for: {duty.absent_teacher_name}
                    {duty.room ? ` • Room ${duty.room}` : ""}
                  </Text>
                </View>
                <Text style={styles.dutyTime}>{duty.time}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Quick Actions Card */}
      <View style={styles.actionCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Quick Actions</Text>
          <Text style={styles.cardSubtitle}>Shortcuts</Text>
        </View>

        <View style={styles.actionButtonsRow}>
          <Pressable
            onPress={() => router.push("/(teacher)/leave")}
            style={({ pressed }) => [
              styles.actionBtnPrimary,
              pressed && { transform: [{ scale: 0.985 }] },
            ]}
          >
            <Ionicons name="calendar-outline" size={17} color={theme.primary} />
            <Text style={styles.actionBtnTextPrimary}>Apply Leave</Text>
          </Pressable>

          <Pressable
            onPress={() => router.push("/(teacher)/timetable")}
            style={({ pressed }) => [
              styles.actionBtnSecondary,
              pressed && { transform: [{ scale: 0.985 }] },
            ]}
          >
            <Ionicons name="time-outline" size={17} color={theme.inkSoft} />
            <Text style={styles.actionBtnTextSecondary}>My Timetable</Text>
          </Pressable>
        </View>
      </View>

      {/* Today's Periods Section */}
      <View style={styles.periodsCard}>
        <View style={styles.cardHeader}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <Text style={styles.cardTitle}>Today's Periods</Text>
            <View style={styles.classesPill}>
              <Text style={styles.classesPillText}>
                {data.today_schedule.length} Classes
              </Text>
            </View>
          </View>
          <Pressable onPress={() => router.push("/(teacher)/timetable")}>
            <Text style={styles.viewFullLink}>View full</Text>
          </Pressable>
        </View>

        <View style={styles.periodsList}>
          {data.today_schedule.length === 0 ? (
            <Empty text="No classes scheduled for today." icon="calendar-outline" />
          ) : (
            data.today_schedule.map((slot, i) => (
              <View key={i} style={styles.periodItem}>
                <View style={styles.periodNumBadge}>
                  <Text style={styles.periodNumText}>{slot.period}</Text>
                </View>

                <View style={{ flex: 1, minWidth: 0 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                    <Text style={styles.periodSubject} numberOfLines={1}>
                      {slot.subject}
                    </Text>
                    <View style={styles.sectionBadge}>
                      <Text style={styles.sectionBadgeText}>{slot.class_label}</Text>
                    </View>
                  </View>

                  <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginTop: 3 }}>
                    <Ionicons name="location-outline" size={12} color={theme.inkFaint} />
                    <Text style={styles.roomText}>{slot.room ?? "Assigned Classroom"}</Text>
                  </View>
                </View>

                <Text style={styles.periodTime}>{slot.time}</Text>
              </View>
            ))
          )}
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  profileCard: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    ...theme.shadow.card,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: theme.primary,
    alignItems: "center",
    justifyContent: "center",
    ...theme.shadow.button,
  },
  avatarText: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "800",
  },
  profileDetails: {
    flex: 1,
    gap: 2,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  teacherName: {
    fontSize: 16,
    fontWeight: "700",
    color: theme.ink,
    letterSpacing: -0.2,
    flex: 1,
    paddingRight: 6,
  },
  facultyBadge: {
    backgroundColor: theme.primarySoft,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.15)",
  },
  facultyBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.primary,
    textTransform: "uppercase",
  },
  schoolLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: theme.inkFaint,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: theme.inkSoft,
    marginTop: 2,
  },
  kpiGrid: {
    flexDirection: "row",
    gap: 10,
  },
  kpiCard: {
    flex: 1,
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 13,
    justifyContent: "space-between",
    ...theme.shadow.card,
  },
  kpiLabel: {
    fontSize: 9.5,
    fontWeight: "700",
    color: theme.inkFaint,
    letterSpacing: 0.4,
  },
  kpiValue: {
    fontSize: 22,
    fontWeight: "800",
    color: theme.ink,
    fontVariant: ["tabular-nums"],
    marginTop: 8,
    letterSpacing: -0.4,
  },
  kpiStatusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4.5,
    marginTop: 4,
  },
  kpiDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  kpiStatusText: {
    fontSize: 10.5,
    fontWeight: "600",
    color: theme.inkFaint,
  },
  dutyCard: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: "rgba(217, 119, 6, 0.2)",
    padding: 16,
    gap: 12,
    ...theme.shadow.card,
  },
  warningIconBox: {
    width: 26,
    height: 26,
    borderRadius: 7,
    backgroundColor: theme.warningBg,
    alignItems: "center",
    justifyContent: "center",
  },
  dutyList: {
    gap: 10,
  },
  dutyRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  dutyHeading: {
    fontSize: 13.5,
    fontWeight: "700",
    color: theme.warning,
  },
  dutySub: {
    fontSize: 11.5,
    color: theme.inkSoft,
    marginTop: 2,
  },
  dutyTime: {
    fontSize: 11.5,
    fontWeight: "600",
    color: theme.inkFaint,
    fontVariant: ["tabular-nums"],
  },
  actionCard: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 16,
    gap: 12,
    ...theme.shadow.card,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardTitle: {
    fontSize: 14.5,
    fontWeight: "700",
    letterSpacing: -0.2,
    color: theme.ink,
  },
  cardSubtitle: {
    fontSize: 11,
    fontWeight: "500",
    color: theme.inkFaint,
  },
  actionButtonsRow: {
    flexDirection: "row",
    gap: 10,
  },
  actionBtnPrimary: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: theme.primarySoft,
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.2)",
    paddingVertical: 12,
    borderRadius: 12,
  },
  actionBtnTextPrimary: {
    color: theme.primary,
    fontSize: 13,
    fontWeight: "700",
  },
  actionBtnSecondary: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
    paddingVertical: 12,
    borderRadius: 12,
  },
  actionBtnTextSecondary: {
    color: theme.inkSoft,
    fontSize: 13,
    fontWeight: "600",
  },
  periodsCard: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 16,
    gap: 12,
    ...theme.shadow.card,
  },
  classesPill: {
    backgroundColor: theme.primarySoft,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  classesPillText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.primary,
  },
  viewFullLink: {
    fontSize: 12,
    fontWeight: "700",
    color: theme.primary,
  },
  periodsList: {
    gap: 10,
  },
  periodItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: theme.ground,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 12,
    borderRadius: 12,
  },
  periodNumBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: theme.primarySoft,
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  periodNumText: {
    fontSize: 13,
    fontWeight: "800",
    color: theme.primary,
  },
  periodSubject: {
    fontSize: 13.5,
    fontWeight: "700",
    color: theme.ink,
    letterSpacing: -0.2,
  },
  sectionBadge: {
    backgroundColor: theme.groundAlt,
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
  },
  sectionBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.inkSoft,
  },
  roomText: {
    fontSize: 11,
    color: theme.inkFaint,
  },
  periodTime: {
    fontSize: 11.5,
    fontWeight: "600",
    color: theme.inkSoft,
    fontVariant: ["tabular-nums"],
  },
});
