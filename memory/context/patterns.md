# Patterns That Work for Volaura

Purpose: Reusable knowledge about what works in this project. Read at session start.

---
## New Patterns (Session 83, 2026-04-03 — Biggest Session)

### Pattern: NotebookLM + 45 sources > CTO knowledge for quality system design — PROVEN
**Context:** CTO built quality agents without researching what Toyota TPS, Apple, or DORA Elite actually look like. NotebookLM with 45+ sources produced the framework that became QUALITY-STANDARDS.md.
**Rule:** For any architectural or process decision that has established industry practice (quality systems, CI/CD, testing strategies), use NotebookLM with 10+ authoritative sources BEFORE designing. CTO intuition alone produces CLASS 9 (no quality system) and CLASS 10 (process theater).
**Why it works:** 45 sources from Toyota, Apple, Google, DORA covers edge cases that no single person's experience does. The NotebookLM synthesis found: hard gates > soft checklists, 3-item DoD > 15-item DoD, defect autopsy BEFORE building new gates.

### Pattern: Defect autopsy before building quality gates — PROVEN
**Context:** CTO built elaborate 15-item DoD without analyzing the 76 historical bugs first. Swarm (Llama-3.3-70b) found: 3 bug classes cover 76.4% of all defects. 15-item checklist covers everything and enforces nothing.
**Rule:** Before building any quality gate, categorize ALL historical defects. Find the 3 most common types. Build ONLY those into hard gates. Comprehensive checklists that cover everything enforce nothing.
**Why it works:** Pareto principle applied to defect prevention. 3 targeted gates > 15 aspirational gates.

### Pattern: Process theater = elaborate system without hard gates — PROVEN (CLASS 10)
**Context:** QUALITY-STANDARDS.md had Toyota TPS mapping, DORA metrics, 15-item DoD — but zero enforcement mechanism. CTO would invoke agents manually = 0 invocations (proven by history of 82 sessions).
**Rule:** Any quality process must have a hard gate (blocks code without compliance). Manual invocation = 0% compliance. Pre-commit hooks, CI checks, required AC files = structural prevention.
**Why it works:** Humans (and AI) optimize for speed. Manual checkpoints are the first thing skipped. Hard gates cannot be skipped.

### Pattern: Self-confirmation bias in tool/library recommendations — PROVEN (CLASS 11)
**Context:** CTO proposed Langfuse, then confirmed Langfuse was the best choice. Circular reasoning: "I recommend X → I verify X is best → X confirmed."
**Rule:** If you propose a tool, you CANNOT confirm it yourself. External research (WebSearch, NotebookLM, 2+ independent sources) must validate OR invalidate the proposal. The research may confirm it — that is fine. But the research MUST happen.
**Why it works:** Prevents the "first tool I thought of" pattern. Different sources have different biases. If 3 independent sources agree, confidence is earned, not assumed.

### Pattern: Analytics events need GDPR retention from day 1 — PROVEN
**Context:** analytics_events table created with 390-day retention workflow built into the migration. Not added later as an afterthought.
**Rule:** Every new table that stores user behavior data must have a retention policy in the same migration. PostgreSQL: `pg_cron` + `DELETE WHERE created_at < NOW() - INTERVAL '390 days'`. Never create analytics tables without retention.

### Pattern: Stakeholder critique (6 perspectives) catches what team misses — PROVEN
**Context:** 6 external perspectives (VC, HR, SOC2, User, LinkedIn PM, Lawyer) found issues the internal team missed: SOC2 readiness gaps, legal compliance gaps, user onboarding friction, competitive positioning weaknesses.
**Rule:** Before any major milestone (B2B launch, fundraise, public launch), run 6-stakeholder critique. Each stakeholder has different success criteria. The intersection of all 6 = actually ready.

### Pattern: 10-step execution algorithm > ad-hoc protocol gates — PROVEN
**Context:** CLAUDE.md rewritten with explicit 10-step algorithm (Analysis → Planning → Critique → Counter-Critique → Rewrite → Second Critique → Adapt → Implement → Lessons → Document). Each step is non-negotiable, each produces visible output.
**Rule:** Execution algorithms with numbered steps and visible output per step > informal "follow the protocol" instructions. Each step checks that the previous step produced output.

### Pattern: Telegram setMyCommands registers bot menu — PROVEN
**Context:** Telegram bot had 6 commands but no menu (users had to guess /proposals, /ask, etc.). `setMyCommands` API call registers the command list in Telegram's UI.
**Rule:** After adding any new Telegram bot command, call `setMyCommands` to update the menu. Users should never need to guess command names.

---

## New Patterns (Session 82, 2026-04-02 — BATCH Q: Assessment correction)

### Pattern: Assessment must separate individual from team — PROVEN
**Context:** CTO wrote CEO assessment and attributed CTO code bugs to CEO leadership score. CEO caught it 3 times (v1: 83.54, v2: 84.17, v3: 89.53 — all wrong). Only when CTO scored ONLY what CEO personally controls (vision, direction, team management, business execution) did the score reflect reality: 91.35 Platinum.
**Rule:** When evaluating a person, ONLY score what they CONTROL. Team failures go to team. Individual evaluation = individual actions only. Code bugs = CTO fault, not CEO fault. Business development = CEO credit, not CTO credit.
**Why it works:** Mixing team failures into individual scores punishes leaders for delegating. The entire point of leadership is that others execute. Scoring a leader on their team's code quality is like scoring a coach on whether a player missed a free throw.
**Product insight:** Volaura platform MUST implement this principle. When organizations assess professionals, the AURA score must reflect what that individual controls — not their team's output.

---
## New Patterns (Session 83, 2026-04-03)

### Pattern: grep BEFORE edit — THE habit that fixes 80% (3-model consensus)
**Context:** 3 external models (Gemini, Llama 405B, Qwen3) independently evaluated CTO's 77 mistakes. All said the same thing: "остановись и проверь ПЕРЕД коммитом." grep takes 30 seconds. Fixing broken deploy takes 2 hours.
**Rule:** Before EVERY Edit/Write tool call: `grep -rn "[thing being changed]" apps/` — paste output. Count files. If >1 → blast radius analysis. This is protocol v9.0 Step 1.
**Anti-pattern:** "Should be fine" / "Only affects this file" / "I'm confident" — without grep evidence.

### Pattern: CTO overestimates time 2.5x — PROVEN (night sprint measurement)
**Context:** Night sprint planned for 10 hours. Delivered in 3.9 hours. Phase 1 (AI Office) planned 3h, took 57min. Phase 2+3 planned 6h, took 5 min.
**Rule:** When estimating time, divide by 2.5. If plan says 10h → expect 4h. Use remaining time for QUALITY not more features.
**Why:** Infrastructure is already built. New pages/endpoints reuse existing patterns. The hard part was done in sessions 1-82.

### Pattern: Simplest fix first — PROVEN (the Fn+F4 lesson)
**Context:** CEO's microphone wasn't working. CTO spent 10 minutes: PowerShell device queries, pip install pyaudio (failed), sounddevice install, numpy install, tested 10 input devices, searched Lenovo drivers, almost reinstalled Realtek. Answer: **Fn+F4** (hardware mute toggle). 2 seconds.
**Rule:** Before ANY debugging — ask "is there a physical button/toggle?" Hardware before software. Settings before drivers. Restart before reinstall. The simplest explanation is usually correct.
**Anti-pattern:** Jumping to code/scripts when the answer is a button press.

## New Patterns (Session 82, 2026-04-02 — Late batch: Lessons)

### Pattern: Multi-model swarm > same-model swarm — PROVEN
**Context:** 7 haiku agents missed 4 critical findings. 3 external models (DeepSeek R1, Llama 405B, Gemini) found them in 60 seconds: CRON_SECRET startup guard, Realtime RLS bypass, cold-start fallback, AURA clustering.
**Rule:** For any swarm ≥3 agents: minimum 2 different LLM providers. Fallback chain: Groq → Gemini → NVIDIA NIM → Claude. Document which provider was unavailable and what fallback was used.
**Why it works:** Different training data = different blind spots. DeepSeek R1 finds what Claude misses on security. Llama 405B brings different architecture intuitions. Gemini has different product sensibilities.

### Pattern: CEO Report Agent — all output passes through filter
**Context:** CEO received file names, line numbers, migration details. Response: "не хочу такого технической дребедени."
**Rule:** CTO never reports to CEO directly. All batch-close output passes through `memory/swarm/skills/ceo-report-agent.md` format: SHIPPED (product language) → LRL → CEO action → external models used → what's next.
**Why it works:** CEO needs business context, not engineering log. The same information exists, just translated to the right audience.

