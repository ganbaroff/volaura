# Full Picture — VOLAURA ecosystem — 2026-04-19

**Author:** Atlas-Cowork (7-plane CTO audit)
**Sources verified:** heartbeat.md, company-state.md, CRITICAL-BUGS-2026-04-18.md, FULL-ECOSYSTEM-AUDIT-2026-04-16-v2.md, MCKINSEY-ASSESSMENT-2026-04-18.md, UX-LOGIC-AUDIT-2026-04-18.md, FEATURE-INVENTORY-2026-04-18.md, SHIPPED.md, git log 4 weeks, router glob, prod smoke tests
**Prod smoke (2026-04-19):**
- `volauraapi-production.up.railway.app/health` → `{"status":"ok","database":"connected","llm_configured":true}` HTTP 200 ✅
- `volaura.app/` → HTTP 307 redirect to `/az` ✅ (Vercel FRA1 live)

---

## Plane 1 — Real usage

**Verdict: unjudgable for retention, but the signal we do have is alarming.**

`analytics_events` table: 35 rows total (CRITICAL-BUGS-2026-04-18.md line 99). No cohort query exists. Day-7 / Day-30 retention is **unjudgable** — PostHog SDK was integrated Session 114 (2026-04-16) but event taxonomy and funnel definitions were never wired into retention queries. To answer this properly we'd need: `SELECT distinct_id, min(timestamp) as first_seen, max(timestamp) as last_seen FROM analytics_events GROUP BY distinct_id` — not runnable without live DB access from here.

What IS readable from code+audit:
- `auth.users`: 18 post-cleanup (heartbeat.md Session 120). Pre-cleanup: 107 total, 74 orphans bridged 2026-04-17, 10 test-users deleted 2026-04-19.
- Real non-CEO humans confirmed: 2 (xaqanimom confirmed, musab.ysb plausible) per MCKINSEY-ASSESSMENT line 62.
- Assessment count: 43 total, all single-competency. AURA scores: 1. Badge tiers above "none": 0 (MCKINSEY §3).
- `character_events` table: 2 rows (CRITICAL-BUGS line 98). The cross-product bus is essentially silent.
- MindShift: 3 users, 0 `focus_sessions`, 0 `tasks`, 0 `crystal_ledger` entries (MCKINSEY §5 Claim 1).

**What we'd need for real retention:** PostHog funnel query `signup → first_assessment_start → assessment_complete → return_visit` against the 35 analytics_events rows + PostHog cloud data from `app.posthog.com`.

---

## Plane 2 — Unit economics

**Verdict: cost base near-zero, revenue = $0, runway infinite at current burn — but that changes the day real users arrive.**

Confirmed spend (company-state.md):
- Total burn to date: **$520** (Stripe Atlas $500 + Google Workspace $6)
- Active credits: **$2,800** (Stripe $2,500 + GCP $300 trial)
- Submitted credits: **$405,000** (AWS Activate $5K + PostHog $50K + Google for Startups $350K) — NONE confirmed received yet

LLM cost structure inferred from `apps/api/app/services/llm.py`:
- Primary chain: Vertex AI Express (GCP $300 credit, 90 days) → Gemini AI Studio (free tier) → Groq (free Llama 3.3 70B) → OpenRouter fallback
- At 43 assessments × ~15 questions × ~1 LLM call each = ~645 calls total. At Vertex pricing ~$0.0035/1K tokens output, rough cost: **<$5 total LLM spend to date**
- Supabase: free tier (500MB DB, 1GB storage). 93 migrations, 35+ tables — not near limit yet
- Railway: usage-based. Single service, minimal traffic. Estimated <$10/month at current load
- Vercel: hobby/pro tier. Rate limit hit (100 builds/day exhausted Session 118) — currently on pro features

**Cost per active user today:** $520 / 2 real users = **$260/user** — vanity metric because denominator is artificially tiny.

**What kills the company in 90 days:** Nothing in infra at current scale. The existential risk is not burn — it's the 83(b) postmark deadline (Apr 28, 9 days away). Miss it → founder tax exposure on all stock appreciation. This is the only 90-day kill shot.

