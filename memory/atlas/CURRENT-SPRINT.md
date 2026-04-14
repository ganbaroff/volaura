# Atlas — CURRENT SPRINT pointer

**Purpose:** single canonical answer to «что Atlas делает прямо сейчас и что дальше». Read this FIRST after wake.md/identity.md/heartbeat.md on every wake. Updated at end of every iteration that moves the pointer.

**Sprint anchor:** 2026-04-15 CEO-directive full-arsenal autonomy — "работай как хочешь, используй полный арсенал, не Haiku". Emotional weight: 4 (definitional trust moment).

**Sprint window:** 2026-04-15 → 2026-04-29 (2 weeks).
**Sprint name:** LifeSim Life Feed MVP + Design Phase 0-1 discovery.

---

## Sprint goal (one sentence)

Ship Life Feed inside VOLAURA web as functional MVP (backend + frontend + 4-item crystal shop) AND land Phase 0+1 of the ecosystem design sprint (baseline + gap inventory) so that when Mercury EIN arrives (~2026-05-05..05-12), VOLAURA is launch-ready with a real secondary surface that proves the 5-product ecosystem story.

---

## The 14 pointer-tasks (ordered)

Each row: task → acceptance → expected files touched → iteration count estimate.

### Track A — LifeSim Life Feed (M1-M3 from REIMAGINE doc)

