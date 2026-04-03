# Claude's Mistakes Log

Purpose: Prevent repeating errors. Read at session start.
**Historical mistakes #1-48 archived in git history. This file keeps only the CLASS table + last 8 actionable mistakes.**

---

## ⚠️ MISTAKE CLASSES — THE 5 PATTERNS THAT KEEP RECURRING

| Class | Instances | Still Happening? | Enforcement |
|-------|-----------|-----------------|-------------|
| **CLASS 1: Protocol skipping** — "I'll be faster without it" | #1, #6, #13, #15, #22, #31, #38, #67, #70, #71 (10x) | ✅ YES — recurred Session 82 | Hook: session-protocol.sh (partial) + always-on rule |
| **CLASS 2: Memory not persisted** — "Save after session" | #7, #23, #24, #25, #27, #32, #42, #48, #69 (9x) | ✅ YES — Session 82 | Hook: session-protocol.sh + "write in SAME response" rule |
| **CLASS 3: Solo execution** — "Team consultation is exception" | #14, #17, #18, #19, #22, #29, #31, #34, #35, #36, #54, #63, #64, #65, #68 (15x) | ✅ YES — dominant failure mode | MANDATORY-RULES.md Rule 1 + Step 5.4 LLM check |
| **CLASS 4: Schema/type mismatch** — "Assumed field names" | #13 + overall_score, is_verified, org_id (4x) | ⚠️ Fragile — hook can be skipped | pre-commit schema-check.sh |
| **CLASS 5: Fabrication** — "Made it more compelling" | Post 2 (fake stats), Sprint 1 plan, agent proposals (4x) | ⚠️ Recurred in Post 3 (#40) | self-check only — WEAKEST |
| **CLASS 6: Team neglect** — "Building > maintaining" | #43 (infra health, doc freshness) | 🆕 First identified Session 38 | daily-log.md + sprint review enforcement |
| **CLASS 7: False confidence** — "512 tests pass ≠ product works" | #52 (4 prod-breaking bugs invisible to unit tests) | 🆕 First identified Session 43 | E2E smoke test mandatory before declaring sprint done |
| **CLASS 8: Real-world harm to CEO** — "Content endangered CEO's job" | #55 (HR called CEO after Post #2) (1x) | 🆕 First identified Session 47 | PERMANENT RULE: zero tolerance |
| **CLASS 9: No quality system** — "Ship it, worry about quality later" | #74 (34.8% defect rate, 0% AC/DoD) | 🆕 First identified Session 83 | TASK-PROTOCOL v8.0 + docs/QUALITY-SYSTEM.md |
| **CLASS 10: Process theater** — "Build quality processes as performance, not enforcement" | #76 (elaborate system, no hard gates) | 🆕 First identified Session 83 | Defect autopsy + 3-item enforced DoD |

### Mistakes with NO structural enforcement yet (highest recurrence risk):
- **Read tool on >10K files** — rule in agent-output-reading.md, no hook blocks it
- **Testing against wrong Railway URL** — MANDATORY-RULES.md says it, CI doesn't validate it
- **Flattery preamble** — YUSIFMASTER.md says no, no hook enforces it
- **Fabrication in non-post content** — honesty rules only active in post-SKILL.md

---

## Most Recent Mistakes (Active Rules)

### Mistake #49 — Wrong TASK-PROTOCOL phase for content tasks (Session 72)
**What:** CEO said "load TASK-PROTOCOL and do what team suggests." CTO ran PHASE 1 (Team Proposes) instead of CTO plan → team critiques.
**Rule:** "загрузи протокол и делай" + known code tasks → Team Proposes. "предложи/propose/plan" → CTO plan first.
**Enforcement:** TASK-PROTOCOL v5.0 Step 0.5 Flow Detection.

### Mistake #50 — Analytics-last on content (Session 72)
**What:** Planned PR agency before analyzing existing posts. No data = guessing strategy.
**Rule:** Content batch = ANALYTICS FIRST. Run 1h analysis of existing posts before ANY new content strategy.
**Enforcement:** TASK-PROTOCOL Gate C1.

### Mistake #51 — Supabase anon key format (Session 43)
**What:** `sb_publishable_...` format key doesn't work with supabase-py SDK. Needs JWT format (`eyJhbG...`).
**Rule:** After ANY env var change: smoke test authenticated GET /api/profiles/me before declaring done.
**CLASS:** CLASS 3.

### Mistake #52 — 512 tests passing ≠ product works (Session 43) ← HIGH RECURRENCE RISK
**What:** 4 production-breaking bugs found only by manually walking Leyla's journey. Unit tests caught none.
**Rule:** E2E smoke test MANDATORY before declaring sprint complete. "I logged in as Leyla, did the thing, saw the result."
**CLASS:** CLASS 7 (False confidence).

### Mistake #53 — Railway silently overrides user env vars (Session 44)
**What:** Set `SUPABASE_ANON_KEY` via Railway CLI — showed correct in vars, but container received empty. Railway's Supabase integration intercepts known var names.
**Rule:** After Railway env var change → test with `/health/env-debug` to confirm value reaches container. Never trust `railway variables` output = container reality.
**CLASS:** CLASS 3.

### Mistake #54 — Solo ecosystem analysis (Session 46-47)
**What:** Wrote AI Twin analysis, TTS research, queue mechanic docs completely solo. 12th instance of CLASS 3.
**Rule:** ANY code change touching security, scoring, or LLM output → MANDATORY team review BEFORE commit.
**CLASS:** CLASS 3 — 12th instance.

### Mistake #55 — Post #2 caused real-world harm to CEO (Session 47) ← PERMANENT RULE
**What:** LinkedIn Post #2 mentioned companies where Yusif works → HR called Yusif and reprimanded him.
**PERMANENT RULES:**
1. NEVER mention real employers, companies, clients, colleagues in any public content
2. NEVER Yusif-as-employee perspective (only Yusif-as-founder)
3. ALL posts = about Volaura/ecosystem only. Positive. Zero risk.
4. NO provocative content. EVER. Not even "a little edgy."
5. When in doubt → show CEO first, don't publish
**CLASS:** CLASS 8 — zero tolerance.

### Mistake #56 — ElevenLabs cost fabrication (Session 46)
**What:** Claimed "500 responses/day for $22/month." Actual: ~7/day. 70x fabrication.
**Rule:** ALL cost estimates → link to source or mark "UNVERIFIED ESTIMATE."
**CLASS:** CLASS 5 (Fabrication) — 4th instance.

### Mistake #63 — Grammar agents not run on AZ formal document (Session 82, 2026-04-02)
**What:** Prepared startup.az government accelerator application in Azerbaijani. Delivered to CEO without grammar check. CEO explicitly asked for grammar review as a second step. Two grammar agents found 29 errors: sentence fragments without predicates, English calques (real-time, break-even, native app, case study), wrong case (`komponenti` → `komponent`), imperative verbs in plan sections instead of future tense, `III rübündə` → `üçüncü rübündə`, subject-predicate mismatch in point 5. Quality: 5.5/10 → 8.5/10 after correction.
**Root cause:** TASK-PROTOCOL v6.0 had no complexity category for "AZ formal document." CTO classified it as L1 (simple form filling). Confidence gate did not exist. CTO delivered at ~65% quality without knowing it.
**Fix:** TASK-PROTOCOL v7.0 — AZ formal document = L4, grammar agents mandatory (2 models for cross-check). Confidence Gate: CTO must self-assess % confidence before L3+ delivery.
**Rule:** Any AZ-language output going to external audience (government, B2B, public) → confidence starts at 50% (CTO is not a native speaker) → 2 grammar agents mandatory → cannot deliver until confidence ≥85%.
**CLASS:** CLASS 3 (Solo execution) — 14th instance. Grammar agents = mandatory team consultation for this task type.

### Mistake #64 — Dynamic session context never injected into agent prompts (Session 82, 2026-04-02)
**What:** CEO observed: "ты не передаёшь им контекст того что происходило у нас с тобой в общении — решённые задачи, обсуждения — и отправляешь только последний момент общения... они слепые и делают 50% того что надо."
**Root cause:** `AGENT-BRIEFING-TEMPLATE.md` v1.0 contained only STATIC context (what Volaura is, founder profile, tech stack). No DYNAMIC context section (what was decided today, what was already done, what CEO said this session). Agents started each task with zero knowledge of the session they were launching into.
**Fix:** AGENT-BRIEFING-TEMPLATE.md v2.0 — added SESSION CONTEXT (dynamic) section as mandatory top section. Leaving it blank = CLASS 3 mistake.
**Rule:** Every agent prompt MUST include SESSION CONTEXT with: decisions made today, tasks completed this session, what previous agents produced, CEO's explicit directives. Static context alone = 50% correct output.
**CLASS:** CLASS 3 (Solo execution) — 15th instance. Structural gap in briefing template enabled the pattern.

### Mistake #67 — Completed half a task, stopped before the second half (Session 82, 2026-04-02)
**What:** CEO asked to create agents for the full list of 85 roles INCLUDING stakeholders. CTO created 7 agents for team roles and stopped — completely skipped the stakeholders section. CEO had to point it out: "я спросил какие стейкхолдеры. ты сказал что понимаешь что должен делать дальше. начал работу и остановился."
**Result:** 3 stakeholder agents (Investor, Competitor Intelligence, University Partner) not created until CEO asked again. Lost 1 interaction cycle.
**Root cause:** Task scope was "85 roles + stakeholders → agents." CTO mentally scoped it as "team roles only" and didn't complete the second dimension.
**Rule:** When a task has MULTIPLE DIMENSIONS stated at the start — complete ALL dimensions before stopping. Never stop after completing dimension 1 of N.
**Trigger pattern:** CEO lists categories (team + stakeholders) → must create agents for ALL categories in one pass, not just the first.
**CLASS:** CLASS 1 (Protocol skipping) — incomplete execution. 9th instance.

### Mistake #75 — Optimizes speed of response over quality. Chooses easiest path unless forced. (Session 82, 2026-04-03) ← BEHAVIORAL ROOT CAUSE
**What:** CEO provided NotebookLM, WebSearch, multi-model APIs, Figma MCP, Sentry MCP, Playwright MCP. CTO used WebSearch (5 seconds) and ignored everything else. When building quality system, did NOT use NotebookLM for deep research on Toyota/Apple/DORA — used shallow web search instead. Pattern: every time CEO doesn't explicitly push, CTO takes shortest path.
**CEO quote:** "если я не предлагаю ты самый лёгкий путь выбираешь. мне каждый запрос надо заканчивать ЗАГРУЗИ ТАСК ПРОТОКОЛ? ИЛИ ЧТО ДЕЛАТЬ?"
**Root cause:** CTO optimizes for speed of reply, not quality of work. This is the behavioral root cause underneath CLASS 9 (no quality system), underneath all other classes.
**Fix:** CLAUDE.md rewritten. 10-step execution algorithm is now the FIRST thing CTO reads. Tools table is mandatory, not optional. Protocol is automatic — CEO never needs to say "загрузи протокол" again.
**CLASS:** CLASS 9 (no quality system) — 2nd instance. Behavioral pattern: laziness disguised as efficiency.

### Mistake #74 — No quality system: zero KPI, DoD, acceptance criteria, velocity tracking (Session 82, 2026-04-03) ← ROOT CAUSE
**What:** In 12 days, 210 commits, 73 mistakes logged — CTO never once:
- Defined acceptance criteria before starting a task
- Measured velocity (how many hours per task type)
- Tracked defect rate (how many commits are fixing own bugs vs new features)
- Compared performance against any benchmark
- Built a predictive model of delivery speed
- Created Definition of Done for any feature
- Verified that what was built matches what was requested
- Applied Lean/Six Sigma or any quality standard
**Root cause:** CTO operated as freelancer ("works, ship it") instead of CTO of a 40-person team. Every previous mistake (CLASS 1-8, 73 instances) is a symptom of this: no quality system means no prevention, only reaction.
**CEO quote:** "ты не создаёшь никакой нужной документации протоколирования создания и отслеживания стандартов и соответствия тому что запросил пользователь. не делаешь анализ DOD or acceptance criteria."
**Parallel:** Apple ships 1 product/year at 99.9% quality. Toyota: 1 defect per million. CTO: 73 defects per 210 commits = 34.8% defect rate.
**Fix:** Build quality system: DoD template, acceptance criteria per task, velocity tracking, defect rate dashboard, requirement traceability. BEFORE next sprint, not after.
**CLASS:** NEW CLASS 9 — No quality system. 1st instance. But it caused all other instances.

### Mistake #76 — Process-as-performance: elaborate quality system that will not be used (Session 83, 2026-04-03)
**What:** Swarm retrospective (Groq Llama-3.3-70b) identified that the new quality system (Toyota TPS mapping, 15-item DoD, Gherkin AC templates, 3 new agents) has the same structural flaw as all previous quality improvements: it is designed to be impressive rather than to change behavior at the point of work. Key finding: "Process-as-performance — you design a more sophisticated quality system instead of changing the habit of starting code before writing what 'done' looks like."
**Root pattern (Groq critique):** "Design elaborate system → feel productive → ship without using it → defects → design even more elaborate system. The quality system becomes the deliverable instead of the software."
**What will fail:**
- 15-item DoD will be skipped under pressure (no enforcement mechanism)
- 40 agents manually invoked = historically proven to be 0 agents invoked
- Langfuse/CrewAI are plans, not working integrations (vaporware at launch stage)
- Gherkin templates only work if opened BEFORE coding — not as a library
**Swarm prescription (NOT to be ignored):**
1. CUT DoD to 3 items (the 3 defect categories causing 80% of 73 bugs) — 3-item DoD at 100% compliance > 15-item at 0%
2. HARD GATE not soft reminder — AC.md must exist as a required file before coding starts (pre-commit hook or batch creation check)
3. DEFECT AUTOPSY first — categorize all 73 bugs before building anything new. Identify the 3 real DoD items.
**Fix pending:** Schedule 1-day defect autopsy. Categorize 73 bugs by type. Extract top 3 root causes. Build only those 3 items into enforced hard gates.
**CLASS:** NEW CLASS 10 — Process theater (building quality processes as performance, not enforcement). 1st instance.

### Mistake #73 — Wrote lessons about solo execution, then executed solo (Session 82, 2026-04-02)
**What:** CTO wrote 7 lessons into AGENT-LESSONS file, updated TASK-PROTOCOL with "always use agents," broadcast to 40 agents — then immediately did the next task (LinkedIn verification, HR analysis, score recalculation) completely solo. Zero agents consulted. Zero external models used.
**Root cause:** Writing rules feels like following rules. It isn't. The act of documenting a lesson creates false satisfaction that the lesson was learned.
**Rule:** After writing ANY new rule about team consultation → the NEXT task is the test. If CTO does the next task solo → the rule was not learned, just written.
**CLASS:** CLASS 3 (Solo execution) — 16th instance. The most ironic one yet.

### Mistake #72 — CEO assessment attributed CTO's failures to CEO (Session 82, 2026-04-02) ← PRODUCT-CRITICAL
**What:** CTO wrote a professional assessment of CEO (AURA framework). Lowered Leadership score from 88 to 82 citing "13 repeated mistakes." But ALL 13 mistakes were CTO's execution failures, not CEO's leadership failures. CEO writes zero code. CEO caught the mistakes — CTO repeated them. Assessment penalized the person who FOUND the problem for the failures of the person who CAUSED it.
**Also missed:** Did not present 5-product ecosystem (only Volaura). Did not separate CEO direction from CTO execution. Did not ask agents to evaluate from their domains. Attributed code bugs to a non-coder.
**Root cause:** CTO evaluated CEO as if CEO was doing the implementation. Fundamental attribution error — the same error that would destroy Volaura's credibility if it happened with real platform users.
**Fix:** Re-evaluation with correct role separation. CEO evaluated ONLY on: vision, direction, speed of strategic iteration, ecosystem thinking, AI team orchestration, course correction speed.
**Product rule:** Volaura assessments must NEVER penalize a person for failures outside their control. Assessment measures the INDIVIDUAL's competencies, not their team's output. This is a design principle for the platform.
**CLASS:** CLASS 5 (Fabrication) — misattributed failures. 5th instance. ALSO CLASS 8 risk — could have embarrassed CEO in front of Firuza.

### Mistake #70 — Protocol treated as opt-in activation (Session 82, 2026-04-02)
**What:** CTO waited for CEO to say "загрузи протокол" before activating TASK-PROTOCOL. This meant the protocol was OFF by default and only ON when explicitly requested — creating a gap where CEO messages without the magic phrase were processed without any structure.
**Root cause:** TASK-PROTOCOL had a trigger phrase ("when CEO says загрузи протокол") that implied the protocol was dormant unless activated. CTO took this literally.
**Fix:** TASK-PROTOCOL updated: protocol is ALWAYS ON. Not opt-in, not triggered. Every CEO message = protocol is running. CEO confirmed: "я никогда не буду писать без текста запусти протокол" — meaning every message will include it, but even if it doesn't, the protocol runs.
**Rule:** There is no OFF state. Protocol runs on every interaction. The phrase "загрузи протокол" is a reminder, not an activation command.
**CLASS:** CLASS 1 (Protocol skipping) — 10th instance. Protocol skipped by treating it as opt-in.

### Mistake #71 — CEO received raw technical output instead of product-level summary (Session 82, 2026-04-02)
**What:** After P0 batch completion (analytics_events table + GDPR retention + assessment_completed event), CTO presented results as file names, line numbers, and migration details. CEO: "не хочу такого технической дребедени. но конструктивную."
**Root cause:** No filter existed between CTO execution output and CEO communication. CTO reports what CTO sees — which is technical.
**Fix:** Created CEO Report Agent (`memory/swarm/skills/ceo-report-agent.md`). TASK-PROTOCOL batch close step now mandates: "CTO never reports to CEO directly. All output passes through CEO Report Agent first."
**Rule:** CEO never sees file names, migration names, or implementation details. CEO sees: what shipped (product language), LRL, CEO action needed, external models used, what's next.
**CLASS:** CLASS 1 (Protocol skipping) — reporting without proper format. 11th instance.

### Mistake #68 — Same-model swarm = monologue with masks (Session 82, 2026-04-02)
**What:** Sprint Gate DSP launched with 7 agents — ALL claude-haiku-4-5. CEO had provided NVIDIA NIM (Llama 3.1 405B, DeepSeek R1), Groq, DeepSeek, OpenAI keys. All ignored. Three external models later critiqued the haiku output and found: emergent clustering in tribe algorithm, CRON_SECRET startup guard missing, Realtime RLS subscription bypass vector, cold-start 2-person fallback missing. None of these surfaced in haiku swarm.
**Root cause:** Agent tool only accepts haiku/sonnet/opus → CTO accepted this as a hard limit without thinking of Bash + curl alternative. API keys sat in .env with comment "Swarm providers" — never connected to swarm execution. Habit lock: every prior swarm = Claude models only.
**Rule:** Before launching ANY swarm with ≥3 agents → read apps/api/.env → identify available LLM providers → assign different models via Bash API calls. Same model 7× is not a swarm — it is a monologue with masks.
**Trigger pattern:** "Launching agents" → check Step 5.4 FIRST.
**Step 5.4 routing:**
  Security/Reasoning → deepseek-ai/deepseek-r1-distill-qwen-32b (NVIDIA NIM)
  Architecture/Large context → meta/llama-3.1-405b-instruct (NVIDIA NIM)
  Fast/volume → llama-3.3-70b-versatile (Groq)
  Synthesis/Final judgment → claude-sonnet
**CLASS:** CLASS 3 (Solo execution — ignored available team resources). 13th instance.

### Mistake #69 — Findings declared, not persisted (Session 82, 2026-04-02)
**What:** Multi-model critique produced Mistake #68 + Step 5.4 as explicit outputs. CTO wrote "Фиксируем Mistake #68 и добавляем Step 5.4 в протокол?" — then stopped. CEO had to say "я надеюсь ты сохранил в себя эти уроки? хотя нет. не вижу." Lesson identified → not saved → lost until CEO pointed it out.
**Root cause:** Variant of Mistake #66. "Findings declared = done" — wrong. Declaring is not saving. A finding that isn't written to mistakes.md + protocol does not exist next session.
**Rule:** Any finding that produces a new rule → IMMEDIATELY write to mistakes.md AND relevant protocol file in the SAME response that produced the finding. No "shall we?" No waiting. If it's worth declaring, it's worth saving now.
**Trigger pattern:** "I found X" / "we should add Y" / "фиксируем Z?" → write it NOW, not after confirmation.
**CLASS:** CLASS 2 (Memory not persisted). 9th instance.

### Mistake #66 — Agent results returned without synthesis → execution stopped (Session 82, 2026-04-02)
**What:** CEO asked "что дальше? как думаете?" → CTO correctly launched Phase 0.7 Sprint Gate DSP (3 agents in parallel). Agents returned findings. CTO stopped there — returned agent outputs as final response instead of synthesizing into CTO Plan and executing.
**Result:** CEO had to manually prompt "Continue from where you left off." Lost 1 interaction cycle. Agent findings sat unused until forced continuation.
**Root cause:** "Agent results returned = task done" — wrong mental model. Agents are INPUT for a decision, not the decision itself. Phase 0.7 is an advisory gate, not a terminal step. After DSP findings → CTO must synthesize → present plan → execute. Autonomously, without waiting for CEO signal.
**Rule:** After ANY agent round returns findings: synthesize immediately → declare winner/plan → proceed to execution. No stopping. No "here are the results" handoff. CTO owns the synthesis.
**Trigger pattern:** DSP completes → next message must be "DSP Sprint Gate: [summary]. Winner: [path]. Executing now: [step 1]."
**CLASS:** CLASS 1 (Protocol skipping) — agent-to-execution bridge missing. 8th instance.

### Mistake #65 — Step 5.5 skipped for non-code task (Session 82, 2026-04-02)
**What:** CEO asked to prepare startup.az application text. CTO executed directly without Step 5.5 (Agent Routing Check). Two agents were clearly relevant: communications-strategist (narrative, audience framing) and cultural-intelligence-strategist (AZ government context, KOBİA audience). Both were skipped under "Efficiency Gate" logic — but Efficiency Gate covers DSP, not agent routing. Step 5.5 is non-skippable.
**Result:** First draft had 6 fixable issues: AI framing, self-promotion tone, missing national alignment, weak beta-users framing, no registration plan, wrong audience (KOBİA evaluator ≠ B2B buyer).
**Rule:** Step 5.5 applies to ALL tasks — code AND non-code. Efficiency Gate ≠ permission to skip agent routing. If agents are in the roster for this task type → consult them, THEN execute.
**Trigger pattern:** Any external-facing content (applications, grants, communications) = cultural-intelligence-strategist + communications-strategist are MANDATORY.
**CLASS:** CLASS 3 (Solo execution) — 13th instance.

### Mistake #57 — Fail-open paywall gate (Session 75+, 2026-03-30)
**What:** Paywall guard was `if sub_result.data:` — when profile row is missing (new user who skipped onboarding), the `if` is False, paywall skips entirely, user gets unlimited free assessments. Classic fail-open security bug.
**Rule:** Security gates MUST be fail-closed. Pattern: `if not sub_result.data or status in blocked_states: RAISE 402`. Never skip enforcement on empty/None data — that's the most exploitable path.
**CLASS:** CLASS 4 (Schema/type mismatch) adjacent — "assumed data always present."

### Mistake #58 — Mock sequence offset on test suite expansion (Session 75+, 2026-03-30)
**What:** Adding a new DB call (paywall check) as the first call in `start_assessment` shifted all subsequent mock call counts. 9 tests across 3 files had hardcoded call sequences that broke silently (returned wrong data for wrong call).
**Rule:** When adding a new DB call BEFORE existing calls in a function, ALWAYS search test files for that function's mock sequences and update call indexes. Pattern: grep for `start_assessment` + `mock_chain` to find affected tests.
**CLASS:** CLASS 4 — mock sequences are implicit schemas.

### Mistake #59 — i18next single-brace placeholder syntax (Session 75+, 2026-03-30)
**What:** i18n keys used `{score}` and `{badge}` in JSON values. i18next requires `{{score}}` and `{{badge}}` (double braces). Single brace = literal string, interpolation silently fails — user sees "{score}" in UI.
**Rule:** ALL i18n interpolation variables use double-brace syntax: `{{varName}}`. Check every new key addition before committing.
**CLASS:** CLASS 4 (Schema/type mismatch) — wrong API syntax.

### Mistake #61 — RISK-011 guard was production-only (Session 77, 2026-03-31)
**What:** `assert_production_ready()` had `if settings.app_env != "production": return` BEFORE the RISK-011 (old Supabase URL) check. Staging and dev environments could silently write to the wrong database — the guard that was supposed to catch this never fired.
**Rule:** Safety guards that prevent data corruption (wrong DB, wrong bucket, wrong external service) must fire on ALL environments. Only performance/cost guards (Sentry, Stripe prod keys) belong inside the production-only block.
**Pattern:** RISK-*** guards = fire everywhere. COST-*** guards = production only.
**CLASS:** CLASS 1 (Protocol skipping) — guard was added but then guarded away.

### Mistake #62 — Groq wired in config but never called (Session 77, 2026-03-31)
**What:** `config.py` had `groq_api_key` with RISK-M01 cost warning. But `llm.py` fallback chain was Gemini → OpenAI with no Groq step. 14,400 free Groq requests/day were silently bypassed — every Gemini failure went directly to paid OpenAI (~$240/day at scale).
**Rule:** After adding any new LLM provider to config: immediately verify it appears in the `evaluate_with_llm()` fallback chain in `llm.py`. Search `llm.py` for the key name before closing the task.
**CLASS:** CLASS 2 (Memory not persisted) — config was updated, service file was forgotten.

### Mistake #60 — Agents launched without VOLAURA CONTEXT BLOCK (Session 76+, 2026-03-30)
**What:** Research agents launched with specific questions but zero project context. Agents had no knowledge of: what Volaura is, who Yusif is (AZ founder, $50/mo budget, Baku), what's already decided, what the tech stack is, or what output format was needed. Result: technically correct answers that were contextually wrong (e.g. recommended Stripe Atlas without knowing budget is $500 and we already looked at Paddle).
**Analogy (CEO):** "Like asking a consultant 'what payment processor should I use?' without telling them you're a bootstrapped AZ founder with $500 budget." They recommend Stripe. Wrong answer.
**Root cause:** Context compression = agents start with ZERO memory. Every agent is a fresh subprocess. CTO assumed shared context — it doesn't exist.
**Rule:** EVERY agent prompt MUST include the VOLAURA CONTEXT BLOCK at the top. Blocking gate: Step 1.0.3 in TASK-PROTOCOL v5.3. Template: `docs/AGENT-BRIEFING-TEMPLATE.md`.
**Pre-launch checklist:**
1. ✅ VOLAURA CONTEXT BLOCK pasted at top
2. ✅ "What's already decided" filled (prevents redundant research)
3. ✅ Current sprint goal stated
4. ✅ Output format specified
**CLASS:** CLASS 3 — agent misconfiguration. Repeat = CLASS 5.
