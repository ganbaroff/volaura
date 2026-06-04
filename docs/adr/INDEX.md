# ADR Index — VOLAURA Architecture Decision Records

> One ADR per major architectural decision. Append-only — superseded ADRs stay with `Status: Superseded by ADR-NNN`. Read the most recent first if you need current state.

## Current ADRs

- [[ADR-001-system-architecture|ADR-001 — System Architecture]] — Monorepo Turborepo + pnpm, apps/web Next.js 14, apps/api FastAPI, Supabase Postgres + RLS, Vercel + Railway hosting
- [[ADR-002-database-schema|ADR-002 — Database Schema]] — Tables, RLS policies, character_events bus, atlas_obligations, atlas_debts patterns
- [[ADR-003-auth-verification|ADR-003 — Auth & Verification]] — Supabase Auth, Google OAuth flow, magic-link, Capacitor WebView nuances
- [[ADR-004-assessment-engine|ADR-004 — Assessment Engine]] — IRT 3PL, BARS, anti-gaming, AURA score calculation pipeline
- [[ADR-005-aura-scoring|ADR-005 — AURA Scoring]] — 8-competency weights, badge tiers (Bronze/Silver/Gold/Platinum), score decay (logic exists, scheduler pending)
- [[ADR-006-ecosystem-architecture|ADR-006 — Ecosystem Architecture]] — Five-product ecosystem integration, shared Supabase, FastAPI monolith, `character_events` bridge
- [[ADR-007-ai-gateway-model-router|ADR-007 — AI Gateway — Model Router]] — Role-based provider selection and Article 0 enforcement
- [[ADR-008-zeus-governance-layer|ADR-008 — ZEUS Governance Layer]] — Immutable governance events, policy introspection, hardened ZEUS audit layer
- [[ADR-009-crewai-adoption|ADR-009 — CrewAI Adoption]] — Proposed CrewAI adoption for Sprint Gate DSP and critical multi-agent workflows
- [[ADR-010-defect-autopsy|ADR-010 — Defect Autopsy]] — Top root causes from fix commits and enforced Definition of Done
- [[ADR-011-litellm-gateway-migration|ADR-011 — LiteLLM Gateway Migration]] — Proposed phased migration of Python swarm providers to LiteLLM Router
- [[ADR-016-positioning-lock|ADR-016 — Positioning Lock]] — VOLAURA = verified professional talent platform; event/ops is the initial wedge, not the promise; "volunteer" / "LinkedIn competitor" / "universal talent" framings banned

> **Lineage note:** ADR-012–015 exist on the `codex/swarm-queue-bridge` runtime lineage, not on `main`. The 011→016 gap on `main` is intentional until that lineage is reconciled.

## Pending / proposed

No pending ADR files are tracked on `main` at this time. New proposed ADRs should reserve the next collision-free number and be added to this index in the same PR.

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
