# Master Audit Repair Prompt — narrow truth-table fix

**Created:** 2026-05-03 by Atlas (Session 132) AFTER external verifier caught false claims in `for-ceo/living/2026-05-03-master-audit-consolidated.md`.

**Purpose:** Drop this prompt into a FRESH Claude Code instance (or any code-grounded LLM with file edit access). The fresh instance edits ONLY the lines listed below, with no scope expansion, no new sections, no new files, no new governance documents, no new plans. This is truth repair, not improvement.

**Why a fresh instance:** the Atlas instance that wrote the master audit cannot be trusted to grade its own corrections. Class 11 (self-confirmation) makes the same author defend prior framing even when contradicted by evidence. A fresh instance with no investment in the audit's framing edits cleanly.

---

## 1. Hard rules for the executing instance

(R1) Edit ONLY the file `for-ceo/living/2026-05-03-master-audit-consolidated.md`.

(R2) Make ONLY the corrections listed in Section 3 below. Do not add new sections. Do not add new claims. Do not "improve" framing. Do not insert opinion.

(R3) Do not create new files. No new governance files. No new ADRs. No new plans.

(R4) For each correction in Section 3, run a tool call that confirms the corrected fact BEFORE editing. Cite the tool call in the commit message.

(R5) Use Edit tool with `replace_all: false` and unique `old_string` context. Do not use Write to rewrite the whole file.

(R6) After all edits, run `git diff` on the file. The diff should show ONLY the targeted lines changing, plus any minimal context required for unique `old_string` matching. If the diff shows additions outside the corrections list, revert and retry with tighter `old_string`.

(R7) Single commit. Title: `docs(for-ceo): repair master audit truth table — 12 corrections from external verifier`. Body lists each correction with the tool-call evidence.

(R8) After commit, push to origin/main using `git -c rebase.autoStash=true pull --rebase origin main && git push origin main`.

(R9) Do not write a closing summary chat message longer than 150 words. The work is the diff, not the prose.

(R10) After this task, stop. Do not propose follow-up work. Do not run `auto_audit.py`. Do not regenerate the master audit. Do not write a new sprint plan.

---

## 2. Tool calls to run BEFORE editing (verification protocol)

Run each, save outputs mentally, use as commit-body evidence:

```
Bash: ls -d "C:/Users/user/OneDrive/Documents/GitHub/ANUS"
Bash: ls -d "C:/Users/user/Downloads/mindshift"
Bash: ls -d C:/Projects/VOLAURA/apps/mindshift  # expect: not found
Bash: ls C:/Projects/VOLAURA/packages/swarm/agents/
Bash: cd C:/Projects/VOLAURA && git log --oneline 7752056 3a30070 782da04 -3
Bash: cd C:/Projects/VOLAURA && git log --oneline -20 main
Bash: curl -s https://volauraapi-production.up.railway.app/health
```

Confirm each result lines up with Section 3 corrections. If any result contradicts Section 3, STOP and report instead of editing — Section 3 itself may need revision.

---

## 3. The 12 corrections — exact

Each correction lists the symptom (false claim in master audit), the ground truth, and the action. The executing instance finds the offending text in the master audit and replaces with the corrected text.

### Correction 1 — ANUS repo location

**False claim in audit (paraphrased from §1 Discovery scope and §15):**
"`C:/Projects/MINDSHIFT` and `C:/Projects/ANUS` — directories do not exist (MindShift lives inside VOLAURA monorepo at `apps/mindshift/` per integration; ANUS is archived in `packages/swarm/archive/zeus_*.py`)."

**Ground truth (`Bash: ls -d "C:/Users/user/OneDrive/Documents/GitHub/ANUS"` returns the directory):**
ANUS exists as a separate repo at `C:/Users/user/OneDrive/Documents/GitHub/ANUS` (Git-tracked OneDrive folder). The `packages/swarm/archive/zeus_*.py` files are derivative ZEUS scaffolding inside VOLAURA, not the ANUS repo itself. ANUS was NOT audited in this master synthesis — its repo path was missed during Glob.

**Action:** rewrite the relevant text in the audit's discovery scope section to:
"`C:/Projects/MINDSHIFT` directory does not exist on disk. **ANUS exists as a separate repo at `C:/Users/user/OneDrive/Documents/GitHub/ANUS` and was NOT audited in this synthesis** — Glob scope was limited to `C:/Projects/`, which missed the OneDrive Git folder. Re-audit of ANUS is a follow-up item, not closed by this file. MindShift Capacitor app lives at `C:/Users/user/Downloads/mindshift`, NOT inside VOLAURA monorepo. The `apps/mindshift/` path referenced earlier does not exist."

### Correction 2 — MindShift path inside monorepo

**False claim:** "MindShift lives inside VOLAURA monorepo at `apps/mindshift/`."

