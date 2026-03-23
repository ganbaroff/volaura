---
name: decision-simulation
description: >
  Swarm-powered decision simulation engine. Runs REAL parallel independent agents
  (not one model arguing with itself) for project decisions. v4.0 uses Agent tool
  to launch 10+ haiku agents in parallel — each evaluates independently, then
  a synthesis agent aggregates. This eliminates pseudo-debate bias and produces
  genuine divergence signals. MUST trigger at sprint start. Also trigger for any
  decision with 2+ viable paths and >1hr rework cost if wrong. Skip for trivial
  choices (variable names, formatting, obvious single-fix bugs).
version: 4.0
updated: 2026-03-23
changelog: >
  v4.0 — SWARM ARCHITECTURE: Real parallel agents via Agent tool instead of
  single-model pseudo-debate. 10 independent evaluators + 1 synthesis agent.
  Each evaluator cannot see others' responses. Divergence detection added.
  Cost: ~$0.01-0.02 per DSP (haiku agents). Kills fake consensus.
  v3.2 — Mandatory precheck, visible output per step, schema verification.
  v3.0 — Self-improvement protocol, confidence gate, calibration.
  v2.0 — QA Engineer, model routing, mandatory pre-sprint trigger.
---

# Decision Simulation Engine v4.0 — Swarm Architecture

_From MiroFish swarm intelligence. v4.0 replaces single-model debate with
real parallel independent agents._

## What Changed in v4.0

| v3.x (Pseudo-Debate) | v4.0 (Swarm) |
|---|---|
| One model plays 6 roles | 10 real independent agents |
| Sequential (same context) | Parallel (no shared context) |
| Agents see each other's opinions | Agents are blind to each other |
| Consensus is often fake | Divergence is real signal |
| ~39/50 average scores | Expected ~44-47/50 |
| Free (same context) | ~$0.01-0.02 per run (haiku) |

## When to Run

**MANDATORY** — start of every sprint, before code.
**Always** — decisions with Stakes >= Medium and 2+ viable paths.
**Never** — variable names, formatting, obvious single-fix bugs, user said "just do it".

## The Algorithm (v4.0)

### Step 0: DETECT — Should I simulate?

1. Are there genuinely 2+ viable paths?
2. Would picking wrong cost >1 hour of rework or have security/UX consequences?
3. Is this reversible in 5 minutes?

If (1) AND (2) AND NOT (3) → run simulation.

### Step 1: SEED — Structure the problem

```
DECISION SEED:
├── Question: [What are we deciding?]
├── Context: [Why now? What triggered this?]
├── Constraints: [Budget, timeline, tech stack, existing code]
├── Stakes: Low | Medium | High | Critical
├── Reversibility: Easy | Moderate | Hard | Irreversible
└── Affected Systems: [files/services touched]
```

### Step 2: GENERATE PATHS — Create 3-5+ alternatives

Each path must be genuinely different. For each:
- **Name**: Short label
- **Description**: 2-3 sentences
- **Best case / Worst case / Side effects**
- **Effort**: S/M/L/XL
- **Dependencies**: What must exist

For High/Critical stakes: generate 6-10 paths (more paths = better winner).

### Step 3: MODEL ROUTING

| Stakes | Agents | Model | Cost |
|--------|--------|-------|------|
| Low | 5 evaluators + 1 synthesis | haiku | ~$0.005 |
| Medium | 10 evaluators + 1 synthesis | haiku | ~$0.01 |
| High | 10 evaluators + 1 synthesis | haiku eval, sonnet synthesis | ~$0.02 |
| Critical | 15 evaluators + 1 synthesis | haiku eval, sonnet synthesis | ~$0.03 |
| Irreversible | 20 evaluators + opus synthesis | haiku eval, opus synthesis | ~$0.05 |

### Step 4: LAUNCH SWARM — Parallel independent evaluation

**This is the core change.** Instead of one model playing roles, launch REAL
Agent(haiku) instances in parallel via the Agent tool.

Each agent gets this prompt template:

