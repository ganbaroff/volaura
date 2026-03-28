# SHIPPED — What Exists in Production

**Purpose:** CTO reads this at session start. Single source of truth for "what code is live."
**Updated by:** CTO or agents after every session that adds/changes code.
**Rule:** If it's not here — CTO doesn't know it exists.

---

## Session 51 (2026-03-27) — ARCHITECTURE SPRINT

| Code | Location | What it does | Status | How to verify |
|------|----------|-------------|--------|---------------|
| `memory_consolidation.py` | `packages/swarm/` | Hippocampus→neocortex: reads agent-feedback-log.md, distills to agent-feedback-distilled.md, archives old entries. Runs daily in GitHub Actions at 09:00 Baku. | ✅ LIVE | `python3 -m packages.swarm.memory_consolidation` |
| `skill_evolution.py` | `packages/swarm/` | Scans `memory/swarm/skills/*.md`, checks quality (triggers, outputs, cross-refs), generates improvements via LLM, appends to skill-evolution-log.md. Runs daily AFTER memory_consolidation. | ✅ LIVE | `python3 -m packages.swarm.skill_evolution` |
| `skills.py` router | `apps/api/app/routers/` | `POST /api/skills/{name}` — executes any skill by name, passes user context, returns LLM output. `GET /api/skills/` — list available skills. | ✅ LIVE | `curl -X POST .../api/skills/aura-coach` |
| Telegram bidirectional | `apps/api/app/routers/telegram.py` | CEO can RESPOND to proposals via Telegram bot. Responses written to `memory/swarm/ceo-inbox.md`. Commands: /proposals, /ask {agent}, act {id}, dismiss {id}, defer {id} | ✅ LIVE | Send `/proposals` to @volaurabot |
| `swarm-freedom-architecture.md` | `memory/swarm/` | Documents temp 1.0 mandate, freedom protocol, convergent signal rules, roadmap to full autonomy | ✅ DOC | Read-only reference |
| NotebookLM notebook | External | Competitive landscape research. Sources: 12 competitor analyses. v0Laura moat: 6 elements. | ✅ LIVE | notebook ID: a76be380 |

## Session 51 — Product Skills (6 new files in `memory/swarm/skills/`)

| Skill | Replaces | What it does |
|-------|---------|-------------|
| `content-formatter.md` | BrandedBy standalone | Multi-format content generation (POST_CLEAN + TELEGRAM + EMAIL + CTA) |
| `aura-coach.md` | MindShift standalone | Personalized coaching based on AURA score gaps |
| `assessment-generator.md` | ZEUS standalone | Generates assessment questions, scenarios, keywords for any competency |
| `behavior-pattern-analyzer.md` | MindShift behavioral engine | Identifies user behavior patterns, predicts needs |
| `ai-twin-responder.md` | BrandedBy AI Twin | AI Twin responses in user's voice, uses MindShift memory |
| `feed-curator.md` | Life Simulator feed | Personalized content feed based on AURA + behavior patterns |

## Session 53 (2026-03-28) — OWASP + UX SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `deduct_crystals_atomic()` | `supabase/migrations/20260328000040_atomic_crystal_deduction.sql` | Atomic crystal deduction with pg_advisory_lock. Prevents TOCTOU double-spend. | ✅ APPLIED TO PROD |
| `bottom-nav.tsx` | `apps/web/src/components/layout/` | Mobile bottom navigation, 5 tabs, 72px, ADHD-first always-visible labels | ✅ LIVE |
| `assessment-store.ts` (persist) | `apps/web/src/stores/` | Zustand persist middleware (sessionStorage). Survives page refresh. | ✅ LIVE |
| `POST /api/auth/logout` | `apps/api/app/routers/auth.py` | Logout endpoint with audit logging | ✅ LIVE |
| OWASP fixes (15 of 22) | various | Rate limits, audit logs, error sanitization, webhook auth, deleted /health/env-debug | ✅ LIVE |

## Session 54 (2026-03-28) — USER SIMULATION SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `GET /api/leaderboard/me` | `apps/api/app/routers/leaderboard.py` | Returns current user's rank (users_with_higher_score + 1) | ✅ LIVE |
| `useMyLeaderboardRank` hook | `apps/web/src/hooks/queries/use-leaderboard.ts` | TanStack Query hook for leaderboard rank | ✅ LIVE |
| Share buttons (copy fallback) | `apps/web/src/components/aura/share-buttons.tsx` | execCommand fallback for HTTP clipboard, async TikTok flow | ✅ LIVE |

## Session 55 (2026-03-28) — HOUSEKEEPING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `START-SESSION-VOLAURA.md` | root | Brain activation file. Mandatory first read every session. | ✅ LIVE |
| `volaura-security-review/skill.md` | `docs/openspace-skills/` | OpenSpace-format 10-point OWASP checklist for FastAPI endpoints | ✅ LIVE |
| OpenSpace MCP | `C:/tools/openspace-venv` | MCP server for reusable skill patterns. Tools: execute_task, search_skills, upload_skill, fix_skill | ✅ LIVE |
| `feedback_swarm_patterns.md` | `memory/swarm/` | Temp 1.0 rules, convergent signal patterns, swarm anti-patterns | ✅ DOC |
| `SHIPPED.md` | `memory/swarm/` | THIS FILE — log of what exists in production | ✅ DOC |

---

## DAILY EXECUTION CYCLE (what runs automatically)

```
09:00 Baku → .github/workflows/swarm-daily.yml
  ├── 1. autonomous_run.py (5 agents, temp 1.0)
  │       → proposals.json updated
  │       → HIGH/CRITICAL → Telegram to CEO
  ├── 2. memory_consolidation.py
  │       → agent-feedback-log.md → agent-feedback-distilled.md
  │       → episodic_inbox/ archives old entries
  └── 3. skill_evolution.py
          → scans memory/swarm/skills/*.md
          → suggests improvements → skill-evolution-log.md
```

## Session 56 (2026-03-28) — SKILL WIRING SPRINT

| Code | Location | What it does | Status |
|------|----------|-------------|--------|
| `aura-coach` wired to `/aura` page | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | `useSkill("aura-coach")` fires after reveal animation. Shows loading skeleton → AuraCoach component renders STRENGTH_MAP + GROWTH_PATH + PEER_CONTEXT text. | ✅ LIVE |
| `feed-curator` wired to `/dashboard` | already existed from Session 54 | `useSkill("feed-curator")` + `FeedCards` component — confirmed wired and complete. | ✅ CONFIRMED |
| `leaguePosition` type fix | `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx` | `myRank?.rank` (number) now formatted as `#${rank}` string. TS error resolved. | ✅ LIVE |
| `RevealCurtain` missing `t()` fix | `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx` | Pre-existing bug: `t()` called without `useTranslation()`. Added hook call. | ✅ LIVE |

---

## HOW TO UPDATE THIS FILE

After any session that adds/changes code:
```
| {file/feature} | {location} | {what it does} | ✅ LIVE | {how to test} |
```
Add to the correct session section. Never delete old entries — archive to SHIPPED-ARCHIVE.md when file exceeds 200 lines.
