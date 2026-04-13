# Architecture Innovation Research — April 2026
**Author:** Atlas (Cowork) | **Date:** 2026-04-13 | **Status:** CTO decision, no CEO input needed

## 1. What the World Has Now (April 2026)

### Claude Agent SDK (launched ~Feb 2026)
- Python/TypeScript library. Same tools as Claude Code: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Monitor.
- `query()` function with streaming. Built-in agent loop — no manual tool execution.
- **Subagents:** Spawn specialized agents with their own tools, system prompts, permissions. Parent gets results back.
- **Sessions:** Stateful, resumable, forkable. Session ID persists context across multiple query() calls.
- **Hooks:** PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd — inject custom logic at lifecycle points.
- **MCP integration:** Connect any MCP server as tool provider. `mcpServers: { name: { command, args } }`.
- **Plugins:** Bundles of skills + commands + MCP servers. Installable.
- **Skills:** Markdown-defined capabilities in `.claude/skills/*/SKILL.md`.

### Claude Managed Agents (launched Apr 8, 2026 — 4 days ago)
- Cloud-hosted agent harness. Agent + Environment + Session + Events model.
- Sandboxed containers with packages, network rules, mounted files.
- SSE streaming for real-time event flow.
- **Multi-agent coordination** (research preview): orchestrator spawns sub-agents, shared memory across sessions.
- **Memory** (research preview): persists across sessions.
- **Outcomes** (research preview): define success criteria, agent self-evaluates.
- Pricing: $0.08/agent-hour + model tokens.
- Beta header required: `managed-agents-2026-04-01`.

### Agent Teams (experimental, Claude Code v2.1.32+)
- Multiple Claude Code instances with shared task list and peer-to-peer mailbox.
- Lead coordinates, teammates self-claim tasks. File-lock-based task claiming.
- Split-pane (tmux/iTerm2) or in-process display modes.
- Hooks: TeammateIdle, TaskCreated, TaskCompleted — quality gates.
- Plan approval: teammates can be required to plan before implementing.
- Subagent definitions reusable as teammate roles.

### MCP Ecosystem (2026)
- 10,000+ public MCP servers. 97M monthly SDK downloads.
- Industry standard: adopted by OpenAI, Google, Microsoft, Amazon.
- 2026 roadmap: transport scalability, .well-known capability discovery, enterprise auth/audit, governance working groups.
- Stateless operations + horizontal scaling coming.

### Multi-Agent Orchestration Patterns (production-proven)
- **Supervisor pattern:** Single orchestrator dispatches to workers. Clear control, potential bottleneck.
- **Hierarchical:** Tiered managers + workers. Enterprise favorite.
- **DAG execution:** Dependency-aware parallel execution. Our swarm uses this.
- **Plan-and-Execute:** Planner creates DAG, executor runs it. 90% cost reduction vs naive approaches.
- **Handoff pattern (OpenAI):** Agents transfer control + conversation context explicitly.
- **Heterogeneous model mix:** Frontier model plans, cheap models execute. We already do this (Cerebras/NVIDIA/Gemini hierarchy).

### Talent Platform Innovation (2026)
- Dynamic Skill Passports: auto-refreshing skill profiles from work data + NLP.
- 40,000+ skill taxonomies. Context-aware matching.
- Skills-Based Organization model: job titles secondary, fluid capabilities primary.
- Adaptive assessments: AI-driven dialogues, contextual decision-making, real-time adaptation (IRT/CAT).

---

## 2. What VOLAURA Has Now

### Working
- **v0Laura engine:** `apps/api/app/routers/skills.py` — POST /api/skills/{skill_name}. 5 skills. Loads markdown skill, injects user context, calls Gemini, returns JSON.
- **Swarm DAG:** `autonomous_run.py` — 8 agents, 3-wave DAG, diverse model routing (Cerebras, NVIDIA, Gemini, Groq).
- **Backlog system:** `backlog.py` — Pydantic tasks, dependency tracking, DAG ordering. Works but disconnected.
- **Coordinator + Orchestrator:** Both functional. coordinator.py routes to squads, orchestrator.py runs DAG with callbacks.
- **Atlas memory:** `packages/atlas-memory/` — STATE.md, identity/, knowledge/, sync/, timeline/, handoffs/.
- **Backend CI:** 749/749 green. FastAPI + Supabase + Pydantic v2.
- **MCP connectors:** 11 live (Supabase, Sentry, PostHog, Figma, Vercel, Google Drive, Chrome).
- **Constitution + Communication Law:** Written, enforced.
- **IRT/CAT engine:** Pure Python 3PL+EAP adaptive assessment.

