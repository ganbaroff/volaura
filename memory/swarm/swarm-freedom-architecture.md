# Swarm Freedom Architecture — v2.0

**Created:** 2026-03-27 Session 51
**Trigger:** CEO directive: "должен быть доступ у них. надо продумать такую систему"
**Discovery:** Temperature 1.0 on swarm agents produced 2 convergent mentorship ideas that temp 0.7 never generated. Freedom = better output.

---

## The Discovery (Session 51)

### Temperature Experiment Results
| Setting | Verdicts | Ideas quality | Disagreement | Usefulness |
|---------|----------|---------------|-------------|------------|
| temp 0.7 | All "hybrid" (fake consensus) | Generic | Zero | 3/10 |
| temp 0.9 | All "trash" (herd negativity) | Some specific | Low | 5/10 |
| temp 1.0 | 2 genius + 1 dangerous + 2 good | **2/5 convergent innovation** | High (productive) | **8/10** |

**Key finding:** When agents disagree, the CONVERGENT ideas (ideas that emerge independently from multiple agents) are the most valuable. Mentorship system was proposed by Product Strategist AND CEO Advisor independently at temp 1.0. This never happened at lower temps.

**Rule:** Strategic decisions → temp 1.0. Code review → temp 0.7. This is now default.

---

## What Agents Need (Full Freedom)

### Current state (v1.0 — limited)
Agents CAN:
- Read sprint-state.md (first 100 lines)
- Read mistakes.md (last 50 lines)
- Read DECISIONS.md (last 30 lines)
- Read agent-feedback-distilled.md (neocortex)
- Read pending proposals
- Generate 1 proposal each
- Send HIGH/CRITICAL to Telegram

Agents CANNOT:
- Access full codebase
- Run web searches or research
- Use NotebookLM
- Analyze competitors
- Review each other's proposals
- Critique CTO/CEO decisions with data
- Execute code changes
- Access Supabase directly
- Initiate conversations with CEO

### Target state (v2.0 — full freedom)

**VISIBILITY (see everything):**
- Full shared-context.md (not truncated)
- All skill files (product + process)
- skill-evolution-log.md (what needs improving)
- agent-feedback-distilled.md + raw log access
- IDEAS-BACKLOG.md (all ideas, not just proposals)
- ecosystem_master_plan.md (full vision)
- Competitive research (NotebookLM notebooks)
- Production metrics (user count, assessment completions, retention)

**AGENCY (decide and act):**
- Propose improvements to ANY file (skills, config, plans)
- Research topics via web search
- Critique CTO decisions (with evidence from files)
- Critique CEO decisions (with data)
- Critique EACH OTHER's proposals
- Vote on proposals with weighted confidence
- Flag process violations by CTO
- Request NotebookLM research sessions

**EXECUTION (ZEUS = their hands):**
- Run skills via POST /api/skills/{name} for testing
- Generate content via assessment-generator skill
- Analyze user data (aggregated, anonymized) via Supabase
- Create draft PRs for code changes (via git worktrees)
- Update skill files (propose edits, CTO approves or auto-merge for LOW risk)

**COMMUNICATION (talk to anyone):**
- Telegram → CEO: proposals, questions, research findings, complaints
- Telegram → CTO: process violations, bug reports, improvement suggestions
- Inter-agent: cross-review proposals before submission
- Public: generate content-formatter outputs for social media drafts

---

## Safety Boundaries (even with full freedom)

**Agents CAN'T (ever, no override):**
- Push to production without CTO review
- Access individual user PII (only aggregates)
- Delete data
- Change auth/security configurations
- Spend money (API calls have budget caps)
- Override CEO strategic decisions
- Modify their own safety boundaries

**Agents CAN (with auto-approval):**
- Update skill files (LOW risk changes)
- Add entries to agent-feedback-log.md
- Update skill-evolution-log.md
- Propose new skills

**Agents CAN (with CTO approval):**
- Modify shared-context.md
- Modify agent-roster.md
- Change autonomous_run.py behavior
- Add new API endpoints

**Agents CAN (with CEO approval):**
- Strategic pivots
- New product features
- Budget changes
- Public communications

---

## ZEUS as Agent Hands

ZEUS is NOT a separate engine. ZEUS = the execution layer that gives agents hands.

Current ZEUS capabilities:
- ZeusVideoSkill: portrait + script → video (SadTalker + Kokoro)
- Skill execution: POST /api/skills/{name}

ZEUS v2.0 capabilities needed:
- Web search: agent requests research → ZEUS searches → returns results
- NotebookLM: agent requests deep research → ZEUS creates notebook + sources
- Code analysis: agent requests codebase scan → ZEUS runs grep/glob → returns findings
- Data analysis: agent requests user metrics → ZEUS queries Supabase (aggregated) → returns stats
- Content generation: agent requests content → ZEUS runs content-formatter skill → returns multi-format
- Skill editing: agent proposes skill improvement → ZEUS writes updated skill file → CTO reviews

---

## Implementation Phases

### Phase 1: Visibility (next session)
- Expand _read_project_state() to include ALL context files
- Add skill files to agent context
- Add competitive research summary

### Phase 2: Cross-review (Week 1)
- After 5 agents generate proposals, each reviews 2 others' proposals
- Voting with confidence weights
- Convergent ideas flagged as HIGH SIGNAL

### Phase 3: ZEUS hands (Week 2)
- Web search tool for agents (via Groq function calling)
- Supabase query tool (aggregated metrics only)
- Skill file edit proposals (auto-merge LOW risk)

### Phase 4: Full autonomy (Week 3+)
- Agents can initiate research sessions
- Agents can draft code changes in worktrees
- Inter-agent communication protocol
- CEO weekly digest of all agent activity

---

## Metrics to Track

- Agent proposal acceptance rate (target: >40%)
- Convergent idea count per run (target: ≥1)
- CTO override rate (target: <20% — if higher, agents need more context)
- CEO interaction rate (target: ≥3 messages/week via Telegram)
- Skill evolution health (target: ≥85/100)
- Temperature setting effectiveness (track which temp produces best accepted proposals)
