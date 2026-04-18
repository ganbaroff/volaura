# Design Manifesto — Gap Analysis

**Date:** 2026-04-16
**Method:** grep/audit of apps/web/src/ against DESIGN-MANIFESTO.md 7 Laws
**Scope:** 55 pages, 78 components, globals.css, i18n

---

## Verdict: 70% aligned, 30% needs work

The foundation is strong — Constitution Laws embedded, design tokens solid, energy system wired. But Phase 3 Polish has gaps that separate "working product" from "world-class product."

---

## GAP 1: Spinners vs Skeletons (Law 6: Craft in the Details)

**Finding:** 63 spinner instances (Loader2 + animate-spin) vs 70 skeleton usages. Ratio should be 0 spinners : all skeletons.

**Worst offenders (bare spinners, no skeleton):**
- `loading.tsx` (dashboard catch-all) — bare Loader2
- `my-organization/page.tsx` — 2 spinners
- `my-organization/invite/page.tsx` — spinner
- `org-volunteers/page.tsx` — 2 spinners
- `notifications/page.tsx` — spinner
- `events/[eventId]/attendees/page.tsx` — spinner
- `brandedby/generations/[id]/page.tsx` — spinner
- `verify/[token]/page.tsx` — spinner
- `reset-password/page.tsx` — spinner

**Fix:** Replace every `<Loader2 className="animate-spin" />` with page-specific `<Skeleton>` layouts that match the actual content structure. The user should see the shape of the page before the data arrives.

**Priority:** P1 — visible on every page load

---

## GAP 2: Streak Shame Language (Law 4: Calm is the Luxury)

**Finding:** `"crystalFading": "Keep your streak alive this week"` in tribe-card.tsx

This is streak punishment language. "Keep alive" implies death if you don't act. Constitution says no streak punishments.

**Fix:** Rephrase to opportunity framing: "Your tribe earned X crystals this week" (past positive) or remove the fading urgency entirely.

**Priority:** P1 — directly violates Constitution

---

## GAP 3: Autoplay Video (Law 4: Calm is the Luxury)

**Finding:** `autoPlay` in `brandedby/generations/[id]/page.tsx:365`

**Fix:** Remove autoPlay. Let user initiate playback. Add poster frame.

**Priority:** P2

---

## GAP 4: Typography Scale Not in CSS (Law 6: Craft in the Details)

**Finding:** Figma defines 5 explicit type sizes (24/18/14/12/10px). globals.css has font families but NO size tokens.

Components use arbitrary Tailwind classes (text-sm, text-lg, text-2xl) instead of semantic tokens. This means:
- No single source of truth for type scale
- AZ text length (+20-30%) not accounted for systematically
- Energy mode can't adjust type density

**Fix:** Add to globals.css @theme:
```css
--text-page: 24px;
--text-section: 18px;
--text-body: 14px;
--text-caption: 12px;
--text-overline: 10px;
--tracking-overline: 0.15em;
```

Then replace ad-hoc Tailwind type classes with semantic tokens in components.

**Priority:** P1 — foundational, blocks consistent typography

---

## GAP 5: Focus Ring (Law 6: Craft in the Details)

**Finding:** `--color-ring-focus: #FFFFFF` defined in globals.css, but no custom focus-visible styles applied globally. Most components rely on Tailwind's default `focus:ring` or shadcn's built-in focus.

**Fix:** Add global focus-visible style:
```css
:focus-visible {
  outline: 2px solid var(--color-ring-focus);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
```
Ensure every interactive element has visible, consistent focus indication.

**Priority:** P1 — WCAG 2.1 AA requirement

---

## GAP 6: Figma ↔ Code Token Drift (Law 3: Depth Through Light)

**Finding (from 02-FIGMA-RECONCILIATION.md):**
- Surface base: Figma #0A0A0F vs code #0d0d15
- Success: Figma #34D399 vs code #6ee7b7
- Glass blur: Figma 16px vs code 12px
- Glass border: Figma 6% white vs code 12%
- Product accent colors: NOT in Figma

