import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth, type Role } from "../src/auth/AuthContext";
import { Button, Loading, s } from "../src/components/ui";
import { theme } from "../src/theme";

/**
 * Demo login ids and role-specific passwords from backend/seed.py (DEMO_PASSWORDS).
 * Student: 2024000001 / Student@123
 * Parent: 9876500001 / Parent@123
 * Teacher: TCH001 / Teacher@123
 */
const DEMO: Record<Role, { loginId: string; hint: string; defaultPassword: string }> = {
  student: { loginId: "2024000001", hint: "Admission number", defaultPassword: "Student@123" },
  parent: { loginId: "9876500001", hint: "Registered mobile number", defaultPassword: "Parent@123" },
  teacher: { loginId: "TCH001", hint: "Employee ID", defaultPassword: "Teacher@123" },
};

const ROLES: Role[] = ["student", "parent", "teacher"];

export default function Login() {
  const router = useRouter();
  const { me, loading, login } = useAuth();
  const [role, setRole] = useState<Role>("student");
  const [loginId, setLoginId] = useState(DEMO.student.loginId);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return <Loading />;
  if (me) return <Redirect href={`/(${me.user.role})/dashboard`} />;

  const pickRole = (next: Role) => {
    setRole(next);
    setLoginId(DEMO[next].loginId);
    setPassword("");
    setShowPassword(false);
    setError(null);
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await login(role, loginId.trim(), password);
      // Imperative router replace ensures immediate transition
      router.replace(`/(${role})/dashboard` as any);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.ground }}>
      <ScrollView contentContainerStyle={{ padding: 20, gap: 16, flexGrow: 1, justifyContent: "center" }}>
        <View style={{ gap: 4 }}>
          <Text style={{ fontSize: 22, fontWeight: "700", color: theme.ink }}>
            Sunrise Public School
          </Text>
          <Text style={{ color: theme.inkSoft }}>Sign in to continue</Text>
        </View>

        <View style={{ flexDirection: "row", gap: 8 }}>
          {ROLES.map((r) => (
            <Pressable
              key={r}
              onPress={() => pickRole(r)}
              style={{
                flex: 1,
                paddingVertical: 10,
                borderRadius: theme.radius.input,
                alignItems: "center",
                backgroundColor: role === r ? theme.primary : theme.surface,
                borderWidth: 1,
                borderColor: role === r ? theme.primary : theme.rule,
              }}
            >
              <Text
                style={{
                  color: role === r ? "#fff" : theme.inkSoft,
                  fontWeight: "600",
                  textTransform: "capitalize",
                }}
              >
                {r}
              </Text>
            </Pressable>
          ))}
        </View>

        <View style={{ gap: 10 }}>
          <Text style={s.meta}>{DEMO[role].hint}</Text>
          <TextInput
            style={s.input}
            value={loginId}
            onChangeText={setLoginId}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              borderWidth: 1,
              borderColor: theme.rule,
              borderRadius: theme.radius.input,
              backgroundColor: theme.surface,
            }}
          >
            <TextInput
              style={{
                flex: 1,
                padding: 12,
                fontSize: 14,
                color: theme.ink,
              }}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              placeholder={`Password (${DEMO[role].defaultPassword})`}
              placeholderTextColor={theme.inkFaint}
            />
            <Pressable
              onPress={() => setShowPassword((prev) => !prev)}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              style={{
                paddingRight: 12,
                paddingLeft: 4,
                justifyContent: "center",
                alignItems: "center",
              }}
              accessibilityLabel={showPassword ? "Hide password" : "Show password"}
              accessibilityRole="button"
            >
              <Ionicons
                name={showPassword ? "eye-outline" : "eye-off-outline"}
                size={20}
                color={theme.inkSoft}
              />
            </Pressable>
          </View>
          <Pressable
            onPress={() => setPassword(DEMO[role].defaultPassword)}
            hitSlop={{ top: 8, bottom: 8 }}
          >
            <Text style={{ fontSize: 12, color: theme.primary, fontWeight: "600" }}>
              Auto-fill demo password ({DEMO[role].defaultPassword})
            </Text>
          </Pressable>
        </View>

        {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}

        <Button label={busy ? "Signing in..." : "Sign in"} onPress={submit} disabled={busy} />

        <View style={{ gap: 4, marginTop: 4 }}>
          <Text style={[s.meta, { fontWeight: "600" }]}>Demo Accounts (Tap to auto-fill)</Text>
          {ROLES.map((r) => (
            <Pressable
              key={r}
              onPress={() => {
                pickRole(r);
                setPassword(DEMO[r].defaultPassword);
              }}
              style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 3 }}
            >
              <Text style={s.meta}>
                {r}: <Text style={{ color: theme.ink, fontWeight: "500" }}>{DEMO[r].loginId}</Text>
              </Text>
              <Text style={[s.meta, { color: theme.primary, fontWeight: "600" }]}>
                {DEMO[r].defaultPassword}
              </Text>
            </Pressable>
          ))}
          <Text style={[s.meta, { marginTop: 6 }]}>
            Admin signs in on the web dashboard, not this app.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
