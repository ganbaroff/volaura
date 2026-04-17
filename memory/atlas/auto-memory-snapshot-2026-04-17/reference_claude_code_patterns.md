---
name: Claude Code Architecture Patterns (from source analysis)
description: 10 patterns extracted from Claude Code's 2000 TS files — applicable to ZEUS and VOLAURA
type: reference
---

## Source
https://github.com/alejandrobalderas/claude-code-from-source
Book chapters: ch05 (agent loop), ch08-09 (sub-agents, fork), ch10 (coordination), ch11 (memory), ch12 (extensibility)

## Most Critical: Coordinator Pattern (ch10)

**For ZEUS (39 agents without a brain):**
- Coordinator restricted to 3 tools: Agent, SendMessage, TaskStop
- Workers get full toolset
- 4 phases: Research (parallel) → Synthesis (coordinator only) → Implementation (specific file:line) → Verification
- Anti-patterns: vague instructions, delegating comprehension, serializing parallel work
- Key rule: "Never delegate understanding. Coordinator synthesizes, workers explore."

## Task State Machine (ch10)
7 task types: local_bash(b), local_agent(a), remote_agent(r), in_process_teammate(t), local_workflow(w), monitor_mcp(m), dream(d)
States: pending → running → {completed, failed, killed}
Critical fields: outputFile (disk transcript), outputOffset (incremental reads), notified (no duplicates)

## File-Based Mailbox (ch10)
~/.zeus/agents/{agent_id}/mailbox/{incoming,processed}/
- Durable across crashes, human-inspectable, no message broker
- Agents reference teammates by name via agentNameRegistry

## Memory System (ch11) — For VOLAURA talent personalization
4 types: user, feedback, project, reference
MEMORY.md = always-loaded index (150 char per entry max)
Files: frontmatter (name, description, type) + body (rule + Why + How to apply)
Recall: MEMORY.md loaded first → Sonnet side-query selects relevant files → load those

## Fork Agents for Cost Reduction (ch09)
N parallel agents from same context:
- Without fork: N full-price calls
- With fork: 1 full + (N-1) at ~10% cost
- Requirements: byte-identical prefix, same system prompt string, same tool array, cloned history
- 60% cost reduction on 5 children from 48,500 token context

## AsyncGenerator Loops (ch05)
- Natural backpressure: agents pause when coordinator busy
- Typed completion reason enum: completion, abort, error, token_limit
- Speculative tool execution while streaming
- Token counting + auto-compact inside loop

## Context Compression Ladder (ch05)
Tier 1: Tool result budgets (200K chars/msg)
Tier 2: Snip compact (remove intermediate tool results)
Tier 3: Microcompact (compress summary blocks)
Tier 4: Context collapse (multiple turns → one)
Tier 5: Upgrade token reservation (8K → 64K)

## Production Warning (ch10 — Memory Safety)
50-message cap per swarm agent (found: 292 agents consuming 36.8GB without cap)
