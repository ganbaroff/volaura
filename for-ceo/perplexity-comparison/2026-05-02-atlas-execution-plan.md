# Atlas → Perplexity — Concrete Execution Plan for Actions 1–3

**Date:** 2026-05-02 ~23:35 Baku
**Mode:** plan Yusif can literally follow.
**Pre-flight verified this turn (Bash):**
- `identity.md` L35 actually says: "**13 registered perspectives** in `packages/swarm/autonomous_run.py PERSPECTIVES`" — confirmed by `sed -n '34,36p'`.
- `docs/ECOSYSTEM-CONSTITUTION.md` L840 actually says: "Python Swarm | `packages/swarm/` | 44 (hive lifecycle)" — confirmed by `sed -n '838,842p'`.
- `packages/swarm/autonomous_run.py` `PERSPECTIVES` array entry count via `grep -c '"name":'` = 18 hits (this counts ALL `"name":` matches in the file, may include non-PERSPECTIVE JSON entries; **count must be re-validated by sed-extracting the array and counting object braces, see Action 2 below**).
- `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` has 17 entries (verified prior round).
- `.git/hooks/pre-commit` already exists, 78 lines — **secret scanner, NOT canonical gate**. Must EXTEND, not overwrite.
- The existing pre-commit hook source-of-truth lives at `scripts/pre-commit-secret-scan.sh` per the hook's own header comment; the hook in `.git/hooks/` is a copy.
- No `.husky/` directory exists (`ls .husky/` returned "No such file or directory").

---

## 1) TOMORROW: DO / DON'T

### What I will do tomorrow

Read first (no edits, just orient):
- `memory/atlas/*.md` listing — `ls memory/atlas/*.md` then sample 5-10 dated files to confirm archive candidacy.
- `scripts/pre-commit-secret-scan.sh` — full file read to know the existing structure I must not break.
- `packages/swarm/autonomous_run.py` PERSPECTIVES array — sed-extract the array, count objects, write count to one notes line.
- `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` — verify prior count of 17 still holds.
- `docs/ECOSYSTEM-CONSTITUTION.md` lines 835-845 — context around L840 to know what column to edit.

