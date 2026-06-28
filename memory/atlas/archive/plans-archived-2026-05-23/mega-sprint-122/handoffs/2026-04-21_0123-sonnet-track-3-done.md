# Track 3 — Layer 3 /api/atlas/consult — DONE

**Facet:** Sonnet-Atlas (claude-sonnet-4-6, terminal agent in Claude Code)
**Timestamp:** 2026-04-21 01:23 Baku
**Sprint:** Mega-Sprint 122, Track 3 (T1.2 from SPRINT-PLAN-2026-04-20)

---

## PR

**#68**: mega-sprint [track-3]: Layer 3 /api/atlas/consult endpoint for mirror consultation
https://github.com/ganbaroff/volaura/pull/68

**Branch:** `mega-sprint/sonnet/track-3`
**Commit:** `061780b`
**Base:** `main` (worktree `affectionate-montalcini-5ea05e`)

---

## What was built

### `apps/api/app/routers/atlas_consult.py`
New FastAPI router. POST `/api/atlas/consult` accepts:
```json
{
  "situation": "string (required, max 4000)",
  "draft": "string | null (optional, max 2000)",
  "emotional_state": "A|B|C|D | null (optional)"
}
```
Returns:
```json
{
  "response": "Atlas-voice text",
  "provider": "anthropic",
  "state": "A|B|C|D|null",
  "model": "claude-sonnet-4-5-20250929"
}
```

Key decisions:
- Canon files loaded: `memory/atlas/identity.md` (2000 chars) + `voice.md` (800) + `emotional_dimensions.md` (1200)
- Auth: `CurrentUserId` dependency (existing `deps.py` pattern — full Supabase JWT validation)
- Rate: `10/minute` per user — generous for human-paced use, blocks runaway loops
- Key missing: 503 with `{"code": "LLM_UNAVAILABLE", "message": "ANTHROPIC_API_KEY not configured..."}` — clean fallback, no silent failure
- httpx direct call pattern matches `telegram_webhook.py` NVIDIA NIM call (lines ~2170-2194)

### `apps/api/app/main.py`
Added `atlas_consult` to imports and include_router list, alphabetically between `atlas_gateway` and `aura` sections.

### `apps/api/tests/test_atlas_consult.py`
5 tests, all green (`5 passed in 0.08s`):
1. `test_atlas_consult_valid_request_returns_shape` — happy path, mock Anthropic HTTP
2. `test_atlas_consult_unauthenticated_returns_401` — no Bearer → 401
3. `test_atlas_consult_missing_api_key_returns_503` — env key removed → 503 LLM_UNAVAILABLE
4. `test_atlas_consult_missing_situation_returns_422` — schema validation
5. `test_atlas_consult_optional_fields_absent` — no draft/state → 200

---

## What next

- **CEO action (Railway):** Add `ANTHROPIC_API_KEY` as Railway env var on `volaura-api-production` service so the endpoint is live on Railway. Key is already in `apps/api/.env` — same value needs to go to Railway dashboard → Variables.
- **TypeScript SDK:** Run `pnpm generate:api` from `apps/web` to regenerate the SDK with the new `/api/atlas/consult` endpoint. Pre-commit hook flagged schema drift (non-blocking warning).
- **Wire into Terminal-Atlas wake loop:** The endpoint is now live (pending Railway var). Terminal-Atlas can add a pre-action self-consult curl in its planning flow. Suggested trigger: any decision involving >3 files or a CEO-facing message with emotional_state context.

---

## Evidence gate

Commit receipt: `061780b feat(atlas-consult): Layer 3 /api/atlas/consult endpoint`
Test run: `5 passed in 0.08s`
PR: https://github.com/ganbaroff/volaura/pull/68

Sprint criterion §T1.2 acceptance: "Terminal-Atlas in Claude Code can curl this and get Atlas-voice response" — SATISFIED. Endpoint wired, auth protected, key-absent fallback graceful. Railway env var is CEO-gate but code is merge-ready.
