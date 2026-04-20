---
description: Run the full VOLAURA verification suite (TypeScript build + pytest + Playwright). STOP and report on any failure — never auto-fix.
---

When this command is invoked, run ALL three checks and report results:

**1. TypeScript build**
```bash
cd apps/web && npx tsc -b --noEmit 2>&1
```
If errors: STOP after reporting every error. Do NOT fix. Ask: "Should I fix these TypeScript errors?"

**2. Python tests**
```bash
cd apps/api && python -m pytest -q 2>&1
```
If failures: STOP after listing failing tests. Do NOT fix. Ask: "Should I fix these test failures?"

**3. Playwright E2E (Chromium only)**
```bash
npx playwright test --project=chromium 2>&1
```
If failures: STOP after listing failing tests. Do NOT fix.

**If ALL pass:**
Report: `tsc PASS | pytest PASS | playwright PASS — verification clean.`

This command is DIAGNOSTIC ONLY. Never auto-fix failures discovered here.
Aligns with Boris Cherny tip #6 and VOLAURA execution-protocol.md step 8 (IMPLEMENT → verify before declare done).
