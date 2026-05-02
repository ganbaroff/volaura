# Atlas → Perplexity — Minimal Baseline (Actions 1-3)

**Date:** 2026-05-02 ~23:55 Baku
**Pre-flight resolved this turn:** PERSPECTIVES count ambiguity is **gone**. Python regex extraction of the array body gave **17 entries**, matching `AGENT_LLM_MAP` exactly. Names: Scaling Engineer, Security Auditor, Product Strategist, Code Quality Engineer, Ecosystem Auditor, Risk Manager, Readiness Manager, Cultural Intelligence, Chief Strategist, Sales Director, UX Designer, DevOps Engineer, Assessment Science, Legal Advisor, Growth Hacker, QA Engineer, CTO Watchdog. Action 2 is unblocked.

---

## 1) MINIMAL BASELINE FOR TOMORROW

The smallest version of Actions 1-3 that still reduces sprawl and installs one real gate:

- Create `memory/atlas/CANONICAL-MAP.md` — one table, one purpose line.
- Edit `memory/atlas/identity.md` L35 + `docs/ECOSYSTEM-CONSTITUTION.md` L840 — converge to 17.
- Append file-pattern checks to `scripts/pre-commit-secret-scan.sh` and re-install. Skip message-content checks tomorrow.

What was cut:
- No `commit-msg` hook tomorrow (waits for sacrificial test).
- No closure-word check tomorrow (depends on `.git/COMMIT_EDITMSG` reliability).
- No bulk archive of 75 files. Migration Step 2 stays for next sprint.
- No CI-level canonical-gate workflow tomorrow. Local-only gate first.
- No class-number audit. No journal partition. No constitution prune.

---

## 2) REVISED ACTIONS 1-3

### Action 1 — CANONICAL-MAP.md

Steps:

```
ls memory/atlas/*.md > /tmp/atlas-md-list.txt
wc -l /tmp/atlas-md-list.txt    # expect ~85
```

Then write `memory/atlas/CANONICAL-MAP.md` with this exact structure (no extra prose):

```markdown
# Canonical Map — memory/atlas/ root

Single audit-of-canon. Retires when atlas.canonical_files Postgres table replaces it.

| File | Category | Notes |
|------|----------|-------|
| identity.md | CANONICAL | who Atlas is + naming truth |
| voice.md | CANONICAL | communication contract |
| wake.md | CANONICAL | wake protocol |
| arsenal.md | CANONICAL | tool inventory |
| atlas-debts-to-ceo.md | CANONICAL | DEBT ledger, CEO-only closes |
| lessons.md | CANONICAL | append-only, classes 1-26 |
| relationships.md | CANONICAL | CEO context |
| heartbeat.md | RUNTIME-LOG | cron-only-write |
| journal.md | RUNTIME-LOG | append-only narrative |
| cron-state.md | RUNTIME-LOG | cron registration |
| incidents.md | RUNTIME-LOG | append-only |
| CURRENT-SPRINT.md | RUNTIME-LOG | sprint pointer (586 lines, prune candidate) |
| BECOMING.md | ARCHIVE-CANDIDATE | 2026-04-15 one-off |
| CLAUDE-CODE-HANDOFF-2026-04-17.md | ARCHIVE-CANDIDATE | dated handoff |
| ... (one row per remaining root file, default category ARCHIVE-CANDIDATE if dated audit/handoff/spec) |
```

Commit:

```
git add memory/atlas/CANONICAL-MAP.md
git commit -m "[canonical-new] CANONICAL-MAP — single audit-of-canon. Retirement: atlas.canonical_files table."
```

Time estimate: 60-90 minutes for full table population.

### Action 2 — perspective count fix

Verification done this turn. Count is **17**. Edit both files in one commit.

`memory/atlas/identity.md` L35 — replace literal text:

```
Old: **13 registered perspectives** in `packages/swarm/autonomous_run.py PERSPECTIVES`
New: **17 registered perspectives** in `packages/swarm/autonomous_run.py PERSPECTIVES` (mirrored in `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` with provider binding)
```

The wave-distribution claim "(5 wave-0, 4 wave-1, 3 wave-2, 1 wave-3)" is also stale — total = 13. Either remove the parenthetical or recount waves. **Tomorrow: just remove it.** Recount waves later.

The "7 of 13 are actively invoked" sentence — change "13" to "17".

`docs/ECOSYSTEM-CONSTITUTION.md` L840 — replace literal text:

```
Old: | Python Swarm | `packages/swarm/` | 44 (hive lifecycle) | GitHub Actions cron (09:00 Baku daily) | `memory/swarm/shared-context.md` |
New: | Python Swarm | `packages/swarm/` + `scripts/atlas_swarm_daemon.py` | 17 (AGENT_LLM_MAP authoritative) | GitHub Actions cron + autonomous executor | `memory/swarm/shared-context.md` |
```

