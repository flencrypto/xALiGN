import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        align: {
          bg:       "#050505",
          surface:  "#0F0F0F",
          accent:   "#00E5FF",
          metallic: "#C8C8C8",
          text:     "#F0F0F0",
          muted:    "#888888",
        },
      },
      backgroundImage: {
        "grid-palantir":
          "linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
export default config;