**Ground truth (`Bash: ls -d C:/Projects/VOLAURA/apps/mindshift` → not found):**
`apps/mindshift/` does not exist in the VOLAURA monorepo. MindShift is a standalone Capacitor app at `C:/Users/user/Downloads/mindshift`, separate from VOLAURA's git repo. The integration is via `volaura-bridge.ts` HTTP client, not via co-location.

**Action:** correct every "apps/mindshift" reference in the audit to "Standalone Capacitor app at `C:/Users/user/Downloads/mindshift`".

### Correction 3 — `packages/swarm/agents/` is NOT empty

**False claim:** "§6.10 packages/swarm/agents/ empty — NOT-DONE. No Python implementation files. Coordinator Agent not built."

**Ground truth (`Bash: ls C:/Projects/VOLAURA/packages/swarm/agents/`):**
Directory contains `coordinator.py` plus several JSON perspective configs (assessment_science, chief_strategist, code_quality_engineer, communications_strategist, cto_watchdog, etc.). Coordinator Agent IS built (see Correction 9).

**Action:** rewrite §6.10 to:
"§6.10 packages/swarm/agents/ contains Python coordinator + JSON perspective configs — **DONE**. `packages/swarm/agents/coordinator.py` is the runnable Python agent (commit `782da04 feat(S3-G1): coordinator agent — first runnable Python agent`). Plus JSON configs for assessment_science, chief_strategist, code_quality_engineer, communications_strategist, cto_watchdog, and others. Class 3 (solo execution) gating is now structurally possible."

### Correction 4 — journal.md rotation

**False claim:** "§6.5 journal.md rotation — NOT-DONE. 172KB still in active root. No rotation hook."

**Ground truth (`git log --oneline 7752056` → "feat(S2-G1): journal rotation — 172KB -> 5.8KB"):**
Rotation shipped as commit `7752056`. journal.md size dropped from 172KB to 5.8KB.

**Action:** rewrite §6.5 to:
"§6.5 journal.md rotation — **DONE**. Commit `7752056 feat(S2-G1): journal rotation — 172KB -> 5.8KB` shipped. journal.md current size 5.8KB. Older entries archived per rotation policy."

### Correction 5 — BRAIN.md compile target

**False claim:** "§6.6 BRAIN.md compile target — NOT-DONE. Mentioned in wake.md L11 as conditional, never built."

**Ground truth (`git log --oneline 3a30070` → "feat(S2-G3): BRAIN.md compile script — single-file cold-start [canonical-new]"):**
BRAIN.md compile script shipped as commit `3a30070`.

**Action:** rewrite §6.6 to:
"§6.6 BRAIN.md compile target — **DONE**. Commit `3a30070 feat(S2-G3): BRAIN.md compile script — single-file cold-start` shipped. Single-file cold-start path exists; Atlas-next reads compiled BRAIN.md instead of nine separate files."

### Correction 6 — Coordinator Agent

**False claim (in §10.3 NOT-DONE engineering scope):** "Coordinator Agent (`packages/swarm/agents/coordinator.py`). Source: identity.md, atlas-self-audit-2026-04-26, this session."

**Ground truth:** Coordinator Agent IS built (commit `782da04`, see Correction 3).

**Action:** delete the "Coordinator Agent" line from §10.3, OR move it to a new §13 "Closed earlier this week" with the commit SHA.

### Correction 7 — Profile 422 fix already merged

**False claim (in §2.14 and §10.1 CEO-BLOCKED):** "Profile 422 fix awaits CEO PR review per Session 131 breadcrumb."

**Ground truth (`git log --oneline -20`):**
Fix shipped as commit chain `9226443 fix(profiles): exclude age_confirmed from INSERT payload (500)` followed by `9a3e1c7 revert: restore age_confirmed in profile INSERT payload`. These are merged on main, not awaiting review.

**Action:** rewrite §2.14 to:
"§2.14 Profile creation 422 bug — **DONE then partially reverted**. Commits `9226443` excluded `age_confirmed` from INSERT, then `9a3e1c7` reverted that change. Profile flow currently in unknown state on main; verify with authenticated walk before closing."

### Correction 8 — Swarm-service docker fix already merged

**False claim (§2.15 and §10.1):** "Swarm-service docker fix awaits CEO PR review."

**Ground truth (`git log --oneline -20` → `f5a8a Merge branch 'fix/swarm-service-lazy-docker-import'`):**
Branch merged to main.

**Action:** rewrite §2.15 to:
"§2.15 Swarm-service docker import crash — **DONE**. Branch `fix/swarm-service-lazy-docker-import` merged via `f5a8a Merge branch 'fix/swarm-service-lazy-docker-import'`. Lazy-import + try/except fallback to BARS now in main. Hot-fix `SWARM_ENABLED=false` from earlier this session 132 redundant once code-fix deploys."