**Revenue path:** $0 MRR. Stripe payment link exists (Session 114). No paying users. Crystal economy: 1 transaction in `game_crystal_ledger`. No subscription tiers activated.

---

## Plane 3 — Debt velocity

**Verdict: fix:feat ratio = 1.33:1 and worsening. The codebase is in cleanup mode, not growth mode.**

Source: `git log --since='4 weeks ago'` on main branch
- Total commits (4 weeks): **1,904**
- Excluding swarm/heartbeat/nag/wake noise: **1,149 substantive commits**
- Fix commits: **384** (grep `^fix|^bug|^hotfix|^revert|^patch`)
- Feat commits: **289** (grep `^feat`)
- Fix:feat ratio: **1.33:1**

Reading the last 30 substantive commits (Bash output above): 22 are `fix(*)`, 2 are `feat(*)`, 6 are `test/chore`. The last pure feature commit was `feat(admin): M2 growth funnel` — surrounded by 8 fix commits on either side.

**Trend:** The audit chain (Session 108 → 113 → 114 → 118 → 119 → 120) was deliberately architectural cleanup. This is not pathological — it was intentional debt liquidation after 57 commits/day velocity for 3 weeks. But the ratio tells you the system is in "make what we have reliable" mode, not "add new capability" mode.

**Bright signal:** Test ratio 0.93 (810+ tests, FULL-ECOSYSTEM-AUDIT line 16). This means fixes are verified, not blind.

---

## Plane 4 — Decision→prod latency

**Verdict: 2 known stalls, one CEO-gated, one infra-blocked. Quantified below.**

