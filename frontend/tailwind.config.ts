import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nexus: {
          bg: "#0a0e17",
          panel: "#121826",
          border: "#1f2937",
          accent: "#6366f1",
          accent2: "#22d3ee",
          good: "#34d399",
        },
      },
    },
  },
  plugins: [],
};

export default config;