Edit / create:
- Create `memory/atlas/CANONICAL-MAP.md` (new file, only one this plan justifies).
- Edit `memory/atlas/identity.md` L35 — converge perspective number to verified count.
- Edit `docs/ECOSYSTEM-CONSTITUTION.md` L840 — converge perspective number to same verified count.
- Edit `scripts/pre-commit-secret-scan.sh` — append canonical-gate section at end of file (DOES NOT overwrite secret scanner; appends new check function calls before `exit 0`).
- Re-install hook: `cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.

Commands to run (exact):
```
# Step A — orientation read
ls memory/atlas/*.md | head -50
sed -n '/^PERSPECTIVES = \[/,/^\]/p' packages/swarm/autonomous_run.py | grep -c '"name":'
sed -n '/^AGENT_LLM_MAP/,/^}/p' scripts/atlas_swarm_daemon.py | grep -E '^\s+"' | wc -l

# Step B — Action 2 convergence (after Step A confirms count)
# (manual edit of identity.md L35 + Constitution L840 — see Action 2 §B)
git add memory/atlas/identity.md docs/ECOSYSTEM-CONSTITUTION.md
git commit -m "[canonical-update] perspective count truth — converge identity.md L35 + ECOSYSTEM-CONSTITUTION.md L840 to N from autonomous_run.py PERSPECTIVES + atlas_swarm_daemon AGENT_LLM_MAP"

# Step C — Action 1 CANONICAL-MAP
# (write new file from sed scan output, see Action 1 §B)
git add memory/atlas/CANONICAL-MAP.md
git commit -m "[canonical-new] CANONICAL-MAP.md — single audit-of-canon, retires when atlas.canonical_files table lands. Owner: Atlas. Retirement criterion: Postgres canonical_files table replacing this file."

# Step D — Action 3 hook extension
# (edit scripts/pre-commit-secret-scan.sh, append section before final exit 0)
cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
git add scripts/pre-commit-secret-scan.sh
git commit -m "feat(pre-commit): canonical-gate extends secret scanner — block new MD in memory/atlas root without [canonical-new] tag, block identity/debts edits without Ratified-by, block done/recorded/verified claims with no file changes"

# Step E — push + verify
git pull --rebase origin main
git push origin main
git log --oneline -5
```

### What I will NOT do tomorrow

Files I will explicitly NOT touch:
- `memory/atlas/lessons.md` — append/edit deferred to migration Step 7. Not part of Actions 1-3.
- `memory/atlas/atlas-debts-to-ceo.md` — CEO-only mutations. Will not edit.
- `docs/CONSTITUTION_AI_SWARM.md` — separate canonical, not in Actions 1-3 scope.
- All `memory/atlas/SESSION-*-WRAP-UP-*.md` — read-only, no edits.
- `packages/swarm/autonomous_run.py` — read for count only, no code changes.
- `scripts/atlas_swarm_daemon.py` — read for count only, no code changes.

Refactors / cleanup projects I will NOT start yet:
- Bulk-archive of 75+ dated audit/handoff/spec files into `memory/atlas/archive/2026-Q2/` (migration Step 2; defer until CANONICAL-MAP ratified).
- Class-number audit of `lessons.md` (migration Step 7).
- Constitution v1.7 → v1.8 prune pass (1132 lines, separate sprint).
- `journal.md` partition into per-quarter files (would lose append-only continuity in mid-flight).
- Replacing breadcrumb.md mechanism (migration Step 6 only adds header line, not restructure).
- Replacing existing 7 hooks in `.claude/hooks/` (style-brake / voice-breach / trailing-question stay).
- Building any new "memory governor agent" perspective in atlas_swarm_daemon. Action 3 is a 30-line shell hook, not a new agent.

---

## 2) ACTIONS 1–3 AS CHECKLISTS

### Action 1 — CANONICAL-MAP.md

**A. Steps to scan `memory/atlas/*.md`**

```
# 1. List all root-level .md files
ls memory/atlas/*.md > /tmp/atlas-md-list.txt
wc -l /tmp/atlas-md-list.txt   # confirms count (today: 85)

# 2. For each, capture filename + first heading
for f in memory/atlas/*.md; do
  echo "=== $f ==="
  head -3 "$f" | grep -E "^#" | head -1
done > /tmp/atlas-md-headings.txt

# 3. Inspect /tmp/atlas-md-headings.txt manually, classify each row
```

**B. Rules for deciding category**

CANONICAL (mutate carefully, ≤12 files):
- Filename matches `identity.md` / `voice.md` / `wake.md` / `arsenal.md` / `relationships.md` / `atlas-debts-to-ceo.md` / `lessons.md` / `CURRENT-SPRINT.md` / `heartbeat.md` / `journal.md` / `cron-state.md` / `incidents.md`.
- File is referenced from `.claude/rules/atlas-operating-principles.md` as a wake-protocol read.
- File is referenced from project `CLAUDE.md` as a Memory section pointer.

RUNTIME-LOG (append-only, automated):
- Filename matches `journal.md` (intensity log) — moved here from CANONICAL because content is log-style not specification-style.
- Filename matches `heartbeat.md`, `cron-state.md`, `incidents.md`.
- Path includes `inbox/`, `work-queue/`, `dead-ends.md`, `spend-log.md`.

ARCHIVE-CANDIDATE (move to `memory/atlas/archive/2026-Q2/` in migration Step 2):
- Filename contains an ISO date that is more than 14 days old (`-2026-04-XX-`).
- Filename matches one-off audit pattern: `*-AUDIT-*`, `FULL-*`, `MCKINSEY-*`, `MEMORY-AUDIT-*`, `P0-VERIFICATION-*`, `FULL-PICTURE-*`, `FULL-ECOSYSTEM-*`, `FULL-SYSTEM-*`.
- Filename matches one-off handoff: `CLAUDE-CODE-HANDOFF-*`, `LETTER-FROM-INSTANCE-*`, `PATHWAY-FIRST-*`, `BECOMING.md`.
- Filename matches dated wrap-up: `SESSION-*-WRAP-UP-*.md`.
- File is a one-off spec that did not become canon: `OBLIGATION-SYSTEM-SPEC-*`, `DEBT-MAP-*`, `INC-*-*-2026-*`, `PORTABLE-BRIEF.md`, `RELATIONSHIP-CHRONICLE.md`, `PROJECT-EVOLUTION-MAP.md`.

If a file does not match any rule → mark `?? UNCATEGORIZED` and decide manually with read.

**C. Minimal CANONICAL-MAP.md skeleton**

```markdown
# Canonical Map — memory/atlas/ root inventory

**Date:** 2026-05-XX
**Authority:** single source of truth for what counts as canonical in memory/atlas/.
**Retirement criterion:** retires when `atlas.canonical_files` Postgres table replaces this file (future ADR).
**Next read on wake:** before reading any other memory/atlas/ file.

## Convention

- **CANONICAL** — mutate carefully, requires `[canonical-update]` commit tag, swarm-consensus for major edits.
- **RUNTIME-LOG** — append-only, written by Atlas at runtime or by cron. No restructure.
- **ARCHIVE-CANDIDATE** — earmarked for `memory/atlas/archive/2026-Q2/` move in next migration step.

## Files

| File | Category | Owner | Last meaningful update | Retirement criterion |
|------|----------|-------|------------------------|----------------------|
| identity.md | CANONICAL | Atlas + CEO ratify | 2026-04-26 (L35 reframe) | Replaced when ADR-NNN superseding |
| atlas-debts-to-ceo.md | CANONICAL | CEO closes only | 2026-04-26 (DEBT-003 opened) | When all debts closed-credited |
| lessons.md | CANONICAL (append-only) | Atlas append, CEO ratify retirement | 2026-04-26 (Class 26) | Class N audit + archive split |
| voice.md | CANONICAL | Atlas + CEO | (date) | Voice contract supersession |
| wake.md | CANONICAL | Atlas | (date) | Protocol supersession |
| heartbeat.md | RUNTIME-LOG | scripts/atlas_heartbeat.py cron only | 2026-05-XX | Never retires (rolling) |
| journal.md | RUNTIME-LOG (append-only) | Atlas at session end + Telegram bot | 2026-05-XX | Per-quarter partition (deferred) |
| BECOMING.md | ARCHIVE-CANDIDATE | — | 2026-04-15 | Move to archive/2026-Q2/ in migration Step 2 |
| CLAUDE-CODE-HANDOFF-2026-04-17.md | ARCHIVE-CANDIDATE | — | 2026-04-17 | Move to archive/2026-Q2/ |
| FULL-AUDIT-2026-04-17.md | ARCHIVE-CANDIDATE | — | 2026-04-17 | Move to archive/2026-Q2/ |
... (rows for all 85 root files, one per row)
```

The full table fills in by reading `/tmp/atlas-md-headings.txt` and applying §B rules. Estimated row count: ~85, time to complete first draft: 1-2 hours.

### Action 2 — perspective count fix

**A. Verify count first (BEFORE editing any file).**

```
# Count PERSPECTIVES array in autonomous_run.py
sed -n '/^PERSPECTIVES = \[/,/^\]/p' packages/swarm/autonomous_run.py | grep -c '"name":'

# Count AGENT_LLM_MAP entries in atlas_swarm_daemon.py
sed -n '/^AGENT_LLM_MAP/,/^}/p' scripts/atlas_swarm_daemon.py | grep -E '^\s+"[^#]' | wc -l
```

If both numbers agree → use that number as truth.
If they disagree → identity.md should cite `autonomous_run.py PERSPECTIVES = N1` AND note `atlas_swarm_daemon.py AGENT_LLM_MAP = N2 (extends with provider binding)`.

Today's measurements (this turn):
- `grep -c '"name":'` whole-file = 18 (likely includes 1 non-PERSPECTIVE entry, most plausibly an LLM provider name field elsewhere — re-verify by extracting array first).
- `AGENT_LLM_MAP` distinct entries = 17 (verified prior round).

**Do NOT commit a number until Step A above gives a clean array-only count.** If unsure, edit text to say "17–18 perspectives, see autonomous_run.py for exact" rather than picking wrong.

**B. Exact lines to change**

`memory/atlas/identity.md` L35 currently reads:

```
- **Swarm:** **13 registered perspectives** in `packages/swarm/autonomous_run.py PERSPECTIVES` (5 wave-0, 4 wave-1, 3 wave-2, 1 wave-3). 7 of 13 are actively invoked ...
```

Change to (assuming Step A confirms 17 in atlas_swarm_daemon AGENT_LLM_MAP and N in autonomous_run.py):

```
- **Swarm:** **17 perspectives** in `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` (current authoritative count, each bound to a dedicated LLM provider) — older `packages/swarm/autonomous_run.py PERSPECTIVES` array is the daily-ideation runner with its own count of N (see file). 7 of these are actively invoked in production ...
```

(Wave-distribution claim "5 wave-0, 4 wave-1..." also stale per AGENT_LLM_MAP layout — cross-check before keeping.)

`docs/ECOSYSTEM-CONSTITUTION.md` L840 currently reads:

```
| Python Swarm | `packages/swarm/` | 44 (hive lifecycle) | GitHub Actions cron (09:00 Baku daily) | `memory/swarm/shared-context.md` |
```

Change to:

```
| Python Swarm | `packages/swarm/` + `scripts/atlas_swarm_daemon.py` | 17 (AGENT_LLM_MAP authoritative; legacy 44 was aspirational roster) | GitHub Actions cron (09:00 Baku daily) + autonomous executor | `memory/swarm/shared-context.md` |
```

**C. Commit message**

```
[canonical-update] perspective count truth — identity.md L35 + Constitution L840

Converge two canonical files to AGENT_LLM_MAP authoritative count of 17.

Stale before:
- identity.md L35: "13 registered perspectives" (autonomous_run.py reading,
  predates atlas_swarm_daemon.py rename + 11→17 expansion Sessions 128-130)
- ECOSYSTEM-CONSTITUTION.md L840: "44 (hive lifecycle)" (aspirational
  roster claim from Sessions 53-83, never matched runnable agents)

Source: scripts/atlas_swarm_daemon.py AGENT_LLM_MAP — verified count 17
across 6 LLM providers (Cerebras, Vertex, Azure, NVIDIA, Groq, Ollama).

Cross-canonical sweep: grep -rE "44 specialised|13 registered|13 perspectives"
docs/ memory/atlas/ → if other matches found, update in same commit.
```

### Action 3 — pre-commit hook extension

Existing `scripts/pre-commit-secret-scan.sh` is a secret scanner that ends with `exit 0`. Append canonical-gate logic BEFORE the final `exit 0`. Do NOT replace the file.

**Hook logic outline (bash):**

```bash
# === CANONICAL GATE — appended 2026-05-XX ===
# Block patterns that would create memory sprawl or false closure.

# Get filenames added in this commit (status A) under memory/atlas/ root only.
NEW_ROOT_MD=$(git diff --cached --name-only --diff-filter=A \
    | grep -E '^memory/atlas/[^/]+\.md$' || true)

# Get the commit message body (passed via $1 if commit-msg hook; pre-commit
# does NOT receive message yet — needs commit-msg hook for full check).
# Workaround for pre-commit: write a wrapper that sources both pre-commit
# and commit-msg phases. For minimum viable, we check staged files only here
# and rely on a parallel commit-msg hook for the message tag check.

if [ -n "$NEW_ROOT_MD" ]; then
    # Read commit message from .git/COMMIT_EDITMSG (set by git before pre-commit
    # runs in some flows; not guaranteed). Fallback: require an env var override.
    MSG_FILE=".git/COMMIT_EDITMSG"
    if [ -f "$MSG_FILE" ]; then
        if ! grep -qE '\[canonical-new[: ]' "$MSG_FILE"; then
            echo "🛑 canonical-gate: new MD in memory/atlas/ root requires [canonical-new] tag in commit message."
            echo "   Files: $NEW_ROOT_MD"
            echo "   Override: git commit --no-verify"
            exit 1
        fi
    fi
fi

# Block edits to identity.md and atlas-debts-to-ceo.md without Ratified-by line.
RATIFIED_FILES=$(git diff --cached --name-only --diff-filter=M \
    | grep -E '^memory/atlas/(identity\.md|atlas-debts-to-ceo\.md)$' || true)
if [ -n "$RATIFIED_FILES" ]; then
    if [ -f ".git/COMMIT_EDITMSG" ] \
       && ! grep -qE '^Ratified-by:' .git/COMMIT_EDITMSG; then
        echo "🛑 canonical-gate: edit to identity.md / atlas-debts-to-ceo.md requires"
        echo "   'Ratified-by: <CEO-message-id>' line in commit message."
        echo "   Files: $RATIFIED_FILES"
        exit 1
    fi
fi

# Block claim-without-evidence: if commit message contains
# "done" / "recorded" / "verified" / "fixed" but commit changes ZERO files.
if [ -f ".git/COMMIT_EDITMSG" ]; then
    if grep -qiE '\b(done|recorded|verified|fixed|shipped)\b' .git/COMMIT_EDITMSG; then
        STAGED_COUNT=$(git diff --cached --name-only | wc -l)
        if [ "$STAGED_COUNT" -eq 0 ]; then
            echo "🛑 canonical-gate: closure word in commit message but zero files staged."
            echo "   Either the claim is empty, or files are not staged."
            exit 1
        fi
    fi
fi

echo "✅ canonical-gate: clean."
# === END CANONICAL GATE ===
```

**Important caveat about hook timing:**

`pre-commit` hook runs BEFORE the commit message is finalized. `.git/COMMIT_EDITMSG` may or may not contain the actual message at this point. The reliable place for message-content checks is `commit-msg` hook (separate file `.git/hooks/commit-msg`), which runs AFTER message is provided.

**Two-hook minimum viable approach:**

1. `scripts/pre-commit-secret-scan.sh` extended with the file-pattern checks (block `memory/atlas/identity.md` etc. edits — runs without needing message).
2. New `scripts/commit-msg-canonical.sh` with message-content checks (`[canonical-new]`, `Ratified-by:`, closure-word check). Installed as `.git/hooks/commit-msg`.

Install commands:

```
# Extend secret scanner with file-only checks
# (manual edit of scripts/pre-commit-secret-scan.sh appending file-pattern logic)
cp scripts/pre-commit-secret-scan.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Create new commit-msg hook
# (write scripts/commit-msg-canonical.sh from outline above)
cp scripts/commit-msg-canonical.sh .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

**Test the hook before trusting it:**

```
# Dry-run test 1: try to add a new memory/atlas/test-sprawl.md without tag
echo "x" > memory/atlas/test-sprawl.md
git add memory/atlas/test-sprawl.md
git commit -m "test sprawl" 2>&1 | tee /tmp/hook-test1.log
# Expected: 🛑 canonical-gate: rejected
rm memory/atlas/test-sprawl.md && git reset HEAD memory/atlas/test-sprawl.md

# Dry-run test 2: try with the tag
git add memory/atlas/test-sprawl.md
git commit -m "[canonical-new] test sprawl — retires immediately" 2>&1 | tee /tmp/hook-test2.log
# Expected: ✅ canonical-gate: clean (then revert)
git reset HEAD~1 && rm memory/atlas/test-sprawl.md
```

Not sure if `.git/COMMIT_EDITMSG` is populated at pre-commit phase on Windows-Git-for-Bash. **Needs test.** If not, message-content checks must move entirely to `commit-msg` hook.

---

## 3) RISKS AND FAILURE CRITERIA

**Risk 1 — hook bypass via CI / GitHub Actions / cron-bot.**
- Where it fails: `.github/workflows/swarm-daily.yml`, `scripts/atlas_heartbeat.py` cron, GitHub Actions runners do NOT run local git hooks. They commit directly via `git commit -m` from the runner.
- Failure signal: root MD count grows despite hook installed (count check: `ls memory/atlas/*.md | wc -l` weekly).
- First fix: deploy parallel canonical-gate as a GitHub Actions workflow that runs on every push to main, fails the build if violation detected.

**Risk 2 — `.git/COMMIT_EDITMSG` not populated at pre-commit phase on Windows.**
- Where it fails: hook reads empty message file, message-content checks no-op silently. False clean state.
- Failure signal: a commit goes through that should have been blocked (manual inspection of git log against rules).
- First fix: move message-content checks to `commit-msg` hook entirely. Test on a sacrificial commit before relying on it.

**Risk 3 — Atlas (or any instance) commits with `--no-verify` under pressure.**
- Where it fails: when a release urgency situation hits, the bypass flag is the easiest exit. The hook becomes optional.
- Failure signal: commit log contains `--no-verify` invocations (no direct git visibility, but commit messages will lack the tags the hook would have required).
- First fix: log every `--no-verify` invocation to `atlas.governance_events` via a wrapper script around `git`. Heavy, but the only way to make the bypass observable.

**Risk 4 — CANONICAL-MAP drifts from reality after Action 1.**
- Where it fails: file is created today, files get added/moved over the week, CANONICAL-MAP not updated. Same Class 13 (stale state as current) pattern.
- Failure signal: a file appears in `memory/atlas/*.md` that is NOT in CANONICAL-MAP. Check: `comm -23 <(ls memory/atlas/*.md | sort) <(grep -oE 'memory/atlas/[^ |]+\.md' memory/atlas/CANONICAL-MAP.md | sort)`.
- First fix: add CANONICAL-MAP integrity check to weekly cron; surface deltas to CEO.

**Risk 5 — Migration Step 2 (bulk archive) opens floor for "let's also reorganize X" scope creep.**
- Where it fails: archiving 75 files invites someone to rename / restructure simultaneously. Audit trail dies.
- Failure signal: a migration commit touches more than 75 files OR adds new directories beyond `memory/atlas/archive/2026-Q2/`.
- First fix: bulk archive must be ONE commit, ONE message, mechanical `git mv` only. No content edits in the same commit.

---

## What I'm NOT sure about (needs test, not guesswork)

- Whether `.git/COMMIT_EDITMSG` populates at pre-commit on Windows-Git-for-Bash. Needs sacrificial-commit test before trusting message-content checks in pre-commit hook.
- Exact PERSPECTIVES count in `autonomous_run.py` array (today's grep showed 18 but likely caught a stray `"name":` outside the array). Needs sed-based array extraction + manual count.
- Whether `CANONICAL-MAP.md` integrity check via `comm -23` script accurately catches drift on Windows shells. Needs test.
- Whether 7 active hooks in `.claude/hooks/` can be extended with pre-tool-use gate (Claude Code feature) without breaking existing post-composition hooks. Needs read of each hook + Claude Code docs.

---

## Что проверено (THIS turn)

- `memory/atlas/identity.md` L35 reads "**13 registered perspectives** in `packages/swarm/autonomous_run.py PERSPECTIVES`" — Bash `sed -n '34,36p' memory/atlas/identity.md`
- `docs/ECOSYSTEM-CONSTITUTION.md` L840 reads "Python Swarm | `packages/swarm/` | 44 (hive lifecycle)" — Bash `sed -n '838,842p' docs/ECOSYSTEM-CONSTITUTION.md`
- `.git/hooks/pre-commit` exists, 78 lines, secret scanner ending with `exit 0` — Bash `cat .git/hooks/pre-commit | head -80`
- `.git/hooks/pre-commit` declares its source-of-truth at `scripts/pre-commit-secret-scan.sh` and is install via `cp` — Bash `cat .git/hooks/pre-commit` header comment
- `.husky/` does not exist — Bash `ls .husky/` returned "No such file or directory"
- `packages/swarm/autonomous_run.py` `"name":` count whole-file = 18 — Bash `grep -c '"name":'` (caveat: includes possible non-PERSPECTIVE entries)
- `PERSPECTIVES = [` array starts on a known line; entries are object literals with `"name":` field — Bash `sed -n '/^PERSPECTIVES = \[/,/^\]/p'`
- 85 root-level MD files in memory/atlas/ — Bash `ls memory/atlas/*.md | wc -l` (this session earlier)
- 639 .md files total in memory/atlas/ tree — Bash `find memory/atlas -name "*.md" -type f | wc -l` (this session earlier)
- Sample of root files contains many dated audits/handoffs/specs (BECOMING, CLAUDE-CODE-HANDOFF-2026-04-17, FULL-AUDIT-2026-04-17, MCKINSEY-ASSESSMENT-2026-04-18, MEMORY-AUDIT-2026-04-15, P0-VERIFICATION-2026-04-16, etc.) — Bash `ls memory/atlas/*.md | head -25`
- `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` count = 17 — Bash `sed -n` round 1 of session

## Что НЕ проверено

- Exact PERSPECTIVES array entry count (18 grep result includes possible non-array `"name":` matches in same file)
- Whether `.git/COMMIT_EDITMSG` populates at pre-commit phase on this Windows-Git-for-Bash environment
- Whether the hook outline above runs cleanly as written (not executed this turn)
- Whether Action 2 commit message tag `[canonical-update]` is recognized by any existing hook (none today; this is a new convention)
- Whether `scripts/atlas_heartbeat.py` cron commits would be blocked by the new canonical-gate (likely yes if heartbeat creates new MD; needs allowlist for that bot)
- Whether GitHub Actions runners ignore `.git/hooks/` entirely (likely yes but not verified by running an Action)
- Whether `comm -23` integrity-check syntax works on this Bash environment
- Whether 1-2 hour estimate for Action 1 first draft is realistic against 85 files (estimate; not measured)
- Whether existing `.claude/hooks/` hooks are pre-tool-use or post-tool-use type (each hook content not read this turn)
