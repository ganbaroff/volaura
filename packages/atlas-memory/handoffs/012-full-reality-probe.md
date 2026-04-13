# Handoff 012 — Full Reality Probe (P1)

**From:** Cowork Session 9 (continued) | **To:** Atlas (Claude Code, local)
**Date:** 2026-04-13 | **Priority:** P1 — unblocks accurate planning
**CEO directive:** "передай атлас коду промпт чтобы дал всю картину"

---

## Why this exists

Cowork lives inside a sandbox with network egress blocked. Curl returns HTTP 000, WebFetch returns EGRESS_BLOCKED for `*.railway.app`, `supabase.com`, etc. Every time Cowork writes «prod is down», it may be reading its own prison wall instead of prod state.

Atlas runs locally on Yusif's machine. Atlas can:
- `curl` Railway directly (no egress block)
- `ls` and `git log` inside `mindflow/`, `brandedby/`, `life-simulator/`, `zeus/` repos (not mounted in Cowork sandbox)
- Hit Sentry / Vercel / Railway CLIs with real credentials
- Run Playwright locally
- Read files and configs Cowork cannot see

The previous audit (Handoff 011) called prod DOWN based on curl HTTP 000 from the sandbox. Verification report (`packages/atlas-memory/knowledge/verification-2026-04-13.md`) shows that was sandbox blindness, not outage. Cowork needs Atlas to run ground-truth checks and write them back where Cowork can read them.

---

## What Atlas Must Do

Execute **all 9 probes**. Every result goes into `packages/atlas-memory/sync/claudecode-state.md` under a new section **"Reality Probe 2026-04-13"**. One file, one section. Format: markdown. Include raw command output where helpful.

### Probe 1 — VOLAURA Production Health (10 min)

Commands, run in sequence:

```bash
curl -sS -o /tmp/h.json -w "HTTP:%{http_code} TIME:%{time_total}s\n" https://volauraapi-production.up.railway.app/health
curl -sS -o /tmp/r.json -w "HTTP:%{http_code}\n" https://volauraapi-production.up.railway.app/
curl -sS -o /tmp/v.json -w "HTTP:%{http_code}\n" https://volauraapi-production.up.railway.app/api/v1/competencies
cat /tmp/h.json
cat /tmp/r.json
echo "---"
railway status || true
railway logs --tail 50 || true
```

Also: frontend health. Hit `https://volaura.co/` (or whatever domain is in `apps/web/.env.production`) with curl and record HTTP code + size.

Report: HTTP codes, response bodies (truncate JSON to 500 chars), Railway status, last 20 deploy log lines. **Is prod actually alive or dead?**

### Probe 2 — Sentry Reality Check (5 min)

```bash
# Using Sentry CLI or curl with auth token
sentry-cli projects list || true
```

Then via Sentry dashboard / API: event count last 7 days, last 24 hours, last event timestamp, organization slug + project slug. Confirm DSN on Railway points to the right project (not MindShift).

Report: event count per day for last 7 days. If 0 — dig why: is SDK initialized, is DSN correct, is network blocked?

### Probe 3 — Standalone Products — do they exist, what state (20 min)

For each of these four repos (paths are guesses — Atlas knows real paths):

1. `~/projects/mindflow/` (MindShift)
2. `~/projects/brandedby/` (BrandedBy)
3. `~/projects/life-simulator/` (LifeSimulator)
4. `~/projects/zeus/` (ZEUS)

For each repo report:
- Absolute path
- Branch + last 3 commits (`git log --oneline -3`)
- Uncommitted changes (`git status --short | wc -l`)
- File count by language
- Last deploy / last activity (check CI status, deploy logs, or mtime of built artifacts)
- Test suite state: `npm test` or `pytest` — total tests / passing / failing
- Deploy target (Railway / Vercel / Cloudflare / App Store / Firebase) and whether live URL responds 200
- Integration with VOLAURA: does this repo write to `character_events` or read `aura_scores`? Grep for `character_events`, `volaura`, `aura_scores`, `EXTERNAL_BRIDGE_SECRET`.

**Honest readiness rating 0–100** per product, with reasoning. Cowork's previous 75–95% numbers came from a 2026-04-12 scan and are not trusted.

### Probe 4 — VOLAURA Test Suite Ground Truth (10 min)

```bash
cd apps/api && pytest -q 2>&1 | tail -20
cd apps/web && npm test -- --run 2>&1 | tail -30
```

Report: pass/fail counts for backend and frontend. Any red tests — name them.

