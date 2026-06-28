# AGENTS.md — apps/api

**Parent manifest:** [../../AGENTS.md](../../AGENTS.md)

## Scope

FastAPI async backend: routers, services, assessment IRT/CAT engine, AURA, compliance (grievance, export).

## May depend on

- Supabase SDK via `Depends(SupabaseAdmin|SupabaseUser)` from `app/deps.py`
- `packages/swarm/` only where explicitly documented

## May NOT depend on

- `apps/web/*`, frontend state, module-level Supabase clients

## Error handling

- `HTTPException` detail must be `{"code": "...", "message": "..."}` — never bare strings
- loguru only (no `print()`)

## Tests

- `pytest tests/` from `apps/api/` (CI job: Backend (FastAPI))
- Reconciler: `test_assessment_completion_reconciler.py` also in ecosystem-hard-gates
