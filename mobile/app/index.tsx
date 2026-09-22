import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth, type Role } from "../src/auth/AuthContext";
import { Button, Loading, s } from "../src/components/ui";
import { theme } from "../src/theme";

/**
 * Demo login ids are printed on the login screen so a reviewer gets in
 * unaided. The passwords are not: a password on a login screen is a password
 * in every screenshot of it, and this file is public. They are in the
 * gitignored PASSWORDS.md.
 *
 * `SPS2024001` was prefilled here until 9 September 2026 and had not existed
 * for some time - admission numbers became `YYYY` plus a six-digit counter
 * (ERP_BLUEPRINT section 0.21), so the demo student login was simply wrong.
 */
const DEMO: Record<Role, { loginId: string; hint: string }> = {
  student: { loginId: "2024000001", hint: "Admission number" },
  parent: { loginId: "9876500001", hint: "Registered mobile number" },
  teacher: { loginId: "TCH001", hint: "Employee ID" },
};

const ROLES: Role[] = ["student", "parent", "teacher"];

export default function Login() {
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
              placeholder="Password"
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
        </View>

        {error ? <Text style={{ color: theme.danger }}>{error}</Text> : null}

        <Button label={busy ? "Signing in..." : "Sign in"} onPress={submit} disabled={busy} />

        <View style={{ gap: 2 }}>
          <Text style={s.meta}>Demo accounts</Text>
          {ROLES.map((r) => (
            <Text key={r} style={s.meta}>
              {r}: {DEMO[r].loginId}
            </Text>
          ))}
          <Text style={[s.meta, { marginTop: 6 }]}>
            Admin signs in on the web dashboard, not this app.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
