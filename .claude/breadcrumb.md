# CTO BREADCRUMB — Live Working Memory
**Read this FIRST after any context compression.**

---

## NOW
**FULL ECOSYSTEM AUDIT — CEO запросил: SWOT, архитектура, структура, пробелы, agents, memory, функционал. Без спешки. С роем. Всё просмотреть.**

## SESSION 88 — FULL LOG (everything shipped)

### Commits on `claude/blissful-lichterman` (pushed, PR #12 merged to main):
- `8a4cedf` — fix: G9 leaderboard deleted, G15 counters 2000→800ms, G21+CL6 badge/crystals removed from complete page
- `3b3ce9f` — feat: CLAUDE.md Article 0 (Constitution supreme law) + shared-context updated
- `bcf69a0` — chore: sprint-state session 88

### Commits on `main` (pushed):
- `5c940a4` — feat: Ollama local GPU + ECOSYSTEM-MAP.md for 44 agents
- `4c2e612` — feat: agent memory chain wired (inject_global_memory + auto-consolidation + Global_Context.md)
- `9683324` — feat: Python↔Node.js bridge (autonomous_run.py → POST /event)

### Commits on claw3d-fork:
- `ccc0ef5` — fix: CLAUDE.md Law 1 colors (overloaded/error: red→purple/orange)

### Figma (B30q4nqVq5VjdqAVVYRh3t):
- "Screens" page created with 3 Constitution P0 screens:
  1. Energy Picker (Law 2) — 5 levels, AZ copy, shame-free
  2. Pre-Assessment Commitment Layer (G45) — AI disclosure + scenario choice + energy check
  3. Vulnerability Window (Rule 29) — DeCE evidence only, no badge/score/crystals
- "Design System" page had only color palette — screens were MISSING before this session
- Still needed: Dashboard, AURA page, Profile, Landing, Community Signal widget

### Swarm run results (real, not simulated):
- 6 agents, all Gemini 2.0 Flash (after dead-weight filter removed 9/15 providers)
- **Ollama registered** (qwen3:8b) but didn't participate — was brand new, no exam history
- Winner: path_b (30.3/50) — "Plan is premature and theatrical. Fix platform first."
- All agents agreed: stop pushing users on broken platform, fix 19 blockers first

### Memory files saved:
- `feedback_ollama_local_gpu.md` — ALWAYS try local GPU before external APIs
- `feedback_breadcrumb_protocol.md` — write state to disk before/during/after work
- `feedback_task_protocol_honest.md` — TASK-PROTOCOL: helps for arch, hurts for 80%
- `feedback_no_premature_users.md` — STOP saying "real users" when platform broken

### Key CEO directives this session:
1. "локальный GPU использовал?" → NO. Fixed: Ollama added to Python swarm.
2. "переписать CLAUDE.md вокруг конституции" → Done: Article 0 added.
3. "рой должен РЕАЛЬНО ЗНАТЬ" → Fixed: memory chain wired (was completely broken).
4. "обсуди с агентами план" → Done: swarm said plan is premature.
5. "хватит говорить про реальных пользователей" → Memory saved. Will not repeat.
6. "дизайн на фигма?" → Was 5% done. Created 3 P0 screens.
7. "агентам дал к фигме доступ?" → NO. Agents can't call MCP tools.
8. "конституция!" → Read Constitution before acting. 19 pre-launch blockers.

## CONTEXT (critical facts)
- Constitution v1.7 is supreme law: `docs/ECOSYSTEM-CONSTITUTION.md`
- Figma fileKey: `B30q4nqVq5VjdqAVVYRh3t`
- Provider hierarchy: Cerebras → Ollama → NVIDIA → Anthropic Haiku
- Two swarms: Python 44 (GitHub Actions) + Node.js 39 (Railway WebSocket)
- Bridge added but GATEWAY_SECRET not in Railway yet
- 19 pre-launch blockers (see Constitution Part 3)
- Other chat task: commit MindShift CLAUDE.md (in worktree, not committed)

## DECISIONS (irreversible)
1. Leaderboard page deleted (G9) — redirect to dashboard
2. Badge/crystals removed from assessment complete (G21+CL6)
3. Constitution is Article 0 in CLAUDE.md
4. Ollama priority 0 in Python swarm
5. inject_global_memory wired into engine.decide()
6. Python→Node.js bridge via POST /event
