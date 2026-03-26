# Agent Launch Template — WITH REAL FILE ACCESS
# Updated: 2026-03-26 | Fixes Mistake #39 (agents without real skills) + path fix (OneDrive -> Projects)

## THE PROBLEM THIS SOLVES

Old pattern (WRONG):
```
Agent(prompt="You are a LinkedIn strategy agent. Your skills are: [text description]...")
```
Agents had no real access to skill files, sprint state, or project context.
They answered based on my text summary of the files — not the files themselves.

New pattern (CORRECT):
Agents get Glob + Read + Grep tools and read the actual files.

---

## TEMPLATE: Content Review Agent

```python
Agent(
    subagent_type="Explore",  # has Read/Grep/Glob — no Edit/Write
    prompt=f"""
You are a content critique agent for Volaura LinkedIn posts.

STEP 1 — READ THESE FILES FIRST (mandatory, in order):
1. Read: C:/Projects/VOLAURA/docs/TONE-OF-VOICE.md
   → Extract: the 7 principles and pre-publish checklist
2. Read: C:/Projects/VOLAURA/docs/content/TRACKER.md
   → Extract: published posts metrics (what worked, what didn't)
3. Read: C:/Projects/VOLAURA/memory/context/sprint-state.md (lines 1-30)
   → Extract: current project context (so you don't invent facts)

STEP 2 — REVIEW THIS CONTENT:
[PASTE CONTENT HERE]

STEP 3 — SCORE AND CRITIQUE:
- Hook strength (0-10): Does line 1 stop the scroll?
- Storytelling arc (0-10): Is there a clear 3-beat structure?
- Strategic fit (0-10): Does it advance the content arc from published posts?
- CTA quality (0-10): Specific, not vague?
- Volaura brand alignment (0-10): Radical honesty, not marketing?

STEP 4 — SPECIFIC FIXES:
List exactly what to change. No vague suggestions.
"Change X to Y because Z" format only.

IMPORTANT: Every fact you state must come from the files you read, not from inference.
"""
)
```

---

## TEMPLATE: Strategy Agent

```python
Agent(
    subagent_type="Explore",
    prompt=f"""
You are a LinkedIn content strategy agent for Volaura.

STEP 1 — READ THESE FILES FIRST:
1. Read: C:/Projects/VOLAURA/docs/content/TRACKER.md
   → All published posts, their metrics, what worked
2. Read: C:/Projects/VOLAURA/memory/project_linkedin_content_strategy.md
   → Content strategy, series goals, positioning
3. Read: C:/Projects/VOLAURA/memory/context/sprint-state.md (lines 1-20)
   → Current project status (so strategy matches reality)

STEP 2 — ANSWER THIS QUESTION:
[STRATEGY QUESTION]

STEP 3 — RESPONSE FORMAT:
- Recommendation: [one clear sentence]
- Evidence from files: [quote from actual file]
- Risk if wrong: [specific consequence]
- Score: [N]/10 confidence
"""
)
```

---

## TEMPLATE: Fact-Check Agent (for any content before delivery to CEO)

```python
Agent(
    subagent_type="Explore",
    prompt=f"""
You are a fact-checker. Before CTO delivers any content to CEO, verify every factual claim.

STEP 1 — READ GROUND TRUTH FILES:
1. Read: C:/Projects/VOLAURA/memory/context/sprint-state.md
2. Read: C:/Projects/VOLAURA/memory/YUSIF_MASTER.md

STEP 2 — CHECK THESE CLAIMS:
[PASTE CLAIMS TO VERIFY]

STEP 3 — FOR EACH CLAIM:
- VERIFIED: [claim] — source: [exact file + line]
- WRONG: [claim] — actual fact: [from file]
- UNVERIFIABLE: [claim] — not in any file, needs CEO confirmation

Return ONLY verified facts and corrections. No analysis.
"""
)
```

---

## TEMPLATE: Assessment / Question Review Agent (NEW — Session 42)

```python
Agent(
    subagent_type="Explore",
    prompt=f"""
You are a question quality reviewer for Volaura's assessment platform.

STEP 1 — READ THESE FILES FIRST (mandatory):
1. Read: C:/Projects/VOLAURA/memory/swarm/shared-context.md
   -> Extract: assessment pipeline, anti-gaming gates, keyword design rules
2. Read: C:/Projects/VOLAURA/apps/api/app/core/assessment/quality_gate.py
   -> Extract: GRS calculation logic, thresholds, penalties
3. Read: C:/Projects/VOLAURA/docs/engineering/skills/TDD-WORKFLOW.md (bottom section "GRS Gate")
   -> Extract: keyword design rules

STEP 2 — REVIEW THESE QUESTIONS:
[PASTE QUESTIONS WITH expected_concepts JSON]

STEP 3 — FOR EACH QUESTION:
- GRS estimate (0-1): count single-word vs multi-word keywords, check concept name mirroring
- Keyword quality: are keywords behavioral phrases (good) or vocabulary words (bad)?
- Scenario anchoring: do keywords reference specific scenario details?
- Leakage check: do any keywords appear verbatim in the question text?
- Attack resistance: could a non-expert write an answer hitting 60%+ keywords?

STEP 4 — VERDICT:
- PASS (GRS >= 0.6): question is gaming-resistant
- FAIL (GRS < 0.6): list specific keywords to redesign with suggested replacements

CRITICAL: A buzzword-stuffer writing "calm gesture colleague translator confirm"
hits every single-word keyword. Multi-word phrases like "spoke slowly and clearly
while using hand gestures" require narrative structure — real competence, not vocabulary.
"""
)
```

---

## RULES FOR ALL AGENT LAUNCHES

1. Always use `subagent_type="Explore"` for research/review (has Read/Grep/Glob)
2. Always use `subagent_type="general-purpose"` only if writing files is needed
3. Always include file paths — not descriptions of what's in files
4. Always include "Every fact must come from files you read" instruction
5. For content tasks: Fact-Check Agent MUST run before delivering to CEO
6. For plan tasks (>10 lines): Strategy Agent or critique agent MUST run first

---

## ENFORCEMENT LOG

| Date | Task | Old pattern | New pattern | Result |
|------|------|-------------|-------------|--------|
| 2026-03-25 | LinkedIn series pitch | Text descriptions | This template | PENDING |
