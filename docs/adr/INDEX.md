# ADR Index — VOLAURA Architecture Decision Records

> **Canonical table:** [README.md](README.md) is the authoritative ADR index. This file is the Obsidian navigation view — keep in sync with README on every ADR change.

## Current ADRs (001–011, 016–017 on main)

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
- [[ADR-016-positioning-lock|ADR-016 — Positioning Lock]] — VOLAURA = verified professional talent platform; event/ops is the initial wedge, not the promise
- [[ADR-017-cv-grounded-item-generation|ADR-017 — CV-Grounded Item Generation]] — Two-layer engine: calibrated CAT core (AURA) + CV-grounded Experience Interview; continuous multi-agent AIG with human review gate (Proposed)

> **Lineage note:** ADR-012–015 exist on the `codex/swarm-queue-bridge` runtime lineage, not on `main`. The 011→016 gap on `main` is intentional until that lineage is reconciled.

## Pending / proposed

- ADR-017 (Proposed) — implementation PR-1..PR-4 gated behind the assessment content fixes (FIX-1..3, see `memory/atlas/ASSESSMENT-CONTENT-AUDIT-2026-06-10.md`); LLM-touching code requires Codex review.

New proposed ADRs should reserve the next collision-free number and be added to this index in the same PR.

## Cross-references

- [ECOSYSTEM-CONSTITUTION](../ECOSYSTEM-CONSTITUTION.md) — supreme law over all ADRs
- [ARCHITECTURE.md](../ARCHITECTURE.md) — system overview (§14 points here)
