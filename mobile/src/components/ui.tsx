import Ionicons from "@expo/vector-icons/Ionicons";
import type { ReactNode } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { statusColor, theme } from "../theme";

/** Without an explicit icon, the tab bar renders a missing-glyph box. */
export const tabIcon =
  (name: React.ComponentProps<typeof Ionicons>["name"]) =>
  ({ color, size }: { color: string; size: number }) => <Ionicons name={name} color={color} size={size} />;

export function Screen({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={s.screen} contentContainerStyle={s.screenContent}>
      {children}
    </ScrollView>
  );
}

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <View style={s.card}>
      {title ? <Text style={s.cardTitle}>{title}</Text> : null}
      {children}
    </View>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <View style={s.stat}>
      <Text style={s.statLabel}>{label}</Text>
      <Text style={s.statValue}>{value}</Text>
    </View>
  );
}

export function Pill({ status, label }: { status?: string; label: string }) {
  const color = status ? (statusColor[status] ?? theme.inkSoft) : theme.inkSoft;
  return (
    <View style={[s.pill, { backgroundColor: `${color}1A` }]}>
      <Text style={[s.pillText, { color }]}>{label}</Text>
    </View>
  );
}

export function Row({ left, right }: { left: ReactNode; right?: ReactNode }) {
  return (
    <View style={s.row}>
      <View style={{ flex: 1, minWidth: 0 }}>{left}</View>
      {/* shrinkable, so a long value cannot squeeze the label to zero width */}
      {right ? <View style={{ flexShrink: 1, alignItems: "flex-end" }}>{right}</View> : null}
    </View>
  );
}

export function Empty({ text }: { text: string }) {
  return <Text style={s.empty}>{text}</Text>;
}

export function Loading() {
  return <ActivityIndicator style={{ marginTop: 32 }} color={theme.primary} />;
}

export function Button({
  label,
  onPress,
  disabled,
  tone = "primary",
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  tone?: "primary" | "ghost";
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={[
        s.button,
        tone === "ghost" && s.buttonGhost,
        disabled && { opacity: 0.5 },
      ]}
    >
      <Text style={[s.buttonText, tone === "ghost" && { color: theme.primary }]}>{label}</Text>
    </Pressable>
  );
}

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.ground },
  screenContent: { padding: 16, gap: 12, paddingBottom: 40 },
  card: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    padding: 16,
    gap: 10,
  },
  cardTitle: { fontWeight: "600", fontSize: 15, color: theme.ink },
  stat: { flex: 1, gap: 2, paddingRight: 12 },
  statLabel: { fontSize: 12, color: theme.inkFaint },
  statValue: { fontSize: 20, fontWeight: "600", color: theme.ink },
  pill: { borderRadius: theme.radius.pill, paddingHorizontal: 10, paddingVertical: 3 },
  pillText: { fontSize: 11, fontWeight: "600" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: theme.rule,
  },
  empty: { color: theme.inkFaint, fontSize: 13, textAlign: "center", paddingVertical: 16 },
  button: {
    backgroundColor: theme.primary,
    borderRadius: theme.radius.input,
    paddingVertical: 12,
    alignItems: "center",
  },
  buttonGhost: { backgroundColor: theme.primarySoft },
  buttonText: { color: "#fff", fontWeight: "600" },
  title: { fontSize: 16, color: theme.ink },
  meta: { fontSize: 12, color: theme.inkFaint },
  input: {
    borderWidth: 1,
    borderColor: theme.rule,
    borderRadius: theme.radius.input,
    padding: 12,
    fontSize: 14,
    color: theme.ink,
    backgroundColor: theme.surface,
  },
});
