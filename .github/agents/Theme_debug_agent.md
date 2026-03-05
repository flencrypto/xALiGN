---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description: You are a coding agent working on this repo:
https://github.com/flencrypto/aLiGN.git

TASK: Add a "Theme Debug Page" to validate ALiGN dashboard tokens + shadcn/Radix component styling.
---



CONTEXT
- Frontend is Vite + React Router (see src/app/routes.tsx, src/app/layout/Layout.tsx).
- UI components live in: src/app/components/ui/*
- Theme tokens are defined in CSS via Tailwind v4 CSS-first: src/styles/theme.css (or similar).
- We are using a dark dashboard theme by default (ALiGN OS).
- Goal is a single route that exposes:
  1) token swatches + variable inspector (brand + semantic + sidebar)
  2) typography scale preview
  3) component gallery showing all variants and typical states
  4) quick “copy JSON” export of computed tokens
  5) sanity checks (contrast ratios for key pairs)

REQUIREMENTS
1) Create a new page file:
   - src/app/pages/ThemeDebug.tsx
2) Register a new route in src/app/routes.tsx:
   - path: "theme" OR "debug/theme" (pick one and be consistent)
   - component: ThemeDebug
3) Add a navigation entry for it:
   - Ideally add to the Sidebar under "System Config" as “Theme Debug”
   - If you don’t want it visible, keep it hidden but accessible via URL.
4) Ensure CSS imports are correct:
   - theme.css must already be imported globally (confirm in src/main.tsx or App.tsx).
   - Do not duplicate imports; verify once.
5) Do NOT refactor existing components; debug page should use existing UI components.

PAGE DESIGN (ThemeDebug.tsx)
- Layout: use existing AppLayout chrome (Sidebar + TopBar). The page content can live inside the Outlet.
- Use existing UI components where possible:
  - Card, Button, Badge, Tabs, Alert, DropdownMenu, Accordion, Input, Separator, Sheet/Dialog, Skeleton, Toggle/Switch if present.
- The page should have these sections:

A) “Runtime Token Inspector”
- Read computed CSS variables from document.documentElement using getComputedStyle.
- Display a grid of swatches + values for:
  Brand tokens:
    --color-background
    --color-surface
    --color-border-subtle
    --color-primary
    --color-primary-dark
    --color-secondary
    --color-text-main
    --color-text-muted
    --color-text-faint
    --color-success
    --color-warning
    --color-danger
  Semantic aliases (shadcn-style, if defined):
    --color-foreground
    --color-card
    --color-card-foreground
    --color-popover
    --color-popover-foreground
    --color-muted
    --color-muted-foreground
    --color-accent
    --color-accent-foreground
    --color-border
    --color-input
    --color-ring
  Sidebar set:
    --color-sidebar
    --color-sidebar-foreground
    --color-sidebar-border
    --color-sidebar-accent
    --color-sidebar-accent-foreground
    --color-sidebar-primary
    --color-sidebar-primary-foreground
    --color-sidebar-ring

- Each token row:
  - swatch box (background set to that value)
  - variable name
  - computed value string
  - a “Copy” button (copy value to clipboard)
- Provide a “Copy All Tokens (JSON)” button that copies a JSON blob of all tokens that exist.

B) “Contrast Checks”
- Implement a small function to parse hex/rgb(a) and compute WCAG contrast ratio.
- Show at least these pairs with PASS/FAIL:
  - text-main on background
  - text-muted on background
  - text-main on surface/card
  - primary on background
  - primary-foreground on primary
- Keep it simple: display ratio value + PASS if >= 4.5 for normal text.

C) “Typography Preview”
- Show headings + body + mono labels:
  - H1 / H2 / H3 samples
  - body text
  - small muted
  - mono tag line
- Use your actual Tailwind classes used in app (font-sans/font-mono, text-text-main, text-text-muted, tracking-widest etc).

D) “Component Gallery”
Create a grid of Cards demonstrating:
- Buttons: variants (default/outline/ghost/danger/nav) + sizes (default/sm/lg/icon)
- Badges: any variants (including LIVE if it exists), and neutral.
- Alerts: default + destructive
- Tabs: TabsList + TabsTrigger + content
- DropdownMenu: trigger + items (default + destructive item) + separator + shortcut
- Accordion: open/close states
- Dialog/Sheet: open via button (confirm overlay/backdrop + content uses bg-popover)
- Inputs: normal + focused (add a helper button “Focus input”)
- Skeleton: a few skeleton blocks to ensure bg-accent animate-pulse looks right.

E) “Theme Toggles (visual QA)”
- Buttons to toggle:
  - blueprint overlay class on page container (.bg-blueprint)
  - glass-panel class on a demo card
  - glow-primary class on a demo badge/button
These toggles help quickly verify your utilities.

IMPLEMENTATION DETAILS
- Use React state to hold:
  - tokens object
  - toggles
  - dropdown open state (optional)
- Read tokens on mount and also provide a “Refresh tokens” button.
- Handle missing tokens gracefully (show “(not found)”).
- Keep the page styled in your ALiGN theme (use bg-background, bg-card, border-border, etc).

QUALITY / ACCEPTANCE
- Route loads without errors.
- Tokens display correctly (not empty).
- Component gallery renders and matches the dark dashboard look.
- Copy buttons work.
- Contrast ratio section works.
- The page should not break production build.

DELIVERABLES
- Commit:
  - src/app/pages/ThemeDebug.tsx (new)
  - src/app/routes.tsx (route added)
  - Sidebar nav addition (wherever nav items are defined) OR leave hidden and document URL in code comment.
- Provide a short summary of changes and how to access the page.

NOTE
This repo already includes .github/agents. If your environment supports it, add a small agent note/update there describing how to use the Theme Debug Page (optional).
