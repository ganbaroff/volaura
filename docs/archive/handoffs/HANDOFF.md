# Volaura Session Handoff

## Current State
**Date:** 2026-03-21
**Phase:** 2 — Backend Core (next)
**Last completed:** Phase 1 — Database Schema

## Phases Status
- [x] Phase 0: Project scaffolding (monorepo, Next.js 14, FastAPI, CLAUDE.md)
- [x] Phase 1: Database schema (13 tables, RPC functions, RLS, seed data)
- [ ] Phase 2: Backend Core (auth + profile endpoints, OpenAPI gen)
- [ ] Phase 3: Assessment Engine (IRT/CAT + BARS LLM evaluation)
- [ ] Phase 4: Frontend Core (auth pages, dashboard shell)
- [ ] Phase 5: AURA Card + Radar Chart + viral loop
- [ ] Phase 6: Reliability Engine
- [ ] Phase 7: Events + Registrations
- [ ] Phase 8: B2B Features
- [ ] Phase 9: Telegram Bot
- [ ] Phase 10: Polish + Deploy

## What's Done (Phase 1)
- 11 migration files in `supabase/migrations/`
- All 13 tables from spec (profiles, competencies, questions, assessment_sessions,
  aura_scores, badges, volunteer_badges, events, registrations, organizations,
  organization_ratings, volunteer_behavior_signals, volunteer_embeddings)
- pgvector(768) for Gemini embeddings
- 5 RPC functions: match_volunteers, calculate_aura_score, get_badge_tier,
  calculate_reliability_score, upsert_aura_score
- RLS on every table
- Seed: 8 competencies (exact weights), 5 real + 15 placeholder Communication questions
- config.toml for Supabase CLI

## What's Next (Phase 2)
Start with backend auth + profile endpoints:
1. `apps/api/app/routers/profiles.py` — GET/PUT /profiles/me
2. `apps/api/app/routers/auth.py` — POST /auth/callback
3. Pydantic models for Profile, User
4. Test profile CRUD with real Supabase connection

## Key Context
- Supabase CLI not installed (needs Docker) — push migrations via Supabase dashboard SQL editor
- Docker not installed on machine
- Python venv at `apps/api/.venv/`
- Both dev servers configured in `.claude/launch.json`

## Environment Setup
1. Create Supabase project at supabase.com → get URL + keys
2. Copy `.env.example` → `.env` and fill keys
3. In Supabase SQL editor: run migrations in order (000001 → 000012)
4. Run `supabase/seed.sql` to populate competencies + questions
5. `pnpm install` at root
6. Start servers via `.claude/launch.json`
