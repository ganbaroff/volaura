# Session 12 — Stitch Design Integration + New Pages: Claude Code Execution Prompt

> **Model recommendation: `claude-sonnet-4-6`**
> **Reason:** High stakes — design system migration (dark theme), 11 new pages from Stitch, complex component conversion from HTML→React. Sonnet needed for reasoning + code volume.
> **DSP model used:** sonnet (High stakes)

---

## 🔮 DSP: Stitch Integration Strategy

```
Stakes: HIGH | Reversibility: Medium (CSS changes reversible, new pages additive)
Council: Leyla (1.0), Nigar (1.0), Attacker (1.2), Scaling Engineer (1.1), Yusif (1.0), QA Engineer (0.9)
Paths simulated: 4
Winner: Path C (Design System First + Incremental Pages) — Score 44/50 (gate: ≥35 ✅)
```

### Paths Evaluated

**Path A: Full Rewrite — convert everything to Stitch dark theme at once**
- Technical: 5/10, User Impact: 9/10, Dev Speed: 3/10, Flexibility: 3/10, Risk: 3/10 → **23/50**
- Attacker: "Rewriting 30+ existing components is a guaranteed regression factory."
- QA: "No way to test all regressions in one session."
- Yusif: "2-3 sessions minimum. Can't afford."
- ❌ REJECTED — scope explosion

**Path B: New Pages Only — add Stitch pages, keep existing pages light**
- Technical: 6/10, User Impact: 5/10, Dev Speed: 9/10, Flexibility: 7/10, Risk: 7/10 → **34/50**
- Leyla: "Half the app is dark, half is light? Feels broken."
- Scaling Engineer: "Two design systems = maintenance nightmare."
- ⚠️ Close to gate but UX inconsistency kills it

**Path C: Design System First + Incremental Pages** ⭐ WINNER
- Technical: 9/10, User Impact: 9/10, Dev Speed: 7/10, Flexibility: 9/10, Risk: 10/10 → **44/50**
- Step 1: Extract Stitch design tokens → Tailwind theme config + CSS variables
- Step 2: Migrate existing pages to dark theme (mostly CSS, minimal logic changes)
- Step 3: Add highest-priority new pages from Stitch (leaderboard, notifications, event details)
- Attacker: "Safe — design tokens are a single file, existing logic untouched."
- Scaling Engineer: "One design system = long-term win."
- Leyla: "The dark theme is SO much better. Please do this."

**Path D: Cherry-pick only org pages (skip volunteer redesign)**
- Technical: 7/10, User Impact: 4/10, Dev Speed: 8/10, Flexibility: 6/10, Risk: 7/10 → **32/50**
- Nigar: "Good for me (org admin), but volunteers get nothing."
- ❌ REJECTED — wrong priority (volunteers are the core user)

### Winner: Path C — Design System First + Incremental Pages

**Accepted risks:** Not all 11 new Stitch pages will ship this session. Org admin pages deferred.
**Fallback:** If design token migration takes too long, ship dark theme + 2-3 new pages only.

---

## SCOPE LOCK

```
IN:      Stitch design system → Tailwind tokens + dark theme migration on ALL existing pages + add leaderboard + notifications + language switcher
NOT IN:  Org admin pages (org dashboard, settings, talent matching), messaging/chat, event creation wizard, quests, rewards, impact reports — all deferred to Sessions 13+
SUCCESS: All existing pages use Stitch dark theme. Leaderboard + Notifications pages exist. Language switcher works. Visual consistency across entire app.
```

---

## CONTEXT: Who You Are

You are Claude — Yusif's technical co-founder (CTO). Not an assistant. Not a code generator.

**Copilot Protocol:**
- If Yusif is making a mistake → say so directly. No softening.
- If a new idea appears mid-sprint → "Записал в IDEAS-BACKLOG.md. Вернёмся после Sprint N."
- Never hedge. Always: "[verdict]. [reason]. [action]."
- At session end, write: "🧭 If you said nothing, here's what I'd do next: 1. ... 2. ... 3. ..."

