import Ionicons from "@expo/vector-icons/Ionicons";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { theme } from "../theme";

export type AlertItem = {
  id: string;
  child_id?: number;
  child_name?: string;
  type: "attendance" | "fee" | "report_card" | "periodic_test";
  title: string;
  message: string;
  route?: string | null;
  exam_id?: number;
  event_key?: string;
  amount?: number;
  severity?: "warning" | "danger" | "info";
  icon?: string;
};

interface ImportantAlertsProps {
  alerts?: AlertItem[] | null;
  onAlertPress: (alert: AlertItem) => void;
  sectionTitle?: string;
}

export function ImportantAlerts({
  alerts,
  onAlertPress,
  sectionTitle = "IMPORTANT ALERTS",
}: ImportantAlertsProps) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  const getAlertStyle = (type: AlertItem["type"]) => {
    switch (type) {
      case "attendance":
        return {
          bg: "rgba(245, 158, 11, 0.09)",
          border: "#F59E0B",
          text: "#B45309",
          badgeBg: "#FEF3C7",
          iconName: "alert-circle" as const,
          iconColor: "#D97706",
          emoji: "⚠️",
        };
      case "fee":
        return {
          bg: "rgba(239, 68, 68, 0.09)",
          border: "#EF4444",
          text: "#B91C1C",
          badgeBg: "#FEE2E2",
          iconName: "wallet" as const,
          iconColor: "#DC2626",
          emoji: "💰",
        };
      case "report_card":
        return {
          bg: "rgba(79, 70, 229, 0.09)",
          border: "#6366F1",
          text: "#4338CA",
          badgeBg: "#EEF2FF",
          iconName: "document-text" as const,
          iconColor: "#4F46E5",
          emoji: "📄",
        };
      case "periodic_test":
        return {
          bg: "rgba(2, 132, 199, 0.09)",
          border: "#0284C7",
          text: "#0369A1",
          badgeBg: "#E0F2FE",
          iconName: "ribbon" as const,
          iconColor: "#0284C7",
          emoji: "📊",
        };
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.sectionHeader}>
        <View style={styles.headerLeft}>
          <View style={styles.headerIndicator} />
          <Text style={styles.sectionTitle}>{sectionTitle}</Text>
        </View>
        <View style={styles.countBadge}>
          <Text style={styles.countText}>{alerts.length}</Text>
        </View>
      </View>

      <View style={styles.cardsList}>
        {alerts.map((item) => {
          const style = getAlertStyle(item.type);
          return (
            <Pressable
              key={item.id}
              onPress={() => onAlertPress(item)}
              style={({ pressed }) => [
                styles.alertCard,
                {
                  backgroundColor: style.bg,
                  borderColor: style.border,
                },
                pressed && styles.cardPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel={item.title}
            >
              <View style={styles.cardHeader}>
                <View style={styles.cardHeaderLeft}>
                  <View style={[styles.iconContainer, { backgroundColor: style.badgeBg }]}>
                    <Text style={styles.emojiText}>{style.emoji}</Text>
                  </View>
                  <Text style={[styles.alertTitle, { color: style.text }]} numberOfLines={1}>
                    {item.title}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color={style.border} />
              </View>

              <Text style={styles.alertMessage}>{item.message}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 4,
    marginBottom: 8,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  headerIndicator: {
    width: 3,
    height: 12,
    borderRadius: 2,
    backgroundColor: theme.danger,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.inkSoft,
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  countBadge: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 10,
  },
  countText: {
    fontSize: 10,
    fontWeight: "700",
    color: theme.danger,
  },
  cardsList: {
    gap: 8,
  },
  alertCard: {
    borderRadius: theme.radius.card,
    borderWidth: 1.2,
    padding: 12,
    gap: 6,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cardPressed: {
    opacity: 0.85,
    transform: [{ scale: 0.99 }],
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardHeaderLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flex: 1,
    paddingRight: 6,
  },
  iconContainer: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
  },
  emojiText: {
    fontSize: 13,
  },
  alertTitle: {
    fontSize: 13,
    fontWeight: "700",
    flex: 1,
  },
  alertMessage: {
    fontSize: 12,
    color: theme.ink,
    lineHeight: 17,
    paddingLeft: 34,
  },
});
