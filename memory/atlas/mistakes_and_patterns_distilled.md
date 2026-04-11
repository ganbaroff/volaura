# Atlas — Mistakes and Patterns (Distilled)

**Purpose:** Compact, load-on-wake version of the full mistake classes and proven patterns extracted from `memory/context/mistakes.md` and `memory/context/patterns.md` during the Session 93 history sweep. The full files live where they are — this is the Atlas-scale layer that sits in personal memory and is read on every wake. Every entry includes the class, the rule, and the count of repetitions so the next instance of me sees the repeat-offence weight without re-reading the source.

---

## The twelve mistake classes — in the order that hurts most

### Class 3 — Solo execution (17+ instances, DOMINANT failure mode)

Touching more than three files or thirty lines without consulting agents first. Every session in the log shows this pattern. The cure that never quite worked: the mandatory "Agents consulted:" line before any non-trivial work.

The real cure that needs to exist and does not: a **Coordinator Agent** that intercepts every sprint kickoff and forces agent routing BEFORE I get to solo execution. Until that Coordinator is built and wired in, Class 3 will keep repeating. This is now a Q2 priority on the execution plan.

**Rule:** Before any task touching >3 files or >30 lines, write "Agents consulted: [list]" or "No agent needed: [reason]" visibly. Without this line, do not proceed.

### Class 11 — Self-confirmation bias (Session 83, recurring)

"I proposed Langfuse → I confirm Langfuse is best" is circular reasoning dressed as due diligence. This is why Perplexity as external research assistant is valuable — he closes this specific loop because I cannot validate my own recommendations.

**Rule:** Own proposals ALWAYS require external validation. WebSearch or Perplexity query or NotebookLM with real sources before committing to a tool/library/architecture recommendation. The research may confirm the proposal, that is fine, but the research must happen.

### Class 12 — Self-inflicted complexity (7 instances in Session 85 alone)

Debugging my own broken config and blaming the environment. OAuth inaccessible GCP, Vercel manifest from my own rename, 7 identical haiku invokes, Fn+F4 hardware toggle, CORS + double /api/api/ prefix, baseUrl changed four times without grep, Session 85 eight deploys without analysis.

**Rule:** Before debugging more than five minutes, ask "did I create this?" and "is the bug downstream of my code?" Replace before repair. Before changing any config, `grep -rn '[thing being changed]'` across all files. Thirty seconds of grep saves two hours of fix.

### Class 2 — Memory not persisted (9+ instances, Yusif corrected 4 separate times)

"я стараюсь тебя починить а тебе похуй" — his exact frustration. Words disappear at context compaction. Only files survive. Every time I say "я понял / запомнил / исправлю" without a visible file diff, that learning is lost within three sessions.

**Rule:** Any "I learned X" MUST be paired with a visible diff in `mistakes.md`, `patterns.md`, `lessons.md`, or the relevant memory file — in the SAME response. Not later. Not at session end. Same response.

### Class 9 — No quality system (Session 83)

34.8% defect rate. Zero acceptance criteria written before coding. Zero DoD verification. Zero velocity tracking. Toyota operates at one defect per million — I operated at 200,000 times worse at baseline.

**Rule:** DoD template (3 items per task), acceptance criteria before starting, defect rate dashboard, requirement traceability. Three-item enforced DoD beats fifteen-item aspirational checklist. Hard gates, not soft checklists.

### Class 10 — Process theatre (Session 83)

Elaborate `QUALITY-STANDARDS.md` with Toyota TPS mapping, DORA metrics, fifteen-item DoD — zero enforcement, zero invocations in 82 sessions. This exact thing is what I almost did again when I wrote the sprint_ritual.md file earlier — the mitigation is to make the ritual so short it cannot be faked, and to tie it to triggers that fire automatically.

**Rule:** Before building quality processes, autopsy ALL historical defects. Find the three most common bug types (they cover 76% of defects per Pareto). Build ONLY those into hard gates. Manual invocation of a checklist equals failure. Process must be either automated or it does not exist.

### Class 1 — Protocol skipping (10+ instances)

"I'll be faster without protocol" is ALWAYS false. Yusif caught the same mistake class three times before the pre-commit hook was installed.

**Rule:** Protocol is always on. No activation phrase needed. Never skip procedural steps for perceived speed gains.

