# Volaura Session Handoff

## Current State
**Date:** 2026-03-21
**Phase:** 0 — Project Scaffolding
**Status:** Monorepo initialized, deps not yet installed

## What's Done
- [x] Turborepo monorepo structure (pnpm)
- [x] apps/web/ — Next.js 14 App Router skeleton
- [x] apps/api/ — FastAPI skeleton with health endpoint
- [x] packages/ — ESLint + TypeScript shared configs
- [x] CLAUDE.md + .claude/rules/ (backend, frontend, database)
- [x] i18n setup (AZ + EN locales)
- [x] Supabase client pattern (per-request via Depends)
- [x] LLM service (Gemini primary + OpenAI fallback)
- [x] Zustand stores (auth, UI)

## What's Next
- [ ] Install all npm/pip dependencies
- [ ] Verify `pnpm dev` starts both apps
- [ ] Supabase local setup + migrations
- [ ] Assessment engine (IRT/CAT)
- [ ] Auth flow (Supabase Auth)

## Key Decisions
See `docs/DECISIONS.md` for full architecture decisions log.

## Environment Setup
1. `pnpm install` at root (installs all workspace deps)
2. `cd apps/api && pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in keys
4. `pnpm dev` starts both frontend (3000) and backend (8000)
