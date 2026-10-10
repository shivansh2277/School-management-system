import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
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
import { Button, Card, Loading, Pill, Row, Screen, Stat, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type ChildHostelInfo = {
  student_id: number;
  student_name: string;
  admission_no: string;
  is_hosteller: boolean;
  admission: {
    hostel_name: string;
    hostel_code: string;
    room_number: string;
    bed_number: string;
    floor_number: number;
    admission_date: string;
    status: string;
  } | null;
  evening_attendance_summary: {
    days_recorded: number;
    present: number;
    absent: number;
    on_leave: number;
    on_outing: number;
  };
  fee_status: {
    head_code: string;
    amount: number | string;
    is_active: boolean;
  } | null;
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
  created_at: string;
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

export default function ParentHostelScreen() {
  const qc = useQueryClient();
  const { selectedChildId } = useAuth();

  const [activeTab, setActiveTab] = useState<"overview" | "leaves" | "mess">("overview");
  const [modalVisible, setModalVisible] = useState(false);
  const [requestType, setRequestType] = useState<"leave" | "outing">("leave");
  const [startDate, setStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
  const [returnTime, setReturnTime] = useState("20:00");
  const [purpose, setPurpose] = useState("");

  const { data: hostelInfo, isLoading: loadingHostel } = useQuery<ChildHostelInfo>({
    queryKey: ["parent-hostel-info", selectedChildId],
    queryFn: () => api.get<ChildHostelInfo>(`/parent/children/${selectedChildId}/hostel`),
    enabled: selectedChildId !== null,
  });

  const { data: leaves = [], isLoading: loadingLeaves } = useQuery<LeaveItem[]>({
    queryKey: ["parent-hostel-leaves", selectedChildId],
    queryFn: () => api.get<LeaveItem[]>(`/parent/children/${selectedChildId}/hostel/leaves`),
    enabled: selectedChildId !== null && !!hostelInfo?.is_hosteller,
  });

  const { data: messMenu = [] } = useQuery<MessDay[]>({
    queryKey: ["parent-hostel-mess", selectedChildId],
    queryFn: () => api.get<MessDay[]>(`/parent/children/${selectedChildId}/hostel/mess`),
    enabled: selectedChildId !== null && !!hostelInfo?.is_hosteller,
  });

  const submitLeave = useMutation({
    mutationFn: async () => {
      if (!purpose.trim()) throw new Error("Purpose is required");
      const expectedReturnIso = `${endDate}T${returnTime}:00Z`;
      return api.post(`/parent/children/${selectedChildId}/hostel/leave`, {
        request_type: requestType,
        start_date: startDate,
        end_date: endDate,
        expected_return_time: expectedReturnIso,
        purpose: purpose.trim(),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["parent-hostel-leaves", selectedChildId] });
      setModalVisible(false);
      setPurpose("");
      Alert.alert("Success", "Request submitted to Hostel Warden for approval.");
    },
    onError: (err: any) => {
      Alert.alert("Submission Failed", err.message || "Could not submit request.");
    },
  });

  if (loadingHostel) return <Loading />;

  if (!hostelInfo || !hostelInfo.is_hosteller) {
    return (
      <Screen>
        <Card title="Hostel Facility">
          <Text style={{ fontSize: 14, color: theme.inkSoft, lineHeight: 20 }}>
            {hostelInfo?.student_name || "Your child"} is currently enrolled as a Day Scholar.
          </Text>
          <View style={{ marginTop: 12, padding: 12, backgroundColor: theme.ground, borderRadius: 8 }}>
            <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>
              Residential Facility Information
            </Text>
            <Text style={{ fontSize: 12, color: theme.inkSoft, marginTop: 4, lineHeight: 18 }}>
              • Optional boarding available for students in Class 9 and above.
              {"\n"}• Separate Boys and Girls Hostels with 24/7 security.
              {"\n"}• Daily 8:00 PM safety attendance and biometric supervision.
              {"\n"}• Integrated dining mess with breakfast, lunch, snacks, and dinner.
            </Text>
          </View>
        </Card>
      </Screen>
    );
  }

  const { admission, evening_attendance_summary: att, fee_status: fee } = hostelInfo;

  return (
    <Screen>
      {/* Sub-tab Navigation */}
      <View style={localStyles.tabBar}>
        {(["overview", "leaves", "mess"] as const).map((tab) => (
          <Pressable
            key={tab}
            onPress={() => setActiveTab(tab)}
            style={[localStyles.tabBtn, activeTab === tab && localStyles.tabBtnActive]}
          >
            <Text style={[localStyles.tabText, activeTab === tab && localStyles.tabTextActive]}>
              {tab === "overview" ? "Hostel & Room" : tab === "leaves" ? "Leaves / Outings" : "Mess Menu"}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <>
          <Card title="Residential Allotment">
            <Row
              left={<Text style={s.meta}>Hostel Building</Text>}
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
              left={<Text style={s.meta}>Admitted On</Text>}
              right={<Text style={s.title}>{formatDate(admission?.admission_date)}</Text>}
            />
            <Row
              left={<Text style={s.meta}>Resident Status</Text>}
              right={<Pill status={admission?.status} label={admission?.status || "active"} />}
            />
          </Card>

          <Card title="8:00 PM Evening Safety Attendance">
            <Text style={{ fontSize: 12, color: theme.inkSoft, marginBottom: 8 }}>
              Mandatory residential roll-call conducted by the Warden every evening at 8:00 PM.
            </Text>
            <View style={{ flexDirection: "row", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
              <Stat label="Present" value={att.present} />
              <Stat label="Absent" value={att.absent} />
              <Stat label="On Leave" value={att.on_leave} />
              <Stat label="On Outing" value={att.on_outing} />
            </View>
          </Card>

          {fee && (
            <Card title="Hostel & Mess Fee Integration">
              <Row
                left={<Text style={s.meta}>Fee Head</Text>}
                right={<Text style={s.title}>{fee.head_code} (Accommodation + Mess)</Text>}
              />
              <Row
                left={<Text style={s.meta}>Monthly Rate</Text>}
                right={<Text style={s.title}>₹{fee.amount}</Text>}
              />
              <Row
                left={<Text style={s.meta}>Billing Status</Text>}
                right={<Pill status={fee.is_active ? "active" : "inactive"} label={fee.is_active ? "Active In Fee Plan" : "Inactive"} />}
              />
            </Card>
          )}
        </>
      )}

      {/* Leaves & Outings Tab */}
      {activeTab === "leaves" && (
        <>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Text style={{ fontSize: 14, fontWeight: "700", color: theme.ink }}>
              Leave & Outing Requests
            </Text>
            <Button label="+ Apply Leave / Outing" onPress={() => setModalVisible(true)} />
          </View>

          {loadingLeaves ? (
            <Loading />
          ) : leaves.length === 0 ? (
            <Card>
              <Text style={{ fontSize: 13, color: theme.inkSoft, textAlign: "center", paddingVertical: 12 }}>
                No leave or outing requests filed yet.
              </Text>
            </Card>
          ) : (
            leaves.map((item) => (
              <Card key={item.id}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={{ fontSize: 14, fontWeight: "700", color: theme.ink, textTransform: "uppercase" }}>
                    {item.request_type}
                  </Text>
                  <View style={{ flexDirection: "row", gap: 6, alignItems: "center" }}>
                    {item.is_overdue && (
                      <View style={{ backgroundColor: "#fef3c7", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, borderWidth: 1, borderColor: "#f59e0b" }}>
                        <Text style={{ fontSize: 10, fontWeight: "700", color: "#b45309" }}>⚠️ OVERDUE</Text>
                      </View>
                    )}
                    <Pill status={item.status} label={item.status} />
                  </View>
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
                    left={<Text style={s.meta}>Gate Arrival</Text>}
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
                {item.rejection_reason && (
                  <Row
                    left={<Text style={s.meta}>Rejection Reason</Text>}
                    right={<Text style={[s.meta, { color: theme.danger }]}>{item.rejection_reason}</Text>}
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
          <Card title="Dining Schedule">
            <Text style={{ fontSize: 12, color: theme.inkSoft, lineHeight: 18 }}>
              Four nutritious daily meals planned by the Chief Provost. Included with residential accommodation.
            </Text>
          </Card>

          {messMenu.map((day) => (
            <Card key={day.day_of_week} title={DAY_LABELS[day.day_of_week] || day.day_of_week.toUpperCase()}>
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#b45309" }]}>Breakfast (7:30 AM)</Text>}
                right={<Text style={s.title}>{day.breakfast}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#047857" }]}>Lunch (12:30 PM)</Text>}
                right={<Text style={s.title}>{day.lunch}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#0369a1" }]}>Snacks (4:30 PM)</Text>}
                right={<Text style={s.title}>{day.snacks}</Text>}
              />
              <Row
                left={<Text style={[s.meta, { fontWeight: "600", color: "#4338ca" }]}>Dinner (7:30 PM)</Text>}
                right={<Text style={s.title}>{day.dinner}</Text>}
              />
            </Card>
          ))}
        </>
      )}

      {/* Apply Leave / Outing Modal */}
      <Modal visible={modalVisible} animationType="slide" transparent>
        <View style={localStyles.modalOverlay}>
          <View style={localStyles.modalContent}>
            <Text style={{ fontSize: 16, fontWeight: "700", color: theme.ink, marginBottom: 12 }}>
              Apply for Leave / Outing
            </Text>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={localStyles.label}>Request Type</Text>
              <View style={{ flexDirection: "row", gap: 10, marginBottom: 12 }}>
                <Pressable
                  onPress={() => setRequestType("leave")}
                  style={[localStyles.typeBtn, requestType === "leave" && localStyles.typeBtnActive]}
                >
                  <Text style={[localStyles.typeText, requestType === "leave" && localStyles.typeTextActive]}>
                    Home Visit Leave
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => setRequestType("outing")}
                  style={[localStyles.typeBtn, requestType === "outing" && localStyles.typeBtnActive]}
                >
                  <Text style={[localStyles.typeText, requestType === "outing" && localStyles.typeTextActive]}>
                    Day Outing
                  </Text>
                </Pressable>
              </View>

              <Text style={localStyles.label}>Start Date (YYYY-MM-DD)</Text>
              <TextInput
                value={startDate}
                onChangeText={setStartDate}
                placeholder="2026-10-08"
                style={localStyles.input}
              />

              <Text style={localStyles.label}>End Date (YYYY-MM-DD)</Text>
              <TextInput
                value={endDate}
                onChangeText={setEndDate}
                placeholder="2026-10-09"
                style={localStyles.input}
              />

              <Text style={localStyles.label}>Expected Return Time (HH:MM)</Text>
              <TextInput
                value={returnTime}
                onChangeText={setReturnTime}
                placeholder="20:00"
                style={localStyles.input}
              />

              <Text style={localStyles.label}>Purpose / Reason *</Text>
              <TextInput
                value={purpose}
                onChangeText={setPurpose}
                placeholder="State the purpose for leave or outing..."
                multiline
                numberOfLines={3}
                style={[localStyles.input, { height: 70, textAlignVertical: "top" }]}
              />

              <View style={{ flexDirection: "row", justifyContent: "flex-end", gap: 10, marginTop: 16 }}>
                <Button label="Cancel" tone="ghost" onPress={() => setModalVisible(false)} />
                <Button
                  label={submitLeave.isPending ? "Submitting..." : "Submit to Warden"}
                  disabled={submitLeave.isPending}
                  onPress={() => submitLeave.mutate()}
                />
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
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
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    padding: 16,
  },
  modalContent: {
    backgroundColor: theme.surface,
    borderRadius: 12,
    padding: 16,
    maxHeight: "85%",
  },
  label: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.inkSoft,
    textTransform: "uppercase",
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.ground,
    backgroundColor: theme.ground,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 13,
    color: theme.ink,
    marginBottom: 10,
  },
  typeBtn: {
    flex: 1,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: theme.ground,
    borderRadius: 6,
    alignItems: "center",
  },
  typeBtnActive: {
    backgroundColor: theme.primary,
    borderColor: theme.primary,
  },
  typeText: {
    fontSize: 12,
    color: theme.ink,
    fontWeight: "500",
  },
  typeTextActive: {
    color: "#fff",
    fontWeight: "700",
  },
});
