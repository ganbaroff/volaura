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

## Reactivation criteria (CEO-only)

Before reactivation, one or more of these must be true and explicitly acknowledged by CEO:
1. MindShift shipped to Play Store with ≥1000 MAU and stable <2% crash-free rate
2. VOLAURA has ≥100 paying organizations AND an identifiable BrandedBy-specific demand signal from those orgs
3. A strategic partnership surfaces that makes BrandedBy a required deliverable on a funded timeline
4. CEO explicitly reassesses the two-active + one-read-only + two-dormant shape and lifts BrandedBy dormancy

"One of our products failed and we need BrandedBy as fallback" is NOT a valid reactivation reason — that would indicate ecosystem pivot, which is a separate CEO decision.

## Sign-off

Filed by: Cowork-Atlas (orchestrator) 2026-04-19
Parallel notice: see `2026-04-19-zeus-frozen.md` in same directory.