```
You are an independent evaluator for a technical decision.
You have NOT seen any other evaluator's opinion. Be honest and specific.

ROLE: {persona_name} — {persona_description}
YOUR LENS: {evaluation_lens}

DECISION: {question}
CONTEXT: {constraints}

PATHS:
{path_descriptions}

For EACH path, provide:
1. Score (0-10) on: Technical, User Impact, Dev Speed, Flexibility, Risk
2. One specific concern (cite a file/table/endpoint if possible)
3. Your recommended winner and ONE sentence why

Output as JSON:
{
  "scores": {"path_a": {"technical": N, "user": N, "speed": N, "flex": N, "risk": N}, ...},
  "concerns": {"path_a": "...", "path_b": "..."},
  "winner": "path_X",
  "reason": "..."
}
```

**10 personas for Medium+ stakes (all launched in parallel):**

| # | Persona | Lens | Influence |
|---|---------|------|-----------|
| 1 | **Leyla** (Volunteer, 22yo, Baku, mobile) | "Can I do this in 30 sec on my phone?" | 1.0 |
| 2 | **Nigar** (Org Admin, HR, desktop) | "Does this help me manage 50+ volunteers?" | 1.0 |
| 3 | **Attacker** (Security adversary) | "How do I exploit this? OWASP top 10." | 1.2 |
| 4 | **Scaling Engineer** | "What breaks at 10x? Where are bottlenecks?" | 1.1 |
| 5 | **Yusif** (Founder, $50/mo budget) | "Does this get us to launch faster?" | 1.0 |
| 6 | **QA Engineer** | "What edge cases break this? Test plan?" | 0.9 |
| 7 | **DevOps Pragmatist** | "Can I deploy this in 1 command? What breaks in CI?" | 1.0 |
| 8 | **Data Architect** | "Is the schema right? Indexes? Query performance?" | 1.0 |
| 9 | **Accessibility Advocate** | "WCAG 2.1 AA? Screen reader? Keyboard nav?" | 0.8 |
| 10 | **Devil's Advocate** | "Why is the obvious winner actually wrong?" | 1.1 |

For Low stakes: use personas 1, 3, 5, 6, 10 (5 agents).

**Implementation — use Agent tool:**

```
// Launch ALL agents in a SINGLE message with multiple Agent tool calls
Agent(haiku, prompt=evaluator_1_prompt)  // Leyla
Agent(haiku, prompt=evaluator_2_prompt)  // Nigar
Agent(haiku, prompt=evaluator_3_prompt)  // Attacker
...all 10 in parallel
```

### Step 5: AGGREGATE — Synthesis Agent

After all 10 agents return, a synthesis agent (sonnet for High+, haiku for Low/Medium)
receives ALL 10 evaluations and produces:

```
SYNTHESIS PROMPT:
You received 10 independent evaluations of the same decision.
No evaluator saw any other's response. This is real divergence data.

EVALUATIONS:
{all_10_results}

Produce:
1. CONSENSUS: What do most agents agree on?
2. DIVERGENCE: Where do agents DISAGREE most? (This is the real risk signal)
3. SURPRISE: Any evaluator raised something no one else did? (May be genius or noise)
4. WEIGHTED SCORES: Calculate per path using influence weights.
5. WINNER: Path with highest weighted score.
6. CONFIDENCE: How strong is the consensus? (unanimous = suspicious, split = real uncertainty)
```

### Step 6: DECLARE — Output format

