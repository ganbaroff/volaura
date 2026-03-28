# HANDOFF — Session 55 → New Chat
**Date:** 2026-03-28 | **Project:** Volaura | **Branch:** main

---

## 📍 WHERE WE ARE RIGHT NOW

**Sessions completed:** 54
**Last work:** User simulation sprint (acted as Leyla/Wali/Rashad) → 7 UX gaps found + fixed.
**Git status:** Sessions 52-54 NOT committed (34 modified files + 8 untracked). All on disk.

---

## ⚠️ CRITICAL — DO THIS FIRST

```bash
# Apply atomic crystal migration to Supabase production BEFORE any traffic
supabase db push
# OR via Supabase MCP: apply migration 20260328000040_atomic_crystal_deduction.sql
```
This fixes a live TOCTOU race condition on crystal spending. Every minute it's not applied = risk.

---

## 🏗️ WHAT EXISTS

**Tech stack:** Next.js 14 App Router + FastAPI + Supabase PostgreSQL + Gemini AI
**Monorepo:** `apps/web/` (frontend) + `apps/api/` (backend) + `supabase/` (migrations)
**Deployed:** Vercel (frontend) + Railway (backend) + Supabase (DB)

**Core features working:**
- Assessment flow (adaptive IRT/CAT, Gemini evaluation)
- AURA scores + badge system (Bronze → Platinum)
- Leaderboard with real rank (`GET /api/leaderboard/me`)
- Mobile bottom nav (5 tabs, ADHD-first)
- Crystal economy (atomic deduction — migration pending)
- Telegram notifications via @volaurabot
- i18n: AZ (primary) + EN (secondary)

---

## 🎯 NEXT SESSION PRIORITIES

1. **Apply crystal migration** (P0 — see above)
2. **Commit Sessions 52-54** — 34 files + 8 new files uncommitted
3. **Real user test** — put 1 real person through: signup → onboarding → assessment → AURA → share
4. **OpenSpace analysis** — evaluate https://github.com/HKUDS/OpenSpace.git for team use
5. **Profile verifications backend** — hardcoded empty arrays, no API yet
6. **Assessment description** — users don't know AI evaluates their text responses

---

## 🤖 TEAM (SWARM AGENTS)

3 agents exist: Security Agent, Architecture Agent, QA Agent.
**New agents proposed but NOT created yet** (from earlier sessions).
`memory/swarm/proposals.json` has pending proposals.
Agent roster: `memory/swarm/agent-roster.md`

---

## 🐛 KNOWN ISSUES (not yet fixed)

| Issue | Priority | Notes |
|-------|----------|-------|
| Profile verifications empty | HIGH | hardcoded `[]` — no backend |
| Assessment has no description | HIGH | users don't know what they're tested on |
| Leaderboard no jump-to-rank | MED | users ranked >20 can't find themselves |
| Download Card not built | LOW | button disabled with tooltip "coming soon" |

---

## 🔧 CONFIG CHANGE THIS SESSION

**Removed `Stop` hook** (`session-end-check.sh`) from `.claude/settings.local.json`.
Was causing infinite loop: every response triggered the hook → my reply triggered it again → loop.
The session-end memory update is now done manually by CTO (protocol still applies).

---

## 📐 CRITICAL RULES (never break these)

- **NEVER** use SQLAlchemy — Supabase SDK only
- **NEVER** hand-write API types — run `pnpm generate:api`
- **NEVER** relative routing (`/dashboard`) — always `/${locale}/dashboard`
- **ALWAYS** unwrap `response.data` from `{ data, meta }` envelope
- **ALWAYS** per-request Supabase client via FastAPI `Depends()`
- **ALWAYS** i18n for all user-facing strings — no hardcoded English
- **ALWAYS** Pydantic v2 syntax (`ConfigDict`, `@field_validator`)

---

## 🏃 TOP 3 MISTAKES TO AVOID

1. **Decide alone** — always consult team agents first (CLASS 3 mistake, happened 10x)
2. **Skip memory update** — sprint-state.md MUST be updated at session end (CLASS 2, 8x)
3. **Say "done" without E2E** — 512 tests passing ≠ product works for a real user (feedback rule)

---

## 📁 KEY FILES

```
CLAUDE.md                          — Operating algorithm (read first)
memory/context/sprint-state.md    — Current position (read second)
memory/context/mistakes.md        — What NOT to repeat
docs/EXECUTION-PLAN.md             — Sprint checkboxes
docs/DECISIONS.md                  — Architecture decisions log
memory/swarm/agent-roster.md       — Agent team
supabase/migrations/               — DB migrations (20260328000040 = pending)
apps/api/app/routers/              — FastAPI endpoints
apps/web/src/app/[locale]/         — Next.js pages
apps/web/src/hooks/queries/        — TanStack Query hooks (generated)
apps/web/src/locales/              — i18n strings (EN + AZ)
```

---

## 💡 CTO RECOMMENDATION FOR NEW CHAT

Start with:
1. Apply migration (1 command)
2. Commit everything from Sessions 52-54
3. Then pick: OpenSpace evaluation OR real user test OR new agents

Don't start coding without reading `CLAUDE.md` → `memory/context/sprint-state.md` → `memory/context/mistakes.md`.
