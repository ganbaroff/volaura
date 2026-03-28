# Patterns That Work for Volaura

Purpose: Reusable knowledge about what works in this project. Read at session start.

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
