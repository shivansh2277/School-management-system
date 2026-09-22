import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, Tabs } from "expo-router";
import React, { useState } from "react";
import { Pressable, View } from "react-native";

import { useAuth } from "../../src/auth/AuthContext";
import { NavDrawer } from "../../src/components/NavDrawer";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

export default function StudentLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { me, loading } = useAuth();

  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "student") return <Redirect href={`/(${me.user.role})/dashboard`} />;

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
          name="timetable"
          options={{ title: "Timetable", tabBarIcon: tabIcon("calendar-outline") }}
        />
        <Tabs.Screen
          name="homework"
          options={{ title: "Homework", tabBarIcon: tabIcon("book-outline") }}
        />
        <Tabs.Screen
          name="profile"
          options={{ title: "Profile", tabBarIcon: tabIcon("person-outline") }}
        />

        {/* Hidden Stack Routes (href: null) - accessible via Drawer and router.push */}
        <Tabs.Screen
          name="attendance"
          options={{ href: null, title: "Attendance" }}
        />
        <Tabs.Screen
          name="results"
          options={{ href: null, title: "Results" }}
        />
        <Tabs.Screen
          name="notices"
          options={{ href: null, title: "Notices" }}
        />
      </Tabs>

      {/* Hamburger Navigation Drawer */}
      <NavDrawer visible={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </View>
  );
}
