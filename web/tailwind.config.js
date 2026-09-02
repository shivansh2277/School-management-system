/** Design tokens from BLUEPRINT section 14 — kept identical in mobile/src/theme.ts. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#5B4BE0", dark: "#3E2FB5", soft: "#EEEBFC" },
        ground: "#F6F7FB",
        surface: "#FFFFFF",
        ink: { DEFAULT: "#1B2333", soft: "#5A6478", faint: "#8A93A6" },
        rule: "#E4E7EF",
        success: "#16A34A",
        warning: "#F59E0B",
        danger: "#EF4444",
        info: "#3B82F6",
      },
      borderRadius: { card: "12px", input: "8px", pill: "999px" },
      boxShadow: {
        card: "0 1px 2px rgba(27,35,51,.05), 0 8px 24px -12px rgba(27,35,51,.18)",
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
