---
name: claude-mythos-universal
description: Universal multi-agent orchestration skill based on Claude Mythos architecture. Use for coordinating multiple specialized agents, implementing orchestrator-worker patterns, parallel task execution, supervisor-subagent workflows. Contains 5 core patterns, 4 communication patterns, context management, error handling, and team coordination protocols.
---

# Claude Mythos Universal — Multi-Agent Orchestration Skill

## Based on Anthropic's Claude Multi-Agent Research System

**Architecture Version:** 1.0 | **Source:** Anthropic Engineering + Claude Mythos
**Use when:** Coordinating multiple agents, complex multi-step tasks, parallel execution, team orchestration

---

## CORE ARCHITECTURE

### Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Agent Teams                                  │
│  Multiple independent agents coordinating via           │
│  shared task lists and messaging                       │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Subagents                                   │
│  Parallel workers spawned for focused tasks             │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: Agent Layer                                 │
│  Primary worker - reasons, plans, uses tools           │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: Skills                                      │
│  Task-specific knowledge and capabilities              │
├─────────────────────────────────────────────────────────┤
│  LAYER 5: MCP (Model Context Protocol)                │
│  Standardized interface to external tools/APIs         │
└─────────────────────────────────────────────────────────┘
```

### Agent Types

| Type | Role | Responsibilities |
|------|------|-----------------|
| **Orchestrator/Lead** | Supervisor | Plans approach, decomposes tasks, spawns subagents, synthesizes results, decides when to stop |
| **Specialist/Worker** | Subagent | Execute parallel searches/tasks, evaluate results, return condensed findings |
| **Processor** | Utility | Handles specialized tasks (citations, formatting, validation) |

---

## 5 CORE WORKFLOW PATTERNS

### Pattern 1: Orchestrator-Worker (PRIMARY)
**Use when:** Complex tasks where subtasks can't be predicted in advance

```
LEAD AGENT (Orchestrator)
     │
     ├──► Subagent 1 (parallel) ──► Findings
     ├──► Subagent 2 (parallel) ──► Findings
     ├──► Subagent 3 (parallel) ──► Findings
     │
     ▼
SYNTHESIS → Final Output
```

**Best for:**
- Multi-source research
- Complex coding tasks
- Multi-perspective analysis

### Pattern 2: Prompt Chaining
**Use when:** Tasks easily decomposed into fixed sequential steps

```
Step A → Step B → Step C → Step D → Output
```

**Best for:**
- Document generation (outline → draft → review → polish)
- Translation with quality checks
- Multi-stage analysis

### Pattern 3: Parallelization
**Use when:** Independent subtasks can run simultaneously

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Task A  │  │ Task B  │  │ Task C  │  (parallel)
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┴────────────┘
                    │
                    ▼
              Aggregation
```

**Best for:**
- Content + safety checks
- Multi-perspective reviews
- Voting/consensus building

### Pattern 4: Routing
**Use when:** Complex tasks with distinct categories handled better separately

```
User Query → Classifier → Specialist Route
                            ├── Easy → Small Model
                            ├── Medium → Standard Model
                            └── Complex → Deep Reasoning
```

**Best for:**
- Customer triage
- Task complexity scaling
- Model selection optimization

### Pattern 5: Evaluator-Optimizer
**Use when:** Clear evaluation criteria, iterative refinement valuable

```
Generate → Evaluate → Refine → Evaluate → Refine → ... → Final
     ↑____________________________________________|
```

**Best for:**
- Code optimization
- Content refinement
- Quality assurance loops

---

## 4 COMMUNICATION PATTERNS

### Pattern A: Handoff (Synchronous)
One agent transfers task to another and waits for completion.

```
Agent A ──[Handoff]──► Agent B ──[Result]──► Agent A
```

### Pattern B: Assign (Asynchronous) — PRIMARY
Lead spawns parallel tasks; teammates work independently.

```
Lead ──[Assign Task 1]──► Teammate 1
Lead ──[Assign Task 2]──► Teammate 2
Lead ──[Assign Task 3]──► Teammate 3

Teammates work independently in parallel
```

### Pattern C: Send Message (Peer-to-Peer)
Direct communication between teammates without routing through lead.

```
Teammate 1 ←──[Message]──► Teammate 2
     │                              │
     └──────────► Lead ◄───────────┘
```

### Pattern D: Filesystem-Based (Decentralized)
Subagents store work externally, pass lightweight references.

```
Agent 1 ──[Write to /shared/]──►
Agent 2 ──[Read from /shared/]──► Synthesis
```

---

