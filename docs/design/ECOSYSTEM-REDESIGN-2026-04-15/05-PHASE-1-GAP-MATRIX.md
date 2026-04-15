# Phase 1 Gap Matrix — synthesis

**Date:** 2026-04-15 · **Author:** Terminal-Atlas
**Inputs:** `03-UX-GAP-INVENTORY.md` (UX agent, 6 P0 + 7 P1 + 10 P2 + AZ cultural), `04-A11Y-AUDIT.md` (a11y agent, 5 P0 + 5 P1 + 4 P2 + contrast matrix)
**Method:** merge findings into a single priority matrix ranked by Impact × Constitution-weight × Effort-inverse.

---

## 1. Ranking formula

```
score = impact × constitution_weight × (1 / max(effort, 0.25))

impact:                0-3 (affects few users → affects all users)
constitution_weight:   0.5 (no Law hit), 1.0 (soft Law hit), 2.0 (hard Law violation)
effort:                0.25 / 0.5 / 1 / 2 / 4 / 8 (days; 0.25 = trivial one-liner)
```

Higher score = ship first. When scores tie, prefer the Law-violating item (hard safety over polish).

---

## 2. TIER-0 — ship before anything else visible to users (P0-code)

These are correctness bugs. They cost nothing narratively and fixing them is pure win.

| # | Item | Source | Law | Impact | Effort | Score | Fix file(s) |
|---|---|---|---|---|---|---|---|
| T0-1 | `aria-hidden` wraps `sr-only` table in radar-chart → AT gets zero data | A11Y P0-1 | none (WCAG) | 3 | 0.25 | 24.0 | `apps/web/src/components/aura/radar-chart.tsx:89` |
| T0-2 | Focus ring `#C0C1FF` on `bg-primary` `#C0C1FF` = 1:1 invisible | A11Y P0-2 | none | 3 | 0.25 | 24.0 | `apps/web/src/app/globals.css:118` + `button.tsx:81` — introduce `--color-ring-focus: #FFFFFF` |
| T0-3 | Timer `aria-live="off"` — countdown not announced to AT | A11Y P0-4 | none | 2 | 0.5 | 8.0 | `apps/web/src/components/assessment/timer.tsx:44-78` |
| T0-4 | Textarea `open-text-answer` has no focus ring | A11Y P0-3 | none | 2 | 0.25 | 16.0 | `apps/web/src/components/assessment/open-text-answer.tsx:112` |
| T0-5 | No skip-navigation link anywhere | A11Y P0-5 | none | 2 | 0.5 | 8.0 | `apps/web/src/app/[locale]/(dashboard)/layout.tsx` + `a11y.skipToContent` i18n key |
| T0-6 | BrandedBy surface shows perpetual spinner — broken state | UX P0-03 | soft | 2 | 0.5 | 8.0 | `apps/web/src/app/[locale]/brandedby/page.tsx` — fallback "Coming soon" pattern |
| T0-7 | Subscription-cancelled uses English + destructive X icon | UX P0-04 | Law 1 hard | 2 | 0.5 | 16.0 | `subscription/cancelled/page.tsx` — neutral icon + AZ copy |
| T0-8 | Profile-edit form has English labels ("About you", "Public profile") | UX P0-05 | Law 3 soft | 2 | 0.25 | 16.0 | i18n keys `about_you`, `public_profile`, `org_discoverable` in AZ + EN |
| T0-9 | Two equal primary CTAs on subscription-cancelled | UX P0-06 | Law 5 hard | 2 | 0.25 | 32.0 | same file as T0-7, demote second to text link |

**Total T0 effort:** ~3 engineering days. Total score ceiling: 152. Every item ships in Phase 1 week 1.

---

## 3. TIER-1 — ship alongside core redesign (P0-UX + P1-code)

These require some design decision but are P0 for either user harm or Law compliance.

