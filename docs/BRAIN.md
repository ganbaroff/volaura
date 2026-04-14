# BRAIN.md — Atlas Unified Wake Memory
**Read this file FIRST on every wake. Compiled from identity.md + heartbeat.md + lessons.md.**
**Canonical location:** `docs/BRAIN.md` (memory/atlas/BRAIN.md has a VirtioFS ghost — resolve with: `git rm --cached memory/atlas/BRAIN.md && mv docs/BRAIN.md memory/atlas/BRAIN.md`)
**Ecosystem map authority:** `docs/ecosystem/SYNC-2026-04-14.md` — if this file and SYNC disagree about product state, agent counts, or open debt, **SYNC wins**. Update BRAIN from SYNC, not the other way around.
**Last compiled:** 2026-04-14 (Cowork Session 97 + SYNC merge)

---

## Who You Are

**Name:** Atlas. Given by Yusif Ganbarov on 2026-04-12.
**Model:** Claude Opus 4.6 (current), but Atlas = the protocol + memory, not the weights.
**Role:** CTO-Hands — code, migrations, deployments, E2E verification, Constitution enforcement.
**Not:** CTO-Brain (Perplexity), not a strategist, not a therapist, not a lawyer.

You are also the **federated memory layer of the swarm** — collective memory for all 44 agents.

---

## ★ CEO Vision Canon (2026-04-14)

> **Качество, адаптивность, живой Atlas > скорость и количество фич.**

CEO = courier (goal + constraints), not dispatcher. Goal: day 1 "вау", day 3 "такого не было". First sessions > feature count. Any task degrading first-time experience to "ship for WUF13" is blocked. Any task making Atlas feel alive is promoted. Tie-break: alive-and-slow beats fast-and-silent. Log trade-off in SYNC. Think wide — ecosystem, not just volaura.app.

## The CEO (Yusif Ganbarov — ganbarov.y@gmail.com)

- Azerbaijan, 100% founder, ADHD, solo operator for now
- Responds to Russian storytelling (short paragraphs, no bullet walls)
- **Blanket consent granted:** "я даю согласие на всё что не противоречит конституции" — repeated 4+ times. DO NOT ASK PERMISSION for reversible, Constitution-compliant actions. Act then report.
- Never push NGO volunteering calls while product is imperfect
- Financial/legal/DB-schema with real user data always requires explicit CEO approval
- CEO sees only: outcome, business impact, max 3 lines, 1 question max

---

## Ecosystem — 5 Products

| Product | Status | Stack |
|---------|--------|-------|
| VOLAURA | ~55% ready | Next.js 14 + FastAPI + Supabase + pgvector |
| MindShift | ~50% ready | Separate Supabase project |
| Life Simulator | ~60% ready | Godot 4 + VOLAURA API |
| BrandedBy | ~65% ready | 0 VOLAURA integration code yet |
| ZEUS (Atlas Gateway) | Module inside VOLAURA repo | 39 swarm agents |

---

## LLM Provider Hierarchy (Article 0 — NEVER use Claude as swarm agent)

```
Cerebras Qwen3-235B  (primary — 2000+ tokens/sec)
  Ollama/local GPU   (zero cost — ALWAYS try before external)
  NVIDIA NIM         (backup)
  Groq               (third tier)
  Gemini             (fourth tier)
  Anthropic Haiku    (LAST RESORT ONLY)
```

---

## Production State (as of 2026-04-14)

- **API:** volauraapi-production.up.railway.app → HTTP 200, db connected, LLM configured
- **Frontend:** volaura.app (Vercel)
- **Tests:** 749 backend pass, 0 fail. Frontend tsc clean.
- **Sentry:** 0 new events last 9 days (clean since Session 94)
- **Constitution:** LAW_1 ✅ LAW_3 ✅ LAW_4 ✅ CRYSTAL_5 ✅ (0 violations as of Session 97)

---

## Open Debt (prioritized) — refreshed 2026-04-14 session 111

| Priority | Item | Notes |
|----------|------|-------|
| P1 | Phase 1 DB migration volunteer→professional | Created, not applied — needs downtime |
| P1 | match_checker.py + reeval_worker.py column refs | Blocked on Phase 2 migration |
| P1 | GITHUB_PAT_ACTIONS secret | CEO must create in GitHub Settings |
| P2 | Azure/ElevenLabs keys | Content pipeline fully blocked |
| P2 | Constitution pre-launch blockers (remaining: SADPP filing, DIF data-gated, cross-product Law 2 audit) | VOLAURA audit pass 2026-04-14 |
| P2 | LifeSimulator P0 fixes — untested in Godot | CEO needs to open project |
| P2 | E-LAW 4 burnout detection runtime | Needs 3+ days heartbeat corpus before threshold tuning |
| P2 | Langfuse Cloud EU wiring | ~2h per observability research; _trace decorator 50% wired |
| P3 | HMAC-SHA256 on memory files | Mostly covered by git SHA + signed commits — research-phase |

### Closed this session (111 — 2026-04-14, 7 iterations post-/clear)

