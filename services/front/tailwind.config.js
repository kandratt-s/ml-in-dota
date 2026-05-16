/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        radiant: "#3a7d3a",
        dire: "#a23b2c",
        panel: "#101418",
        panelMuted: "#1a2027",
        accent: "#e7b15a",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
