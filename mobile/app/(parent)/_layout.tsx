import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, Tabs } from "expo-router";
import React, { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../../src/auth/AuthContext";
import { NavDrawer } from "../../src/components/NavDrawer";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

/** Horizontal child switcher chips rendered when parent has 2+ children. */
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
                { backgroundColor: on ? theme.primary : theme.ground },
              ]}
            >
              <Text
                style={{
                  fontSize: 12,
                  fontWeight: on ? "600" : "400",
                  color: on ? "#fff" : theme.inkSoft,
                }}
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
          style={styles.hamburgerBtn}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          accessibilityRole="button"
          accessibilityLabel="Open Menu"
        >
          <Ionicons name="menu-outline" size={26} color={theme.ink} />
        </Pressable>

        <Text style={styles.headerTitle}>{title}</Text>

        {/* Balance layout with right-aligned spacer */}
        <View style={styles.headerRightSpacer} />
      </View>

      {children.length > 1 ? <ChildSwitcherBar /> : null}
    </View>
  );
}

export default function ParentLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { me, loading } = useAuth();

  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "parent") return <Redirect href={`/(${me.user.role})/dashboard`} />;

  return (
    <View style={{ flex: 1 }}>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: theme.primary,
          tabBarInactiveTintColor: theme.inkFaint,
          tabBarLabelStyle: { fontSize: 10, fontWeight: "600" },
          tabBarStyle: { backgroundColor: theme.surface },
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
          options={{ title: "Home", tabBarIcon: tabIcon("home-outline") }}
        />
        <Tabs.Screen
          name="child"
          options={{ title: "Child", tabBarIcon: tabIcon("person-circle-outline") }}
        />
        <Tabs.Screen
          name="fees"
          options={{ title: "Fees", tabBarIcon: tabIcon("card-outline") }}
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
          name="homework"
          options={{ href: null, title: "Homework" }}
        />
        <Tabs.Screen
          name="results"
          options={{ href: null, title: "Results" }}
        />
        <Tabs.Screen
          name="grievances"
          options={{ href: null, title: "Grievances" }}
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

const styles = StyleSheet.create({
  headerContainer: {
    backgroundColor: theme.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  headerRow: {
    height: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
  },
  hamburgerBtn: {
    padding: 4,
    justifyContent: "center",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: theme.ink,
    textAlign: "center",
  },
  headerRightSpacer: {
    width: 34,
  },
  childBar: {
    paddingBottom: 8,
  },
  childChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: theme.radius.pill,
  },
});
