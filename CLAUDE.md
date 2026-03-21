# Volaura — Elite Volunteer Talent Platform

## Project Overview
Volaura is a verified volunteer talent platform for Azerbaijan (CIS/MENA expansion later).
Launch target: WUF13 Baku, May 2026.

## Tech Stack

### Frontend (`apps/web/`)
- Next.js 14 App Router (ONLY — never Pages Router)
- TypeScript 5 strict mode (no `any`)
- Tailwind CSS 4 (CSS-first config, `@tailwindcss/postcss`)
- Zustand (global state — NOT Redux)
- TanStack Query (server state)
- React Hook Form + Zod (validation)
- Recharts (radar chart)
- react-i18next (AZ primary, EN secondary)
- shadcn/ui (base components)
- Framer Motion (animations)
- PWA via @ducanh2912/next-pwa

### Backend (`apps/api/`)
- Python 3.11+ with FastAPI (async)
- Supabase async SDK — `acreate_client` per-request via `Depends()`
- Pydantic v2 (ConfigDict, @field_validator — NEVER v1 syntax)
- google-genai SDK (Gemini 2.5 Flash primary LLM)
- OpenAI SDK (fallback only)
- adaptivetesting (IRT/CAT engine)
- python-telegram-bot
- loguru (logging — NEVER print())

### Database
- Supabase PostgreSQL + RLS
- pgvector with vector(768) — Gemini embeddings (NOT 1536/OpenAI)
- All vector ops via RPC functions only (never PostgREST directly)

### Hosting
- Vercel: frontend (free tier)
- Railway: backend (~$8/mo)
- Supabase: database (free tier → Pro if needed)

## Critical Rules

### NEVER DO
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

### ALWAYS DO
- UTF-8 encoding everywhere (explicit `encoding='utf-8'`)
- Per-request Supabase client via FastAPI Depends()
- Type hints on all Python functions
- Strict TypeScript (no `any`)
- i18n for all user-facing strings
- RLS policies on all tables
- Structured JSON error responses from API
- Cache LLM evaluations in session at submit_answer time

## Architecture
- Monorepo: Turborepo + pnpm
- Frontend: `apps/web/` (Next.js 14)
- Backend: `apps/api/` (FastAPI monolith — NOT microservices)
- Database: `supabase/` (migrations + seed)
- Shared: `packages/` (eslint-config, typescript-config)
- Docs: `docs/` (HANDOFF.md, DECISIONS.md)

## API Type Safety
FastAPI generates `/openapi.json` → `@hey-api/openapi-ts` generates:
- TypeScript types
- TanStack Query hooks
- Zod schemas
Run: `pnpm generate:api`

## AURA Score Weights (FINAL — DO NOT CHANGE)
- communication: 0.20
- reliability: 0.15
- english_proficiency: 0.15
- leadership: 0.15
- event_performance: 0.10
- tech_literacy: 0.10
- adaptability: 0.10
- empathy_safeguarding: 0.05

## Badge Tiers
- Platinum: >= 90
- Gold: >= 75
- Silver: >= 60
- Bronze: >= 40
- None: < 40

## File Naming
- TypeScript: kebab-case files, PascalCase components
- Python: snake_case everywhere
- SQL: snake_case tables and columns
- Import alias: `@/` for `apps/web/src/`
