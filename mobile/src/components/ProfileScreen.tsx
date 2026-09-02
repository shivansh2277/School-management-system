import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Text, TextInput, View } from "react-native";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { theme } from "../theme";
import { Button, Card, Loading, Row, Screen, s } from "./ui";

/** Shared by all three roles: profile fields, change password, logout. */
export function ProfileScreen({
  path,
  fields,
}: {
  path: string;
  /** [label, key] pairs read from the profile payload. */
  fields: [string, string][];
}) {
  const router = useRouter();
  const { logout } = useAuth();
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
      setNote("Password changed.");
      setOldPassword("");
      setNewPassword("");
    },
    onError: (e: Error) => setNote(e.message),
  });

  if (isLoading || !data) return <Loading />;

  const show = (value: unknown) =>
    value === null || value === undefined || value === "" ? "-" : String(value);

  return (
    <Screen>
      <Card title="Profile">
        {fields.map(([label, key]) => (
          <Row
            key={key}
            left={<Text style={s.meta}>{label}</Text>}
            right={<Text style={s.title}>{show(data[key])}</Text>}
          />
        ))}
      </Card>

      <Card title="Change password">
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
        {note ? <Text style={s.meta}>{note}</Text> : null}
        <Button
          label="Update password"
          onPress={() => change.mutate()}
          disabled={change.isPending || newPassword.length < 8}
        />
      </Card>

      <View style={{ marginTop: 4 }}>
        <Button
          label="Log out"
          tone="ghost"
          onPress={async () => {
            await logout();
            router.replace("/");
          }}
        />
      </View>
    </Screen>
  );
}
