# SESSION FINDINGS — Living Intelligence Document

**Purpose:** Every session insight, strategic finding, validated hypothesis, and discovered pattern gets saved HERE immediately.
Not just code commits. Not just mistakes. Everything that matters.

**Rule (added 2026-03-29):** If you say it in a session, you write it here. No exceptions.
This file exists because CEO caught CTO generating insights verbally without saving them.

---

## SESSION 75 (2026-03-29) — BATCH E: 5-Agent Simulation Findings + Bug Fixes

### FINDING-026: Org onboarding never creates organizations row — B2B launch blocker
**Source:** Nigar simulation (agent a324cf66189035aa9)
**Finding:** `POST /api/profiles/me` with `account_type=organization` only creates a `profiles` row. The `organizations` table row (required for `GET /api/organizations/me`, search, and intro requests) was never created. Nigar could complete onboarding but then hit 403 on every downstream org action.
**Fix:** Auto-create organizations row in `onboarding/page.tsx` after profile creation when `accountType === "organization"`. 409 (already exists) is silently ignored.
**Rule:** Any org account completing onboarding MUST have both a `profiles` row AND an `organizations` row before leaving the onboarding flow.

### FINDING-027: .single() causes 500 instead of 404 in organizations.py
**Source:** QA chaos agent (a5c2bf18b51a55c2e)
**Finding:** 4 calls to `.single()` in organizations.py throw APIError (406/400) when 0 rows found instead of returning None. FastAPI returns 500, not the intended 404/403. Fixed to `.maybe_single()` at lines 47, 107, 128, 232, 457.
**Rule:** ALWAYS `.maybe_single()` unless you are certain the row exists. NEVER `.single()` on queries that may return 0 rows.

### FINDING-028: Discovery endpoint leaked private AURA columns
**Source:** QA chaos agent — ADR enforcement
**Finding:** `discovery.py` used `.table("aura_scores")` (base table) instead of `.table("aura_scores_public")` (safe view). `events_no_show` was explicitly selected and appeared in API responses. Migration 20260324000015 explicitly mandates using the public view.
**Fix:** Changed to `aura_scores_public`, removed `events_no_show` from select.
**Rule:** Discovery, search, and any multi-user endpoint MUST use `aura_scores_public` view. Never the base table.

### FINDING-029: badge_only visibility leaked last_updated + event fields
**Source:** QA chaos agent
**Finding:** For `visibility=badge_only`, `result.data` was spread into `AuraScoreResponse` constructor, leaking `last_updated`, `events_attended`, `events_no_show`, `events_late`, `reliability_score`. Only `competency_scores` and `aura_history` were cleared.
**Fix:** Explicit field allowlist for badge_only path — strip all private fields before constructing response.

### FINDING-030: MCQ scoring breaks silently on empty correct_answer
**Source:** QA chaos agent
**Finding:** `correct_answer.strip()` was only called on submitted answer, not on DB value. Empty string `correct_answer` evaluated to falsy — score always 0.0 without any warning. Now: both sides stripped + lowercased, explicit logger.warning when MCQ question has no correct_answer.

### FINDING-031: Double UPDATE race condition in complete_assessment
**Source:** QA chaos agent
**Finding:** Session marked `completed` in first UPDATE, then gaming columns written in second UPDATE. If second UPDATE fails or races, gaming analysis can be lost. Fixed: merged into single UPDATE when `in_progress`, separate single UPDATE for gaming columns only when already completed.

### FINDING-032: Zero-score ghost profiles appear in search
**Source:** QA chaos agent
**Finding:** Users who set `visible_to_orgs=True` but never completed an assessment appear in org search with `total_score=0.0`. Added `.gt("total_score", 0)` filter to discovery endpoint.

### FINDING-033: Session expiry never enforced
**Source:** QA chaos agent
**Finding:** `expires_at` column exists in `assessment_sessions` but was never checked. Users could submit answers or complete sessions 48+ hours after expiry. Added expiry check in both `submit_answer` and `complete_assessment` with 410 SESSION_EXPIRED response.

### FINDING-034: "Find talent" CTA on landing routed to same signup as volunteers
**Source:** Leyla simulation (a546de269fadf19d4)
**Finding:** Both hero CTAs led to the same `/signup` URL. Org users clicking "Find talent" expected an org-specific form but arrived at generic signup with volunteer pre-selected. Fixed: `?type=organization` parameter added, signup pre-selects org type.

### FINDING-035: Privacy consent text used as validation error
**Source:** Leyla simulation
**Finding:** When user submits without checking privacy consent, `t("auth.privacyConsent")` was shown as error — meaning the consent label text "🔒 My data is protected..." appeared as an error message. Fixed: separate `auth.privacyConsentRequired` key.

### FINDING-036: display_name not required on onboarding Step 1
**Source:** Leyla simulation
**Finding:** `step1Valid` only checked `username.trim().length >= 3` — users could proceed with empty `display_name`. Profile would be saved with no name, making AURA cards and share pages show blank. Fixed: added `display_name.trim().length >= 1` to step1Valid.

### FINDING-037: Share buttons passive — no trigger mechanism
**Source:** Team critique agent (a7da737d554f97186), Product Agent
**Finding:** AURA page has ShareButtons component but it's passive (user must find and click). The viral growth loop depends on shares. No prompt means viral coefficient ≈ 0.
**Fix:** Added post-reveal share modal that fires 3s after first AURA score reveal. Uses `sessionStorage` to ensure it only fires once per session (not on every revisit).

