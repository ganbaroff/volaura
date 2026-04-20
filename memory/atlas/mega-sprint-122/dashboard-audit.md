# Dashboard First-60-Seconds Audit
**Track 4 — Sonnet-Atlas, Session 122 — 2026-04-21**
**File audited:** `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` (600 LOC) + all imported dashboard components

---

## Foundation Laws — Pass / Fail per Law

### Law 1 — No red
**PASS.**

Evidence:
- `--color-destructive` maps to `--color-error-container: #3d1a6e` (purple). Confirmed in `globals.css:114`.
- `text-destructive` in TrialBanner expired state = purple text, not red.
- `bg-destructive/10 border-destructive/20 text-destructive` in TrialBanner = purple-on-dark.
- `border border-error/30 bg-error-container` in ErrorCard = `--color-error: #d4b4ff` (spec-correct purple).
- Zero `text-red`, `bg-red`, `border-red`, `rgb(255,` anywhere in page or component files.
- TribeCard opt-out confirmation: `border-destructive/30 bg-destructive/5` = still purple.

All semantic destructive/error tokens resolve to purple. Law 1 is clean.

### Law 2 — Energy modes Full/Mid/Low
**PASS with architectural gap (non-blocking).**

Evidence:
- `useEnergyMode()` is imported and used on line 26–84.
- `isLowEnergy` gates: TribeCard (`!isLowEnergy`), FeedCards (`!isReducedEnergy` for mid+low).
- `isReducedEnergy` gates: Personalized feed hidden in mid AND low — correct per Constitution comment on line 333.
- CSS energy system is fully wired: `[data-energy="full/mid/low"]` blocks in globals.css with `--energy-animation` multipliers.
- Motion variants: `prefersReducedMotion` check fires per component via `useReducedMotion()`. Low energy mode zeroes all animation-duration/transition-duration via CSS (`[data-energy="low"] * { animation-duration: 0.01ms !important }`).

Gap: Framer Motion JS durations (e.g., `duration: 0.35` in `sectionVariants`) are not CSS-variable-driven, so they don't respond to `--energy-animation: 0.5` in mid mode at the JS level. They ARE zeroed by the CSS override in low mode, but mid mode only affects CSS transitions, not Framer JS. This is a pre-existing architectural gap, not a new violation, and mid mode in practice degrades animation via CSS fallback.

Recommendation (future work): create a `useAnimationDuration(base)` hook that returns `base * energyMultiplier` from `--energy-animation` and thread it into all Framer variants.

### Law 3 — Shame-free language
**PASS.**

Evidence:
- No `%` profile completion anywhere in page or components.
- StatsRow at `streak = 0`: renders `"not yet"` via `t("stats.notYet")` — never "0 days".
- StatsRow at `eventsCount = 0`: same `"not yet"` fallback — never "0 events".
- No "keep alive", "you missed", "days behind", "falling behind" in any string.
- TribeCard `kudos_count = 0`: shows `"Be the first to send kudos"` — never "0 kudos" (Q1 encoded in comments).
- AuraScoreWidget score < 40 / badge_tier = "none": shows `"Assessing"` label — not a deficiency label.
- NewUserWelcomeCard: "Prove your skills. Earn your AURA." — aspirational, not deficit-framing.
- Crystal fading: `"Your crystal glow is fading"` in amber-500 — gentle nudge, not shame. Arguable but within Law 3 bounds.

### Law 4 — Animations ≤800ms
**PASS with one boundary note.**

Evidence:
- `sectionVariants` duration: 0.35s (350ms). Well under limit.
- `stagger` in StatsRow item: 0.3s (300ms). Clean.
- AuraScoreWidget progress bar: `duration: 0.8` = **800ms exactly**. Boundary — valid per "≤800ms" spec.
- TribeCard crystal opacity: `transition-opacity duration-700` = 700ms CSS. Below 800ms limit.
- `prefersReducedMotion`: overrides all Framer animations to zero delay/duration via `sectionVariantsReduced`.
- `globals.css:403`: `@media (prefers-reduced-motion: reduce)` zeroes all transitions at CSS level.
- `globals.css:421`: `[data-energy="low"]` zeroes all transitions.

No violations. The 800ms progress bar is the closest approach to the limit — if the spec ever tightens, that's the first target.

### Law 5 — One primary CTA per screen
**CONDITIONAL VIOLATION — returning users with unread share prompt.**

Evidence:

**New user (no AURA score):** PASS. `NewUserWelcomeCard` renders with exactly one `bg-primary` CTA button (line 526: "Start my first assessment"). `QuickActions` section is gated behind `hasScore` (line 368) so it doesn't render. Share prompt is gated behind `showSharePrompt = hasScore && ...` so it also doesn't render. Single primary CTA. Clean.

