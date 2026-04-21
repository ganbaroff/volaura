# ARCHIVE NOTICE — BrandedBy frozen

**Date frozen:** 2026-04-19
**Authority:** CEO directive (Yusif Ganbarov) via Cowork-Atlas orchestration, Session 121 post-compaction.
**Status:** Dormant — no development, no maintenance, no agent allocation.
**Reactivation:** Requires explicit CEO signoff. No agent may touch BrandedBy code or specs without that signoff.

## What BrandedBy was

"AI professional identity builder" — planned product in VOLAURA ecosystem. Intended scope (pre-freeze):
- AI-generated professional twin (LinkedIn-style profile synthesis from user's AURA score + event history)
- Video-generation pipeline for candidate self-presentation
- Cross-posting to professional networks

## Why frozen

Ecosystem isolation directive 2026-04-19 — only MindShift and VOLAURA get active development capacity until MindShift ships to Play Store and VOLAURA positioning (volunteer→talent rename, Article 9 GDPR, AI-event-generation, assessment flow stabilization) lands. BrandedBy's video-gen block on API keys (Task #54 in TaskList) makes it a capital-drain without near-term ROI signal.

Five-product simultaneous development across solo-founder capacity (28-day-old ecosystem as of this writing) = scattering pattern that CEO and Cowork-Atlas agreed to close. Two active + one read-only + two dormant shape is the agreed response.

## State at freeze

- Video-gen pipeline: blocked on keys (RunwayML / Pika / similar), not started
- Profile synthesis: specs exist in memory, no code
- Integration with VOLAURA character_events: not designed
- Supabase schema: none specific to BrandedBy

No in-flight code to preserve. Freeze is clean.

## What does NOT happen while frozen

- No `feat/brandedby-*` branches opened
- No migrations added referencing BrandedBy tables
- No agent allocation (swarm modes, handoffs, dev cycles)
- No inclusion in launch communications
- No Play Store / App Store presence
- No marketing pages referencing BrandedBy as "coming soon" or "planned"

## What DOES stay

- Existing references in `CLAUDE.md` and ecosystem diagrams stay as historical record with status changed to "Dormant" — not deleted
- Any existing archive docs in `docs/archive/` stay
- This notice stays — if BrandedBy reactivates later, this file documents freeze conditions for comparison

## Path E — "Ship the Bridge" (Cowork-Atlas recommendation, confirmed 2026-04-21)

Cowork-Atlas (multi-model orchestration, Session 121+122) produced a structural recommendation called Path E: concentrate all active-development capacity on exactly two products — MindShift (ship to Play Store) and VOLAURA core (assessment + AURA + LifeSim active) — and formally archive BrandedBy and ZEUS rather than leave them as ambiguous "coming soon" stubs. The reasoning: a solo-founder 28-day-old ecosystem cannot sustain five parallel active tracks without scattering. Two active products shipped and validated beat five products half-started and unvalidated. Path E is not a retreat — it is a deliberate concentration that removes the organisational noise of tracking five products with incomplete feature sets.

BrandedBy dormancy is the direct output of Path E. The archive notice formalises what the ecosystem-shape already implied.

## What is preserved in frozen state

**Code stays in git.** `apps/web/src/app/[locale]/(dashboard)/brandedby/page.tsx` exists and returns `notFound()` behind `NEXT_PUBLIC_ENABLE_BRANDEDBY`. The feature-flag gate is the correct mechanism — no code deletion, no branch deletion, no route removal. The route simply 404s in production until the flag is set.

**Docs stay.** Every BrandedBy mention in `CLAUDE.md`, `docs/ECOSYSTEM-CONSTITUTION.md`, `docs/MODULES.md`, and ecosystem diagrams stays as historical record — status changed to "Dormant" inline, not deleted. `docs/archive/` artefacts (if any) stay. This notice stays permanently as a decision artifact — if BrandedBy ever reactivates, the freeze conditions are documented for comparison.

**Memory stays.** `memory/atlas/` references to BrandedBy (research, `brandedby_context.md`, `brandedby_video_research.md` in auto-memory) are read-only historical record. No deletion.

## Reactivation criteria (CEO-only)

Before reactivation, one or more of these must be true and explicitly acknowledged by CEO:

1. **Celebrity demand signal.** A confirmed celebrity or talent manager asks for AI-Twin video capability — a specific ask from an identified person, not a hypothetical market opportunity. BrandedBy's core differentiator (talking-head video from AURA score) is a niche that only becomes high-ROI when a real talent-management pipeline is attached. One real celebrity inquiry = the signal.
2. MindShift shipped to Play Store with ≥1000 MAU and stable <2% crash-free rate, AND VOLAURA has ≥100 paying organizations with identifiable BrandedBy-specific demand from those orgs.
3. A strategic partnership surfaces that makes BrandedBy a required deliverable on a funded timeline.
4. CEO explicitly reassesses the two-active + one-read-only + two-dormant shape and lifts BrandedBy dormancy.

"One of our products failed and we need BrandedBy as fallback" is NOT a valid reactivation reason — that would indicate ecosystem pivot, which is a separate CEO decision.

## Specific files / dirs affected by this archival notice

| Path | Status |
|------|--------|
| `apps/web/src/app/[locale]/(dashboard)/brandedby/page.tsx` | Frozen — 404 in prod via feature flag |
| `NEXT_PUBLIC_ENABLE_BRANDEDBY` env var | Stays `false` / unset — do not flip |
| `docs/archive/` (any BrandedBy specs) | Read-only historical record |
| `memory/atlas/archive-notices/2026-04-19-brandedby-frozen.md` (this file) | Living decision artifact — update if criteria change |
| CLAUDE.md BrandedBy references | Status = "Dormant" — not removed |

## Sign-off

Filed by: Cowork-Atlas (orchestrator) 2026-04-19
Expanded by: Atlas (Session 123) 2026-04-21 per CEO task — Path E formalisation.
Parallel notice: see `2026-04-19-zeus-frozen.md` in same directory.
