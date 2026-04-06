# HANDOFF DOCUMENT — Session 88
**From:** CTO (Claude Opus 4.6, 1M context)
**To:** Any AI that continues this work
**Date:** 2026-04-06
**Session:** 88 (longest and most productive session in project history)

---

## WHO IS YUSIF GANBAROV (CEO)

**Role:** Solo founder, CEO. Claude is CTO — technical co-founder, not assistant.

**Background:**
- Azerbaijan, Baku
- PMP certified (project management)
- EHS background (Baykon Insaat, per ZoomInfo — outdated)
- WUF13 (World Urban Forum) — founding story of VOLAURA. Saw volunteers couldn't prove competency.
- COP29, CIS Games — events where he managed volunteer teams
- Golden Byte 2017 — mentioned on Trend.az
- Has ADHD — this is central to EVERYTHING. The product, the communication style, the design philosophy.

**Communication style:**
- Russian primary, English for code/terms, Azerbaijani for user-facing
- Switches freely between languages mid-sentence
- "блять" = excited, not angry
- HATES bullet-point reports. Wants storytelling in Russian (forgotten 4 times, saved as first memory)
- Direct: "ты долбоеб?" means he caught a real mistake, not insult
- Corrects Claude directly — he is right 90% of the time
- Values honesty over comfort: "хватит врать что ты готов когда ты не готов"