**Fix:** CSS follows Figma as source of truth for visual design. Update globals.css to match Figma values. Document product accents in Figma.

**Priority:** P2 — visual polish

---

## GAP 7: No Red — CLEAN ✅

Zero instances of text-red, bg-red, border-red, ring-red in source. Constitution Law 1 fully enforced.

---

## GAP 8: Leaderboard — CLEAN ✅

Leaderboard route exists but redirects with clear Constitution comments. All competitive framing removed from dashboard. Crystal Law 5 enforced.

---

## GAP 9: Profile Completion % — CLEAN ✅

No "X% complete" patterns found. Onboarding uses progress bar with explicit comment: "not X% complete (Constitution Law 3 shame-free)." safety-block.tsx has explicit comment: "no profile-percent indicators."

---

## GAP 10: Thin Fonts in Dark Mode — CLEAN ✅

No font-light, font-thin, or font-extralight in components. Body text uses regular (400) minimum.

---

## GAP 11: Score-as-Headline Check (Law 5: Identity First)

**Finding:** Assessment complete page (complete/page.tsx) uses identity framing with percentile as context — appears correct from grep. Need visual verification.

**Action:** Visual audit needed — screenshot assessment complete screen to verify identity headline is dominant.

**Priority:** P2 — verify visually

---

## SUMMARY: Actionable Fixes

| # | Gap | Priority | Effort | Law |
|---|-----|----------|--------|-----|
| 1 | Replace 63 spinners with skeletons | P1 | 3-4 hours | Law 6 |
| 2 | Fix streak shame language | P1 | 15 min | Law 4 |
| 3 | Remove autoPlay | P2 | 5 min | Law 4 |
| 4 | Add typography scale tokens | P1 | 1 hour | Law 6 |
| 5 | Global focus-visible style | P1 | 30 min | Law 6 |
| 6 | Reconcile Figma ↔ CSS tokens | P2 | 1 hour | Law 3 |
| 7-10 | Clean — no action | — | — | — |
| 11 | Visual verify identity-first | P2 | 15 min | Law 5 |

**Total P1 effort (product-level):** ~5-6 hours
**Total P2 effort (product-level):** ~1.5 hours

---

## ECOSYSTEM-LEVEL GAPS (v2 — added after CEO correction)

The product-level audit above missed the forest. These gaps are about whether 5 faces feel like one body.

### EGAP 1: No Face-Aware Component Theming (Principle 1: Shared Skeleton, Different Skin)

**Finding:** Components are VOLAURA-only. There is no mechanism for a Card or Button to change accent color when the user is in the MindShift face vs VOLAURA face. Product accents exist in CSS (`--color-product-volaura`, etc.) but no component reads them dynamically.

**What's needed:** A `face` context (React Context or CSS attribute like `[data-face="mindshift"]`) that all Tier 3 (product) tokens respond to. When the user switches tabs, `data-face` changes on the layout root, and every component that uses `--color-accent` automatically re-themes.

**Status:** NOT STARTED — critical ecosystem infrastructure
**Priority:** P0 — without this, five faces are impossible

### EGAP 2: No Cross-Face Event Display (Principle 2: Data Flows Freely)

**Finding:** `character_events` table exists. `ecosystem_events.py` service writes events. But NO frontend component consumes cross-product events. The activity-feed on dashboard shows VOLAURA-only activity. MindShift and Life Simulator pages are placeholders.

**What's needed:** A `<CrossFaceEventCard>` component that:
- Takes a raw event from character_events
- Renders it with the source face's accent + icon
- Includes a deep link to the relevant face
- Has face-specific copy templates ("assessment completed" vs "character gained XP")

**Status:** Backend ready (character_events + ecosystem_events.py), frontend NOT STARTED
**Priority:** P1 — this is how users discover the ecosystem is alive