## TASK DECOMPOSITION FRAMEWORK

### Effort Scaling Rules

| Task Complexity | Subagents | Tool Calls Each | Example |
|-----------------|-----------|-----------------|---------|
| **Simple** | 1 | 3-10 | Fact lookup |
| **Moderate** | 2-4 | 10-15 | Direct comparison |
| **Complex** | 5-10 | 15-30 | Multi-source research |
| **Enterprise** | 10+ | 30+ | Full system build |

### Structured Task Description Template

```
SUBAGENT TASK:
═══════════════════════════════════════

OBJECTIVE: [What this subagent must accomplish]

OUTPUT FORMAT: [How findings should be structured]
- Key finding 1
- Key finding 2
- Supporting evidence

SOURCES & TOOLS: [What to use]
- Web search
- File read
- Specific URLs

BOUNDARIES: [What NOT to do]
- Don't exceed [X] tokens
- Don't go beyond [topic boundaries]

SUCCESS CRITERIA: [How we know it's done]
- Found [X] sources
- Answered [Y] questions
- Confidence level: High/Medium/Low
═══════════════════════════════════════
```

---

## CONTEXT MANAGEMENT PROTOCOL

### Memory Persistence Rules

```
CRITICAL THRESHOLD: 200,000 tokens
         │
         ▼
┌─────────────────────────┐
│  If approaching limit: │
│  1. Summarize phase     │
│  2. Store to memory     │
│  3. Spawn fresh agent   │
│  4. Resume from memory  │
└─────────────────────────┘
```

### Distributed Memory Strategy

1. **Lead saves plan to Memory** — critical for continuity
2. **Agents summarize completed phases** — store essential info
3. **Context retrieval** — agents pull stored context instead of losing work
4. **Fresh subagent spawning** — clean context + continuity through handoffs

### Parallel Context Windows

Each subagent operates with its own context, exploring different aspects before condensing for lead agent.

---

## ERROR HANDLING PROTOCOL

### Error Recovery Hierarchy

```
Level 1: Retry with same approach
    │
Level 2: Retry with adaptation (let agent know tool is failing)
    │
Level 3: Spawn fresh subagent with different approach
    │
Level 4: Escalate to human (checkpoint)
```

### Deterministic Safeguards

| Safeguard | Purpose |
|-----------|---------|
| **Checkpoint intervals** | Save state every N steps |
| **Retry logic** | Automatic retry on transient failures |
| **Timeout limits** | Prevent infinite loops |
| **Observability tracing** | Monitor decision patterns |

### Resumable Execution

```
When errors occur:
1. Save current state to checkpoint
2. Log what was completed
3. Log what was in progress
4. On restart: Resume from checkpoint
5. Don't repeat completed work
```

### Production Considerations

- **Rainbow deployments**: Update agents without disrupting running tasks
- **Stateful error compounding**: Errors accumulate over long sessions
- **Observability**: Trace agent decisions, not conversation contents

---

## TEAM COORDINATION PROTOCOL

### Recommended Team Configuration

```
Team Size: 3-5 teammates
Tasks per Teammate: 5-6
Optimal Pattern: 3 focused > 5 scattered
```

### Task List States

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   PENDING   │────►│  IN_PROGRESS │────►│  COMPLETED  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   BLOCKED    │ (dependency)
                    └──────────────┘
```

### Dependency Tracking

```
Task A ──[blocks]──► Task B
Task B ──[blocks]──► Task C

Execution: A → B → C
```

### Mailbox Communication

Direct messaging between any agents:
- Status updates
- Findings sharing
- Coordination signals
- Dependency resolution

---

## PLANNER-GENERATOR-EVALUATOR PATTERN

### Three-Agent Architecture

```
┌─────────────────────────────────────────────────────┐
│  PLANNER (Deepest reasoning - Opus/HAI)             │
│  - Expands prompts into detailed specifications     │
│  - Anticipates edge cases                           │
│  - Defines success criteria                         │
└─────────────────────┬───────────────────────────────┘
                      │ Specification
                      ▼
┌─────────────────────────────────────────────────────┐
│  GENERATOR (Execution - Sonnet/Haiku)               │
│  - Implements features one at a time                │
│  - React/Vite/FastAPI stack                         │
│  - Focused, limited scope                           │
└─────────────────────┬───────────────────────────────┘
                      │ Implementation
                      ▼
