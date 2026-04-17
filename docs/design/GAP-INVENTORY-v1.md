# GAP INVENTORY v1 — VOLAURA Ecosystem Design Audit

**Date:** 2026-04-16 Session 113, updated 2026-04-17 (code-level audit + agent swarm)
**Method:** Session 113 Explore agent (58 gaps) + Session 117 triple-agent audit (a11y-scanner + ecosystem-auditor + direct grep, 180+ tool uses, 200+ files)
**Scope:** All 5 products, 48 pages, globals.css tokens, Constitution Laws 1-5, WCAG 2.2 AA, 16 anti-patterns

## Summary

**Session 117 update:** 22 code-verified gaps. 11 fixed (F1-F7 + M5 + C2 + H3 + H1). 0 Critical, 4 High, 4 Medium, 3 Low remaining.
**Session 113 original:** 58 gaps (8 P0, 34 P1, 24 P2). Cross-product gaps remain valid. P0 items 1-5 (MindShift/LifeSim/BrandedBy placeholders, crystal economy) are architectural; items 6-8 (Stripe, Resend, Atlas page) partially resolved.

---

## FIXED 2026-04-17 (committed)

| # | Issue | Fix |
|---|-------|-----|
| F1 | "Keep your streak alive" — anti-pattern #5 banned copy | EN+AZ reworded to "Your crystal glow is fading" |
| F2 | autoPlay on BrandedBy video — anti-pattern #9 | Removed autoPlay attribute |
| F3 | Streak shown at value 0/1 — Law 3 shame-free | Added `currentStreak > 1` guard in tribe-card.tsx |
| F4 | AURA progress bar animation 1.2s — Law 4 max 800ms | Reduced to 0.8s in aura-score-widget.tsx |
| F5 | Impact ticker animation 1800ms — Law 4 max 800ms | Reduced to 800ms in impact-ticker.tsx |
| F6 | Impact ticker no reduced-motion guard | Added prefers-reduced-motion check |
| F7 | No focus trapping in 5 modals (C1) | Added `useFocusTrap` hook + applied to all 5 dialogs. `role="dialog"` moved to inner panel. |
| F8 | Onboarding labels unassociated (C2) | Added `id`/`htmlFor` to all inputs, `role="group"` + `aria-labelledby` + `aria-pressed` to language toggles |
| F9 | Onboarding slide animations ignore reduced motion (H3) | Gated `slideVariants` on `prefersReduced` for all 3 steps |
| F10 | `role="button"` cards missing Space key (H1) | Added Space key handler with `preventDefault()` across 6 instances in 5 files |
| F8 | Onboarding inputs no label association (C2) | Added `id`/`htmlFor` pairs to all inputs, `role="group"` + `aria-labelledby` on language toggles, `aria-pressed` on language buttons. |
| F9 | Onboarding animations ignore reduced motion (H3) | Added `useReducedMotion` gating to ProgressBar + all 3 step slide transitions. |

---

## CRITICAL — Blocks launch

### ~~C1. No focus trapping in ANY modal (5 modals)~~ FIXED

Added `hooks/use-focus-trap.ts` — traps Tab cycle inside dialog, restores focus on close. Applied to all 5 modals. Also moved `role="dialog"` from backdrop to inner panel (M5 also resolved).

**Files changed:** `crystal-shop.tsx`, `intro-request-button.tsx`, `aura/page.tsx`, `org-talent/page.tsx`, `assessment/[sessionId]/page.tsx`

### ~~C2. Onboarding inputs have no label-input association~~ FIXED

Added `id`/`htmlFor` pairs to all 3 Input instances (display_name, username, location) via `useId()`. Language button group now has `role="group"` + `aria-labelledby` with a labelled container. Each language toggle button has `aria-pressed` for state.

**Files changed:** `onboarding/page.tsx`

---

## HIGH — Fix before launch

