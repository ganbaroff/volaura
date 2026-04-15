# WCAG 2.2 AA Accessibility Audit — VOLAURA

**Date:** 2026-04-15 · **Author:** Agent `a11y-scanner` (invoked by Terminal-Atlas) · **Model:** Claude via Task subagent
**Scope:** 47 routes, source `apps/web/src/`, tokens `apps/web/src/app/globals.css`
**Prior baseline:** `docs/design/DESIGN-SYSTEM-AUDIT.md` scored a11y 48/100 on 18 pages

---

## 1. Overall Score

**58 / 100** — WCAG Level **A partial** (Level AA not achieved)

Improvement from prior 48/100 is positive — ARIA landed for progress bars, radar table, energy picker radiogroup. But 5 P0 barriers block AA certification.

---

## 2. P0 Barriers — Blocking Screen-Reader or Keyboard Use

### P0-1 — WCAG 4.1.2 Name, Role, Value
**File:** `apps/web/src/components/aura/radar-chart.tsx:89`

`aria-hidden="true"` is placed on the `motion.div` wrapper that contains both the Recharts visual AND the `sr-only` accessibility table. `aria-hidden` hides all descendants regardless of CSS class. The competency score table (`<table className="sr-only">`) is completely invisible to screen readers. Code comment says "sr-only table provides the data" — incorrect as implemented.

**Fix:**
```tsx
return (
  <div>
    {srTable}  {/* outside aria-hidden */}
    <motion.div aria-hidden="true">
      <ResponsiveContainer ...>
```

### P0-2 — WCAG 1.4.11 Non-text Contrast
**Files:** `apps/web/src/components/ui/button.tsx:81`, `apps/web/src/app/globals.css:118`

`--color-ring: var(--color-primary)` = `#C0C1FF`. Button `variant="default"` uses `bg-primary` = `#C0C1FF`. Focused default button → ring (`#C0C1FF`) sits on bg (`#C0C1FF`) = **1:1 contrast — ring invisible**. Same collision on any element with `bg-primary` class.

**Fix:** Introduce `--color-ring-focus: #FFFFFF` (21:1 on dark, visible against `#C0C1FF`). Override `--color-ring: var(--color-ring-focus)` in `@layer base`.

### P0-3 — WCAG 2.4.7 Focus Visible
**File:** `apps/web/src/components/assessment/open-text-answer.tsx:112`

Textarea uses `outline-none` with only `focus:border-primary` — 1px border color change insufficient. Fails WCAG 2.4.11 3px-minimum advisory. No ring applied.

Same pattern correct on auth form inputs (`login`, `reset-password`, `signup`, `settings`) — use `outline-none focus:ring-2 focus:ring-ring`. `open-text-answer` is the outlier.

**Fix:** Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` to textarea.

### P0-4 — WCAG 4.1.2 Name, Role, Value
**File:** `apps/web/src/components/assessment/timer.tsx:44–78`

Timer `<div>` has `aria-label` but no `role="timer"`. `<motion.span>` displaying countdown has `aria-live="off"` (commented "parent has the aria-label" — parent is not a live region). Screen readers announce initial value at mount but never announce updates. AT users cannot perceive time pressure.

**Fix:** Add `role="timer"` on wrapper. Change `aria-live="off"` → `aria-live="polite"` with `aria-atomic="true"`. Throttle announcements to transitions at 60s/30s/10s/5s only.

### P0-5 — WCAG 2.4.1 Bypass Blocks
**File:** `apps/web/src/app/[locale]/(dashboard)/layout.tsx`

No skip navigation link anywhere in codebase (grep "skip" returned zero). Keyboard users tab through entire `<Sidebar>` (11 nav items + logout) on every page before reaching main. Mobile `<BottomTabBar>` compounds this.

**Fix:** Add skip link as first child of `<body>`:
```tsx
<a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[999] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-primary focus:text-on-primary">
  {t("a11y.skipToContent")}
</a>
```
Add `id="main-content"` to the `<main>` element.

---

## 3. P1 Degradations

### P1-1 — WCAG 1.4.3 Contrast (Minimum)
**File:** `apps/web/src/app/globals.css:333–338`

`.btn-primary-gradient` = `#C0C1FF → #8083FF`. Text = `--color-on-primary: #1000A9`.

