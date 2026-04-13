# ECOSYSTEM MAP — VOLAURA 5-Product Network
**Auto-read by all swarm agents at init. Updated by CTO after each sprint.**
**Last Updated:** 2026-04-15 (Constitution v1.7, ZEUS→Atlas rename)
**Authority:** ECOSYSTEM-CONSTITUTION.md v1.7 supersedes everything in this file.

---

## THE RULE BEFORE ALL RULES

Every agent, every proposal, every line of code is governed by the **ECOSYSTEM CONSTITUTION**.
Read it: `docs/ECOSYSTEM-CONSTITUTION.md` (VOLAURA repo, branch `claude/blissful-lichterman`)
Or: `git show origin/claude/blissful-lichterman:docs/ECOSYSTEM-CONSTITUTION.md`

**5 Foundation Laws (memorize these):**
1. **NEVER RED** — errors = purple `#D4B4FF`, warnings = amber `#E9C400`. Zero exceptions.
2. **Energy Adaptation** — every product needs Full/Mid/Low energy modes.
3. **Shame-Free Language** — no "you haven't done X", no profile % complete, no streaks at 0.
4. **Animation Safety** — max 800ms for non-decorative, no infinite loops, `prefers-reduced-motion` mandatory.
5. **One Primary Action** — one CTA per screen. ≤5 tappable elements on mobile without scroll.

**7 Crystal Economy Laws (summarized):**
- Rewards must be: informational, unexpected, identity-framed, collaborative
- NO leaderboards of any kind (Law 5 — Crystal Law 7)
- NO badge display immediately after assessment (Crystal Law 6 Amendment)
- NO crystals visible during or immediately after assessment (G21)
- Crystal earn requires simultaneous spend path (Crystal Law 8)

---

## 5 PRODUCTS — CURRENT STATE

| Product | Repo | Status | Port/URL |
|---------|------|--------|----------|
| **VOLAURA** | `C:\Projects\VOLAURA` | ✅ Live | `https://volaura.app` |
| **Atlas Gateway** | `C:\Users\user\Downloads\claw3d-fork\server\` | ✅ Running | `wss://zeus-gateway-production.up.railway.app` + `ws://localhost:18789` |
| **Life Simulator (claw3d)** | `C:\Users\user\Downloads\claw3d-fork\src\` | 🔄 65% | `http://localhost:3000` |
| **MindShift** | `C:\Users\user\Downloads\mindshift\` | ✅ 92% | Vercel (separate Supabase: `awfoqycoltvhamtrsvxk`) |
| **BrandedBy** | `packages/swarm/archive/zeus_video_skill.py` | 🔄 15% | No UI yet |

---

## VOLAURA — Verified Talent Platform

**Core promise:** "Prove your skills. Earn your AURA. Get found by top organizations."

**Tech stack:** Next.js 14 App Router + FastAPI + Supabase PostgreSQL + pgvector(768)

**Key files:**
| File | What |
|------|------|
| `apps/api/app/routers/assessment.py` | Assessment start/answer/complete (IRT/CAT engine) |
| `apps/api/app/routers/aura.py` | AURA score, explanation, sharing |
| `apps/api/app/routers/organizations.py` | B2B org dashboard, volunteer search |
| `apps/api/app/core/assessment/engine.py` | Pure Python 3PL IRT + EAP, no external library |
| `apps/api/app/services/bars.py` | LLM evaluation pipeline (Gemini primary) |
| `apps/web/src/app/[locale]/(dashboard)/` | All dashboard pages |

**Assessment pipeline:**
```
POST /api/assessment/start
→ POST /api/assessment/answer (IRT theta update after each answer)
→ POST /api/assessment/complete/{session_id}
   → upsert_aura_score RPC
   → emit crystal_earned + skill_verified to character_events
```

**Anti-gaming gates (multiplicative):**
1. min_length < 30 words → cap 0.4
2. stuffing_detection → 0.3×
3. coherence_heuristic → 0.55×
4. scenario_relevance → 0.65×

**AURA score weights (FINAL — DO NOT CHANGE):**
communication 0.20 · reliability 0.15 · english_proficiency 0.15 · leadership 0.15 · event_performance 0.10 · tech_literacy 0.10 · adaptability 0.10 · empathy_safeguarding 0.05

**Badge tiers:** Platinum ≥90 · Gold ≥75 · Silver ≥60 · Bronze ≥40

**DB schema highlights:**
- `profiles` — account_type, visible_to_orgs (default true)
- `aura_scores` — total_score, badge_tier, percentile_rank, effective_score
- `assessment_sessions` — IRT state, theta, answers JSONB
- `character_events` — cross-product bus (source_product, payload JSONB)
- `game_crystal_ledger` — crystal rewards (NOT delta, NOT reason — exact columns)
- `analytics_events` — 390-day GDPR retention (GitHub Actions cron delete)

**Open PRs:**
- PR #9 — Dashboard NewUserWelcomeCard (ready to merge)
- PR #12 — Constitution v1.3 base (Constitution v1.7 now on branch `claude/blissful-lichterman`)

**Active Constitution violations FIXED this session:**
- G9: Leaderboard page deleted (was `/app/[locale]/(dashboard)/leaderboard/page.tsx`)
- G15: Score counter 2000ms → 800ms (aura/page.tsx + complete/page.tsx)
- G21 + Crystal Law 6: Badge/crystals removed from assessment complete page

**Pre-launch blockers (19 total — see Constitution Part 3):**
Critical path: Energy picker · Pre-Assessment Commitment Layer · DIF audit · SADPP registration · Soniox DPA · Vulnerability Window content · Landing sample AURA profile

---

## ATLAS GATEWAY — Agent Infrastructure

**Two disconnected systems (current reality):**

| System | Location | Agents | Memory |
|--------|----------|--------|--------|
| Node.js Gateway | `claw3d-fork/server/zeus-gateway-adapter.js` | 39 | `claw3d-fork/memory/session-context.md` |
| Python Swarm | `packages/swarm/` | 44 | `memory/swarm/shared-context.md` |

**They share ONLY the filesystem. No WebSocket or HTTP between them yet.**
**Bridge planned: `autonomous_run.py` → POST to `/event` endpoint (~20 lines).**

**Node.js LLM hierarchy (authoritative):**
```
Cerebras Qwen3-235B (2000+ tokens/sec)
  → Gemma4 via Ollama (LOCAL GPU — zero cost, zero rate limit)
  → NVIDIA NIM (Nemotron 253B)
  → Anthropic Haiku (last resort)