### ~~H1. `role="button"` cards missing Space key handler~~ FIXED

Added Space key (`" "`) alongside Enter in `onKeyDown` handlers across all 6 `role="button"` instances: `discover/page.tsx` (2), `organizations/page.tsx` (1), `my-organization/page.tsx` (1), `org-talent/page.tsx` (1), `invite/page.tsx` (1). `e.preventDefault()` prevents page scroll on Space.

### H2. Hardcoded color classes — contrast failures on dark bg

`text-cyan-600` (Lc ~38), `text-blue-500` (Lc ~42) on dark surface. Below Lc 45 minimum.
**Files:** `profile-header.tsx:63,68,73`, `competency-breakdown.tsx:41,42,110`, `impact-metrics.tsx:41,47`
**Fix:** Replace with `-400` variants or tokens.

### ~~H3. Onboarding animations not gated by useReducedMotion~~ FIXED

Added `useReducedMotion()` from framer-motion. ProgressBar skips initial animation and uses `duration: 0`. All 3 step slide transitions (enter/exit) disabled when reduced motion preferred. Also added `role="progressbar"` with `aria-valuenow/min/max` to ProgressBar.

**Files changed:** `onboarding/page.tsx`

### H4. McqOptions uses aria-pressed for single-selection

`mcq-options.tsx:29` — Should be `role="radiogroup"` + `role="radio"` + `aria-checked`.

### H5. Infinite animation loops on action screens

`badge-display.tsx:76`, `aura/page.tsx:143` — Infinite repeat on non-celebration screens violates Law 4.

### H6. AuraRadarChart animation ignores reduced motion

`radar-chart.tsx:92` — Framer Motion + Recharts SVG animation both ungated.

---

## MEDIUM — Polish sprint

### M1. Glass on navigation — anti-pattern #8

`bottom-tab-bar.tsx:101` (glass-nav), `top-bar.tsx:43` (glass-header). Manifesto: glass for hero only.
**Decision needed from CEO.**

### M2. Energy mode coverage gap — 15+ pages missing

Implemented in 9 files. Missing: onboarding, settings, events/*, org-talent, brandedby/*. Track as mini-sprint.

### M3. Sidebar mobile loses focus on close

`sidebar.tsx:88` — No returnFocusTo hamburger button.

### M4. Auth inputs: focus:ring-2 instead of focus-visible:ring-2

All auth pages. Mouse users see unnecessary ring. Inconsistent with rest of codebase.

### ~~M5. Share modal aria structure fragile~~ FIXED (in C1 fix)

All 5 modals now have `role="dialog"` on inner panel, not backdrop.

---

## LOW — Track

### L1. Leaderboard route exists (redirect-only compliant)
### L2. "volunteer" in backend API field names (not user-visible)
### L3. Impact ticker countUp on aggregate stats (borderline, now gated + 800ms)

---

## SESSION 113 CROSS-PRODUCT GAPS (still valid)

These are architectural, not fixable by code audit alone:

1. **MindShift** — placeholder only, no functional integration
2. **LifeSim** — Godot client location unknown (web feed built, native deferred)
3. **BrandedBy** — placeholder, no twin generation UI
4. **Character events** — all from VOLAURA, zero from other products
5. **Crystal economy** — earn only, zero spend paths (Crystal Shop is Life Feed only)
6. **Email keys** — Resend still needs CEO
7. **Atlas admin page** — should show swarm status, currently ProductPlaceholder

---

## VERIFIED PASS (from both audits)

- Law 1 (Never Red): PASS — `--color-destructive` resolves to purple `#3d1a6e`, zero raw red hex
- No "volunteer" in user-visible strings (locales clean, only backend API fields)
- No shame language in locales
- No #000000 pure black
- No infinite scroll
- Skip-to-content present in layout
- All `role="progressbar"` have proper aria-value attributes
- EnergyPicker uses correct radio pattern
- No tabIndex > 0 anywhere
