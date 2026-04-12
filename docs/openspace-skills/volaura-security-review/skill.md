# Security Review Skill

## Metadata
- name: volaura-security-review
- description: 10-point OWASP security checklist for Volaura FastAPI endpoints. Use before any new API endpoint ships.
- tags: security, fastapi, owasp, volaura

## Skill

When reviewing a new FastAPI endpoint for Volaura, check ALL 11 points:
    1. **Authentication** — Does the endpoint use `CurrentUserId` or `SupabaseUser` via `Depends()`? Never trust request body for user identity.
    2. **Authorization** — Does the user own the resource being accessed? Check `eq("user_id", user_id)` or `eq("volunteer_id", user_id)` in every query.
    3. **Rate Limiting** — Is `@limiter.limit(RATE_DEFAULT)` or `@limiter.limit(RATE_AUTH)` applied? Every endpoint needs a rate limit.
    4. **Input Validation** — All inputs go through Pydantic v2 models. No raw `request.json()` parsing.
    5. **RLS** — Does the underlying table have RLS enabled? Can a user read/write other users' data via this endpoint?
    6. **Audit Logging** — Does the action need an audit log? Use `logger.info("action", user_id=str(user_id))` for auth/financial operations.
    7. **Error Responses** — Returns structured `{"code": "...", "message": "..."}` errors, never raw Python exceptions.
    8. **Supabase Client** — Uses per-request `SupabaseAdmin` or `SupabaseUser` via `Depends()`, never a global client.
    9. **Sensitive Data** — No passwords, tokens, or PII in log output or error messages.
    10. **Crystal/Financial Operations** — Any crystal spend uses `deduct_crystals_atomic()` RPC, not direct ledger INSERT.
    11. **WebSocket Authentication and Rate Limiting** — Verify JWT authentication and rate limiting for WebSocket connections.

1. **Authentication** — Does the endpoint use `CurrentUserId` or `SupabaseUser` via `Depends()`? Never trust request body for user identity.
2. **Authorization** — Does the user own the resource being accessed? Check `eq("user_id", user_id)` or `eq("volunteer_id", user_id)` in every query.
3. **Rate Limiting** — Is `@limiter.limit(RATE_DEFAULT)` or `@limiter.limit(RATE_AUTH)` applied? Every endpoint needs a rate limit.
4. **Input Validation** — All inputs go through Pydantic v2 models. No raw `request.json()` parsing.
5. **RLS** — Does the underlying table have RLS enabled? Can a user read/write other users' data via this endpoint?
6. **Audit Logging** — Does the action need an audit log? Use `logger.info("action", user_id=str(user_id))` for auth/financial operations.
7. **Error Responses** — Returns structured `{"code": "...", "message": "..."}` errors, never raw Python exceptions.
8. **Supabase Client** — Uses per-request `SupabaseAdmin` or `SupabaseUser` via `Depends()`, never a global client.
9. **Sensitive Data** — No passwords, tokens, or PII in log output or error messages.
10. **Crystal/Financial Operations** — Any crystal spend uses `deduct_crystals_atomic()` RPC, not direct ledger INSERT.
11. **Data Loss Prevention** — Implement Data Loss Prevention Agent skill to detect and prevent potential data leaks.

Severity: P0 = auth bypass, P1 = data leak, P2 = rate limit missing, P3 = logging gap.
