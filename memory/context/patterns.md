# Patterns That Work for Volaura

Purpose: Reusable knowledge about what works in this project. Read at session start.

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
