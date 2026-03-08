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
        card:   "var(--radius-card)",
        button: "var(--radius-button)",
        lg:     "var(--radius-card)",
        xl:     "calc(var(--radius-card) + 4px)",
        "2xl":  "calc(var(--radius-card) + 8px)",
        vv:     "var(--vv-radius)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      colors: {
        /* ── brand palette (RGB channel tokens) ── */
        "color-background":    "rgb(var(--color-background) / <alpha-value>)",
        "color-surface":       "rgb(var(--color-surface) / <alpha-value>)",
        "color-border-subtle": "rgb(var(--color-border-subtle) / <alpha-value>)",
        "color-primary":       "rgb(var(--color-primary) / <alpha-value>)",
        "color-primary-dark":  "rgb(var(--color-primary-dark) / <alpha-value>)",
        "color-secondary":     "rgb(var(--color-secondary) / <alpha-value>)",
        "color-text-main":     "rgb(var(--color-text-main) / <alpha-value>)",
        "color-text-muted":    "rgb(var(--color-text-muted) / <alpha-value>)",
        "color-text-faint":    "rgb(var(--color-text-faint) / <alpha-value>)",
        "color-success":       "rgb(var(--color-success) / <alpha-value>)",
        "color-warning":       "rgb(var(--color-warning) / <alpha-value>)",
        "color-danger":        "rgb(var(--color-danger) / <alpha-value>)",

        /* ── semantic tokens (alpha-aware) ── */
        background:              "rgb(var(--background) / <alpha-value>)",
        foreground:              "rgb(var(--foreground) / <alpha-value>)",

        card:                    "rgb(var(--card) / <alpha-value>)",
        "card-foreground":       "rgb(var(--card-foreground) / <alpha-value>)",

        popover:                 "rgb(var(--popover) / <alpha-value>)",
        "popover-foreground":    "rgb(var(--popover-foreground) / <alpha-value>)",

        primary:                 "rgb(var(--primary) / <alpha-value>)",
        "primary-foreground":    "rgb(var(--primary-foreground) / <alpha-value>)",

        secondary:               "rgb(var(--secondary) / <alpha-value>)",
        "secondary-foreground":  "rgb(var(--secondary-foreground) / <alpha-value>)",

        muted:                   "rgb(var(--muted) / <alpha-value>)",
        "muted-foreground":      "rgb(var(--muted-foreground) / <alpha-value>)",

        accent:                  "rgb(var(--accent) / <alpha-value>)",
        "accent-foreground":     "rgb(var(--accent-foreground) / <alpha-value>)",

        destructive:             "rgb(var(--destructive) / <alpha-value>)",
        "destructive-foreground":"rgb(var(--destructive-foreground) / <alpha-value>)",

        border: "rgb(var(--border) / <alpha-value>)",
        input:  "rgb(var(--input) / <alpha-value>)",
        ring:   "rgb(var(--ring) / <alpha-value>)",

        sidebar:              "rgb(var(--sidebar) / <alpha-value>)",
        "sidebar-foreground": "rgb(var(--sidebar-foreground) / <alpha-value>)",
        "sidebar-border":     "rgb(var(--sidebar-border) / <alpha-value>)",
        "sidebar-ring":       "rgb(var(--sidebar-ring) / <alpha-value>)",

        /* ── legacy hex tokens (kept for backwards compat) ── */
        align: {
          bg:       "var(--align-bg)",
          surface:  "var(--color-surface)",
          accent:   "var(--color-primary)",
          metallic: "#C8C8C8",
          text:     "var(--color-text-main)",
          muted:    "var(--color-text-muted)",
        },

        /* ── VinylVault tokens ── */
        vv: {
          bg:      "var(--vv-bg)",
          panel:   "var(--vv-panel)",
          card:    "var(--vv-card)",
          text:    "var(--vv-text)",
          border:  "var(--vv-border)",
          divider: "var(--vv-divider)",
          cyan:    "var(--vv-cyan)",
          violet:  "var(--vv-violet)",
          success: "var(--vv-success)",
          warning: "var(--vv-warning)",
          danger:  "var(--vv-danger)",
        },
      },
      backgroundImage: {
        "grid-palantir":
          "linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px)",
      },
      boxShadow: {
        panel: "0 12px 30px rgba(0,0,0,.45)",
        glow:  "0 0 20px rgba(0,229,255,0.15), 0 8px 32px rgba(0,0,0,0.30)",
        "glow-lg": "0 0 40px rgba(0,229,255,0.20), 0 16px 48px rgba(0,0,0,0.40)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.06), 0 12px 30px rgba(0,0,0,.45)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease forwards",
        "fade-in-up": "fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards",
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "slide-in-right": "slideInRight 0.4s cubic-bezier(0.16,1,0.3,1) forwards",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          from: { opacity: "0", transform: "translateX(20px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