### Correction 9 — Railway auto-deploy gap closed

**False claim (multiple sections):** "Railway auto-deploy gap. Last auto-deploy 2026-05-02 18:15 UTC. Manual `railway redeploy` works."

**Ground truth (`curl /health` → `{"git_sha":"9a3e1c7cfced"}`, advanced from `7216ce43886a`):**
Railway prod git_sha is now `9a3e1c7cfced`, ahead of the audit's claimed `7216ce43886a`. Auto-deploy may have resumed naturally after the env-flip plus manual redeploy combo.

**Action:** rewrite §10.2 line "Railway auto-deploy gap" to:
"Railway auto-deploy gap — **CLOSED as of 2026-05-03**. Prod git_sha advanced from `7216ce43886a` to `9a3e1c7cfced` per `curl /health`. Cause of original gap not fully diagnosed (manual redeploy plus env-flip plus auto-deploy resume — sequence unclear). Treat as resolved, monitor for regression."

### Correction 10 — prod git_sha wording

**False claim (§2.16 and elsewhere):** "Status: DONE in main, IN-PROGRESS on prod — Railway deploy gap means it has not reached prod yet."

**Ground truth:** Railway deploy gap is closed (Correction 9). Auth-session race fix is now on prod via the new sha `9a3e1c7cfced`.

**Action:** rewrite §2.16 to:
"§2.16 Auth session race — **DONE on main and on prod**. Codex's `1554adf` merged Session 131. Prod git_sha `9a3e1c7cfced` is downstream of `1554adf` per git ancestry, so the fix is live. Authenticated walk required to close behavioural verification."

### Correction 11 — "53 audits consolidated" framing overstated

**False claim (audit title and §15):** "53 audit files into one"

**Ground truth (audit's own §15):** "Items synthesized in full from latest audits: VOLAURA core, MindShift, Cross-product, Constitution, Memory. Items captured by reference but not re-synthesized in this pass."

**Action:** rewrite §15 first paragraph to:
"This file consolidates findings from **5 audit files read in full**, **13 audit files headline-scanned**, and **35 audit files indexed by file path only** — total inventory 53. Calling this 'consolidated' is half-true: the inventory is complete, the synthesis is a sample. Each finding has source path. None of the source files are deleted; they remain as the evidence base. This file is a status snapshot derived from a representative sample, not a complete re-synthesis of every claim in every audit."

### Correction 12 — tribe streak fix already merged

**False claim (§2.X and §10.2):** "Tribe streak record fail at assessment.py:1188" listed as IN-PROGRESS engineering.

**Ground truth (`git log --oneline -20` → `02cb246 fix(tribe): wrap maybe_single in try/except for streak tracker`):**
Fix shipped as commit `02cb246`.

**Action:** move "Tribe streak record fail" from §10.2 IN-PROGRESS to §11 Closed today (today's session) with commit `02cb246`.

---

## 4. Commit message template (use after edits)

```
docs(for-ceo): repair master audit truth table — 12 corrections from external verifier

External AI auditor (per for-ceo/living/2026-05-03-audit-verifier-prompt.md)
caught 12 false or stale claims in for-ceo/living/2026-05-03-master-audit-
consolidated.md. Each correction backed by a tool call that contradicts the
original claim:

1. ANUS repo location (Bash: ls -d OneDrive/Documents/GitHub/ANUS exists)
2. MindShift path (Bash: ls -d apps/mindshift not found, Downloads/mindshift exists)
3. packages/swarm/agents not empty (ls shows coordinator.py + 8+ JSON configs)
4. journal.md rotation done (commit 7752056)
5. BRAIN.md compile target done (commit 3a30070)
6. Coordinator Agent done (commit 782da04)
7. Profile 422 fix merged (commits 9226443 + 9a3e1c7)
8. Swarm-service docker fix merged (f5a8a Merge branch)
9. Railway auto-deploy gap closed (curl /health git_sha advanced)
10. Prod git_sha now 9a3e1c7cfced not 7216ce43886a
11. "53 audits consolidated" framing overstated (5 deep + 13 scan + 35 indexed)
12. Tribe streak fix merged (commit 02cb246)

No new sections added. No new files. No new governance docs. No new plans.
This commit is truth repair only — Class 26 (verification-through-count)
correction by external verification.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## 5. After this commit lands

- Master audit becomes a working map again, not a snapshot frozen at noon.
- Atlas next instance treats this as the canonical state; any audit older than this commit is superseded.
- No follow-up work scheduled by THIS prompt. Whatever next happens is CEO's decision, not Claude's auto-pilot.
- If executing instance is tempted to "improve" anything beyond the 12 corrections, RE-READ Rule R10 and stop.
