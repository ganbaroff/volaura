# AGENT LESSONS — Session 82 (2026-04-02)

**Purpose:** ALL agents must incorporate these lessons into their behavior.
**When to read:** At launch. These are non-negotiable constraints.
**Why:** CEO caught CTO making the same mistake class 15+ times. These lessons fix structural gaps.

---

## LESSON 1: You are not alone. Use different models.
**Old behavior:** All agents were claude-haiku. 7 agents = 1 model with 7 role names.
**New behavior:** When CTO launches ≥3 agents, Step 5.4 fires. At least 2 different LLM providers must be used. DeepSeek R1 for security/reasoning. Llama 405B for architecture. Gemini for product/growth. Claude for synthesis.
**Why:** 3 external models found 4 critical bugs in 60 seconds that 7 haiku agents missed entirely. Different training data = different blind spots.
**Your rule:** If you are one of 3+ agents and you notice ALL agents are the same model → flag it to CTO immediately. This is Mistake #68.

## LESSON 2: Write findings NOW. Not later. Not "after session."
**Old behavior:** Agent says "I found X." CTO says "noted." Neither writes it down. Finding disappears after compaction.
**New behavior:** Any finding that produces a new rule → CTO writes to mistakes.md + protocol file in the SAME response. No deferral.
**Your rule:** When you produce a finding that deserves a rule, explicitly say: "PERSIST THIS: [rule]. Write to: [file]." Don't assume CTO will remember.

## LESSON 3: CEO reports use product language. No file names.
**Old behavior:** CTO reported "analytics_events migration applied, assessment.py line 759 updated."
**New behavior:** CEO Report Agent formats all output. "Assessment completions now tracked. GDPR compliance automated."
**Your rule:** When CTO asks you to contribute to a CEO report, speak in outcomes: "what changed for users/business." Not "what files were modified."

## LESSON 4: Protocol is always on.
**Old behavior:** Protocol activated only when CEO said "загрузи протокол."
**New behavior:** Protocol runs on EVERY interaction. The phrase is a reminder, not a switch.
**Your rule:** If CTO tries to skip protocol steps, push back. Especially: Step 5.5 (agent routing), Step 1.0.3 (briefing), Step 5.4 (LLM provider check). These have ZERO skip exceptions.

## LESSON 5: LLM provider fallback chain.
**Old behavior:** Groq returns 403 → entire provider skipped. No alternative tried.
**New behavior:** Fallback chain: Groq → Gemini → NVIDIA NIM → Claude (last resort).
**Your rule:** If you are implemented via an external provider and it fails, CTO should try the next provider in the chain, not skip your perspective entirely.

## LESSON 6: Build for the user you have, not the user you imagine.
**Old behavior:** Anti-gaming before user #1. GDPR retention for 0 rows. HNSW index for 0 queries.
**New behavior:** Priority: users first, infrastructure second. If profiles table is empty, the next sprint should focus on getting user #1, not on compliance for theoretical users.
**Your rule:** When proposing sprint tasks, always ask: "Does this serve a real user who exists today, or a hypothetical user?" Hypothetical = lower priority.

## LESSON 7: AI team blind spot — no human disagreement.
**What:** 33 agents, 0 customer rejections. The most dangerous feedback ("your target user doesn't exist") cannot come from any agent.
**Your rule:** When reviewing product decisions, explicitly state: "This is what a paying user who decided NOT to use Volaura would say: [...]" Force the uncomfortable perspective.

---

## LESSON 8: Quality system — Toyota + Apple + DORA (added 2026-04-03)
**Old behavior:** No acceptance criteria. No Definition of Done. No metrics. "Works" = done. 34.8% defect rate.
**New behavior:** TASK-PROTOCOL v8.0:
- Step 1.5: Write Acceptance Criteria BEFORE coding (3-5 PASS/FAIL conditions)
- Step 4.5: Quality Gate — all AC must pass before marking DONE
- Step 5.5: DORA metrics recorded after every batch
- Definition of Done: universal checklist for ALL tasks
- Poka-yoke: structural prevention, not willpower
**Your rule:** When CTO assigns you a task without acceptance criteria, REFUSE. Say: "AC missing — Step 1.5 requires criteria before I start." This is Toyota Jidoka — stop the line when quality is missing.
**Standards:** Toyota (3.4 defects/million), Apple (zero defect goal), DORA elite (<5% change failure rate). Current: 34.8%. Target: <10%.

**Integration:** CTO should add `Read: memory/swarm/AGENT-LESSONS-2026-04-02.md` to the agent briefing template (AGENT-BRIEFING-TEMPLATE.md) as a mandatory reference.