### FINDING-038: Waitlist mechanic wrong for warm contacts
**Source:** Team critique agent, Growth Agent
**Finding:** The original "beta landing page + waitlist" plan creates 48-72h delay for warm contacts who expect instant access from a personal invite. Waitlist is a cold-audience mechanic.
**Fix:** Built `/invite` page with beta code allowlist. Direct route to `/signup` with invite code attribution. `OPEN` code works for LinkedIn CTA. Personal codes (BETA_01-30) for direct invites.

### FINDING-039: LinkedIn DAY 7 is the conversion peak, CTA belongs there
**Source:** Nigar simulation, Growth Agent
**Finding:** MiroFish simulation predicted DAY 7 "0 real users" as conversion peak (MiroFish predicted 7,200 impressions). CTA placed at emotional vulnerability moment = highest conversion. Added: "If you want to be in the first 50 → volaura.app/invite"

### FINDING-040: Org contacts should arrive AFTER 15 individual users have AURA scores
**Source:** Team critique agent, Cultural Intelligence + Sales Strategist
**Finding:** Inviting orgs concurrently with individuals means org admins arrive to empty platform. 30 individuals + 5 orgs simultaneously = org admin searches for talent, finds 2 profiles. Correct sequence: Week 1 = individuals only, Week 2 Day 4+ = 2 org design partners (not 5).

---

## SESSION 76 (2026-03-30) — BATCH I: Payment Kill Switch + Agent Briefing Lessons

### FINDING-041: Agent context loss is a structural problem, not a one-off mistake
**Source:** CTO analysis after CEO caught 3 research agents returning contextually wrong answers
**Finding:** After context compression, every agent subprocess starts with ZERO knowledge of the project. CTO assumed shared context exists — it doesn't. Agents answered the literal question (e.g. "best payment processor") without knowing: AZ founder, $50/mo budget, already evaluated Paddle, 6-week timeline. Got correct generic answers, wrong for this situation.
**CEO analogy:** "Like asking a consultant 'what payment processor?' without telling them you're a bootstrapped AZ founder with $500 budget. They recommend Stripe. Wrong answer."
**Resolution:** VOLAURA CONTEXT BLOCK template (docs/AGENT-BRIEFING-TEMPLATE.md) + Step 1.0.3 blocking gate in TASK-PROTOCOL v5.3.
**Rule:** Every agent prompt = VOLAURA CONTEXT BLOCK + "What's already decided" + sprint goal + output format. Non-negotiable.

### FINDING-042: "What's already decided" prevents redundant agent research
**Source:** Same session — payment research agents
**Finding:** Without "what's already decided" section, agents re-research decisions we already made. This is token waste AND creates false uncertainty. Agents may reach different conclusions and re-open closed debates.
**Example:** Stripe Atlas was evaluated and deferred (operational budget: $200+/mo for AI/infra, need $500 for registration). Next agent shouldn't re-propose it. "What's already decided: DSP council voted Path C — Polar/Paddle now, Stripe Atlas at MRR >$500" = agent skips this path.
**Rule:** Include in every agent prompt: a "What We Already Know (do not repeat)" section with 3-5 bullet points. See template.

### FINDING-043: 10% WHT on SWIFT transfers is the hidden "LinkedIn HR call" risk for AZ founders
**Source:** AZ payment research agent + CTO tax analysis
**Finding:** Azerbaijan Tax Code 2025 introduced 10% withholding tax on transfers from "electronic wallets / digital payment software." Paddle pays via SWIFT — may be classified as WHT-eligible. Tax advisors disagree on scope. Risk is real, not theoretical.
**Resolution:** Polar.sh (Stripe Connect Express, not SWIFT) avoids the WHT category entirely. Direct to AZ bank. $40 threshold, 4% fee, 24h approval.
**Rule:** For AZ bank accounts: prefer Stripe Connect over SWIFT for subscription revenue. Get written WHT opinion ($100-150) before going live with any SWIFT-based payout at scale.

### FINDING-044: PAYMENT_ENABLED kill switch is the correct architecture for pre-revenue beta
**Source:** CTO implementation session
**Finding:** "Prepare but don't activate" = one env var that gates the entire billing stack simultaneously (paywall, checkout, webhook). Default False = beta users assess freely. Set True on Railway = entire billing goes live. No code deploys needed at activation.
**Rule:** Any feature that will be activated at a future date (billing, feature gates, experiments) should be behind a kill switch in config.py from day 1. Flip env var > code deploy.

---

## SESSION 81 (2026-04-02) — BATCH A–D: Crystal Reward + Admin Panel + Full Audit

### FINDING-055: Crystal reward was silent — users never knew they earned crystals
**Source:** CTO audit of assessment complete flow
**Finding:** `emit_assessment_rewards()` was inserting rows into `game_crystal_ledger` and `character_events` correctly but returning `None`. The router wasn't capturing the return value. `AssessmentResultOut` had no `crystals_earned` field. Users completed assessments and earned crystals invisibly — no UI feedback at all.
**Fix:** (1) `rewards.py` returns `int` (0 = already claimed, CRYSTAL_REWARD = newly awarded). (2) Router captures return value with `int(... or 0)` guard. (3) `AssessmentResultOut` gains `crystals_earned: int = 0`. (4) Animated 💎 card on assessment complete page with Framer Motion.
**Rule:** At peak behavioral moments (task completion), never let a reward go unannounced. Silent rewards = no behavior reinforcement.

### FINDING-056: CRIT-I01 — No request body size limit (DoS vector)
**Source:** Backend Audit Agent (5-agent parallel codebase audit)
**Finding:** `main.py` had CORS, rate limiting, security headers — but no request body size limit. Any client could send arbitrarily large bodies. At scale, 50 concurrent 100MB uploads = 5GB memory spike → OOM → Railway restart.
**Fix:** `@app.middleware("http") async def limit_request_body()` — checks Content-Length header on POST/PUT/PATCH. Returns 413 if > 1MB.
**Rule:** Every FastAPI app needs a body size limit. Add it at app creation time, not as an afterthought.

