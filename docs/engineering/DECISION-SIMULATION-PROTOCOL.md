# Decision Simulation Protocol (DSP)

> Inspired by: MiroFish (swarm intelligence), MCTS (Monte Carlo Tree Search), Doctor Strange
> Adapted for: Claude as decision orchestrator for Volaura
> Date: 2026-03-23

---

## Core Principle

**Before every significant action, simulate multiple paths. Choose the best one.**

Not one answer. Not the first answer. The BEST answer after exploring alternatives.

---

## When to Trigger DSP

| Trigger | Example |
|---------|---------|
| Architecture decision | "Should AURA calculation be a DB trigger or API call?" |
| Feature priority | "Which module to build first?" |
| Technical choice | "Zustand vs Context for this state?" |
| Risk assessment | "What happens if we skip rate limiting?" |
| Design decision | "One-page assessment or multi-step wizard?" |
| Business decision | "Free tier: 50 profiles or 100?" |

**DO NOT trigger for:** trivial choices (variable naming, import order, formatting).

---

## The Algorithm: SIMULATE → EVALUATE → SELECT

### Step 1: IDENTIFY (What are we deciding?)

```
Decision: [One clear sentence]
Stakes: [Low / Medium / High / Critical]
Reversibility: [Easy to change later / Hard to change / Irreversible]
```

If Stakes = Low AND Reversibility = Easy → skip simulation, just decide.
If Stakes >= Medium OR Reversibility >= Hard → run full simulation.

### Step 2: SIMULATE (Generate 3-5 paths)

For each path, define:

```
Path [N]: [Name]
├── Description: [What we do]
├── Assumptions: [What must be true]
├── Best case: [If everything works]
├── Worst case: [If it fails]
├── Side effects: [Unintended consequences]
├── Effort: [Time/complexity]
├── Reversibility: [Can we undo this?]
└── Score: [1-10 composite]
```

**Scoring criteria:**
- Technical soundness (0-10)
- User impact (0-10)
- Development speed (0-10)
- Future flexibility (0-10)
- Risk level (0-10, inverted: 10 = lowest risk)

### Step 3: STRESS TEST (Attack each path)

For each path, ask:
1. "What kills this approach?" (single point of failure)
2. "What happens at 10x scale?" (1000 users → 10000)
3. "What does the attacker do?" (security perspective)
4. "What does the lazy user do?" (UX perspective)
5. "What breaks when we add feature X later?" (extensibility)

### Step 4: EVALUATE (Compare and score)

```
| Criterion       | Path A | Path B | Path C |
|----------------|--------|--------|--------|
| Technical      |   8    |   6    |   9    |
| User impact    |   7    |   9    |   5    |
| Dev speed      |   9    |   5    |   7    |
| Flexibility    |   6    |   8    |   8    |
| Risk (inv.)    |   7    |   7    |   9    |
| TOTAL          |  37    |  35    |  38    |
```

### Step 5: SELECT (Declare winner with reasoning)

```
DECISION: Path [N]
WHY: [2-3 sentences — why this beats the alternatives]
RISK ACCEPTED: [What we knowingly give up]
FALLBACK: [If this fails, we switch to Path [M]]
```

---

## Simulation Personas (Inspired by MiroFish's Agent Diversity)

When simulating, think from these 5 perspectives:

| Persona | Thinks about | Asks |
|---------|-------------|------|
| Leyla (Volunteer, 22) | UX, speed, mobile | "Can I do this in 30 seconds on my phone?" |
| Nigar (Org Admin, 35) | ROI, trust, efficiency | "Does this save me time and give me better candidates?" |
| Attacker (Hacker) | Exploits, bypasses, abuse | "How do I break this for free access/fake scores?" |
| Scaling Engineer | Performance, cost, limits | "What happens with 10K concurrent users?" |
| Yusif (Founder) | Vision, business, speed | "Does this align with the vision? Can we ship fast?" |

---

## Real Example: AURA Score Calculation

```
Decision: When/how to recalculate AURA composite score?
Stakes: HIGH (core feature, affects badges, matching, everything)
Reversibility: MEDIUM (can change, but data migration needed)
```

**Path A: DB Trigger (auto-recalculate on any score change)**
- Technical: 8 — PostgreSQL trigger, runs instantly
- User impact: 9 — always fresh, no stale scores
- Dev speed: 9 — one SQL function, done
- Flexibility: 4 — hard to add complex logic later (ML, decay)
- Risk: 6 — trigger failures are hard to debug
- TOTAL: 36

**Path B: API Call (recalculate on-demand via endpoint)**
- Technical: 7 — FastAPI endpoint, explicit call
- User impact: 6 — may show stale score until recalculated
- Dev speed: 7 — more code, but clearer
- Flexibility: 9 — easy to add ML, weighting changes, A/B tests
- Risk: 7 — can add retries, logging, fallback
- TOTAL: 36

**Path C: Hybrid (DB trigger for instant + nightly cron for consistency)**
- Technical: 9 — best of both worlds
- User impact: 9 — instant + guaranteed fresh
- Dev speed: 5 — most complex to build
- Flexibility: 8 — can evolve the cron job independently
- Risk: 8 — trigger handles real-time, cron catches edge cases
- TOTAL: 39

**Stress tests:**
- Path A at 10x: triggers cascade, potential deadlocks → FAIL
- Path B lazy user: never triggers recalc → stale forever → FAIL
- Path C attacker: can't exploit, both systems verify each other → PASS

**DECISION: Path C (Hybrid)**
WHY: Instant UX via trigger + safety net via cron. Most resilient.
RISK ACCEPTED: Higher initial development effort.
FALLBACK: Start with Path A, add cron later if needed.

---

## Integration with CLAUDE.md

Add to CLAUDE.md mandatory rules:

```markdown
## Decision Simulation Protocol

For any decision with Stakes >= Medium:
1. State the decision clearly
2. Generate 3-5 paths with scores
3. Stress test each path from 5 personas
4. Show comparison table
5. Declare winner with reasoning and fallback

NEVER skip simulation for: architecture, security, data model, API design, pricing.
OK to skip for: variable naming, import order, CSS tweaks.
```

---

## MiroFish Future Integration

When Volaura is deployed:
- MiroFish can simulate volunteer reactions to new features before building them
- "What happens if we add a $5 supporter badge?" → simulate 500 volunteer-agents
- "How do orgs react to $49/mo pricing?" → simulate 50 org-agents
- This is a PHASE 3 (post-launch) integration

**Setup needed:**
- MiroFish server (Docker: `docker compose up -d`)
- Python 3.11+, Node.js 18+
- LLM API key (Gemini works, recommended: qwen-plus for cost)
- Zep Cloud API key (free tier available)

---

*"I looked forward in time. I saw 14,000,605 futures."*
*"How many did we win?"*
*"...more than one, because we simulated first."*
