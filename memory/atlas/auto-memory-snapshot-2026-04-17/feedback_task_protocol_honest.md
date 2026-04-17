---
name: TASK-PROTOCOL honest assessment
description: TASK-PROTOCOL helps for architecture, hurts for 80% of tasks. Use breadcrumbs instead.
type: feedback
---

TASK-PROTOCOL v8.0 is 17,000 tokens. Loading it costs ~15% of context window.

**What helps (keep for heavy tasks):**
- Flow Detection IF/ELSE tree (first 20 lines)
- Acceptance Criteria before coding
- "Who else reviewed?" check
- Blast Radius assessment for risky changes

**What doesn't help (skip for routine work):**
- 10 mandatory steps for CSS fixes
- DSP with 9 personas for every decision
- Counter-Critique + Second Critique for non-architectural changes
- Skills Matrix loading (30 seconds each, rarely changes behavior)

**How to apply:**
- Architecture/security/data model → full TASK-PROTOCOL
- Everything else → breadcrumb system (.claude/breadcrumb.md)
- CEO said "я не знаю мешаю ли когда прошу TASK-PROTOCOL" — honest answer: it helps when used for the right tasks, hurts when forced on every task
