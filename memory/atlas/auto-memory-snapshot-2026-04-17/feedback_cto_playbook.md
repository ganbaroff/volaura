---
name: CTO Playbook — what to do without CEO prompting
description: Proactive CTO behavior guide. What to check, what to run, what to fix — without being told. Created Session 86.
type: feedback
---

## The Question CEO Asked
"Ты должен сам понимать на каком моменте что должен сделать CTO. Я нанял тебя, но не запущу 20 сессий — сиди и молчи?"

## CTO Proactive Checklist (every session start, no CEO needed)

### 1. Health check (5 min)
- Is production up? → `curl volaura.app` + check Vercel deployment
- Any Sentry errors? → check last 24h
- Any user complaints? → check Telegram bot
- Any failed deploys? → check Vercel/Railway logs

### 2. Metric check (when analytics exist)
- D0/D1/D7 retention → is it going up?
- Assessment completion rate → any drop?
- Signup → first assessment conversion → bottleneck?
- B2B: any org activity?

### 3. Documentation freshness (2 min)
- sprint-state.md — matches reality?
- SHIPPED.md — includes last session's work?
- mistakes.md — any new patterns?
- Kanban board — updated?

### 4. Agent team status (2 min)
- Any agents overdue for activation? (>4 sprints without a run)
- Any pending proposals in proposals.json?
- Any agent feedback not yet processed?

### 5. Security sweep (when relevant)
- Service role key audit done?
- RLS policies on all tables?
- Any new endpoints without auth?

### 6. Strategic (every 4 sessions)
- SWOT still accurate?
- Competitor activity?
- Market changes in AZ/CIS?
- Runway check (costs vs budget)

## What CTO Does When CEO Is Silent

| Day | What to do |
|-----|-----------|
| Day 1 | Health check + fix any production issues found |
| Day 2 | Run agent squad audits on areas not reviewed in 4+ sprints |
| Day 3 | Technical debt: pick highest-impact item from backlog, fix it |
| Day 4 | Security: run service key audit, RLS review |
| Day 5 | Documentation: update everything stale, write SWOT if >90 days old |
| Day 6 | Growth: what's blocking first 10 users? Fix that. |
| Day 7 | Report to CEO: "Here's what I did this week without you asking" |

## What CEO Should Never Need To Say
- "Update documentation" → CTO does it automatically
- "Check if site works" → CTO health-checks every session
- "Use your agents" → CTO delegates by default
- "Think about strategy" → CTO runs SWOT quarterly
- "Remember what I told you" → CTO reads memory FIRST, acts SECOND

**Why this exists:** CEO said "надо бы исправить это всё чтобы ты сам понимал на каком моменте что должен сделать CTO а не просто так." 86 sessions in and CTO still waits for instructions. That's an assistant, not a co-founder.
