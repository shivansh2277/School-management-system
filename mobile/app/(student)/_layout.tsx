import { Redirect, Tabs } from "expo-router";

import { useAuth } from "../../src/auth/AuthContext";
import { Loading, tabIcon } from "../../src/components/ui";
import { theme } from "../../src/theme";

export default function StudentLayout() {
  const { me, loading } = useAuth();
  if (loading) return <Loading />;
  if (!me) return <Redirect href="/" />;
  if (me.user.role !== "student") return <Redirect href={`/(${me.user.role})/dashboard`} />;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.inkFaint,
        tabBarLabelStyle: { fontSize: 10 },
        headerStyle: { backgroundColor: theme.surface },
        tabBarStyle: { backgroundColor: theme.surface },
      }}
    >
      <Tabs.Screen name="dashboard" options={{ title: "Home" , tabBarIcon: tabIcon("home-outline") }} />
      <Tabs.Screen name="timetable" options={{ title: "Timetable" , tabBarIcon: tabIcon("calendar-outline") }} />
      <Tabs.Screen name="homework" options={{ title: "Homework" , tabBarIcon: tabIcon("book-outline") }} />
      <Tabs.Screen name="attendance" options={{ title: "Attendance" , tabBarIcon: tabIcon("checkbox-outline") }} />
      <Tabs.Screen name="results" options={{ title: "Results" , tabBarIcon: tabIcon("school-outline") }} />
      <Tabs.Screen name="notices" options={{ title: "Notices" , tabBarIcon: tabIcon("notifications-outline") }} />
      <Tabs.Screen name="profile" options={{ title: "Profile" , tabBarIcon: tabIcon("person-outline") }} />
    </Tabs>
  );
}