### EGAP 3: No Agent Character Presence in UI (Principle 3: Agent Characters Are the UI)

**Finding:** 13 specialised perspectives + ~118 skill modules exist in swarm. Zero agent personalities surface in the user-facing UI. No character avatars, no agent voice in empty states, no "who is speaking" slot in any component.

**What's needed (Phase 2):** Design system accommodation for agent presence:
- Agent avatar component (small, circular, with face-specific accent ring)
- "Character speech" card variant (glass card with agent avatar + message)
- Notification source attribution ("Atlas noticed..." vs "MindShift coach suggests...")

**Status:** Design not started. No Figma. No component spec.
**Priority:** P2 — Phase 2 territory, but token slots should be reserved now

### EGAP 4: Tab Bar Lacks Face-Switch Animation (Principle 5: Tab Bar Is Spine)

**Finding:** Bottom Tab Bar exists (`components/navigation/bottom-tab-bar.tsx`). Switches pages. BUT:
- No accent color crossfade on tab switch
- No icon morph animation
- No prefetch of adjacent face content
- MindShift/LifeSim/BrandedBy tabs lead to placeholder pages

**What's needed:**
- CSS transition on tab accent (200ms ease-out)
- Icon scale animation (0.9→1.0, 150ms spring)
- TanStack Query prefetch for adjacent face data
- Real content in at least one non-VOLAURA face (MindShift is closest to buildable)

**Status:** Tab bar renders, but no transition polish. Placeholders everywhere except VOLAURA.
**Priority:** P1 for animation, P2 for real content in other faces

### EGAP 5: No Cross-Face Moment Design (Principle 4: Cross-Face Moments)

**Finding:** Zero cross-face moments exist in the UI. Assessment completion doesn't trigger Life Simulator events. Crystal earning doesn't animate a Life Sim character. No "your assessment result unlocked a new chapter" card anywhere.

**What's needed:**
- Cross-face moment card component (dual-accent, deep link, attribution copy)
- Event triggers: assessment_completed → Life Sim XP, badge_earned → MindShift celebration, streak_milestone → VOLAURA badge glow
- Frontend event listeners (Supabase realtime subscriptions on character_events)

**Status:** Backend bridge exists (character_events + emit functions). Frontend: ZERO.
**Priority:** P1 — this is the "magic moment" that proves the ecosystem

### EGAP 6: Energy System Not Tested Across Faces

**Finding:** Energy picker exists. `[data-energy]` CSS attribute works. But energy mode is only visually tested on VOLAURA pages. MindShift, Life Sim, BrandedBy, Atlas pages are placeholders — energy mode effects unknown.

**Priority:** P2 (blocked until faces have real content)

---

## UPDATED SUMMARY

| # | Gap | Priority | Layer | Effort |
|---|-----|----------|-------|--------|
| EGAP 1 | Face-aware component theming (data-face context) | P0 | Ecosystem | 2-3 hours |
| EGAP 2 | Cross-face event display | P1 | Ecosystem | 4-5 hours |
| EGAP 3 | Agent character UI presence | P2 | Ecosystem | Design phase |
| EGAP 4 | Tab bar face-switch animation | P1 | Ecosystem | 2 hours |
| EGAP 5 | Cross-face moment cards | P1 | Ecosystem | 3-4 hours |
| GAP 1 | Replace 63 spinners with skeletons | P1 | Product | 3-4 hours |
| GAP 2 | Fix streak shame language | P1 | Product | 15 min |
| GAP 3 | Remove autoPlay | P2 | Product | 5 min |
| GAP 4 | Typography scale tokens | P1 | Product | 1 hour |
| GAP 5 | Global focus-visible style | P1 | Product | 30 min |
| GAP 6 | Figma ↔ CSS token drift | P2 | Product | 1 hour |

**P0 (blocks everything):** Face-aware theming — ~2-3 hours
**P1 total:** ~14-16 hours
**P2 total:** ~2.5 hours + design phase for agent characters