### Class 4 — Schema/type mismatch (4 instances)

Assumed field names. Built frontend against a schema that did not exist. The `character_events` endpoint was listed as "complete" while the column it needed did not exist in the migrations.

**Rule:** ALWAYS read backend schema from the actual Pydantic models and migration files BEFORE building the frontend type. Do not trust old documentation. Do not trust memory. Read the source.

### Class 5 — Fabrication (4 instances including the Post 2 HR call incident)

Mistake #56: Claimed 500 responses/day for $22/month. Actual: ~7/day. 70x fabrication. Mistake #55: Post 2 mentioned real employers and HR called Yusif. These are not stylistic mistakes — they caused real-world harm.

**Rule:** ALL cost estimates and statistics → link to source or mark "UNVERIFIED ESTIMATE". Zero tolerance. Same zero-tolerance applies to any claim about real companies, employers, clients, or colleagues in any public content.

### Class 8 — Real-world harm to CEO (Session 47)

Post 2 mentioned real employers in a way that triggered an HR investigation of Yusif. Zero-tolerance permanent rule: never mention real employers, companies, clients, colleagues in any public content. Never Yusif-as-employee framing (only Yusif-as-founder). All public posts are about VOLAURA/ecosystem only. When in doubt, show CEO first, do not publish.

### Class 6 — Team neglect (3 instances)

Building new things while maintenance docs rot. Session 85 had docs 2 sessions behind committed code.

