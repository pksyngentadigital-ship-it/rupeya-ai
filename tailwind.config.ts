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
        // Rupeya brand palette — calm, premium, fintech-trustworthy
        background: "#0B0F14",
        surface: "#121821",
        surfaceAlt: "#1A2230",
        border: "#1F2A3A",
        text: "#E6EDF3",
        textMuted: "#8B95A7",
        accent: "#16C784", // PSX green-coded for "good"
        accentSoft: "#0F3A2A",
        warn: "#F0B72F",
        danger: "#EA3943",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Inter", "sans-serif"],
      },
      maxWidth: {
        page: "1100px",
      },
    },
  },
  plugins: [],
};

export default config;