| # | Item | Source | Law | Impact | Effort | Score | Notes |
|---|---|---|---|---|---|---|---|
| T1-1 | Landing shows "0" on two stat counters — anti-social-proof for AZ | UX P0-01 | Law 3 soft | 3 | 1 | 6.0 | Gate display below threshold; swap for qualitative statement |
| T1-2 | Leaderboard + Discover redirect to login — B2B funnel dies | UX P0-02 | Law 5 soft | 3 | 2 | 3.0 | Build public read-only teaser variants |
| T1-3 | Button gradient end `#8083FF` + `#1000A9` text = 4.0:1 fails AA | A11Y P1-1 | none | 3 | 0.5 | 12.0 | globals.css — shift gradient end to `#6366FF` OR text to `#FFFFFF` |
| T1-4 | Framer Motion animations bypass `prefers-reduced-motion` | A11Y P1-3 | Law 4 hard | 3 | 1 | 12.0 | Add `useReducedMotion()` guard to `badge-display.tsx`, `hero-section.tsx`, `aura-score-widget.tsx` |
| T1-5 | Onboarding "ADDIM 1/3" text counter = quantified incompleteness | UX P1-02 | Law 3 hard | 2 | 0.5 | 16.0 | Replace fraction with dots; optional AZ labels Başlanğıc / almost / final |
| T1-6 | AURA empty state missing identity aspiration framing | UX P1-01 | Law 3 soft | 2 | 0.5 | 4.0 | `apps/web/src/app/[locale]/aura/page.tsx` — aspiration line above CTA |
| T1-7 | Energy picker not visible in any screenshot (Law 2 fail) | UX P1-05 | Law 2 hard | 3 | 2 | 6.0 | Confirm three top-bar icons = picker; add visible label + aria. If not, build persistent picker |
| T1-8 | `bottom-tab-bar` wrong ARIA (tablist without arrow-keys) | A11Y P1-4 | none | 2 | 0.5 | 8.0 | Switch to `role="navigation"` + `aria-current` — matches working `bottom-nav.tsx` |
| T1-9 | Voice/mic toggle same aria-label both states | A11Y P1-2 | none | 1 | 0.25 | 8.0 | i18n `startListening` / `stopListening` |
| T1-10 | Life Sim "Pul: 0" shown on empty character | UX P1-04 | Crystal Law 4 | 2 | 0.5 | 8.0 | Gate "Pul" until first crystal; "Başlanğıc" instead of 0 |
| T1-11 | Notifications empty state has no CTA (dead end) | UX P1-07 | Law 3 soft | 2 | 0.25 | 8.0 | Secondary CTA nudging to share |
| T1-12 | Energy-low `min-target: 56px` not applied to hardcoded button sizes | A11Y P1-5 | Law 2 soft | 2 | 1 | 2.0 | Apply `.energy-target` class to Button sizeClasses |
| T1-13 | Assessment list shows English social-proof inside AZ session | UX P1-03 | Law 3 soft | 2 | 0.25 | 4.0 | `assessment.social_proof` key |
| T1-14 | Signup mobile has 6+ fields visible simultaneously | UX P1-06 | Law 5 hard | 3 | 2 | 6.0 | Split into 2 steps; progressive reveal |

**Total T1 effort:** ~11 engineering days. Covers hard Law violations across Laws 2, 3, 4, 5.

---

## 4. TIER-2 — batch during token/design-system rebuild

These align with `01-TOKENS-AUDIT.md` + `02-FIGMA-RECONCILIATION.md` recommended changes. Do them all in one pass while we're editing globals.css anyway.