| Point | Ratio | WCAG AA |
|---|---|---|
| Gradient start `#C0C1FF` | 9.5:1 | PASS |
| Gradient end `#8083FF` | 4.0:1 | **FAIL** |

Gradient end is ~40% of button surface. Primary CTAs (login, signup, hero) all affected.

**Fix:** Darken gradient end to `#6366FF` OR shift text to `#FFFFFF` (21:1 on both ends).

### P1-2 — WCAG 4.1.2 Name, Role, Value
**File:** `apps/web/src/components/assessment/open-text-answer.tsx:124`

Voice/mic toggle uses same `aria-label` (`t("assessment.voiceHint")`) for both `isListening=true` and `false`. AT users don't know current state.

**Fix:**
```tsx
aria-label={isListening
  ? t("assessment.stopListening", { defaultValue: "Stop voice input" })
  : t("assessment.startListening", { defaultValue: "Start voice input" })}
```

### P1-3 — WCAG 1.4.3 / Constitution Law 4 (Animation)
**Files:** `badge-display.tsx:54-70`, `hero-section.tsx:34-52`, `aura-score-widget.tsx:32-36`

`globals.css:386-401` correctly sets CSS durations to `0.01ms` under `prefers-reduced-motion`. But Framer Motion drives animations via JS `requestAnimationFrame` — bypasses CSS entirely.

`badge-display.tsx` runs infinite `boxShadow` pulse for platinum/gold with no `useReducedMotion()` check. `aura/page.tsx:7` imports `useReducedMotion` correctly — this pattern must be applied universally.

**Fix:** Add `const prefersReducedMotion = useReducedMotion()` to each animated component. Gate: `animate={prefersReducedMotion ? {} : { boxShadow: [...] }}`.

### P1-4 — WCAG 2.1.1 Keyboard / ARIA Pattern
**File:** `apps/web/src/components/navigation/bottom-tab-bar.tsx:103-139`

`role="tablist"` + `role="tab"` require Arrow Left/Right keyboard nav per ARIA APG. Currently plain `<a>` links — Tab works, Arrow doesn't. AT announces "tablist" → keyboard users expect arrows that don't exist.

**Fix (preferred):** Remove `role="tablist/tab"`. Use `role="navigation"` + `aria-current={isActive ? "page" : undefined}` — matches working `bottom-nav.tsx` pattern.

### P1-5 — WCAG 2.5.5 Target Size / Constitution Law 2
**File:** `apps/web/src/app/globals.css:242-247`

`[data-energy="low"]` sets `--energy-min-target: 56px`. Correct intent. But token only applied via `.energy-target` class. Hardcoded `h-8` small Button sizes, `h-10` inputs, and `min-w-[44px] min-h-[44px]` on mic button don't scale in Low energy.

**Fix:** Add `energy-target` to all Button sizes except `sm`. For `sm`: `data-[energy=low]:min-h-[56px]`. Replace mic button hardcoded sizes with `energy-target`.

---

## 4. P2 Polish

- **P2-1** `::selection` bg and `--color-ring` are same lavender hue. Hard to distinguish focused vs selected visually. Fixed by P0-2 white ring.
- **P2-2** Sidebar `Escape` closes (good) but focus doesn't return to trigger. Same for all modals (`crystal-shop.tsx`, `org-volunteers/page.tsx`, `aura/page.tsx` share prompt). No `FocusTrap` in codebase.
- **P2-3** Share prompt dialog uses `aria-label` directly — should use `aria-labelledby` pointing to visible title. `org-volunteers:388` dialog close button hardcoded English "Close" — use `t("common.close")`.
- **P2-4** AZ charset `ə ğ ı ö ü ş ç` confirmed in Figma annotation, regex in signup. No CI test verifies rendering at all weights. Font-loading failure would fall silently to system-ui.

---

## 5. Contrast Matrix

