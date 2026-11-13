import Ionicons from "@expo/vector-icons/Ionicons";
import { Redirect, useRouter } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth, type Role } from "../src/auth/AuthContext";
import { Loading } from "../src/components/ui";
import { theme } from "../src/theme";

/**
 * Demo login ids and role-specific passwords from backend/seed.py (DEMO_PASSWORDS).
 * Student: 2024000001 / Student@123
 * Parent: 9876500001 / Parent@123
 * Teacher: TCH001 / Teacher@123
 */
const DEMO: Record<
  Role,
  { loginId: string; hint: string; defaultPassword: string; icon: keyof typeof Ionicons.glyphMap }
> = {
  student: {
    loginId: "2024000001",
    hint: "Admission number",
    defaultPassword: "Student@123",
    icon: "school-outline",
  },
  parent: {
    loginId: "9876500001",
    hint: "Registered mobile number",
    defaultPassword: "Parent@123",
    icon: "call-outline",
  },
  teacher: {
    loginId: "TCH001",
    hint: "Teacher ID",
    defaultPassword: "Teacher@123",
    icon: "briefcase-outline",
  },
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
  const [isWarmingUp, setIsWarmingUp] = useState(false);

  if (loading) return <Loading />;
  if (me) return <Redirect href={`/(${me.user.role})/dashboard`} />;

  const pickRole = (next: Role) => {
    setRole(next);
    setLoginId(DEMO[next].loginId);
    setPassword("");
    setShowPassword(false);
    setError(null);
    setIsWarmingUp(false);
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    setIsWarmingUp(false);
    const warmTimer = setTimeout(() => {
      setIsWarmingUp(true);
    }, 4000);
    try {
      await login(role, loginId.trim(), password);
      router.replace(`/(${role})/dashboard` as any);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid credentials. Please verify and try again.");
    } finally {
      clearTimeout(warmTimer);
      setBusy(false);
      setIsWarmingUp(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Brand Identity Header */}
          <View style={styles.header}>
            <View style={styles.crestWrapper}>
              <View style={styles.crestContainer}>
                <Ionicons name="shield-checkmark" size={26} color="#FFFFFF" />
              </View>
            </View>
            <Text style={styles.schoolName}>Sunrise Public School</Text>
            <Text style={styles.tagline}>Sign in to continue</Text>
          </View>

          {/* User Role Segmented Tab Selector */}
          <View style={styles.segmentedTrack}>
            {ROLES.map((r) => {
              const active = role === r;
              return (
                <Pressable
                  key={r}
                  onPress={() => pickRole(r)}
                  style={[styles.roleTab, active && styles.roleTabActive]}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: active }}
                >
                  <Text style={[styles.roleTabText, active && styles.roleTabTextActive]}>
                    {r}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* Authentication Form */}
          <View style={styles.formContainer}>
            {/* Field 1: Identification Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.fieldLabel}>{DEMO[role].hint}</Text>
              <View style={styles.inputWrapper}>
                <TextInput
                  style={styles.textInput}
                  value={loginId}
                  onChangeText={setLoginId}
                  autoCapitalize="none"
                  autoCorrect={false}
                  placeholder={DEMO[role].hint}
                  placeholderTextColor={theme.inkFaint}
                />
                <View style={styles.inputIconBox}>
                  <Ionicons name={DEMO[role].icon} size={18} color={theme.inkFaint} />
                </View>
              </View>
            </View>

            {/* Field 2: Password Input */}
            <View style={styles.inputGroup}>
              <Text style={styles.fieldLabel}>Password</Text>
              <View style={styles.inputWrapper}>
                <TextInput
                  style={[styles.textInput, { paddingRight: 44 }]}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  placeholder={`Password (${DEMO[role].defaultPassword})`}
                  placeholderTextColor={theme.inkFaint}
                />
                <Pressable
                  onPress={() => setShowPassword((prev) => !prev)}
                  hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                  style={styles.eyeIconButton}
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

            {/* Demo Password Auto-fill Link */}
            <Pressable
              onPress={() => setPassword(DEMO[role].defaultPassword)}
              hitSlop={{ top: 8, bottom: 8 }}
              style={styles.autofillLink}
            >
              <Ionicons name="flash-outline" size={14} color={theme.primary} />
              <Text style={styles.autofillText}>
                Auto-fill demo password ({DEMO[role].defaultPassword})
              </Text>
            </Pressable>

            {/* Server Warming Notice (Screen 19) */}
            {isWarmingUp && !error ? (
              <View style={styles.warmBanner}>
                <Ionicons name="cloud-outline" size={18} color={theme.primary} />
                <Text style={styles.warmText}>
                  Connecting to server... Cloud backend is waking from standby (Render cold start).
                </Text>
              </View>
            ) : null}

            {/* Validation Error Banner (Screen 19) */}
            {error ? (
              <View style={styles.errorBanner}>
                <Ionicons name="alert-circle" size={18} color={theme.danger} />
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}

            {/* Primary Action Button */}
            <Pressable
              onPress={submit}
              disabled={busy}
              style={({ pressed }) => [
                styles.submitButton,
                busy && { opacity: 0.7 },
                pressed && !busy && { transform: [{ scale: 0.985 }] },
              ]}
            >
              <Text style={styles.submitButtonText}>
                {busy ? "Signing in..." : "Sign in"}
              </Text>
              <Ionicons name="arrow-forward" size={17} color="#FFFFFF" />
            </Pressable>
          </View>

          {/* Demo Accounts Card */}
          <View style={styles.demoCard}>
            <View style={styles.demoHeader}>
              <Text style={styles.demoTitle}>DEMO ACCOUNTS (TAP TO AUTO-FILL)</Text>
              <View style={styles.quickFillPill}>
                <Text style={styles.quickFillText}>Quick Fill</Text>
              </View>
            </View>

            <View style={styles.demoRows}>
              {ROLES.map((r, i) => (
                <Pressable
                  key={r}
                  onPress={() => {
                    pickRole(r);
                    setPassword(DEMO[r].defaultPassword);
                  }}
                  style={[
                    styles.demoRow,
                    i < ROLES.length - 1 && styles.demoRowBorder,
                  ]}
                >
                  <Text style={styles.demoRowLabel}>
                    <Text style={{ color: theme.inkFaint }}>{r}: </Text>
                    <Text style={{ color: theme.ink, fontWeight: "600" }}>
                      {DEMO[r].loginId}
                    </Text>
                  </Text>
                  <Text style={styles.demoRowPassword}>{DEMO[r].defaultPassword}</Text>
                </Pressable>
              ))}
            </View>
          </View>

          {/* Footer Note */}
          <Text style={styles.footerNote}>
            Admin signs in on the web dashboard, not this app.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: theme.ground,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
    flexGrow: 1,
    justifyContent: "center",
    maxWidth: 440,
    alignSelf: "center",
    width: "100%",
  },
  header: {
    alignItems: "flex-start",
    marginBottom: 20,
  },
  crestWrapper: {
    padding: 3,
    borderRadius: 20,
    backgroundColor: theme.primarySoft,
    marginBottom: 14,
  },
  crestContainer: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: theme.primary,
    alignItems: "center",
    justifyContent: "center",
    ...theme.shadow.button,
  },
  schoolName: {
    fontSize: 23,
    fontWeight: "800",
    letterSpacing: -0.5,
    color: theme.ink,
    lineHeight: 28,
  },
  tagline: {
    fontSize: 14,
    fontWeight: "500",
    color: theme.inkSoft,
    marginTop: 3,
  },
  segmentedTrack: {
    flexDirection: "row",
    backgroundColor: "#EBEFF5",
    borderRadius: 16,
    padding: 4,
    gap: 4,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
    marginBottom: 18,
  },
  roleTab: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  roleTabActive: {
    backgroundColor: theme.primary,
    ...theme.shadow.subtle,
  },
  roleTabText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
    textTransform: "capitalize",
    letterSpacing: 0.2,
  },
  roleTabTextActive: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
  formContainer: {
    gap: 14,
  },
  inputGroup: {
    gap: 6,
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.inkSoft,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  inputWrapper: {
    position: "relative",
    justifyContent: "center",
  },
  textInput: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.ruleStrong,
    borderRadius: 14,
    paddingHorizontal: 15,
    paddingVertical: 13,
    fontSize: 14,
    color: theme.ink,
    fontWeight: "500",
    ...theme.shadow.subtle,
  },
  inputIconBox: {
    position: "absolute",
    right: 14,
  },
  eyeIconButton: {
    position: "absolute",
    right: 12,
    padding: 4,
  },
  autofillLink: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  autofillText: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.primary,
  },
  warmBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: theme.primarySoft,
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.2)",
    borderRadius: 12,
    padding: 12,
  },
  warmText: {
    flex: 1,
    fontSize: 12.5,
    color: theme.primary,
    fontWeight: "600",
    lineHeight: 17,
  },
  errorBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: theme.dangerBg,
    borderWidth: 1,
    borderColor: "rgba(225, 29, 72, 0.25)",
    borderRadius: 12,
    padding: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 12.5,
    color: theme.danger,
    fontWeight: "600",
    lineHeight: 17,
  },
  submitButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: theme.primary,
    borderRadius: 16,
    paddingVertical: 14,
    marginTop: 4,
    ...theme.shadow.button,
  },
  submitButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  demoCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: 16,
    padding: 14,
    marginTop: 18,
    ...theme.shadow.card,
  },
  demoHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  demoTitle: {
    fontSize: 10.5,
    fontWeight: "700",
    color: theme.inkFaint,
    letterSpacing: 0.5,
  },
  quickFillPill: {
    backgroundColor: theme.primarySoft,
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  quickFillText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.primary,
  },
  demoRows: {
    paddingTop: 4,
  },
  demoRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 9,
  },
  demoRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  demoRowLabel: {
    fontSize: 12.5,
    color: theme.inkSoft,
  },
  demoRowPassword: {
    fontSize: 12.5,
    fontWeight: "700",
    color: theme.primary,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
  },
  footerNote: {
    fontSize: 11,
    color: theme.inkFaint,
    textAlign: "center",
    marginTop: 14,
    fontWeight: "500",
  },
});
