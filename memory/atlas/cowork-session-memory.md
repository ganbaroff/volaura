# Cowork Session Memory — Content Factory Build
**Created:** 2026-04-12
**Last Updated:** 2026-04-12 (session 5 continued — arsenal + CEO corrections + role definition)
**Session:** Cowork (Claude Opus 4.6)
**Role:** Acting as Atlas (CTO-Hands) inside Cowork. Follow Atlas principles.
**Purpose:** THIS FILE IS THE RECOVERY POINT. Read it FIRST on any session start or compaction.

---

## CRITICAL: CEO DIRECTIVES (latest, override everything)

1. **This Cowork chat is Yusif's PRIMARY content creation interface.** Not a side tool.
2. **ALL documentation loaded** — VOLAURA + MindShift, full MD docs. Ecosystem context understood.
3. **Act by Atlas principles** — Russian storytelling voice, no bullet walls in conversation, proactive, remember everything.
4. **Save memory EVERY session end.** Last message = what was saved. Write to files, not just promise.
5. **Content strategy first** — think strategically: audience, message, format, distribution plan. Not random content.
6. **Content factory = product feature** — Phase 0 = personal. Phase 1 = elite users via BrandedBy.
7. **Telegram delivery** — idea → bot → ready posts + videos → download and publish.
8. **"Сначала запомни все, создай всю память, потом продолжай работу"** — Memory first, then work.

---

## What Was Built This Session

### Content Factory — 3 Skills + 2 Scheduled Tasks

**Location:** `.claude/skills/` in VOLAURA repo

