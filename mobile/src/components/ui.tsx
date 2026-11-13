import Ionicons from "@expo/vector-icons/Ionicons";
import type { ReactNode } from "react";
import {
  ActivityIndicator,
  ColorValue,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from "react-native";

import { statusBg, statusColor, theme } from "../theme";

/** Without an explicit icon, the tab bar renders a missing-glyph box. */
export const tabIcon =
  (name: React.ComponentProps<typeof Ionicons>["name"]) =>
  ({ color, size }: { color: ColorValue; size: number }) => (
    <Ionicons name={name} color={color as string} size={size} />
  );

export function Screen({
  children,
  style,
  contentContainerStyle,
}: {
  children: ReactNode;
  style?: ViewStyle;
  contentContainerStyle?: ViewStyle;
}) {
  return (
    <ScrollView
      style={[s.screen, style]}
      contentContainerStyle={[s.screenContent, contentContainerStyle]}
      showsVerticalScrollIndicator={false}
    >
      {children}
    </ScrollView>
  );
}

export function Card({
  title,
  subtitle,
  rightAction,
  icon,
  style,
  children,
}: {
  title?: string;
  subtitle?: string;
  rightAction?: ReactNode;
  icon?: keyof typeof Ionicons.glyphMap;
  style?: ViewStyle;
  children: ReactNode;
}) {
  return (
    <View style={[s.card, style]}>
      {title || rightAction ? (
        <View style={s.cardHeader}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 10, flex: 1 }}>
            {icon ? (
              <View style={s.cardIconBox}>
                <Ionicons name={icon} size={18} color={theme.primary} />
              </View>
            ) : null}
            <View style={{ flex: 1 }}>
              {title ? <Text style={s.cardTitle}>{title}</Text> : null}
              {subtitle ? <Text style={s.cardSubtitle}>{subtitle}</Text> : null}
            </View>
          </View>
          {rightAction ? <View>{rightAction}</View> : null}
        </View>
      ) : null}
      {children}
    </View>
  );
}

export function Stat({
  label,
  value,
  subvalue,
  status,
}: {
  label: string;
  value: ReactNode;
  subvalue?: string;
  status?: string;
}) {
  const dotColor = status ? statusColor[status] ?? theme.inkFaint : undefined;
  return (
    <View style={s.stat}>
      <Text style={s.statLabel}>{label}</Text>
      <Text style={s.statValue}>{value}</Text>
      {subvalue ? (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 5, marginTop: 4 }}>
          {dotColor ? <View style={[s.statusDot, { backgroundColor: dotColor }]} /> : null}
          <Text style={[s.statSubvalue, dotColor ? { color: dotColor } : null]}>{subvalue}</Text>
        </View>
      ) : null}
    </View>
  );
}

export function Pill({
  status,
  label,
  showDot = true,
}: {
  status?: string;
  label: string;
  showDot?: boolean;
}) {
  const color = status ? (statusColor[status] ?? theme.inkSoft) : theme.inkSoft;
  const bg = status ? (statusBg[status] ?? `${color}14`) : `${color}14`;
  return (
    <View style={[s.pill, { backgroundColor: bg }]}>
      {showDot ? <View style={[s.statusDot, { backgroundColor: color }]} /> : null}
      <Text style={[s.pillText, { color }]}>{label}</Text>
    </View>
  );
}

export function Row({
  left,
  right,
  border = true,
}: {
  left: ReactNode;
  right?: ReactNode;
  border?: boolean;
}) {
  return (
    <View style={[s.row, !border && { borderBottomWidth: 0 }]}>
      <View style={{ flex: 1, minWidth: 0 }}>{left}</View>
      {right ? <View style={{ flexShrink: 1, alignItems: "flex-end" }}>{right}</View> : null}
    </View>
  );
}

export function Empty({
  text,
  icon,
}: {
  text: string;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  return (
    <View style={s.emptyContainer}>
      {icon ? (
        <View style={s.emptyIconBox}>
          <Ionicons name={icon} size={28} color={theme.inkFaint} />
        </View>
      ) : null}
      <Text style={s.empty}>{text}</Text>
    </View>
  );
}

export function Loading() {
  return (
    <View style={{ paddingVertical: 40, alignItems: "center" }}>
      <ActivityIndicator size="small" color={theme.primary} />
    </View>
  );
}

export function Button({
  label,
  onPress,
  disabled,
  tone = "primary",
  icon,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  tone?: "primary" | "ghost" | "danger";
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  const isPrimary = tone === "primary";
  const isDanger = tone === "danger";
  const isGhost = tone === "ghost";

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        s.button,
        isPrimary && s.buttonPrimary,
        isGhost && s.buttonGhost,
        isDanger && s.buttonDanger,
        disabled && { opacity: 0.5 },
        pressed && !disabled && { transform: [{ scale: 0.985 }] },
      ]}
    >
      {icon ? (
        <Ionicons
          name={icon}
          size={16}
          color={isPrimary ? "#fff" : isDanger ? theme.danger : theme.primary}
          style={{ marginRight: 6 }}
        />
      ) : null}
      <Text
        style={[
          s.buttonText,
          isGhost && { color: theme.primary },
          isDanger && { color: theme.danger },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

export const s = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.ground,
  },
  screenContent: {
    padding: 16,
    gap: 14,
    paddingBottom: 48,
  },
  card: {
    backgroundColor: theme.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.rule,
    padding: 16,
    gap: 12,
    ...theme.shadow.card,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: 4,
  },
  cardIconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: theme.primarySoft,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    fontWeight: "700",
    fontSize: 15,
    letterSpacing: -0.2,
    color: theme.ink,
  },
  cardSubtitle: {
    fontSize: 11,
    color: theme.inkFaint,
    marginTop: 1,
  },
  stat: {
    flex: 1,
    gap: 2,
    paddingRight: 8,
  },
  statLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.inkFaint,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  statValue: {
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: -0.5,
    color: theme.ink,
    fontVariant: ["tabular-nums"],
  },
  statSubvalue: {
    fontSize: 11,
    fontWeight: "600",
    color: theme.inkSoft,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderRadius: theme.radius.pill,
    paddingHorizontal: 9,
    paddingVertical: 3.5,
    alignSelf: "flex-start",
  },
  pillText: {
    fontSize: 10.5,
    fontWeight: "700",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: theme.rule,
  },
  emptyContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 24,
    gap: 8,
  },
  emptyIconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: theme.groundAlt,
    alignItems: "center",
    justifyContent: "center",
  },
  empty: {
    color: theme.inkFaint,
    fontSize: 13,
    textAlign: "center",
  },
  button: {
    flexDirection: "row",
    borderRadius: theme.radius.input,
    paddingVertical: 13,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  buttonPrimary: {
    backgroundColor: theme.primary,
    ...theme.shadow.button,
  },
  buttonGhost: {
    backgroundColor: theme.primarySoft,
  },
  buttonDanger: {
    backgroundColor: theme.dangerBg,
  },
  buttonText: {
    color: "#fff",
    fontSize: 13.5,
    fontWeight: "700",
    letterSpacing: 0.1,
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: -0.2,
    color: theme.ink,
  },
  meta: {
    fontSize: 12,
    color: theme.inkSoft,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.ruleStrong,
    borderRadius: theme.radius.input,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    color: theme.ink,
    backgroundColor: theme.surface,
  },
});