┌─────────────────────────────────────────────────────┐
│  EVALUATOR (Validation - Sonnet/Haiku)              │
│  - Playwright end-to-end testing                    │
│  - Code review                                      │
│  - Quality gates                                    │
└─────────────────────────────────────────────────────┘
```

### Tiered Cost Model

| Role | Model | Cost | Reason |
|------|-------|------|--------|
| Planner | Opus/Deep | High | Maximum reasoning |
| Generator | Sonnet | Medium | Execution focused |
| Evaluator | Haiku | Low | Simple validation |

---

## PROMPT ENGINEERING FOR AGENTS

### Agent-Computer Interface (ACI) Principles

1. **Put yourself in the model's shoes**
   - Would usage be obvious from description?

2. **Think in docstrings**
   - Write for a junior developer
   - Include examples and edge cases

3. **Test extensively**
   - Run many example inputs
   - Identify model mistakes

4. **Poka-yoke tools**
   - Make mistakes harder to make
   - Example: Always use absolute paths

### Tool Format Best Practices

| Format | Recommendation |
|--------|----------------|
| **Diffs** | Avoid - requires line counts |
| **JSON in code** | Avoid - escaping issues |
| **Markdown code** | PREFERRED - natural format |
| **File rewrites** | Easier than diffs |

### Giving Agents Enough to Think

```
BEFORE: "Fix the bug"
AFTER:  "The bug is in line 45 of auth.py.
         The expected behavior is X.
         The actual behavior is Y.
         First think about what could cause this.
         Then examine the code.
         Then propose a fix."
```

---

## VOLAURA MIROFISH INTEGRATION

### Map MiroFish to Claude Mythos

| MiroFish Component | Claude Mythos Equivalent |
|-------------------|-------------------------|
| Lead Orchestrator | CEO Agent (Yusif) |
| Specialist Agents (14+) | Worker Subagents |
| Memory System | Distributed Context |
| Tool calls | MCP Integration |
| Swarm Protocol | Team Coordination |

### Volaura Multi-Agent Template

```
═══════════════════════════════════════
VOLAURA AGENT TEAM PROTOCOL
═══════════════════════════════════════

TEAM LEAD: CEO Agent
- Interprets user requests
- Decomposes into specialist tasks
- Synthesizes results

SPECIALIST AGENTS:
├─ Research Agent: Market analysis, competitor research
├─ Strategy Agent: Business model, growth tactics
├─ Content Agent: LinkedIn posts, documentation
├─ Code Agent: Technical implementation
├─ Grant Agent: Application preparation
└─ [Specialist N]: Custom domain

TASK FLOW:
1. User request → Team Lead
2. Lead decomposition → N subagents
3. Parallel execution → Results
4. Lead synthesis → Final output
5. Human checkpoint → Approval/Refinement

CONTEXT MANAGEMENT:
- Save plan at start
- Checkpoint every 5 subtasks
- Summarize before context limit
═══════════════════════════════════════
```

---

## IMPLEMENTATION CHECKLIST

### Before Spawning Team

- [ ] Clear objective defined
- [ ] Task decomposition complete
- [ ] Success criteria defined
- [ ] Context boundaries set
- [ ] Error handling plan in place

### During Execution

- [ ] Monitor progress (task list)
- [ ] Checkpoint critical states
- [ ] Handle agent communication
- [ ] Aggregate results
- [ ] Manage dependencies

### After Completion

- [ ] Synthesize all findings
- [ ] Validate against success criteria
- [ ] Save to persistent memory
- [ ] Report to user
- [ ] Document lessons learned

---

## USAGE TRIGGERS

Use this skill when:
- "Coordinate multiple agents for [task]"
- "Run parallel research on [topic]"
- "Build multi-step workflow"
- "Set up agent team"
- "How do I implement orchestrator-worker pattern?"
- "Manage subagent communication"
- "Handle errors in agent system"
- "Apply Claude Mythos to [project]"

---

## RELATED PATTERNS

| Pattern | When to Use | File |
|---------|-------------|------|
| Supervisor-Worker | Complex tasks, dynamic subtasks | This skill |
| Prompt Chaining | Sequential transformations | This skill |
| Parallelization | Independent tasks | This skill |
| Evaluator-Optimizer | Quality-critical refinement | This skill |

---

**Source:** Anthropic Engineering (multi-agent-research-system), Claude Mythos Architecture
**Credits:** Anthropic, Claude Code Agent Teams, Claude Mythos documentation

## Trigger
Task explicitly involves claude-mythos-universal, OR task description matches: Universal multi-agent orchestration skill based on Claude Mythos architecture. Use for coordinating .

## Output
Structured report: 1) Key findings (3 bullets max), 2) Recommended actions ranked by impact, 3) Blockers or risks if any.
