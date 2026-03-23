# Continuous Learning Protocol — Volaura Edition
# Source: everything-claude-code (affaan-m) — Stop Hook pattern
# Use this: automatically at session end (STEP 0.5)

## Concept
Every session Claude should extract reusable patterns and update the knowledge base.
This is what makes each session smarter than the last.

## What to Extract at Session End

### Pattern Types (always check for these)

1. **Error Resolution**
   - Was a bug fixed? → Document in mistakes.md: what caused it, how it was caught, how to prevent
   - Pattern format: "When you see [symptom] in [context], the cause is [root] and fix is [action]"

2. **Process Improvements**
   - Did a step in the algorithm save time? → Note in patterns.md under "Process Patterns"
   - Did a step waste time (no value added)? → Note for algorithm improvement in DECISIONS.md

3. **Yusif Corrections**
   - Did Yusif correct Claude? → Always add to mistakes.md immediately
   - He's right 90% of the time. Don't debate. Fix and document.

4. **Code Patterns**
   - Found a better way to write a recurring pattern? → Add to patterns.md "Code Patterns"
   - Example: "isMounted ref pattern prevents memory leaks in polling components"

5. **DSP Calibration**
   - Did the DSP winner path perform as predicted?
   - If off by >10 points: log in DECISIONS.md under DSP Calibration table
   - Adjust persona influence weights if a persona was consistently right/wrong

## Session End Checklist (STEP 0.5 — non-negotiable)

```
□ memory/context/sprint-state.md  → Update "Last Updated" + current position
□ memory/projects/volaura.md      → Update "Current Sprint Status"
□ memory/context/deadlines.md     → Check milestone checkboxes
□ memory/context/mistakes.md      → Add any new mistakes (even small ones)
□ memory/context/patterns.md      → Add any new patterns discovered
□ docs/EXECUTION-PLAN.md          → Mark [x] on completed items
□ docs/DECISIONS.md               → Add retrospective if sprint step completed
```

**Yusif has caught Claude skipping this TWICE. It is non-negotiable.**
The cost of not updating = next session starts blind and repeats mistakes.

## Confidence Degradation Rule

A pattern that hasn't been validated in 3+ sessions should be marked as `[needs revalidation]`.
A pattern that has been validated 5+ times should be marked as `[established]`.

## Algorithm Evolution Rule

At the end of every sprint, ask:
- Did any step in Operating Algorithm v3.0 add zero value? → Propose removal in DECISIONS.md
- Was there a gap not covered by the algorithm? → Propose new step
- Did a council persona never contribute useful dissent? → Propose weight reduction

Current version: v3.0. Changes require entry in docs/DECISIONS.md with version bump.