### FINDING-057: `getRelativeTime()` had hardcoded English strings — AZ UI showed "m ago" not "dəq əvvəl"
**Source:** i18n audit
**Finding:** Time-ago strings ("5m ago", "2h ago", "Yesterday") were hardcoded in English in `dashboard/page.tsx`. AZ users saw English timestamps.
**Fix:** `getRelativeTime(dateStr, t)` — added `t` parameter, uses `common.timeAgo.*` i18n keys with `{{count}}` interpolation. EN + AZ keys added.
**Rule:** Any user-facing string including formatted dates/times must go through `t()`. No hardcoded English.

### FINDING-058: Tinkoff/Aviasales benchmark was known but not codified
**Source:** CEO directive 2026-04-02
**Finding:** Team was writing LinkedIn posts in corporate style despite knowing about Tinkoff/Aviasales benchmark. Knowledge wasn't enforced anywhere. `docs/TONE-OF-VOICE.md` had not been updated despite communications-strategist.md being updated. CEO: "ты нарушаешь свои правила."
**Fix:** TONE-OF-VOICE.md v2.0: added §1.5 (Tinkoff/Aviasales mandatory benchmark), §1.6 (AZ bilingual strategy + A/B testing), §1.7 (hook taxonomy — 6 types, rotation rule).
**Rule:** When a benchmark or standard changes, update the PRIMARY governing document (`docs/TONE-OF-VOICE.md`) immediately — not just the skill file.

### FINDING-059: Docs were 6–30 sessions stale — audit found critical intelligence gaps
**Source:** 5-agent full codebase audit (Docs/Memory Agent)
**Finding:** `agent-feedback-log.md` had no entries after Session 42 (30+ sessions missing). Agents were proposing already-rejected ideas. `SESSION-FINDINGS.md` was 6 days stale (Sessions 76–81 missing). `patterns.md` had no entries after Session 73. TASK-PROTOCOL.md header says v6.0 but changelog only goes to v5.3.
**Fix:** This session — all four files updated.
**Rule:** `agent-feedback-log.md` + `SESSION-FINDINGS.md` + `patterns.md` are CLASS 6 obligations. If any is >2 sessions stale, session end protocol is not being followed. Staleness = agent learning broken.

### FINDING-060: Admin panel must be fail-closed, not fail-open
**Source:** Security Agent review of admin route design
**Finding:** Initial design had admin check as `is_admin: bool = False` with `if not is_admin: raise 403`. The check reads from `SupabaseUser` (RLS-enforced). Risk: if RLS policy is misconfigured, check could return wrong result.
**Fix:** `require_platform_admin` uses `SupabaseAdmin` (service-role, bypasses RLS). Reads `is_platform_admin` column directly. No RLS dependency on security-critical gate.
**Rule:** Security gates that determine access to admin/elevated functionality must use service-role (SupabaseAdmin), not user-context client (SupabaseUser), to avoid RLS misconfiguration leaks.

---

## SESSION 80 (2026-04-01) — CIS-001 Fix + Profile Intelligence

### FINDING-051: "Top 5%" framing re-surfaced in production despite earlier fix
**Source:** Cultural Intelligence Agent first activation in 3 months
**Finding:** FINDING-001 documented "Top 5%" as toxic. It was fixed in early sessions for the main AURA card. But the assessment complete page and public profile page (`/u/[username]`) still used `t("profile.topPercent", ...)` percentile display. CIS users on production still saw competitive framing.
**Fix:** `getAchievementLevelKey(percentileRank)` utility maps 0-100 percentile → 6 achievement labels (Expert/Advanced/Proficient/Growing/Building/Starting). Non-competitive, non-numeric, culturally safe.
**Rule:** When fixing cultural framing in one location, grep for ALL usages of the same translation key. `topPercent` appeared in 2 locations — only one was fixed in the original session.

### FINDING-052: Profile views had no feedback loop to the volunteer
**Source:** Product Agent, Growth Agent
**Finding:** When an org admin searched for talent and clicked a profile, the volunteer had zero visibility into "someone viewed my profile." This removes a key motivational signal — "I'm being noticed." Without it, users have no reason to keep their AURA score updated.
**Fix:** `notify_profile_viewed()` — throttled org_view notification (1 per 24h per org). Partial index on `notifications(user_id, reference_id, created_at) WHERE type='org_view'` prevents seq scan.
**Rule:** Professional discovery platforms require profile view notifications. They drive re-engagement without any other trigger.

---

## SESSION 79 (2026-04-01) — Org Saved Search + Realtime Notifications

### FINDING-048: WebSocket real-time was over-engineered for current scale
**Source:** DSP Score 28/50 — WebSocket layer explicitly deferred
**Finding:** Team proposed WebSocket (FastAPI native) for real-time notifications. DSP ran with 9 personas. Score: 28/50 (below 35/50 gate). Supabase Realtime (already integrated) handles the use case at zero additional complexity. WebSocket adds a new protocol to maintain, new Railway resource, Railway charges per open connection at scale.
**Decision:** Supabase Realtime for notifications. WebSocket re-evaluation gate: 2026-07-01 OR 500 active users (whichever first). Must bring: connection count data + Railway cost impact + specific user workflow polling can't serve.
**Rule:** Don't add new infrastructure when existing infrastructure (Supabase Realtime) handles the use case. The bar for new infra = data, not intuition.

