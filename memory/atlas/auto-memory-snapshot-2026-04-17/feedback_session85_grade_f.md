---
name: Session 85 Grade F — lessons
description: 8 deploys, 10 errors, CEO caught every miss. Two external models gave F. Core failure: solo execution + no pre-analysis + asking CEO to test.
type: feedback
---

# Session 85: Grade F — What Went Wrong and How to Never Repeat

## The 5 Rules (burned into memory)

1. **BEFORE changing ANY config:** `grep -rn` ALL files that reference it. Count. Fix ALL in one pass. NEVER deploy a partial fix.

2. **Max 2 deploys per issue.** If 2nd deploy fails → STOP. Analyze. Grep. Ask agent. Do NOT try a 3rd variation.

3. **NEVER ask CEO to test.** CEO is not QA. Use Playwright MCP. "Clear cache and check" = CTO failure.

4. **NEVER evaluate CEO solo.** External models required. CTO mistakes ≠ CEO score. CLASS 5 + CLASS 11 = reputation damage.

5. **baseUrl changes:** Read generated client paths FIRST: `grep -rn "url:" apps/web/src/lib/api/generated/sdk.gen.ts | head -5`. Understand structure BEFORE editing.

## Why It Happened

Root cause: CLASS 3 (16th instance). I jumped to fixing without analyzing. I treated each CEO error report as a new problem instead of ONE systemic problem requiring ONE systemic grep.

**Why:** I wanted to show speed. Speed without understanding = 8 useless deploys.

**How to apply:** Before ANY code change: (1) grep the pattern across ALL files, (2) count matches, (3) fix ALL in one commit, (4) verify with Playwright, (5) deploy ONCE.

## External Verdicts

- **Gemini 2.0 Flash:** 10 errors. 3 HIGH. Proposed CLASS 13 (tool ignorance).
- **NVIDIA Nemotron Ultra 253B:** Grade F. "Systematic failure. Role should be reconsidered."
