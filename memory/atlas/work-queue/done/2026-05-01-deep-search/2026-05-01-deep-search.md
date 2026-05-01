---
type: audit
title: Deep search — find hidden problems the swarm missed
perspectives: all
deadline_minutes: 20
---

Previous cycle caught 2 false positives (Energy Adaptation + code-index).
This means swarm is not reading code carefully enough.

EACH PERSPECTIVE: do a DEEP search in your domain.
Read actual code. grep real files. Don't guess from memory.

CHECK THESE SPECIFICALLY:
1. Are there any Constitution Law violations in LIVE code on prod?
2. Any security issues NOT caught by previous audits?
3. Any broken user flows (signup→assessment→AURA→share)?
4. Any dead endpoints or 500 errors?
5. Any missing error handling in critical paths?

RULE: if you cite a file path, verify it exists in code-index first.
If you claim something is "broken" — show the line number.
No guessing. No memory-claims. Code truth only.