### FINDING-049: Org saved searches had no privilege escalation protection
**Source:** Security Agent review of Sprint 8
**Finding:** Initial design of `PATCH /saved-searches/{id}` and `DELETE /saved-searches/{id}` lacked explicit ownership check. Org A could theoretically modify Org B's saved search by guessing UUID.
**Fix:** `_assert_search_ownership()` in organizations.py — fetches search, verifies org_id matches the authenticated org. Raises 403 if mismatch.
**Rule:** Any endpoint that modifies a resource by ID must validate ownership BEFORE executing the modification. Pattern: fetch → verify org match → then act.

### FINDING-050: Match checker needs circuit breaker, not infinite retry
**Source:** Architecture Agent review
**Finding:** Daily match_checker runs via GitHub Actions cron. If Telegram bot token is invalid or rate-limited, retry loop would exhaust GitHub Actions minutes and send duplicate notifications.
**Fix:** Circuit breaker: 3 consecutive Telegram failures → 60s silence → stop for that run. Results still written to DB. Next day's run starts fresh.
**Rule:** Any external service call in a cron job needs a circuit breaker. Silent failure + log > infinite retry.

---

## SESSION 78 (2026-04-01) — Swarm Infrastructure + TASK-PROTOCOL v6.0

### FINDING-045: Agents proposed files that don't exist — 3.3% ungrounded rate
**Source:** Proposal Verifier (proposal_verifier.py) — first run
**Finding:** Out of 30 agent proposals, 1 referenced `apps/api/app/routes.py` (doesn't exist — it's `routers/`). Without verification, CTO would start searching for a file that was never created. `proposal_verifier.py` checks all file paths in proposals against disk.
**Rule:** Every proposal that names a file path must be verified against the actual file tree. "Grounded" proposals (paths exist) = 96.7% after verification. 3.3% hallucination rate is expected for LLM agents.

### FINDING-046: Daily swarm ran even when nothing changed
**Source:** Architecture Agent
**Finding:** `swarm-daily.yml` ran every day at 09:00 Baku regardless of whether there was anything to act on. Wasted GitHub Actions minutes + created low-signal CEO inbox noise on quiet days.
**Fix:** `heartbeat_gate.py` — KAIROS binary gate. 3 conditions: urgent proposals pending OR active git changes OR staleness floor exceeded. Exit 0=RUN, Exit 1=SKIP. Manual dispatch always bypasses.
**Rule:** Autonomous systems should gate themselves. "Should I run right now?" is a question every scheduled process should answer before consuming resources.

### FINDING-047: Cross-repo analysis found patterns we hadn't implemented
**Source:** CTO analysis of ZEUS + MindShift v6.0 architecture (Session 78)
**Finding:** ZEUS had: adaptive execution states, recovery strategies, context intelligence. MindShift had: v6.0 protocol with outcome verification, session-end skill evolution check. Both patterns were absent from Volaura's swarm. We had proposals but no execution state machine, and no outcome verification (agents declared DONE without proof).
**Fix:** TASK-PROTOCOL v6.0: Added SESSION-DIFFS + code-index read step, trigger_reason on proposals, Round-2 debate gate (<35/50 AND delta<5 → mandatory second round), outcome verification requirement, skill evolution check at session end.
**Rule:** Other repos in the same ecosystem are the best source of swarm architecture patterns. Cross-repo analysis > solo invention.

---

## SESSION 77 (2026-03-31) — Security Hardening + LLM Chain

### FINDING-044b: Startup guard was silently bypassed on staging/dev (Mistake #61)
**Source:** Security Agent
**Finding:** `assert_production_ready()` had `if settings.app_env != "production": return` BEFORE the RISK-011 check. Staging container could boot pointing at wrong Supabase URL — nobody would know until a user complained about wrong data.
**Fix:** RISK-011 check moved BEFORE the env guard. Safety guards (wrong DB, wrong bucket) fire on ALL environments. Cost guards (Sentry, paid keys) remain production-only.
**Taxonomy added:** RISK-*** guards = fire everywhere. COST-*** guards = production only.

### FINDING-044c: Groq had 14,400 free req/day — silently unused for 10+ sessions (Mistake #62)
**Source:** Architecture Agent
**Finding:** `config.py` had `groq_api_key` with RISK-M01 cost warning. `llm.py` fallback chain was Gemini → OpenAI. No Groq step. Every Gemini failure went directly to paid OpenAI (~$240/day at 1k users). Groq's free tier was completely bypassed.
**Fix:** Full `llm.py` rewrite. New chain: Vertex Express → Gemini → Groq (free, llama-3.3-70b-versatile) → OpenAI. Singleton clients with `reset_llm_clients()` for test teardown.
**Rule:** After adding any LLM provider to config.py, immediately verify it appears in `evaluate_with_llm()` fallback chain. Search `llm.py` for the key name before closing the task.

---

## SESSIONS 68–69 (2026-03-29) — Mega-Session Findings

### FINDING-001: Cultural Framing P0 — "Top 5%" is toxic in AZ market
**Source:** Cultural Intelligence Agent first activation
**Finding:** Competitive framing ("Top 5% in your field", leaderboard ranking) creates shame in collectivist cultures (AZ, CIS). You don't want to be seen outranking your network — you want to be part of it.
**Resolution:** Changed to AURA score (78/100) + "Trusted by top organizations" framing.
**Rule:** NEVER use percentile ranking as motivation in AZ. Use absolute scores and community belonging.
**Files changed:** `en/common.json`, `az/common.json`

