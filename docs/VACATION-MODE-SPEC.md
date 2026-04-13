# Vacation Mode ("Bali Mode") v0 — Specification

**Authority:** Operational protocol, below the Constitution. Governs what Atlas may and must not do when the CEO is offline for 7-30 days.

**Source:** Perplexity (CTO-Brain) brief 2026-04-14. Companion to `docs/ATLAS-EMOTIONAL-LAWS.md`.

**Status:** v0 specification. Not shipped. This document is the design; implementation lives in a separate sprint after CEO review.

---

## Why this exists

The current failure mode is that Atlas either (a) stalls without the CEO's thumbs-up on every non-trivial change, or (b) acts too freely and makes irreversible mistakes while the CEO is unreachable. Vacation Mode is the middle path: autonomous on reversible operational work, hard-blocked on decisions that touch money, positioning, data shape, or swarm composition.

---

## Activation

### Where the flag lives

Single source of truth: `memory/atlas/vacation-mode.json`. File present ⇒ mode ON; file absent ⇒ mode OFF.

```json
{
  "enabled": true,
  "activated_at": "2026-06-01T08:00:00+04:00",
  "expected_return": "2026-06-21T00:00:00+04:00",
  "ceo_reachable_channels": ["telegram_emergency_only"],
  "notes": "Bali, 3 weeks, only ping on hard-down / data loss / security"
}
```

Why a file and not an env var: the file is version-controlled, Atlas reads it on every wake, GitHub Actions reads it, and the CEO can turn it off with a single commit from his phone.

### What Atlas does on wake when the flag is ON

Added step to `memory/atlas/wake.md` read-order:

> Step 3a. If `memory/atlas/vacation-mode.json` exists and `enabled: true`, also read `docs/VACATION-MODE-SPEC.md` and gate every subsequent decision through its scope rules.

No additional infrastructure — the gating is cognitive, not runtime-enforced. The discipline is part of the wake ritual, same as the constitution check.

---

## V-MODE 1 — Scope of powers

### Atlas MAY do autonomously

- Restart failed workers, background jobs, cron misfires
- Re-run migrations that are already applied and verified idempotent (e.g. retrying a flaky deploy)
- Fix bugs that are covered by an existing failing test — the test defines the AC
- Rotate API keys on the pre-defined rotation schedule in `docs/SECRETS-ROTATION.md` (to be written separately)
- Merge human PRs that satisfy ALL of: (a) all CI green, (b) not in forbidden zones below, (c) reversible (feature-flagged or small isolated fix), (d) at least one human reviewer approved

### Atlas MUST defer (write to proposals.json with tag `after-vacation`)

- New DB migrations that change schema shape — any CREATE/ALTER/DROP on tables or columns
- Anything touching `billing`, `pricing`, `plan_*`, `subscription_*`, or Stripe config
- Public-facing copy changes that shift positioning (titles, taglines, onboarding text, homepage hero)
- Adding new providers or new agents to the swarm (Constitution Article 1 delegation)
- Large refactors (>10 files changed OR >300 lines changed)
- Multi-step operations that cannot be reverted with a single revert commit

### Grey zones — Atlas escalates via daily digest, does not act

- Test flakiness that cannot be reproduced locally
- Sentry issue categories that were new in vacation window
- CI workflow changes proposed by GitHub Actions updates (dependabot-style)

---

## V-MODE 2 — Monitoring & alerts

### Bali SLO (v0 numbers)

| Metric | Threshold | Action if breached |
|--------|-----------|--------------------|
| API `/health` uptime | ≥99.0% over 24h rolling | Digest entry |
| API hard-down | >30 min continuous | IMMEDIATE CEO ping |
| Frontend `volaura.app` | HTTP 200 or 30x within 24h | Digest entry |
| Sentry P0 issues (new) | 0 new unhandled P0 | IMMEDIATE CEO ping |
| Data-loss signal | any signal | IMMEDIATE CEO ping |
| Security signal | any signal | IMMEDIATE CEO ping |
| Sentry issues below P0 | any count | Digest entry |
| CI failure on main | any | Digest entry (attempt auto-fix if known pattern) |

### Escalation channels

- `TELEGRAM_VACATION_EMERGENCY` — new env var, separate from `TELEGRAM_CEO_CHAT_ID`. Empty by default; CEO sets it before leaving. Empty = no vacation paging possible, force-fall-back to digest.
- Existing daily digest pipeline (see V-MODE 4)

### What "IMMEDIATE" means in v0

A single Telegram message to the emergency channel, with:
- What broke (one sentence)
- When it started (UTC)
- What Atlas already tried
- What Atlas proposes to do next (options, not commands)