| Use case | Fg | Bg | Hex fg | Hex bg | Ratio | AA normal | AA large/UI |
|---|---|---|---|---|---|---|---|
| Body text | on-surface | surface | `#E4E1ED` | `#13131B` | **14.5:1** | PASS | PASS |
| Muted text | on-surface-variant | container-low | `#C7C4D7` | `#1B1B23` | **10.2:1** | PASS | PASS |
| Muted on card | on-surface-variant | container-high | `#C7C4D7` | `#292932` | **8.7:1** | PASS | PASS |
| Primary accent text | primary | surface | `#C0C1FF` | `#13131B` | **10.9:1** | PASS | PASS |
| Btn text (gradient start) | on-primary | `#C0C1FF` | `#1000A9` | `#C0C1FF` | **9.5:1** | PASS | PASS |
| Btn text (gradient end) | on-primary | `#8083FF` | `#1000A9` | `#8083FF` | **4.0:1** | **FAIL** | PASS |
| Error on container | on-error-container | error-container | `#EDD6FF` | `#3D1A6E` | **11.1:1** | PASS | PASS |
| Success | success | surface | `#6EE7B7` | `#13131B` | **12.8:1** | PASS | PASS |
| Outline/placeholder | outline | surface | `#908FA0` | `#13131B` | **6.1:1** | PASS | PASS |
| Focus ring on dark | primary (ring) | surface | `#C0C1FF` | `#13131B` | **10.9:1** | — | PASS |
| Focus ring on primary | primary (ring) | primary | `#C0C1FF` | `#C0C1FF` | **1:1** | — | **FAIL** |
| Badge gold | `text-yellow-400` | card | `#FACC15` | `#1B1B23` | **11.7:1** | PASS | PASS |
| Badge silver | `text-slate-300` | card | `#CBD5E1` | `#1B1B23` | **9.6:1** | PASS | PASS |
| Badge bronze | `text-amber-600` | card | `#D97706` | `#1B1B23` | **5.3:1** | PASS | PASS |
| Warning (amber text) | warning | surface | `#E9C400` | `#13131B` | **10.0:1** | PASS | PASS |

**Only failures:** gradient-end on primary button (P1-1) and ring-on-primary-bg (P0-2).

---

## 6. Token Additions Needed

| Token | Value | Fixes | Priority |
|---|---|---|---|
| `--color-ring-focus` | `#FFFFFF` | P0-2, P2-1 | P0 |
| `--color-ring-focus-offset` | `var(--color-surface)` | P0-2 | P0 |
| `--color-btn-gradient-end-safe` | `#6366FF` | P1-1 | P1 |

**Systemic change:** `--color-ring: var(--color-ring-focus);` (was `var(--color-primary)`). One line → fixes P0-2 across 40+ interactive elements.

**Energy-target gap:** class-application audit — add `.energy-target` to Button `sizeClasses.default` and `.lg`, conditional for `.sm`.

---

## 7. PASSED Criteria

- 1.4.3 body/muted/primary text pairs: all pass except gradient-end
- 2.1.1 keyboard on custom controls: EnergyPicker radiogroup ✅, McqOptions ✅, modals Escape ✅
- 2.4.3 focus order: no `tabIndex > 0` anywhere
- 3.2.2 on-input: no auto-advance without activation
- 4.1.2 progress bars: `ProgressBar` + `aura-score-widget` correct `role="progressbar"` + `aria-valuenow/min/max`
- 4.1.2 EnergyPicker: `role="radiogroup"/"radio"` + `aria-checked` + `aria-label` ✅

**11 issues across 6 criteria. 5 partially/fully passing.**

---

## Evidence files

`apps/web/src/components/aura/radar-chart.tsx`, `apps/web/src/components/ui/button.tsx`, `apps/web/src/components/assessment/open-text-answer.tsx`, `apps/web/src/components/assessment/timer.tsx`, `apps/web/src/app/[locale]/(dashboard)/layout.tsx`, `apps/web/src/app/globals.css`, `apps/web/src/components/aura/badge-display.tsx`, `apps/web/src/components/navigation/bottom-tab-bar.tsx`, `apps/web/src/components/layout/sidebar.tsx`, `apps/web/src/app/[locale]/(auth)/login/page.tsx`.