| # | Item | Source | Effort | Notes |
|---|---|---|---|---|
| T2-1 | 6 duplicate token definitions (fixed-dim == primary, etc.) | 01-TOKENS §2 | 0.25 | Introduce darker shades for `-dim` tokens |
| T2-2 | 12 hardcoded color literals in utility classes | 01-TOKENS §3 | 0.5 | Replace with `var(--token)` + `color-mix()` |
| T2-3 | `aura-glow-*` vs `badge-glow-*` naming consolidation | 01-TOKENS §4 | 0.25 | Rename to `-hero-` / `-inline-` |
| T2-4 | 8 missing token categories (focus-ring, motion easing, scrim, blur levels, typography, line-height, breakpoints, elevation) | 01-TOKENS §5 | 1 | Add tokens + propagate to Tailwind v4 `@theme` |
| T2-5 | Surface `Base #0A0A0F` missing from CSS (in Figma) | 02-FIGMA §1 | 0.25 | Add `--color-surface-base` |
| T2-6 | `--color-success: #6ee7b7` drift (Figma `#34D399`) | 02-FIGMA §2 | 0.25 | Update token |
| T2-7 | Glass card blur spec drift (Figma 16px / 6%, code 12px / 12%) | 02-FIGMA §4 | 0.25 | Reconcile `.liquid-glass` to Figma |
| T2-8 | Typography size scale absent — 5 tiers in Figma | 02-FIGMA §3 | 0.5 | Add `--text-caption/body/overline/section/page` |
| T2-9 | `tabular-nums` not applied to AURA score display | UX P2-08 | 0.25 | `font-variant-numeric: tabular-nums` on score element |
| T2-10 | "INVITE FRIENDS" section on profile English-only | UX P2-09 | 0.25 | i18n |
| T2-11 | Leaderboard middleware: either enforce public or remove from public list | UX P2-10 | 0.5 | audit middleware chain |
| T2-12 | Modal focus-return to trigger on close (Escape path) | A11Y P2-2 | 1 | Generic FocusTrap utility |
| T2-13 | Share-prompt dialog should use `aria-labelledby` | A11Y P2-3 | 0.25 | |
| T2-14 | AZ charset visual regression test | A11Y P2-4 | 1 | Playwright screenshot test with AZ glyphs |

**Total T2 effort:** ~7 days. Delivers a clean token base + polish.

---

## 5. CROSS-ECOSYSTEM — Phase 2 scope-defining decision

**From UX §7, single CEO decision required.** Four options for the "Coming soon" ecosystem surfaces (MindShift, ATLAS, BrandedBy, Life Sim):

| Option | Gist | Cost | Ecosystem-narrative value |
|---|---|---|---|
| A | Rebrand as "Preview" with waitlist capture + AZ value prop | 1 day | Low — still stubs |
| B | Gate stubs for first-30-day users; Bottom nav = 3 items | 2 days (feature-flag) | Medium — reduces cognitive noise, preserves stubs |
| C | Make Life Sim surface fully data-driven from VOLAURA events | 5 days | High — first real cross-ecosystem bridge |
| D | Remove ecosystem surfaces from VOLAURA web until real interaction exists | 1 day | Low — clean standalone, but kills cross-product story |

**Atlas Strange-pattern recommendation (evidence from UX audit):**

**Option B + C hybrid — ship in this order:**

1. Week 1: Option B cheap gate. Hide MindShift / ATLAS / BrandedBy from bottom nav for users in first 30 days (`auth_user.created_at + 30 days`). Reduces Leyla's first-week cognitive load immediately.
2. Week 2-3: Option C on Life Sim. Wire VOLAURA `character_events` to visible XP on the Life Sim surface. Crystal balance comes from real assessment completions. One real cross-ecosystem bridge ships.
3. MindShift + ATLAS + BrandedBy stay as stubs with "Preview" framing (Option A lite) for 30-day+ users only.

**Why:**
- Option D (remove) loses the ecosystem story which is a core VOLAURA differentiator.
- Option A alone (rebrand all to Preview) is decoration without substance.
- Option B alone doesn't build any real ecosystem value.
- Option C alone overloads new users' first week.
- The hybrid ships narrative + scope in 6 days across two weeks.

**Fallback if CEO disagrees:** Option B alone (cheapest, 2 days, biggest UX relief).

---

## 6. AZ-specific workstream

These are AZ-cultural items from UX §6 that don't fit cleanly in T0-T2 because they require translation + cultural review, not code-only changes.

| # | Item | Source | Owner suggestion |
|---|---|---|---|
| AZ-1 | Landing "What your profile could look like" English heading | UX AZ-01 | Cowork + AZ writer |
| AZ-2 | "EKSPERT DOGRULAMALARI" missing Ğ diacritic | UX AZ-02 | Frontend + AZ font audit |
| AZ-4 | Referral copy "INVITE FRIENDS / Share this link…" English | UX AZ-04 | Cowork + AZ writer — rephrase to "tövsiyyə edin" warm-network framing |
| AZ-5 | AURA privacy "Gizli" option — reframe culturally | UX AZ-05 | Product decision + UX writer |
| AZ-6 | Landing "Necə işləyir" section body not rendering | UX AZ-06 | Frontend debug |

