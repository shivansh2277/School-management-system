import Ionicons from "@expo/vector-icons/Ionicons";
import { useRouter } from "expo-router";
import React from "react";
import {
  Alert,
  Dimensions,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../auth/AuthContext";
import { theme } from "../theme";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const DRAWER_WIDTH = Math.min(SCREEN_WIDTH * 0.82, 340);

type MenuItem = {
  id: string;
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  path?: string;
  action?: () => void;
};

type MenuSection = {
  title: string;
  items: MenuItem[];
};

function getInitials(name?: string): string {
  if (!name) return "S";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (name[0] ?? "S").toUpperCase();
}

export function NavDrawer({
  visible,
  onClose,
}: {
  visible: boolean;
  onClose: () => void;
}) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { me, logout, selectedChildId, selectChild } = useAuth();
  const role = me?.user.role ?? "student";

  const handleNavigate = (path?: string, action?: () => void) => {
    onClose();
    if (action) {
      action();
    } else if (path) {
      router.push(path as any);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      "Confirm Logout",
      "Are you sure you want to sign out of your account?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Logout",
          style: "destructive",
          onPress: async () => {
            onClose();
            await logout();
            router.replace("/");
          },
        },
      ],
    );
  };

  const showSupport = () => {
    Alert.alert(
      "Sunrise ERP Helpdesk",
      "For student credentials, fee ledger disputes, or tech support:\n\nEmail: office@sunrisepublic.edu\nPhone: +91 (0522) 234-5678\nHours: Mon–Sat, 8:00 AM – 3:30 PM",
      [{ text: "OK" }],
    );
  };

  const showSettings = () => {
    Alert.alert(
      "Settings & Preferences",
      "Academic Year: 2025-26\nSystem Language: English (CBSE)\nNotifications: Enabled\nApp Cache: Up to date",
      [{ text: "Done" }],
    );
  };

  // Categorized sections per role
  const sections: MenuSection[] = [];

  if (role === "parent") {
    sections.push({
      title: "ACADEMICS",
      items: [
        {
          id: "p_timetable",
          title: "Timetable & Schedule",
          icon: "calendar-outline",
          path: "/(parent)/child",
        },
        {
          id: "p_homework",
          title: "Homework",
          icon: "book-outline",
          path: "/(parent)/homework",
        },
        {
          id: "p_attendance",
          title: "Attendance History",
          icon: "checkbox-outline",
          path: "/(parent)/attendance",
        },
        {
          id: "p_results",
          title: "Results & Report Cards",
          icon: "school-outline",
          path: "/(parent)/results",
        },
      ],
    });
    sections.push({
      title: "COMMUNICATION",
      items: [
        {
          id: "p_notices",
          title: "School Notices",
          icon: "notifications-outline",
          path: "/(parent)/notices",
        },
        {
          id: "p_grievances",
          title: "Grievances & Helpdesk",
          icon: "chatbubbles-outline",
          path: "/(parent)/grievances",
        },
      ],
    });
    sections.push({
      title: "OTHER",
      items: [
        {
          id: "p_settings",
          title: "Settings",
          icon: "settings-outline",
          action: showSettings,
        },
        {
          id: "p_support",
          title: "Support & Help",
          icon: "help-circle-outline",
          action: showSupport,
        },
      ],
    });
  } else if (role === "teacher") {
    sections.push({
      title: "ACADEMICS",
      items: [
        {
          id: "t_timetable",
          title: "Timetable & Slots",
          icon: "calendar-outline",
          path: "/(teacher)/timetable",
        },
        {
          id: "t_homework",
          title: "Homework Manager",
          icon: "book-outline",
          path: "/(teacher)/homework",
        },
        {
          id: "t_results",
          title: "Marks Entry & Results",
          icon: "school-outline",
          path: "/(teacher)/results",
        },
      ],
    });
    sections.push({
      title: "OPERATIONS",
      items: [
        {
          id: "t_stock",
          title: "Classroom Supplies / Stock",
          icon: "cube-outline",
          path: "/(teacher)/stock",
        },
        {
          id: "t_leave",
          title: "Leave & Substitution Duties",
          icon: "calendar-clear-outline",
          path: "/(teacher)/leave",
        },
      ],
    });
    sections.push({
      title: "COMMUNICATION",
      items: [
        {
          id: "t_notices",
          title: "School Notices",
          icon: "megaphone-outline",
          path: "/(teacher)/announcements",
        },
        {
          id: "t_grievances",
          title: "Grievance Desk",
          icon: "chatbubbles-outline",
          path: "/(teacher)/grievances",
        },
      ],
    });
    sections.push({
      title: "OTHER",
      items: [
        {
          id: "t_settings",
          title: "Settings",
          icon: "settings-outline",
          action: showSettings,
        },
        {
          id: "t_support",
          title: "Teacher Support",
          icon: "help-circle-outline",
          action: showSupport,
        },
      ],
    });
  } else {
    // Student
    sections.push({
      title: "ACADEMICS",
      items: [
        {
          id: "s_attendance",
          title: "Attendance History",
          icon: "checkbox-outline",
          path: "/(student)/attendance",
        },
        {
          id: "s_results",
          title: "Exam Results & Scorecard",
          icon: "school-outline",
          path: "/(student)/results",
        },
      ],
    });
    sections.push({
      title: "COMMUNICATION",
      items: [
        {
          id: "s_notices",
          title: "School Notices",
          icon: "notifications-outline",
          path: "/(student)/notices",
        },
      ],
    });
    sections.push({
      title: "OTHER",
      items: [
        {
          id: "s_settings",
          title: "Settings",
          icon: "settings-outline",
          action: showSettings,
        },
        {
          id: "s_support",
          title: "Support & Help",
          icon: "help-circle-outline",
          action: showSupport,
        },
      ],
    });
  }

  const roleLabel =
    role === "parent" ? "Parent" : role === "teacher" ? "Faculty" : "Student";
  const initials = getInitials(me?.user.full_name);
  const children = me?.children ?? [];

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        {/* Semi-transparent backdrop */}
        <Pressable
          style={styles.backdrop}
          onPress={onClose}
          accessibilityRole="button"
          accessibilityLabel="Dismiss Menu"
        />

        {/* Drawer Slide-in Container */}
        <View
          style={[
            styles.drawer,
            { paddingTop: Math.max(insets.top, 16), paddingBottom: Math.max(insets.bottom, 16) },
          ]}
        >
          {/* Header with User Profile & Top-Right Red X */}
          <View style={styles.header}>
            <View style={styles.profileRow}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{initials}</Text>
              </View>
              <View style={styles.profileInfo}>
                <View style={styles.nameBadgeRow}>
                  <Text style={styles.userName} numberOfLines={1}>
                    {me?.user.full_name ?? "Sunrise User"}
                  </Text>
                  <View style={styles.roleBadge}>
                    <Text style={styles.roleBadgeText}>{roleLabel}</Text>
                  </View>
                </View>
                <Text style={styles.schoolName}>Sunrise Public School</Text>
              </View>
            </View>

            {/* Red X Close Button */}
            <Pressable
              onPress={onClose}
              style={styles.closeBtn}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
              accessibilityRole="button"
              accessibilityLabel="Close"
            >
              <Ionicons name="close" size={22} color="#ef4444" />
            </Pressable>
          </View>

          {/* Child Switcher in Drawer (for Parents with multiple children) */}
          {role === "parent" && children.length > 1 && (
            <View style={styles.childSwitcherBox}>
              <Text style={styles.childSwitcherLabel}>ACTIVE CHILD</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ gap: 6, paddingTop: 4 }}
              >
                {children.map((c) => {
                  const on = c.id === selectedChildId;
                  return (
                    <Pressable
                      key={c.id}
                      onPress={() => selectChild(c.id)}
                      style={[
                        styles.childChip,
                        on ? styles.childChipActive : styles.childChipInactive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.childChipText,
                          on ? styles.childChipTextActive : styles.childChipTextInactive,
                        ]}
                      >
                        {c.name} ({c.class_label})
                      </Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>
          )}

          {/* Scrollable Categorized Menu List */}
          <ScrollView
            style={styles.menuScroll}
            contentContainerStyle={styles.menuContent}
            showsVerticalScrollIndicator={false}
          >
            {sections.map((section) => (
              <View key={section.title} style={styles.section}>
                <Text style={styles.sectionTitle}>{section.title}</Text>
                {section.items.map((item) => (
                  <Pressable
                    key={item.id}
                    onPress={() => handleNavigate(item.path, item.action)}
                    style={({ pressed }) => [
                      styles.menuItem,
                      pressed && styles.menuItemPressed,
                    ]}
                  >
                    <View style={styles.itemIconBox}>
                      <Ionicons name={item.icon} size={20} color={theme.primary} />
                    </View>
                    <Text style={styles.itemTitle}>{item.title}</Text>
                    <Ionicons
                      name="chevron-forward-outline"
                      size={16}
                      color={theme.inkFaint}
                    />
                  </Pressable>
                ))}
              </View>
            ))}
          </ScrollView>

          {/* Drawer Footer with App Version and Red Logout */}
          <View style={styles.footer}>
            <Pressable
              onPress={handleLogout}
              style={({ pressed }) => [
                styles.logoutBtn,
                pressed && { opacity: 0.8 },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Logout"
            >
              <Ionicons name="log-out-outline" size={20} color="#ef4444" />
              <Text style={styles.logoutText}>Logout</Text>
            </Pressable>

            <Text style={styles.versionText}>Sunrise ERP • v1.0.0</Text>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
  },
  backdrop: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  drawer: {
    width: DRAWER_WIDTH,
    backgroundColor: theme.surface,
    height: "100%",
    elevation: 16,
    shadowColor: "#000",
    shadowOffset: { width: 4, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  profileRow: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    paddingRight: 8,
    gap: 10,
  },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: theme.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
  profileInfo: {
    flex: 1,
    gap: 2,
  },
  nameBadgeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
  },
  userName: {
    fontSize: 15,
    fontWeight: "700",
    color: theme.ink,
    maxWidth: 130,
  },
  roleBadge: {
    backgroundColor: `${theme.primary}1A`,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.primary,
    textTransform: "uppercase",
  },
  schoolName: {
    fontSize: 11,
    color: theme.inkFaint,
  },
  closeBtn: {
    padding: 6,
    borderRadius: 20,
    backgroundColor: "rgba(239, 68, 68, 0.1)",
    alignItems: "center",
    justifyContent: "center",
  },
  childSwitcherBox: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: theme.ground,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  childSwitcherLabel: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.8,
    color: theme.inkFaint,
  },
  childChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: theme.radius.pill,
  },
  childChipActive: {
    backgroundColor: theme.primary,
  },
  childChipInactive: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.rule,
  },
  childChipText: {
    fontSize: 11,
  },
  childChipTextActive: {
    color: "#fff",
    fontWeight: "600",
  },
  childChipTextInactive: {
    color: theme.inkSoft,
  },
  menuScroll: {
    flex: 1,
  },
  menuContent: {
    paddingVertical: 12,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1,
    color: theme.inkFaint,
    paddingHorizontal: 16,
    marginBottom: 6,
    textTransform: "uppercase",
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 11,
    gap: 12,
  },
  menuItemPressed: {
    backgroundColor: theme.ground,
  },
  itemIconBox: {
    width: 28,
    alignItems: "center",
    justifyContent: "center",
  },
  itemTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: "500",
    color: theme.ink,
  },
  footer: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.rule,
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 10,
  },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "rgba(239, 68, 68, 0.08)",
    paddingVertical: 10,
    borderRadius: theme.radius.input,
  },
  logoutText: {
    color: "#ef4444",
    fontSize: 14,
    fontWeight: "700",
  },
  versionText: {
    fontSize: 11,
    color: theme.inkFaint,
    textAlign: "center",
  },
});
