# Ecosystem Redesign Analysis — Cowork → Atlas

**Date:** 2026-04-12
**Source:** 9 CEO research files + Constitution + Figma MCP audit
**Purpose:** Full analysis of ECOSYSTEM-REDESIGN-BRIEF-2026-04-14.md with implementation guidance

---

## 1. FIGMA AUDIT — CRITICAL FINDING

Queried Figma file `B30q4nqVq5VjdqAVVYRh3t` (57 variables mentioned in brief) via MCP:

- **Custom variables:** 0 found (searched: AURA, volaura, energy, purple, amber, error, warning)
- **Custom components:** 0 found (searched: button, card, component)
- **Custom styles:** 0 found for VOLAURA
- **Only match:** `M3/key-colors/primary` from default Material 3 Design Kit

**Conclusion:** The Figma file either has no custom design system yet, or the 57 variables are in a separate library file not linked. Atlas should verify — if this is the working file, the design system needs to be built from scratch in Figma before any frontend implementation.

---

## 2. CONSTITUTION COMPLIANCE MATRIX

Cross-referencing brief decisions against 5 Foundation Laws:

| Law | Brief Compliance | Gaps |
|-----|-----------------|------|
| **1. Never Red** | Brief specifies purple #D4B4FF errors, amber #E9C400 warnings | Compliant. But Figma has no tokens for these. Need `error/surface`, `error/text`, `warning/surface`, `warning/text` variables created. |
| **2. Energy Adaptation** | Brief mentions energy picker as P0 pre-launch blocker | No detailed energy-mode UI spec in brief. Need: Full/Mid/Low visual states for every screen. How does navigation change? Do animations reduce? Does content density change? |
| **3. Shame-Free** | ADHD research covers this well (no "you haven't done X") | Brief doesn't explicitly map shame-free language to component copy. Need: empty state copy guidelines, progress indicator wording, error message templates. |
| **4. Animation Safety** | Brief specifies spring damping ≥14, 150ms tabs, max 800ms non-decorative | Compliant. Add: `prefers-reduced-motion` must disable ALL non-essential motion. Brief mentions this but doesn't specify fallback behavior per component. |
| **5. One Primary CTA** | ADHD research rule: "one action per screen" | Brief doesn't map this per screen. Need: CTA hierarchy document — which action is primary on each of the ~15 key screens across 5 products. |

**19 Constitution pre-launch blockers status:** Energy picker, Pre-Assessment Layer, DIF audit, SADPP registration — none addressed by the brief's design decisions. These are product/regulatory blockers, not visual design.

---

## 3. DESIGN SYSTEM ARCHITECTURE — WHAT TO BUILD

### Token Architecture (from ecosystem-design-research.md)

The brief confirms a three-tier token system. Here's the implementation spec:

**Tier 1 — Global Primitives** (shared across all 5 products):
```
--color-purple-100 through --color-purple-900
--color-amber-100 through --color-amber-900
--color-neutral-50 through --color-neutral-950
--spacing-xs: 4px / --spacing-sm: 8px / --spacing-md: 16px / --spacing-lg: 24px / --spacing-xl: 32px
--radius-sm: 6px / --radius-md: 12px / --radius-lg: 16px / --radius-full: 9999px
--font-sans: Inter (body) / --font-display: chosen display font
--duration-fast: 150ms / --duration-normal: 300ms / --duration-slow: 500ms
--spring-damping: 14 (minimum)
```

**Tier 2 — Semantic Tokens** (meaning-based, theme-switchable):
```
--color-error-surface: var(--color-purple-200)    /* Law 1: NEVER red */
--color-error-text: var(--color-purple-400)        /* #D4B4FF */
--color-warning-surface: var(--color-amber-200)
--color-warning-text: var(--color-amber-500)       /* #E9C400 */
--color-success: green palette (NOT red/green binary — colorblind safe)
--color-surface-primary / --color-surface-secondary / --color-surface-elevated
--color-text-primary / --color-text-secondary / --color-text-disabled
```

**Tier 3 — Product Tokens** (per-product brand overlay):
```
VOLAURA:       --product-accent: #7C5CFC (purple)
MindShift:     --product-accent: #3B82F6 (blue)
Life Simulator: --product-accent: #F59E0B (amber/gold)
BrandedBy:     --product-accent: #EC4899 (pink)
ZEUS:          --product-accent: #10B981 (emerald)
```

### Component Library Priority

Based on ADHD-first research + brief:

