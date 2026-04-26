# ADR Index — VOLAURA Architecture Decision Records

> One ADR per major architectural decision. Append-only — superseded ADRs stay with `Status: Superseded by ADR-NNN`. Read the most recent first if you need current state.

## Current ADRs

- [[ADR-001-system-architecture|ADR-001 — System Architecture]] — Monorepo Turborepo + pnpm, apps/web Next.js 14, apps/api FastAPI, Supabase Postgres + RLS, Vercel + Railway hosting
- [[ADR-002-database-schema|ADR-002 — Database Schema]] — Tables, RLS policies, character_events bus, atlas_obligations, atlas_debts patterns
- [[ADR-003-auth-verification|ADR-003 — Auth & Verification]] — Supabase Auth, Google OAuth flow, magic-link, Capacitor WebView nuances
- [[ADR-004-assessment-engine|ADR-004 — Assessment Engine]] — IRT 3PL, BARS, anti-gaming, AURA score calculation pipeline
- [[ADR-005-aura-scoring|ADR-005 — AURA Scoring]] — 8-competency weights, badge tiers (Bronze/Silver/Gold/Platinum), score decay (logic exists, scheduler pending)

## Pending / proposed

- ADR-006 — Cross-instance memory sync between Code-Atlas (VOLAURA monorepo `memory/atlas/`) and Atlas-CLI (`OneDrive/Documents/GitHub/ANUS/`). Mastra wraps runtime memory; Karpathy Wiki-pattern compiles raw → concepts. CEO's parallel track. Decision pending phase 1+ of [[../../C:/Users/user/OneDrive/Documents/GitHub/ANUS/ARCHITECTURE-DECISION|atlas-cli ADR]].
- ADR-007 — Direct APK Sideload pipeline for MindShift (CEO directive 2026-04-26 — Google Play Console blocked). Implementation already shipped in MindShift repo `fix/gitignore-keystore-security` branch commit `3bbf6e5`. ADR write-up pending.
- ADR-008 — Swarm save-path + learning-loop fix (Class 26 ground-truth: empty perspective JSONs, all-zero weights). Terminal-Atlas swarm-development handoff is the implementation track. ADR write-up after phase 4 lands.

## Cross-references

- [[../ECOSYSTEM-CONSTITUTION|Constitution v1.7]] — Supreme law over all ADRs. Conflicts resolved in favor of Constitution.
- [[../INDEX|Knowledge Base Root]] — full vault navigation
- [[../../memory/atlas/lessons|Atlas Lessons]] — Class 14, 19, 21, 22, 24, 26 each map to one or more architectural decisions
- [[../../memory/atlas/atlas-debts-to-ceo|Atlas Debts ledger]] — DEBT-001 (Stripe Atlas auto-filing not surfaced), DEBT-002 (parallel-shipment miss), DEBT-003 (narrative-fabrication)

## ADR template

When proposing a new ADR, use this skeleton:

```
# ADR-NNN — <one-line title>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by ADR-NNN | Rejected
**Decision by:** <Atlas-instance | CEO | swarm consensus>

## Context
What problem requires architectural choice?

## Decision
The choice made.

## Consequences
- Positive
- Negative
- Mitigation

## Alternatives considered
- Option A — rejected because ...
- Option B — rejected because ...

## Sources
- Research / docs / repos consulted
```

Save as `ADR-NNN-<slug>.md` in this directory. Add backlink to this INDEX.md `## Current ADRs` section. If superseding an older ADR, edit the older one's `Status:` field to `Superseded by ADR-NNN`.
