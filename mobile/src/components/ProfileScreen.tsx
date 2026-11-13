import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { theme } from "../theme";
import { Button, Card, Loading, Row, Screen, s } from "./ui";

/** Shared by teacher and student roles: profile fields, change password, logout. */
export function ProfileScreen({
  path,
  fields,
}: {
  path: string;
  /** [label, key] pairs read from the profile payload. */
  fields: [string, string][];
}) {
  const router = useRouter();
  const { me, logout } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [note, setNote] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["profile", path],
    queryFn: () => api.get<Record<string, unknown>>(path),
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

  const fullName = String(data.full_name || me?.user.full_name || "User");
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <Screen>
      {/* Top Identity Card */}
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
            <View style={{ flexDirection: "row", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
              <View
                style={{
                  paddingHorizontal: 8,
                  paddingVertical: 2,
                  borderRadius: theme.radius.pill,
                  backgroundColor: theme.primarySoft,
                }}
              >
                <Text style={{ fontSize: 11, fontWeight: "700", color: theme.primary, textTransform: "capitalize" }}>
                  {me?.user.role || "Member"}
                </Text>
              </View>
              {data.admission_no ? (
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
                    Adm #{String(data.admission_no)}
                  </Text>
                </View>
              ) : null}
              {data.employee_id ? (
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
                    Emp #{String(data.employee_id)}
                  </Text>
                </View>
              ) : null}
            </View>
          </View>
        </View>
      </Card>

      {/* Details Card */}
      <Card title="Account Details">
        {fields.map(([label, key]) => (
          <Row
            key={key}
            left={<Text style={s.meta}>{label}</Text>}
            right={<Text style={s.title}>{show(data[key])}</Text>}
          />
        ))}
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

      {/* Sign Out Card / Action */}
      <View style={{ marginTop: 8, marginBottom: 20 }}>
        <Button
          label="Sign Out"
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
