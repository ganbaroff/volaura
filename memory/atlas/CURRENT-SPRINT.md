# Current Sprint — VOLAURA Truth Lock + Gate Honesty

**Started:** 2026-06-06 Baku  
**Window:** 2026-06-06 → 2026-06-13 (7 days)  
**Owner:** Atlas (engineering), CEO (legal gate in parallel)

## Outcome

Control-plane truth matches runtime: portable daemon CI proof, ADR-013 LLM canon synced, sprint/docs pointers honest, branch reconciled toward `main`.

## North star (this sprint)

Completed, contestable, verified AURA profiles per week — unblocked by **honest gates**, not new features.

## Checkpoints

1. [x] Portable repo-root daemon tests (`tests/_paths.py`, no `C:/` hardcodes)
2. [x] CI job `Control Plane (daemon + litellm)` in `.github/workflows/ci.yml`
3. [x] Cerebras removed from `model_router.py`; CLAUDE.md + AGENTS.md aligned with ADR-013
4. [x] PRE-LAUNCH CEO legal gate section + contradiction fixes
5. [x] Per-workspace AGENTS.md stubs (`apps/web`, `apps/api`, `apps/tg-mini`, `packages/swarm`)
6. [ ] Reconcile `codex/swarm-queue-bridge` with `origin/main` (merge/rebase)
7. [ ] Promote `Control Plane` + `hard-gates` to required branch checks (when green)

## Do NOT touch during sprint

Open Badges VC, MIRT upgrade, BrandedBy/ZEUS revival, MindShift production track (12×14-day), meta-repo extraction, new daemon features beyond CI portability.

## CEO parallel (launch-blocking)

Art. 9 legal memo (#4) + AZ PDPA SADPP filing (#5) — see [PRE-LAUNCH-BLOCKERS-STATUS.md](../../docs/PRE-LAUNCH-BLOCKERS-STATUS.md).

## Previous sprint (archived)

MindShift Play internal-test — **CLOSED 2026-05-28** (CEO confirmed publish). Not repeated here; see git history / `memory/atlas/codex-loop.md`.

## Read order on wake

1. This file  
2. [docs/VOLAURA-FIRST-MASTER-EXECUTION-PLAN-2026-04-23.md](../../docs/VOLAURA-FIRST-MASTER-EXECUTION-PLAN-2026-04-23.md)  
3. [docs/PRE-LAUNCH-BLOCKERS-STATUS.md](../../docs/PRE-LAUNCH-BLOCKERS-STATUS.md)  
4. [memory/atlas/codex-loop.md](codex-loop.md)