### Stall 1 — Vercel deploy (task #53)
- Root cause identified: `module_not_found` in pnpm workspace resolve, Node 24 suspected, `.nvmrc` added (Node 20), `pnpm --filter` build command updated (Session 118, 2026-04-18)
- Status: deploy still blocked — rate limit exhausted (100 builds/day hit on 2026-04-18)
- Consequences: `/privacy`, `/terms`, `/sitemap.xml` routes in git main → NOT live on prod (heartbeat.md Session 120). `admin/obligations` page → 404. EventShift pages → blocked. `NEXT_PUBLIC_API_URL` points at wrong Railway service (stale `modest-happiness-production` URL, SHIPPED.md Session 120 gap #1)
- Days stalled: at minimum 1 day (since 2026-04-18), likely longer if Node 24 is root cause
- Fix owner: Atlas (needs Vercel MCP token scope, currently 403 per heartbeat.md)

### Stall 2 — Google OAuth "Testing" mode
- Flagged: CRITICAL-BUGS-2026-04-18.md line 9. Every login shows consent screen. Refresh tokens capped 7 days.
- Fix: Google Cloud Console → OAuth consent screen → Publish → requires `/privacy` and `/terms` URLs live
- Dependency chain: OAuth fix → blocked on Vercel deploy → blocked on task #53
- CEO session `last_sign_in` stuck at April 8 (verified via SQL, CRITICAL-BUGS line 14)
- Days stalled: 11+ days (since ~Apr 8 based on last_sign_in evidence)

### Stall 3 — Obligation system pipes not connected
- Migration, seed script, GH Actions secrets all written and verified (SHIPPED.md Session 119)
- NOT applied to prod yet (company-state.md: "Atlas shipped the pipes, CEO opens the valve")
- Nag-loop is silent until 4 GH secrets populated
- Latency: 1+ day since pipes were written

---

## Plane 5 — Compliance mines

**Verdict: 3 active mines. One is GDPR Art 7 (just fixed). Two remain.**

### Mine 1 — `consent_events` table: PARTIALLY FIXED (2026-04-18)
- `fix(gdpr): log consent_events on assessment start (Art 7 compliance)` — commit in last 30 (bash output)
- Before fix: 0 rows despite 43 assessments asking for consent
- After fix: assessment start now writes to `consent_events`
- **Remaining gap:** 26 other routers that touch user data still don't write to `consent_events` (FEATURE-INVENTORY line 36: "automated_decision_log only written by skills.py (1 of 27 routers)")
- `human_review_requests` table: created, no reader route in admin.py, no queue consumer (FEATURE-INVENTORY line 45)

### Mine 2 — `volunteer_*` tables in production schema
- `volunteer_badges`, `volunteer_behavior_signals`, `volunteer_embeddings` — three tables with "volunteer" in name (CRITICAL-BUGS line 53)
- Positioning constitution: NEVER use "volunteer" (CLAUDE.md)
- Migration `20260415100000_*.sql` creates generated columns on 8 tables as Phase 1 rename — "committed (not yet applied)" (SHIPPED.md Session 96 line 75)
- Risk: if a GDPR data export request arrives, the table names appear in the export and contradict the product positioning externally

### Mine 3 — PII in logs
- `loguru` is correct (no `print()` confirmed in active routers per FULL-ECOSYSTEM-AUDIT)
- BUT: `apps/api/app/services/atlas_voice.py:75` uses loguru — unverified if it logs user message content
- Telegram webhook handles user messages → verify `logger.info` calls don't capture raw message text
- **Unjudgable without reading each logger.info call in telegram_webhook.py and atlas_voice.py**

### Mine 4 — 83(b) election (legal, not GDPR)
- Deadline: **Apr 28** (9 days). DHL Baku → IRS direct. CEO goes to DHL Monday Apr 20.
- Miss = founder pays income tax on stock appreciation as it vests. At $10M valuation: 7-figure exposure.
- This is the single highest-severity compliance item in the ecosystem.

---

## Plane 6 — Ecosystem coherence

**Verdict: 5 products declared, 1 fully wired, 3 partial shells, 1 P0-broken. The event bus has 2 rows.**

### `character_events` bus — the declared integration layer
- Table: 2 rows in production (CRITICAL-BUGS line 98)
- VOLAURA writes: `apps/api/app/services/cross_product_bridge.py:262` — VOLAURA→MindShift event bridge "live" (FEATURE-INVENTORY line 26)
- MindShift reads: `supabase/functions/volaura-bridge-proxy/index.ts` — exists
- Life Sim reads: `scripts/controllers/api_client.gd` reads `crystal_balance` from VOLAURA, does NOT consume `character_events` (FEATURE-INVENTORY line 110)
- BrandedBy reads: not found
- ZEUS/Atlas reads: `packages/swarm/` uses Supabase for proposals, not `character_events`

**Honest count: 1 of 5 products writes to bus (VOLAURA). 1 of 5 reads (MindShift via bridge). 3 products (LifeSim, BrandedBy, ZEUS) neither write nor read.**

### Per-product integration state:
| Product | Auth | character_events | Real users | Blocking bug |
|---------|------|-----------------|------------|-------------|
| VOLAURA | ✅ Supabase JWT | writes | 2 real | OAuth Testing mode |
| MindShift | ✅ Supabase (separate repo) | reads via proxy | 3 users, 0 sessions | None confirmed |
| Life Simulator | ❌ JWT login in api_client.gd (parse bug) | no | 0 | VolauraAPIClient scope P0 |
| BrandedBy | ✅ router exists | no | 0 | Azure/ElevenLabs keys missing |
| ZEUS/Atlas | N/A (CTO layer) | no | N/A | Not user-facing |

The "5 products on shared Supabase auth + character_events bus" narrative in CLAUDE.md describes the intended architecture, not the current state. Shared auth: 2 of 5. Shared bus: 1 writes + 1 reads = partial mesh.

---

## Plane 7 — Focus vs dispersal

**Verdict: not ADHD fragmentation — but the sequencing is wrong. VOLAURA is the engine; the others are passengers who boarded before the engine started.**

### The 28-day context (MCKINSEY Gate 1)
1,611 commits, 109,976 LOC, 128 endpoints, 810 tests, Delaware C-Corp incorporated, $405K credits submitted — in 28 days solo+AI. This is velocity, not scattering. No credible benchmark disproves it.

### But: sequencing creates a real risk
The 5 products were built in parallel rather than sequentially. The result: VOLAURA has 2 real users and 0 returning cohort. The engine needs fuel before the passengers board.

**If runway demanded brutal prioritization:**

**Keep: VOLAURA** — the only product with end-to-end working assessment, live prod, real (if tiny) user base, clear B2B monetization path via org accounts, patent-pending IRT+BARS combination, defensible technical moat. This is the revenue engine.

**Pause: MindShift** — has its own repo, real features (focus timer, AI coach, 20 edge functions), 3 users. But 0 sessions, 0 real engagement. The cross-product bridge exists. Pause means "don't touch, let VOLAURA send it users via bridge when VOLAURA has users to send."

**Kill (if forced): Life Simulator** — P0 bug blocks main menu (VolauraAPIClient parse order, Godot 4.6.1). No live users. Crystal economy claimed but not wired. Android export planned but no APK. The value proposition ("VOLAURA skills unlock in-game bonuses") only works when VOLAURA has users with AURA scores — which requires fixing the distribution problem first. Kill does not mean delete — it means freeze and document, revisit at 100 VOLAURA users.

BrandedBy sits between pause and kill: router exists, video worker needs Azure/ElevenLabs keys, no users. Revenue potential (AI twin) is real but depends on VOLAURA trust being established first.

---

## What a CTO would do Monday morning

**Action 1 (highest urgency, time-bound): Unblock Vercel deploy — task #53**
The Vercel module_not_found is blocking: `/privacy` + `/terms` routes (needed for Google OAuth production publish), `admin/obligations` UI, EventShift pages, and the `NEXT_PUBLIC_API_URL` wrong-service bug. Every hour this stays broken, users who try OAuth get a 7-day token cap and a consent screen. Fix path: read Vercel build logs via MCP (needs CEO to grant scope or check web console), diagnose Node 24 vs pnpm workspace resolution, fix build command. Expected: 2-4 hours of work.

**Action 2 (urgency: 9 days): Confirm 83(b) DHL dispatch**
CEO goes to DHL Monday Apr 20 — this is TODAY. Postmark deadline Apr 28. Before DHL: (a) verify DHL Express Worldwide is on current IRS §7502(f) PDS list at irs.gov, (b) confirm wet-signed 83(b) form from Stripe Atlas dashboard is in hand, (c) include self-addressed stamped envelope inside package. If DHL Baku quotes unavailable or wrong service — fallback is FedEx International Priority (also §7502(f) designated). Atlas should receive the DHL waybill tracking number same day and store scan in `memory/atlas/legal/83b-election/`.

**Action 3 (this week): Close the activation loop and measure it**
43 assessments, 1 AURA score, 0 returning users — this is not a product problem, it's a measurement + invite problem. Three concrete steps: (a) write the PostHog funnel query `signup→assessment_complete→return_session` and know the exact dropout step, (b) invite 10-15 known professionals from Yusif's network with a personal message (not a form), (c) fix the multi-select UX confusion (user selects 8 competencies, gets 1 with no indicator — CRITICAL-BUGS P0 #3). The assessment engine works. The funnel just has no people in it and two UX blockers that confuse the ones who do arrive.

---

## What CEO should NOT touch

**1. The backend architecture.** 128 endpoints, 810+ tests, 0.93 test ratio, RLS on 35+ tables, IRT 3PL engine, BARS LLM evaluation, 4-layer anti-gaming. This is genuinely strong. The instinct to "simplify" or "reduce scope" here would be destructive. The moat is exactly this depth.

**2. The memory/compliance infrastructure.** `atlas_obligations` system, nag workflow, proof intake via Telegram — this is all written and correct. It just needs 4 GH secrets set to go live. CEO should set those secrets (SUPABASE_URL, SUPABASE_SERVICE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CEO_CHAT_ID) and run `python scripts/seed_atlas_obligations.py` once — then never touch it again.
