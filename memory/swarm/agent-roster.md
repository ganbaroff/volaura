# Agent Roster — Swarm Team

**Purpose:** Agents know who's on the team and what each agent is best at.
**Updated:** 2026-03-25

---

## Active Agents

| Agent Role | Model | Primary Strength | Known Weakness | Recent Score |
|-----------|-------|-----------------|----------------|-------------|
| Architecture Agent | haiku | System coherence, data flow gaps, storage math | Sometimes misreads auth patterns (recommended SupabaseUser fix that wasn't applicable) | 6.5/10 |
| Security Agent | haiku | CVSS scoring, attack vectors, enumeration risks, injection patterns | Needs actual DB state to verify RLS correctness | 7.5/10 |
| Product Agent | haiku | User journey gaps, Leyla/Nigar persona gaps, adoption risks | Doesn't have usage data — reviews based on design inference only | 5.5/10 |
| Needs Agent | haiku | Meta-analysis, process improvement, swarm structure | N/A (introspective role) | N/A |

---

## When to Call Each Agent

| Task | Best Agent |
|------|-----------|
| New API endpoint design | Architecture Agent |
| RLS policy review | Security Agent |
| New feature UX review | Product Agent |
| Sprint planning critique | All 4 in parallel |
| Code change >50 lines | Architecture + Security |
| New user-facing flow | Product Agent |
| Process improvement | Needs Agent |
| Data model changes | Architecture Agent |
| New auth flow | Security Agent |

---

## Escalation Rules

- If Security Agent finds CVSS >= 8.0 → CTO must fix before any other work
- If Architecture Agent scores design < 5/10 → don't implement, redesign
- If Product Agent finds >3 critical user journey gaps → ship partial, not full feature
- Any agent can veto by scoring < 35/50 in DSP — triggers extra debate round

---

## What Agents Need in Every Task Prompt

**Required (blocks good work without these):**
1. Current DB schema (in `memory/swarm/shared-context.md` — include this file)
2. Specific code snippet being reviewed (paste it, don't reference file paths)
3. Current sprint goal (from shared-context.md)
4. Decision log — what's already decided (from shared-context.md)

**Helpful (improves review quality):**
5. Related file context (e.g., if reviewing aura.py, also include schemas/aura.py)
6. Recent agent feedback (from agent-feedback-log.md)
7. Which other agents are running in parallel (avoid duplicate proposals)

---

## Agent Improvement Tracking

| Agent | Session | Was Agent Right? | Note |
|-------|---------|-----------------|------|
| Security Agent | 25 | Yes (4/5 findings correct) | Route shadowing was false positive (FastAPI handles) |
| Architecture Agent | 25 | Mostly (4/6 correct) | SupabaseAdmin fix recommendation was wrong context |
| Product Agent | 25 | Yes (all gaps real) | Can't prioritize without usage data |
| Needs Agent | 25 | Yes (schema snapshot was top need) | Schema now in shared-context.md |