```

**Python Swarm LLM hierarchy (as of 2026-04-06):**
```
Ollama qwen3:8b (LOCAL GPU — priority 0, zero cost)  ← ADDED this session
  → Groq (14 active models, 14.4K req/day free)
  → Gemini (5 models, 15 RPM free)
  → DeepSeek (paid, deep reasoning)
```

**P0 open items (Atlas Gateway):**
- JWT WebSocket auth (code ready in `memory/agent-findings/Z-EV-MNMVBDDE`) — needs Railway deploy
- WEBHOOK_SECRET_RAILWAY/GITHUB/SENTRY — set in Railway Dashboard
- Python↔Node.js bridge — ~20 lines in autonomous_run.py

---

## MINDSHIFT — Daily Focus Platform

**Repo:** `C:\Users\user\Downloads\mindshift\`
**Status:** v1.0, Google Play awaiting account verification
**Supabase:** separate project `awfoqycoltvhamtrsvxk`

**Key rules (Constitution MindShift section):**
- Hard stop at 90 min (3-stage warning: 80→85→90min)
- 66% capacity rule: NOW≤3 tasks, NEXT≤6
- Streaks: invisible when 0 or 1
- Audio: pink noise default (g=0.249 ADHD effect size)
- Crystal chip: Progress page ONLY, never post-session

---

## LIFE SIMULATOR — 3D Agent Office

**Repo:** `C:\Users\user\Downloads\claw3d-fork\src\`
**Stack:** Next.js + React Three Fiber + Three.js 0.183.2
**GitHub:** `https://github.com/ganbaroff/Claw3D`

**10-state model (Phase 1 done):**
```
idle → #f59e0b amber
focused → #06b6d4 cyan
working → #22c55e green
waiting → #eab308 yellow
blocked → #f97316 orange
overloaded → #c084fc PURPLE (Law 1 — NEVER RED)
recovering → #a855f7 purple
degraded → #6b7280 gray
meeting → #3b82f6 blue
error → #f97316 orange (Law 1 — NEVER RED)
```

**Phase 2 open:** Ready Player Me avatars · `agent.wake` event wiring · blocked/overloaded/recovering derivation

---

## CROSS-PRODUCT EVENT BUS

All products write to `character_events` table in VOLAURA Supabase:

```sql
character_events (
  source_product TEXT,  -- 'volaura' | 'mindshift' | 'life_simulator' | 'atlas'
  event_type TEXT,      -- 'crystal_earned' | 'skill_verified' | 'xp_gained'
  payload JSONB,
  user_id UUID
)
```

**Flow:** VOLAURA assessment complete → `crystal_earned` event → Life Simulator reads → character gets crystals

**Crystal sequencing rule (Crystal Law 8):** Never emit crystal_earned without an active spend path.

---

## AGENT ROUTING — WHEN TO CALL WHOM

| Task domain | Call |
|-------------|------|
| Architecture / tech decisions | `architecture-agent` |
| Security, RLS, auth | `security-agent` |
| UX, product features | `product-agent` |
| Infrastructure, Railway, deploy | `devops-sre-agent` |
| Multi-domain synthesis | `swarm-synthesizer` |
| Constitution compliance | Any agent with Constitution context injected |

**Never call Claude (Haiku/Sonnet/Opus) as a swarm agent — use external providers only.**
**Always diverse: Gemini + Groq + Ollama = different providers = real disagreement.**

---

## KNOWN BUGS — DO NOT RE-PROPOSE FIXES

| ID | Issue | Status |
|----|-------|--------|
| BUG-005 | list_org_volunteers OOM | Deferred post-beta |
| BUG-011 | Fire-and-forget notification failure | Architectural, documented |
| BUG-016 | JWT revocation (logout doesn't invalidate sessions) | Sprint 6 |
| SEC-030 | rating CHECK constraint (float not validated at DB) | BATCH L |

---

## WHAT NOT TO PROPOSE

- Redis for rate limiting (not needed <2 Railway instances)
- Microservices / API gateway (monolith intentional)
- Celery/workers (use Supabase Edge Functions or pg_cron)
- Leaderboards of ANY kind (Crystal Law 5 + G9)
- Badge display immediately after assessment (Crystal Law 6 Amendment)
- Score count-up > 800ms (G15)
- Red color anywhere (Law 1)
- "Profile X% complete" (Law 3)