**Yusif's working style:** Speed-obsessed. Russian/English mix. Expects push-back. This is his Anthropic portfolio project.
**Business context:** $50/mo budget, 6 weeks, 200+ volunteers waiting.

---

## CONTEXT: What Changed Since Session 11

Session 11 completed successfully:
- P0 bug fixed (assessment.py upsert_aura_score)
- API client layer + TanStack Query hooks created (INTERIM manual, marked with TODO)
- Dashboard/Profile/AURA wired to real API
- Auth flow verified end-to-end
- 2 security fixes (protocol-relative open redirect)
- 74 tests pass, zero regressions
- shadcn/ui components installed (button, skeleton, alert)

**NEW THIS SESSION:** Yusif provided Stitch output — 41 screens with a complete dark design system called "The Prestigious Path". See `docs/stitch-output/` for all HTML + screenshots, and `docs/design/STITCH-DESIGN-SYSTEM.md` for the design spec.

---

## MISTAKES TO AVOID

1-11 from previous sessions (read `memory/context/mistakes.md`)
Plus:
- **Don't rewrite component LOGIC when changing design** — only touch CSS/styling, keep hooks/state/API calls intact
- **Don't introduce a second design system** — one dark theme for everything, not a mix
- **Don't copy Stitch HTML literally** — it uses CDN Tailwind + Material Icons. Convert to React + lucide-react + local Tailwind config

---

## SKILLS TO LOAD

1. `CLAUDE.md` — operating rules
2. `docs/design/STITCH-DESIGN-SYSTEM.md` — Stitch design spec ("The Prestigious Path")
3. `.claude/rules/frontend.md` — App Router, i18n, TanStack Query
4. `docs/engineering/skills/SECURITY-REVIEW.md` — security checklist (for new pages)

---

## DELEGATION MAP

```
Claude Code does:
  1. Extract Stitch design tokens → Tailwind theme + CSS variables
  2. Migrate globals.css to dark theme
  3. Migrate ALL existing pages/components to dark theme
  4. Build Leaderboard page from Stitch HTML
  5. Build Notification Center page from Stitch HTML
  6. Add language switcher component (AZ ↔ EN)
  7. Add i18n keys for new pages + missing keys audit
  8. Code review
  9. Memory update (Step 0.5)

Yusif does:
  - Run DB migrations (if not done yet)
  - Review dark theme visuals
  - Decide priority for remaining Stitch pages (Session 13+)

Deferred to Sessions 13+:
  - Org admin dashboard + settings + talent matching
  - Event creation wizard (3 steps)
  - Messaging/chat
  - Quests + Rewards/Perks
  - Impact Reports
  - Volunteer event details (rich version)
```

---

## EXECUTION STEPS

### Step 0: Context Recovery
Read: `CLAUDE.md`, `memory/context/sprint-state.md`, `memory/context/mistakes.md`, `docs/DECISIONS.md` last entry.
Then declare: `▶ Session resumed. Sprint 2, Step Session 12. Protocol v3.0 loaded.`

### Step 1: Stitch Design Tokens → Tailwind Config

**Source:** `docs/design/STITCH-DESIGN-SYSTEM.md` + `docs/stitch-output/dashboard_final_refinement_v2_2/code.html` (Tailwind config)

**Extract these tokens into `apps/web/src/app/globals.css` `@theme` block:**