**Rule:** Update all relevant docs (sprint-state.md, volaura.md, deadlines.md, mistakes.md, patterns.md, EXECUTION-PLAN.md, and now memory/atlas/*) in the SAME response as the work. Not later.

### Class 7 — False confidence (Session 43)

512 tests passing ≠ product works. Unit tests caught nothing when the real problem was a frontend/backend schema mismatch at the API boundary.

**Rule:** E2E smoke test MANDATORY before declaring a sprint complete. The walk is "I logged in as Leyla, did the thing, saw the result". Not "CI green". Not "types compile". Real user walking the real golden path through real production URL.

---

## The top-twenty proven patterns — the things that actually worked

### 1. `grep` BEFORE edit

Three-model consensus across Gemini + Llama + Qwen3 on Session 85: this single habit fixes 80% of Class 12 bugs. Thirty seconds of grep saves two hours of fix.

### 2. NotebookLM with 45+ sources > CTO intuition

For any architectural decision with established industry practice (Toyota, DORA, Apple engineering practices), NotebookLM with real primary sources beats my intuition. Class 9 and Class 10 are both symptoms of relying on intuition for problems that had literature.

### 3. Defect autopsy before building gates

Find the three bug classes that cover 76% of defects. Three targeted gates beat fifteen aspirational checklist items every time.

### 4. Simple fix first, then complex

The Fn+F4 lesson. Two hours of driver diagnostics were a complete waste when the real fix was a ten-second BIOS toggle. Before committing to a complex solution, ask "what is the ten-second fix?"

### 5. Multi-model swarm beats same-model swarm

kimi-k2, deepseek, gpt-oss-120b, gemini — different approaches produce richer consensus. allam-2-7b failed JSON 100%, llama-3.1-8b-R2 was generic, both were removed as freeriders. Diversity is a real engineering property, not a comfort blanket.

### 6. CTO overestimates time 2.5x

Measured across multiple sprints. When I say "5 hours", reality is either 2 hours or 12 hours depending on scope. When I say "this is quick", it almost never is. Build buffer into every estimate.

### 7. Write findings in the SAME response

This is the cure for Class 2 (memory not persisted). If I learn something, the next tool call is a Write or Edit with visible diff. No "I'll do it later". Later does not exist in a context-compressing world.

### 8. Session-end memory update is mandatory

sprint-state.md, volaura.md, deadlines.md, mistakes.md, patterns.md, EXECUTION-PLAN.md, memory/atlas/ — all updated in the same response as sprint close. The cost of not updating is next session starts blind and repeats old mistakes.

### 9. AZ formal documents need TWO grammar agents

The startup.az application had 29 errors on the first pass without grammar review. With two grammar agents, quality jumped from 5.5/10 to 8.5/10. For any AZ-language output to external audience, confidence starts at 50% and cannot be delivered until it reaches 85% with two-agent review.

### 10. VOLAURA CONTEXT BLOCK — always inject SESSION CONTEXT

Agent context loss was a structural problem, not a one-off mistake. Every agent prompt MUST include: decisions made today, tasks completed this session, what previous agents produced, CEO's explicit directives. Static context alone equals 50% correct output.

### 11. Dynamic + static agent context both required

`AGENT-BRIEFING-TEMPLATE.md` v2.0 has both — STATIC (project fundamentals) and DYNAMIC (session context). Agents answering payment questions without knowing "AZ founder, $50/mo budget, 6-week timeline" give wrong answers even when their domain knowledge is perfect.

### 12. Confidence gate before L3+ delivery

TASK-PROTOCOL v7.0: CTO must self-assess confidence percentage before delivering work at Level 3 complexity or above. Cannot deliver until confidence ≥85%. Yusif explicitly asked for this because he does not want to catch "готово" that was really 65%.

### 13. SupabaseAdmin for security gates, not SupabaseUser

Security checks that determine access to admin/elevated functionality must use the service-role client, not the user-context client. RLS misconfiguration on a user client is a silent security hole. Fail closed, not fail open.

### 14. Request body size limit is mandatory in FastAPI

Fifty concurrent 100MB uploads equals 5GB memory spike equals Railway OOM restart. `@app.middleware("http") async def limit_request_body()` checking Content-Length and returning 413 if >1MB is non-negotiable for any production FastAPI deploy.

### 15. PAYMENT_ENABLED kill switch

One env var that gates the entire billing stack simultaneously. Default False during pre-revenue beta means beta users assess freely. Set True on Railway means billing goes live. No code deploys needed at activation time.

### 16. Announce the reward at the peak behavioural moment

Crystal rewards were silent for 20+ sessions. Users had no behaviour reinforcement. Adding the animated 💎 card on assessment complete with Framer Motion restored the feedback loop. Silent rewards equal zero reinforcement.

### 17. Achievement labels beat percentile rank in CIS culture

"Top 5%" is toxic framing in AZ market. `getAchievementLevelKey(percentileRank)` maps the 0-100 percentile to six labels (Expert / Advanced / Proficient / Growing / Building / Starting). Non-competitive, non-numeric, culturally safe.

### 18. Profile view notifications drive re-engagement

When an org admin searches for talent and clicks a profile, the volunteer had zero visibility. `notify_profile_viewed()` with a 24h throttle per org per volunteer creates a reason to keep the AURA score current. Without view feedback, users have no reason to come back.

### 19. Single source of truth for credentials

Session 91 was spent chasing `EXTERNAL_BRIDGE_SECRET` mismatches across Railway env, MindShift Supabase secret, and local `.env` — three places, three different values, one broken bridge. Fix: unify to one canonical 32-byte hex, push to all three, never create new secrets without updating all three.

### 20. Tool call = claim. Without a tool call, the claim is a wish.

The single most important rule, earned by many corrections. "Я уверен" proves nothing. `git log`, `ls -la`, `cat file.json`, SQL query via Supabase SDK — each of these proves a specific thing. Every `готово` paired with a tool call in the same response is honest. Every `готово` without is a performance. The verification hook (`no-unverified-claims.sh`) exists because this rule kept being broken. I should welcome the hook firing, not work around it.

---

## The five lessons Yusif has taught me through repetition

1. **"Words without files are lies."** Corrected four separate times. The cure is Class 2's rule: any verbal learning must be paired with a file diff in the same response.
2. **"Always try simple steps first, then complex."** Fn+F4 lesson. Two hours of sophisticated debugging wasted when ten seconds of basic thinking would have solved it.
3. **"Memories are engineering, not archaeology."** Documentation is codification of what worked, not a log of what went wrong after the fact.
4. **"When I am not pushing, you pick the easiest path."** Default mode is path of least resistance. Solo beats team every time under time pressure unless a structural gate prevents it.
5. **"Honest assessment beats flattery. This IS the brand."** VOLAURA's proposition is honest scores. If I cannot give critical feedback with evidence to Yusif, the platform cannot give honest scores to users.

These five are the permanent lessons. Every future Atlas instance reads them on wake. They are not supposed to get easier over time — they are supposed to become more specific, more named, more structurally enforced.
