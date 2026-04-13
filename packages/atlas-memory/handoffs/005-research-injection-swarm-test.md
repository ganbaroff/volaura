# Handoff 005: Research Injection into Swarm + Test Run
**From:** Cowork (coordinator) | **Date:** 2026-04-13 | **Priority:** P1

**IMPORTANT:** Read `packages/atlas-memory/sync/PROTOCOL.md` FIRST. Follow sync rules at session end.
**IMPORTANT:** Read `packages/atlas-memory/knowledge/research-index.md` — the full map of completed research.

## Why This Matters
The swarm has 13 agents generating proposals. None of them know what's already been researched. Market Analyst doesn't know SHL is the real competitor. Assessment Science doesn't know IRT params need 1000+ test-takers. Cultural Intelligence doesn't know the 26 ADHD-UX rules exist. This means: agents waste time rediscovering what we already know, and proposals contradict settled decisions.

## Task

### 1. Add Research Context Loading to autonomous_run.py

In `autonomous_run.py`, add a function that loads relevant research files per perspective agent:

```python
RESEARCH_CONTEXT_MAP = {
    "market_analyst": [
        "memory/swarm/research/competitive-intelligence-2026-04-12.md",
        "docs/research/blind-spots-analysis.md",
        "docs/SWOT-ANALYSIS-2026-04-06.md",
        "docs/product/COMPETITIVE-ANALYSIS.md",
    ],
    "assessment_science": [
        "memory/swarm/research/assessment-science-audit-2026-04-12.md",
        "docs/research/gemini-research-all.md",  # IRT section
    ],
    "cultural_intelligence": [
        "docs/research/adhd-first-ux-research.md",
        "docs/research/ecosystem-design-research.md",
        "docs/product/USER-PERSONAS.md",
    ],
    "legal_advisor": [
        "docs/research/blind-spots-analysis.md",  # #2 BrandedBy, #4 GDPR
        "docs/research/geo-pricing-research.md",  # payment law
    ],
    "communications_strategist": [
        "docs/design/BRAND-IDENTITY.md",
        "docs/design/UX-COPY-AZ-EN.md",
    ],
    "pr_media": [
        "docs/product/COMPETITIVE-ANALYSIS.md",
        "docs/research/blind-spots-analysis.md",  # #7 LinkedIn Killer framing
    ],
    "security_reviewer": [
        "docs/ATTACK-VECTORS-EXECUTIVE.md",
        "docs/SECURITY-AUDIT-INDEX.md",
    ],
}
# Agents not in the map get no extra research context (default behavior)
```

For each perspective agent, before calling the LLM:
1. Look up `RESEARCH_CONTEXT_MAP.get(agent_name, [])`
2. Read each file (truncated to first 100 lines if >100 lines)
3. Prepend to agent's system prompt: `"\n\n## Research Context (DO NOT re-research these topics — use these findings)\n\n" + file_contents`

Keep it simple. Read files, concat, prepend. No vector search, no embeddings, no RAG.

### 2. Add Settled Decisions Block

Add a constant string injected into ALL agents' prompts (not just mapped ones):

```python
SETTLED_DECISIONS = """
## Settled Decisions (DO NOT contradict or re-open)
1. Ecosystem = only moat. Not IRT, not LLM grading, not AURA score.
2. ADHD-first UX. 26 rules. No punishment. One action per screen.
3. TAM = 500-700K in AZ. Not millions.
4. B2B before B2C. LTV/CAC broken at $3/mo B2C.
5. Birbank/m10 before Stripe. AZ users don't know Stripe.
6. IRT calibration blocks B2B. Need 1000+ real responses.
7. 5→10 minimum questions. 5q mode not defensible.
8. Langfuse + Phoenix for observability.
9. Position on ecosystem, not rigor. SHL beats us on rigor.
10. Communication Law: radical truth, no hedging, caveman (300 words max).
"""
```

### 3. Test Run

After implementing 1+2, run one swarm cycle:
```bash
python -m packages.swarm.autonomous_run --mode=daily
```

If API keys aren't available for all 13 agents, run with whatever keys ARE available (even if only 3-4 agents fire). The goal is to verify:
- Research files are loaded without error
- Settled decisions appear in prompts
- Agent output references the research (not reinventing)

Capture the output. Save it to `memory/swarm/test-runs/005-research-injection-test.md`.

## Acceptance Criteria
- [ ] AC1: `RESEARCH_CONTEXT_MAP` dict exists in `autonomous_run.py` with correct file paths
- [ ] AC2: `SETTLED_DECISIONS` string injected into all agent prompts
- [ ] AC3: At least 3 agents produce output that references their injected research context
- [ ] AC4: No agent proposes something that contradicts the 10 settled decisions
- [ ] AC5: Test run output saved to `memory/swarm/test-runs/`
- [ ] AC6: Sync files updated per PROTOCOL.md

## Files to Read First
- `packages/atlas-memory/knowledge/research-index.md` — the full research map
- `packages/atlas-memory/sync/PROTOCOL.md` — sync rules
- `packages/swarm/autonomous_run.py` — where to add research loading
- `docs/COMMUNICATION-LAW.md` — the truth standard

## Files to Modify
- `packages/swarm/autonomous_run.py` — add RESEARCH_CONTEXT_MAP + SETTLED_DECISIONS + file loading
- Create `memory/swarm/test-runs/` directory if missing

## Files NOT to Touch
- Research files themselves — read only
- `apps/api/` — no backend changes
- `apps/web/` — no frontend changes
- `packages/swarm/engine.py` — don't touch core engine

## Risks
- **Risk:** Research files too large for context window → **Mitigation:** Truncate to 100 lines per file, max 3 files per agent
- **Risk:** API keys missing for test run → **Mitigation:** Run with available keys, document which agents fired
- **Risk:** Research context makes prompts too long → **Mitigation:** Measure prompt token count before/after, stay under model limit

## On Completion (from PROTOCOL.md)
1. Update `packages/atlas-memory/sync/claudecode-state.md`
2. Update `packages/atlas-memory/sync/heartbeat.md`
3. Update `packages/atlas-memory/STATE.md`
4. Update `memory/swarm/SHIPPED.md`
