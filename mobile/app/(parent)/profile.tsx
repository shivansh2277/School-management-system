import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Loading, Row, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

export default function ParentProfile() {
  const router = useRouter();
  const { me, logout } = useAuth();
  const { language, setLanguage, t } = useTranslation();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [note, setNote] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["profile", "/parent/profile"],
    queryFn: () => api.get<Record<string, unknown>>("/parent/profile"),
  });

  const change = useMutation({
    mutationFn: () =>
      api.post("/auth/change-password", {
        old_password: oldPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      setNote("Password changed successfully.");
      setOldPassword("");
      setNewPassword("");
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (isLoading || !data) return <Loading />;

  const show = (value: unknown) =>
    value === null || value === undefined || value === "" ? "-" : String(value);

  const fullName = String(data.full_name || me?.user.full_name || "Parent");
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <Screen>
      {/* Guardian Identity Hero Card */}
      <Card>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 28,
              backgroundColor: theme.primarySoft,
              alignItems: "center",
              justifyContent: "center",
              borderWidth: 2,
              borderColor: theme.primary,
            }}
          >
            <Text style={{ fontSize: 20, fontWeight: "800", color: theme.primary }}>{initials}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 18, fontWeight: "800", color: theme.ink }}>{fullName}</Text>
            <View style={{ flexDirection: "row", gap: 6, marginTop: 4 }}>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.primarySoft,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary }}>
                  Parent / Guardian
                </Text>
              </View>
              {data.phone ? (
                <View
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                    borderRadius: theme.radius.pill,
                    backgroundColor: theme.ground,
                    borderWidth: 1,
                    borderColor: theme.rule,
                  }}
                >
                  <Text style={{ fontSize: 11, fontWeight: "600", color: theme.inkSoft }}>
                    {String(data.phone)}
                  </Text>
                </View>
              ) : null}
            </View>
          </View>
        </View>
      </Card>

      {/* Language Preference Card */}
      <Card title={t("prof_app_settings")}>
        <Text style={styles.sectionLabel}>{t("prof_language")}</Text>
        <View style={styles.langPillsRow}>
          <Pressable
            onPress={() => setLanguage("en")}
            style={[styles.langChip, language === "en" && styles.langChipActive]}
          >
            <Text style={[styles.langChipText, language === "en" && styles.langChipTextActive]}>
              {t("prof_lang_en")}
            </Text>
            {language === "en" && <Text style={styles.checkMark}>✓</Text>}
          </Pressable>

          <Pressable
            onPress={() => setLanguage("hi")}
            style={[styles.langChip, language === "hi" && styles.langChipActive]}
          >
            <Text style={[styles.langChipText, language === "hi" && styles.langChipTextActive]}>
              {t("prof_lang_hi")}
            </Text>
            {language === "hi" && <Text style={styles.checkMark}>✓</Text>}
          </Pressable>
        </View>
      </Card>

      {/* Profile Details Card */}
      <Card title={t("prof_guardian_info")}>
        <Row
          left={<Text style={s.meta}>{t("prof_name")}</Text>}
          right={<Text style={s.title}>{show(data.full_name)}</Text>}
        />
        <Row
          left={<Text style={s.meta}>{t("prof_phone")}</Text>}
          right={<Text style={s.title}>{show(data.phone)}</Text>}
        />
        <Row
          left={<Text style={s.meta}>{t("prof_relationship")}</Text>}
          right={<Text style={s.title}>{show(data.occupation || "Guardian")}</Text>}
        />
        <Row
          left={<Text style={s.meta}>{t("nav_child")}</Text>}
          right={<Text style={s.title}>{show(data.children_names)}</Text>}
        />
      </Card>

      {/* Change Password Card */}
      <Card title="Security & Password">
        <TextInput
          style={s.input}
          placeholder="Current password"
          placeholderTextColor={theme.inkFaint}
          secureTextEntry
          value={oldPassword}
          onChangeText={setOldPassword}
        />
        <TextInput
          style={s.input}
          placeholder="New password (min 8 characters)"
          placeholderTextColor={theme.inkFaint}
          secureTextEntry
          value={newPassword}
          onChangeText={setNewPassword}
        />
        {note ? <Text style={[s.meta, { color: theme.primary, fontWeight: "600", marginBottom: 8 }]}>{note}</Text> : null}
        <Button
          label="Update Password"
          onPress={() => change.mutate()}
          disabled={change.isPending || newPassword.length < 8}
        />
      </Card>

      {/* Sign Out Button */}
      <View style={{ marginTop: 8, marginBottom: 20 }}>
        <Button
          label={t("nav_sign_out")}
          tone="danger"
          onPress={async () => {
            await logout();
            router.replace("/");
          }}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: theme.inkSoft,
    marginBottom: 8,
  },
  langPillsRow: {
    flexDirection: "row",
    gap: 8,
  },
  langChip: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: theme.radius.input,
    borderWidth: 1,
    borderColor: theme.rule,
    backgroundColor: theme.surface,
    gap: 6,
  },
  langChipActive: {
    backgroundColor: `${theme.primary}15`,
    borderColor: theme.primary,
  },
  langChipText: {
    fontSize: 13,
    fontWeight: "500",
    color: theme.inkSoft,
  },
  langChipTextActive: {
    fontWeight: "700",
    color: theme.primary,
  },
  checkMark: {
    fontSize: 14,
    color: theme.primary,
    fontWeight: "700",
  },
});