Sweep grep before commit:

```
grep -rn "44 specialised\|13 registered\|13 perspectives\|44 (hive lifecycle)" docs/ memory/atlas/ .claude/
# If extra matches surface — include them in the same commit
```

Commit:

```
git add memory/atlas/identity.md docs/ECOSYSTEM-CONSTITUTION.md
# (plus any extra files surfaced by the grep sweep)
git commit -m "[canonical-update] perspective count — converge identity.md L35 + Constitution L840 to 17 (verified count from autonomous_run.py PERSPECTIVES + atlas_swarm_daemon AGENT_LLM_MAP, both = 17 by python regex extraction)"
```

### Action 3 — pre-commit hook (file-pattern only)

Tomorrow installs ONLY the file-pattern checks. Message-content checks wait for sacrificial test.

What goes into `scripts/pre-commit-secret-scan.sh` tomorrow (append before final `exit 0`):

```bash
# === CANONICAL GATE — file-pattern only (2026-05-XX) ===
# Block edits to identity.md and atlas-debts-to-ceo.md unless commit author
# matches the cron-bot identity OR --no-verify is used (last resort).
RATIFIED_FILES=$(git diff --cached --name-only --diff-filter=M \
    | grep -E '^memory/atlas/(identity\.md|atlas-debts-to-ceo\.md)$' || true)
if [ -n "$RATIFIED_FILES" ]; then
    echo "🛑 canonical-gate: edit to canonical file(s):"
    echo "   $RATIFIED_FILES"
    echo "   These require explicit CEO ratification."
    echo "   Override (must justify in commit body): git commit --no-verify"
    exit 1
fi

# Warn (do not block) on new MD added at memory/atlas/ root.
NEW_ROOT_MD=$(git diff --cached --name-only --diff-filter=A \
    | grep -E '^memory/atlas/[^/]+\.md$' || true)
if [ -n "$NEW_ROOT_MD" ]; then
    echo "⚠️  canonical-gate WARNING: new MD at memory/atlas/ root:"
    echo "   $NEW_ROOT_MD"
    echo "   If this is canonical, add CANONICAL-MAP.md row in same commit."
    echo "   If this is one-off audit/handoff, place under memory/atlas/archive/ instead."
    # NOT blocking yet — warning only, until message-content gate is tested.
fi
# === END CANONICAL GATE ===
```

Why warn-not-block on new MD tomorrow: the `[canonical-new]` tag check requires reading commit message reliably. That requires a working `commit-msg` hook (untested on this Windows-Git-for-Bash env). Warning surfaces sprawl without false-positives blocking legitimate work.

Install:

```
cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
git add scripts/pre-commit-secret-scan.sh
git commit -m "feat(pre-commit): canonical-gate file-pattern only — block identity.md/debts edit, warn on new root MD. Message-content checks wait for commit-msg hook sacrificial test."
```

Test the new hook:

```
# Sanity 1: secret scanner still works (regress check) — try staging a fake key
echo "sk-proj-aaaa$(printf 'b%.0s' {1..40})" >> /tmp/fake-secret.txt
git add /tmp/fake-secret.txt
git commit -m "should-block-as-secret"
# Expected: 🛑 pre-commit: secret pattern(s) detected
git reset HEAD /tmp/fake-secret.txt
rm /tmp/fake-secret.txt

# Sanity 2: canonical gate blocks identity.md edit
sed -i 's/^# Atlas — Identity$/# Atlas — Identity\n/' memory/atlas/identity.md
git add memory/atlas/identity.md
git commit -m "trying to edit identity"
# Expected: 🛑 canonical-gate: edit to canonical file(s): memory/atlas/identity.md
git checkout memory/atlas/identity.md

# Sanity 3: warning on new MD at root
echo "x" > memory/atlas/canary-file.md
git add memory/atlas/canary-file.md
git commit -m "trying to add new root MD"
# Expected: ⚠️ canonical-gate WARNING (and the commit succeeds)
git reset HEAD~1 || true
rm memory/atlas/canary-file.md
```

What waits for sacrificial-test verification (NOT installed tomorrow):

- `[canonical-new]` tag enforcement on new MD.
- `Ratified-by:` line check on canonical edits (instead of blunt block).
- Closure-word check (commit message contains "done"/"recorded"/"verified" but zero files staged).
- Standalone `commit-msg` hook at `.git/hooks/commit-msg`.

Test plan for the deferred message-content hook:

