import { useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Card, Loading, Pill, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type StudentHostelInfo = {
  is_hosteller: boolean;
  admission: {
    hostel_name: string;
    hostel_code: string;
    room_number: string;
    bed_number: string;
    floor_number: number;
    admission_date: string;
  } | null;
  roommates: Array<{
    student_name: string;
    bed_number: string;
  }>;
  evening_attendance_summary: {
    days_recorded: number;
    present: number;
    absent: number;
    on_leave: number;
    on_outing: number;
  };
};

type LeaveItem = {
  id: number;
  request_type: "leave" | "outing";
  start_date: string;
  end_date: string;
  expected_return_time: string;
  actual_return_time: string | null;
  purpose: string;
  status: string;
  is_overdue: boolean;
  remarks: string | null;
  rejection_reason: string | null;
};

type MessDay = {
  id?: number;
  day_of_week: string;
  breakfast: string;
  lunch: string;
  snacks: string;
  dinner: string;
  is_published: boolean;
};

const DAY_LABELS: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
};

export default function StudentHostelScreen() {
  const [activeTab, setActiveTab] = useState<"room" | "attendance" | "leaves" | "mess">("room");

  const { data: hostelInfo, isLoading: loadingHostel } = useQuery<StudentHostelInfo>({
    queryKey: ["student-hostel-info"],
    queryFn: () => api.get<StudentHostelInfo>("/student/hostel"),
  });

  const { data: leaves = [], isLoading: loadingLeaves } = useQuery<LeaveItem[]>({
    queryKey: ["student-hostel-leaves"],
    queryFn: () => api.get<LeaveItem[]>("/student/hostel/leaves"),
    enabled: !!hostelInfo?.is_hosteller,
  });

  const { data: messMenu = [] } = useQuery<MessDay[]>({
    queryKey: ["student-hostel-mess"],
    queryFn: () => api.get<MessDay[]>("/student/hostel/mess"),
    enabled: !!hostelInfo?.is_hosteller,
  });

  if (loadingHostel) return <Loading />;

  if (!hostelInfo || !hostelInfo.is_hosteller) {
    return (
      <Screen>
        <Card title="Hostel Facility">
          <Text style={{ fontSize: 14, color: theme.inkSoft, lineHeight: 20 }}>
            You are currently enrolled as a Day Scholar.
          </Text>
          <View style={{ marginTop: 12, padding: 12, backgroundColor: theme.ground, borderRadius: 8 }}>
            <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
              Hostel Accommodation (Class 9+)
            </Text>
            <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 4, lineHeight: 18 }}>
              Hostel admissions for senior students are processed by the Chief Provost. If you wish to apply for hostel boarding, please have your parents contact the school administration.
            </Text>
          </View>
        </Card>
      </Screen>
    );
  }

  const { admission, roommates, evening_attendance_summary: att } = hostelInfo;

  return (
    <Screen>
      {/* Sub-tab Navigation */}
      <View style={localStyles.tabBar}>
        {(["room", "attendance", "leaves", "mess"] as const).map((tab) => (
          <Pressable
            key={tab}
            onPress={() => setActiveTab(tab)}
            style={[localStyles.tabBtn, activeTab === tab && localStyles.tabBtnActive]}
          >
            <Text style={[localStyles.tabText, activeTab === tab && localStyles.tabTextActive]}>
              {tab === "room" ? "My Room" : tab === "attendance" ? "Attendance" : tab === "leaves" ? "Leaves" : "Mess"}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Room Tab */}
      {activeTab === "room" && (
        <>
          <Card title="My Residential Allotment">
            <Row
              left={<Text style={s.meta}>Hostel</Text>}
              right={<Text style={s.title}>{admission?.hostel_name} ({admission?.hostel_code})</Text>}
            />
            <Row
              left={<Text style={s.meta}>Room & Bed</Text>}
              right={<Text style={s.title}>Room {admission?.room_number} • Bed {admission?.bed_number}</Text>}
            />
            <Row
              left={<Text style={s.meta}>Floor</Text>}
              right={<Text style={s.title}>Floor {admission?.floor_number}</Text>}
            />
            <Row
              left={<Text style={s.meta}>Allotment Date</Text>}
              right={<Text style={s.title}>{formatDate(admission?.admission_date)}</Text>}
            />
          </Card>

          <Card title="Roommates">
            {roommates.length === 0 ? (
              <Text style={{ fontSize: 13, color: theme.inkSoft }}>No other roommates currently assigned.</Text>
            ) : (
              roommates.map((r, i) => (
                <Row
                  key={i}
                  left={<Text style={s.title}>{r.student_name}</Text>}
                  right={<Text style={s.meta}>Bed {r.bed_number}</Text>}
                />
              ))
            )}
          </Card>
        </>
      )}

      {/* Attendance Tab */}
      {activeTab === "attendance" && (
        <Card title="8:00 PM Evening Roll-Call History">
          <Text style={{ fontSize: 12, color: theme.inkSoft, marginBottom: 8 }}>
            Hostel safety attendance is marked daily by the Warden at 8:00 PM.
          </Text>
          <View style={{ flexDirection: "row", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
            <Stat label="Present" value={att.present} />
            <Stat label="Absent" value={att.absent} />
            <Stat label="On Leave" value={att.on_leave} />
            <Stat label="On Outing" value={att.on_outing} />
          </View>
        </Card>
      )}

      {/* Leaves Tab (Read-Only per Specification §13) */}
      {activeTab === "leaves" && (
        <>
          <View style={{ marginBottom: 4 }}>
            <Text style={{ fontSize: 12, color: theme.inkSoft }}>
              Outing and leave requests must be submitted by your parent or guardian via the Parent App.
            </Text>
          </View>

          {loadingLeaves ? (
            <Loading />
          ) : leaves.length === 0 ? (
            <Card>
              <Text style={{ fontSize: 13, color: theme.inkSoft, textAlign: "center", paddingVertical: 12 }}>
                No active or past leave requests found.
              </Text>
            </Card>
          ) : (
            leaves.map((item) => (
              <Card key={item.id}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={{ fontSize: 14, fontWeight: "700", color: theme.ink, textTransform: "uppercase" }}>
                    {item.request_type}
                  </Text>
                  <Pill status={item.status} label={item.status} />
                </View>

                <Row
                  left={<Text style={s.meta}>Schedule</Text>}
                  right={<Text style={s.title}>{item.start_date} → {item.end_date}</Text>}
                />
                <Row
                  left={<Text style={s.meta}>Expected Return</Text>}
                  right={<Text style={s.title}>{new Date(item.expected_return_time).toLocaleString()}</Text>}
                />
                {item.actual_return_time && (
                  <Row
                    left={<Text style={s.meta}>Gate Return</Text>}
                    right={<Text style={[s.title, { color: theme.success }]}>{new Date(item.actual_return_time).toLocaleString()}</Text>}
                  />
                )}
                <Row
                  left={<Text style={s.meta}>Purpose</Text>}
                  right={<Text style={[s.title, { maxWidth: 200 }]}>{item.purpose}</Text>}
                />
                {item.remarks && (
                  <Row
                    left={<Text style={s.meta}>Warden Remarks</Text>}
                    right={<Text style={s.meta}>{item.remarks}</Text>}
                  />
                )}
              </Card>
            ))
          )}
        </>
      )}

      {/* Mess Menu Tab */}
      {activeTab === "mess" && (
        <>
          <Card title="Weekly Dining Menu">
            <Text style={{ fontSize: 12, color: theme.inkSoft }}>
              Weekly breakfast, lunch, tea & snacks, and dinner planned by the Chief Provost.
            </Text>
          </Card>

          {messMenu.map((day) => (
            <Card key={day.day_of_week} title={DAY_LABELS[day.day_of_week] || day.day_of_week.toUpperCase()}>
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#b45309" }]}>Breakfast</Text>}
                right={<Text style={s.title}>{day.breakfast}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#047857" }]}>Lunch</Text>}
                right={<Text style={s.title}>{day.lunch}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#0369a1" }]}>Snacks</Text>}
                right={<Text style={s.title}>{day.snacks}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#4338ca" }]}>Dinner</Text>}
                right={<Text style={s.title}>{day.dinner}</Text>}
              />
            </Card>
          ))}
        </>
      )}
    </Screen>
  );
}

const localStyles = StyleSheet.create({
  tabBar: {
    flexDirection: "row",
    backgroundColor: theme.surface,
    borderRadius: 8,
    padding: 4,
    marginBottom: 8,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 6,
  },
  tabBtnActive: {
    backgroundColor: theme.primary,
  },
  tabText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
  },
  tabTextActive: {
    color: "#fff",
  },
});