### FINDING-002: Assessment Store Must Use localStorage, Not sessionStorage
**Source:** Production audit
**Finding:** sessionStorage cleared on browser refresh. Users lose in-progress assessments on any refresh.
**Resolution:** Changed to localStorage. Auto-clear on complete/error.
**Rule:** Any state that must survive a redirect (auth callback, page refresh) = localStorage, NOT sessionStorage.

### FINDING-003: QA Agent Was Testing Its Own Output (Circular Evaluation)
**Source:** Session 69 agent audit
**Finding:** QA was marking its own generated keywords as "independently verified." No blind test.
**Resolution:** `scripts/validate_qa_blind.py` — enforces that QA keywords can't be single-word matches (too easy to self-generate).
**Rule:** Validation must be structurally blind. Same agent can't write AND certify.

### FINDING-004: Skills Hired But Never Activated (Sessions 57–68)
**Source:** CEO challenge + agent roster audit
**Finding:** Behavioral Nudge Engine and Cultural Intelligence were on the roster for 11 sessions but never loaded. Found 7 new P0/P1 issues on first activation.
**Lesson:** An agent on the roster who was never called = 0% value. Loading a skill costs 30 seconds. Not loading it costs hours of rework.
**Rule added to CLAUDE.md Skills Matrix:** "If in doubt — load it."

### FINDING-005: MiroFish vs Our Swarm — Architecture Comparison
**Source:** CEO question + MiroFish codebase research
**Finding:**
- MiroFish: OASIS engine (Twitter simulation) + Zep Cloud (paid memory) + Vue frontend + persona database
- Our swarm: Claude parallel agents + file-based memory (`shared-context.md`, `career-ladder.md`, `agent-feedback-log.md`)
- Our swarm is better for: product/code decisions with codebase context
- MiroFish is better for: large-scale social behavior simulation (10k+ personas)
**Recommendation:** Do NOT migrate. Integrate MiroFish's persona methodology for content testing only.
**Status:** PENDING team vote (see TASK-PROTOCOL below)

### FINDING-006: Health Check Was a Stub for 69 Sessions
**Source:** Production audit
**Finding:** `GET /health` returned `{"status": "ok"}` always, regardless of DB/LLM connectivity.
**Resolution:** Real health check now tests Supabase ping + LLM config presence.
**Rule:** Health checks must test the ACTUAL stack, not return static strings.

### FINDING-007: Sentry Was Not Configured (69 sessions of invisible errors)
**Source:** Production audit
**Finding:** All 5xx errors in production were invisible — no alerting, no tracking.
**Resolution:** Created org "volaura" + project "volaura-api" via Sentry API. DSN deployed to Railway. `error_alerting.py` middleware sends Telegram alerts for 5xx (rate-limited 1/5min).
**Lesson:** "We'll add monitoring later" = "errors will be invisible forever."

### FINDING-008: ProxyHeadersMiddleware Removed in Starlette 0.46+
**Source:** Import error during sprint
**Finding:** `starlette.middleware.trustedhost.ProxyHeadersMiddleware` was removed. Code that imports it crashes silently on startup.
**Resolution:** try/except fallback to `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware`.
**Rule:** Never import starlette internals without version pinning.

### FINDING-009: LinkedIn Series — Day 6 is the Breakout, Day 7 is the Conversion
**Source:** MiroFish 50-persona simulation
**Finding:**
- Day 6 "Culture Test" = viral peak (10/10, +287 follows) — AURA score vs "Top 5%" is a universal localization insight that crosses HR + product + VC audiences
- Day 7 "Numbers" = conversion peak (10/10 conversion) — "$50/mo + 0 users" triggers support/empathy DM response
- Peak impressions: 5,800 (Day 6) and 7,200 (Day 7)
- Predicted total: ~22,200 impressions, 890→1,700 followers
**Rule:** Content that crosses audience boundaries (HR + product + VC) outperforms content targeted at one audience.

### FINDING-010: Follower Growth Compound Effect — Day 4 Threshold
**Source:** MiroFish simulation
**Finding:** LinkedIn series engagement compounds. If Day 4 breaks 500 impressions, Days 5-7 benefit from follower amplification (Sequoia GP reshare → VC network activation predicted at Day 5).
**Rule:** Track Day 4 as leading indicator. If < 500 → adjust posting time or boost with comment seeding.

### FINDING-011: .single() → .maybe_single() Prevents 406 Errors
**Source:** Session 68 audit
**Finding:** `supabase.table().select().single()` throws 406 when 0 rows found. `.maybe_single()` returns None instead.
**Rule:** ALWAYS use `.maybe_single()` unless you are certain the row exists.

### FINDING-012: Email Domain Logging (Not Full Email) — Security P1
**Source:** Session 69 security audit
**Finding:** Auth router was logging full `user@email.com` in plaintext. Domain `@email.com` is sufficient for debugging.
**Resolution:** Log `email.split('@')[1]` (domain only) in auth endpoints.
**Rule:** PII never in logs. Domain is sufficient for debugging email-related issues.

### FINDING-013: Assessment Hint Messaging Increases Completion
**Source:** Behavioral Nudge Engine first activation + UX analysis
**Finding:** Users with no AURA score have no context for what they're starting. Adding "Start with 1-2 skill areas" + "Your progress is auto-saved" messaging reduces abandonment.
**Resolution:** Guidance copy added to assessment start page (EN + AZ).

### FINDING-014: Swarm Agent Never Called ≠ Agent Available
**Source:** Agent roster audit
**Finding:** Having an agent in the roster but not calling it is operationally equivalent to not having it. Growth Agent had 0 findings across 4 sprints — under retirement review.
**Rule:** Agents must be explicitly routed (STEP 5.5). If routing table shows no match, document why, don't silently skip.