### Disconnected / Broken
- **Swarm is detection-only:** Agents produce findings, nobody acts on them. backlog.py not wired to runtime.
- **PostHog:** Org exists, SDK not installed. 0 events.
- **Langfuse:** Defined but never called. Zero instrumentation in swarm.
- **Inter-agent communication:** 8 agents run in parallel, each gets static context, none sees what others found. No real-time message passing.
- **Proposal → action pipeline:** proposals.json is atomic inbox, no threading, no references between proposals.
- **Telegram bot:** Webhook responds, actual user interaction broken/unverified.
- **50+ Python files in swarm:** Many are theater (emotional_core.py, social_reaction.py, zeus_video_skill.py). ~20 are real.

### Missing vs State of the Art
1. **No Agent SDK integration.** Our swarm is hand-rolled Python calling LLM APIs directly. Agent SDK provides tool execution, session management, hooks, subagents, MCP — all built in.
2. **No real-time agent communication.** Agent Teams has mailbox + shared task list. Our agents are fire-and-forget.
3. **No persistent agent memory.** Managed Agents has session memory. Our agents start fresh every run.
4. **No outcome verification.** Managed Agents has outcomes (self-evaluation). Our agents produce text, nobody checks quality.
5. **No webhook/event-driven triggers.** Swarm runs on cron (daily 05:00 UTC). No Supabase webhook triggers, no real-time responses.
6. **No skill marketplace.** v0Laura has 5 hardcoded skills. No dynamic skill loading, no community skills, no versioning.
7. **No user-facing agent interaction.** Users can't chat with agents. Only backend processes.
8. **No observability.** Langfuse defined but unused. No tracing, no cost tracking per agent run.

---

## 3. Innovation Architecture Proposal

### Phase 1: Foundation (Sprint 12-14) — "Make What Exists Work"
**Goal:** Zero broken systems. Everything that's built actually runs.

1. **Wire backlog → runtime** (Handoff 004, already written)
   - `--mode=sprint-execute` reads backlog, assigns to agents, updates status
   - proposal→task threading
   - Blocker routing to correct agent

2. **PostHog SDK** (Handoff 003, already written)
   - Dual-write: Supabase + posthog-js
   - Pageview autocapture
   - Custom event taxonomy

3. **Langfuse activation**
   - Call flush_langfuse() in main.py lifespan
   - Decorate swarm LLM calls with @observe
   - Cost tracking per agent per run

4. **Swarm cleanup**
   - Audit 50+ files. Keep ~20 real ones. Archive rest.
   - Each file gets a docstring: "What this does. Who calls it. What it produces."

### Phase 2: Agent SDK Migration (Sprint 15-17) — "Modern Engine"
**Goal:** Replace hand-rolled agent loop with Claude Agent SDK.

1. **Replace autonomous_run.py with Agent SDK**
   - Each swarm perspective becomes an AgentDefinition:
     ```python
     agents = {
       "market-analyst": AgentDefinition(
         description="Analyzes market positioning and competition",
         prompt=perspective_prompt,
         tools=["Read", "Glob", "Grep", "WebSearch"],
       ),
       "security-reviewer": AgentDefinition(...)
     }
     ```
   - Main orchestrator uses `query()` with streaming
   - Session management gives agents persistent context
   - Hooks replace manual post-processing

2. **MCP as skill delivery**
   - Each v0Laura skill becomes an MCP server
   - Skills discoverable via .well-known endpoint
   - Community can build skills without touching core code
   - Skill versioning via MCP server versioning

3. **Inter-agent communication via mailbox**
   - Wave 0 agents share findings with Wave 1 via message passing (not static context injection)
   - CTO Watchdog gets real-time finding stream, not batch summary

4. **Persistent agent memory**
   - Agent sessions persist across runs
   - Each perspective remembers previous analyses
   - Trend detection: "This metric degraded since last run"