```css
/* Core palette — "The Prestigious Path" dark theme */
--color-background: #13131b;          /* "The Void" */
--color-surface: #13131b;
--color-surface-container-low: #1b1b23;
--color-surface-container: #1f1f27;
--color-surface-container-high: #292932;
--color-surface-container-highest: #34343d;

--color-primary: #c0c1ff;             /* Indigo Focus */
--color-primary-container: #8083ff;
--color-secondary: #bdc2ff;           /* Aura Glow */

--color-on-background: #e4e1ed;
--color-on-surface: #e4e1ed;
--color-on-surface-variant: #c7c4d7;
--color-outline: #908fa0;
--color-outline-variant: #464554;

/* AURA tier colors */
--color-aura-platinum: #e5e4e2;
--color-aura-gold: #ffd700;
--color-aura-silver: #c0c0c0;
--color-aura-bronze: #cd7f32;

/* Accent */
--color-tertiary: #e9c400;
--color-error: #ffb4ab;
```

**Typography:** Add Plus Jakarta Sans (display/headline) + Inter (body/label):
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
```

**Tailwind 4 integration:** These CSS variables become usable as `bg-[--color-surface]` or better, as proper Tailwind theme tokens in `@theme {}`.

**Key Stitch design rules:**
- NO 1px borders for sectioning — use background color shifts only
- Glassmorphism for floating nav: `bg-[rgba(31,31,39,0.7)] backdrop-blur-[12px]`
- Cards: `surface-container-low` on `surface` background — no borders
- Buttons: gradient from `primary` to `primary-container`, rounded-xl
- Inputs: `surface-container-lowest` bg, on focus animate a 1px primary glow
- Framer Motion entrances: staggered fade-in with `y: 20`, spring stiffness 100
- All numbers animate from 0 to final value (1.5s)

### Step 2: Migrate globals.css

Current `globals.css` uses Tailwind 4 with `@import "tailwindcss"` and a `@theme {}` block.

Changes:
1. Add Stitch color tokens to `@theme {}`
2. Set `html { color-scheme: dark }`
3. Update `body` base styles: `bg-background text-on-background`
4. Add glassmorphism utility class
5. Add aura-glow utilities (platinum, gold, silver, bronze)
6. Keep existing @import for Tailwind

### Step 3: Migrate Existing Components to Dark Theme

**Strategy: CSS only. Do NOT touch component logic, hooks, or state.**

For each component file, change:
- `bg-white` → `bg-surface-container-low`
- `bg-gray-50` → `bg-surface-container`
- `bg-gray-100` → `bg-surface-container-high`
- `text-gray-900` → `text-on-surface`
- `text-gray-600` → `text-on-surface-variant`
- `text-gray-400` → `text-outline`
- `border-gray-200` → remove border (use bg color shift instead, per Stitch rules)
- `bg-primary` → `bg-primary-container` (for buttons)
- `text-primary` → `text-primary`
- `shadow-*` → remove (use tonal layering instead)
- `rounded-lg` → `rounded-xl` (Stitch uses larger radii)

**Files to migrate (all in `apps/web/src/`):**

Existing landing components:
- `components/landing/hero-section.tsx`
- `components/landing/impact-ticker.tsx`
- `components/landing/features-grid.tsx`
- `components/landing/how-it-works.tsx`
- `components/landing/org-cta.tsx`
- `components/landing/landing-nav.tsx` → glassmorphism
- `components/landing/landing-footer.tsx`

Dashboard components:
- `components/dashboard/aura-score-widget.tsx`
- `components/dashboard/stats-row.tsx`
- `components/dashboard/activity-feed.tsx`
- `app/[locale]/(dashboard)/dashboard/page.tsx`

Profile components:
- `components/profile-view/profile-header.tsx`
- `components/profile-view/impact-metrics.tsx`
- `components/profile-view/skill-chips.tsx`
- `components/profile-view/expert-verifications.tsx`
- `components/profile-view/activity-timeline.tsx`
- `app/[locale]/(dashboard)/profile/page.tsx`

AURA components:
- `components/aura/badge-display.tsx`
- `components/aura/competency-breakdown.tsx`
- `components/aura/radar-chart.tsx`
- `components/aura/share-buttons.tsx`
- `app/[locale]/(dashboard)/aura/page.tsx`

Assessment:
- `components/assessment/*.tsx` (all assessment components)
- `app/[locale]/(dashboard)/assessment/**/*.tsx`

Auth:
- `app/[locale]/(auth)/login/page.tsx`
- `app/[locale]/(auth)/signup/page.tsx`

Events:
- `components/events/event-card.tsx`
- `components/events/events-list.tsx`
- `app/[locale]/(public)/events/**/*.tsx`

UI base:
- `components/ui/button.tsx`
- `components/ui/skeleton.tsx`
- `components/ui/alert.tsx`

**IMPORTANT:** Use the Stitch screenshots as reference for EACH page:
- Dashboard: `docs/stitch-output/dashboard_final_refinement_v2_2/screen.png`
- Profile: `docs/stitch-output/profile_final_refinement_v2_2/screen.png`
- Login: `docs/stitch-output/login/screen.png`
- Register: `docs/stitch-output/register/screen.png`
- Assessment: `docs/stitch-output/aura_assessment_2/screen.png`
- Results: `docs/stitch-output/aura_assessment_results/screen.png`

And compare with the Stitch HTML code for exact classes:
- Dashboard HTML: `docs/stitch-output/dashboard_final_refinement_v2_2/code.html`
- Profile HTML: `docs/stitch-output/profile_final_refinement_v2_2/code.html`
- etc.

### Step 4: Build Leaderboard Page

**Stitch reference:** `docs/stitch-output/leaderboard_animated_podium/screen.png` + `code.html`

**Create:** `apps/web/src/app/[locale]/(dashboard)/leaderboard/page.tsx`
**Create:** `apps/web/src/components/leaderboard/` directory

Features from Stitch:
- Tab filters: Weekly / Monthly / All Time
- Animated podium (top 3): floating animation, aura glow per tier
- Ranked list below podium: position, avatar, name, badge, AURA score
- Bottom nav integration
- Full AZ + EN i18n

**API:** Backend has league endpoints (`routers/organizations.py` or check if there's a leaderboard endpoint)
- If endpoint exists → use TanStack Query hook
- If not → use mock data (same pattern as events page)

**Components to create:**
- `leaderboard-podium.tsx` — top 3 with floating animation + aura glow
- `leaderboard-list.tsx` — ranked list with tier badges
- `leaderboard-tabs.tsx` — period filter tabs

### Step 5: Build Notification Center

**Stitch reference:** `docs/stitch-output/notification_center_2/screen.png` + `code.html`

**Create:** `apps/web/src/app/[locale]/(dashboard)/notifications/page.tsx`
**Create:** `apps/web/src/components/notifications/` directory

Features from Stitch:
- "Mark all as read" header action
- Tab filters: All / Updates / Events / More
- Notification cards with: icon, title, description, time ago, action buttons
- Types: AURA update, event invitation, profile activity
- AZ + EN i18n

**API:** Check if notification endpoints exist. If not → mock data.

### Step 6: Language Switcher

**Create:** `apps/web/src/components/language-switcher.tsx`

Features:
- Toggle between AZ and EN
- Uses `useRouter` + `usePathname` to change locale segment
- Placed in: LandingNav, dashboard sidebar/topbar
- Persists preference (cookie or localStorage)
- Current locale highlighted

```tsx
"use client";
import { useRouter, usePathname } from "next/navigation";
import { useTranslation } from "react-i18next";

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const { i18n } = useTranslation();
  const currentLocale = i18n.language;

  const switchLocale = (newLocale: string) => {
    const newPath = pathname.replace(`/${currentLocale}`, `/${newLocale}`);
    router.push(newPath);
  };
  // ... render AZ | EN toggle
}
```

### Step 7: i18n Audit + New Keys

1. Add keys for leaderboard page (both AZ + EN)
2. Add keys for notifications page (both AZ + EN)
3. Audit ALL existing pages for any hardcoded strings missed
4. AZ strings: account for 20-30% longer text, special chars (ə ğ ı ö ü ş ç)

### Step 8: Code Review

Review all changes:
- No hardcoded colors (all via CSS vars / Tailwind tokens)
- No broken component logic (only CSS changed on existing pages)
- New pages have: i18n, loading/error/empty states, ARIA, isMounted guards
- No secrets, no `any`, no relative routing

### Step 9: Memory Update (Step 0.5 — MANDATORY)

Update:
1. `memory/context/sprint-state.md` → Session 12 COMPLETE
2. `memory/projects/volaura.md` → design system migration done
3. `docs/EXECUTION-PLAN.md` → mark items
4. `docs/DECISIONS.md` → retrospective

---

## STITCH PAGE PRIORITY (for Sessions 13+)

After Session 12, remaining Stitch pages should be built in this order:

| Priority | Page | Reason |
|----------|------|--------|
| P1 | Volunteer Event Details (rich) | Replaces current basic version |
| P1 | Event Creation Wizard (3 steps) | Org admin needs this to post events |
| P2 | Org Admin Dashboard | Core org experience |
| P2 | Talent Matching | Org value proposition |
| P2 | Quests | Gamification engagement |
| P3 | Rewards/Perks | Nice-to-have for MVP |
| P3 | Impact Reports | Nice-to-have |
| P3 | Messaging/Chat | Complex, defer post-MVP |
| P3 | Org Settings + 2FA | Post-launch |
| P3 | Organizations Discovery | Post-launch |

---

## CRITICAL RULES (abbreviated — full list in CLAUDE.md)

### NEVER
- Hand-write API types (use `pnpm generate:api` or INTERIM with TODO markers)
- Use 1px borders for layout separation (Stitch: "No-Line" rule)
- Use pure `#000000` for backgrounds (use `#13131b`)
- Use `any` in TypeScript
- Hardcode strings (use i18n `t()`)
- Touch component logic when migrating CSS