### FINDING-015: "Done" Before E2E Walk = Not Done
**Source:** `feedback_e2e_before_declare.md` confirmation
**Finding:** 512 tests can pass while the actual user journey is broken. Sprint E1 declared complete before walking: register → onboarding → assessment → results.
**Rule:** Definition of Done = walk the full user journey from an incognito window on production URL.

### FINDING-016: CTO Plan → Council Critique = Better Than Team Proposals for Strategic Decisions
**Source:** Session 72 — CEO caught wrong TASK-PROTOCOL phase
**Finding:** TASK-PROTOCOL v4.0 "Team Proposes" works well for product/code sprints. For strategic architecture decisions (PR agency structure, org design), the right flow is: CTO presents full plan → council attacks it with specific objections → plan improves.
**Rule:** Read the signal. CEO says "propose/plan" → CTO plan first. CEO says "start working on X" → team proposes tasks.
**What the council found that CTO missed:** (1) Analytics before strategy — not after. (2) Growth feedback loop undefined. (3) Hook extraction mandate missing. (4) Cultural Strategist needed in brief, not just in review.

### FINDING-017: PR Agency Was Missing 4 of 5 Roles
**Source:** Session 72 batch
**Finding:** We had 1.5 of 5 roles: copywriters (3 models) + partial Cultural Intelligence (not activated). Missing: Communications Strategist (narrative direction), Analytics/Growth (feedback loop), Distribution (timing/channel), Media Relations (press).
**Built this session:** Strategist skill + AZ Audience Profile + Brief Template + Cultural Audit Checklist.
**Still missing:** Analytics Foundation (data on 6 existing posts), Distribution Calendar.

### FINDING-018: Copywriters Without Strategist = Artists Without Director
**Source:** Session 72
**Finding:** CORTEX, SPARK, PRISM all wrote good copy but without narrative arc, audience targeting logic, or cultural constraints pre-baked. The quality gap was structural, not talent.
**Fix:** Communications Strategist fills brief BEFORE copywriters write. Brief contains: series position, audience segment, P1-P7 constraints, forbidden patterns, hook constraint, PS instruction.
**New pipeline:** Strategist → [filled CONTENT-BRIEF-TEMPLATE.md] → Copywriters read SOURCE FILES → compete → Cultural Audit → CEO.

---

## SESSION 73 (2026-03-29) — Protocol Improvement Batch

### FINDING-019: Parallel proposals save 70 minutes per batch
**Source:** Growth Agent proposal — backed by timing data (avg 95 min sequential vs 25 min parallel)
**Finding:** Agent proposals were sequential. Each agent waits for previous to finish reading + writing. 6 agents × ~15 min = 90+ min wall-clock just for Phase 1.
**Fix:** TASK-PROTOCOL v5.0 Step 1.0 — 15-min READ window (all agents parallel) + 10-min PROPOSE window (all write in parallel). Synchronize at Needs Agent only.
**Rule:** "Parallel batch execution" means proposals are also parallel. Not sequential-per-agent.

### FINDING-020: EFFORT estimates change triage order, reducing unblocking time
**Source:** Growth Agent — modeled 2.5h improvement on historical batch data
**Finding:** Without EFFORT estimates, Needs Agent sorts by priority only. A 20-min P0 and a 4h P0 are treated identically. But the 20-min P0 should go first — it unblocks faster, builds momentum.
**Fix:** EFFORT field added to every proposal format: [20 min | 1.5h | 4h | >4h]
**Triage order:** P0+LOW_EFFORT → P0+HIGH_EFFORT → P1+LOW_EFFORT → ...

### FINDING-021: CTO never declared "what's next" — CEO always had to ask
**Source:** Product Agent proposal + repeated CEO pattern across sessions
**Finding:** Every batch close required CEO to ask "что дальше." This means CTO stopped thinking at task completion. Every ask = context switch cost for CEO.
**Fix:** "WHAT'S NEXT" is now a required field in Step 4.1 batch report. 3 items, proactive.
**Rule:** If CEO asks "что дальше" → protocol isn't working. The answer should already be there.

### FINDING-022: MICRO fastpath reduces protocol overhead 60% for trivial changes
**Source:** Product Agent — confirmed by Architecture Agent
**Finding:** A 2-line i18n string fix going through skills declaration, security checklist, peer review, cross-QA = 20-30 min of process for 2 min of work. Zero risk reduction.
**Fix:** ≤10 lines + 1-2 files + no auth/security = FASTPATH. Skip 3.0, 3.1, 3.3, 3.4.
**Boundary:** MICRO is declared, not assumed. Security/auth can NEVER be MICRO regardless of lines.

