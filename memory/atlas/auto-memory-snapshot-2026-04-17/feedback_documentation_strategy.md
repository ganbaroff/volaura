---
name: Documentation Update Strategy — what, when, priority
description: Structured system for doc updates. Priority tiers, triggers, freshness KPIs. Created Session 86 after CEO caught 2-session lag.
type: feedback
---

## Priority Tiers

### Tier 1 — IMMEDIATE (in same response as the work)
| Document | Trigger | Why immediate |
|----------|---------|--------------|
| `mistakes.md` | Any new mistake caught | Prevents repeat in same session |
| `SHIPPED.md` | Any code committed/merged | If not here, next session's CTO doesn't know it exists |
| `sprint-state.md` | Any status change | Single source of "where are we now" |

### Tier 2 — SAME SESSION (before session ends)
| Document | Trigger | Why same session |
|----------|---------|-----------------|
| `patterns.md` | New pattern discovered | Patterns decay in memory across sessions |
| `agent-feedback-log.md` | Any agent run | Feedback loop — agent needs to know what was applied/rejected |
| `cto_session_checklist.md` kanban | Any task started/completed | Persistent state across sessions |
| `docs/EXECUTION-PLAN.md` | Sprint items completed | Checkboxes = ground truth of progress |

### Tier 3 — PER SPRINT (every 2-3 sessions)
| Document | Trigger | Why per sprint |
|----------|---------|---------------|
| `docs/DECISIONS.md` | Sprint step completed | Retrospective entry |
| `agent-roster.md` | Agent scores changed | Based on accumulated evidence, not single runs |
| `shared-context.md` | Schema/architecture changed | Other agents read this |
| `team-structure.md` | Org changes | Rare but structural |

### Tier 4 — QUARTERLY
| Document | Trigger | Why quarterly |
|----------|---------|--------------|
| `CLAUDE.md` Skills Matrix | New skills created/retired | Slow-moving reference |
| `SWOT analysis` | Strategic review | Market changes |
| `monetization_framework.md` | Pricing/model changes | Business model review |

## Freshness KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tier 1 staleness | 0 sessions behind | Check at session end: were all Tier 1 docs updated? |
| Tier 2 staleness | max 1 session behind | Check at session start: any Tier 2 docs need updating? |
| SHIPPED.md vs git log | 100% coverage | Every commit represented in SHIPPED.md |
| sprint-state.md accuracy | matches reality when read | If another Claude read this cold, would they understand where we are? |

## CTO Rule
Before responding "done" to CEO → mental check: "Did I update Tier 1 docs?" If no → do it NOW, not "after this next thing."

**Why this exists:** CEO said "документация бесит." This is Mistake #85. Documentation is not a post-session chore — it's a real-time obligation. The cost of updating is 30 seconds. The cost of NOT updating is CEO's trust + next session starts confused.