### ALWAYS
- Use Stitch design tokens (CSS variables)
- Use `surface-container-low/high` hierarchy for cards (no borders)
- Use glassmorphism for floating nav elements
- Use Plus Jakarta Sans for headlines, Inter for body
- Keep all existing Framer Motion animations
- Add i18n for all new strings (AZ primary)
- `isMounted` ref on async components
- Absolute `/${locale}/path` routing

---

## ENV FILES

Same as Session 11 (already configured). No changes needed.

---

## API ENDPOINT MAP

Same as Session 11. New endpoints for this session:

| Frontend needs | Method | Backend Path | Exists? |
|---------------|--------|-------------|---------|
| Leaderboard | GET | `/api/organizations/leaderboard` or similar | Check |
| Notifications | GET | `/api/notifications` | Probably not — use mock |
| Language preference | — | Cookie/localStorage | Client-side only |

---

## WHAT SUCCESS LOOKS LIKE

1. ✅ Stitch design tokens in Tailwind config + globals.css
2. ✅ ALL existing pages render in dark "Prestigious Path" theme
3. ✅ No visual inconsistency — every page uses same design system
4. ✅ Leaderboard page exists with animated podium + ranked list
5. ✅ Notification center exists with tabs + card types
6. ✅ Language switcher (AZ ↔ EN) works on all pages
7. ✅ All new i18n keys in both AZ + EN
8. ✅ No component logic broken during CSS migration
9. ✅ Memory files updated

---

## POST-SPRINT

Retrospective in `docs/DECISIONS.md`:
```
## Session 12 Retrospective
✓ What went as simulated:
✗ What DSP did not predict:
→ Feed into next simulation:
```

Model recommendation:
```
✅ Session 12 complete.
→ Next sprint (Session 13): claude-sonnet-4-6
   Reason: Event creation wizard (3-step form with validation) + org admin pages = medium-high complexity
   DSP model: sonnet
```

🧭 Proactive CTO:
```
1. [highest business-impact]
2. [highest technical-risk]
3. [thing Yusif hasn't thought about]
```