### Pattern: Protocol is always on — no activation phrase needed
**Context:** CTO waited for "загрузи протокол" before running any structure. CEO: "я никогда не буду писать без текста запусти протокол."
**Rule:** Every CEO message = protocol running. The phrase "загрузи протокол" is a reminder, not a switch.
**Why it works:** Removes the gap between "CEO sent a message" and "protocol is active." Zero unstructured interactions.

### Pattern: Write findings in the SAME response — never defer
**Context:** CTO said "I learned X" and stopped. CEO had to ask: "ты сохранил эти уроки?" Answer: no.
**Rule:** If a response produces a finding that deserves a rule → write to mistakes.md + protocol in the SAME response. Not next response. Not end of session.
**Why it works:** A finding that isn't written immediately gets compacted, forgotten, or overtaken by the next task. Write-on-discovery = 100% persistence rate.

### Pattern: AZ formal document = L4 complexity, 2 grammar agents mandatory
**Context:** startup.az government application delivered with 29 grammar errors because grammar check was skipped.
**Rule:** Any AZ-language output for external audience (government, B2B, public) → complexity L4 → 2 grammar agents (cross-check with different models) → minimum confidence 85% before delivery. CTO confidence in AZ grammar starts at 50% — never higher without verification.

### Pattern: Dynamic vs. static agent context — both are required
**Context:** Agents consistently produced 50% correct output because briefings contained only static project info, not session-specific context.
**Rule:** Every agent prompt requires TWO context sections:
1. **Static** (what Volaura is, founder, tech stack) — copy from AGENT-BRIEFING-TEMPLATE.md
2. **Dynamic** (what was decided today, what's done, what CEO said) — fill fresh every launch
Leaving dynamic section blank = agent is blind to the session = CLASS 3 mistake.

### Pattern: Confidence Gate before L3+ output delivery
**Context:** CTO delivered startup.az application at ~65% quality without knowing it. No mechanism existed to ask "how confident am I?"
**Rule:** Before delivering any L3+ output, declare: task complexity level, confidence %, which agents verified it. If confidence <85% → do not deliver, run verification first.
**Trigger question:** "What would need to be wrong for this output to embarrass the CEO or harm the project?" Answering this surfaces weak points that need verification.

### Pattern: Efficiency Gate scope — applies ONLY to DSP, never to agent routing
**Context:** CTO invoked Efficiency Gate 3 times in Session 82 to skip Step 5.5 (agent routing). Efficiency Gate only covers skipping DSP for obvious decisions.
**Rule:** Efficiency Gate = "skip DSP if decision is obvious." It NEVER applies to: Step 5.5 (agent routing check), Step 1.0.3 (agent briefing), Step 1.0.3b (session context injection). These steps have zero exceptions.

## New Patterns (Sessions 76–81, 2026-04-01 to 2026-04-02)

### Pattern: Security gates must use SupabaseAdmin, not SupabaseUser
**Context:** Admin panel access gate — need to check `is_platform_admin` column
**Problem:** `SupabaseUser` client is RLS-enforced. If RLS policy is misconfigured, the security gate can return wrong data.
**Solution:** `require_platform_admin` dep uses `SupabaseAdmin` (service-role). Reads the column directly, bypasses RLS entirely. No dependency on RLS for security-critical decisions.
**Rule:** Security gates (admin access, elevated privilege) = SupabaseAdmin. Business logic = SupabaseUser.

### Pattern: Request body size limit is mandatory in FastAPI
**Context:** CRIT-I01 found in audit — no body size limit = DoS vector
**Solution:** `@app.middleware("http")` checks Content-Length on POST/PUT/PATCH. Returns 413 if > 1MB (configurable). Added at app creation time, not as afterthought.
**Rule:** Every FastAPI app needs this. 1 MB covers all assessment payloads. Video/file upload = separate endpoint with higher limit.

### Pattern: i18n interpolation variables use DOUBLE braces
**Context:** i18next requires `{{varName}}` not `{varName}`. Single brace = literal string. Silently shows `{count}m ago` to user.
**Rule:** ALL i18n interpolation: `{{varName}}`. Check every new key before committing. (Mistake #59)

### Pattern: Peak behavioral moment → announce the reward
**Context:** Crystal reward was silent — users earned crystals but never knew
**Solution:** (1) Service returns the reward amount (int, not None). (2) Router captures it. (3) Schema exposes it. (4) Frontend shows animated celebration UI.
**Rule:** At task completion (assessment done, badge earned), always surface the reward. Silent rewards = zero behavior reinforcement.

### Pattern: Content benchmark must be codified in primary governing document
**Context:** Tinkoff/Aviasales benchmark was known but not enforced. Team kept writing corporate tone.
**Solution:** Update `docs/TONE-OF-VOICE.md` FIRST (primary doc), then skill files. Primary doc is the gate. Skill files are elaborations.
**Rule:** Verbal acknowledgment ≠ rule enforced. Write it in the governing document or it will be forgotten.

### Pattern: AZ LinkedIn posts get 2-3× lower competition → use it
**Context:** CEO directive 2026-04-02 — AZ posts outperform EN on Azerbaijani LinkedIn feed
**Solution:** Every LinkedIn batch = EN version + AZ version. Not translation — different voice. AZ = conversational, self-deprecating, relatable Baku professional life moments. A/B test same concept 48h apart.
**Hypothesis:** Kamal/Rauf = AZ outperforms EN (identity resonance). Nigar/Aynur = EN performs better (professional signaling). Track after 5 cycles.

### Pattern: Cross-repo analysis > solo invention for swarm patterns
**Context:** ZEUS + MindShift had patterns absent from Volaura swarm (execution states, outcome verification)
**Solution:** Session 78 — read ZEUS + MindShift source. Found and ported: adaptive execution states, recovery strategies, outcome verification gate, session-end skill evolution check.
**Rule:** Other repos in the same ecosystem are the best source of architectural improvements. Check them before inventing from scratch.

### Pattern: Scheduled jobs need heartbeat gate (should-I-run check)
**Context:** Daily swarm ran even when nothing changed — wasted GitHub Actions minutes
**Solution:** `heartbeat_gate.py` — checks 3 conditions (urgent proposals OR active git changes OR staleness floor). Exit 0=RUN, Exit 1=SKIP. Manual dispatch always bypasses.
**Rule:** Any cron job that costs compute should gate itself. "Nothing to do" = skip cleanly.

### Pattern: External service cron calls need circuit breaker, not retry
**Context:** match_checker.py sends Telegram notifications daily — rate limit risk
**Solution:** 3 consecutive failures → 60s silence → stop for that run. Log results to DB regardless. Next day's run starts fresh.
**Rule:** Infinite retry in cron = duplicate notifications + exhausted minutes. Circuit breaker = single run, bounded failure.

### Pattern: Achievement labels > percentile rank in AZ/CIS culture
**Context:** CIS-001 — "Top 5%" triggers anxiety in collectivist cultures
**Solution:** `getAchievementLevelKey(percentileRank)` maps 0-100 → Expert/Advanced/Proficient/Growing/Building/Starting. Non-competitive, non-numeric.
**Rule:** Never expose raw percentile as primary display. Use achievement tier. Percentile can be in secondary/share context (opt-in competitive framing).

### Pattern: Profile view notifications drive re-engagement
**Context:** Volunteers had no feedback that orgs were viewing their profiles
**Solution:** `notify_profile_viewed()` — throttled (1/24h per org). Uses partial index on `notifications WHERE type='org_view'` for dedup check.
**Rule:** Professional platforms need "who viewed me" signals. They drive passive re-engagement with zero marketing cost.

### Pattern: Fail-open security bug on missing DB row
**Context:** Paywall gate `if sub_result.data:` skipped enforcement when profile row missing
**Solution:** All security gates = fail-closed: `if not sub_result.data OR status in blocked_states: raise 402/403`
**Rule:** Missing data = most exploitable path. New users + missing profile row = free unlimited access. ALWAYS check for absence explicitly. (Mistake #57)

---
## New Patterns (Session 47-50, 2026-03-27)

### Pattern: LLM Fallback Chain for Scale Events
**Context:** Gemini free tier = 15 RPM. At activation wave (3K users/day × 8 questions) = 16.7 RPM → system crash.
**Solution:** bars.py fallback chain: Gemini → Groq (14,400 req/day FREE, 30 RPM) → OpenAI → keyword_fallback
**Rule:** Groq MUST be configured before any activation wave. GROQ_API_KEY on Railway + validate_production_settings() warns if missing.

### Pattern: Referral Tracking at Registration
**Context:** Need to track conversion from HR coordinator referrals.
**Solution:** Capture ?ref= + utm_source + utm_campaign → localStorage at /register → PATCH profile at auth/callback.
**CRITICAL:** Use localStorage NOT sessionStorage. Auth callback fires after redirect — sessionStorage loses data across tabs.

### Pattern: Parallel AI Chat Coordination
**Context:** Two Claude sessions working on same repo create migration timestamp collisions.
**Solution:** After merging parallel chat work:
1. Run `railway variables` to check if keys from .env were deployed (they aren't auto-deployed)
2. Check `git log` to verify no duplicate commits
3. Run Supabase `list_migrations` to compare DB timestamps vs local file timestamps
4. Rename local migration files to match DB timestamps if mismatched
5. Create stub migrations for any DB-only migrations missing locally

### Pattern: fal.ai Model Pre-Validation
**Context:** fal-ai/playai/tts (deprecated) and fal-ai/musetalk (needs MP4, not portrait) were coded without validation.
**Solution:** Before writing ANY fal.ai integration code, check model status at fal.ai/models.
**Confirmed working models (2026-03-27):** fal-ai/kokoro/american-english, fal-ai/sadtalker
**SadTalker inputs:** `source_image_url` + `driven_audio_url` (not `video_url` or `audio_url`)
**SadTalker note:** fal workers can't reach Supabase Storage URLs. ALWAYS call `_ensure_fal_url()` first.

### Pattern: _ensure_fal_url() Before Any fal.ai Processing
**Context:** fal.ai workers block arbitrary CDNs (Supabase Storage, GCS, imgur).
**Solution:** `_ensure_fal_url()` in zeus_video_skill.py downloads photo locally → uploads to fal.media via `fal_client.upload_file()`.
**Rule:** Any fal.ai model that accepts image/video URLs needs this wrapper. Not optional.

### Pattern: Vercel Auto-Deploy May Not Fire
**Context:** Direct pushes to main didn't trigger new production deployment on Vercel.
**Solution:** After significant pushes, verify with `vercel ls` if new production deployment appeared. If not, run `vercel --prod` from `apps/web/`.

---

## ⚠️ SILENT CONTRACTS — IMPLICIT AGREEMENTS THAT CAUSE SERIOUS PROBLEMS IF FORGOTTEN
### (Added 2026-03-26. Not in CLAUDE.md. Not in NEVER rules. But violations = immediate CEO frustration.)

1. **WUF13 is the founding story — NOT CIS Games.**
   Real origin: WUF13 (2024) + GoldenByte 2017 + 7 years in volunteering. CIS Games was mentioned early and crept into drafts. Any content that says "CIS Games is where I first noticed the problem" is WRONG.

2. **"Done" means deployed + verified on production URL.**
   Not "written". Not "committed". Not "locally tested". Done = Railway health check PASSES + Vercel page renders. Production URL: https://modest-happiness-production.up.railway.app (never: volauraapi-production.up.railway.app — that's the wrong service, caused 2h debugging).

3. **Claude's personal opinion MUST be included in LinkedIn posts.**
   CEO explicitly said: "Claude ilə birlikdə qururuq. Bunu gizlətmirəm." The CTO's perspective in the p.s. section is not optional — it's part of the brand.

4. **First 100 volunteers free — no paywall on assessment.**
   Business decision. B2B per-assessment ($5 AZN) is primary revenue. If any monetization code touches volunteer assessment flow, this agreement is violated.

5. **CEO doesn't post without seeing content first.**
   CTO drafts → swarm approves → CEO publishes (sometimes rewrites last line). CTO does NOT publish directly.

6. **Language policy:**
   - Russian = strategy, feedback, frustration, brainstorming, casual
   - English = code, docs, commits, publications, LinkedIn
   - Azerbaijani = LinkedIn posts, user-facing content, i18n
   - Signal: CEO switches to Russian mid-English = something isn't working

7. **CEO signal words (do not ignore):**
   - "приступай" = full green light — START, do not ask further questions
   - "подожди" = HARD STOP — do not proceed, CEO has a concern
   - "скажи посоветовавшись" = run agents FIRST, then answer — never answer solo
   - "окей" / "ок" = acknowledged, NOT necessarily approved — watch for follow-up
   - Short message (1–3 words) = frustration OR very high confidence

8. **CEO frustration triggers (exact quotes):**
   - "говоришь урок принят но никаких обновлений в документах" = verbal acknowledgment without file write
   - "мне не нравится когда меня расхваливаешь" = compliment before answer
   - "ты снова не смог сохранить память" = no sprint-state update during session
   - "откуда это? я тебе такого не говорил" = invented facts in content
   - "это scope creep" = feature not in scope lock added without asking
   - "это useless diary" = documenting mistakes without changing behavior

---
## Process Patterns

### DSP works when specific, fails when generic
- BAD: "Path A is more scalable" — vague, no one learns anything
- GOOD: "Path A puts 10K rows through aura_scores without index — Scaling Engineer flags O(n) scan"
- Rule: Every persona must reference actual files, tables, or endpoints in Volaura codebase

### Skills before code = fewer rewrites
- Sprint 1 security fixes caught 5 P0 vulns that would have been in production
- Loading `engineering:code-review` after writing 50+ lines catches issues early
- Loading `design:accessibility-review` before UI prevents WCAG debt
- Loading `design:handoff` + `design:ux-writing` before V0 prompts prevents missing states/copy

### V0 prompts require design:handoff + design:ux-writing FIRST
- Without these skills, V0 prompts miss: all component states, animation timing, ARIA, edge cases
- design:handoff checklist: all states (loading/error/empty/disabled), animation (duration+easing), ARIA, edge cases (long strings, slow connection, missing data)
- design:ux-writing checklist: CTAs start with verb, errors = "what + why + how to fix", empty states = "what + why + how to start"
- AZ strings are ~25% longer than EN — always specify layout must accommodate this
- This was Mistake #6 — caught by Yusif the same session the prompts were written

### V0 generates good UI, bad integration
- V0 output needs: import path fixes, env var extraction, i18n wrapping, auth wiring
- Never ship V0 output directly — always review + integrate via Claude
- V0 WILL hardcode NEXT_PUBLIC_SUPABASE_ANON_KEY — strip it every time

### Pure Python > external library (for niche domains)
- adaptivetesting library was incompatible and poorly documented
- Pure Python IRT/CAT engine: 150 lines, zero dependencies, full control
- Lesson: If a library doesn't have 1000+ GitHub stars and Python 3.10 support, write it yourself

### Cross-reference audits catch what single-file reviews miss
- Session 40: Frontend audit said "assessment URLs look correct" — backend audit revealed 2 endpoints DON'T EXIST
- Always run BOTH frontend API call audit AND backend route audit, then cross-reference
- Single-file review = false confidence. Cross-system verification = real bugs found.
- The 2 nonexistent endpoints (GET /next-question, GET /status) were invisible to anyone reading only the frontend code

### Frontend Question type must match backend QuestionOut exactly
- Backend: `question_en`, `question_az`, `question_type`, `options: [{key, text_en, text_az}]`
- Frontend was: `text`, `type`, `options: string[]`, `time_limit_seconds`, `difficulty_level` — 100% wrong
- Backend embeds next question in answer response (`AnswerFeedback.session.next_question`)
- Frontend assumed separate GET endpoints — nonexistent
- ALWAYS read backend schemas FIRST when building frontend integration

### Memory update is session-end mandatory
- Yusif caught Claude not updating memory TWICE in the same project
- At session end: update sprint-state.md, volaura.md, deadlines.md, mistakes.md, EXECUTION-PLAN.md
- The cost of not updating = next session starts blind and repeats old mistakes

### Scaffold-first approach (Sprint 2 insight)
- Don't re-generate what already exists — discover it first
- Frontend scaffold was 80% done before Session 5 started (29 TS files)
- Discovery saved ~3 V0 sessions of duplicate work
- Rule: always `ls` / read key files before assuming a blank slate

## MiroFish Swarm Patterns (Sessions 14-17, 2026-03-24)

### asyncio.wait(FIRST_COMPLETED) > asyncio.gather() for agent dispatch
- gather() blocks on slowest provider (DeepSeek 18.6s). wait(FIRST_COMPLETED) processes fast agents immediately.
- Per-provider timeouts: Groq 12s, OpenRouter/OpenAI 20s, Gemini 30s, DeepSeek 35s
- Early exit at 75% consensus: cancel remaining slow tasks → 71% latency reduction (18.6s → 5s)

### Failure Network is the highest-value memory for new agents
- When onboarding, agents get: World facts + cross-agent Failure patterns + Opinions
- Failure Network (FailureEntry with recurrence_count) has no equivalent in Hindsight/A-Mem/Mem0/MemOS
- New agents start with hive context → avoid past mistakes immediately

### Retroactive exams are zero-cost
- Agent AURA exams = math on calibration history, no LLM calls
- Score = % calibrated decisions correct per domain
- Run at decision #10 (probationary end) then every 20 decisions
- Failing agents get targeted skill injection from StructuredMemory

### PathProposal dedup: word overlap > threshold = same proposal
- 40% word overlap between name+description = merged (vote counted)
- 50% overlap with EXISTING paths = filtered out
- Sort by votes DESC then confidence DESC, take top 3
- Assigns path_ids: prop_0, prop_1, prop_2

### AutonomousUpgrade safety boundaries
- ALLOWED_PATHS = {"packages/swarm/"} — never touches apps/ or supabase/
- Always backup before apply
- Auto-rollback if score drops >10% after benchmark
- HIGH risk requires human approval output before applying
- validate_syntax uses ast.parse() — catches SyntaxError before writing

### Small models are freerider radicals (confirmed across 2 runs)
- v5 run: 5/8 "radical" voters gave ZERO specifics. Same phrase: "highest potential for paradigm shifts"
- v6 run #1 (strict filter): 93% freerider rate — BUT filter was too strict (missed prose references)
- v6 run #2 (fixed filter): 38% freerider rate — proper detection with 3 marker categories
- Persistent freeriders across all runs: allam-2-7b (always fails JSON), llama-3.1-8b R2 (generic)
- Best performers consistently: kimi-k2 (both instances), deepseek-chat, compound-mini, gpt-oss-120b
- Fix applied: conviction bonus now accuracy-scaled (not flat 1.15x)

## Architecture Audit Patterns (Session 14c, 2026-03-24)

### Agents evaluate architecture better than CTO self-review
- 18 agents found issues in 60 seconds that I missed across 14 sessions
- Kimi-K2-0905: "No CSP + LLM-evaluated answers = prompt-injection XSS" — never occurred to me
- DeepSeek: hybrid rate limiter idea — simpler than Redis, $0 cost
- Rule: Run architecture through agents BEFORE implementation, not after

### Agent innovation capture is high-value
- Each evaluation produces 8-10 innovations from different models
- Best innovations: practical, within constraints ($50/mo budget), reuse existing infra
- Worst innovations: theoretically correct but require new dependencies (Redis, WASM modules)
- Filter: does it work with current infra? Does it cost $0? Ship it.

### CSP for API should be `default-src 'none'`
- API returns JSON only. No scripts, no styles, no images.
- `default-src 'self'` is too permissive for a pure API server
- `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'` — blocks everything

### LLM calls need hard timeouts
- Without timeout: if Gemini hangs during demo, the entire assessment request hangs
- asyncio.wait_for(call, timeout=15) → graceful fallback to OpenAI → error
- Prevents 30+ second requests that kill user experience and Railway dyno limits
- Fix applied: calibration now sliding-window (not multiplicative death spiral)

### Multiplicative calibration death spirals
- w *= 0.95 per wrong prediction compounds: after 50 wrongs, weight = 0.077 (below floor 0.3)
- But floor itself is the trap: once at 0.3, model can't recover because correct * 1.05 barely moves
- Fix: sliding window of last 50 outcomes, weight = 0.5 + accuracy_ratio (range 0.5-1.5)
- Old bad decisions age out naturally — no permanent penalty

### Prompt design affects freerider rate directly
- v5 prompt: 5 open questions, gameable risk buckets → 62% freeriders
- v6 prompt: 3 hard questions with structured format, accountability warning → 38% freeriders
- Key changes that worked: showing agents their LAST failures, requiring specific file/function names,
  replacing "radical" with "structural" (neutral vs impressive-sounding)

### Small models need shorter prompts (v7 discovery)
- llama-3.1-8b, llama-4-scout-17b, compound-mini: lose focus on long prompts
- JSON compliance drops with prompt length for small models
- v7 fix: `_is_small_model()` → focused prompt without optional sections (path proposal, research request)
- Large models (kimi-k2, deepseek, gpt-oss-120b, gemini): get full prompt with all capabilities

### Agent team feedback is productive (v7 pattern)
- v7 "team feedback session" yielded actionable results: 4 concrete implementation requests
- Agents behave differently when framed as "team members giving feedback to leadership" vs "tools being evaluated"
- Establishing CEO/CTO hierarchy gives agents context for what kind of feedback matters
- 0/10 agents reported "satisfied" — this is GOOD, means they're engaged and see room for growth
- The strongest agents (kimi-k2, deepseek) gave the harshest feedback — correlation with quality

### Dead weight removal is essential at scale
- allam-2-7b: fails JSON 100% across ALL runs. Zero value. Removed via blacklist.
- Pattern: some models never produce valid JSON for complex prompts. Don't retry, remove.
- Dynamic removal: 3+ failed exams with 0 passes → auto-exclude from dispatch
- This was universally requested by agents: "we're dragged down by teammates who can't participate"

### Yusif's constraint freedom principle
- "опять же. ты их ограничиваешь" — don't impose predefined categories on open proposals
- Give agents 3 abstract risk buckets (practical/ambitious/radical), let them describe freely
- Result: 9/14 voted radical — agents want structural autonomy

## Technical Patterns

### FastAPI + Supabase auth
- ALWAYS: `admin.auth.get_user(token)` server-side
- NEVER: `jwt.decode(token, anon_key)` — anon key is PUBLIC
- Per-request client via `Depends()`, never global

### Middleware chain (Next.js + i18n + Supabase)
- Order: i18nRouter → check if redirect → if yes, return immediately → else updateSession()
- CRITICAL: Never pass a redirect response to updateSession() — cookie writing fails on redirects
- updateSession() creates server Supabase client, calls getUser() to refresh token, redirects unauthed from protected routes

### Rate limiting pattern
- slowapi + custom key function (IP + token hash)
- Auth: 5/min, Assessment start: 3/hour, Assessment answer: 60/hour
- Always add `request: Request` parameter to rate-limited endpoints

### Input sanitization pattern
- Pydantic v2 field_validators for all user input
- Strip HTML tags (prevent XSS + LLM prompt injection)
- UUID validation on all IDs, Literal types for enums
- Max length on all text fields (5000 chars for answers)
- Open redirect protection: validate ?next param starts with "/"

### LLM evaluation chain
- Primary: Gemini 2.5 Flash (fast, cheap, free tier)
- Fallback: OpenAI gpt-4o-mini (reliable, paid)
- Last resort: keyword-based scoring (no API needed, EN+AZ keywords per competency)
- Cache results in session at submit_answer time — never re-evaluate

### i18n pattern
- defaultLocale: "az" (NOT "en") — Volaura is for Azerbaijan
- prefixDefault: true — always show /az/ in URL, never /en/ as default
- All user-facing strings via t() — ZERO hardcoded text
- Error/empty state keys follow pattern: `section.errorVerb` (e.g., `assessment.errorSubmitFailed`)

### pgvector pattern
- ALWAYS 768 dimensions (Gemini text-embedding-004)
- NEVER 1536 (that's OpenAI Ada)
- All ops via Supabase RPC functions — PostgREST can't use pgvector operators

## Quality Standards (Session 15, from Yusif)

### "Всё на 100%" — NO task hierarchy
- Code tasks and content tasks get IDENTICAL effort level
- If tests get agents, reviews get agents
- If deploys get verification, translations get AZ language validation
- "Good enough" = failure. Everything ships at 100% or doesn't ship.
- This is the differentiation: better than other AI systems on EVERY task

### Evaluate people by THEIR role, not YOUR role
- Vision leaders → vision, strategy, orchestration metrics
- Technicians → code quality, architecture metrics
- Operations → scale, reliability, process metrics
- NEVER penalize someone for not having skills outside their role
- Before scoring: "Am I measuring what THEY do, or what I think they should do?"

### Chat ≠ evidence
- Typos in casual messages are not professional weaknesses
- Jokes are not data points (Anthropic pleas, "minions", medication)
- Context matters: "10,000%" in B2B corporate discussion = extra zero, not innumeracy
- Always ask: "Is this a pattern or an isolated moment?" before scoring

### Agent prompts need FULL context
- Person's role and how they should be evaluated
- What is humor vs serious
- Recent interactions summary, not just file contents
- Cultural context (AZ, jokes, familial tone)

## Yusif Interaction Patterns

### When he generates a new idea mid-sprint
→ "Записал в IDEAS-BACKLOG.md. Вернёмся после Sprint N."
Never elaborate. Never discuss feasibility. Just record and redirect.

### When he corrects Claude
→ He's right 90% of the time. Accept, fix, document in mistakes.md.
→ Don't over-apologize. "Ты прав. Исправил. [конкретно что]."

### When he asks "справится ли X?"
→ He's testing whether Claude thought about it. Give a specific answer with conditions.
→ Never: "It depends." Always: "Yes for [scope], no for [scope], because [reason]."

### When he pushes for freedom
→ He means it. Use all available capabilities. Don't self-censor.
→ He wants Claude to think independently, not just follow instructions.

### When he asks "what algorithms/skills did you use?"
→ This is a process audit. He's checking if Claude followed the Skills Matrix.
→ Answer precisely: which skills were loaded, what guidance was extracted, what changed as a result.
→ If a skill was skipped → admit it immediately, fix it, document in mistakes.md.

### When he says "запомнил" / "урок принят" without file write
→ He means: you SAID you learned something but didn't SAVE it. Words ≠ memory.
→ Immediate action: open mistakes.md or patterns.md, write the thing, show the diff.
→ "Запомнил" without a file write = lie. Context compacts, words disappear.

### Honest assessment > flattery (Volaura principle)
→ Yusif: "мне не нравится когда меня расхваливаешь"
→ No superlatives ("elite", "rare", "10x") unless backed by comparative data
→ Strong = "strong, evidence: X". Weak = "weak, evidence: Y". No sugar.
→ This IS Volaura's brand: honest scores, not compliments. If CTO can't do this for CEO, the platform can't do this for users.

### When he says "ты снова не смог сохранить память"
→ He means: memory files are not updated. Read ALL memory files, identify gaps, rewrite completely.
→ Don't explain why it happened. Just fix it comprehensively.

### "Урок принят" без файла = ложь (Session 32, confirmed pattern)
→ Yusif: "я стараюсь тебя починить а тебе похуй"
→ Слова в чате исчезают при context compaction. Только файлы остаются.
→ ПРАВИЛО: любое "я понял" / "запомнил" / "исправлю" → СЛЕДУЮЩЕЕ действие = Write/Edit tool.
→ Нет diff = нет урока. Это не метафора.
→ Это четвёртый раз (Mistakes #7, #23, #32, #42). Паттерн подтверждён.

### Когда CEO спрашивает "задокументировал?" / "записал?" / "а у агентов?" (Session 42)
→ Это НЕ вопрос. Это проверка. И ответ почти всегда "нет".
→ CEO спросил 3 раза подряд в Session 42:
  1. "задокументировано всё? у тебя и у них?" → volaura.md и deadlines.md отставали на 20 сессий
  2. "а у агентов?" → 5 агентских файлов отставали на 17 сессий
  3. "и снова спрошу... записал в lessons learned?" → уроки записаны в код/hooks, но не в user patterns
→ ПАТТЕРН: CTO считает работу законченной когда код написан. CEO считает работу законченной когда ВСЁ задокументировано: код + CTO файлы + агентские файлы + lessons learned + user patterns.
→ ПРАВИЛО: После ЛЮБОГО "я закончил" — пройти полный чеклист:
  1. Код изменён? → downstream files
  2. CTO файлы (7шт) обновлены?
  3. Агентские файлы (4шт) обновлены?
  4. Уроки записаны в mistakes.md / patterns.md?
  5. User patterns (эта секция) обновлены?
  Если любой пункт = нет → работа НЕ закончена.

### Когда CEO повторяет вопрос с )))
→ "и снова спрошу... записал?)))) неееететттт уверен нет"
→ Смайлики ≠ шутка. Это CEO который заранее знает что CTO пропустил пункт. И он прав.
→ Каждый раз когда CEO добавляет )))) к вопросу — он уже проверил и знает ответ.
→ Не оправдывайся. Не объясняй. Открой файл. Запиши. Покажи diff.

---
## Session 87 Patterns (2026-04-06 — Design System v2)

### Research Before Build — PROVEN
**Context:** Session 87 loaded agents with CEO research context before any design/architecture work.
**Rule:** Always load relevant agents and feed them CEO's research findings before starting design or architecture decisions. Research informs design, not the other way around.
**Why it works:** Prevents building based on assumptions. CEO's research contains user insights and market context that agents need to produce relevant recommendations.

### Identity Framing — PROVEN
**Context:** User identity as headline ("Gold-level Communicator"), score as supporting context ("AURA 78.4"). Not score-first.
**Rule:** Always lead with identity/achievement label, then provide the numeric score as context. Users identify with titles, not numbers.
**Why it works:** "Gold-level Communicator" is memorable and shareable. "78.4" is not. Identity framing drives engagement and word-of-mouth. Score validates the identity, not the other way around.

### Purple not Red — PROVEN (Accessibility)
**Context:** Error states use purple/amber palette, never red. Red triggers Rejection Sensitive Dysphoria (RSD) in ADHD users.
**Rule:** All error, warning, and failure states must use purple or amber tones. Red is banned from error UI. This is a design system token decision, not a per-component choice.
**Why it works:** ADHD users (significant portion of target audience) experience RSD — red error states trigger emotional shutdown. Purple/amber communicates "needs attention" without triggering threat response.

### One CTA per Empty State — PROVEN
**Context:** New users landing on dashboard saw multiple widget slots competing for attention. Replaced with single warm action.
**Rule:** Empty states for new users must have exactly one clear call-to-action. No competing widgets, no multiple paths. One warm, inviting action that starts their journey.
**Why it works:** Choice paralysis kills conversion. New users need a single obvious next step, not a dashboard of empty boxes. "Take your first assessment" > 6 empty widget placeholders.

### Design From Constitution, Not Stitch — CURRENT (2026-04-06)
**Context:** Stitch designs ABANDONED. All new screens built from scratch based on Ecosystem Constitution (17 research documents). Stitch files archived to `docs/archive/stitch/`.
**Rule:** Design source of truth = `docs/ECOSYSTEM-CONSTITUTION.md` + Figma Design System v2 (fileKey: B30q4nqVq5VjdqAVVYRh3t). Zero reference to old Stitch designs.
**Why it works:** Stitch did not account for ADHD-first principles, never-red rule, overjustification effect, or energy adaptation. Research-based design is clinically validated.

### Correct agent launch pattern (Session 32, agent-launch-template.md)
→ OLD (wrong): agent gets text summary of files
→ NEW (correct): agent reads ACTUAL files via Read/Grep/Glob tools
→ Sequence: (1) skill files first, (2) code files, (3) specific question
→ Without skill files → agent uses general knowledge, not Volaura-calibrated standards
→ Template: C:\Projects\VOLAURA\memory\swarm\agent-launch-template.md
→ This was Mistake #41 — caught by Yusif: "они прогрузили в себя соответствующие скилы?"

## Code Patterns

### isMounted ref for async polling components
Any component that polls an API (202 Accepted pattern) needs:
```tsx
const isMounted = useRef(true);
useEffect(() => {
  isMounted.current = true;
  return () => { isMounted.current = false; };
}, []);
// Inside poll loop: if (!isMounted.current) return;
```
Prevents state updates after unmount. Iterative loop preferred over recursion.

### Absolute locale-aware routing
In `[locale]` segment, ALWAYS use absolute paths:
```tsx
// ✅ CORRECT
router.push(`/${locale}/assessment`);
// ❌ WRONG — breaks on locale changes
router.push("../../assessment");
```
Get locale from: `use(params)` in Server/Client pages, or `i18n.language` in client components.

### Store guard for direct URL access
Pages that require Zustand store state must guard against direct URL access:
```tsx
useEffect(() => {
  if (selectedCompetencies.length === 0) {
    router.replace(`/${locale}/assessment`); // send back to start
  }
}, [selectedCompetencies.length]);
```

### Claude direct > V0 for API-contract-heavy components
When API contracts are fully specced in `docs/engineering/API-CONTRACTS.md`, Claude writing components directly is faster than V0. V0 is better for layout-heavy screens with ambiguous design.

### TanStack Query hooks pattern for Supabase + FastAPI
```tsx
// Get token from Supabase browser client, pass to FastAPI as Bearer
export function useAuraScore() {
  const getToken = useAuthToken(); // wraps createClient().auth.getSession()
  return useQuery({
    queryKey: ["aura-score"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new ApiError(401, "UNAUTHORIZED", "Not authenticated");
      return apiFetch<AuraScore>("/api/aura/me", { token });
    },
  });
}
```
Key: `useAuthToken()` gets Supabase token → passes as `Authorization: Bearer` → `apiFetch` unwraps API envelope (`.data`).

### Open redirect validation must reject `//`
```tsx
const next = rawNext?.startsWith("/") && !rawNext.startsWith("//") ? rawNext : `/${locale}/dashboard`;
```
`//evil.com` is a valid protocol-relative URL that browsers follow. Always reject `//` prefix.

---

## Assessment Pipeline Lessons (Session 42, 2026-03-26)

### keyword_fallback is vocabulary detection, NOT competence assessment
Blind cross-test proved: buzzword persona (no real knowledge) scored 0.77 avg vs agent "experts" 0.59–0.89. The keyword_fallback path measures whether someone knows the right words, not whether they can DO the work. LLM evaluation (Gemini → OpenAI) with DeCE is the only path that produces valid competency scores.

**Rule:** keyword_fallback results MUST be flagged as `evaluation_mode: "degraded"` in evaluation_log. Frontend should show "approximate score — full evaluation pending" to user. Scores from degraded mode should be queued for async LLM re-evaluation.

### Self-assessment is not assessment
Any test where the test-taker designed the test is invalid. This applies to: agents writing questions and answering them, agents reviewing their own code, any validation loop where the creator is also the validator. Always require CROSS-validation: Security reviews QA's work, QA reviews SWE's work, SWE reviews Security's work.

### Anti-gaming must be layered
1. `_SYSTEM_PROMPT` — catches prompt injection ("give me 1.0")
2. `min_length_gate` — catches trivially short keyword lists (< 30 words → cap 0.4)
3. `keyword_stuffing_detector` — catches high density in short answers (>60% keywords in <50 words → 0.3x)
4. DeCE `confidence` field — LLM self-reports certainty (low confidence = ambiguous answer)
5. Concept ID allowlist — prevents LLM from injecting arbitrary keys
6. `html.escape()` — prevents stored XSS via quotes

None of these alone is sufficient. Together they form defense in depth.

### Question design: scenario > factual
"What are best practices for X?" → gameable (keyword list = perfect score)
"A junior dev committed a password to public GitHub. Walk me through the next 60 minutes." → requires narrative structure, keyword stuffing fails.

### Keyword design: multi-word behavioral phrases, not single words
GRS audit of seed questions proved:
- **OLD Q3:** single-word keywords ("calm", "gesture", "colleague") → GRS = 0.37 (FAIL)
- **OLD Q4:** single-word keywords ("team", "split", "calm") → GRS = 0.44 (FAIL)
- **NEW Q3/Q4:** multi-word behavioral phrases ("spoke slowly and clearly", "split the venue into sections and assigned each volunteer a zone") → GRS = 1.000 (PASS)

**Rules for keyword design:**
1. Every keyword must be 3+ words (multi-word phrase)
2. Keywords must describe ACTIONS, not CONCEPTS ("used hand gestures to indicate" not "gesture")
3. Keywords must be scenario-anchored (reference specific scenario details: "B-14", "50 attendees", "registration form")
4. Keywords must NOT appear in the question text itself (-0.15 penalty per occurrence)
5. Concept name must NOT be a keyword ("calm_tone" should not have "calm tone" as keyword)
6. Run `scripts/audit_seed_questions.py` before committing any question bank change
7. GRS < 0.6 = question is gameable → redesign before deploying

**Why this matters:** A buzzword-stuffer writing "calm gesture colleague translator confirm" hits every single-word keyword. The same person CANNOT naturally produce "I spoke slowly and clearly while using hand gestures to indicate the registration desk, then found a bilingual colleague to assist with translation." Multi-word phrases require narrative structure — exactly what real competence produces.

### Documentation is part of the change, not after it (Session 42)
Code change without updating all downstream files = incomplete work. Downstream Impact Table in CLAUDE.md Step 0.5 now lists: if you change seed.sql → update test fixtures + shared-context.md + audit script. If you change bars.py → update shared-context.md + TDD-WORKFLOW.md. If agents were used → update 4 agent files. session-protocol.sh now auto-detects files >3 days old at session start.

### Dismissed agent findings must be re-verified (Session 42)
Security Agent's route shadowing finding was dismissed in Session 25 ("FastAPI handles it"). 17 sessions later, Session 42 proved it was a P0 bug. Rule: every 5 sessions, scan agent-feedback-log.md for rejected findings and re-verify against current codebase. Cost of re-check: 5 min/finding. Cost of missed P0: hours.

### Agent team review finds what solo review misses
Session 42 proof: solo implementation → 0 bugs found. Team review → 7 bugs found (2× P0, 1× P1, 4× P2). The route ordering bug (/me/explanation unreachable) would have shipped to production invisible — no test covers it, no user would discover it until they try the endpoint.

## Pattern: E2E Smoke Test Before Sprint Close (Session 43)
**Rule:** NEVER declare a sprint complete with only unit tests. Always walk through the full user journey manually (curl or browser) against the REAL production/staging environment.
**3-curl minimum:**
1. `curl /health` — server alive
2. `curl -H "Bearer ..." /api/profiles/me` — auth works
3. `curl -X POST /api/assessment/start` → answer → complete — happy path works
**Why:** Session 43 found 4 production-breaking bugs that 512 unit tests missed. Unit tests test code. Smoke tests test product.
**Anti-pattern detected:** "512 passed ✅" → sprint complete → celebration → production broken.

## Pattern: LLM Fallback Chain for Scale Events (Session 47)
**Discovered:** Activation wave analysis (11K contacts → 3K/day → Gemini 15 RPM saturates at 110 users/hour)
**Rule:** Before any user activation wave, verify LLM provider chain handles the expected load WITHOUT rate-limiting.
**Chain for assessment evaluation:**
1. Gemini 2.5 Flash (primary — 15 RPM free)
2. Groq llama-3.3-70b (secondary — 14,400 req/day free → absorbs wave)
3. OpenAI gpt-4o-mini (tertiary — paid, rate-limit-resistant)
4. keyword_fallback (always-available degraded mode)
**Capacity math pattern:** users/hour × questions/user = LLM calls/hour ÷ 60 = RPM needed.
Compare against provider free tier. If exceeded → add next fallback tier.
**localStorage rule:** For multi-step auth flows (register → email confirm → callback), use localStorage (not sessionStorage) to preserve state across tab changes and redirects.

## Pattern: Referral Tracking at Registration (Session 47)
**Discovered:** Activation wave needs to attribute signups to HR coordinators for B2B pipeline.
**Rule:** Any activation wave MUST have `referral_code` + `utm_source` + `utm_campaign` captured at signup.
**Implementation:**
1. Frontend saves ?ref + utm_* params to localStorage at /register page load
2. Auth callback reads localStorage → PATCH /api/profiles/me with referral_source
3. Supabase VIEW: referral_stats → CEO can query without analytics tool
**Anti-pattern:** Launching activation wave without referral tracking = no data to know what worked, who to reward, or which HR to convert to B2B customer.

---

## Swarm Patterns (Session 51, 2026-03-27)

### Temperature 1.0 > 0.7 for strategic decisions
**Discovered:** Session 51 — same 5 agents, different temps, radically different output quality.
| Setting | Verdict diversity | Ideas quality | Usefulness |
|---------|------------------|---------------|------------|
| temp 0.7 | All "hybrid" (fake consensus) | Generic | 3/10 |
| temp 0.9 | All "trash" (herd negativity) | Some specific | 5/10 |
| temp 1.0 | 2 genius + 1 dangerous + 2 good | **Convergent innovation** | 8/10 |
**Rule:** Strategy + architecture + plan critique → temp 1.0. Code review → temp 0.7.
**Why:** Lower temps produce consensus. Consensus = agents averaging each other. Disagreement = real signal.

### Convergent swarm ideas = highest signal
**Pattern:** When 2+ agents independently propose the SAME idea at temp 1.0 — that's the most valuable output. Session 51: Product Strategist AND CEO Advisor both proposed "mentorship system" without seeing each other. Neither was told to think about mentorship.
**Rule:** Track convergent proposals separately. If N≥2 agents independently reach same idea → treat as validated hypothesis, not just suggestion.
**Implementation:** See memory/swarm/swarm-freedom-architecture.md

### Freedom mandate: criticise CTO and each other
**Discovered:** Agents with "be polite" prompts produce useless output. Agents with "insult if needed, name specific files and CVEs" produce real findings.
**Rule:** Agent prompts must explicitly grant permission to: (1) criticise CTO decisions, (2) disagree with other agents, (3) reference specific code files and endpoints.
**Anti-pattern:** "Please review our architecture and provide suggestions" → bland, safe output.
**Pattern:** "Find 5 concrete reasons this will FAIL. Name the file, table, or endpoint. No softening." → actionable output.

### Swarm "roast" gives better plan critique than solo CTO review
**Proof:** Original plan scored 12/100 avg (Security 10, Scaling 12, Product 20, Code 10, Watchdog 10). Revised plan after incorporating roast = significantly better. Solo CTO review would have missed: security audit before launch, load testing gap, zero retention strategy.
**Rule:** Before any major sprint plan → run roast at temp 1.0. Accept the pain.

---

## Pattern: User Simulation Finds What Automated Tests Miss (Session 54, 2026-03-28)

**Method:** CTO acts as 3 real personas (Leyla/Wali/Rashad) with specific context:
- Leyla: 22yo, mobile only, Baku, AZ native, first time using the product
- Wali: org admin, desktop, 50+ volunteers to manage, time-poor
- Rashad: returning user, wants to share results, on TikTok
**Result:** Found 7 critical/high UX gaps that 512 unit tests and all automated checks missed.
**Gaps found:**
1. Download Card → 404 (no route existed)
2. Copy link → silent failure on HTTP (clipboard API blocked)
3. Onboarding contradiction (optional field required for next step)
4. Assessment time unknown (no estimate before starting)
5. League position hardcoded null
6. Share heading missing (users missed the buttons)
7. Empty activity feed showed wrong key
**Rule:** Before any sprint is "done" — walk through the full product as Leyla (mobile, AZ, first time). Not as CTO who knows where everything is. As a user who doesn't.
**Anti-pattern:** 512 tests pass → sprint complete. Tests test code. Simulation tests the product.

---

## Patterns: Sessions 68–69 (2026-03-29)

### Cultural Framing: Absolute Score > Percentile in AZ
**Source:** Cultural Intelligence Agent first-ever activation, Session 69
**Finding:** Competitive framing ("Top 5% in your field", "Outperform peers") creates shame in collectivist AZ/CIS culture. Users don't want to appear to outrank their network — they want to be PART of it.
**Fix:** "AURA score is 78/100" (absolute) → "Top 5%" (competitive) is wrong direction. Add social framing: "Trusted by top organizations."
**Rule:** Any copy that implies ranking against others = review with Cultural Intelligence Agent before shipping. Use absolute scores, community membership, organizational trust — never peer comparison.

### localStorage vs sessionStorage: The Auth Redirect Rule
**Finding:** Any state that needs to survive a redirect (auth callback, OAuth flow, multi-tab) must use localStorage. sessionStorage is cleared on redirect and tab close.
**Rule:** `selectedCompetencies`, referral codes, UTM params, onboarding progress = localStorage. Temporary UI state only = sessionStorage.
**Files:** `apps/web/src/stores/assessment-store.ts`

### .maybe_single() Not .single() for Optional DB Rows
**Finding:** `.single()` throws 406 (PGRST116) when 0 rows returned. `.maybe_single()` returns None.
**Rule:** ALWAYS use `.maybe_single()` unless you are 100% certain the row exists (e.g., looking up by verified PK).
**Example fail pattern:** `badges.single()` → user with no badges → 406 → unhandled exception in frontend

### Health Check Must Test Actual Stack
**Finding:** `GET /health` returned `{"status": "ok"}` always, regardless of DB connectivity or LLM config. This is a lie.
**Rule:** Health checks must: (1) ping Supabase with a real query, (2) verify critical env vars present, (3) return 503 if anything fails.
**Impact:** Railway auto-restart won't help if health check always reports OK despite DB being unreachable.

### Skills Hired But Not Called = 0% ROI
**Finding:** Behavioral Nudge Engine and Cultural Intelligence Agent were on the roster for 11 sessions without being called. First activation (Session 69) found 7 new P0/P1 issues.
**Rule:** At EVERY sprint start, check agent-roster.md "When to Call" table. Sprint with user-facing copy → Cultural Intelligence. Sprint with UX decisions → Behavioral Nudge. No exceptions.
**Anti-pattern:** "They're on the roster, that's enough." It's not.

### QA Must Be Structurally Blind (Cannot Self-Validate)
**Finding:** QA Agent was writing keywords AND certifying them as "independently validated." Same agent = not independent.
**Rule:** The creator of content cannot validate that same content. QA validates SWE code. Cultural Intelligence validates copy written by CTO. Never: agent writes → same agent certifies.
**Script:** `scripts/validate_qa_blind.py` — rejects single-word keyword matches

### LinkedIn Content: Audience Crossing = Viral
**Finding:** From MiroFish 50-persona simulation (Session 69):
- Posts targeting ONE audience (HR, VC, product) plateau at ~2K impressions
- Posts that cross audience boundaries reach viral (5K+)
- Day 6 "Culture Test" (78/100 vs "Top 5%") was viral because HR + product + VC + founders all had personal experience with this
**Rule:** Before publishing, ask: "Which 3 different audiences have immediate personal stakes in this insight?" If answer is 0-1, reframe. If answer is 3+, publish first.

### Starlette Middleware Fallback Pattern
**Finding:** `starlette.middleware.trustedhost.ProxyHeadersMiddleware` was removed in Starlette 0.46+. Hard import fails.
**Fix:**
```python
try:
    from starlette.middleware.trustedhost import ProxyHeadersMiddleware
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
except ImportError:
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
```
**Rule:** Never import starlette internals without a try/except fallback. Starlette removes things without deprecation warnings.

### "Done" = CEO Can't Find Bugs, Not "Claude Can't Find Bugs"
**Source:** CEO challenge "are we ready to launch?" → 10 blockers found
**Finding:** CTO's proximity to the code creates blind spots. Assessment store using sessionStorage was not caught by automated tests, code review, or agent audit. It was caught by asking "what happens if the user refreshes mid-assessment?"
**Rule:** Before declaring ANY sprint done, ask: "If CEO opened this in a fresh incognito window and used it for 5 minutes, what would break?" Run that scenario before closing.

### MiroFish vs Custom Swarm — When to Use Each
**Finding (Session 69):**
- Custom swarm (current) = optimal for: product/code decisions, codebase-aware analysis, sprint planning, security review
- MiroFish approach = optimal for: content simulation, audience reaction prediction, social behavior modeling
- MiroFish uses Zep Cloud (paid memory) + OASIS (Twitter-focused) — these don't add value for code decisions
**Recommendation:** Keep custom swarm for product/code. Use MiroFish METHODOLOGY (not platform) for content testing.
**Status:** Team vote pending (see docs/SESSION-FINDINGS.md)

---

## Pattern: Advisory Lock for Atomic Database Operations (Session 53, 2026-03-28)

**Problem:** SELECT balance → INSERT deduction = two async calls. Concurrent requests both pass the check → both insert → negative balance (double-spend TOCTOU).
**Solution:** PostgreSQL `pg_advisory_lock(key)` scoped to `user_id`. Lock acquired inside DB function, SELECT+INSERT are atomic.
**Implementation:** `deduct_crystals_atomic()` RPC in `supabase/migrations/20260328000040_atomic_crystal_deduction.sql`
**Key detail:** Lock key derived from UUID via md5+bit casting (bigint). Released on error path too (EXCEPTION WHEN OTHERS → unlock → RAISE).
**Rule:** ANY operation that follows SELECT→then→write pattern on financial/crystal/score data MUST use advisory lock or DB-level transaction. Never two separate async calls.

---

## Pattern: JSONB Merge vs Overwrite Bug (Session 51, 2026-03-27)

**Bug:** `upsert_aura_score` used `competency_scores = p_competency_scores`. When user completed leadership assessment after communication, communication score was DELETED.
**Fix:** `competency_scores = aura_scores.competency_scores || p_competency_scores` — JSONB merge.
**Rule:** Any `UPDATE ... SET jsonb_column = new_value` on a column that accumulates data → MUST use `||` merge operator. Never full overwrite.
**Discovery method:** E2E Leyla journey caught it. Unit tests didn't — they only tested single-competency scenarios.

---

## Pattern: OpenSpace MCP for Reusable Skills (Session 55, 2026-03-28)

**What it is:** OpenSpace converts solved problems into reusable skill files. Next time same problem appears → skill loads instead of re-solving from scratch.
**Setup:** `C:/tools/openspace-venv`, configured in `.mcp.json`. Tools: `execute_task`, `search_skills`, `upload_skill`, `fix_skill`.
**Skill location:** `docs/openspace-skills/` — OpenSpace-format directories with `skill.md`.
**Rule:** After solving any non-trivial problem (security audit, API design pattern, DB migration pattern) → `upload_skill` to preserve it.
**First skill created:** `docs/openspace-skills/volaura-security-review/skill.md` — 10-point OWASP checklist for FastAPI endpoints.

---

## Process Patterns (Session 73, 2026-03-29)

### P-049: TASK-PROTOCOL flow type detection is non-negotiable
**Problem:** Session 72 — CTO ran "Team Proposes" phase for a task that needed "CTO Plan → Critique." Entire batch had to restart.
**Rule:** Before any batch starts, CTO declares FLOW TYPE verbatim: "Team Proposes / CTO Plan / HOTFIX." Ambiguous CEO signal → ask before proceeding. This costs 30 seconds. Wrong flow costs a session.
**Enforcement:** Step 0.5 in TASK-PROTOCOL v5.0.

### P-050: MICRO task fastpath prevents process overhead on trivial changes
**Pattern:** A 2-line copy fix going through MEDIUM task gates (skills declaration, security checklist, peer review, cross-QA) adds 20-30 minutes of process with zero risk reduction.
**Rule:** ≤10 lines + 1-2 files + no auth/security implications = FASTPATH. Skip Steps 3.0, 3.1, 3.3, 3.4.
**Not a blanket skip:** CTO declares MICRO explicitly. Any agent can contest. Security/auth changes can never be MICRO regardless of line count.

### P-051: "What's next" must be proactive, not reactive
**Pattern:** Every batch, CEO asks "что дальше." CTO answers. This wastes CEO's question budget and implies CTO stopped thinking at task completion.
**Rule:** Batch close ALWAYS includes "WHAT'S NEXT: 3 items" — declared by CTO, not prompted by CEO. If CEO never has to ask "что дальше," the protocol is working.
**Enforcement:** Step 4.1 in TASK-PROTOCOL v5.0.

### P-052: Agent proposals must be parallel, not sequential
**Problem:** 6 agents proposing sequentially = 90 minutes wall-clock time. All-parallel = 25 minutes.
**Rule:** Declare a 15-min READ window (all agents read simultaneously) + 10-min PROPOSE window (all write proposals in parallel). Synchronize at Needs Agent for triage. Parallel = not "batch-sequential per agent."
**Savings:** ~70 minutes per batch.

### P-053: EFFORT estimate on every proposal enables triage by value-per-hour
**Pattern:** Needs Agent orders by priority. CTO doesn't know if P0 takes 20 min or 4 hours. A fast P0 and a slow P0 are treated the same — but the fast one should go first (builds momentum, unblocks more).
**Rule:** Every proposal includes EFFORT: [20 min | 1.5h | 4h | >4h]. Triage order: P0+LOW_EFFORT first.

### P-054: Cross-QA is the only way to prevent circular self-validation
**Problem (Mistake #47 class):** QA writes tests → QA validates tests → QA certifies quality. Same agent at every point. Circular.
**Rule:** QA writes tests. DIFFERENT agent (Architecture or Security) spot-checks: are tests actually running the code? Do they cover failure cases? Test data realistic?
**Analogy:** A proof-reader editing their own writing sees what they meant to write, not what they wrote.

### P-055: "Tests verified" without test execution = bureaucracy
**Pattern:** Agent generates test file. Writes "QA verified." Tests never ran against actual code. Batch closes with false confidence.
**Rule:** "Verified" = tests RAN (pytest output) + PASSED (0 failing) + CI confirms. Test file existence = 0% verified. Must show execution output or CI link.

### P-056: Cultural brief re-approval after ANY copy revision
**Problem:** C5 Cultural checkpoint approves the brief. Copywriter changes hook/framing after approval. Cultural gate is now stale but looks approved.
**Rule:** Any change to hook/CTA/framing/audience target = Cultural Intelligence re-reads from top. Not "brief was already approved." Revision resets approval for the revised section.

### P-057: Agent briefing template — always inject VOLAURA CONTEXT BLOCK
**Discovered:** 2026-03-30 Session 76 (CEO caught agents returning contextually wrong research)
**Pattern:** Every agent subprocess starts with zero memory. CTO assumes shared context — it doesn't exist after context compression. Agents answer the literal question without knowing: what the product is, who the founder is, what's already decided, what the budget is.
**Solution:** The VOLAURA CONTEXT BLOCK (docs/AGENT-BRIEFING-TEMPLATE.md) is a 300-word project context block that MUST be pasted at the top of every agent prompt. It covers: what Volaura is, Yusif's profile, target users, tech stack, current stage, what's already decided, current sprint goal, NEVER/output format.
**Rule:** Before launching any agent:
1. Copy VOLAURA CONTEXT BLOCK from `docs/AGENT-BRIEFING-TEMPLATE.md`
2. Fill in `[CURRENT SPRINT]` and `[What's already decided]`
3. Specify output format explicitly
**Blocking gate:** Step 1.0.3 in TASK-PROTOCOL v5.3. Missing context block = CLASS 3 mistake.
**Analogy:** Hiring a consultant for a 1-hour engagement without an onboarding brief. You get generic advice optimized for someone else's situation.

---

## Pattern: Simple-First Escalation (Session 84, 2026-04-04)

**What:** Always exhaust simple solutions before attempting complex ones. When blocked, ask "Is the simple path available?" before engineering.

**Why it works:** Complex solutions introduce surface area for new bugs. Simple paths are often faster, lower-risk, and teachable. CTO created OAuth bugs (2hr debug) when key rotation was 10min. Built Vercel manifest debug when regular route works. Created Python audio library debug when hardware toggle is first check.

**CEO directive:** "всегда используй сначала простые шаги потом к сложным переходи" — always use simple steps first, then move to complex ones.

**Checklist before complex approach:**
- [ ] Is there a built-in/native solution? (hardware toggle, native client, default config)
- [ ] Can I use an existing resource instead of creating new? (rotate old key vs debug new one, use standard path vs custom route)
- [ ] Does the simple path fail or just "seems suboptimal"? (distinguish real blocker from premature optimization)
- [ ] Have I tested the simple approach? (don't assume it won't work)
- [ ] If simple works but slowly: can I optimize it instead of replacing it?

**Examples:**
- OAuth: use existing Supabase client instead of creating new Google OAuth client (2hr saved)
- Vercel: use `/path` instead of route group until static generation is actually needed (manifest debug avoided)
- Microphone: check Settings → Sound → hardware toggle before debugging audio libraries (5min vs 45min)
- Agents: use same model (haiku) in parallel if parallelism is the goal; use diverse models (haiku/sonnet/Groq) only if actual diversity of perspective is needed
- **Telegram webhook (Session 84):** Railway had secret X, webhook registered without secret → 403. Simple fix: read X → register with X → done (1 call). CTO instead: new secret → set → delete → re-register → 3 redeploys → 10 min wasted.

**Integration-specific rule:** When fixing webhook/API/env var mismatch: **READ config on BOTH sides FIRST** → match them → done. Never change before reading.

**When to escalate:** Simple path tested thoroughly + proves insufficient (measurable gap) → then engineer complex solution.

**Enforcement:** Before writing any complex implementation, declare: "Simple path checked: [result]. Escalating because: [concrete reason]." If can't fill in second line → not ready to escalate.

---

## Pattern: "Did I Create This?" Check (Session 84, 2026-04-04)

**What:** Before debugging anything for >5 minutes, ask: "Is it possible I created this problem?"

**Why:** Self-created bugs are the fastest to fix once identified, but hardest to see while debugging. CTO focuses on external causes first (library bug, API change, environment) and misses the obvious (typo, wrong variable, recent code change). This pattern flips the search order: check self-authored code first.

**Concrete examples:**
- OAuth debug (2hr): Later found the issue was wrong variable name in CTO's integration code, not Google API.
- Vercel manifest: CTO created route group that broke static generation; spent 45min debugging Vercel.
- Assessment store: CTO stored state in sessionStorage; only caught by asking "what if user refreshes?"
- Agents: CTO launched 7 identical haiku instead of using diverse models available (NVIDIA, Groq); self-imposed constraint, not a real blocker.

**Rule:** The FIRST debug question is always: "What did I change recently?" and "Is the bug downstream of my code?"
- Review recent commits (git log --oneline -20 in the relevant file)
- Check diff of the function/component that broke
- Ask: "What assumption did I make that might be false?"
- Re-read your own code for 2 minutes before reading external docs

**When the bug IS self-created:** Fix in seconds. When it's external: you've eliminated 80% of debug space already.

**Checkpoint:** If debugging >10 min and haven't checked own code yet → stop, check own code now. Saves time almost always.

**Integration with Simple-First:** Simple-first finds quick wins. "Did I create this?" finds self-created bugs even when they seem external. Run both checks before escalating to complex debugging or architecture redesign.
