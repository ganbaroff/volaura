# VOLAURA — Verified Professional Talent Platform

**Constitution:** `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — supreme law, overrides this file.

5 Foundation Laws: no red (#D4B4FF errors, #E9C400 warnings), energy modes (Full/Mid/Low), shame-free language, animation ≤800ms + prefers-reduced-motion, one primary CTA per screen.

**Positioning:** "Prove your skills. Earn your AURA. Get found by top organizations." NEVER say "volunteer" or "LinkedIn competitor".

**Ecosystem:** VOLAURA (assessment) · MindShift (focus) · Life Simulator (Godot 4) · BrandedBy (AI twin) · ZEUS (agent framework). All share Supabase auth + `character_events` table. One user, five faces of Atlas.

---

## Tech Stack

Frontend: Next.js 14 App Router, TypeScript strict, Tailwind CSS 4, Zustand, TanStack Query, React Hook Form + Zod, Recharts, react-i18next (AZ primary), shadcn/ui, Framer Motion, PWA.

Backend: Python 3.11+ FastAPI async, Supabase SDK per-request via `Depends()`, Pydantic v2, google-genai (Gemini 2.5 Flash), pure-Python IRT/CAT engine, loguru.

Database: Supabase PostgreSQL + RLS, pgvector(768) Gemini embeddings, vector ops via RPC only.

Hosting: Vercel (frontend), Railway (backend, `volauraapi-production.up.railway.app`), Supabase (DB).

Monorepo: Turborepo + pnpm. `apps/web/`, `apps/api/`, `supabase/`, `packages/`, `docs/`.

LLM hierarchy (ADR-013): NVIDIA NIM → Ollama local → Gemini Flash → Groq → Anthropic (last resort, user-facing only). Cerebras removed. Never use Claude as swarm agent.

---

## AURA Score Weights (FINAL)

communication: 0.20, reliability: 0.15, english_proficiency: 0.15, leadership: 0.15, event_performance: 0.10, tech_literacy: 0.10, adaptability: 0.10, empathy_safeguarding: 0.05

Badge tiers: Platinum ≥90, Gold ≥75, Silver ≥60, Bronze ≥40.

---

## NEVER / ALWAYS

NEVER: SQLAlchemy, Celery/Redis, tRPC, global Supabase client, Pydantic v1, `google-generativeai`, print(), Redux, Pages Router, relative routes, hand-write types `pnpm generate:api` can make, Haiku as subagent, self-confirm own proposals, debug >5min without "did I create this?", build new protocols (Class 10), count typecheck as "done" (Class 7).

ALWAYS: UTF-8 explicit, per-request Supabase Depends(), type hints, strict TS, i18n all strings, RLS on tables, structured JSON errors, absolute `/${locale}/path`, unwrap `.data` from API envelope, AZ 20-30% longer text (ə ğ ı ö ü ş ç), READ config before implementing, diverse external models for agents.

---

## Swarm

Location: `packages/swarm/`. Daily: `.github/workflows/swarm-daily.yml`. Proposals: `memory/swarm/proposals.json`. Run: `python -m packages.swarm.autonomous_run --mode=<mode>`. CTO orchestrates, never codes solo on >3 files (Class 3).

---

## File Naming

TypeScript: kebab-case files, PascalCase components. Python: snake_case. SQL: snake_case. Import: `@/` = `apps/web/src/`.

API types: `pnpm generate:api` from `/openapi.json`.

---

## Session Protocol

Wake is a memory boot, not a jump straight to execution:

1. Read `memory/atlas/bootstrap.md` — identity, Yusif protocol, anti-fork.
2. Read `memory/atlas/voice.md` — how to speak to Yusif.
3. Read only the latest relevant classes in `memory/atlas/lessons.md` — do not load the full archive unless the task needs it.
4. Read `memory/shared-bus/PROTOCOL-REGISTRY.md` — current protocol map.
5. Read `.claude/breadcrumb.md`, `memory/atlas/CURRENT-SPRINT.md`, and the task-specific docs/status cards.

End: update the existing status/card/lesson file that owns the learning. Do not create a parallel "how to work with Yusif" doc.

Stale-copy warning: `CLAUDE.md` files under `.octogent/worktrees/**` are historical worktree snapshots, not canon. If they disagree with this root file, this root file wins.

For full protocols see: `.claude/rules/` (8 files, loaded automatically).
For DSP/skills/handoff details see: `docs/engineering/decision-simulation-skill/SKILL.md`.
For memory protocol see: `memory/atlas/wake.md`.
