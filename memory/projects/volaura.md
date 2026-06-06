# VOLAURA — Project Context

**Updated:** 2026-06-06 (supersedes Session 50 volunteer-era snapshot)

## What it is

**Verified professional talent platform** for Azerbaijan (CIS/MENA expansion later).

Positioning lock: [ADR-016](../../docs/adr/ADR-016-positioning-lock.md) — prove skills via adaptive assessment, earn AURA, get found by organizations. NEVER "volunteer platform" or "LinkedIn competitor."

Event/operations workflows are an initial wedge, not the product promise.

## Execution priority

VOLAURA-first until launch-readiness. MindShift, Life Simulator, BrandedBy, ZEUS share Supabase auth + `character_events` but are not equally mature. BrandedBy and ZEUS are frozen (Path E).

## Launch gate (2026-06)

- **Legal (CEO):** Art. 9 energy/burnout consent interpretation, AZ PDPA SADPP filing — see [PRE-LAUNCH-BLOCKERS-STATUS.md](../../docs/PRE-LAUNCH-BLOCKERS-STATUS.md)
- **Engineering:** Control-plane truth — CI gates, doc canon, assessment/AURA durability — see [VOLAURA-FIRST Master Plan](../../docs/VOLAURA-FIRST-MASTER-EXECUTION-PLAN-2026-04-23.md)

## Technical snapshot (origin/main baseline)

- Monorepo: `apps/web`, `apps/api`, `apps/tg-mini`, `packages/swarm`, 119+ Supabase migrations
- North star metric: completed, contestable, verified AURA profiles per week

## Historical note

Pre-2026-04 content in this file described a "volunteer talent platform" and BrandedBy sprint — **superseded by ADR-016 and Path E freeze.** Do not use for status.