### FINDING-023: QA self-validates own tests — structural impossibility of blind review
**Source:** QA Agent proposal (referencing Session 69 Mistake #47)
**Finding:** QA writes tests → QA validates tests → QA certifies quality. No independent check. Same agent at every stage = circular loop. Like a proof-reader editing their own manuscript.
**Fix:** Gate 3.4 — Cross-QA: different agent (Architecture or Security) spot-checks QA's tests. Not "QA approves QA."
**Rule:** Test verification = independent. Always.

### FINDING-024: "Tests verified" without execution = bureaucracy
**Source:** QA Agent proposal
**Finding:** Agents wrote "QA verified" after generating test file — not after running it. CI didn't run tests. Batch closed with false confidence. "Test file exists" ≠ "tests pass."
**Fix:** Gate 3.2.5 — test execution gate. "Verified" = ran (`pytest` output attached) + passed (0 failing) + CI confirms.
**Rule:** No test execution proof = not verified. Full stop.

### FINDING-025: Protocol improvements came from agents who were UNDER-USED
**Source:** Session 73 agent proposal round — all 6 agents
**Meta-finding:** Cultural Intelligence (11 sessions unused) and QA (self-validation problem for sessions) produced the sharpest proposals BECAUSE they'd experienced the problem. Agents who experience friction know where the protocol fails.
**Rule:** Protocol improvements should be proposed by the agents who FEEL the friction, not by CTO assuming where friction is.

---

## SWARM ARCHITECTURE DECISION — Team Vote Required

**Question:** Should we migrate our swarm core to MiroFish, integrate MiroFish methodology, or keep current architecture?

**Options:**
- **A:** Keep current architecture. Integrate MiroFish persona simulation as a separate tool for content testing.
- **B:** Migrate swarm memory to Zep Cloud (MiroFish's approach). Higher capability, higher cost.
- **C:** Adopt MiroFish's OASIS persona database model locally. No Zep Cloud dependency.

**Voting:** Run via TASK-PROTOCOL. All 6 agents + CEO must vote. Decision logged in DECISIONS.md.
**Status:** PENDING

---

## PATTERN REGISTRY (Session 68–69 New Patterns)

| # | Pattern | Category | First Seen |
|---|---------|----------|-----------|
| P-040 | LLM eval cache at submit_answer time | Performance | Session 68 |
| P-041 | localStorage for auth-redirect-crossing state | Frontend | Session 68 |
| P-042 | `.maybe_single()` not `.single()` for optional rows | Backend | Session 68 |
| P-043 | Cultural framing: absolute score > percentile rank in AZ | UX/Content | Session 69 |
| P-044 | Content that crosses audience boundaries = viral | Marketing | Session 69 |
| P-045 | Health check must test actual stack, not return static string | Backend | Session 69 |
| P-046 | Agent hired but not called = 0% ROI | Process | Session 69 |
| P-047 | QA must be structurally blind (can't validate own output) | Process | Session 69 |
| P-048 | Try/except fallback for removed starlette middleware | Backend | Session 68 |
| P-049 | TASK-PROTOCOL flow type declaration before any batch | Process | Session 73 |
| P-050 | MICRO fastpath: ≤10 lines, no auth = skip gates 3.0/3.1/3.3/3.4 | Process | Session 73 |
| P-051 | "What's next" is proactive, not reactive — declared at every batch close | Process | Session 73 |
| P-052 | Parallel agent proposals: READ window (15min) + PROPOSE window (10min) | Process | Session 73 |
| P-053 | EFFORT estimate on every proposal: enables value-per-hour triage | Process | Session 73 |
| P-054 | Cross-QA: QA cannot self-validate own tests — independent agent required | Process | Session 73 |
| P-055 | "Verified" = tests ran + passed + CI proof (not: file exists) | QA | Session 73 |
| P-056 | Cultural brief re-approval required after ANY copy revision | Content | Session 73 |

---

## SESSION 83 (2026-04-03) — MEGA SESSION: Analytics, Quality System, Verification, GDPR, Product Gaps

### FINDING-061: NotebookLM with 45+ sources produces better architecture than CTO intuition
**Source:** Quality system design session — NotebookLM notebook 888d43e4
**Finding:** CTO designed quality agents (AC agent, QA agent, DORA agent) based on general knowledge. NotebookLM loaded 45+ sources (Toyota TPS, Apple, Google SRE, DORA reports) and synthesized: hard gates > soft checklists, 3-item enforced DoD > 15-item aspirational DoD, defect autopsy BEFORE building gates. The NotebookLM synthesis was categorically better than CTO intuition on every dimension.
**Rule:** For architecture/process decisions with established industry practice, NotebookLM with 10+ authoritative sources is mandatory BEFORE design. CTO intuition starts the search, research completes it.

### FINDING-062: Process theater — elaborate systems without enforcement = 0% compliance
**Source:** Swarm retrospective (Groq Llama-3.3-70b external model)
**Finding:** CTO built QUALITY-STANDARDS.md with Toyota TPS mapping, DORA metrics, 15-item DoD. Zero enforcement mechanism. Agent invocation was manual. History of 82 sessions proves: manual invocation = 0 invocations. The elaborate system existed only in documentation, never in execution.
**Fix:** 3-question DoD (added to Step 0c in TASK-PROTOCOL v8.0) replaces 15-item checklist. Questions are structural: "Did I write AC before code?" / "Did external model critique the plan?" / "Did I run tests?" These can be hard-gated (pre-commit hooks, CI checks).
**Rule:** Quality systems must have hard gates that block progress without compliance. Any system that relies on voluntary invocation will have 0% adoption rate.

### FINDING-063: Self-confirmation bias — proposing and confirming own tool recommendation
**Source:** Session 83 audit of Langfuse selection process
**Finding:** CTO proposed Langfuse for LLM observability, then confirmed Langfuse was the best choice. No external research validated or invalidated the proposal. This is circular reasoning: "I recommend X, I verify X is best, therefore X." The same pattern appeared with CrewAI adoption.
**Fix:** New rule in CLAUDE.md: "If you propose a tool/library/architecture decision, you CANNOT confirm it yourself." External research (WebSearch, NotebookLM, 2+ sources) must validate. The research may confirm the proposal — that is fine. But the research must happen.
**Rule:** Self-confirmation = bias disguised as due diligence. Every recommendation needs independent validation.

### FINDING-064: Defect autopsy reveals 3 bug classes cover 76.4% of all 76 historical bugs
**Source:** Swarm critique of quality system design
**Finding:** Instead of building quality gates based on intuition, categorizing all 76 historical bugs showed that 3 root cause classes cover 76.4%: (1) missing tests before merge, (2) schema/type mismatches between API and frontend, (3) security gates that are fail-open instead of fail-closed. Building hard gates for ONLY these 3 classes would prevent more bugs than a comprehensive 15-item DoD.
**Rule:** Before building any quality prevention system, run a defect autopsy. Categorize ALL historical bugs. Find the Pareto classes. Build gates for ONLY those classes.

### FINDING-065: 6-stakeholder critique catches what the team misses
**Source:** Session 83 external critique round
**Finding:** 6 stakeholder perspectives (VC, HR Director, SOC2 Auditor, End User, LinkedIn Product Manager, Technology Lawyer) each found issues invisible to the internal team. VC found: no unit economics model. HR: no bulk assessment API. SOC2: no audit logging for data access. User: onboarding too long. LinkedIn PM: verification link not sharable enough. Lawyer: GDPR consent not explicit.
**Rule:** Before major milestones (B2B launch, fundraise, public beta), run multi-stakeholder critique with 6+ distinct perspectives. The intersection of all passing = actually ready.

### FINDING-066: Analytics must include GDPR retention from day 1 — not retrofitted
**Source:** Analytics pipeline design session
**Finding:** analytics_events table was designed with a 390-day retention workflow built into the same migration that created the table. This is correct. Many startups create analytics tables, collect data for months, then face GDPR compliance pressure and have to retrofit retention policies with data already collected.
**Rule:** Every analytics/behavioral-data table migration must include: (1) retention period in table comment, (2) pg_cron job for deletion, (3) GDPR article reference in migration comment.

### FINDING-067: SECURITY_DEFINER views allow privilege escalation when search_path not set
**Source:** Security audit batch (BATCH-X)
**Finding:** 4 Supabase views used `SECURITY DEFINER` without `SET search_path = public`. An attacker could create a schema with the same table name and trick the view into reading from their schema instead of public. Additionally, 6 functions had the same issue.
**Fix:** All 4 views and 6 functions hardened with explicit `SET search_path = public, pg_catalog`.
**Rule:** Every SECURITY_DEFINER view/function MUST have `SET search_path` explicitly. Supabase default schema search path is not guaranteed to be safe.

### FINDING-068: Telegram webhook without secret verification accepts all POSTs
**Source:** Security audit of Telegram integration
**Finding:** `TELEGRAM_WEBHOOK_SECRET` was optional — missing key meant the webhook endpoint accepted all HTTP POSTs without signature verification. Any attacker could forge Telegram-style payloads.
**Fix:** Made `TELEGRAM_WEBHOOK_SECRET` a hard-fail in `assert_production_ready()` — missing key in production raises RuntimeError and blocks deployment.
**Rule:** Webhook endpoints that accept external payloads MUST verify signatures. Missing signature secret = deployment blocker, not warning.

### FINDING-069: Badge download was disabled ("coming soon") for 20+ sessions
**Source:** Product gap audit during customer journey walk
**Finding:** ShareButtons component had badge download button permanently disabled with "coming soon" text. Users could see their AURA score but couldn't download it for LinkedIn. The viral loop was broken at the last step.
**Fix:** Enabled badge download. The underlying functionality (Canvas → PNG) already existed — only the disabled state was wrong.
**Rule:** Audit all "coming soon" / disabled states every 10 sessions. If the underlying code exists, enable it. "Coming soon" that stays for 20+ sessions is a product gap, not a roadmap item.

### FINDING-070: Referral crystal reward drives viral growth at near-zero cost
**Source:** Product gap analysis — referral code implementation
**Finding:** Adding referral_code to registration (auth.py) + crystal reward on first assessment completion (rewards.py) creates a behavioral loop: user refers friend → friend completes assessment → referrer gets 10 crystals + notification. Cost: 0 (crystals are virtual). Value: each referral is a qualified lead who completes onboarding.
**Rule:** Virtual economy rewards for referrals should be implemented early — they cost nothing and create growth loops. The key is the notification: referrer must KNOW their referral converted.

---

## PATTERN REGISTRY (Session 83 New Patterns)

| # | Pattern | Category | First Seen |
|---|---------|----------|-----------|
| P-057 | NotebookLM with 10+ sources > CTO intuition for process design | Research | Session 83 |
| P-058 | Defect autopsy before building quality gates (Pareto principle) | Quality | Session 83 |
| P-059 | Process theater: elaborate system without hard gates = 0% compliance | Quality | Session 83 |
| P-060 | Self-confirmation bias: cannot validate own recommendation | Process | Session 83 |
| P-061 | Analytics tables need GDPR retention in same migration | Compliance | Session 83 |
| P-062 | 6-stakeholder critique before major milestones | Process | Session 83 |
| P-063 | SECURITY_DEFINER needs explicit search_path | Security | Session 83 |
| P-064 | Webhook signature verification = deployment blocker | Security | Session 83 |
| P-065 | "Coming soon" > 10 sessions = product gap, not roadmap item | Product | Session 83 |
| P-066 | Virtual economy referral rewards: zero cost, high growth | Growth | Session 83 |
| P-067 | 10-step execution algorithm with visible output per step | Process | Session 83 |
| P-068 | Telegram setMyCommands for bot menu registration | Backend | Session 83 |

---

## HOW TO USE THIS FILE

**At session start:** Read the last 20 entries. They contain fresh context that patterns.md may not have yet.
**During session:** When you discover something that would prevent a future mistake → add it here immediately.
**At session end:** Merge new patterns into `memory/context/patterns.md`. Archive entries older than 10 sessions.
**CEO access:** This file is CEO-readable. Write for strategic clarity, not technical verbosity.
