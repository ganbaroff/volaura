# P0.4 — Design Tokens Audit (globals.css)

**Date:** 2026-04-15 · **Author:** Terminal-Atlas · **Source:** `apps/web/src/app/globals.css` (433 lines)
**Depends on:** 00-BASELINE.md · **Feeds:** Phase 1 design brief, Figma `get_variable_defs` reconciliation

---

## TL;DR

- 3-tier token architecture is in place (primitives / semantic / product) — structurally sound.
- Constitution Laws 1, 2, 4 are encoded as tokens correctly.
- **12 hardcoded color literals** in utility classes that should reference tokens.
- **6 duplicate token definitions** (same hex on both sides of `=` assignment).
- **2 redundant utility class families** (`aura-glow-*` vs `badge-glow-*`) — pick one.
- **8 missing token categories** needed for redesign (focus ring, motion easing, scrim, blur levels, typography scale, line-height, breakpoints, elevation layers).
- Product accent palette (`#7C5CFC` Volaura purple) does not visually match primary primitive palette (`#c0c1ff` lavender) — intentional separation but undocumented.

---

## 1. Constitution compliance (✅ clean)

| Law | Token(s) | File line | Verdict |
|---|---|---|---|
| 1 — errors purple, warnings amber | `--color-error: #d4b4ff`, `--color-warning: #e9c400` | 67, 73 | ✅ encoded |
| 2 — energy modes | `[data-energy="full\|mid\|low"]` blocks | 228-255 | ✅ 3 modes with spacing/animation/min-target |
| 4 — max 800ms | `--duration-max: 800ms` | 173 | ✅ primitive present |
| 4 — prefers-reduced-motion | `@media (prefers-reduced-motion: reduce)` | 386-401 | ✅ full override |
| 4 — spring damping ≥ 14 | `--spring-damping: 14` | 176 | ✅ at floor |

---

## 2. Duplicate token definitions (6 findings)

These pairs have identical hex values. Either the second is a stub waiting for theme variation, or one is redundant.

| Token A | Token B | Value | Risk |
|---|---|---|---|
| `--color-surface` | `--color-surface-dim` | `#13131b` | Breaks M3 convention (dim should be darker) |
| `--color-surface-bright` | `--color-surface-variant` | `#34343d` | Two semantic names, one value |
| `--color-surface-tint` | `--color-primary` | `#c0c1ff` | M3 tint = primary is conventional, leave but document |
| `--color-primary-fixed-dim` | `--color-primary` | `#c0c1ff` | `fixed-dim` should be darker shade |
| `--color-secondary-fixed-dim` | `--color-secondary` | `#bdc2ff` | Same issue |
| `--color-tertiary-fixed-dim` | `--color-tertiary` | `#e9c400` | Same issue |

**Cross-palette collision (intentional but flag-worthy):**
- `--color-warning` == `--color-tertiary` == `#e9c400` — amber serves both. Document: "warning reuses gold primitive; if tertiary brand accent changes, add distinct warning primitive."

**Gold inconsistency:**
- `--color-aura-gold: #ffd700` (badge, line 99) vs `--color-tertiary: #e9c400` (primitive, line 57) — two golds. Badge gold is brighter/yellower. Keep split IF intentional for Constitution Law 8 (AURA tier distinction), else collapse.

---

## 3. Hardcoded color literals in utility classes (12 findings)

Should reference tokens so themes are portable.

| Line | Class | Hardcoded value | Should reference |
|---|---|---|---|
| 193 | `body` | `#13131b` | `var(--color-surface)` |
| 194 | `body` | `#e4e1ed` | `var(--color-on-surface)` |
| 205 | `::-webkit-scrollbar-track` | `#13131b` | `var(--color-surface)` |
| 208 | `scrollbar-thumb` | `#464554` | `var(--color-outline-variant)` |
| 212 | `scrollbar-thumb:hover` | `#908fa0` | `var(--color-outline)` |
| 217-218 | `::selection` | `rgba(192,193,255,0.2)`, `#e4e1ed` | `--color-primary` with alpha, `--color-on-surface` |
| 277-281 | `.liquid-glass` | 4 rgba literals of primary | Token-ize as `--glass-*` layer |
| 293 | `.glass-header` | `rgba(19,19,27,0.7)` | `--color-surface` with alpha |
| 300 | `.glass-nav` | `rgba(27,27,35,0.8)` | `--color-surface-container-low` with alpha |
| 321, 326 | `.ambient-glow-*` | `rgba(192,193,255,0.08)`, `rgba(189,194,255,0.05)` | `--color-primary`, `--color-secondary` with alpha |
| 333-337 | `.btn-primary-gradient` | 4 hex literals | `--color-primary`, `--color-primary-container` |
| 342 | `.podium-gradient` | 2 rgba literals | `--color-surface-container-high`, `--color-surface-container-low` |
| 414-418 | `.mesh-gradient-hero` | 3 rgba literals + var | Token-ize primary/secondary rgba halos |
| 423, 425, 429, 432 | `.badge-glow-*` | 4 AURA colors literally | `var(--color-aura-*)` with rgba wrapper |
| 307, 310, 313, 316 | `.aura-glow-*` | same 4 AURA colors + primary halo for platinum | same |

