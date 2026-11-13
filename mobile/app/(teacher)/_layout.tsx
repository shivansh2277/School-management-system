import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, Tabs } from "expo-router";
import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../../src/auth/AuthContext";
import { NavDrawer } from "../../src/components/NavDrawer";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

function TeacherCustomHeader({
  title,
  onOpenDrawer,
}: {
  title: string;
  onOpenDrawer: () => void;
}) {
  const insets = useSafeAreaInsets();

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
    </View>
  );
}

export default function TeacherLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { me, loading } = useAuth();
  const insets = useSafeAreaInsets();

  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "teacher") return <Redirect href={`/(${me.user.role})/dashboard`} />;

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
            <TeacherCustomHeader
              title={(options.title as string) ?? route.name}
              onOpenDrawer={() => setDrawerOpen(true)}
            />
          ),
        }}
      >
        {/* Strictly 4 Visible Bottom Tabs */}
        <Tabs.Screen
          name="dashboard"
          options={{ title: "Home", tabBarIcon: tabIcon("home-outline") }}
        />
        <Tabs.Screen
          name="classes"
          options={{ title: "Classes", tabBarIcon: tabIcon("people-outline") }}
        />
        <Tabs.Screen
          name="attendance"
          options={{ title: "Attendance", tabBarIcon: tabIcon("checkbox-outline") }}
        />
        <Tabs.Screen
          name="profile"
          options={{ title: "Profile", tabBarIcon: tabIcon("person-outline") }}
        />

        {/* Hidden Stack Routes - accessible via Drawer and router.push */}
        <Tabs.Screen
          name="homework"
          options={{ tabBarItemStyle: { display: "none" }, title: "Homework" }}
        />
        <Tabs.Screen
          name="stock"
          options={{ tabBarItemStyle: { display: "none" }, title: "Supplies" }}
        />
        <Tabs.Screen
          name="grievances"
          options={{ tabBarItemStyle: { display: "none" }, title: "Grievances" }}
        />
        <Tabs.Screen
          name="results"
          options={{ tabBarItemStyle: { display: "none" }, title: "Results" }}
        />
        <Tabs.Screen
          name="announcements"
          options={{ tabBarItemStyle: { display: "none" }, title: "Notices" }}
        />
        <Tabs.Screen
          name="timetable"
          options={{ tabBarItemStyle: { display: "none" }, title: "Timetable" }}
        />
        <Tabs.Screen
          name="leave"
          options={{ tabBarItemStyle: { display: "none" }, title: "Leaves" }}
        />
      </Tabs>

      {/* Hamburger Navigation Drawer */}
      <NavDrawer visible={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </View>
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
    backgroundColor: theme.primary,
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
});
