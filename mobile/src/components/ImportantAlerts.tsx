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
          bg: theme.warningBg,
          border: "rgba(217, 119, 6, 0.2)",
          text: theme.warning,
          badgeBg: "#FEF3C7",
          iconName: "alert-circle" as const,
          iconColor: theme.warning,
        };
      case "fee":
        return {
          bg: theme.dangerBg,
          border: "rgba(225, 29, 72, 0.2)",
          text: theme.danger,
          badgeBg: "#FFE4E6",
          iconName: "wallet" as const,
          iconColor: theme.danger,
        };
      case "report_card":
        return {
          bg: theme.primarySoft,
          border: "rgba(67, 56, 202, 0.2)",
          text: theme.primary,
          badgeBg: "#E0E7FE",
          iconName: "document-text" as const,
          iconColor: theme.primary,
        };
      case "periodic_test":
        return {
          bg: theme.infoBg,
          border: "rgba(2, 132, 199, 0.2)",
          text: theme.info,
          badgeBg: "#E0F2FE",
          iconName: "ribbon" as const,
          iconColor: theme.info,
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
                    <Ionicons name={style.iconName} size={15} color={style.iconColor} />
                  </View>
                  <Text style={[styles.alertTitle, { color: style.text }]} numberOfLines={1}>
                    {item.title}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color={style.text} />
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
    marginBottom: 8,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 2,
    marginBottom: 8,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  headerIndicator: {
    width: 3.5,
    height: 14,
    borderRadius: 2,
    backgroundColor: theme.danger,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: theme.danger,
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  countBadge: {
    backgroundColor: theme.dangerBg,
    paddingHorizontal: 7,
    paddingVertical: 1.5,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(225, 29, 72, 0.2)",
  },
  countText: {
    fontSize: 10,
    fontWeight: "800",
    color: theme.danger,
  },
  cardsList: {
    gap: 10,
  },
  alertCard: {
    borderRadius: theme.radius.card,
    borderWidth: 1,
    padding: 14,
    gap: 6,
    ...theme.shadow.subtle,
  },
  cardPressed: {
    opacity: 0.88,
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
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  alertTitle: {
    fontSize: 13.5,
    fontWeight: "700",
    flex: 1,
    letterSpacing: -0.2,
  },
  alertMessage: {
    fontSize: 12,
    color: theme.inkSoft,
    lineHeight: 17,
    paddingLeft: 36,
  },
});
