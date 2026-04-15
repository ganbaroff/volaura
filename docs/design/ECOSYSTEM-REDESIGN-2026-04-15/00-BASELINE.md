# 00-BASELINE — Ecosystem Redesign 2026-04-15

**Purpose:** Snapshot of current state BEFORE any new design work. Read this to know what exists.
**Updated:** 2026-04-15 Session 111 (Atlas, Phase 0)

---

## Route inventory (apps/web/src/app — 47 pages, not 18)

**Auth (4):** login · signup · forgot-password · reset-password
**Entry (3):** `[locale]/page.tsx` (landing) · welcome · onboarding · callback
**Assessment (5):** list · [sessionId] · questions · complete · info/[slug]
**AURA (2):** aura · aura/contest (grievance)
**Ecosystem surfaces in web (4):** atlas · brandedby (+ generations/[id]) · life · mindshift
**Discovery (3):** discover · leaderboard · events (public list)
**Profile/settings (3):** profile · profile/edit · settings
**Public profiles (3):** u/[username] · u/[username]/verify/[sessionId] · verify/[token]
**Events (5):** create · [eventId] public · [eventId]/attendees · [eventId]/checkin · public list
**Org (3):** my-organization · my-organization/invite · org-volunteers
**Public orgs (2):** organizations (list) · organizations/[id]
**Subscription (2):** success · cancelled
**Admin (4):** admin · admin/grievances · admin/swarm · admin/users
**Other (3):** notifications · invite (public) · privacy-policy

Total: **47 pages**. Snapshot scope for Phase 0 = all 47 on desktop (1440) + mobile (390). ~94 screenshots.

## Tech stack (current)

- Next.js **14.2.35** App Router
- React 18.3.1
- Tailwind CSS **4.0.0** (CSS-first, no tailwind.config.js)
- Framer Motion **12.0.0**
- Lucide React 0.474.0 (icons)
- Recharts 2.15.0 (AURA radar)
- globals.css: **422 lines** (3-tier tokens already in place)

## Prior design work (DO NOT RESTART — BUILD ON IT)

| Doc | Date | Status | Useful content |
|-----|------|--------|----------------|
| `docs/design/DESIGN-SYSTEM-AUDIT.md` | 2026-03-22 | Baseline audit | Score 62/100, i18n 15%, a11y 48%, critical issues list |
| `docs/design/REDESIGN-MEGAPLAN.md` | ~2026-04 | Partial | Phase 1 tokens ✅ + Energy System ✅ DONE; product accent colors locked |
| `docs/design/PHASE-0-ECOSYSTEM-DESIGN-PLAN.md` | 2026-04-13 | Plan only | Prior Phase-0 attempt by Cowork — research + gate model |
| `docs/design/REDESIGN-BRIEF-v2.md` | — | Brief | Fixes from audit, not applied end-to-end |
| `docs/design/DESIGN-LIBRARIES-SHORTLIST-2026-04-13.md` | 2026-04-13 | Shortlist | Candidate libraries already evaluated |
| `docs/design/STITCH-DESIGN-SYSTEM.md` | — | Stitch output | Component prompts used earlier |
| `docs/research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14.md` | 2026-04-14 | Research | Perplexity pre-work on ecosystem patterns |
| `docs/research/ecosystem-design-research.md` | — | Research | Reference patterns |

**Locked facts from prior work (take as given, do not re-decide):**
- Product accent colors: VOLAURA `#7C5CFC` · MindShift `#3B82F6` · Life Sim `#F59E0B` · BrandedBy `#EC4899` · ZEUS `#10B981`
- Tokens are 3-tier: primitives → semantic → product (in globals.css)
- Energy System exists: `[data-energy]` attribute, `useEnergyMode()` hook, low-mode disables animations
- Foundation Laws (Constitution): never red, energy adaptation, shame-free, max 800ms animations, one primary CTA

## What's BROKEN / what CEO hates (from 2026-04-15 directive)

- Typography breaks on narrow widths — need variable fonts + `text-wrap: balance/pretty`
- Static, no scroll-driven life — need `animation-timeline: scroll()` + Framer useScroll fallback
- Products feel disconnected — need cross-ecosystem linkage (one user journey across 5 surfaces)
- No evidence chain — each element must prove it's the best choice (EV-NNN references)
- Quality bar: Apple taste + Toyota genchi genbutsu + 5 whys

## Gap list (what Phase 1 swarm must find)

Prior audit (2026-03-22) scored 62/100 on a smaller scope (18 pages). Current scope is 47 pages. Likely worse in:
- i18n coverage (audit said 15% — most pages still English-only?)
- a11y on new pages added since March (ecosystem surfaces, admin)
- Animation consistency on cross-product transitions (didn't exist in March)
- Variable font integration (not attempted)
- Scroll-driven elements (not attempted)

Swarm Phase 1 job = confirm/update these numbers with live audit on current 47 pages.

## Phase 0 checklist progress

- [x] P0.1 Re-read PLAN.md + STATE.md ✅
- [x] P0.2 Inventory all routes (47 found) ✅
- [ ] P0.3 Screenshot all 47 pages desktop + mobile (deferred — needs prod access + Playwright/Chrome, done in next wake batch)
- [x] P0.4 Read prior design docs — peeked ✅ (DESIGN-SYSTEM-AUDIT, MEGAPLAN, PHASE-0, BRIEF-v2, LIBRARIES-SHORTLIST)
- [ ] P0.5 Figma MCP `get_variable_defs` vs globals.css (deferred — Figma auth)
- [x] P0.6 Package.json deps checked (Next 14.2.35, Tailwind 4.0, Framer 12, Lucide, Recharts) ✅
- [x] P0.7 Create 00-BASELINE.md ✅ (this file)
- [ ] P0.8 Archive stale docs (deferred — must not delete until Phase 3 incorporates their content)
- [x] P0.9 Update STATE.md (next action)
- [ ] P0.10 Gate G1 self-review → proceed to Phase 1+2

## Decisions this step

**D-2026-04-15-01 — Don't archive prior design docs yet.**
Rationale: MEGAPLAN + PHASE-0-PLAN contain locked decisions (accent colors, tokens, Energy System) that must flow into Phase 3 spec. Archive only after Phase 3 references them. Revisit if Phase 3 complete.

**D-2026-04-15-02 — Scope is 47 pages, not 18.**
Rationale: Audit from March was smaller. Current prod has grown. Budget Phase 0 screenshots + Phase 1 swarm against real scope.

**D-2026-04-15-03 — Defer Playwright screenshots to next wake.**
Rationale: 94 screenshots (47×2) takes time + requires prod access + MCP browser setup. Better to do in a fresh batch than partial now. Phase 1 swarm can work on existing-doc analysis in parallel until screenshots land.

## Next action on next wake

1. Update STATE.md P0.2, P0.4, P0.6, P0.7 → ✅
2. P0.3 Screenshot batch via Chrome MCP or Playwright, save to `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/screenshots/YYYY-MM-DD/{desktop,mobile}/`
3. P0.5 Figma `get_variable_defs` if auth works
4. P0.10 Gate G1 — decide if Phase 1 swarm can start in parallel (yes, existing-doc analysis doesn't need screenshots)
