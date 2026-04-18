# GAP INVENTORY v1 — VOLAURA Ecosystem Design Audit

**Date:** 2026-04-16 Session 113, updated 2026-04-17 (code-level audit + agent swarm)
**Method:** Session 113 Explore agent (58 gaps) + Session 117 triple-agent audit (a11y-scanner + ecosystem-auditor + direct grep, 180+ tool uses, 200+ files)
**Scope:** All 5 products, 48 pages, globals.css tokens, Constitution Laws 1-5, WCAG 2.2 AA, 16 anti-patterns

## Summary

**Session 117-118 update:** 22 code-verified gaps. 18 fixed (F1-F7 + M5 + C2 + H1-H6 + M3 + M4 + M2). 0 Critical, 0 High, 1 Medium (M1 — CEO decision), 3 Low remaining.
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
| F11 | Hardcoded color contrast failures (H2) | Replaced `-600`/`-500` with `-400` variants across 4 files |
| F12 | MCQ aria-pressed for single-selection (H4) | Changed to `role="radiogroup"` + `role="radio"` + `aria-checked` |
| F13 | Infinite animation loops (H5) | Badge glow limited to 3 cycles, AURA reveal to 5 cycles |
| F14 | Radar chart ignores reduced motion (H6) | Added `useReducedMotion` gating to framer + recharts + reveal delay |

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

### ~~H2. Hardcoded color classes — contrast failures on dark bg~~ FIXED

Replaced `text-cyan-600` → `text-cyan-400`, `text-blue-500` → `text-blue-400` across 4 files: profile-header.tsx, competency-breakdown.tsx, feed-cards.tsx, features-grid.tsx. APCA Lc now ~60+ (was ~38-42). Commit 7bedae9.

### ~~H3. Onboarding animations not gated by useReducedMotion~~ FIXED

Added `useReducedMotion()` from framer-motion. ProgressBar skips initial animation and uses `duration: 0`. All 3 step slide transitions (enter/exit) disabled when reduced motion preferred. Also added `role="progressbar"` with `aria-valuenow/min/max` to ProgressBar.

**Files changed:** `onboarding/page.tsx`

### ~~H4. McqOptions uses aria-pressed for single-selection~~ FIXED

Changed container from `role="group"` to `role="radiogroup"`, buttons from `aria-pressed` to `role="radio"` + `aria-checked`. Tests updated.

### ~~H5. Infinite animation loops on action screens~~ FIXED

Badge glow (platinum/gold) limited from `Infinity` to 3 repeats. AURA reveal symbol limited to 5 repeats. Both already gated by `prefersReducedMotion`.

### ~~H6. AuraRadarChart animation ignores reduced motion~~ FIXED

Added `useReducedMotion` from framer-motion. Framer entry animation skipped when reduced motion. Recharts `animationDuration` set to 0. Reveal delay set to 0.

---

## MEDIUM — Polish sprint

### M1. Glass on navigation — anti-pattern #8

`bottom-tab-bar.tsx:101` (glass-nav), `top-bar.tsx:43` (glass-header). Manifesto: glass for hero only.
**Decision needed from CEO.**

### ~~M2. Energy mode coverage gap — 15+ pages missing~~ FIXED

Energy mode gating added to all 31 dashboard pages across 20+ commits (Session 117-118 autonomous wakes). Coverage: 31/31 pages including assessment session, all placeholders, create flows, profile edit, subscription, checkin, and brandedby. Low energy hides non-essential descriptions, meta cards, difficulty badges, share buttons, and secondary CTAs throughout.

### ~~M3. Sidebar mobile loses focus on close~~ FIXED

Added `hamburgerRef` + `closeSidebar()` callback. Escape, overlay click, and close button all return focus to hamburger. WCAG 2.4.3 compliant.

**Files changed:** `sidebar.tsx`

### ~~M4. Auth inputs: focus:ring-2 instead of focus-visible:ring-2~~ FIXED

Replaced `focus:ring-*` with `focus-visible:ring-*` across 16 files (auth, dashboard, public). Mouse users no longer see focus rings; keyboard users still do. WCAG 2.4.7 compliant.

**Files changed:** 16 files across auth/, dashboard/, public/, components/

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
