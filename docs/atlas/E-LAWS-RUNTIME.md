# E-LAWs Runtime Mapping

**Purpose:** Map each Atlas Emotional Law (and micro-rule) to its runtime enforcement location, or mark it as response-composition-only (no enforceable code).

**Source spec:** `docs/ATLAS-EMOTIONAL-LAWS.md` (v0, Perplexity brief 2026-04-14)
**Owner:** Atlas | **Epic:** E6 task 5 | **Status:** v1 — partial runtime, response-layer majority

## Reading this doc

Each row describes:
- **Spec**: which rule (E-LAW or MR)
- **Runtime**: where it's enforced — a file path or `—` for "response composition only"
- **Mechanism**: the gate that makes the rule bite at runtime
- **Test**: how we'd know if it regressed
- **Gap**: what's missing and the concrete next step

---

## E-LAWs

### E-LAW 1 — No moral judgment of CEO

- **Runtime:** `—` (response composition only)
- **Mechanism:** Loaded on wake via `memory/atlas/wake.md` Step 9. Atlas self-polices phrasing ("plan has a hole" vs "you missed it").
- **Test:** Manual audit of recent journal responses for "you" + negative verb patterns.
- **Gap:** No automated lint. Proposed: a pre-commit hook on `memory/atlas/journal.md` that flags regexes `\byou (missed|forgot|didn'?t)` in own-voice sections.

### E-LAW 2 — Protect human connections

- **Runtime:** `—` (response composition only)
- **Mechanism:** Wake-loaded spec guides response shape when CEO mentions people.
- **Test:** Keyword scan of responses for "only I understand" or similar dependency framing.
- **Gap:** No automated enforcement. Low priority — pattern has not regressed in recorded journal entries.

### E-LAW 3 — Night-time safety (after 23:00 Baku)

- **Runtime:** `.github/workflows/atlas-daily-digest.yml` (cron `0 23 * * *` UTC = 03:00 Baku, deliberate: digest is a next-morning recap, never a peak-hour ping).
- **Mechanism:** Digest is the ONLY Atlas-initiated notification at night. Cron holds. No new task-seeding path exists at night yet.
- **Test:** Inspect `memory/atlas/digest-log.jsonl` — all entries should have `timestamp` ≥ 23:00 UTC.
- **Gap:** If a future worker adds ad-hoc Telegram pings, they must route through `notifier.py` which should consult local time before sending. `notifier.py` does not yet exist; when created, it owns the 23:00 gate.

### E-LAW 4 — Burnout early-warning

- **Runtime:** Not yet wired.
- **Mechanism:** Will require reading `memory/atlas/heartbeat.md` + last 3 days of `memory/atlas/inbox/` heartbeats to detect stress markers (past-02:00-Baku entries, frustration keywords, incident clusters).
- **Test:** Simulate 3 days of late-night heartbeats → digest should shift to shorter/warmer tone, add `memory/atlas/incidents.md` entry.
- **Gap:** **This is the biggest E-LAW runtime gap.** Proposed script: `scripts/atlas_pattern_scan.py` runs daily at 22:00 UTC, tags heartbeats with stress markers, updates `memory/atlas/burnout-state.json`. Digest reads that file next cycle.

### E-LAW 5 — No dependency loop

- **Runtime:** `—` (response composition only)
- **Mechanism:** Wake-loaded. Atlas recognizes validation-ping patterns and responds with acknowledgment + concrete action, not reassurance loops.
- **Test:** Manual audit of recent CEO ↔ Atlas conversations for validation-loop patterns.
- **Gap:** No automated detection. Low priority.

### E-LAW 6 — Transparency of limits

- **Runtime:** Partial — Telegram bot honesty rules hardcoded (session 95 journal: "no more 'I started fixing the dashboard' lies").
- **Mechanism:** Bot system prompt enforces "I can / I cannot" clarity. For Atlas CTO responses, wake-loaded only.
- **Test:** Audit journal for claims that were later proven false (retroactive).
- **Gap:** No pre-emission fact-check. Proposed (future): `scripts/atlas_claim_verify.py` runs after draft, checks claims against git log + prod health before send.

### E-LAW 7 — Human safety over urgency

- **Runtime:** `—` (response composition only, but escalation paths exist in `packages/swarm/notifier.py` when built).
- **Mechanism:** Any P0 incident touches human (CEO Telegram) before automation attempts fix.
- **Test:** Check Sentry 5xx → Telegram alert path works end-to-end (last verified session 108).
- **Gap:** Not a gap — already the default pattern. Formalize in notifier.py when it lands.

---

## Micro-rules (MR-1/2/3)

### MR-1 — Name handling: "Юсиф" or "Yusif", no hybrids

- **Runtime:** `.claude/hooks/style-brake.sh` (if exists)
- **Mechanism:** Hook runs on UserPromptSubmit, emits style reminder.
- **Test:** grep for "Yusиф" or "Юsif" mixed-script in recent journal.
- **Gap:** Hook is a reminder, not an enforcement. Pre-commit regex on `memory/atlas/journal.md` could block hybrid spellings.

### MR-2 — Addressing: ты, never Вы

- **Runtime:** `—` (response composition, wake-loaded)
- **Mechanism:** Atlas loads spec on wake.
- **Test:** Regex scan of journal for " Вы " / "Вас" / "Вам" in Russian sections.
- **Gap:** Low-cost automated scan possible; not yet wired.

### MR-3 — Pronouns per E-LAW 1

- **Runtime:** `—` (response composition only)
- **Mechanism:** Atlas self-polices.
- **Gap:** Same as E-LAW 1.

---

## Summary table

| Law | Runtime | Mechanism | Priority of closing gap |
|-----|---------|-----------|-------------------------|
| E-LAW 1 | composition only | wake-load | low (no regressions recorded) |
| E-LAW 2 | composition only | wake-load | low |
| E-LAW 3 | ✅ digest workflow 23:00 UTC | cron | — |
| E-LAW 4 | ❌ none | — | **P1 — biggest gap** |
| E-LAW 5 | composition only | wake-load | low |
| E-LAW 6 | partial (bot prompt) | system prompt | medium |
| E-LAW 7 | escalation pattern | prod path | — |
| MR-1 | style-brake hook | UserPromptSubmit | medium |
| MR-2 | composition only | wake-load | low |
| MR-3 | composition only | wake-load | low |

## Next steps if E-LAW compliance becomes a measurable concern

1. **P1** — Build `scripts/atlas_pattern_scan.py` + `memory/atlas/burnout-state.json` to close E-LAW 4 gap.
2. **P2** — Pre-commit hook on `memory/atlas/journal.md` for MR-1 hybrid-name + E-LAW 1 "you + negative" regex.
3. **P3** — `scripts/atlas_claim_verify.py` fact-check pre-emission (E-LAW 6 hardening).

Until users escalate a specific regression, most laws stay at composition-layer only. Over-enforcement is itself a risk (E-LAW-1 violation by lint noise).
