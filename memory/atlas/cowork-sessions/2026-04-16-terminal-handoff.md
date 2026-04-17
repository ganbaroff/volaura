# Terminal-Atlas Handoff — Phase A: Fix the Floor

**From:** Cowork-Atlas (Ecosystem Design Lead)
**Date:** 2026-04-16 15:45 Baku
**Context:** CEO approved full design plan. This is the code execution handoff.
**Source doc:** `docs/design/ECOSYSTEM-RISK-ANALYSIS-AND-PLAN-2026-04-16.md`
**Gap Matrix:** `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/05-PHASE-1-GAP-MATRIX.md`

---

## Your mission: Phase A — ship these before any visual redesign

### Priority 1: T0 Accessibility Bugs (3 days)

Fix these 9 items. Each has exact file:line.

| # | What | File | Fix |
|---|------|------|-----|
| T0-1 | `aria-hidden` wraps sr-only table — AT gets zero AURA data | `components/aura/radar-chart.tsx:89` | Move sr-only table OUTSIDE the aria-hidden div |
| T0-2 | Focus ring #C0C1FF on bg-primary #C0C1FF = 1:1 invisible | `globals.css:118` + `components/ui/button.tsx:81` | Add `--color-ring-focus: #FFFFFF`, override `--color-ring` in @layer base |
| T0-3 | Timer aria-live="off" — countdown not announced | `components/assessment/timer.tsx:44-78` | Add `role="timer"`, change to `aria-live="polite"` `aria-atomic="true"`, throttle to 60s/30s/10s/5s |
| T0-4 | Textarea has no focus ring | `components/assessment/open-text-answer.tsx:112` | Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` |
| T0-5 | No skip-navigation link anywhere | `app/[locale]/(dashboard)/layout.tsx` | Add skip link as first child of body, add `id="main-content"` to main, add i18n key `a11y.skipToContent` |
| T0-6 | BrandedBy shows perpetual spinner | `app/[locale]/brandedby/page.tsx` | Replace with "Coming soon" pattern matching ATLAS/MindShift stubs |
| T0-7 | subscription-cancelled: English copy + destructive X icon | `subscription/cancelled/page.tsx` | Neutral icon, AZ copy "Heç bir xərc tutulmadı", single primary CTA |
| T0-8 | Profile-edit English labels ("About you", "Public profile") | Profile edit page | Add i18n keys: `about_you`, `public_profile`, `org_discoverable` in AZ + EN |
| T0-9 | Two equal primary CTAs on subscription-cancelled | Same file as T0-7 | Demote "Go to Settings" to text link, keep "Back to Dashboard" as sole primary |

### Priority 2: Build [data-face] Context System (2 days)

This is the P0 ecosystem blocker. Without it, every face renders as VOLAURA-purple.

**What to build:**
1. CSS attribute `[data-face]` on layout root element — values: `volaura`, `mindshift`, `lifesim`, `brandedby`, `atlas`
2. React context `FaceContext` that provides current face to all components
3. Tier 3 accent token per face in globals.css:
   - `[data-face="volaura"] { --color-face-accent: #7C5CFC; }`
   - `[data-face="mindshift"] { --color-face-accent: #3B82F6; }`
   - `[data-face="lifesim"] { --color-face-accent: #F59E0B; }`
   - `[data-face="brandedby"] { --color-face-accent: #EC4899; }`
4. Wire into `bottom-tab-bar.tsx` — active tab uses `--color-face-accent`
5. Wire into `layout.tsx` — set `data-face` attribute based on current route segment

**Gate:** Navigating to /mindshift should change bottom-tab accent to blue. Navigating to /lifesim should change to amber. Verifiable visually.

### Priority 3: Make Energy Picker Visible (2 days)

Constitution Law 2 requires Full/Mid/Low picker on every screen.

**Current state:** `useEnergyMode()` hook exists. `[data-energy]` CSS selectors exist in globals.css. Three icons in mobile top bar MIGHT be the picker — labels/active states invisible.

**What to do:**
1. Confirm if three top-bar icons are the energy picker. If yes, add visible labels + active state styling + aria attributes.
2. If no existing picker, build one: persistent accessible element, 3 states (Full/Mid/Low), visible label, `role="radiogroup"`.
3. Ensure `[data-energy]` attribute propagates on layout root.
4. Test: switching to Low should increase tap target sizes and reduce animations.

### Priority 4: Ecosystem Option B (2 days)

Hide stub surfaces from first-30-day users.

**What to do:**
1. In bottom-tab-bar, check `auth_user.created_at + 30 days`
2. If user < 30 days old: show only VOLAURA + Life Sim tabs (2 working products)
3. If user >= 30 days: show all 5 tabs with "Preview" framing on stubs
4. Feature-flag this via env var `ECOSYSTEM_STUBS_GATE=true` so we can toggle

---

## What NOT to do

- No visual redesign yet. Fix floor first.
- No new protocols or documents. Code only.
- No globals.css token cleanup yet — that's Phase B.
- Don't touch Figma.

## When you're done

Update `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/STATE.md` with completed items. Cowork-Atlas reviews design quality of each change.
