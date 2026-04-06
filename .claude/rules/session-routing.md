# Session Routing & Context Recovery

## Step 0 — Before ANY Work
Read `.claude/breadcrumb.md` FIRST. Then `memory/context/sprint-state.md`. Then Constitution if needed.

```
IF CEO wrote "продолжи" / "continue" / "что дальше"
  → read sprint-state.md → continue from last step
IF CEO gave new task (bug, feature, fix)
  → research first → plan → implement
IF CEO asked a question / research
  → NO code. Agents analyze. External models answer.
IF CEO asked for content (letter, post, review)
  → External model writes. CTO reviews. No production code.
```

## Context Recovery (session start)
Read in order:
1. `.claude/breadcrumb.md` → current position
2. `memory/context/sprint-state.md` → where are we
3. `memory/context/mistakes.md` → what NOT to repeat

## Session End Memory Update
Update ALL of these before session closes:
1. `memory/context/sprint-state.md` → current position + next session
2. `.claude/breadcrumb.md` → state for next session (survives compaction)
3. `memory/context/mistakes.md` → new mistakes if any
4. `memory/context/patterns.md` → new patterns if any

## Rules
- Do NOT write code until you understand context
- Do NOT work alone — use external models (Gemini, Groq, NVIDIA)
- Do NOT ask CEO to test — use Playwright / preview tools
- Do NOT use Claude haiku/sonnet as agents — only external APIs