1. **Bottom Tab Bar** (Discord pattern) — shared shell, 5 product tabs
2. **Energy Picker** (P0 blocker) — Full/Mid/Low selector, affects entire UI density
3. **AURA Radar** (Liquid Glass container) — identity-first, replaces profile page
4. **Card Component** — base card with energy-responsive density
5. **Button System** — primary (one per screen), secondary, ghost, destructive (purple not red)
6. **Assessment Flow** — question card, progress indicator (shame-free), answer options
7. **Character Avatar** (Habitica pattern) — gamified identity across products
8. **Crystal/Badge Display** — gamification layer
9. **Empty State** — shame-free language templates
10. **Toast/Notification** — purple errors, amber warnings

---

## 4. NAVIGATION ARCHITECTURE

Brief specifies: Discord bottom-tab + Duolingo colors + Habitica avatar.

**Recommended implementation:**

```
┌─────────────────────────────────────────┐
│  [Avatar]  Product Name    [Energy] [⚙]  │  ← Top bar (minimal)
├─────────────────────────────────────────┤
│                                         │
│           Main Content Area             │
│        (single primary CTA rule)        │
│                                         │
├─────────────────────────────────────────┤
│  🏠   📊   🧠   🎮   ⚡                │  ← Bottom tabs
│ Home  AURA  Mind  Life  ZEUS            │
│              Shift Sim                  │
└─────────────────────────────────────────┘
```

**Key decisions:**
- Bottom tab = product switcher (not page nav within product)
- Within-product navigation = horizontal scroll tabs or side drawer
- Active tab uses product accent color (Tier 3 token)
- Character avatar in top-left = identity anchor (Habitica pattern)
- Energy selector in top-right = always accessible (P0 requirement)
- Tab transitions: 150ms, spring damping ≥14

**375px breakpoint** (from research): Design mobile-first at 375px. This is the base. Larger screens get more breathing room but same layout.

---

## 5. ADHD-FIRST UX RULES — IMPLEMENTATION MAP

From adhd-first-ux-research.md (26 rules), the 9 highest-impact for implementation:

| Rule | Implementation | Component Affected |
|------|---------------|-------------------|
| One action per screen | CTA hierarchy doc needed | Every screen |
| Floor mechanic <2min | Assessment: first question in <30s, micro-task entry points | Assessment, MindShift |
| Variable reward magnitude, not existence | Crystal/badge values randomized within range, always earned | Gamification layer |
| No infinite scroll | Paginated lists, explicit "load more" | All list views |
| Clear structure | Consistent card grid, predictable layout | Layout system |
| Focus mode | Energy=Low strips everything to essentials | Energy system |
| No dopamine manipulation | No streaks that punish. Streaks celebrate, missing = neutral | MindShift habits |
| Self-aware humor | Tone of voice in microcopy (Tinkoff/Aviasales benchmark) | All copy |
| Immediate feedback | Every tap = visual response <100ms | Button/interaction layer |

---

## 6. BLIND SPOTS FROM CEO RESEARCH

blind-spots-analysis.md raises 10 critical issues. Three directly affect redesign:

1. **TAM 10-15x smaller than assumed** — Azerbaijan volunteer market is tiny. Design must support Phase 2 (universal skills) from day one. Don't over-invest in volunteer-specific UI that won't scale.

2. **5 products = debt bomb** — Redesign MUST use shared components aggressively. Any product-specific component is technical debt. Target: 80%+ component reuse across products.

3. **LTV/CAC broken in Azerbaijan** — Onboarding flow must be frictionless enough that word-of-mouth works. No complex sign-up. Assessment should be accessible before account creation (Pre-Assessment Layer = P0 blocker).

---

## 7. NEUROCOGNITIVE ARCHITECTURE IMPLICATIONS

From NEUROCOGNITIVE-ARCHITECTURE-2026.md — ZEUS product uses Global Workspace Theory. For the UI:

- ZEUS interface must visualize agent activity (workspace partitions: context, work, system, answer)
- Memory architecture (7 layers) needs a simplified user-facing view (not all 7 visible)
- Curiosity Engine scoring could surface in recommendations ("we think you'd find this interesting because...")
- This is Phase 3+ — don't design ZEUS UI now, but ensure the design system can accommodate it

---

## 8. GEMINI RESEARCH IMPLICATIONS

The 140K-word research covers AI memory, agile methodology, and handoff protocols. For the redesign specifically:

