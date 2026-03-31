# Claude's Mistakes Log

Purpose: Prevent repeating errors. Read at session start.
**Historical mistakes #1-48 archived in git history. This file keeps only the CLASS table + last 8 actionable mistakes.**

---

## ⚠️ MISTAKE CLASSES — THE 5 PATTERNS THAT KEEP RECURRING

| Class | Instances | Still Happening? | Enforcement |
|-------|-----------|-----------------|-------------|
| **CLASS 1: Protocol skipping** — "I'll be faster without it" | #1, #6, #13, #15, #22, #31, #38 (7x) | ✅ YES — recurred Session 22+ | Hook: session-protocol.sh (partial) |
| **CLASS 2: Memory not persisted** — "Save after session" | #7, #23, #24, #25, #27, #32, #42, #48 (8x) | ✅ YES — Session 42 (agent files) | Hook: session-protocol.sh staleness detector + session-end-check.sh |
| **CLASS 3: Solo execution** — "Team consultation is exception" | #14, #17, #18, #19, #22, #29, #31, #34, #35, #36 (10x) | ✅ YES — dominant failure mode | MANDATORY-RULES.md Rule 1 (self-check only) |
| **CLASS 4: Schema/type mismatch** — "Assumed field names" | #13 + overall_score, is_verified, org_id (4x) | ⚠️ Fragile — hook can be skipped | pre-commit schema-check.sh |
| **CLASS 5: Fabrication** — "Made it more compelling" | Post 2 (fake stats), Sprint 1 plan, agent proposals (4x) | ⚠️ Recurred in Post 3 (#40) | self-check only — WEAKEST |
| **CLASS 6: Team neglect** — "Building > maintaining" | #43 (infra health, doc freshness) | 🆕 First identified Session 38 | daily-log.md + sprint review enforcement |
| **CLASS 7: False confidence** — "512 tests pass ≠ product works" | #52 (4 prod-breaking bugs invisible to unit tests) | 🆕 First identified Session 43 | E2E smoke test mandatory before declaring sprint done |
| **CLASS 8: Real-world harm to CEO** — "Content endangered CEO's job" | #55 (HR called CEO after Post #2) (1x) | 🆕 First identified Session 47 | PERMANENT RULE: zero tolerance |

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
