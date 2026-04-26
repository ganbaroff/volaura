# Three-Instance Audit — Orchestration

**Date:** 2026-04-26
**Goal:** McKinsey-grade technical audit of VOLAURA ecosystem across 3 AI instances, each playing to its strength. Output is for AI-consumer (next-sprint executor), NOT for human reading.

## Why three instances

Each instance has tools and weaknesses the others lack. A single instance auditing alone produces blind spots. Three instances with distinct prompts, no shared context, then synthesized → cross-validated coverage.

| Instance | Strengths | Weaknesses | Audit slot |
|---|---|---|---|
| **Browser-Atlas** (claude.ai web, Opus 4.7) | NotebookLM mount of project docs, web search, multi-doc reasoning, business framing | No localhost, no .env, no live tool calls | Strategic / business / vision-drift / monetization / cross-product narrative |
| **Codex** (Codex Cloud or similar code-aware) | Deep code reading, type checking, dead-code detection, RLS scan, repo-wide refactor analysis | No live runtime, no DB access, no production observability | Code health / security / type safety / dead code / RLS gaps / test coverage |
| **Code-Atlas** (this machine, Opus 4.7 with Claude Code CLI) | Live tool calls, .env keys, Supabase MCP, daemon control, PowerShell, real prod curl, GitHub Actions logs, Sentry | Mid context window for huge multi-doc tasks, single-machine bound | Live runtime / infra / cross-instance courier / DB row checks / cron health / observability |

## Protocol

1. Yusif opens three separate chats (or sessions).
2. Pastes the matching prompt from this directory:
   - `prompt-browser-atlas.md` → claude.ai web (or NotebookLM with VOLAURA repo mounted)
   - `prompt-codex.md` → Codex / equivalent code-aware AI
   - `prompt-code-atlas.md` → Code-Atlas runs this against itself in next session, OR a parallel Claude Code CLI instance picks it up
3. Each instance produces its audit deliverable at the specified path.
4. Code-Atlas synthesizes the three deliverables into `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md` — the executable backlog for next 10 sprints.
5. CEO ratifies the synthesis. Sprints kick off.

## Output contract (all three prompts enforce)

Each instance writes a single markdown file. Every finding has:

```
### F-NN — <short title>
**Severity:** P0 / P1 / P2 / P3
**Specialist:** Architecture / Security / Product / UX / Cultural / Comms / Risk / Readiness / Code Quality / Legal / Cost / Infra / Observability
**Surface:** <exact file path or system component>
**Evidence:** <tool-call receipt or quote from canonical source>
**Impact if unfixed:** <one paragraph, concrete consequence>
**Recommended fix:** <mechanically-actionable steps an AI can execute, with file paths and code snippets>
**Sprint slot:** S1 / S2 / ... / S10
**Estimated effort:** <hours, AI-time>
**Dependencies:** <other findings or external blockers>
```

No prose summaries. No bullet lists outside this structure. AI-readable, not human-readable.

## Synthesis target

`docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md` consolidates all findings into 10 sprints, deduplicated, dependency-ordered, with one finding per row in a manifest table. Each sprint slot has clear deliverable, owner-instance (which AI executes), and acceptance criteria.

## Cross-instance discipline

Per `.claude/rules/atlas-operating-principles.md` "Pre-critique audit gate" + "Verify-before-save gate" — each prompt mandates:
- Read named source files BEFORE making claims
- Tool-call receipts in evidence field
- No fabrication of paths, line numbers, or function names
- If unable to verify a claim — mark `[UNVERIFIED]` and explain why

The three instances do NOT share context. Each starts cold from its prompt. Convergence on findings between instances is itself a signal — multi-perspective confirmation.
