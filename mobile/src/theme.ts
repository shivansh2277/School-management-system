/**
 * Sunrise EdTech Luxe Design Tokens
 * Master design system aligned with Google Stitch Redesign and DESIGN.md.
 */
export const theme = {
  // Brand Primary & Accents
  primary: "#4338CA",
  primaryHover: "#4F46E5",
  primaryDark: "#3730A3",
  primarySoft: "#EEF2FF",
  primaryContainer: "#4338CA",
  onPrimary: "#FFFFFF",

  // Secondary Iris
  secondary: "#6366F1",
  secondarySoft: "#E0E7FE",
  secondaryContainer: "#6063EE",

  // Neutrals & Surfaces
  ground: "#F8FAFC",
  groundAlt: "#F1F5F9",
  surface: "#FFFFFF",
  surfaceContainerLow: "#F2F3FF",
  surfaceContainer: "#EAEDFF",
  surfaceContainerHigh: "#E2E7FF",

  // High-Clarity Typography Colors
  ink: "#0F172A",
  inkSoft: "#475569",
  inkFaint: "#94A3B8",
  rule: "#EEF2F6",
  ruleStrong: "#E2E8F0",

  // Semantic Status Tones (Intense foreground + light tint base)
  success: "#059669",
  successCore: "#10B981",
  successBg: "#ECFDF5",

  danger: "#E11D48",
  dangerCore: "#F43F5E",
  dangerBg: "#FFF1F2",

  warning: "#D97706",
  warningCore: "#F59E0B",
  warningBg: "#FFFBEB",

  info: "#0284C7",
  infoCore: "#0EA5E9",
  infoBg: "#F0F9FF",

  // Geometry
  radius: {
    xs: 4,
    sm: 8,
    input: 12,
    card: 16,
    modal: 24,
    pill: 9999,
  },

  // Spacing Scale (4, 8, 12, 16, 20, 24, 32, 40)
  space: [4, 8, 12, 16, 20, 24, 32, 40],

  // Shadows
  shadow: {
    card: {
      shadowColor: "#0F172A",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.04,
      shadowRadius: 16,
      elevation: 2,
    },
    elevated: {
      shadowColor: "#0F172A",
      shadowOffset: { width: 0, height: 12 },
      shadowOpacity: 0.08,
      shadowRadius: 28,
      elevation: 6,
    },
    button: {
      shadowColor: "#4338CA",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.25,
      shadowRadius: 10,
      elevation: 3,
    },
    subtle: {
      shadowColor: "#0F172A",
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.03,
      shadowRadius: 3,
      elevation: 1,
    },
  },
} as const;

/** Semantic status mapping for badges, indicators, and chips */
export const statusColor: Record<string, string> = {
  present: theme.success,
  paid: theme.success,
  submitted: theme.success,
  active: theme.success,
  approved: theme.success,
  resolved: theme.success,

  absent: theme.danger,
  overdue: theme.danger,
  failed: theme.danger,
  rejected: theme.danger,

  leave: theme.warning,
  pending: theme.warning,
  late: theme.warning,
  medical: theme.info,
  under_review: theme.warning,

  info: theme.info,
  circular: theme.info,
};

export const statusBg: Record<string, string> = {
  present: theme.successBg,
  paid: theme.successBg,
  submitted: theme.successBg,
  active: theme.successBg,
  approved: theme.successBg,
  resolved: theme.successBg,

  absent: theme.dangerBg,
  overdue: theme.dangerBg,
  failed: theme.dangerBg,
  rejected: theme.dangerBg,

  leave: theme.warningBg,
  pending: theme.warningBg,
  late: theme.warningBg,
  medical: theme.infoBg,
  under_review: theme.warningBg,

  info: theme.infoBg,
  circular: theme.infoBg,
};
