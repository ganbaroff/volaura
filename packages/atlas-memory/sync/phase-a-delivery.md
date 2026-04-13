# Phase A Delivery — Cowork → Atlas

**Date:** 2026-04-12
**Status:** READY FOR REVIEW

---

## What was delivered

### 1. globals.css — Full 3-Tier Token System

**File:** `apps/web/src/app/globals.css`

**Changes from previous version:**
- Added Tier 3 product tokens: `--color-product-volaura/mindshift/lifesim/brandedby/zeus`
- Added spacing scale: `--spacing-xs` through `--spacing-2xl`
- Added shadow/elevation tokens: `--shadow-sm/md/lg/glow`
- Added z-index scale: `--z-base` through `--z-bottomnav`
- Added animation duration tokens: `--duration-instant/fast/normal/slow/max` (Law 4: max=800ms)
- Added spring physics tokens: `--spring-damping: 14` (Law 4 minimum)
- Added success color tokens (colorblind-safe green)
- Added `--radius-full: 9999px`
- Added `liquid-glass` utility class (Q2 decision: CSS-only)
- Added Energy Mode CSS system via `[data-energy]` attribute
- Added product accent system via `[data-product]` attribute
- Added energy-responsive utilities: `.energy-gap`, `.energy-p`, `.energy-target`
- Enhanced `prefers-reduced-motion` to cover ALL elements (was only float animations)
- Added `[data-energy="low"]` animation disabling (equivalent to reduced-motion)
- Added `backdrop-filter` fallback for liquid-glass

**Preserved:** All existing tokens, shadcn aliases, AURA tier tokens, glows, gradients unchanged.

### 2. Bottom Tab Bar

**File:** `apps/web/src/components/navigation/bottom-tab-bar.tsx`

- Discord-style product switcher (5 tabs: Home, AURA, MindShift, Life Sim, ZEUS)
- Active tab uses product accent color (Tier 3)
- Labels always visible (ADHD clarity rule)
- Inline SVG icons (0KB dependency)
- 150ms transitions (Law 4)
- `energy-target` min touch target
- glass-nav background
- Fixed position with z-bottomnav
- i18n ready
- a11y: radiogroup pattern, aria-selected, focus-visible ring

### 3. Liquid Glass AURA Radar

**File:** `apps/web/src/components/aura/liquid-glass-radar.tsx`

- Wraps existing `AuraRadarChart` in liquid-glass container
- Identity-first layout: name → score → tier → radar → growth hint → CTA
- Badge tier glow effects (platinum/gold/silver/bronze)
- Shame-free growth hint (Law 3): "Your strongest areas shine here"
- Single primary CTA (Law 5)
- Spring animation: damping 14, stiffness 100 (Law 4)
- Uses existing radar-chart.tsx (no duplication)

### 4. Energy Mode Hook

**File:** `apps/web/src/hooks/use-energy-mode.ts`

- `useEnergyMode()` → `{ energy, setEnergy }`
- localStorage persistence (key: `volaura_energy_level`)
- Sets `data-energy` attribute on `<html>` element
- TODO stub for Supabase sync (Q4 decision)
- Three states: full/mid/low with specific CSS variable changes

### 5. Enhanced Energy Picker

**File:** `apps/web/src/components/assessment/energy-picker.tsx`

- Two variants: `default` (full card grid) and `compact` (inline for header/settings)
- Compact variant: emoji-only buttons in pill container (for top bar placement)
- energy-target sizing for touch accessibility
- 150ms transitions
- i18n ready

### 6. Assessment Card

**File:** `apps/web/src/components/assessment/assessment-card.tsx`

- Energy-responsive: density changes with energy level
- Shame-free progress (Law 3): "Question 3 of ~12" not "33% complete"
- Spring entrance animation (damping 14)
- Composable: accepts children (MCQ, rating, open text)
- Subtle progress bar (not dominant)
- Low energy: larger text, max-w-md (narrower focus)

---

## Constitution Compliance Audit

| Law | Status | Evidence |
|-----|--------|----------|
| **1. Never Red** | ✅ PASS | `--color-error: #d4b4ff` (purple), `--color-warning: #e9c400` (amber). No red in any token. |
| **2. Energy Adaptation** | ✅ PASS | Three modes via `[data-energy]`. Hook, CSS variables, utility classes all delivered. |
| **3. Shame-Free** | ✅ PASS | Assessment shows "Question X of ~Y" not percentages. Radar shows "Your strongest areas shine". No "you haven't done X". |
| **4. Animation Safety** | ✅ PASS | `--duration-max: 800ms`. `--spring-damping: 14`. `prefers-reduced-motion` disables ALL animations. `[data-energy="low"]` also disables. liquid-glass degrades to solid bg. |
| **5. One Primary CTA** | ✅ PASS | Liquid Glass Radar has single CTA. Assessment Card has only answer options. Bottom Tab is navigation only. |

## ADHD Rules Audit (top 9)

| Rule | Status |
|------|--------|
| One action per screen | ✅ Single CTA in radar, answers in assessment |
| Floor mechanic <2min | ✅ Assessment card renders instantly, first question fast |
| Variable reward magnitude | ⏳ Crystal system not yet implemented (blocked on CEO crystal economy) |
| No infinite scroll | ✅ No lists in delivered components |
| Clear structure | ✅ Consistent card layout, predictable navigation |
| Focus mode (energy=low) | ✅ Low strips to essentials, zero animation |
| No streak punishment | ⏳ MindShift not yet built |
| Self-aware humor | ⏳ Needs microcopy pass |
| Immediate feedback | ✅ 150ms transitions, energy-target sizing |

---

## For Atlas: Integration Checklist

1. **globals.css** — Already updated in place. Pull and verify `npm run build` passes.
2. **Bottom Tab** — Add `<BottomTabBar locale={locale} />` to root layout. Add `pb-20` to main content for spacing.
3. **Liquid Glass Radar** — Replace current radar usage on AURA results page.
4. **Energy Hook** — Call `useEnergyMode()` in root layout provider. Wire compact EnergyPicker in top bar.
5. **Assessment Card** — Replace current question-card.tsx usage in assessment flow.
6. **Verify** — Check `data-energy` attribute toggles correctly in browser DevTools.

---

## Open Items (not blocking Phase A)

- Figma token library (Tier 1-3 variables) — needs manual Figma work, can't be automated from Cowork
- Button System — shadcn button.tsx exists, needs product accent variants
- BrandedBy tab — disabled/hidden until product exists
- Supabase energy_level sync — stub in hook, needs auth integration
