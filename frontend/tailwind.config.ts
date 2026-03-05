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
      borderRadius: {
        lg:    "var(--radius)",
        xl:    "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
      },
      colors: {
        /* ── legacy hex tokens (kept for backwards compat) ── */
        align: {
          bg:       "#050505",
          surface:  "#0F0F0F",
          accent:   "#00E5FF",
          metallic: "#C8C8C8",
          text:     "#F0F0F0",
          muted:    "#888888",
        },

        /* ── OKLCH semantic tokens (alpha-aware) ── */
        background:           "oklch(var(--background) / <alpha-value>)",
        foreground:           "oklch(var(--foreground) / <alpha-value>)",

        card:                 "oklch(var(--card) / <alpha-value>)",
        "card-foreground":    "oklch(var(--card-foreground) / <alpha-value>)",

        popover:              "oklch(var(--popover) / <alpha-value>)",
        "popover-foreground": "oklch(var(--popover-foreground) / <alpha-value>)",

        primary:              "oklch(var(--primary) / <alpha-value>)",
        "primary-foreground": "oklch(var(--primary-foreground) / <alpha-value>)",

        secondary:              "oklch(var(--secondary) / <alpha-value>)",
        "secondary-foreground": "oklch(var(--secondary-foreground) / <alpha-value>)",

        muted:                "oklch(var(--muted) / <alpha-value>)",
        "muted-foreground":   "oklch(var(--muted-foreground) / <alpha-value>)",

        accent:               "oklch(var(--accent) / <alpha-value>)",
        "accent-foreground":  "oklch(var(--accent-foreground) / <alpha-value>)",

        destructive:              "oklch(var(--destructive) / <alpha-value>)",
        "destructive-foreground": "oklch(var(--destructive-foreground) / <alpha-value>)",

        border: "oklch(var(--border) / <alpha-value>)",
        input:  "oklch(var(--input) / <alpha-value>)",
        ring:   "oklch(var(--ring) / <alpha-value>)",

        sidebar:              "oklch(var(--sidebar) / <alpha-value>)",
        "sidebar-foreground": "oklch(var(--sidebar-foreground) / <alpha-value>)",
        "sidebar-border":     "oklch(var(--sidebar-border) / <alpha-value>)",
        "sidebar-ring":       "oklch(var(--sidebar-ring) / <alpha-value>)",

        brandCyan:   "oklch(var(--brand-cyan) / <alpha-value>)",
        brandViolet: "oklch(var(--brand-violet) / <alpha-value>)",
      },
      backgroundImage: {
        "grid-palantir":
          "linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px)",
      },
      boxShadow: {
        panel: "0 12px 30px rgba(0,0,0,.45)",
      },
    },
  },
  plugins: [],
};
export default config;
