# Architecture Decisions Log

## ADR-001: Monorepo with Turborepo
**Date:** 2026-03-21
**Decision:** Turborepo + pnpm workspaces
**Why:** Single repo for frontend + backend + migrations. Parallel dev servers. No code sharing between TS/Python (just API types via OpenAPI).
**Alternatives:** Separate repos (too much overhead for solo dev), Nx (heavier).

## ADR-002: Supabase Client — Per-Request via Depends()
**Date:** 2026-03-21
**Decision:** Use `acreate_client()` per request via FastAPI `Depends()`, NOT global client.
**Why:** RLS requires user-scoped JWT. Global client = all requests share same auth context = RLS bypass risk.
**Note:** `fastapi-supabase` package evaluated and rejected (abandoned, only 1 release mid-2025).
**Source:** Supabase team recommendation via @silentworks in GitHub Discussion #33811.

## ADR-003: No tRPC — OpenAPI + @hey-api/openapi-ts
**Date:** 2026-03-21
**Decision:** FastAPI generates OpenAPI spec → `@hey-api/openapi-ts` generates TypeScript types + TanStack Query hooks.
**Why:** FastAPI has built-in OpenAPI generation. tRPC requires tight coupling. hey-api provides equivalent type safety without framework lock-in.

## ADR-004: Gemini Primary, OpenAI Fallback
**Date:** 2026-03-21
**Decision:** Gemini 2.5 Flash (free tier) as primary LLM. OpenAI GPT-4o-mini as paid fallback.
**Why:** Free tier = $0 for MVP. 15 RPM limit is sufficient for assessment evaluations with caching.
**SDK:** `google-genai` (NOT `google-generativeai` — different package).

## ADR-005: pgvector 768 dimensions
**Date:** 2026-03-21
**Decision:** vector(768) using Gemini text-embedding-004.
**Why:** Matches Gemini embedding model output. NOT 1536 (OpenAI). All vector ops via Supabase RPC functions (PostgREST can't call pgvector operators directly).

## ADR-006: i18n — react-i18next with [locale] segment
**Date:** 2026-03-21
**Decision:** `react-i18next` + `next-i18n-router` with `[locale]` route segment.
**Why:** Official approach for App Router. AZ primary, EN secondary. No Russian in assessment content.
**Note:** `next-i18next` is deprecated for App Router — use `react-i18next` directly.
