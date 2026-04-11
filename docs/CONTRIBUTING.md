# CONTRIBUTING

## Branches

- `main` — production. Direct push requires CEO approval.
- `feature/*` — all work goes here, PR to main.
- Never force-push to main.

## PR Process

1. Branch from main: `git checkout -b feature/your-thing`
2. Write code, run tests
3. `pnpm typecheck && pnpm lint` — must pass
4. `cd apps/api && python -m pytest tests/ -x` — must pass
5. Push → open PR → wait for CI
6. Swarm audit runs automatically (`.github/workflows/ci.yml`)

## Commit Style

```
type(scope): short description

feat(assessment): add IRT adaptive question selection
fix(aura): correct badge tier boundary at score 75
chore(swarm): update agent feedback distilled
docs(runbook): add MindShift deploy steps
```

Types: `feat` `fix` `chore` `docs` `refactor` `test` `perf`

## Code Rules

**Backend (FastAPI):**
- Per-request Supabase client via `Depends()` — never global
- Pydantic v2 only (`ConfigDict`, `@field_validator` with `@classmethod`)
- `loguru` for logging — never `print()`
- Structured error responses: `{"code": "...", "message": "..."}`

**Frontend (Next.js):**
- App Router only — never Pages Router
- All routes: `/${locale}/path` — never relative
- No `any` TypeScript — strict mode enforced
- Server Components by default, `"use client"` only when needed

**Both:**
- UTF-8 encoding explicit everywhere
- i18n for all user-facing strings
- No hardcoded event names, dates, or feature-specific strings

## Testing

```bash
# Frontend unit tests
pnpm test

# Backend tests
cd apps/api && python -m pytest tests/ -v

# Production smoke test
python scripts/prod_smoke_test.py
```

## Never Do

- Use SQLAlchemy or any ORM
- Use global Supabase client
- Use `print()` for logging
- Use Pydantic v1 syntax
- Hardcode Supabase URLs (old ref: hvykysvdkalkbswmgfut — BLOCKED)
- Use Claude/Haiku as swarm agents (use Gemini/NVIDIA/Groq)

## After Merging

Swarm runs automatically via `swarm-daily.yml`. Manual trigger:
```bash
python -m packages.swarm.autonomous_run
```
P0 proposals → implement immediately. P1 → this sprint. P2 → backlog.