**Rule:** CSS custom properties do not support alpha-from-hex at declaration time without `color-mix()`. For redesign, switch to `color-mix(in srgb, var(--color-primary) 8%, transparent)` where browser support matters (Chromium 111+, Safari 16.4+ — all target browsers covered).

---

## 4. Redundant utility class families

`aura-glow-*` (lines 306-317) and `badge-glow-*` (lines 421-433) both do `box-shadow` with AURA tier colors. Values differ slightly:

| Tier | `.aura-glow-*` outer shadow | `.badge-glow-*` outer shadow |
|---|---|---|
| platinum | `0 0 40px rgba(229,228,226,0.4)` + indigo halo | `0 0 8px rgba(229,228,226,0.3)` + tighter halo |
| gold | `0 0 30px rgba(255,215,0,0.3)` | `0 0 8px rgba(255,215,0,0.3)` + tighter halo |
| silver | `0 0 25px rgba(192,192,192,0.2)` | `0 0 8px rgba(192,192,192,0.2)` + tighter halo |
| bronze | `0 0 20px rgba(205,127,50,0.15)` | `0 0 8px rgba(205,127,50,0.25)` + tighter halo |

**Decision needed:** `aura-glow-*` = large ambient (profile hero, badge display page), `badge-glow-*` = compact inline (list rows, cards). If that's the intent, rename to `aura-glow-hero-*` and `aura-glow-inline-*` for clarity. Consolidate to one naming family with modifier.

---

## 5. Missing token categories for redesign

These are needed for Phase 1/2 design work. Add during Phase 1 token pass.

| Category | Why needed | Proposed token(s) |
|---|---|---|
| Focus ring distinct from selection ring | Accessibility WCAG 2.2 — focus indicator must be 3:1 contrast | `--ring-focus`, `--ring-focus-offset` |
| Motion easing curves | 5 duration tokens exist but no easing — all uses rely on `ease-out` hardcoded | `--ease-standard`, `--ease-decelerate`, `--ease-accelerate`, `--ease-bounce` (for crystal earn) |
| Scrim / overlay | Modals currently use inline rgba | `--color-scrim`, `--opacity-scrim-light`, `--opacity-scrim-heavy` |
| Glass blur levels | 3 classes hardcode `blur(12px)` | `--blur-sm: 6px`, `--blur-md: 12px`, `--blur-lg: 24px` |
| Typography scale | Only families, no sizes | `--text-xs` through `--text-6xl` or map to Tailwind v4 defaults explicitly |
| Line-height | No line-height tokens | `--leading-tight`, `--leading-normal`, `--leading-relaxed` |
| Breakpoints | Implicit via Tailwind | Document explicit mobile-first breakpoints for component contracts |
| Elevation layers | 3 shadows exist, no semantic mapping | `--elevation-card`, `--elevation-modal`, `--elevation-popover`, `--elevation-toast` |

---

## 6. Product palette mismatch (needs design decision)

| Token | Value | Visual |
|---|---|---|
| `--color-primary` (primitive) | `#c0c1ff` | Light lavender |
| `--color-primary-container` | `#8083ff` | Mid-indigo |
| `--color-product-volaura` (tier 3) | `#7C5CFC` | Saturated purple |

Volaura accent `#7C5CFC` does not chain with the primitive primary palette. It's from a different hue family. Either:
- (A) the tier-3 product accent is intentionally off-palette to distinguish cross-product chrome from in-product chrome — **document this in the design brief**; or
- (B) align `--color-product-volaura` to `#8083ff` or `#c0c1ff` for visual continuity.

**Recommendation:** Ask Cowork / CEO before changing. Log as Phase 1 open question.

---

## 7. Spacing comment — audit confirms fix is in place

Lines 136-143 document a prior regression (2026-04-14) where `--spacing-md: 1rem` collided with Tailwind v4's `max-w-md` scale and collapsed the signup page. No custom `--spacing-*` overrides present. Rule stands. Keep the comment block — it's load-bearing documentation.

---

## 8. Priority queue for Phase 1 token refactor

| # | Item | Effort | Blocker? |
|---|---|---|---|
| 1 | Replace 12 hardcoded literals with `var(--token)` + `color-mix()` | ~45 min | No — visual-identical |
| 2 | Add 8 missing token categories | ~30 min declaration + ~60 min propagation | Yes for Phase 2 — need before new components |
| 3 | Resolve `aura-glow-*` vs `badge-glow-*` rename/consolidate | ~20 min + search-replace | No |
| 4 | Decide product accent palette alignment (6) | 1 design decision | Yes — affects entire brand voice |
| 5 | Fix 6 duplicate token definitions (darker `-dim` variants) | ~15 min but requires palette values | Yes — `fixed-dim` tokens unusable currently |
| 6 | Reconcile Figma `get_variable_defs` output (when MCP reconnected) | Depends on drift | Yes for source-of-truth |

---

## 9. No changes made to globals.css in this audit

Read-only pass. All findings are proposals for Phase 1 execution.

MEMORY-GATE: task-class=doc-update · SYNC=⏭️ · BRAIN=⏭️ · sprint-state=✅ · extras=[globals.css, 00-BASELINE, STATE] · proceed
