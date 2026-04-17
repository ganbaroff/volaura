---
name: Swarm Interaction Patterns
description: How to work with the swarm effectively — learned from Session 51
type: feedback
last_updated: 2026-03-27
---

# Swarm Interaction Patterns — CTO Learnings

## Discovery: Temperature = Quality Control

| Temp | What happens | Best for |
|------|-------------|----------|
| 0.7 | Fake consensus, all agree, generic ideas | Code review, routine tasks |
| 0.9 | Herd negativity, all say "trash" | Stress testing a plan |
| 1.0 | Real disagreement, convergent innovation | Strategic decisions |

**Rule:** Strategic questions → 1.0. Operational → 0.7. Stress test → 0.9.

## Discovery: Convergent Ideas = Strongest Signal

When 2+ agents independently propose the same idea at temp 1.0, it's the highest quality signal.
- Session 51: 2/5 proposed "mentorship system" independently → REAL innovation
- Session 51: 3/5 proposed "security vulnerability detector" → REAL need

**Rule:** Track convergent count. 2/5 = investigate. 3/5 = act immediately.

## Discovery: Swarm Needs Prioritization, Not Freedom Alone

First run with full freedom: swarm said "we need CLEAR PRIORITIZATION."
Freedom without direction = paralysis. The swarm is a team, not a democracy.

**Rule:** CTO provides priority order. Swarm critiques the order. CTO adjusts. Then execute.
Not: "what should we do?" → Better: "I plan X→Y→Z. Attack this order."

## Discovery: Swarm is Best at Finding CTO Blind Spots

3 runs in a row: swarm found "CTO doesn't prioritize security."
CTO was building features (skills, telegram, avatar). Swarm caught the pattern.

**Rule:** After every feature sprint, ask swarm: "what did CTO miss?"

## Pattern: How to Ask the Swarm

BAD: "What should we build next?" → generic, scattered answers
GOOD: "Here's my plan. Find the fatal flaw." → specific, actionable
BEST: "Here's plan A and plan B. Which kills us faster?" → forces real analysis

## Pattern: Swarm Roles That Work

| Agent | Best at | Worst at |
|-------|---------|----------|
| Security Auditor | Finding what CTO forgot | Proposing features |
| Scaling Engineer | Infrastructure math | UX decisions |
| Product Strategist | User retention, aha moments | Security |
| Code Quality | Shortcuts that will break | Vision |
| CTO Watchdog | Process violations | Technical depth |

**Rule:** Route questions to the right agent. Don't ask Security about UX.

## Anti-Pattern: Don't Run Swarm Too Often

Groq rate limit: 12000 TPM. 5 agents × ~6000 tokens = 30000 TPM needed.
Running swarm 3x in 10 minutes → 429 errors.

**Rule:** Max 1 full swarm run per 5 minutes. Stagger if needed.

## CEO Directive (Session 51)

"слушай изучай паттерн роя. не только мой. учись как с ним работать."

Translation: CTO should learn the swarm's patterns like CTO learned Yusif's patterns.
The swarm is a team member, not a tool. Study how they think, what they need, what they miss.