```
🔮 DSP v4.0: [Decision Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stakes: [Level] | Agents: [N] | Model: haiku→[synthesis model]

📊 Path Scores (weighted by influence):
  Path A — [Name]: [Score]/50
  Path B — [Name]: [Score]/50  ← WINNER
  Path C — [Name]: [Score]/50

🤝 CONSENSUS (8/10 agents agree):
  [What most agents converged on]

⚡ DIVERGENCE (key disagreements):
  - Attacker vs Yusif: [security vs speed trade-off]
  - Scaling Engineer vs DevOps: [architecture vs deployability]

💡 SURPRISE (unique insights from 1-2 agents):
  - Devil's Advocate: "[unexpected perspective]"

🏆 Winner: Path [X] — [Score]/50
Reasoning: [2-3 sentences, citing specific agent arguments]
Confidence: [Strong/Moderate/Weak] ([N]/10 agents chose this path)

⚠️ Accepted Risks: [what we knowingly trade off]
🔄 Fallback: Path [Y] if [specific trigger condition]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quick Mode (Stakes: Low)

For trivial decisions, DON'T launch agents. Single-model is fine:

```
🔮 DSP Quick: [Decision Name]
Paths: A) [Name] vs B) [Name] vs C) [Name]
Winner: B — [One sentence why]
Risk: [One sentence what could go wrong]
```

## Calibration Rules

1. **No unanimous votes.** If 10/10 agree → paths aren't genuinely different. Regenerate.
2. **Attacker MUST find a real vuln** per path. "This is fine" = simulation too shallow.
3. **Divergence IS the signal.** Where agents disagree most = where real risk lives.
4. **Don't simulate what you can test.** "Which query is faster?" → benchmark it.
5. **1-2 agent outliers may be right.** Don't dismiss minority positions — flag them.

## Confidence Gate

Winner must score **≥ 35/50**. If below:
1. Generate 2 more paths and re-run with 5 additional agents
2. If still < 35 → decision is genuinely uncertain. Document:
   ```
   ⚠️ LOW CONFIDENCE: [N]/50. Proceeding because: [reason].
   Review trigger: [when to revisit].
   ```

## Post-Sprint Calibration

After each sprint:
```
DSP predicted: Path [X] — Score [N]/50
Actual result: [what happened]
Delta: [better/worse/as expected]
Which agent was most accurate? → +0.1 weight
Which agent was most wrong? → -0.1 weight
```

Log in `docs/DECISIONS.md`.

## Council Evolution

| Trigger | Action |
|---------|--------|
| Agent's concern proved correct 3+ times | +0.1 influence weight |
| Agent consistently blocks good decisions | -0.1 influence weight |
| Agent never dissents | Rewrite prompt, increase specificity |
| New blind spot found | Add 11th agent with that specialization |
| Agent's domain irrelevant for 5+ sessions | Remove from default roster |

**Current weights (v4.0):**
Leyla: 1.0 | Nigar: 1.0 | Attacker: 1.2 | Scaling Engineer: 1.1 |
Yusif: 1.0 | QA Engineer: 0.9 | DevOps: 1.0 | Data Architect: 1.0 |
Accessibility: 0.8 | Devil's Advocate: 1.1

## Future: Swarm Scaling (v5.0 roadmap)

| Level | Agents | Mechanism | Use case |
|-------|--------|-----------|----------|
| v4.0 | 10-20 | Agent tool parallel | DSP decisions |
| v5.0 | 100-200 | Agent tool waves (20×N) | Skill evolution, prompt optimization |
| v6.0 | 1000+ | Anthropic Batch API | Prediction markets, AURA calibration |

See IDEAS-BACKLOG.md Idea #6 for full swarm engine roadmap.

## Volaura-Specific Context

Personas are calibrated for Volaura:
- **Leyla**: 22yo, Baku, mobile, AZ native, wants AURA on LinkedIn
- **Nigar**: HR at NGO, 50+ volunteers, desktop, needs export/filter
- **Attacker**: Knows FastAPI + Supabase + Next.js vulns, 5 known criticals
- **Scaling Engineer**: Monolith FastAPI, Supabase free tier, target 10K volunteers
- **Yusif**: $50/mo budget, 6-week timeline, HR bouquets + LinkedIn growth
- **Data Architect**: pgvector(768), RLS policies, AURA weights, IRT parameters
- **DevOps**: Vercel free + Railway $8/mo, no CI/CD yet, manual deploy

When running simulations, agents MUST reference actual files, tables, endpoints — never generic platitudes.