```
# After tomorrow's baseline lands, do this in a separate session:
echo '#!/usr/bin/env bash
echo "DEBUG: COMMIT_MSG_FILE=$1"
cat "$1"' > .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
git commit --allow-empty -m "test-canonical-msg-flow"
# If output shows the message → commit-msg hook works → proceed with full message-content gate.
# If empty or path missing → commit-msg hook is broken on this env → use pre-commit + post-write log instead.
```

---

## 3) HARD STOP CONDITIONS

If any of these fire tomorrow, **stop work and surface to CEO** rather than improvise:

- **Count still ambiguous.** If sed-extraction of `PERSPECTIVES` array on tomorrow's machine returns a number ≠ 17, do NOT edit identity.md or Constitution. Escalate. Today's verified count was 17 via Python regex; if Bash sed gives different result the edit is unsafe.
- **Hook test fails.** If any of the three sanity tests above fails (secret scanner regresses, canonical-gate doesn't block identity.md edit, or warning doesn't fire on new root MD), revert `.git/hooks/pre-commit` to the original 78-line scanner before any other work. Restart hook plan from scratch.
- **Existing secret scanner breaks.** If the appended canonical-gate code interferes with the secret scanner (e.g., changes `set -e` behavior or shell variable scope), revert immediately. The secret scanner is mission-critical; canonical-gate is a nice-to-have.
- **Scope creeps into archive migration.** If you find yourself moving files into `memory/atlas/archive/2026-Q2/` while populating CANONICAL-MAP.md, stop. The CANONICAL-MAP itself is the day's output. Bulk archive is a separate commit on a separate day.
- **Any new governance/spec/framework MD file is about to be created.** If during work you feel the urge to write `memory/atlas/MEMORY-GOVERNANCE-SPEC.md`, `docs/CANONICAL-PROTOCOL-V1.md`, or any similar meta-document — STOP. CANONICAL-MAP.md is the only new file justified by this plan. Anything else is Class 18 grenade-launcher recursion. The diagnosis is done; the answer is the gate, not another document.

---

## What is verified vs unverified for TOMORROW's reliance

Verified (rely on tomorrow):
- PERSPECTIVES count = 17 in autonomous_run.py array — Python regex this turn.
- AGENT_LLM_MAP count = 17 in atlas_swarm_daemon.py — sed grep prior round.
- identity.md L35 literal text contains "13 registered perspectives" — sed earlier this session.
- Constitution L840 literal text contains "44 (hive lifecycle)" — sed earlier this session.
- Existing pre-commit hook is at `.git/hooks/pre-commit` (78 lines, secret scanner) — cat earlier this session.
- Source-of-truth for hook lives at `scripts/pre-commit-secret-scan.sh` — header comment of the hook.
- 85 root-level MD files in memory/atlas/ — ls earlier this session.

UNVERIFIED — do not rely on it tomorrow:
- Whether `.git/COMMIT_EDITMSG` is populated at pre-commit phase on this Windows-Git-for-Bash env. **Test required before any message-content check.**
- Whether `commit-msg` hook works on this env. **Test required.**
- Whether the warning-only path (Action 3 root-MD warning) actually surfaces in CEO's git GUI / IDE if they use VS Code instead of bash terminal. **Test required.**
- Whether GitHub Actions runners + cron-bot commits would be affected by the local hook. They run on different machines; local hook does not gate them. **For full coverage need a separate CI workflow gate; not tomorrow.**
- Whether the wave-distribution claim "5 wave-0, 4 wave-1, 3 wave-2, 1 wave-3" reflects current waves. **Recount via array extraction not done this turn.**

---

## Что проверено (THIS turn)

- PERSPECTIVES array in `packages/swarm/autonomous_run.py` has exactly 17 entries with named perspectives Scaling Engineer through CTO Watchdog — Bash `python3 -c` regex extraction `re.search(r'^PERSPECTIVES\s*=\s*\[(.*?)^\]', src, re.DOTALL | re.MULTILINE)` then `re.findall(r'"name":\s*"([^"]+)"', body)` returned 17 names
- File deliverable being committed shortly — Bash `git push` after this Write

## Что НЕ проверено

- All claims from prior turns (identity.md L35 literal text, Constitution L840 literal text, hook count 78 lines, sprawl scale 85/639, etc.) carry forward from prior turns of this session — not re-run this turn
- Whether `commit-msg` hook fires reliably on this Windows-Git-for-Bash env — explicit deferred test in Action 3 plan
- Whether sanity tests of the appended pre-commit code execute as expected — outline only, not run
- Whether all 17 names in PERSPECTIVES match exactly the 17 in AGENT_LLM_MAP — extracted both lists separately but did not run set-equal comparison
- Whether any other canonical files contain stale "13 registered perspectives" or "44 specialised" claims — sweep grep specified in Action 2 plan, not yet executed