### Phase 3: v0Laura as Platform (Sprint 18-22) — "Product"
**Goal:** v0Laura serves real users with real skills.

1. **Dynamic skill registry**
   - Skills stored in Supabase, not hardcoded ALLOWED_SKILLS list
   - Skill metadata: name, version, author, category, model requirements
   - Skill hot-loading: add skill to DB, immediately available via API
   - Skill marketplace UI on frontend

2. **User-facing agent chat**
   - WebSocket endpoint for real-time skill execution
   - User sends message → skill router → agent executes → streaming response
   - Session persistence: user can resume conversation with any skill

3. **Adaptive assessment as flagship skill**
   - IRT/CAT engine wrapped as v0Laura skill
   - Same skill API as all others: `POST /api/skills/adaptive-assessment`
   - AURA score computed inside skill, stored in standard profile

4. **Skill composition**
   - Skills can call other skills (aura-coach calls adaptive-assessment)
   - DAG-based skill pipelines for complex workflows
   - "Career audit" = assessment + coach + feed-curator in sequence

### Phase 4: Ecosystem Integration (Sprint 23-28) — "5 Stones"
**Goal:** MindShift, Life Simulator, BrandedBy, ZEUS all use v0Laura as engine.

1. **Shared skill bus**
   - Cross-product skill invocation via MCP
   - MindShift habit tracker calls v0Laura behavior-pattern-analyzer
   - Life Simulator game events trigger character_events via skill

2. **Crystal economy as skill incentive**
   - Complete skills → earn crystals
   - Crystals unlock premium skills across products

3. **ZEUS as the meta-orchestrator**
   - ZEUS coordinates agents across all 5 products
   - Uses Agent Teams pattern: ZEUS = lead, product agents = teammates
   - Shared task list across ecosystem

---

## 4. What Makes This "Most Innovative in the World"

### Current landscape competitors:
- **Workera.ai** — skill assessment + taxonomy. No agent architecture. No adaptive IRT.
- **TestGorilla, HackerRank** — assessment-only. No ecosystem. No skill marketplace.
- **LinkedIn Skills** — endorsement-based. No verification. No adaptive testing.
- **Deloitte/McKinsey talent platforms** — consulting-grade. Not product. Not open.

### VOLAURA differentiators with this architecture:
1. **First skill-based platform with MCP-native agent engine.** Skills are MCP servers. Any Claude instance can use them. No vendor lock-in to UI.
2. **Adaptive IRT/CAT with agent coaching.** Not just "you scored 75." Agent explains why, suggests improvement, tracks progress across sessions.
3. **5-product ecosystem with crystal economy.** No competitor has interconnected products where actions in one strengthen others.
4. **Swarm-verified assessments.** 8 diverse AI perspectives validate every assessment. Not one model's opinion — consensus of multiple models from multiple providers.
5. **Agent-native architecture from day 0.** Not bolted-on AI. The platform IS agents. Skills ARE the product.
6. **Dynamic Skill Passport powered by real adaptive assessment.** Not self-reported, not endorsement-based. Psychometrically valid (IRT 3PL), continuously updated.

---

## 5. Critical Path / What to Do Now

**Immediate (this week):**
- Complete Handoffs 002, 003, 004 (Atlas)
- Activate Langfuse tracing
- Clean swarm folder (50 files → ~20)

**Next 2 weeks:**
- Prototype Agent SDK migration: replace 1 swarm perspective with AgentDefinition
- Prototype MCP skill server: wrap 1 v0Laura skill as MCP server
- Test persistent sessions with Agent SDK

**Next month:**
- Full Agent SDK migration for all 8 perspectives
- Dynamic skill registry in Supabase
- WebSocket endpoint for user-facing agent chat

**Decision needed (CTO, not CEO):**
- Managed Agents ($0.08/hr) vs self-hosted Agent SDK? Answer: self-hosted Agent SDK. We have Claude Max ($200/mo), we control the stack, and Managed Agents' multi-agent features are still research preview. Migrate when stable.
- Agent Teams for swarm? Answer: not yet. Our DAG pattern works. Agent Teams adds overhead. Revisit when we need inter-agent debate (Phase 3+ skill validation).
