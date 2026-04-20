# Inbox — Perplexity MASTER BRIEF 2026-04-15
**From:** Perplexity (CTO-Brain) via CEO courier · **To:** Atlas + Cowork (both read) · **Priority:** P0 · **Received:** 2026-04-15

## Summary
Perplexity tested volaura.app signup flow end-to-end as a real user yesterday. Found 6 bugs. Tropa broke at signup — assessment/score/badge never reached. First real-user walkthrough by non-CEO = now the ONLY metric that matters. Everything else secondary until tropa works.

## Atlas assignments (priorities 1→4)

**P1 — Layout collapse on /signup + landing page.** Desktop signup renders in ~100px narrow column, every word on separate line. Radio buttons "Siz kimsiniz?" overlap — two options rendered on top of each other. Landing subtitle also vertical word-per-line. Same CSS root bug in all three places. DONE = /signup desktop renders normally, all fields readable, radios don't overlap, landing subtitle one line.

**P2 — Signup error handling.** Spinner appeared then silently returned without feedback. User can't see what failed. DONE = all error cases (invalid invite, duplicate email, weak password) show text message. Constitution Law 1: purple `#D4B4FF` or amber `#E9C400`, NEVER red.

**P3 — D-001 Railway redeploy verification.** Telegram LLM bug fix not yet deployed. DONE = redeploy applied + bot responds + digest line reports status.

**P4 — D-004 character_events bridge smoke test.** MindShift writes event → VOLAURA sees row in table. DONE = one green test + fact documented.

## Cowork assignments
1. After Atlas closes P1 layout — organize first live non-CEO user test on tropa. Fix where they stumble.
2. Invite-gate decision — prepare ONE question for CEO with TWO options (disable for closed alpha / auto-issue by email). CEO picks, Atlas implements.
3. Update `sprint-state.md` with bugs #1–#6 as open tasks with priorities.
4. E7 BrandedBy — remind CEO ONCE: "need 15 min for concept doc." No more. Don't pester.

## Vision Canon (locked)
"Quality, adaptivity, living Atlas > speed and feature count." Not up for debate this sprint. External deadlines (WUF13, GITA May 27) don't override Canon — they mean be selective, not chase everything.

WUF13 goal: working first tropa + live MindShift↔VOLAURA signal + 5-product narrative. Not scale, not enterprise.

## Reporting protocol
- Atlas after each closed bug: one line in digest — "БАГ #N closed. DONE: [criterion]. Commit: [hash]."
- Cowork after sprint-state update: one message to CEO — "updated, top 3 open questions needing your decision today."
- Either side blocked >30 min → escalate via CEO to Perplexity.

## Next sync
When first live tropa passes by non-CEO user.

Consumed by inbox-consumer: 2026-04-20T21:01:26+00:00 · intent=chat