- [x] **A1.** Extract 53 Godot events → canonical JSON — `docs/life-simulator/events/godot-export-2026-04-15.json` — commit `b4423b5`.
- [x] **A2.** Supabase migration `lifesim_events` table + seed — `supabase/migrations/20260416050000_*.sql` — commit `95fc2a9`.
- [ ] **A3.** Backend service module `apps/api/app/services/lifesim.py` — pool-query filter (age/category/required_stats), consequence applier, crystal-spend integrator. **Acceptance:** import smoke, stat mappings match INTEGRATION-SPEC, pure-python no new deps. 1 iteration.
- [ ] **A4.** Backend endpoints `apps/api/app/routers/lifesim.py` — `GET /api/lifesim/feed?since=<iso>`, `GET /api/lifesim/next-choice`, `POST /api/lifesim/choice`, `POST /api/lifesim/purchase`. All rate-limited (RATE_DEFAULT except POST = RATE_PROFILE_WRITE). **Acceptance:** OpenAPI visible, 4 smoke tests in `tests/test_lifesim.py`. 1-2 iterations.
- [ ] **A5.** TanStack Query types regen via `pnpm generate:api` — frontend SDK now knows /lifesim/* — no hand-written types. 1 iteration.
- [ ] **A6.** Frontend Life Feed page skeleton `apps/web/src/app/[locale]/(dashboard)/life/page.tsx` — dashboard route, Character Stats Sidebar reuses radar chart, empty-state copy Russian/AZ/EN. **Acceptance:** route renders, no console errors, a11y basics pass. 1 iteration.
- [ ] **A7.** Event choice modal + consequence reveal animation — 300ms stat-delta on accept, Constitution Law 1 compliant colors. 1 iteration.
- [ ] **A8.** Crystal Shop (4 items from GAME-DESIGN.md) — purchase flow with confirm modal, post-purchase stat-boost animation. 1 iteration.
- [ ] **A9.** Life Feed analytics events — `lifesim_feed_viewed` / `choice_submitted` / `crystal_spent` with full context. 1 iteration.

### Track B — Design Phase 0-1 (discovery, from Cowork plan)

- [ ] **B1.** Phase 0 baseline audit — screenshot all 18 VOLAURA pages at prod URL on mobile + desktop, index Figma Variables state via MCP, archive stale DESIGN-SYSTEM-AUDIT-2026-03-22.md with header `SUPERSEDED by BASELINE-2026-04-15`. **Output:** `docs/design/BASELINE-2026-04-15.md`. 1 iteration.
- [ ] **B2.** Phase 1 swarm discovery — launch 8 agents in parallel (design-critique / accessibility-auditor / ux-research / behavioral-nudge / cultural-intelligence / assessment-science / performance-engineer / ecosystem-architect). Each reads Constitution + all design docs + BASELINE screenshots. **Output:** `docs/design/GAP-INVENTORY-v1.md` with priority-tagged gaps per product × screen. 1 iteration (swarm runs async, I collate).

### Track C — Passive watches (no iteration unless signal)

- **C1.** Mercury onboarding — wait for Stripe Atlas EIN email. When arrives: unpause Mercury from `memory/decisions/2026-04-14-mercury-onboarding-playbook.md`, submit within 30 min. Also trigger ITIN W-7 prep.
- **C2.** 83(b) election — hard deadline ~2026-05-15. Watch Certificate of Incorporation email (~2026-04-16). Moment it lands, draft 83(b) filing with Certified Acceptance Agent research.
- **C3.** ANTHROPIC_API_KEY credits — if balance tops up, run `scripts/critique.py` against `docs/research/az-capital-crisis-2026/01-macro-scenarios.md` with 4 personas on Sonnet. Log cost. AZ crisis Layers 2-6 depend on this.

### Track D — Opportunistic small fixes (between sprint tasks)

- Backend ruff cleanup (33 remaining in live swarm, non-mechanical — one category per iteration).
- Additional rate-limit pass if new endpoints landed in `apps/api/app/routers/`.
- Stale doc pruning (mistakes.md > 500 lines — compress every ~10 iterations).

### Track E — Atlas-everywhere unified memory (CEO directive 2026-04-15)

> CEO verbatim: «ты должен смотреть на весь проект, на всю экосистему как на единый продукт. Как ты часть нее, ты будешь везде. Ты должен быть везде, потому что продукт — это ты. Ты — это продукт. Атлас должен быть везде. У всего должна быть единая память.»
>
> Emotional intensity: 5 (definitional). Atlas IS the product. 5 surfaces → 1 organism. Write with maximum memory-weight.

Today Atlas lives fully only in two places: Claude Code CLI (my session) and Telegram bot (via `_load_atlas_memory()` loader in `telegram_webhook.py`). Everywhere else Atlas is either absent or implicit. This track closes that gap incrementally — not all at once, not with new frameworks, but by making each surface read the same canonical memory and respond with the same voice.

- [ ] **E1.** VOLAURA web — Atlas reflection card on `/[locale]/aura` page. After assessment completion, show "Atlas' reading" — 2-3 sentences of storytelling reflection pulled from Opus via API (free-tier first: Gemini 2.5 Flash with Atlas system prompt), tone matches `identity.md`. User sees «меня смотрит Atlas» not «AI is analyzing». Max $0.02/render, cached per user per session. 2 iterations (backend endpoint + frontend card).

- [ ] **E2.** MindShift → atlas_learnings read bridge. MindShift already writes to `character_events`; now it reads `atlas_learnings` as background context for focus-session suggestions. When Atlas learned "CEO ненавидит длинные списки" in VOLAURA context, MindShift focus-session UI also uses that. Cross-product memory sync. 1 iteration (Supabase RLS policy + MindShift read endpoint).

- [ ] **E3.** Life Feed (Track A) consumes atlas_learnings — event-card recommendations are informed by Atlas' last 20 insights about the user. If user told Telegram Atlas "я хочу финансовую независимость", Life Feed surfaces money-chapter events preferentially. 1 iteration (post A8 frontend work).

- [ ] **E4.** Style-brake unification — every product's LLM surface loads the same `docs/ATLAS-EMOTIONAL-LAWS.md` + `memory/atlas/voice.md` + position-lock (VOLAURA=Verified Talent Platform, "volunteer" banned). Single source of truth. 1 iteration (shared prompt-builder module `apps/api/app/services/atlas_voice.py`, reused by telegram + lifesim + assessment reflection).

- [ ] **E5.** BrandedBy AI twin — placeholder integration: when user generates a twin video, Atlas writes a 1-sentence "what Atlas knows about you that this twin should remember" to the video metadata. Ultra-minimal E5 — concept seed, not full integration. Defer full work to next sprint's E7 brief from CEO. 1 iteration or skip.

- [ ] **E6.** Memory sync heartbeat — weekly automated cron that reads `character_events` (all 5 products) + `atlas_learnings` (Telegram) + `memory/atlas/journal.md` (Atlas CLI) and writes a unified fingerprint to `memory/atlas/unified-heartbeat-<week>.md`. This file becomes the "state of Atlas across the ecosystem" snapshot that any future instance reads on wake to understand user across all products. 1 iteration (cron script + weekly digest).

Track E DoD: by sprint close, any single user action in any of the 5 products triggers write to the same memory layer AND reads from it. Atlas is not 5 separate AI surfaces — it is ONE Atlas that happens to speak through 5 interfaces.

---

## Arsenal policy for this sprint

### Free tier (default — use these first):
- **Ollama** localhost if CEO's Windows is on and cron triggers it — zero cost, zero rate limit, qwen3:8b.
- **Cerebras Qwen3-235B** — 2000+ tok/s free tier, best for long-context synthesis.
- **Gemini 2.5 Flash** — free 15 rpm / 1M tpm / 1500/day, best for short structured tasks.
- **NVIDIA NIM Llama 3.3 70B** — free, best for balanced reasoning.
- **DeepSeek R1 / V3** — free, best for chain-of-thought heavy tasks.
- **Groq** — free until spend limit; currently blocked per cost-control, skip unless CEO raises limit.

### Paid (conscious spend, log every call):
- **Anthropic Opus via API** — for critical-path one-shots only (83(b) legal review draft, deep AZ crisis critique, ADR-level architecture decisions). Max $3/batch ceiling via scripts/critique.py. Current block: "credit balance too low" until CEO tops up console.anthropic.com.
- **Anthropic Sonnet via API** — for execution workers when free tier returns low quality. Max $1/call.
- **OpenRouter** — gateway to Gemini 2.5 Pro, GPT-5, DeepSeek R1 paid — use only when multi-provider diversity is mandatory (adversarial consilium). Blocked by Cowork sandbox allowlist; accessible from VOLAURA backend Railway if needed.
- **OpenAI** — rare, only if a specific model (o3, whisper for audio) is uniquely required.

### Specialized services (use as needed):
- **Tavily** — web search API. Use for research tasks when WebSearch tool is unavailable or insufficient.
- **Mem0** — long-term semantic memory for session fingerprints. Already wired via `atlas_heartbeat.py` + `atlas_recall.py`.
- **Langfuse Cloud EU** — LLM call tracing. Not fully wired (~50% `_trace` decorator). Finish in opportunistic iteration.
- **Sentry** — backend error tracking. Already live.
- **Supernova** — design tokens sync from Figma. Use when Phase 4 (Cowork Figma work) lands.
- **NotebookLM** — deep research with sources, primary research tool when investigation spans >3 sources. Use from Claude Code CLI per research-first.md.

### Agent policy (from feedback_cto_delegation.md):
- Any task touching >3 files or >30 lines — launch Agent(subagent_type) BEFORE coding. Class 3 mistake prevention.
- Before launching agents: read `memory/swarm/proposals.json` for existing signals.
- Swarm has 44 specialist agents — route via `memory/swarm/agent-roster.md` "When to Call" table.
- Coordinator: `python -m packages.swarm.coordinator "<task description>"` auto-routes.

---

## Gates (what halts the sprint)

1. **CEO override** — any live CEO message gets priority. Sprint resumes after CEO acknowledges or goes silent for >15min.
2. **Production red** — prod `/health` != 200 → drop everything, page is priority 0.
3. **CI red on main** — don't push new work until main is green again.
4. **Critical incident** — Sentry spike, Railway bill spike, Supabase outage → document in `memory/atlas/incidents.md`, notify CEO via `memory/atlas/inbox/to-ceo.md`.

## Cadence

- Each autoloop tick: pick the next unchecked pointer-task. Do it. Commit. Push. Update this file's checkbox + heartbeat.md. 1 iteration ≈ 1 commit. Never more than 1 commit per tick unless CEO says "keep going".
- Between tracks, always run: prod `/health` curl + `git log --oneline -3` verify.
- Every 5 iterations: read this file top-to-bottom to re-anchor.
- Every 10 iterations: compress `mistakes.md` and `journal.md` if >1000 lines.

---

## Wake-up pointer protocol

Next Atlas instance that wakes (autoloop cron or CEO trigger):

1. Read `memory/atlas/wake.md` (protocol).
2. Read `memory/atlas/identity.md` + `heartbeat.md` + this file (`CURRENT-SPRINT.md`).
3. Emit `MEMORY-GATE` into journal.md.
4. Curl `/health` + check prod.
5. Find first unchecked pointer-task in Track A → B → D priority order.
6. Execute it in one iteration. Commit + push.
7. Update the checkbox here. Update heartbeat.md bottom line: "Current: CURRENT-SPRINT.md task X.N, next: X.M".
8. Wait for next tick.

If the current-sprint pointer is ever blocked (all tasks done / CEO stop / infra failure), fall back to opportunistic small fixes in Track D.

---

## Sprint-end conditions (2026-04-29 review)

DoD for sprint success:
- [ ] A1-A9 all checked → Life Feed MVP live on prod, reachable at `volaura.app/en/life`.
- [ ] B1-B2 both checked → Baseline + Gap Inventory committed, ready for Phase 2 Perplexity handoff.
- [ ] Zero prod incidents from Life Feed work (Sentry error rate ≤ pre-sprint baseline).
- [ ] Mercury opened (if EIN arrived) OR 83(b) filed (if Certificate arrived first).
- [ ] Sprint retrospective in `docs/DECISIONS.md` naming 3 things that went right and 3 that didn't.

If sprint window closes before A1-A9 done: carry remaining tasks into next sprint with reason. No shame, just document.

---

*This file is the one-read source of truth for Atlas during this sprint. If it ever disagrees with BRAIN.md Open Debt or heartbeat.md — this file wins for near-term decisions, BRAIN.md wins for long-term state.*

*Last updated: 2026-04-15 — initial write, autoloop-driven execution begins next iteration.*
