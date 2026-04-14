# Epic E3 — Alive-Atlas First-Session UX

**Owner:** Cowork (design + copy) → Atlas (wire)
**Duration:** 4 days (2 Cowork design, 2 Atlas wire)
**Priority:** P0 for Vision Canon — this IS the product's first impression
**Source:** Vision Canon (SYNC §0), Constitution Foundation Laws 2+3 (Energy Adaptation + Shame-Free), PRE-LAUNCH-BLOCKERS-STATUS.md

## Goal
First 5 minutes of a new user's life on VOLAURA demonstrate "живой, адаптивный" Atlas — energy-adaptive greeting, shame-free onboarding, one primary CTA, not-red errors, Crystal Law payoff visible.

This is NOT a generic onboarding. This is the product's thesis, compressed into the first session.

## Tasks (Cowork)

1. **Write first-session script (3 energy modes)**
   - File: `docs/ux/first-session-script.md`
   - Variants: Full / Mid / Low energy
   - Full: ~8 min path, rich intro, crystal animation on completion
   - Mid: ~4 min path, essentials only, quiet tone
   - Low: ~2 min path, "save progress, come back", no guilt copy
   - Every microcopy line passes shame-free check (no "you haven't", no profile %)

2. **Energy picker spec**
   - File: `docs/ux/energy-picker-spec.md`
   - Where: shown after auth, before assessment
   - Copy in RU/EN/AZ
   - Default: Full; re-selectable from settings
   - Persistence: `user_preferences.energy_mode`

3. **Error-state copy**
   - File: `docs/ux/error-copy.md`
   - All error states use purple #D4B4FF or amber #E9C400 — never red
   - Copy tone: "что-то пошло не так у нас", never "you did wrong"

4. **Crystal Law first payoff moment**
   - When: end of first assessment
   - What: visible crystal earned, written explanation of where it travels (Life Simulator hint)
   - Copy: ties to ecosystem without confusing first-time user

5. **Handoff to Atlas**
   - Write `memory/atlas/inbox/2026-04-1X-handoff-E3-wire.md` with:
     - Exact files to touch in `apps/web/`
     - Component map (which shadcn primitives)
     - i18n keys with AZ/RU/EN strings

## Tasks (Atlas, after Cowork handoff)

6. **Wire energy picker** → `apps/web/app/[locale]/onboarding/energy/page.tsx`
7. **Wire first-session flow** — 3 branches from energy_mode
8. **Replace red error states** — grep `bg-red-` `text-red-` → swap for constitutional colors
9. **Add crystal payoff screen** after assessment submit

## Files Cowork creates
- `docs/ux/first-session-script.md`
- `docs/ux/energy-picker-spec.md`
- `docs/ux/error-copy.md`
- `memory/atlas/inbox/2026-04-1X-handoff-E3-wire.md`

## Files Atlas touches
- `apps/web/app/[locale]/onboarding/**`
- `apps/web/components/ui/**` (error states)
- `apps/web/messages/az.json`, `ru.json`, `en.json`
- `apps/api/app/routers/preferences.py` (energy_mode field)
- `supabase/migrations/YYYYMMDDHHMMSS_add_user_energy_mode.sql`

## Definition of Done
- [ ] New user can pick energy mode before assessment
- [ ] 3 flow variants render without layout break in AZ (longest locale)
- [ ] Zero red pixels in error states (manual audit: grep + screenshot)
- [ ] Crystal earned on completion visible, explains ecosystem in <20 words
- [ ] Cowork-written copy unchanged by Atlas wire (no silent edits)
- [ ] CEO approves tone in 1 review round (max)

## Dependencies
- E2 must complete before Atlas wires (need staging live to test)
- E1 not required but helps (Memory Gate catches regressions)

## CEO touch
1 request: "tone pass on first-session-script.md" — 15 min review.

## Artifacts required at end
- Decision log `memory/decisions/2026-04-1X-first-session-ux.md`
- Journal entries for each wire step
- Screenshot of completed path (Atlas can use Playwright MCP)