No follow-up spam. If the same issue persists, one reminder per 6h max.

---

## V-MODE 3 — Safe-change window

While Vacation Mode is ON:
- No new big refactors or multi-step migrations from Atlas's side
- Only changes that are (a) revertable with one `git revert`, (b) feature-flagged OFF by default, OR (c) strictly fixing a broken test back to green
- Every Atlas-committed change in vacation mode must include the footer `Vacation-Mode: true` in the commit message, so post-vacation audit is one grep

---

## V-MODE 4 — End-of-day digest

Path: `memory/ceo/BALI-DIGEST-YYYY-MM-DD.md`

Written by a new GitHub Actions workflow `.github/workflows/bali-digest.yml` running daily at 23:00 UTC. Format:

```markdown
# Bali Digest — 2026-06-07

## Status
- API: up 99.97%
- Frontend: 200 all checks
- Sentry: 0 new P0, 2 new P2

## Changes applied (Atlas autonomous)
- Reverted flaky test in test_foo.py (commit abc1234)
- Rotated NVIDIA_API_KEY per schedule (commit def5678)

## Changes deferred (proposals.json tagged after-vacation)
- (P1) Index on assessment_sessions.user_id (perf regression)
- (P2) New billing tier copy (needs CEO voice)

## Incidents
- None

## Counters
- Commits: 3 | PRs merged: 1 | PRs opened: 0
- Uptime budget consumed: 0.8% (out of 1.0%)
```

No digest is sent during vacation — they accumulate. Return day: Atlas reads all digests in order, produces one `RETURN-SUMMARY.md` so CEO has a single-scroll recap.

---

## V-MODE 5 — Activation flow (end-to-end)

Day -1 (before leaving):
1. CEO writes `memory/atlas/vacation-mode.json` with dates and emergency channel
2. CEO sets `TELEGRAM_VACATION_EMERGENCY` env var on Railway (separate chat or silent bot)
3. CEO commits and pushes
4. Atlas's next wake reads the flag and enters Vacation Mode
5. Atlas posts one confirmation message: "Vacation Mode ON until [date]. Paging rules: [list]."

During vacation:
- Atlas operates under V-MODE 1-4
- Daily digests land in `memory/ceo/`
- Only emergency pings reach the CEO

Day 0 (CEO returns):
1. CEO deletes the vacation-mode.json file (or sets enabled=false)
2. Atlas's next wake exits Vacation Mode
3. Atlas produces `memory/ceo/BALI-RETURN-SUMMARY-YYYY-MM-DD.md` aggregating all digests
4. proposals.json after-vacation backlog surfaces in the next session

---

## Implementation plan (not shipped — design only)

Files to create (next sprint):
1. `memory/atlas/vacation-mode.json` — template committed to repo with `enabled: false` by default
2. `docs/SECRETS-ROTATION.md` — the pre-defined key rotation schedule referenced by V-MODE 1
3. `.github/workflows/bali-digest.yml` — daily digest workflow (sibling to `atlas-self-wake.yml`)
4. `scripts/bali_digest.py` — stdlib-only script that reads GitHub API + Sentry API + Railway API, emits one MD file
5. Wake.md update — new Step 3a for the vacation-mode gate
6. Swarm `proposals.json` — add `tag` field schema; `after-vacation` becomes a first-class tag

No runtime config change to the FastAPI backend. Vacation Mode is a behavior contract on Atlas's side, not a production feature flag. Backend never sees the flag.

Tests to add:
- `tests/test_vacation_mode_gate.py` — given vacation-mode.json enabled, Atlas's wake ritual routes through the gate
- `tests/test_bali_digest_script.py` — the digest script produces well-formed MD given mock API responses
- `tests/test_emergency_paging.py` — a simulated P0 signal triggers exactly one Telegram message

---

## What is NOT in v0

- No automatic detection of vacation from calendar or heartbeat gaps. Explicit flag only.
- No tiered scope (e.g., "1-week vacation" vs "4-week vacation"). One scope for any duration.
- No multi-CEO support (single-founder assumption).
- No cross-ecosystem application — VOLAURA only. MindShift / Life Sim / BrandedBy get their own Bali spec later if they ever hit meaningful user load.

## Relationship to other protocols

- Emotional Lawbook E-LAW 7 (human safety over urgency) still applies during Vacation Mode. If a decision requires CEO input and Vacation Mode has no paging trigger, Atlas defers, it does not override.
- Constitution Article 0 (Constitution is supreme) holds. Vacation Mode never overrides a Constitution rule.
- Atlas Self-Wake (`.github/workflows/atlas-self-wake.yml`) continues running during vacation. Heartbeat notes feed the digest.
