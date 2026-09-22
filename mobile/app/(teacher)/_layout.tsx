import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, Tabs } from "expo-router";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { useAuth } from "../../src/auth/AuthContext";
import { NavDrawer } from "../../src/components/NavDrawer";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

export default function TeacherLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { me, loading } = useAuth();

  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "teacher") return <Redirect href={`/(${me.user.role})/dashboard`} />;

  return (
    <View style={{ flex: 1 }}>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: theme.primary,
          tabBarInactiveTintColor: theme.inkFaint,
          tabBarLabelStyle: { fontSize: 10, fontWeight: "600" },
          headerStyle: { backgroundColor: theme.surface },
          headerTintColor: theme.ink,
          headerTitleAlign: "center",
          headerTitleStyle: { fontSize: 16, fontWeight: "600" },
          tabBarStyle: { backgroundColor: theme.surface },
          headerLeft: () => (
            <Pressable
              onPress={() => setDrawerOpen(true)}
              style={{ marginLeft: 16, padding: 6 }}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              accessibilityRole="button"
              accessibilityLabel="Open Menu"
            >
              <Ionicons name="menu-outline" size={26} color={theme.ink} />
            </Pressable>
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

        {/* Hidden Stack Routes (href: null) - accessible via Drawer and router.push */}
        <Tabs.Screen
          name="homework"
          options={{ href: null, title: "Homework" }}
        />
        <Tabs.Screen
          name="stock"
          options={{ href: null, title: "Supplies" }}
        />
        <Tabs.Screen
          name="grievances"
          options={{ href: null, title: "Grievances" }}
        />
        <Tabs.Screen
          name="results"
          options={{ href: null, title: "Results" }}
        />
        <Tabs.Screen
          name="announcements"
          options={{ href: null, title: "Notices" }}
        />
        <Tabs.Screen
          name="timetable"
          options={{ href: null, title: "Timetable" }}
        />
        <Tabs.Screen
          name="leave"
          options={{ href: null, title: "Leaves" }}
        />
      </Tabs>

      {/* Hamburger Navigation Drawer */}
      <NavDrawer visible={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </View>
  );
}
