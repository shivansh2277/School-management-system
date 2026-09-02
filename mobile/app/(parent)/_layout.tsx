import { Redirect, Tabs } from "expo-router";
import { Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../../src/auth/AuthContext";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

/** The switcher only appears when there is more than one child to switch between. */
function ChildSwitcher() {
  const { me, selectedChildId, selectChild } = useAuth();
  const insets = useSafeAreaInsets();
  const children = me?.children ?? [];
  if (children.length < 2) return null;

  return (
    // This replaces the default header, so it has to inset past the status bar
    // itself — otherwise the chips render under the system clock.
    <View
      style={{
        backgroundColor: theme.surface,
        paddingTop: insets.top + 8,
        paddingBottom: 8,
      }}
    >
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingHorizontal: 12 }}>
        {children.map((c) => {
          const on = c.id === selectedChildId;
          return (
            <Pressable
              key={c.id}
              onPress={() => selectChild(c.id)}
              style={{
                paddingHorizontal: 14,
                paddingVertical: 7,
                borderRadius: theme.radius.pill,
                backgroundColor: on ? theme.primary : theme.ground,
              }}
            >
              <Text style={{ fontSize: 12, color: on ? "#fff" : theme.inkSoft }}>
                {c.name} ({c.class_label})
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

export default function ParentLayout() {
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
          tabBarLabelStyle: { fontSize: 10 },
          headerStyle: { backgroundColor: theme.surface },
          tabBarStyle: { backgroundColor: theme.surface },
          header: () => <ChildSwitcher />,
          headerShown: (me.children?.length ?? 0) > 1,
        }}
      >
        <Tabs.Screen name="dashboard" options={{ title: "Home" , tabBarIcon: tabIcon("home-outline") }} />
        <Tabs.Screen name="child" options={{ title: "Child" , tabBarIcon: tabIcon("person-circle-outline") }} />
        <Tabs.Screen name="attendance" options={{ title: "Attendance" , tabBarIcon: tabIcon("checkbox-outline") }} />
        <Tabs.Screen name="homework" options={{ title: "Homework" , tabBarIcon: tabIcon("book-outline") }} />
        <Tabs.Screen name="results" options={{ title: "Results" , tabBarIcon: tabIcon("school-outline") }} />
        <Tabs.Screen name="fees" options={{ title: "Fees" , tabBarIcon: tabIcon("card-outline") }} />
        <Tabs.Screen name="notices" options={{ title: "Notices" , tabBarIcon: tabIcon("notifications-outline") }} />
        <Tabs.Screen name="profile" options={{ title: "Profile" , tabBarIcon: tabIcon("person-outline") }} />
      </Tabs>
    </View>
  );
}