- **Markdown convergence** validates current approach (structured .md files over complex graph DBs)
- **Session capacity planning** confirms: keep design reviews in focused sub-sessions, not massive all-at-once reviews
- **Outcome-based metrics** should inform design: track Human Validation Time for design reviews, not just feature count

---

## 9. SUCCESS CRITERIA VERIFICATION

Brief lists 9 success criteria. Current status:

| # | Criterion | Status | Action Needed |
|---|-----------|--------|---------------|
| 1 | Constitution Law 1-5 pass | Partial | Energy picker UI spec missing, shame-free copy templates missing |
| 2 | 8 Crystal Laws pass | Not checked | Need Crystal Laws section of Constitution (beyond line 100) |
| 3 | Figma variables match code tokens | NOT MET | Figma has 0 custom variables. Must build token library. |
| 4 | Mobile-first 375px | Design decision made | Needs implementation verification |
| 5 | ADHD audit pass | Rules documented | Need formal audit checklist |
| 6 | prefers-reduced-motion | Specified in brief | Needs per-component behavior spec |
| 7 | 3 energy modes work | P0 blocker | No energy mode UI spec exists yet |
| 8 | Bottom tab nav works across products | Architecture defined | Needs Figma prototype |
| 9 | AURA radar renders with Liquid Glass | Concept defined | Needs technical spike (WebGL/Canvas vs CSS) |

---

## 10. RECOMMENDED IMPLEMENTATION ORDER FOR ATLAS

**Phase A — Foundation (before any screens):**
1. Create Figma token library (Tier 1 + Tier 2 + Tier 3 variables)
2. Create Tailwind 4 `@theme {}` block matching Figma tokens
3. Build Energy Picker component (P0 blocker)
4. Build Bottom Tab Bar component
5. Build Button System with one-primary-CTA enforcement

**Phase B — Core Screens:**
6. Assessment flow (shame-free, energy-responsive)
7. AURA Radar with Liquid Glass effect
8. Profile/Character page (avatar + badges)
9. Home dashboard (per-product, one CTA per section)

**Phase C — Cross-Product:**
10. Product switcher animation (150ms spring)
11. Notification system (purple errors, amber warnings)
12. Empty states with shame-free copy
13. Settings with energy mode persistence

**Phase D — Validation:**
14. Constitution audit (all 5 Laws + Crystal Laws)
15. ADHD audit (26-rule checklist)
16. prefers-reduced-motion full test
17. 375px responsive test across all screens
18. Playwright E2E for critical flows

---

## 11. TECH STACK CONFIRMATION

Brief says keep: shadcn/ui + Motion (Framer) + Recharts
Brief says add: Magic UI + ADHD layer + Liquid Glass
Brief says reject: Mantine, DaisyUI, GSAP, Aceternity

**Cowork agrees with all decisions.** Rationale:
- shadcn/ui = unstyled primitives, perfect for custom token system
- Motion = spring physics built-in (damping ≥14 easy to enforce)
- Magic UI = subtle effects without heavy JS (good for ADHD-safe decorative elements)
- Liquid Glass = CSS backdrop-filter + gradient, no heavy library needed
- Rejecting Mantine/DaisyUI = correct, they fight with custom tokens
- Rejecting GSAP = correct, Motion handles everything needed at lower bundle cost
- Rejecting Aceternity = correct, too decorative, violates Animation Safety law

**One addition to consider:** `tailwind-animate` or `tailwindcss-animate` for prefers-reduced-motion utility classes. Makes it trivial to conditionally disable animations.

---

## 12. OPEN QUESTIONS FOR ATLAS

1. **Figma file status** — Is B30q4nqVq5VjdqAVVYRh3t the correct working file? MCP found zero custom assets. Are tokens in a separate library file?

2. **Liquid Glass technical approach** — CSS `backdrop-filter: blur()` + gradient overlay, or WebGL/Canvas? CSS is lighter but less controllable. Recommend CSS-only with fallback.

3. **Character avatar system** — How complex? Static illustrated avatars (cheaper, faster) or dynamic composable parts like Habitica (complex but more engaging)? CEO research leans toward Habitica model.

4. **Energy mode persistence** — Stored in Supabase profile or localStorage? Recommend Supabase (syncs across devices) with localStorage cache for instant load.

5. **Crystal economy monetary policy** — blind-spots-analysis.md flags this as unresolved. Design can proceed with placeholder crystal values, but the economy rules need CEO decision before launch.

---

*Analysis complete. All 9 CEO research files read. Figma audited via MCP. Constitution cross-referenced. Ready for Atlas to begin Phase A implementation.*
