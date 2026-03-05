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
        /* New dark-theme semantic tokens */
        background:     "var(--color-background)",
        surface:        "var(--color-surface)",
        "border-subtle":"var(--color-border-subtle)",
        primary:        "var(--color-primary)",
        "primary-dark": "var(--color-primary-dark)",
        secondary:      "var(--color-secondary)",
        "text-main":    "var(--color-text-main)",
        "text-muted":   "var(--color-text-muted)",
        "text-faint":   "var(--color-text-faint)",
        success:        "var(--color-success)",
        warning:        "var(--color-warning)",
        danger:         "var(--color-danger)",

        /* Legacy align.* tokens kept for backwards compatibility */
        align: {
          bg:       "var(--align-bg)",
          surface:  "var(--color-surface)",
          accent:   "var(--color-primary)",
          metallic: "#C8C8C8",
          text:     "var(--color-text-main)",
          muted:    "var(--color-text-muted)",
        },

        /* Keep foreground alias */
        foreground: "var(--foreground)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
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