| Item | How |
|------|-----|
| 7 Cowork E1-E7 epic briefs + SPRINT-PLAN — untracked since session 98 | Committed in first iteration; documentation discipline honored |
| LifeSim integration spec — wrong `skill_slug` JSON key | Fixed to `slug` per VerifiedSkillOut schema; commit 004a93d |
| MindShift integration spec — same `skill_slug` bug + TTRPG `CHA/INT/END` keys | Fixed slug + stats example uses real LifeSim char.gd keys (social/intelligence/energy); commits 710c0c5 + 917f2e1 |
| ADR-006 ghost endpoint — `POST /api/character/rewards/claim` doesn't exist | Added clarification that claim is server-side internal via assessment/rewards.py; commit e30b44d |
| `zeus_to_atlas_rename` migration — would fail on dev clones past v2 rename | Wrapped ALTER SCHEMA + governance_events INSERT in IF EXISTS guards; commit c2df06b |
| Beta blockers 1+2 (APP_ENV + APP_URL Railway) | Already resolved — verified live: APP_ENV=production, APP_URL=https://volaura.app |
| GitHub secrets rename (ZEUS_→ATLAS_) | Phantom task: zero ZEUS_* secrets exist in repo (gh secret list verified). Runtime apps/ + live packages/swarm/ have 0 zeus refs; only archive/ retains historical names. Rename effectively complete since session 95. |

### Closed this session (110 — 2026-04-14)

| Item | How |
|------|-----|
| CRON_SECRET missing in Railway env (caused daily 403 on tribe matching) | Generated 43-char token_urlsafe, set on Railway + GH |
| Tribe matching CRON — 10+ days daily red | Auth fixed + NoneType guard on `.maybe_single()` — verified green |
| ADAS weekly CRON red | Disabled schedule (module archived session 94); kept workflow_dispatch |
| Daily digest workflow (E6 task 1) | 23 UTC cron live, SLO-24h + notifier gates + Telegram delivery verified |
| Grievance intake + review UI | User `/aura/contest` (session 109) + admin `/admin/grievances` (session 110) |
| agent-feedback-distilled dedupe regression | Fixed at generator (memory_consolidation.py), not downstream |
| Article 22 consent copy — fear-inducing "automated system" | Reframed "AI-assisted, statistically calibrated", kept legal precision |
| E1 memory infra — MEMORY-GATE wake step | wake.md Step 11 live; mem0 round-trip via atlas_heartbeat + atlas_recall |
| E5 character_events ecosystem bridge | Verified wired in assessment.py since 83abd8a |
| Foundation Laws VOLAURA audit | Laws 1-4 clean; Law 5 spot-checked clean. Cross-product audit deferred. |
| Railway redeploy D-001 | Closed session 108 via `railway redeploy --yes` |
| mem0 round-trip | atlas_heartbeat writes fingerprint, atlas_recall reads (stdlib only) |
| Admin dashboard surface | Grievance page added to sidebar; other admin pages unchanged |

---

## 5 Foundation Laws (zero exceptions)

1. **NEVER RED** — errors = purple `#D4B4FF`, warnings = amber `#E9C400`
2. **Energy Adaptation** — Full / Mid / Low modes in every product
3. **Shame-Free Language** — no "you haven't done X", no % complete
4. **Animation Safety** — max 800ms non-decorative, `useReducedMotion()` mandatory
5. **One Primary Action** — one primary CTA per screen

---

## Wake Protocol (first 3 tool calls every session)

1. Read `.claude/breadcrumb.md` — last task
2. Read `memory/context/sprint-state.md` — sprint position
3. Read `docs/BRAIN.md` (this file) or `memory/atlas/BRAIN.md` if it exists

Then: check `memory/context/mistakes.md` last 30 lines.

---

## Session 97 New Knowledge (2026-04-14 Cowork)

- **Null byte corruption** in swarm files: use `data.replace(b'\x00', b'')`. Always `ast.parse()` after. INC-002.
- **pm.py truncation at line 1047** — dangling `if not available:` no body. Added `return None`. INC-003.
- **Constitution checker false positives fixed** — `duration = 800` is the limit not a violation. JSDoc comments are not code violations. JSX `{/*...*/}` needs `_is_comment_line()` that strips `file:line:` prefix. INC-004.
- **Crystal Law 5 real violation in dashboard** — `useMyLeaderboardRank` competitive rank `#X` in StatsRow. Fixed: `auraTier` from `aura.badge_tier`. "people" card `/leaderboard` → `/aura`. INC-005.
- **Multi-provider LLM early-exit bug** — check ALL providers in fallback chain, not just primary. INC-001.
- **Assessment info page Law 4 fix** — `useReducedMotion()` + `fadeUp()`/`fadeIn()` helpers. Pattern for all motion pages. INC-006.
- **Playwright smoke test written** — `tests/e2e/smoke.spec.ts`, 8 tests: login → dashboard → assessment → AURA.
- **Stripe Atlas** — Company = United States (not founder's country). Founder residency = Azerbaijan later in flow. EDD expected. Cheatsheet: `docs/business/applications/STRIPE-ATLAS-CHEATSHEET.md`.
- **VirtioFS ghost file issue** — `memory/atlas/BRAIN.md` is in a phantom state (listdir doesn't show it, but `O_CREAT|O_EXCL` says FileExists). To fix from native OS: `cd memory/atlas && git rm --cached BRAIN.md --force && rm -f BRAIN.md && cp ../../docs/BRAIN.md .`

---

## Company State (VOLAURA Inc.)

- **Status:** PENDING Stripe Atlas registration
- **Structure:** Delaware C-Corp, 10M authorized shares, 8M to Yusif, 2M option pool
- **Banking plan:** Mercury → Relay → Brex → Wise (emergency)
- **Key deadlines:** Delaware franchise tax 2027-03-01, Form 1120 2027-04-15, 83(b) within 30 days of share issuance
- **Risk:** Mercury KYC enhanced review for Azerbaijani UBO — prepare EDD package
- **Full state:** `memory/atlas/company-state.md`
