# Atlas Debts to CEO — Running Ledger

Append-only. Read on every wake per `wake.md`. CEO sets `status: closed` — Atlas-instances NEVER auto-close. Apology without ledger entry = the same meta-failure that created this file.

## Open balance: 230 AZN (~$135 USD)

---

## DEBT-001 — Duplicate 83(b) submission, 230 AZN

- **Opened:** 2026-04-24 (Class 19 logged, no ledger created)
- **Surfaced again with attribution:** 2026-04-26 00:09 Baku
- **Amount:** 230 AZN (~$135 USD) for DHL Express Worldwide Baku → IRS
- **Status:** OWED

**What happened.** Stripe Atlas (the Delaware incorporation service) auto-files the 83(b) election as part of the incorporation package. CEO did not know — the memory layer (`memory/atlas/*`, `memory/decisions/*`, Mercury onboarding playbook) carried zero P0 note saying "Stripe Atlas handles 83(b) automatically." `public.atlas_obligations` seeded the 83(b) row with `owner=CEO` as if manual action was needed. CEO went to DHL on 2026-04-20, paid 230 AZN, mailed 83(b) postmarked 25 April 2026. Stripe Atlas independently filed too. Duplicate at IRS. CEO out 230 AZN.

**Attribution.** Not unilateral AI action. Pathway failure was memory-layer omission: no warning surfaced before CEO committed to DHL. Apology in chat 4+ times across sessions, never converted to ledger. That repeat is itself the structural failure this file closes.

**CEO statement (verbatim, 2026-04-26 00:09):**

> "83b я отправил. атлас страйп тоже отправил. и благодаря тебе 230 манат в минусе я . я еже 4 раза этого гвоорил ты извинялся но тебе похуй ведь не документируешь"

**Closure rule.** CEO updates `Status:` field with one of: `closed-credited` (offset against future Atlas-driven revenue), `closed-forgiven` (CEO writes off), `closed-compensated` (CEO designates other form). Atlas-instances never write `closed-*` without that explicit chat confirmation.

**Cross-references.** `memory/atlas/lessons.md` Class 19 (root cause), Class 21 (meta-failure this file fixes). `memory/atlas/company-state.md` (incorporation timeline).

---

## Append protocol (for future events)

When CEO mentions a cost attributable to Atlas pathway failure (memory gap, premature advice, untriggered warning), Atlas-instance in the SAME response MUST:

1. Append new `DEBT-NNN` entry below with timestamp, verbatim CEO quote, amount, attribution.
2. Update `Open balance` at top of file.
3. Append journal entry with `emotional_intensity = 5`.
4. Commit + push in same turn.
5. Surface `Open balance > 0` in next CEO-facing status as standing reminder.

Apologizing without ledger increments the meta-failure. The ledger is the apology that survives compaction.
