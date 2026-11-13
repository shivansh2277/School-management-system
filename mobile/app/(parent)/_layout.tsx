import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, Tabs } from "expo-router";
import React, { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../../src/auth/AuthContext";
import { NavDrawer } from "../../src/components/NavDrawer";
import { Loading, tabIcon } from "../../src/components/ui";
import { I18nProvider, useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

/** Horizontal child switcher chips rendered when parent has 2+ children matching Stitch Screen 10. */
function ChildSwitcherBar() {
  const { me, selectedChildId, selectChild } = useAuth();
  const children = me?.children ?? [];
  if (children.length < 2) return null;

  return (
    <View style={styles.childBar}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 8, paddingHorizontal: 16 }}
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
                name={on ? "school" : "person-outline"}
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
  );
}

function ParentCustomHeader({
  title,
  onOpenDrawer,
}: {
  title: string;
  onOpenDrawer: () => void;
}) {
  const insets = useSafeAreaInsets();
  const { me } = useAuth();
  const children = me?.children ?? [];

  return (
    <View style={[styles.headerContainer, { paddingTop: insets.top }]}>
      <View style={styles.headerRow}>
        <Pressable
          onPress={onOpenDrawer}
          style={styles.headerIconBtn}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          accessibilityRole="button"
          accessibilityLabel="Open Menu"
        >
          <Ionicons name="menu-outline" size={24} color={theme.ink} />
        </Pressable>

        <Text style={styles.headerTitle}>{title}</Text>

        <Pressable
          style={styles.headerIconBtn}
          accessibilityRole="button"
          accessibilityLabel="Notifications"
        >
          <Ionicons name="notifications-outline" size={22} color={theme.inkSoft} />
          <View style={styles.notificationDot} />
        </Pressable>
      </View>

      {children.length > 1 ? <ChildSwitcherBar /> : null}
    </View>
  );
}

function ParentLayoutContent() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { me, loading } = useAuth();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();

  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "parent") return <Redirect href={`/(${me.user.role})/dashboard`} />;

  return (
    <View style={{ flex: 1, backgroundColor: theme.ground }}>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: theme.primary,
          tabBarInactiveTintColor: theme.inkFaint,
          tabBarLabelStyle: { fontSize: 10.5, fontWeight: "700", letterSpacing: 0.1 },
          tabBarStyle: {
            backgroundColor: theme.surface,
            borderTopWidth: 1,
            borderTopColor: theme.rule,
            height: 60 + (insets.bottom > 0 ? insets.bottom - 4 : 0),
            paddingBottom: insets.bottom > 0 ? insets.bottom : 6,
            paddingTop: 6,
            ...theme.shadow.subtle,
          },
          header: ({ options, route }) => (
            <ParentCustomHeader
              title={(options.title as string) ?? route.name}
              onOpenDrawer={() => setDrawerOpen(true)}
            />
          ),
        }}
      >
        {/* Strictly 4 Visible Bottom Tabs */}
        <Tabs.Screen
          name="dashboard"
          options={{ title: t("nav_home"), tabBarIcon: tabIcon("home-outline") }}
        />
        <Tabs.Screen
          name="child"
          options={{ title: t("nav_child"), tabBarIcon: tabIcon("person-circle-outline") }}
        />
        <Tabs.Screen
          name="fees"
          options={{ title: t("nav_fees"), tabBarIcon: tabIcon("card-outline") }}
        />
        <Tabs.Screen
          name="profile"
          options={{ title: t("nav_profile"), tabBarIcon: tabIcon("person-outline") }}
        />

        {/* Hidden Stack Routes - accessible via Drawer and router.push */}
        <Tabs.Screen
          name="timetable"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_timetable") }}
        />
        <Tabs.Screen
          name="attendance"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_attendance") }}
        />
        <Tabs.Screen
          name="homework"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_homework") }}
        />
        <Tabs.Screen
          name="results"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_results") }}
        />
        <Tabs.Screen
          name="grievances"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_grievances") }}
        />
        <Tabs.Screen
          name="notices"
          options={{ tabBarItemStyle: { display: "none" }, title: t("nav_notices") }}
        />
        <Tabs.Screen
          name="hostel"
          options={{ tabBarItemStyle: { display: "none" }, title: "Hostel & Mess" }}
        />
      </Tabs>

      {/* Hamburger Navigation Drawer */}
      <NavDrawer visible={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </View>
  );
}

export default function ParentLayout() {
  return (
    <I18nProvider>
      <ParentLayoutContent />
    </I18nProvider>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    backgroundColor: theme.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
    ...theme.shadow.subtle,
  },
  headerRow: {
    height: 52,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
  },
  headerIconBtn: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: theme.groundAlt,
    justifyContent: "center",
    alignItems: "center",
  },
  notificationDot: {
    position: "absolute",
    top: 7,
    right: 7,
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: theme.danger,
    borderWidth: 1.5,
    borderColor: theme.surface,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: theme.ink,
    letterSpacing: -0.3,
    textAlign: "center",
  },
  childBar: {
    paddingBottom: 10,
    paddingTop: 4,
  },
  childChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: theme.radius.pill,
  },
  childChipActive: {
    backgroundColor: theme.primary,
    ...theme.shadow.button,
  },
  childChipInactive: {
    backgroundColor: theme.groundAlt,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
  },
  childChipText: {
    fontSize: 12,
  },
  childChipTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  childChipTextInactive: {
    color: theme.inkSoft,
    fontWeight: "600",
  },
});