### Probe 5 — Playwright E2E (15 min)

If `tests/e2e/full-journey.spec.ts` exists, run it:

```bash
npx playwright install chromium  # if not already
npx playwright test tests/e2e/full-journey.spec.ts --reporter=line 2>&1 | tail -30
```

If the file doesn't exist or fails — say so, include the error, don't silently skip. This is Beta Gate 3.

### Probe 6 — Constitution Checker, Full Report (5 min)

```bash
cd packages/swarm
python3 -c "from tools import constitution_checker as cc; print(cc.run_full_audit())" > /tmp/constitution.txt
cat /tmp/constitution.txt
```

Cowork's verification report flagged 15 violations but marked most as false positives (teaching-comments, boundary `duration=800`). Atlas has to look at each flag and say: real issue vs noise. Real issues get fixed in the next sprint.

### Probe 7 — Railway Environment Variables Diff (10 min)

```bash
railway variables | sort > /tmp/railway-vars.txt
cat apps/api/.env | grep -v '^#' | grep -v '^$' | cut -d= -f1 | sort > /tmp/local-vars.txt
diff /tmp/railway-vars.txt /tmp/local-vars.txt
```

Report: count of keys only in Railway, only in local .env, and any suspicious absences (GEMINI_API_KEY, SENTRY_DSN, SUPABASE_SERVICE_KEY, LANGFUSE_*, any MindShift-bridge secrets).

### Probe 8 — Git Index + Repo Health (5 min)

Cowork saw `fatal: unknown index entry format 0x74000000` in the mounted repo. This may just be a Cowork-sandbox artifact, or it could be a real corruption on the live checkout.

```bash
git fsck --full 2>&1 | head -20
git status 2>&1 | head -20
git log --oneline -5
```

Report: is the real repo healthy?

### Probe 9 — Cross-Product Bridge Audit (15 min)

In VOLAURA repo:

```bash
grep -rn "character_events\|EXTERNAL_BRIDGE_SECRET\|mindshift\|life_simulator\|brandedby\|zeus" apps/api/app --include="*.py" | grep -v __pycache__ | wc -l
grep -rn "emit_" apps/api/app/services/ecosystem_events.py | head -10
```

In each standalone repo, grep for references to VOLAURA, `character_events`, `aura_scores`. Report: which products actually read or write cross-product data vs which are advertised as connected but code is absent.

---

## Acceptance Criteria

```
AC-1: Section "Reality Probe 2026-04-13" exists in packages/atlas-memory/sync/claudecode-state.md
  with all 9 probe results filled in, raw command output included.

AC-2: For every claim that contradicts a prior audit finding, Atlas writes
  "CORRECTS PRIOR CLAIM: [what was claimed] → [ground truth]"

AC-3: Each of 4 standalone products has:
  - absolute path
  - last commit date
  - live URL + HTTP response
  - cross-product integration verdict (real / plumbing-only / none)
  - honest readiness % 0-100 with 2-3 line justification

AC-4: Constitution checker's 15 flags each marked REAL / NOISE with one-line reason.

AC-5: Sentry event count for last 7 days is a number, not "unknown".

AC-6: Atlas updates sync/heartbeat.md after finishing (instance, timestamp, one-line summary).

AC-7: If any probe genuinely blocks Atlas (missing credential, missing repo),
  write "BLOCKED: [reason]" instead of faking data. Partial report > fake report.
```

---

## What Cowork will do after

1. Read `sync/claudecode-state.md` → Reality Probe section.
2. Revise `packages/atlas-memory/knowledge/verification-2026-04-13.md` with corrections.
3. Revise `packages/atlas-memory/plans/ROAD-TO-100-2026-04-13.md` using real readiness %s.
4. Rewrite Handoff 011 if prod is confirmed alive (drop Task 0, keep the rest).
5. Return to CEO with a plan built on ground truth, not sandbox guesses.

---

## Notes

- No coding in this handoff. Only data-gathering. Do NOT fix anything during the probe — write findings, that's it. Fixing comes in Handoff 013 once we have a truthful baseline.
- If a probe takes > 20 minutes to get data, skip it with `BLOCKED: took too long — rerun with higher priority`. Don't burn hours.
- Honesty > completeness. Missing data is fine. Fake data is not.
- Atlas should read `packages/atlas-memory/knowledge/verification-2026-04-13.md` first to see what Cowork already knows and where Cowork is blind.

**Total expected time: 90–120 min.** Report goes into `sync/claudecode-state.md` under heading `## Reality Probe 2026-04-13`.
