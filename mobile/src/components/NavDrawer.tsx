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
import { useTranslation } from "../i18n/I18nContext";
import { theme } from "../theme";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const DRAWER_WIDTH = Math.min(SCREEN_WIDTH * 0.84, 340);

type MenuItem = {
  id: string;
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  path?: string;
  action?: () => void;
  disabled?: boolean;
  badge?: string;
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
  const { language, setLanguage, t } = useTranslation();
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
      ]
    );
  };

  const showSupport = () => {
    Alert.alert(
      "Sunrise ERP Helpdesk",
      "For student credentials, fee ledger disputes, or tech support:\n\nEmail: office@sunrisepublic.edu\nPhone: +91 (0522) 234-5678\nHours: Mon–Sat, 8:00 AM – 3:30 PM",
      [{ text: "OK" }]
    );
  };

  const showSettings = () => {
    Alert.alert(
      "Settings & Preferences",
      "Academic Year: 2025-26\nSystem Language: English (CBSE)\nNotifications: Enabled\nApp Cache: Up to date",
      [{ text: "Done" }]
    );
  };

  // Categorized sections per role
  const sections: MenuSection[] = [];

  if (role === "parent") {
    sections.push({
      title: t("nav_navigation"),
      items: [
        {
          id: "p_home",
          title: t("nav_home"),
          icon: "home-outline",
          path: "/(parent)/dashboard",
        },
        {
          id: "p_child",
          title: t("nav_child"),
          icon: "person-circle-outline",
          path: "/(parent)/child",
        },
        {
          id: "p_fees",
          title: t("nav_fees"),
          icon: "card-outline",
          path: "/(parent)/fees",
        },
        {
          id: "p_hostel",
          title: "Hostel & Mess",
          icon: "bed-outline",
          path: "/(parent)/hostel",
        },
        {
          id: "p_profile",
          title: t("nav_profile"),
          icon: "person-outline",
          path: "/(parent)/profile",
        },
      ],
    });
    sections.push({
      title: t("nav_academic"),
      items: [
        {
          id: "p_timetable",
          title: t("nav_timetable"),
          icon: "calendar-outline",
          path: "/(parent)/timetable",
        },
        {
          id: "p_attendance",
          title: t("nav_attendance"),
          icon: "checkbox-outline",
          path: "/(parent)/attendance",
        },
        {
          id: "p_homework",
          title: t("nav_homework"),
          icon: "book-outline",
          path: "/(parent)/homework",
        },
        {
          id: "p_results",
          title: t("nav_results"),
          icon: "school-outline",
          path: "/(parent)/results",
        },
        {
          id: "p_todays_class",
          title: "Today's Class",
          icon: "newspaper-outline",
          disabled: true,
          badge: "Coming Soon",
        },
      ],
    });
    sections.push({
      title: t("nav_communication"),
      items: [
        {
          id: "p_notices",
          title: t("nav_notices"),
          icon: "notifications-outline",
          path: "/(parent)/notices",
        },
        {
          id: "p_grievances",
          title: t("nav_grievances"),
          icon: "chatbubbles-outline",
          path: "/(parent)/grievances",
        },
        {
          id: "p_teacher_chat",
          title: "Teacher Chat",
          icon: "chatbubbles-outline",
          disabled: true,
          badge: "Coming Soon",
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
      title: "NAVIGATION",
      items: [
        {
          id: "t_home",
          title: "Home",
          icon: "home-outline",
          path: "/(teacher)/dashboard",
        },
        {
          id: "t_classes",
          title: "My Classes",
          icon: "people-outline",
          path: "/(teacher)/classes",
        },
        {
          id: "t_attendance",
          title: "Attendance",
          icon: "checkbox-outline",
          path: "/(teacher)/attendance",
        },
        {
          id: "t_profile",
          title: "Faculty Profile",
          icon: "person-outline",
          path: "/(teacher)/profile",
        },
      ],
    });
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
        {
          id: "t_todays_class",
          title: "Today's Class",
          icon: "create-outline",
          disabled: true,
          badge: "Coming Soon",
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
        {
          id: "t_parent_messages",
          title: "Parent Messages",
          icon: "chatbubbles-outline",
          disabled: true,
          badge: "Coming Soon",
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
      title: "NAVIGATION",
      items: [
        {
          id: "s_home",
          title: "Home",
          icon: "home-outline",
          path: "/(student)/dashboard",
        },
        {
          id: "s_timetable",
          title: "Weekly Timetable",
          icon: "calendar-outline",
          path: "/(student)/timetable",
        },
        {
          id: "s_homework",
          title: "Homework",
          icon: "book-outline",
          path: "/(student)/homework",
        },
        {
          id: "s_profile",
          title: "Student Profile",
          icon: "person-outline",
          path: "/(student)/profile",
        },
        {
          id: "s_hostel",
          title: "Hostel & Mess",
          icon: "bed-outline",
          path: "/(student)/hostel",
        },
      ],
    });
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
        {
          id: "s_todays_class",
          title: "Today's Class",
          icon: "newspaper-outline",
          disabled: true,
          badge: "Coming Soon",
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

  const roleBadgeLabel =
    role === "parent" ? "PARENT" : role === "teacher" ? "FACULTY" : "STUDENT";
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
          {/* Header with User Profile matching Stitch Screens 25 & 30 */}
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
                </View>
                <View style={styles.roleRow}>
                  <View style={styles.roleBadge}>
                    <Text style={styles.roleBadgeText}>{roleBadgeLabel}</Text>
                  </View>
                  <View style={styles.statusIndicatorBox}>
                    <View style={styles.pulseDot} />
                    <Text style={styles.statusText}>ACTIVE</Text>
                  </View>
                </View>
              </View>
            </View>

            <Pressable
              onPress={onClose}
              style={styles.closeBtn}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
              accessibilityRole="button"
              accessibilityLabel="Close"
            >
              <Ionicons name="close" size={20} color={theme.inkSoft} />
            </Pressable>
          </View>

          {/* Child Switcher in Drawer (Parent Role) */}
          {role === "parent" && children.length > 1 && (
            <View style={styles.childSwitcherBox}>
              <Text style={styles.childSwitcherLabel}>SELECT WARD</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ gap: 8, paddingTop: 4 }}
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
                      <Ionicons
                        name={on ? "school" : "school-outline"}
                        size={14}
                        color={on ? "#FFFFFF" : theme.inkSoft}
                      />
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
                {section.items.map((item) => {
                  const isDisabled = Boolean(item.disabled);
                  return (
                    <Pressable
                      key={item.id}
                      disabled={isDisabled}
                      onPress={isDisabled ? undefined : () => handleNavigate(item.path, item.action)}
                      style={({ pressed }) => [
                        styles.menuItem,
                        isDisabled && styles.menuItemDisabled,
                        pressed && !isDisabled && styles.menuItemPressed,
                      ]}
                      accessibilityState={{ disabled: isDisabled }}
                    >
                      <View style={[styles.itemIconBox, isDisabled && styles.itemIconBoxDisabled]}>
                        <Ionicons
                          name={item.icon}
                          size={18}
                          color={isDisabled ? theme.inkFaint : theme.primary}
                        />
                      </View>
                      <Text
                        style={[styles.itemTitle, isDisabled && styles.itemTitleDisabled]}
                        numberOfLines={1}
                      >
                        {item.title}
                      </Text>
                      {item.badge ? (
                        <View style={styles.comingSoonBadge}>
                          <Text style={styles.comingSoonText}>{item.badge}</Text>
                        </View>
                      ) : (
                        <Ionicons
                          name="chevron-forward"
                          size={15}
                          color={theme.inkFaint}
                        />
                      )}
                    </Pressable>
                  );
                })}
              </View>
            ))}
          </ScrollView>

          {/* Drawer Footer */}
          <View style={styles.footer}>
            {role === "parent" && (
              <View style={styles.langSwitchContainer}>
                <Text style={styles.langSwitchLabel}>{t("prof_language")}</Text>
                <View style={styles.langSwitchPills}>
                  <Pressable
                    onPress={() => setLanguage("en")}
                    style={[styles.langPill, language === "en" && styles.langPillActive]}
                  >
                    <Text style={[styles.langPillText, language === "en" && styles.langPillTextActive]}>
                      English
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => setLanguage("hi")}
                    style={[styles.langPill, language === "hi" && styles.langPillActive]}
                  >
                    <Text style={[styles.langPillText, language === "hi" && styles.langPillTextActive]}>
                      हिन्दी
                    </Text>
                  </Pressable>
                </View>
              </View>
            )}

            <Pressable
              onPress={handleLogout}
              style={({ pressed }) => [
                styles.logoutBtn,
                pressed && { opacity: 0.8 },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Logout"
            >
              <Ionicons name="log-out-outline" size={18} color={theme.danger} />
              <Text style={styles.logoutText}>{role === "parent" ? t("nav_sign_out") : "Logout"}</Text>
            </Pressable>

            <Text style={styles.versionText}>Sunrise School ERP • EdTech Luxe</Text>
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
    backgroundColor: "rgba(15, 23, 42, 0.45)",
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
    ...theme.shadow.elevated,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 18,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  profileRow: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    paddingRight: 8,
    gap: 12,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: theme.primary,
    alignItems: "center",
    justifyContent: "center",
    ...theme.shadow.subtle,
  },
  avatarText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "800",
  },
  profileInfo: {
    flex: 1,
    gap: 3,
  },
  nameBadgeRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  userName: {
    fontSize: 15,
    fontWeight: "700",
    color: theme.ink,
    letterSpacing: -0.2,
  },
  roleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  roleBadge: {
    backgroundColor: theme.primarySoft,
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 6,
  },
  roleBadgeText: {
    fontSize: 9.5,
    fontWeight: "800",
    color: theme.primary,
    letterSpacing: 0.4,
  },
  statusIndicatorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  pulseDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: theme.successCore,
  },
  statusText: {
    fontSize: 9.5,
    fontWeight: "700",
    color: theme.success,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: theme.groundAlt,
    alignItems: "center",
    justifyContent: "center",
  },
  childSwitcherBox: {
    paddingHorizontal: 18,
    paddingVertical: 12,
    backgroundColor: theme.ground,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  childSwitcherLabel: {
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.8,
    color: theme.inkFaint,
  },
  childChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: theme.radius.pill,
  },
  childChipActive: {
    backgroundColor: theme.primary,
    ...theme.shadow.subtle,
  },
  childChipInactive: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
  },
  childChipText: {
    fontSize: 11.5,
  },
  childChipTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  childChipTextInactive: {
    color: theme.inkSoft,
    fontWeight: "600",
  },
  menuScroll: {
    flex: 1,
  },
  menuContent: {
    paddingVertical: 14,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 10.5,
    fontWeight: "800",
    letterSpacing: 0.8,
    color: theme.inkFaint,
    paddingHorizontal: 18,
    marginBottom: 6,
    textTransform: "uppercase",
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 9.5,
    gap: 12,
  },
  menuItemDisabled: {
    opacity: 0.5,
  },
  menuItemPressed: {
    backgroundColor: theme.ground,
  },
  itemIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: theme.primarySoft,
    alignItems: "center",
    justifyContent: "center",
  },
  itemIconBoxDisabled: {
    backgroundColor: theme.groundAlt,
  },
  itemTitle: {
    flex: 1,
    fontSize: 13.5,
    fontWeight: "600",
    color: theme.ink,
    letterSpacing: -0.1,
  },
  itemTitleDisabled: {
    color: theme.inkFaint,
  },
  comingSoonBadge: {
    backgroundColor: theme.primarySoft,
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.2)",
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: theme.radius.pill,
  },
  comingSoonText: {
    fontSize: 9.5,
    fontWeight: "700",
    color: theme.primary,
  },
  footer: {
    borderTopWidth: 1,
    borderTopColor: theme.rule,
    paddingHorizontal: 18,
    paddingTop: 12,
    gap: 10,
  },
  langSwitchContainer: {
    marginBottom: 4,
    gap: 6,
  },
  langSwitchLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.inkFaint,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  langSwitchPills: {
    flexDirection: "row",
    backgroundColor: theme.ground,
    borderRadius: 10,
    padding: 3,
    gap: 4,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
  },
  langPill: {
    flex: 1,
    paddingVertical: 6,
    alignItems: "center",
    borderRadius: 8,
  },
  langPillActive: {
    backgroundColor: theme.surface,
    ...theme.shadow.subtle,
  },
  langPillText: {
    fontSize: 11.5,
    fontWeight: "600",
    color: theme.inkSoft,
  },
  langPillTextActive: {
    color: theme.primary,
    fontWeight: "700",
  },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: theme.dangerBg,
    borderWidth: 1,
    borderColor: "rgba(225, 29, 72, 0.15)",
    paddingVertical: 11,
    borderRadius: theme.radius.input,
  },
  logoutText: {
    color: theme.danger,
    fontSize: 13.5,
    fontWeight: "700",
  },
  versionText: {
    fontSize: 10.5,
    color: theme.inkFaint,
    textAlign: "center",
  },
});
