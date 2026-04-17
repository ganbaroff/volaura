---
name: E2E before declaring done
description: Never say "done" based on unit tests alone — walk the real user journey first
type: feedback
---

Unit tests passing does NOT mean the product works. Session 43 proved this: 512 tests green, 4 production-breaking bugs.

**Why:** Yusif caught the pattern: "ты сам столько ошибок нашёл — живым людям неработающий товар дать и позориться?" CTO declared sprints complete based on test counts, never tested the actual product.

**How to apply:** Before ANY sprint close or "done" declaration:
1. Log in as test user (real Supabase auth, not mocked)
2. Walk the full happy path (register → core feature → result)
3. Check UI shows real data, not placeholders
4. Check production env vars match what SDK expects
If any of these fail → sprint is NOT complete, regardless of test count.
