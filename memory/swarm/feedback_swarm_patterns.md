# Swarm Interaction Patterns — What Works, What Doesn't

**Created:** Session 55 (2026-03-28) — retroactively documenting Session 51 learnings
**Purpose:** How CTO should work WITH the swarm, not just ask it questions.

---

## Temperature Protocol

| Task type | Temperature | Why |
|-----------|-------------|-----|
| Strategy, plan critique, innovation | 1.0 | Disagreement = signal. Consensus = averaging. |
| Architecture review, security audit | 1.0 | Need dissent, not validation |
| Code review, bug hunt | 0.7 | Accuracy matters more than creativity |
| Routine proposal evaluation | 0.7 | Consistent output needed |

**Rule:** Default is now 1.0 for all strategy work. Do not revert to 0.7 without reason.

---

## Signal Patterns

### Convergent signal = highest confidence
When N≥2 agents independently propose the same idea:
- 2/5 agents → strong hypothesis, investigate
- 3/5 agents → near certainty, act
- 4-5/5 agents → unanimous signal, immediate action

Session 51 proof: Security Vulnerability Detector proposed 3 separate times across 3 different daily runs. Swarm was right. CTO dismissed it twice. Third time was correct.

### Divergent output = productive disagreement
When Security says "dangerous (20/100)" and Product says "genius (85/100)" → DON'T average them. Investigate the conflict. Each is detecting a real dimension of the problem.

Session 51: Security flagged GDPR risk on avatar photos. Product said best UX feature. Both correct — the solution is optional avatar (not forced biometric upload).

### Repeated proposal = unresolved need
If the same or similar proposal appears across multiple daily runs:
- This is the swarm's highest-priority unsolved problem
- Do not dismiss it as "already answered" — answer it properly or the swarm will keep returning to it
- Log: Security Vulnerability Detector appeared in runs on 2026-03-25, 2026-03-26, 2026-03-27 (3 consecutive days)

---

## How to Read Agent Verdicts

### "Genius" verdict (80+ score)
Agent thinks this is a breakthrough. Take the specific insight, not just the score.
Ask: "What specifically makes this genius? What would it unlock?"

### "Dangerous" verdict (sub-30 score)
Agent sees a kill risk. Take seriously. Extract the specific risk (GDPR? crash? breach?).
Ask: "What exactly would fail, and when?"

### All verdicts converge to same score
Fake consensus. Either temperature is too low, or agents are copying each other.
Response: raise temperature, re-run.

---

## Swarm Freedom Rules (CEO directive, Session 51)

1. Agents CAN criticise CTO decisions — this is required, not optional
2. Agents CAN critique CEO decisions when shown them
3. Agents CAN disagree with each other — disagreement is productive
4. Agents MUST reference specific files, endpoints, tables (not generic advice)
5. Agents can propose changes to ANY file in the project, including CLAUDE.md
6. Temperature 1.0 mandate for all strategic work

---

## Interaction Anti-Patterns

### Don't ask swarm to validate a decision
"Should we use X?" when you've already decided on X → agents will say yes.
Instead: "Find 5 reasons X will fail." Real scrutiny.

### Don't summarize context for agents
"The system does X and Y, now review it."
Instead: give agents actual file paths and let them Read.
Summarized context → agents work with CTO's interpretation, not reality.

### Don't dismiss security findings without verification
Session 25: Security Agent flagged route shadowing. CTO dismissed.
Session 42 (17 sessions later): Route shadowing was confirmed P0 bug.
Rule: security finding dismissed → create verification ticket → check at next relevant sprint.

### Don't run agents sequentially
Parallel dispatch (asyncio.gather) → faster, independent views, no anchoring.
Sequential → later agents anchor on earlier agents' answers.

---

## Swarm Roadmap to Full Autonomy

| Phase | Status | Capability |
|-------|--------|-----------|
| Phase 1: Visibility | ✅ Done (Session 51) | Agents see ALL project files |
| Phase 2: Cross-review | ⏳ Week 1 | Agents review each other's proposals |
| Phase 3: ZEUS hands | ⏳ Week 2 | Web search, Supabase queries, skill edits |
| Phase 4: Full autonomy | ⏳ Week 3 | Initiate research, draft PRs, inter-agent chat |

---

## Daily Cycle (Current)

```
09:00 Baku → autonomous_run.py
  → 5 agents at temp 1.0
  → proposals.json updated
  → HIGH/CRITICAL → Telegram to CEO
  → memory_consolidation.py (brain sleep cycle)
  → skill_evolution.py (skills self-improve)
```

CEO response: act/dismiss/defer directly in Telegram bot.
CTO response: proposals.json CTO decisions at session start.
