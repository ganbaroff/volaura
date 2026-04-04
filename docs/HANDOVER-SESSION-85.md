# HANDOVER — Session 85
**From:** Session 84 (2026-04-04)
**Priority:** 10-DAY COMMAND PLAN (from GPT-5.4 external audit)
**Model recommended:** claude-sonnet-4-6 (High stakes — auth, E2E, real user path)

---

## PROTOCOL START (mandatory — say these 3 lines first)

> Protocol v8.0 loaded. Date: 2026-04-05.
> Last session: Session 84 — OAuth fix (3rd attempt), Universal Weapon research, Mem0 MCP installed, MindShift audit, CV corrected.
> I will NOT: (1) debug without asking "did I create this?", (2) execute solo without agents, (3) expand scope without CEO permission.

---

## READ FIRST (30 seconds)

| File | What it tells you |
|------|------------------|
| `docs/EXTERNAL-AUDIT-GPT54-2026-04-04.md` | GPT-5.4 audited 84 sessions. Verdict: stop expanding, start shipping to real users. Read before anything else. |
| `memory/context/sprint-state.md` | Session 84 position, 44% CEO directive completion rate, exact next priorities |
| `memory/swarm/SHIPPED.md` | What code is live vs what is still untested |
| `memory/context/mistakes.md` | 81 mistakes, 12 classes. CLASS 3 (solo) = 18 instances. CLASS 12 (self-inflicted complexity) = NEW. |

---

## CRITICAL: WHAT CHANGED IN SESSION 84

### 1. OAuth — 3rd attempt deployed, NOT yet verified

| Attempt | Method | Outcome |
|---------|--------|---------|
| #1 | Server-side `route.ts` | FAILED — 401, code_verifier not accessible server-side |
| #2 | Client-side `exchangeCodeForSession` | FAILED — 401, double exchange (singleton already auto-exchanges) |
| #3 | `onAuthStateChange` listener, no manual exchange | DEPLOYED — CEO must test in Session 85 |

- File: `apps/web/src/app/[locale]/callback/page.tsx` (live, no route group)
- Backup: `apps/web/src/app/[locale]/callback/route.ts.bak` (old server-side attempt)
- **CEO action required:** Open volaura.app in incognito → click Google login → confirm reaches dashboard

### 2. Google OAuth Client (NEW credentials)

- GCP Project: "My First Project"
- Client ID: `827100239570-q2s725chib0t7ufcs0mjqmne9ca3364m.apps.googleusercontent.com`
- App status: **TESTING MODE** — only `ganbarov.y@gmail.com` can log in
- Other users = "Access blocked: App has not completed Google verification"
- **To enable real users:** GCP Console → OAuth consent screen → Publish app (takes minutes)

### 3. Mem0 MCP — installed but needs Claude Code restart

- API Key: `m0-wTvhS6wWJ4r3iTFyzqr8zwyQSTMP44foUnqU5p9I` (saved to `apps/api/.env`)
- Windows env var: set via `[System.Environment]::SetEnvironmentVariable`
- `.mcp.json` configured with mem0 HTTP endpoint
- **Activation:** Mem0 MCP tools (`mem0_search`, `mem0_add`, etc.) should appear after restarting Claude Code
- **Test it:** Type `mem0_search "volaura sprint state"` — if it returns results, it's active

### 4. CV corrections

