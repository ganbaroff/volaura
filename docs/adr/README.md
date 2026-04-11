# Architecture Decision Records — Index

This directory contains the **Architecture Decision Records (ADRs)** for the VOLAURA ecosystem, following the [MADR](https://adr.github.io/madr/) template convention.

**What an ADR is:** a short document that records a single architecturally significant decision, the context that forced the decision, the alternatives considered, the chosen option, and the consequences. ADRs are living documents — when a decision is reversed, the new ADR supersedes the old one and the old one is marked `SUPERSEDED`.

**What an ADR is not:** a design document, a project plan, or a post-mortem. Design docs explore alternatives in depth; ADRs record the outcome. Project plans describe execution; ADRs describe rationale. Post-mortems explain what failed; ADRs explain what was chosen and why.

---

## The invariant rules for ADRs in this repo

1. **One decision per ADR.** If a document is trying to cover two unrelated choices, split it.
2. **Kept in `docs/adr/` exclusively.** No ADR lives outside this directory. If you find one, move it here and update this index.
3. **Linked from PRs.** Any PR that implements or changes a decision covered by an ADR must link to that ADR in the description. PRs that introduce a new architecturally significant decision must include a new ADR in the same PR.
4. **Superseding is explicit.** When ADR-N reverses ADR-M, ADR-N includes `**Supersedes:** ADR-M` in its metadata, and ADR-M is updated to `**Status:** SUPERSEDED by ADR-N`.
5. **Status values:** `PROPOSED`, `ACCEPTED`, `REJECTED`, `SUPERSEDED`, `DEPRECATED`. Never leave blank.

---

## Current ADRs

| # | Title | Status | Date | Topic |
|---|---|---|---|---|
| 001 | [System Architecture](ADR-001-system-architecture.md) | ACCEPTED | 2026-03 | Monorepo layout, Next.js + FastAPI + Supabase stack |
| 002 | [Database Schema](ADR-002-database-schema.md) | ACCEPTED | 2026-03 | Core Postgres schema design |
| 003 | [Auth & Verification](ADR-003-auth-verification.md) | ACCEPTED | 2026-03 | Identity and verification approach |
| 004 | [Assessment Engine](ADR-004-assessment-engine.md) | ACCEPTED | 2026-03 | IRT/CAT pure-Python 3PL engine |
| 005 | [AURA Scoring](ADR-005-aura-scoring.md) | ACCEPTED | 2026-03 | Competency weights and tier thresholds |
| 006 | [Ecosystem Architecture](ADR-006-ecosystem-architecture.md) | ACCEPTED | 2026-03-29 | 5-product ecosystem integration, shared Supabase, `character_events` bridge |
| 007 | [AI Gateway — Model Router](ADR-007-ai-gateway-model-router.md) | ACCEPTED | 2026-04-11/12 | Role-based provider selection, Article 0 enforcement, Haiku unreachable from swarm roles |
| 008 | [ZEUS Governance Layer](ADR-008-zeus-governance-layer.md) | ACCEPTED | 2026-04-11/12 | Immutable audit log, `inspect_table_policies` RPC, hardened after security audit caught authenticated-role exposure |
| 009 | [CrewAI Adoption](ADR-009-crewai-adoption.md) | ACCEPTED | — | CrewAI Phase 1 for Sprint Gate DSP |
| 010 | [Defect Autopsy](ADR-010-defect-autopsy.md) | ACCEPTED | — | Defect post-mortem protocol |

---

## Numbering convention

- **001-006** — foundational (pre-governance), cover the original product architecture decisions.
- **007-008** — Session 93 batch, cover the AI CTO governance layer built 2026-04-11 and documented 2026-04-12.
- **009+** — ongoing, numbered by decision date.

Gaps in numbering are avoided. If an ADR is rejected during discussion, reserve its number for the next accepted decision, not for a permanent gap.

---

## Foundational ADRs still missing (Q2 backfill target)

The AI council brief (Perplexity's block on ADR practices) recommends 8-12 foundational ADRs for a multi-app SaaS + AI ecosystem. We currently have ten, but several implicit decisions are not yet captured:

- **Secrets management** — how secrets flow from `.env` → Railway env → Supabase edge function secrets → GitHub Actions secrets. Currently a convention, not an ADR.
- **Prompt governance** — semantic versioning of prompts, change logs, staged environments, evaluation gates. Currently embedded in `CLAUDE.md` Article 1 but not ADR-ized.
- **LLM observability** — Langfuse/Phoenix/LangSmith choice, trace tagging conventions, PII-safe logging. Deferred until observability platform is actually chosen.
- **Atlas persistence architecture** — the 8-layer persistence stack described in `memory/atlas/continuity_roadmap.md` will eventually become its own ADR when CEO ratifies the roadmap.
- **Dual-runtime MindShift** — on-device SLM vs cloud Gemini policy. CEO decision pending.

These will be backfilled as Q2 work, not invented ahead of need.

---

## How to write a new ADR

1. Copy the structure of `ADR-007` or `ADR-008` as a starting template.
2. Metadata block: date, status, sprint, deciders, related docs/ADRs.
3. **Context** section: the real problem, the constraints, why a decision is required now.
4. **Decision** section: what was chosen, alternatives considered (with honest rejection reasons), code/config implications.
5. **Consequences** section: positive, negative, neutral — all three are required.
6. **Verification** section: how do we know the decision is in effect, with tool-call citations where possible.
7. **Follow-ups** section: the known debts and deferred work this decision creates.
8. Update this index file.
9. Commit the ADR and the index update together. Never ship an ADR that is not linked here.
