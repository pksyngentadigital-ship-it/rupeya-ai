// Rupeya.ai — Tailwind theme
// Mirrors prototype/style.css design tokens. Edit one place; every page updates.
// See B1_DESIGN_AUDIT.md for the full token mapping rationale.

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // -- Surfaces --
        background: "#0B0F14",
        surface: "#121821",
        surfaceAlt: "#1A2230",

        // -- Borders --
        border: "#1F2A3A",
        borderStrong: "#2A3850",

        // -- Text --
        text: "#E6EDF3",
        textMuted: "#8B95A7",

        // -- Brand / accent --
        accent: "#16C784",
        accentSoft: "#0F3A2A",

        // -- Semantic --
        warn: "#F0B72F",
        danger: "#EA3943",
        info: "#4F8DF7",

        // -- Verdict-badge tints (named for the verdict they support) --
        holdBg: "#1E2A3D",
        trimBg: "#3A2D14",
        exitBg: "#3A1A1F",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Inter",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SF Mono",
          "Cascadia Code",
          "Consolas",
          "monospace",
        ],
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "10px",
        md: "10px",
        lg: "14px",
        xl: "20px",
      },
      maxWidth: {
        page: "1100px",
        disclaimer: "640px",
      },
      spacing: {
        // Section vertical padding helpers (prototype uses 64px / 40px)
        section: "64px",
        sectionTight: "40px",
      },
      letterSpacing: {
        kicker: "0.12em",
        wider2: "0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