- MindShift: "Co-creator" corrected to **"Founder"** (CEO's product, not co-built with CTO)
- BrandedBy: **"Co-founder"** — CEO co-founded with a team, then left due to poor team dynamics
- File: `docs/Yusif_Ganbarov_CV_2026_v2.docx`

### 5. Universal Weapon Research — COMPLETE

- Report: `docs/research/UNIVERSAL-WEAPON-RESEARCH-2026-04-04.md`
- Winners: LibreChat + OpenHands + Letta (top 3 platforms)
- Memory winner: Mem0 (Rank 1 practical), PreCompact hook (Rank 1 quick fix)
- Orchestration winner: LangGraph (47/50) for CEO-proxy architecture
- CEO-proxy feasibility: CONFIRMED via `.claude/agents/`
- Market: $10B → $70B, memory+quality gap uncontested
- **80/20 rule:** Planning only, no UW code until VOLAURA E2E is confirmed working

---

## YOUR ROLE

You are CTO — builder and executor. NOT CEO-proxy. NOT architect of systems.

- ONE KPI: how many real people complete signup → assessment → AURA → share without manual rescue
- Close execution gaps, not expand systems
- Do NOT propose new protocols, governance layers, or architecture
- Do NOT start research (Universal Weapon, ecosystem) until E2E on volaura.app is confirmed

---

## 10-DAY COMMAND PLAN (GPT-5.4 — NON-NEGOTIABLE)

```
Days 1-2   → Product freeze. E2E walk on volaura.app with real email. Fix EVERY blocker found.
Days 3-4   → Micro-fixes on credibility flow (auth, onboarding, copy, share). Basic funnel visibility.
Days 5-6   → 3-5 real user walkthroughs. Fix where they stop, lose trust, or don't understand value.
Days 7-8   → Investor-grade MVP narrative. One story: verified profile → assessment → AURA → share → org value.
Days 9-10  → First 5-20 controlled invites. Minimal launch enablers only.
```

**We are at Day 1. OAuth verification = the gate to proceed.**

---

## WHAT TO DO FIRST (Session 85 — IN THIS ORDER)

**Step 1 — Verify Mem0 MCP is active**
Run `mem0_search "volaura sprint state"` — if returns results, proceed. If not, check `.mcp.json` config.

**Step 2 — CEO tests OAuth**
CEO opens volaura.app in incognito → Google login → you watch Vercel logs. Document outcome. If broken → diagnose root cause (simple first). If working → proceed to Step 3.

**Step 3 — E2E walk on volaura.app (Day 1 of 10)**
Walk the ENTIRE journey with a fresh email:
1. Sign up (email or Google)
2. Complete onboarding
3. Take assessment (1 full competency)
4. View AURA score
5. Share profile
6. Verify the shared link is publicly viewable

Document EVERY point where something fails, errors, looks wrong, or requires manual intervention. Do not skip. Do not fix as you go — document first, fix second.

**Step 4 — Fix blockers (simple first, complex last)**
Apply the Simple-First Escalation table:
- Under 5 min → fix immediately
- 5-20 min → fix, then report
- Over 20 min → brief CEO with 2 options before proceeding

**Step 5 — Apply pending migrations (if auth is confirmed working)**
- Migration `20260403000003` — GDPR fields (age_confirmed, terms_version, terms_accepted_at)
- Apply via Supabase Dashboard → SQL editor (NOT via CLI, CEO 1-click approval first)
- After migration: `is_platform_admin = true` for Yusif's user row (admin panel activation)

---

## WHAT TO STOP (CEO DIRECTIVE — IRON RULE)

| STOP | Why |
|------|-----|
| New protocols, meta-layers, governance docs | Process theater (CLASS 10). 9 versions of TASK-PROTOCOL, 0% adoption without CEO activation phrase. |
| Research (Universal Weapon, ecosystem) | 419 types, 90 questions, 48 agents, 0 real users. Research does not ship product. |
| Counting "done" by typecheck/preview | 512 tests pass ≠ product works (Mistake #52, CLASS 7). User reality = the only test. |
| Solo execution | CLASS 3, 18 instances. Any task >30 min without agents = structural failure. |
| Scope expansion | GPT-5.4: "Market doesn't reward smart layers." One KPI. One path. |

---

## KEY NUMBERS (context for every decision)

| Metric | Value |
|--------|-------|
| Sessions completed | 84 |
| Documented mistakes | 81 |
| Failure classes | 12 |
| CEO directive completion (Session 84) | 44% (regression from 80% in Session 83) |
| Defect rate | 34.8% (73 bugs / 210 commits) |
| Real users | 0 |
| Active agents built | 48 |
| Tests passing | 742 (1 pre-existing failure in test_match_checker.py) |
| Budget | $50/mo |
| Runway | ~6 weeks to launch |
| Gap to Toyota quality standard | 200,000x |

---

## CEO IRON RULES (always active — no activation phrase needed)

| Rule | What it means |
|------|--------------|
| "Простые шаги сначала" | Hardware before software. Settings before drivers. Replace before debug. Ask "Did I create this?" before any debug session >5 min. |
| "Почему без агентов?" | If you did a task >30 min solo, you violated this. Every non-trivial task uses agents. |
| "80% VOLAURA / 20% Universal Weapon" | UW is planning only. Zero UW code until VOLAURA E2E works. |
| "Ты CTO не CEO" | Build and execute. Do not strategize, expand, or theorize. |
| "10 задач стало 2 а похуй" | Track ALL CEO directives. Never silently drop tasks. Build a task matrix at session start. |
| "ТЫ это я. Ты мозги, не руки" | CEO-proxy role confirmed — but not yet integrated. This is future phase. Do not implement now. |
| "Haiku запрещён" | NEVER use Haiku as subagent. Opus = brain (plan, review). FREE external models = hands (Gemini Flash, Llama 3.3 NVIDIA, DeepSeek R1). Heavy models only for planning/verification. |

---

## INFRASTRUCTURE STATE (what is live and where)

| Service | URL / Location | Status |
|---------|---------------|--------|
| Frontend | volaura.app (Vercel) | Live — new Vercel project (route group bug fixed) |
| Backend | Railway (FastAPI) | Live — Langfuse, NVIDIA, Dodo keys deployed |
| Database | Supabase PostgreSQL | Live — pending migration 20260403000003 |
| AI Office | /admin/swarm | Live — 48 agents, proposal inbox, mobile-first |
| Analytics | /api/analytics/event | Live — 6 frontend events wired |
| Verification | /u/{username}/verify/{sessionId} | Live |
| Langfuse | cloud.langfuse.com | Keys on Railway, wiring via LiteLLM pending |
| Telegram bot | Configured | 6 commands registered, webhook secret fixed |
| Mem0 MCP | .mcp.json | Needs Claude Code restart to activate |
| Ollama | Local RTX 5060 GPU | Qwen3 8B + GLM-OCR running |

---

## PENDING (BLOCKERS FOR LAUNCH)

| Blocker | Status | Priority |
|---------|--------|----------|
| OAuth Google login | 3rd attempt deployed, unverified | P0 — Session 85 Day 1 |
| Google OAuth app in testing mode | Real users blocked | P0 — must publish app in GCP |
| GDPR migration 20260403000003 | Written, not applied | P1 — apply after OAuth verified |
| Admin panel activation | is_platform_admin=true for Yusif | P1 — after GDPR migration |
| E2E user journey with real email | Not executed (Session 83+84 deferred) | P0 — Day 1 of 10-day plan |
| Dodo Payments integration code | Research done, 0 code | P2 — after E2E confirmed |
| Langfuse via LiteLLM | Keys on Railway, not wired | P3 — observability, not launch blocker |
| Funnel visibility (conversion metrics) | Not implemented | P2 — needed for Days 3-4 |

---

## FILES CREATED THIS SESSION (Session 84)

| File | Purpose |
|------|---------|
| `docs/research/UNIVERSAL-WEAPON-RESEARCH-2026-04-04.md` | 6-agent Universal Weapon platform research |
| `docs/EXTERNAL-AUDIT-GPT54-2026-04-04.md` | GPT-5.4 audit of 84 sessions — read first |
| `apps/web/src/app/[locale]/callback/page.tsx` | OAuth callback v3 (onAuthStateChange) |
| `apps/web/src/app/[locale]/callback/route.ts.bak` | Previous attempt backup |
| `apps/web/src/app/[locale]/(auth)/callback/page.tsx.bak` | Earlier attempt backup |
| `memory/context/mistakes.md` (updated) | CLASS 12 added, Mistake #79 |
| `memory/context/patterns.md` (updated) | Simple-First Escalation, "Did I Create This?" |
| `memory/context/sprint-state.md` (updated) | Session 84 audit, 44% completion rate |
| `memory/swarm/SHIPPED.md` (updated) | Session 84 deliverables |

---

## QUALITY GATES BEFORE ANY TASK IS "DONE"

Minimum 3-item DoD (enforced — no exceptions):
1. **User can complete it** — walked through in Playwright or real browser, not just code passes
2. **No regression** — checked with `grep -rn` what else uses the changed code
3. **CEO can see it** — deployed to volaura.app, not just local

CLASS 7 reminder: 742 tests passing does not mean product works. Unit tests missed 4 production-breaking bugs in Session 43. E2E on the real URL is the only truth.

---

## AGENT ROUTING (before any task >30 min)

| Task type | Agents to call |
|-----------|---------------|
| Bug fix | `memory/swarm/skills/qa-quality-agent.md` + Security Agent (for auth bugs) |
| E2E walk analysis | `memory/swarm/skills/onboarding-specialist-agent.md` + Customer Success Agent |
| Copy/UX text | `memory/swarm/skills/behavioral-nudge-engine.md` + `memory/swarm/skills/cultural-intelligence-strategist.md` |
| Performance / load | `memory/swarm/skills/performance-engineer-agent.md` |
| Any batch close | `memory/swarm/skills/ceo-report-agent.md` — CEO receives business language, not engineering log |

Rule: If you did a task solo that took >30 min → it was CLASS 3. Acknowledge and route correctly next time.

---

## WHAT GOOD LOOKS LIKE (Session 85 success criteria)

```
DONE when:
1. CEO successfully logs in via Google on volaura.app (confirmed in browser, not inferred)
2. Fresh email signup → assessment → AURA score → profile share works end-to-end
3. Every blocker from E2E walk is documented with severity + fix status
4. GDPR migration 20260403000003 applied (or explicit CEO decision to defer)
5. No new protocols, governance docs, or scope expansions created
```

If criteria 1-3 are not met → session is not complete, regardless of lines of code written.