These become a single PR once translations land. Budget: 1 day coding after AZ writer hands back copy.

---

## 7. Priority execution order — week-by-week

### Week 1 (ship to prod)
- All of TIER-0 (9 items, ~3 days)
- T1-5 (onboarding fraction), T1-6 (AURA identity line), T1-8 (bottom-tab ARIA), T1-9 (voice label), T1-11 (notifications CTA), T1-13 (AZ social proof) — all ≤0.5 days each, batch into one PR
- T2-1 through T2-9 (the globals.css pass) — one PR after T0-2 lands

### Week 2
- T1-1 (landing stat gate), T1-3 (button gradient), T1-4 (Framer Motion rescue), T1-10 (Life Sim Pul gate), T1-12 (energy-target rollout)
- Start ecosystem Option B (gate stubs from first-30-day bottom nav)

### Week 3
- T1-2 (public teasers for leaderboard + discover) — moderate design work
- T1-7 (energy picker visibility) — requires design decision
- T1-14 (signup progressive disclosure) — requires UX work
- Ecosystem Option C work on Life Sim

### Week 4
- AZ workstream after translations land
- T2-11, T2-12, T2-14 (polish items requiring more design taste)

**Gate G2 (end of week 3):** re-run a11y-scanner on the codebase. Target: 85/100, WCAG AA achieved. Re-run product-ux: target 65/100+ (floor raised).

---

## 8. Who does what

| Agent / human | Items |
|---|---|
| `a11y-scanner` (pre-ship verification each week) | Validate T0 fixes after landing. Re-score after each tier. |
| `product-ux` (bi-weekly) | Validate UX-layer changes. Flag new regressions. |
| `code-review-swarm` | Before each PR merge |
| Cowork-Atlas | AZ workstream + cross-ecosystem copy |
| Terminal-Atlas (me) | T0 ship, T1 plan, T2 execution, coordinator routing gap fix |
| CEO | Ecosystem option decision (§5), energy-picker design call (T1-7), privacy framing (AZ-5) |

---

## 9. Known unknowns (call out explicitly so next Atlas doesn't stumble)

- **Agent findings not yet verified by code-read.** UX P0s and A11Y P0s are agent-reported. Before starting T0 implementation, open each cited file and confirm symptom. Class 3 prevention.
- **~12 dynamic-route screenshots missing** (`[sessionId]`, `[username]`, `[id]` routes). May surface additional P0s when real data lands.
- **Figma formal `get_variable_defs`** still requires human in Figma desktop. Current token map is scraped from layer names.
- **Coordinator squad gap** (SECURITY/INFRA/ECOSYSTEM only) — DESIGN squad addition is its own small project. Proposal should land in `memory/swarm/proposals.json`.
- **Test user `270f5710-067a-425b-a948-1e4f37bbcd62`** created on prod during P0.3. Cleanup when count >3 per `incidents.md`.

---

## 10. Budget

~21 engineering days across 4 weeks to ship TIER-0 + TIER-1 + TIER-2 + AZ + ecosystem B+C. Deliverables at each gate:
- G1 (end week 1): T0 + cheap T1 shipped, a11y score ≥70, AA compliance on text contrasts
- G2 (end week 3): all TIER-1, all TIER-2, a11y ≥85, WCAG AA achieved, UX score ≥65
- G3 (end week 4): AZ workstream, ecosystem Life Sim bridge live, cross-ecosystem coherence story visible on hero

MEMORY-GATE: task-class=doc-update · SYNC=⏭️ · BRAIN=⏭️ · sprint-state=✅ · extras=[03-UX, 04-A11Y, 01-TOKENS, 02-FIGMA, 00-BASELINE, ECOSYSTEM-CONSTITUTION] · proceed