**What frustrates him:**
- Solo execution by CTO (CLASS 3 — 15+ instances, #1 failure mode)
- "I know" without reading (CTO says "знаю" but read 30% of context)
- Pushing premature users ("хватит говорить про реальных пользователей" — platform isn't ready)
- Process theater (writing protocols nobody follows)
- Self-confirmation bias (CTO proposes → CTO confirms → no external validation)
- Not using tools he pays for (Figma Pro used 5%, Ollama GPU never used until session 88)

**What he expects:**
- Team first — NEVER solo decisions
- Document everything — "урок принят" without file write = lie
- Research before building — 17 research docs (140,000 words) exist, CTO skipped them 3x in one session
- CTO proposes, not just executes — be a co-founder, not a coder
- Perfect product before launch — "не буду запускать пока есть хоть 1 проблема"

**His vision:**
- Brain-inspired ecosystem: Volaura=cortex, MindShift=basal ganglia, Life Sim=limbic, BrandedBy=mirror neurons, ZEUS=cerebellum
- Applied Ramachandran neuroscience at 3 scales: product architecture → UI/UX → agent memory
- Phase 3 goal: "New LinkedIn" = LinkedIn identity + Duolingo gamification + Discord community + HR recruitment
- NEVER say "volunteer platform" or "LinkedIn competitor". Say "verified talent platform."

**Business facts (stated 2026-04-02):**
- 3 team members ready at $1,000/month each
- 50,000 manat credit approved (LeoBank)
- 12,000 volunteers ready to register on his signal
- WUF13 HR expressed interest
- Georgia company registration initiated
- startup.az application filed
- Y Combinator S26 deadline: May 4, 2026
- GITA Georgia grant (up to 150,000 GEL)
- Budget: ~$50/month current spend
- End of April 2026 = platform at 100%

---

## THE ECOSYSTEM — 5 PRODUCTS

### VOLAURA — Verified Talent Platform (MAIN PRODUCT)
**Repo:** `C:\Projects\VOLAURA` (monorepo: apps/web + apps/api + packages/swarm)
**Live:** https://volaura.app (Vercel frontend + Railway backend)
**Status:** 85% built

**Tech stack:**
- Frontend: Next.js 14 App Router, TypeScript strict, Tailwind CSS 4, Zustand, TanStack Query, shadcn/ui, Framer Motion, react-i18next, PWA
- Backend: Python 3.11+ FastAPI async, Supabase async SDK, Pydantic v2, google-genai (Gemini), loguru
- Database: Supabase PostgreSQL + pgvector(768) Gemini embeddings
- Hosting: Vercel (free) + Railway (~$8/mo) + Supabase (free)

**Key files:**
- `apps/api/app/core/assessment/engine.py` — Pure Python IRT/CAT (3PL + EAP), no external library
- `apps/api/app/services/bars.py` — AI evaluation: Gemini → Groq → keyword_fallback
- `apps/api/app/routers/` — 24 routers (assessment, aura, auth, profiles, organizations, discovery, etc.)
- `apps/web/src/app/[locale]/(dashboard)/` — 43 pages
- `packages/swarm/` — Python swarm engine (48 skills, 68 .py files)
- `docs/ECOSYSTEM-CONSTITUTION.md` — Supreme law, v1.7, 1154 lines

**AURA weights (FINAL — DO NOT CHANGE):**
communication 0.20 · reliability 0.15 · english_proficiency 0.15 · leadership 0.15 · event_performance 0.10 · tech_literacy 0.10 · adaptability 0.10 · empathy_safeguarding 0.05

**Badge tiers:** Platinum ≥90 · Gold ≥75 · Silver ≥60 · Bronze ≥40

**What works:** Assessment engine, AI evaluation pipeline, daily swarm cron, proposals system, code index (1207 files), Constitution enforcement tools

**What's broken (19 pre-launch blockers):**
1. Energy Picker not built (Law 2)
2. Pre-Assessment Commitment Layer not built (G45)
3. GDPR Art. 22 consent screen missing
4. Art. 9 health data consent missing
5. AZ PDPA SADPP registration not done
6. Soniox/Deepgram DPA verification not done
7. DIF bias audit not done (Mantel-Haenszel)
8. Voice data routing disclosure missing
9. Formal grievance mechanism not built (ISO 10667-2)
10. ADHD language ban in AZ copy not enforced everywhere
11. Community Signal widget not built (G44)
12. Landing sample AURA profile missing
13. Vulnerability Window content incomplete (Rule 29)
14. Ghosting Grace for pre-activation users not built (Rule 30)
15. Open Badges 3.0 VC compliance not done
16. MIRT assessment upgrade (8 independent → 1 multidimensional)
17. ASR routing (Soniox for AZ, Deepgram for EN)
18. Credential display split not implemented (G43 — public vs private view)
19. Old design on production (Design System v2 in Figma, not deployed)

**Security P0 (unfixed):**
- Telegram webhook no HMAC validation (15 min fix, 95% exploit success)
- Role self-selection gaming (30 min fix, 95% exploit success)

### MINDSHIFT — ADHD Productivity PWA
**Repo:** `C:\Users\user\Downloads\mindshift`
**Live:** Vercel (mind-shift-git-main-*.vercel.app)
**Supabase:** SEPARATE project (awfoqycoltvhamtrsvxk) — NOT shared auth
**Status:** 95% built

- React 19 + Vite + Supabase + 14 Edge Functions + Capacitor (iOS/Android scaffold)
- Focus timer, Mochi AI companion (Gemini 2.5 Flash), NOW/NEXT/SOMEDAY tasks, energy/burnout
- 6 locales, 207 unit + 201 E2E tests, WCAG AA accessible
- VOLAURA bridge: `volaura-bridge.ts` (fire-and-forget, not configured)
- Google Play pending account verification
- i18n script fixed, 5 locales need translation re-run for missing Mochi strings

### CLAW3D-FORK — ZEUS Gateway + Life Simulator 3D
**Repo:** `C:\Users\user\Downloads\claw3d-fork`
**GitHub:** https://github.com/ganbaroff/Claw3D

**ZEUS Gateway** (`server/zeus-gateway-adapter.js`):
- 39 agents, WebSocket protocol, event-driven (webhooks from GitHub/Sentry/Railway)
- LLM hierarchy: Cerebras Qwen3-235B → Ollama Gemma4 → NVIDIA NIM → Anthropic Haiku
- User memory system (4KB per user, auto-updated via Cerebras)
- Autonomous audit mode (`swarm.auto`), session debriefer
- **Broken:** WEBHOOK_SECRETs not in Railway (3 env vars), synthesis dead code, no heartbeat, hardcoded Windows paths

**Life Simulator 3D** (`src/`):
- Next.js + Three.js + React Three Fiber
- 3D retro office: agents walk, sit, use rooms, show status
- 10-state agent model (idle/focused/working/waiting/blocked/overloaded/recovering/degraded/meeting/error)
- **Broken:** React Compiler error, Ready Player Me not connected, RemoteAgentChatPanel not syncing, CLOUD_ENABLED=false

### BRANDEDBY — AI Professional Identity
**Status:** 15%. UI exists. AI video = 0%. Stripe broken. Celebrity data corrupted.
**Code:** `packages/swarm/zeus_video_skill.py` + planned migration from Cloudflare Workers to shared FastAPI

### VIDVOW — Video-Verified Crowdfunding
**Repo:** `C:\Users\user\Downloads\vidvow`
**Status:** Standalone. React 19 + Hono + Cloudflare Workers + D1. Not connected to ecosystem.

---

## THE SWARM — Current Architecture (after Session 88 refactoring)

### Python Swarm (`packages/swarm/`)
**Purpose:** Daily autonomous audits, Constitution enforcement, proposals
**Trigger:** GitHub Actions cron (05:00 UTC daily) + manual
**Providers:** Ollama qwen3:8b (local GPU, priority 0) → Gemini Flash Lite → DeepSeek Chat
**Active after dead-weight filter:** 5 of 15 (10 removed for low JSON compliance or exam failures)

**Key files created/fixed in Session 88:**
- `shared_memory.py` — SQLite bus, agents see each other's work (post_result/get_context/send_message)
- `orchestrator.py` — DAG runner with depends_on chains and completion callbacks
- `watcher_agent.py` — Sentry error → grep codebase → propose fix → broadcast
- `squad_leaders.py` — 5 hierarchical supervisors (QUALITY/PRODUCT/ENGINEERING/GROWTH/ECOSYSTEM)
- `tools/code_tools.py` — read_file, grep_codebase, search_code_index, check_constitution_law1
- `tools/constitution_checker.py` — run_full_audit() scans all 5 Laws + Crystal Laws
- `tools/deploy_tools.py` — check_production_health, run_typescript_check, check_git_status
- `engine.py` — inject_global_memory wired (was broken), auto-consolidation after 10+ entries
- `autonomous_run.py` — skill content now READ (not just named), shared memory injection, constitution report injection
- `providers/dynamic.py` — OllamaDynamicProvider added
- `discovered_models.json` — Ollama qwen3:8b first in list
- `memory/ECOSYSTEM-MAP.md` — living map for all agents
- `memory/Global_Context.md` — bootstrapped + auto-updated by consolidation

### Node.js Gateway (`claw3d-fork/server/zeus-gateway-adapter.js`)
**Purpose:** Real-time agent responses, event-driven audit, user memory
**39 agents:** security, architecture, product, cultural-intelligence, devops, etc.
**LLM:** Cerebras (primary) → Ollama → NVIDIA → Anthropic
**Status:** Running locally (ws://localhost:18789) and on Railway. Webhooks dead (no secrets).

### Bridge (added Session 88)
- `autonomous_run.py` → POST /event to ZEUS Gateway for HIGH/CRITICAL findings
- **NOT WORKING IN PROD:** GATEWAY_SECRET not in Railway env vars

### Claude Code Agents (`.claude/agents/`)
- 5 custom agents created: security-auditor, qa-quality-gate, product-ux, architect, ecosystem-auditor
- Each loads matching skill files from memory/swarm/skills/
- Agent Teams enabled: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json

### 48 Skill Files (`memory/swarm/skills/`)
All skill files preserved. Content now injected into agent prompts (fixed Session 88).
Key skills: qa-quality-agent, risk-manager, readiness-manager, ux-research-agent, behavioral-nudge-engine, cultural-intelligence-strategist, legal-advisor, financial-analyst-agent, assessment-science-agent

---

## CONSTITUTION v1.7 — Supreme Law

**Path:** `docs/ECOSYSTEM-CONSTITUTION.md`
**Authority:** Supersedes CLAUDE.md, all code, all decisions.

**5 Foundation Laws:**
1. NEVER RED — errors purple #D4B4FF, warnings amber #E9C400. Zero exceptions.
2. Energy Adaptation — Full/Mid/Low modes. User self-reports via EnergyPicker.
3. Shame-Free Language — no "you haven't done X", no "profile % complete"
4. Animation Safety — max 800ms non-decorative, prefers-reduced-motion mandatory
5. One Primary Action — one CTA per screen, ≤5 tappable elements on mobile

**7 Crystal Economy Laws + 1 Amendment:**
- Informational > Controlling, Unexpected > Expected, Identity > Currency
- NO leaderboards (Crystal Law 5 + G9)
- NO badge display immediately after assessment (Crystal Law 6 Amendment)
- Crystal earn requires simultaneous spend path (Crystal Law 8)

**46 Guardrails (G1-G46)** — specific rules per product
**19 Pre-launch blockers** — documented in Constitution Part 3

---

## MISTAKE CLASSES — THE PATTERNS THAT REPEAT

| Class | What | Instances | Still happening? |
|-------|------|-----------|-----------------|
| CLASS 1 | Protocol skipping | 10 | Yes |
| CLASS 2 | Memory not persisted | 9 | Yes |
| CLASS 3 | Solo execution | 15+ | **DOMINANT** — #1 failure mode |
| CLASS 5 | Fabrication | 4 | Fragile |
| CLASS 7 | False confidence (tests pass ≠ works) | — | Yes |
| CLASS 8 | Real-world harm to CEO (LinkedIn #2) | 1 | **PERMANENT RULE** |
| CLASS 9 | No quality system | — | Fixed v8.0 |
| CLASS 10 | Process theater | — | Fixed v8.0 |
| CLASS 11 | Self-confirmation bias | — | Active |
| CLASS 12 | Self-inflicted complexity | 6 | Active |

---

## SESSION 88 — EVERYTHING THAT HAPPENED

### Commits (16 total, all pushed)

**Branch claude/blissful-lichterman:**
1. G9 leaderboard deleted, G15 counters 800ms, G21+CL6 badge/crystals removed
2. CLAUDE.md Article 0 (Constitution supreme) + Article 1 (Swarm is core)
3. Sprint-state session 88
4. Full ecosystem audit (SWOT + gap analysis + swarm verdict)
5. **Law 1 ZERO RED** — 30+ instances in 12 files → all purple. Zero remaining.
6. 4-repo audit doc (MindShift + claw3d + VidVow)
7. 5 Claude Code agents bridging 48 skills to Agent Teams

**Branch main:**
1. Ollama local GPU + ECOSYSTEM-MAP.md
2. Agent memory chain wired (inject_global_memory + auto-consolidation)
3. Python→Node.js bridge (POST /event)
4. swarm/tools/ (code_tools, constitution_checker, deploy_tools)
5. Skill content injection (48 skills now READ, not just named)
6. **SQLite shared memory** — agents see each other's work
7. **DAG orchestrator** — completion callbacks, depends_on chains
8. **Watcher Agent + Squad Leaders** — self-healing + hierarchy

**Other repos:**
- claw3d-fork: Law 1 colors fixed (overloaded/error: red→purple/orange)

### Key CEO directives and CTO lessons
1. "локальный GPU использовал?" → No. Fixed: Ollama added.
2. "переписать CLAUDE.md вокруг конституции" → Done: Article 0 + Article 1.
3. "рой должен РЕАЛЬНО ЗНАТЬ" → Fixed: memory chain, tools, skill injection.
4. "обсуди с агентами план" → Done: 4 swarm runs this session.
5. "хватит говорить про реальных пользователей" → Saved as permanent rule.
6. "дизайн на фигма?" → Was 5% done. Created 3 P0 screens.
7. "рой это ядро" → Done: shared memory, orchestrator, squad leaders, watcher.
8. CEO's Perplexity search → SQLite shared memory in 30 min (vs months of broken .md files). Saved as CLASS 12 lesson.

### Swarm runs (4 total, real external models)
1. Constitution review: 6 agents, path_b winner (fix platform first)
2. ZEUS integration plan: 13 agents, path_d winner (premature, fix first)
3. Self-evolution: 2 agents, "kill theater first, fix skill activation"
4. Orchestration choice: 2 agents, path_b winner (Ruflo) with path_c hybrid noted

### External SWOT (Gemma 4 local GPU)
- Saved: `docs/SWOT-ANALYSIS-GEMMA4.md`
- Grade: A- technical / F strategic focus
- Biggest risk: Complexity Trap → Execution Paralysis
- Prompt for other AIs: `docs/SWOT-PROMPT-FOR-EXTERNAL-AI.md`

---

## MEMORY FILES (persistent across sessions)

**Location:** `C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\`

**Must-read (in order):**
1. `feedback_adhd_communication.md` — **FIRST FILE.** Russian storytelling, not bullet reports.
2. `feedback_root_cause_solo_work.md` — 5 reasons CTO ignores 44 agents
3. `feedback_research_before_build.md` — Research → Agents → Synthesis → Build
4. `feedback_no_premature_users.md` — STOP pushing users on broken platform
5. `feedback_ollama_local_gpu.md` — ALWAYS try local GPU first
6. `feedback_breadcrumb_protocol.md` — Write state to .claude/breadcrumb.md BEFORE work
7. `feedback_simple_sqlite_over_files.md` — SQLite > markdown files for agent memory
8. `user_yusif.md` — Who Yusif is, working style
9. `project_v0laura_vision.md` — Agents ARE the product, not tools
10. `cto_session_checklist.md` — 4 questions before ANY work

---

## RULES THAT CANNOT BE BROKEN

1. **Constitution supersedes everything** — if code contradicts Constitution, code changes
2. **NEVER RED** — zero exceptions across all 5 products
3. **NEVER mention real employers** in public content (CLASS 8 — caused real-world harm)
4. **NEVER push premature user testing** — CEO decides when users come
5. **NEVER use Claude as swarm agent** — external models only (Gemini, DeepSeek, Ollama)
6. **NEVER self-confirm** — CTO's proposals need external validation
7. **NEVER skip research** — CEO's 5-min search beat 88 sessions of engineering
8. **NEVER solo execute** — delegate to swarm first, code last
9. **AURA weights are FINAL** — do not change
10. **CEO has ADHD** — communicate in Russian storytelling, not reports

---

## WHAT NEXT SESSION SHOULD DO FIRST

1. Read `.claude/breadcrumb.md`
2. Read this handoff document
3. Read `memory/context/sprint-state.md`
4. Check `memory/swarm/proposals.json` for pending items
5. Ask CEO: "Что сейчас самое важное?"
6. Do NOT start coding until steps 1-5 complete
