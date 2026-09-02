/** BLUEPRINT section 14 design tokens. mobile/src/theme.ts holds the same values. */
export const theme = {
  primary: "#5B4BE0",
  primaryDark: "#3E2FB5",
  primarySoft: "#EEEBFC",
  ground: "#F6F7FB",
  surface: "#FFFFFF",
  ink: "#1B2333",
  inkSoft: "#5A6478",
  inkFaint: "#8A93A6",
  rule: "#E4E7EF",
  success: "#16A34A",
  warning: "#F59E0B",
  danger: "#EF4444",
  info: "#3B82F6",
} as const;

/** Semantic colour is reserved for state, never decoration. */
export const statusColor: Record<string, string> = {
  present: theme.success,
  paid: theme.success,
  absent: theme.danger,
  overdue: theme.danger,
  leave: theme.warning,
  pending: theme.warning,
};