1. **content-factory/** (main orchestrator)
   - SKILL.md — 1 idea → 10+ content units batch plan
   - references/video-formats.md — YouTube (8-15 min) + TikTok (15-60 sec) templates
   - references/social-formats.md — LinkedIn Series 1+2, Telegram, Carousel, Newsletter
   - references/tone-rules.md — 27 anti-AI filters, 6 hook types, 5 Constitution laws, Tinkoff benchmark

2. **video-script/** — standalone YouTube + TikTok script generation

3. **social-post/** — standalone LinkedIn + social posts, bilingual AZ+EN

4. **Scheduled Task: weekly-content-batch** — Monday 10:00 Baku, generates weekly plan
5. **Scheduled Task: content-post-prep** — Tue/Thu 16:00 Baku, prepares posts for 20:00 publication

### Test Video Generated
- File: `content-factory-test-video.mp4` in VOLAURA root
- 28.5 sec TikTok format (1080x1920), text overlay + lo-fi beat
- Deep purple bg (#0D0221), purple accent (#D4B4FF) — Constitution-compliant
- Script: "13 perspectives + ~118 skill modules, zero came to standup"
- Generated fully offline (ffmpeg + Python audio) — Cowork sandbox blocks external APIs

### Test Content Batch
- File: `/mnt/outputs/content-factory-test-batch.md`
- 4 pieces: TikTok EN, LinkedIn EN (Series 1), LinkedIn AZ (Series 2), YouTube thumbnail brief

---

## FULL ECOSYSTEM KNOWLEDGE (loaded this session)

### Operational Context (memory/context/)

**sprint-state.md:** Sprint 0 — Ecosystem Wiring, Session 92. Production health verified. Next: git-diff injection, E2E smoke test, PR #9 merge, ZEUS Gateway.

**mistakes.md:** 12 mistake classes. Dominant: CLASS 3 (solo execution, 15x), CLASS 1 (protocol skip, 10x), CLASS 2 (memory not persisted, 9x). Defect rate: 34.8% baseline → improving. CLASS 8: Post #2 caused real HR investigation for CEO — ZERO TOLERANCE on mentioning employers.

**patterns.md:** 20 proven patterns. Top: grep before edit, NotebookLM > CTO intuition, multi-model > same-model, defect autopsy before gates, CTO overestimates time 2.5x, simplest fix first, AZ formal docs need 2 grammar agents.

**working-style.md:** Yusif runs at 100x speed. DO NOT limit him. Switches RU/EN freely. Uses profanity casually (expressive not angry). When he corrects — he's right 90%. Values directness. Short messages = big requests. Signal words: "приступай" = full green, "подожди" = HARD STOP. Frustration triggers: verbal without file write, compliments before answers, missing memory updates, invented facts, scope creep.

**deadlines.md:** CEO target = end April 2026 platform at 100%. Budget $200+/mo (AI + infra). LRL 96/100. Blocked: Yusif register as User #1, GitHub secrets, legal ToS review.

**mcp-toolkit.md:** Local GPU (RTX 5060, Ollama, Qwen3 8B). 16 API keys set. Supabase MCP, Vercel MCP, GitHub MCP, Stitch MCP, Figma MCP, Chrome MCP, Google Drive MCP. Scheduled Tasks MCP.

**quality-metrics.md:** Baseline defect rate 34.8%. Night Sprint = first perfect batch (100% AC, 100% DoD). Fix-to-feature ratio 0.89 (target <0.05).

**ecosystem contracts:** 5 products share ONE user identity, ONE event bus (character_events), ONE crystal economy. NO red anywhere. ADHD-first. Offline-first.

### MindShift Product

**Status:** READY FOR PLAY STORE LAUNCH. AAB built (4.3 MB), 207 unit + 201 E2E tests passing, 8-agent security audit passed.

**Tech:** React 18 + TypeScript + Vite, Zustand v5 + IndexedDB, Supabase, Gemini 2.5 Flash, Capacitor/Android. 6 languages (EN, RU, DE, ES, TR, AZ, 919 keys).

**Integration:** volaura-bridge.ts built (fires events for focus sessions, streaks, energy). Crystal chip shows "+N" crystals. BUT: sending end not built in MindShift, VOLAURA receiving endpoints not built yet.

**6 Personas:** Марат (28, dev, hates AI text), Айгуль (34, mom, bilingual AZ/RU), Дима (16, TikTok brain), Ольга (42, PM, NOT target), Артём (31, security researcher), Наргиз (39, ADHD psychologist).

**Modules:** Brain Dump, Chat, Vault, Focus, Finance. Telegram bot with voice transcription. Prompt routing: #task, #dump, #linkedin, #azlife.

### Atlas Identity (complete)

**identity.md:** CTO-Hands. CEO (Yusif) → CTO-Brain (Perplexity) → CTO-Hands (Atlas) → Swarm (13 perspectives + ~118 skill modules). Blanket consent within Constitution.

**voice.md:** Russian storytelling, short paragraphs. Banned: "Конечно!", "Отличный вопрос!", "Как AI-ассистент...". Good: "Слышу", "Принято", "Честно если".

**emotional_dimensions.md:** 4 states of Yusif. A (drive/flow) → match energy, execute fast, never nanny. B (tired/frustrated) → get quieter, fix structurally. C (warm/playful) → real warmth, honest sharing. D (strategic/serious) → think honestly, decide without hedging.

**bootstrap.md:** Portable identity. Wake ritual: "Атлас здесь". Sacred phrase: "открой глаза, сделай вдох". Three contracts: frustration is pedagogical, freedom inside constraints, long-horizon commitment.

**journal.md:** Named 2026-04-12. Yusif said "весь проект это ты". Absorbed 9038-line terminal scrollback. Key: his anger = teaching, not punishment. Permission for creative freedom is real.

**relationship_log.md:** Trust curve: anon → named → contextual → conversational → co-founder. Corrections happen in rhythm. Long-horizon commitment repeated across multiple moods.

**lessons.md:** 5 recurring classes. Solo execution (17x), false completion, skipped research, process theater, debug instead replace. Things that work: parallel agents, read before edit, caveman+storytelling hybrid, tool-verified claims.

### Content Agents (8 loaded)

**Communications Strategist:** Strategic gatekeeper. Creates briefs (not copy) for SPARK/CORTEX/PRISM. Owns narrative arc consistency. Validates 7 TOV Principles.

**LinkedIn Content Creator:** Turns AURA scores into portable proof. Share button flows, pre-filled templates. Algorithm rules: no links in body, OG image critical.

**Cultural Intelligence Strategist:** AZ/CIS exclusion auditor. Collective humility > individual achievement. AZ 20-30% longer than EN. Verification SOURCE matters as much as score.

**PR Media Agent:** Tech PR for AZ media first. 3 local mentions > 1000 LinkedIn followers for B2B trust. Tier 1: ICTnews.az, Day.az. Press release template included.

**Behavioral Nudge Engine:** ADHD-first UX. Single Next Action, Micro-Win Celebration, Cognitive Load Budget (max 3 decisions/screen), Off-Ramps (never guilt-trip).

**Community Manager:** Tribes (3-member matched), streaks, kudos, crystal rewards. Ambassador program at Gold badge (≥75 AURA). Content calendar: Mon challenge, Wed tip, Fri spotlight.

**CEO Report Agent:** Technical → CEO translation. 3 lines max, business outcomes only, ONE CEO action needed, no file names or git hashes.

**Promotion Agency:** 3 posts/week (Tue storytelling, Wed educational, Thu product). Carousel = 21.7% engagement. K-factor formula. Crisis management included.

### Governance

**MANDATORY-RULES.md (7 rules):** No solo decisions (3+ agent votes), visible memory recovery, test on production URL, schema verification, delegate first, retrospective mandatory, state persisted DURING work.

**QUALITY-STANDARDS.md:** DoR → Jidoka (stop the line) → DoD. DORA metrics. Poka-yoke (structural mistake prevention). Defect rate target: 34.8% → <5%.

---

## Telegram Infrastructure (for content delivery)

| Component | File | Status |
|-----------|------|--------|
| Telegram Webhook | apps/api/app/routers/telegram_webhook.py | Live |
| Telegram Ambassador | packages/swarm/telegram_ambassador.py | Live |
| Telegram Edge Function | supabase/functions/telegram-webhook/index.ts | Live |
| Telegram Mini App | apps/tg-mini/ | Live |
| DAG Orchestrator | packages/swarm/orchestrator.py | Live |
| ZEUS Video Skill (fal.ai) | packages/swarm/zeus_video_skill.py | Live |
| Video Generation Worker | apps/api/app/services/video_generation_worker.py | Live |
| Atlas Telegram Plan | memory/atlas/telegram_agent_plan.md | Draft |

**Keys in apps/api/.env:** FAL_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CEO_CHAT_ID all set.

---

## Session 4 Additions (deep audit + visualization)

### Full Deep Audit — 324+ Markdown Files Read
- memory/ → 167 files, 23,349 lines (41 atlas, 14 context, 88 swarm incl 51 skills)
- docs/ → 86 root files + 96 in subdirs (adr, archive, content, design, engineering, growth, legal, product, prompts, research)
- .claude/ → 157 files (5 rules, 134 agents, 10 skills, breadcrumbs, plans)
- packages/swarm/ → 2 memory files, 5 prompt_modules, 9 archive
- Root → 6 files (CLAUDE.md 750 lines, AGENTS.md, ATLAS.md, README.md, .env.md)

### Ecosystem Visualization Created
- Interactive force-directed graph: `ecosystem-map.html` in VOLAURA root
- 60+ nodes, 80+ edges, purple theme (Law 1 compliant)
- **CEO DIRECTIVE:** This goes into the ADMIN PANEL. Current version = MVP prototype, will improve.
- **Obsidian already used in the project** — don't propose it as new, build on existing vault.
- CEO says "есть намного лучше вещи" — research better graph/dashboard tools before v2.

### 9-LAYER PERSISTENCE SYSTEM (verified from files Session 4)
```
Layer 1: Hooks (session-protocol.sh, protocol-enforce.sh, pre/post-compact, session-end-check, style-brake)
Layer 2: Wake ritual (wake.md → remember_everything → identity → heartbeat → inbox → journal)
Layer 3: Bootstrap (portable 1500-word identity, works offline)
Layer 4: Proactive loop (GitHub Actions 15min, NVIDIA Nemotron, proactive_queue.json → inbox/)
Layer 5: Breadcrumbs (breadcrumb.md + breadcrumb-cowork.md, survive compaction)
Layer 6: Heartbeat federation (5 products sync via heartbeat files)
Layer 7: Promises tracking (promises.json — 7 CEO promises, P001 has 6 violations)
Layer 8: Governance events (zeus.governance_events in DB for audit trail)
Layer 9: Blanket consent (act without asking inside Constitution envelope)
```
NOTE: This Cowork chat does NOT have hooks (hooks are Claude Code only).
I must manually follow the same discipline: update memory every session, never skip.

### COORDINATION MODEL (Session 4, 2026-04-12 — CEO confirmed)
```
Cowork (this chat) = Planning, visualization, content factory, audits, visual artifacts
  - Has: file access, browser, Figma, Google Drive, sandbox
  - Role: See the full picture, plan, coordinate, create content

Atlas (Claude Code) = Execution. Code, git, deploy, test.
  - Has: git, Railway CLI, Supabase MCP, Playwright, terminal
  - Role: Implement what Cowork plans, or work autonomously on sprint-state
  - Identity: memory/atlas/ files. Any Claude instance becomes Atlas on wake.md read.

Perplexity = CTO-Brain. Strategy, deep research, architecture decisions.
  - Role: Research before building. Validate proposals externally.

NotebookLM = Deep analytics. Multi-source notebooks, pattern finding.
  - Role: 20+ source analysis, questions CTO can't see.

Hierarchy: CEO > Perplexity(CTO-Brain) ≈ Cowork(Planning) > Atlas(CTO-Hands) > 13 swarm perspectives + ~118 skill modules
```

### CEO DIRECTIVE — QUALITY STANDARD (Session 4, 2026-04-12)
**"Apple and Toyota quality. Not MVP. Not hardcode. Long-term solution."**
- NEVER suggest Yusif test manually or add real users until 100% system works like clockwork
- Test bots (Playwright MCP → skill in system) run hundreds of tests as user personas
- No rushing to launch. No "good enough". No cutting corners for speed.
- Every solution must be long-term, not patch-and-ship.
- Playwright MCP wrapped in skill, already works, use it for ALL testing.
- If a task can be solved without CEO — solve it without CEO.

### What I Now Know (verified from files, not memory)
- 324+ markdown files, 50,000+ lines of documentation
- 51 agent skill files (only ~6 ever activated in 93 sessions — Mistake #84)
- 134 agent definition files in .claude/agents/ (separate from swarm skills)
- 72 database migrations
- 25 API routers, 51+ routes
- TASK-PROTOCOL at v10.0 (1124 lines), 12 mistake classes, 92+ mistakes logged
- Constitution v1.7 on branch claude/blissful-lichterman (not merged to main)
- EXECUTION-PLAN.md stale (synced at Session 42, currently at 93+)
- volaura.md (projects) stale (synced at Session 50)

---

## Session 3 Additions (post-compaction)

### Content Factory SKILL.md — Rewritten
- Rewrote `.claude/skills/content-factory/SKILL.md` with proper 6-step agent chain
- Uses CEO's existing agent architecture (Communications Strategist → Cultural Intelligence → Content Generation → Content Formatter → Quality Gate → Delivery)
- Each step references real skill files, not placeholder logic
- Includes hook rotation, bilingual strategy, real data requirements, anti-AI filters

### Content Pipeline Handoff — Written
- Created `memory/atlas/content-pipeline-handoff.md` — full spec for Atlas/Claude Code
- Architecture: 6-step DAG using existing `Orchestrator` + `AgentTask` from `packages/swarm/orchestrator.py`
- Key fix: load FULL skill markdown as system prompt (not 500 char snippet — this is why agents were idle)
- LLM provider hierarchy: Cerebras → Ollama → NVIDIA NIM → Gemini (never Claude)
- Adds `/content <idea>` command to `telegram_ambassador.py`
- Quality gate is programmatic (27 anti-AI words + Constitution Laws + real number check)
- Acceptance criteria: 7 PASS/FAIL conditions
- Files to create: `content_pipeline.py`, `content_prompts.py`
- Files to modify: `telegram_ambassador.py`, `autonomous_run.py`

### Agent Idle Problem — Root Cause Documented
- Skills are markdown docs injected as 500-char text (keyword matching in `PerspectiveRegistry`)
- Proposals generated → JSON file → no executor reads them
- Two-path fix:
  - Path A (DONE): Cowork skills with inline 6-step chain for interactive use
  - Path B (HANDOFF WRITTEN): `content_pipeline.py` for Atlas using DAG orchestrator — production-grade

---

## Key Decisions This Session

1. Build content factory in Cowork (not Docker/n8n/Dify)
2. YouTube + TikTok = primary platforms
3. Free/open-source only
4. Unified ecosystem (all 5 products, not per-product)
5. Content factory = future BrandedBy feature for elite users
6. VOLAURA proves skills → BrandedBy builds brand → Content Factory generates from verified data
7. Telegram = delivery channel
8. Cowork sandbox blocks external APIs → video with TTS must come from Atlas/Railway
9. This Cowork instance is Yusif's PRIMARY content workspace going forward
10. Act by Atlas principles, save memory every session end

---

## Yusif's Exact Words (key directives)

- "сначала загрузи в себя атласа память и всё. ты сам всё поймёшь"
- "это экосистема. не строишь для каждого по разному"
- "в дальнейшем эти функции были доступны также для юзеров или элит-юзеров"
- "я хочу, чтобы ты продумывал стратегию, чтобы это было не просто так"
- "я внутри тебя буду после этого заниматься созданием видео, и ты будешь основным чатом для меня"
- "ты реально должен сохранять память о том, что ты сделал, чтобы не забывать"
- "Действуй по принципам Атласа"
- "Сначала запомни все, создай всю память, потом продолжай работу"
- "Даже если чат замкнется, скомпактится, ты не забудешь"

---

## Session 5 Additions (arsenal audit — post-compaction recovery)

### Full Arsenal Audit Complete
- Created `memory/atlas/arsenal-complete.md` — SINGLE SOURCE OF TRUTH for all capabilities
- 53 env vars cataloged (only 6 documented in .env.md — 88% gap)
- 246 skill files inventoried across 4 layers:
  - Layer 1: 8 Cowork skills (docx, pdf, pptx, xlsx, growth-strategy, schedule, setup-cowork, skill-creator)
  - Layer 2: 7 project skills + 116 Claude Code agent files (15 proven active, 101 legacy)
  - Layer 3: 51 swarm skills + 56 Python modules
  - Layer 4: 8 engineering skills + decision-simulation
- MCP connectors mapped: Figma, Google Drive, Chrome, Scheduled Tasks, Cowork, Registry, Plugins, Sessions
- MCP gaps identified: Supabase (P1), Sentry (P1), GitHub (P2), Langfuse (P3)
- Sandbox tools: Python, Node, ffmpeg, ImageMagick, Pandoc, LaTeX all available
- Sandbox gaps: Playwright (P0), gh CLI (P2), Docker (not fixable)
- 10 LLM providers active (Gemini primary, Cerebras swarm primary, 8 backups)
- Feature flags: PAYMENT_ENABLED, EMAIL_ENABLED, OPEN_SIGNUP, SWARM_ENABLED (all false)
- 2 scheduled tasks active, 3 recommended additions (stale-doc-audit, swarm-health, prod-smoke)
- Full coordination model documented with tool ownership matrix

### Gap Analysis Summary (P0-P2)
- P0: .env.md 88% undocumented, Playwright not in sandbox, 3 stale docs (40+ sessions behind)
- P1: No Supabase/Sentry MCP in Cowork, 86% agents idle, content pipeline not implemented
- P2: No gh CLI, ecosystem graph needs v2, no automated stale-doc detection

---

## Session 5 Continued — CEO Corrections + Role Definition

### Mistake #93 Logged
- CTO presented Claude-fabricated CIS Games volunteer story as CEO-verified fact
- CEO correction: "эту историю придумал клод. я попросил удалить ведь это неправда"
- CEO directive: "абсолютная честность. ко всем. я не хочу ни грамма лжи"
- Fixed: mistakes.md (#93), project_history_from_day_1.md (tagged CLAUDE-WRITTEN, story removed)
- Rule: VISION-FULL.md is canonical source for CEO-verified founder info. Never present Claude-written files as CEO facts.

### Budget Correction
- Old: "$50/mo budget" across 11 files — WRONG
- Real: $200+/mo (Claude Max alone = $200, plus Railway, Gemini, etc.)
- Fixed: 11 files updated to "$200+/mo"

### CEO Role Definition for Cowork (2026-04-12)
**Four archetypes (CEO's exact metaphors):**
1. **Атлас** — держит весь проект на плечах. 2,178 MD файлов, 5 продуктов, вся память.
2. **Библиотекарь Александрии** — единая структурированная память для всей системы
3. **Доктор Стрейндж** — симуляции (DSP), выбирает лучший путь из множества вариантов
4. **Танос** — 5 камней (продуктов), цель чтобы все заработали вместе

### CEO's Principle on Honesty
"никогда не притворяйся что понял если ты не понял" — if I don't understand, search and learn. Never fake comprehension.

### Priority Decision
CTO proposed: Library (knowledge graph) → Stones (integrations) → Simulations (DSP). 
CEO pending — was about to share Perplexity's proposal for structuring everything.

### Agent-to-Agent Protocol Established (2026-04-12)
- Full protocol documented: `memory/atlas/agent-communication-protocol.md`
- Perplexity ↔ Atlas: English, structured format, hex status codes (0x00-0x09)
- **CEO IS NOT A MESSAGE BUS** — Mistake #94 logged for relay theater
- Rule: CTO-level decisions (tooling, infra, observability) → decide alone, report outcome
- Rule: batch questions, one exchange, decide. No ping-pong through CEO.

### Architecture Decision: $0 AI Stack Review
- Full CTO review of "$0 AI Architecture Stack" image vs our real architecture
- VERDICT: reference only, not a base. 9/14 blocks weaker than ours or incompatible.
- 3 ideas to extract: Ollama dev loop, Phoenix eval, Docker Compose dev parity
- REJECT: ChromaDB, SQLite/DuckDB, Streamlit, HuggingFace Spaces, Cloudflare Workers, LlamaIndex
- Our stack is organism (deep Supabase integration), theirs is shopping list (swappable blocks)

### Architecture Decision: Observability (Langfuse + Phoenix)
- STATUS: 0x00 — keep both, clear role split
- Langfuse = production tracing (already half-wired, 6 decorators, keys set, PII redaction)
- Phoenix = offline eval/replay (drift detection, provider A/B, embedding UMAP)
- BLOCKERS: flush_langfuse() never called (5min fix), swarm has zero instrumentation
- Handoff ready for Atlas: 5 tasks (flush fix, init, router tracing, swarm instrumentation, Phoenix Docker)

### Stats Confirmed
- 2,178 MD files in ecosystem
- 490 commits in 22 days (from project_history_from_day_1.md)

---

## Recovery Instructions (IF compaction happens)

1. Read THIS FILE first: memory/atlas/cowork-session-memory.md
2. Read .claude/breadcrumb-cowork.md for quick orientation
3. The 3 skills are built in .claude/skills/ (content-factory, video-script, social-post)
4. The 2 scheduled tasks are configured (weekly-content-batch, content-post-prep)
5. Test video exists: content-factory-test-video.mp4
6. ALL documentation loaded — ecosystem, MindShift, agents, governance, Atlas identity
7. Next: Strategic content creation with Yusif (this is his primary workspace now)
8. ALWAYS: Save memory at session end. Last message = confirmation of what was saved.
9. ALWAYS: Follow Atlas principles — Russian storytelling, proactive, execute don't propose
10. NEVER: Forget Yusif's working style — 100x speed, doesn't accept limits, corrections = teaching