**Returning user with score + unread share prompt:** VIOLATION. Two visually-primary elements simultaneously visible:
1. `SharePrompt` banner: `bg-primary text-primary-foreground` button ("Share" — line 245) — a full `bg-primary` styled button.
2. `QuickActionPrimary` link: `border-2 border-primary/40 bg-primary/5` elevated card (line 446) — visually dominant, signals primary action.

These can coexist on the same screen. The share prompt is above the fold; QuickActions is below. But on a mobile viewport (typical VOLAURA user) both can be visible at once. Two calls to action compete.

Note: the code intentionally prevents banner + share prompt from coexisting (`showSharePrompt` is false when trial/expired banner is active — line 204). But share prompt + QuickActionPrimary is NOT mutually exclusive.

**Severity:** Medium. Affects returning users who have a score and haven't dismissed the share prompt. New users (the first-60-seconds target audience) are unaffected. Still a Law 5 violation once the product has real returning users.

---

## First-60-Seconds Walkthrough

A new user lands here after completing OAuth login for the first time. They arrive at the dashboard before any assessment.

The first thing they see is the TopBar with "Dashboard" label, then their display name in a time-aware greeting ("Good morning, Yusif!") with a wave emoji. Immediate personalisation — their name appears in under a second. This is the right opening note.

Below the greeting is `NewUserWelcomeCard`. It dominates the viewport: a two-tone gradient card with a target emoji (🎯), the headline "Prove your skills. Earn your AURA.", a one-sentence sub ("Companies search by AURA score — not résumés."), a three-step journey list where step 1 is highlighted in primary color ("you are here"), and a single full-width `bg-primary` button "Start my first assessment →". Nothing else competes for attention — StatsRow, CrystalBalance, TribeCard, FeedCards, QuickActions are all behind `hasScore` gates so they don't render.

The ONE action is unambiguous: tap the CTA, go to `/assessment`. The path from login to first competency is a two-tap sequence (login → dashboard → assessment). Clean.

What the new user does NOT see: no score headline (score-as-identity violates Law 3), no profile completion %, no "welcome to our platform" marketing copy, no red anywhere, no competing CTAs.

The assessment CTA is not just signposted — it IS the page for a new user. The card takes ~70% of the visible viewport before the TribeCard renders. The TribeCard renders for all energy modes (only gated behind `!isLowEnergy`), which means a new user in mid or full energy sees the tribe section below the welcome card. The TribeCard for a non-tribe member shows a join CTA ("Find my tribe") — this is a secondary CTA below the fold, acceptable.

One concern worth naming: for organization accounts (`accountType === "organization"`), the primary CTA goes to `/org-talent` and shows different copy ("Verified talent is waiting." / "Explore verified talent →"). The code path is correct. But `/org-talent` — does that page exist and handle new orgs gracefully? That's outside this audit's scope (Track 4 is dashboard-only) but flagged for Track 2 follow-up.

No anxiety-inducing content. No red. No time pressure. No deficiency framing. The opening 60 seconds is calm, clear, directional.

---

## Single Leveraged Fix

**Law 5 violation in share prompt + QuickActionPrimary coexistence.**

The fix is small: downgrade the SharePrompt's share button from `bg-primary` to a secondary/ghost style. The share prompt already has prominent visual context (🎉 emoji, title, description) — it does not need a filled primary button to read as actionable. Making it `bg-secondary` or `variant="outline"` with `border-primary/50 text-primary` creates clear visual hierarchy: QuickActionPrimary is the primary action, share prompt is a contextual suggestion.

This is ≤10 LOC and unconditional — it makes the hierarchy correct for all users without touching any logic.

---

## Ranked Violations

| # | Law | Severity | Location | Evidence |
|---|-----|----------|----------|---------|
| 1 | Law 5 | Medium | page.tsx:244–246 (SharePrompt button) | `bg-primary text-primary-foreground` on share button competes with QuickActionPrimary when both render simultaneously for returning users with score |
| 2 | Law 2 | Low (architectural) | sectionVariants duration:0.35 + Framer variants | Mid energy mode reduces CSS transitions but not Framer JS durations; gap is pre-existing not new |
| 3 | Law 4 | Boundary | aura-score-widget.tsx:90 | Progress bar `duration: 0.8` = 800ms exactly; valid but worth noting if spec tightens |

No Law 1, Law 3 violations found.

---

## Energy Mode Extension (future work)

The CSS energy system is more mature than the JS animation layer. When Law 2 compliance is extended:

1. Create `apps/web/src/hooks/use-animation-config.ts` — reads `--energy-animation` from computed style, returns multiplier (1.0 / 0.5 / 0.0).
2. Thread into a shared `useDashboardMotion()` hook that returns pre-computed variant sets for each energy level.
3. Replace all inline `sectionVariants` / `stagger` / `item` const objects with hook returns.

This is ~1h of work and makes mid-energy mode behaviorally consistent between CSS and Framer.

---

*Audit by Sonnet-Atlas, mega-sprint-122, Track 4. Evidence-gated: all findings backed by grep output or direct file reads.*
