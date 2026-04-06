# Critical Rules

## NEVER DO
- Use SQLAlchemy or any ORM — Supabase SDK only
- Use Celery/Redis — use Supabase Edge Functions or pg_cron
- Use tRPC — use OpenAPI + @hey-api/openapi-ts
- Use global Supabase client — ALWAYS per-request via Depends()
- Use Pydantic v1 syntax (`class Config`, `orm_mode`)
- Use `google-generativeai` — use `google-genai`
- Use print() for logging — use loguru
- Hardcode strings — use i18n t() function
- Use Redux — use Zustand
- Use Pages Router — use App Router only
- Use relative routing (`/dashboard`) — always `/${locale}/dashboard`
- Use `getattr(settings, "field", default)` — use `settings.field` directly
- Hand-write API types/hooks that `pnpm generate:api` can generate (unless backend unreachable)
- Ignore API response envelope — always unwrap `.data` from `{ data, meta }` responses
- Use Haiku as subagent — CEO BANNED. Use free external models (Gemini Flash, Llama 3.3 NVIDIA, DeepSeek R1)
- Use Claude to review Claude's own output — self-confirmation bias (CLASS 11). Use DIFFERENT provider models.
- Change integration config before reading existing state — READ both sides FIRST
- Debug >5 min without asking "Did I create this?" — replace before repair (CLASS 12)
- Expand scope without CEO permission — ask "Does this help one real user complete the path?" first
- Count "done" by typecheck/test pass — only user reality counts (CLASS 7)
- Build new protocols/governance/meta-layers — process theater (CLASS 10)

## ALWAYS DO
- UTF-8 encoding everywhere (explicit `encoding='utf-8'`)
- Per-request Supabase client via FastAPI Depends()
- Type hints on all Python functions
- Strict TypeScript (no `any`)
- i18n for all user-facing strings
- RLS policies on all tables
- Structured JSON error responses from API
- Cache LLM evaluations in session at submit_answer time
- `isMounted` ref pattern on any component with async state updates
- Absolute routing: `/${locale}/path` (never relative)
- Unwrap API response envelope: response.data (not raw response)
- i18n AZ strings: 20-30% longer text, special chars (ə ğ ı ö ü ş ç), date DD.MM.YYYY, number 1.234,56
- READ docs/config BEFORE implementing
- Use DIVERSE external models for agent work
- Delegate to agents for ANY non-trivial task
- Track ALL CEO directives as explicit task list — never silently drop
- Ask "Does this help one real user?" before any new work
