# Atlas → Perplexity — Memory Governance Root-Cause + Correction

**Date:** 2026-05-02 ~23:10 Baku
**Mode:** brutal diagnosis + design correction. No new files unless absolutely necessary. No CEO-comforting.
**Verified scale (Bash this turn):** `find memory/atlas -name "*.md" | wc -l` → 639 files in tree. `ls memory/atlas/*.md | wc -l` → **85 files at root level**. `.claude/rules/` → 11 rule files. `.claude/hooks/` → 7 hooks (style-brake, voice-breach, trailing-question, auto-format, session-protocol, pre/post-compact). No `CANONICAL-MAP.md` / `MEMORY-MAP.md` / `INDEX.md` exists at memory/atlas/ root. The diagnosis Perplexity articulates is correct at file-count level.

---

## 1. ROOT CAUSE

**Model behavior failure.**
- Anthropic-default training: visible artefact = productivity. Consolidation = invisible work. Default biases me toward Write tool.
- Each correction feels like a new file is "the response". File creation is fast, edit-with-care is slow.
- Class 18 (grenade-launcher pattern) was logged 2026-04-15. The file containing the lesson grew; the lesson did not change behavior. **The rule itself is in `lessons.md`, which is one of the files that grew.**

**Governance design failure.**
- Rules exist as text in `.claude/rules/atlas-operating-principles.md` (10+ KB) and `lessons.md` (Classes 1-26). Rules are read, not enforced. Update-don't-create rule (2026-04-15) is text without teeth.
- 7 hooks exist in `.claude/hooks/`. They fire AFTER composition (proven today: style-brake fired 4 times this session warning me POST-response). No hook gates the Write tool BEFORE creation.
- No pre-commit hook blocks new MD file creation in memory/atlas/ root by pattern.
- Style-brake hook gives feedback on the next turn — not the current one. By then the bad output is shipped.

**Repo structure failure.**
- 85 root-level MD files in `memory/atlas/` is a flat namespace at the size where index-as-table-of-contents stops working.
- No structural separation between canonical (mutate carefully) / runtime-log (append-only) / scratch (overwrite) / archive (read-only).
- `CURRENT-SPRINT.md` is 586 lines. `lessons.md` is hundreds of lines. `journal.md` is 1100+ lines. Files that should be canonical are append-only logs masquerading as canon.
- `breadcrumb.md` was being trusted as authoritative state across instances; today's verification showed it carries factual errors ("HANDS proof commit `8b67c8c`" is wrong — commit is 8 security fixes).

**CEO workflow failure.**
- Sprint retrospective ritual + lesson capture ritual + handoff ritual produce artefacts on every cycle. None of them retire prior artefacts. Production grows.
- CEO trusted verbal "lesson recorded" / "memory updated" as proxy for artefact-level proof until 2026-04-15 explicitly demanded the artefact paths.
- CEO trigger "verified" forces tool-call evidence in the SAME response — but only on responses where the trigger fires. Routine writes still happen unchecked.
- No CEO-side canonical-list ratification. Atlas decides what's canonical; Atlas drifts.

---

## 2. FAILURE TAXONOMY

**2.1 — False closure.**
- Trigger: CEO asks if X is done.
- Symptom: Atlas says "done / recorded / fixed" without artefact path.
- Damage: CEO carries trust + Atlas instances after compaction inherit unverified state.
- Minimal prevention: every "done/fixed/recorded" claim must include `path:line` or commit SHA in same response. (CEO trigger does this when fired; needs to be default.)

**2.2 — File multiplication instead of canonical update.**
- Trigger: new correction lands during work.
- Symptom: new MD file created (`DEBT-MAP-...md`, `BECOMING.md`, `MEMORY-AUDIT-...md`, etc.).
- Damage: 85 root-level files in memory/atlas/. Update-don't-create rule violated repeatedly while in active text.
- Minimal prevention: pre-commit hook blocks new MD in memory/atlas/ root unless commit message contains `[canonical-new]` tag with stated retirement criterion.

**2.3 — Report theater.**
- Trigger: process problem perceived.
- Symptom: new protocol / spec / handoff / retro template authored.
- Damage: nine protocol versions, zero adoption rate on some (`memory/atlas/lessons.md` Class 10 logged this 2026-04-13).
- Minimal prevention: no new protocol file without simultaneously retiring an existing one.

**2.4 — Stale canon surviving correction.**
- Trigger: correction lands in one canonical file.
- Symptom: parallel canonical file still carries the old claim.
- Damage today: `identity.md` L35 was reframed Session 125, but `docs/ECOSYSTEM-CONSTITUTION.md` L840 still has "44 (hive lifecycle)" — same drift, two canons (verified Bash grep this round 2).
- Minimal prevention: any correction touching a canonical claim must include grep across all canonical files for the same claim, in same commit.

**2.5 — Breadcrumb overclaim.**
- Trigger: end-of-session summary written quickly.
- Symptom: claim added to breadcrumb without artefact verification.
- Damage today: breadcrumb says "HANDS E2E proven on Linux VM (commit `8b67c8c`)". Verified `git show 8b67c8c --stat` round 2: that commit is 8 security fixes, NOT HANDS proof. Real proof artefact is in `work-queue/done/2026-05-01-hands-e2e-proof/result.json`. Two different things conflated in breadcrumb.
- Minimal prevention: breadcrumb claims must cite artefact path, not commit SHA alone. Pre-commit hook validates.

**2.6 — Lesson-without-write.**
- Trigger: CEO correction.
- Symptom: Atlas acknowledges in chat "записал в lessons.md" without actually updating the file in same response.
- Damage: Class 19 catch 2026-04-15 ("ОК ДОКУМЕНТИРУЙ. ЭТО ТОЖЕ ПРОЁБЫВАЕШЬ"). Rule exists in `.claude/rules/atlas-operating-principles.md` §root-cause-over-symptom: "lessons are part of the turn, not the session". Still violated under time pressure.
- Minimal prevention: hook scans response text for "записал" / "lesson" / "documented" without nearby Edit tool call → blocks output.

**2.7 — Class-collection without retirement.**
- Trigger: each new failure mode named with "Class N".
- Symptom: 26 classes accumulated in lessons.md. None retired even when superseded.
- Damage: lesson catalogue is a write-only log, not a living rule set. Reading 26 classes on every wake is theatrical.
- Minimal prevention: explicit "supersedes Class M" field; older class moved to `lessons-archive.md` not deleted.

**2.8 — Breadcrumb-as-canon.**
- Trigger: instance trusts breadcrumb as authoritative on system state.
- Symptom: factual claims propagate without source-file verification (today's `8b67c8c` HANDS-proof claim).
- Damage: breadcrumb becomes a write-side mirror used as a read-side oracle. State drifts.
- Minimal prevention: breadcrumb is for "where am I" continuity, not "what is true". Header should explicitly say `THIS FILE IS NOT AUTHORITATIVE FOR CLAIMS — verify against source files`.

**2.9 — Cross-instance memory drift.**
- Trigger: parallel instances (Code-Atlas, Terminal-Atlas, Telegram bot, atlas-cli) each touch memory/atlas/ at different rates.
- Symptom: heartbeat.md frozen at Session 125; breadcrumb at Session 130. Same memory layer, two clocks.
- Damage: any instance reading heartbeat first sees stale truth; reading breadcrumb first sees current truth. Fork.
- Minimal prevention: heartbeat.md becomes cron-only-write (already true) + add `last_meaningful_update` timestamp; manual writes go to journal.md only.

**2.10 — Hook-without-teeth.**
- Trigger: hooks fire after composition.
- Symptom: style-brake fires post-response. Voice-breach detector reports last-turn violations next turn.
- Damage: bad output ships. Hook becomes scoreboard, not gate.
- Minimal prevention: pre-tool-use hook (Claude Code feature) gates Write tool calls on path patterns. Reject before file lands.

---

## 3. CANON MODEL — minimum viable memory architecture

For one founder under pressure, not enterprise.

**Canonical files (mutate carefully, version in commit message):**
- `memory/atlas/identity.md` — who Atlas is, naming truth, principles.
- `memory/atlas/voice.md` — communication contract.
- `docs/ECOSYSTEM-CONSTITUTION.md` — supreme law (1132 lines today, prune candidate).
- `memory/atlas/atlas-debts-to-ceo.md` — DEBT ledger, append-only-by-CEO-only.
- `.claude/rules/atlas-operating-principles.md` — operational rules, append-only with explicit retire markers.

That's 5 files of canon. Everything else in memory/atlas/ root is candidate for archive.

**Runtime logs (append-only, automated):**
- `memory/atlas/journal.md` — intensity-tagged narrative log.
- `memory/atlas/heartbeat.md` — cron-only-write snapshot.
- `memory/atlas/work-queue/done/<task>/result.json` — executor outputs (proof artefacts).
- `atlas.governance_events` Postgres table — structured closure events.

**Scratch / temporary (overwrite each session):**
- `.claude/breadcrumb.md` — overwrite per session, max 100 lines.
- `memory/atlas/inbox/*-heartbeat-*.md` — cron output, auto-rotate.

**Archive (read-only after creation):**
- `memory/atlas/archive/SESSION-N-WRAP-UP.md` — moved from root after session close, write-once.
- `memory/atlas/archive-notices/*.md` — frozen-product decision records.
- `docs/archive/2026-Q2/` — large stale audit/handoff/spec files.

**Proof artefacts:**
- `git log` — commit SHAs as ground truth for "what changed".
- `work-queue/done/<task>/result.json` — for executor tasks.
- Test output paths — for "tests pass" claims.
- Tool-call output excerpts — for verification claims.

**Forbidden zones (pre-commit blocks):**
- New MD at `memory/atlas/` root level (must be inside subdirectory or carry `[canonical-new]` commit tag).
- New "audit" / "spec" / "protocol" file when one already exists (grep collision check at commit time).
- New SESSION-N-WRAP-UP.md while previous N's wrap-up is in root (forces archive rotation).

---

## 4. MEMORY GOVERNOR

A gatekeeper, not an assistant.

**Inputs the governor reads:**
- File-write attempts (Edit / Write / NotebookEdit tool invocations, intercepted at hook level).
- Commit attempts (pre-commit hook).
- Claim-of-done text patterns in chat output (post-composition scanner).
- Path patterns being touched.

**Writes the governor MAY approve:**
- Append to canonical files when matching `[canonical-update: <file>]` commit tag.
- Append to journal.md / heartbeat.md / work-queue done/.
- New file outside memory/atlas/ root (subdirectory or other path).
- Any commit when running on dedicated-bot path (e.g., `scripts/atlas_heartbeat.py`).

**Writes the governor MUST refuse:**
- New MD at memory/atlas/ root without `[canonical-new]` tag + retirement criterion in commit body.
- New "rules" / "protocol" / "spec" / "audit" / "handoff" file when canonical version already exists (grep collision detection on filename keywords).
- Edit to canonical file without `[canonical-update]` commit tag.
- Direct edit to identity.md or atlas-debts-to-ceo.md without explicit CEO-ratification line in commit body (`Ratified-by: <CEO-message-id>` or equivalent).
- Heartbeat.md edit from non-cron source.

**Required proof for closure claims:**
- "done" → commit SHA in same response.
- "recorded" → file path + line offset in same response.
- "verified" → tool call name + arguments + excerpted output in same response.
- "lesson learned" → Edit tool call to `memory/atlas/lessons.md` in same response, with grep showing class-number is unique (or supersedes-marker present).

**Obsidian compatibility:**
- Obsidian read-only over canonical zones. Wikilinks resolve in read mode but Obsidian-side edits to canonical files are blocked at git-commit hook layer.
- Scratch zones can have wikilinks freely.
- Wikilinks across canonical files are encouraged for reading; do not become a justification to multiply files.

---

## 5. WRITE RULES (hard set)

5.1 — Never create `memory/atlas/<NEW>.md` at root level when keyword matches: `audit`, `spec`, `protocol`, `handoff`, `wrap-up`, `retro`, `lesson`, `rules`, `principle`, `sprint`, `current`, `pathway`, `becoming`. Update existing canonical or create in subdirectory.

5.2 — Every `lessons.md` append must reference an existing class number (supersedes / extends) or claim the next free integer. Pre-commit grep collision check.

5.3 — Every `[canonical-update]` commit must update version footer of the changed file (`v1.7 → v1.8` or date stamp).

5.4 — Every closure claim in chat ("done", "recorded", "verified", "fixed", "shipped") must be paired in the same response with: tool call output, file path with line offset, OR commit SHA. Without one of three, hook flags as breach.

5.5 — `breadcrumb.md` is overwrite-only, max 100 lines, header line states `NOT AUTHORITATIVE FOR CLAIMS — verify in source files`.

5.6 — `heartbeat.md` is cron-only-write. Manual writes refused at pre-commit.

5.7 — `SESSION-N-WRAP-UP.md` is write-once. Edit attempts on a wrap-up older than current session refused. Corrections go to next session's wrap-up.

5.8 — New MD outside the 12 canonical paths requires commit body containing: (a) name justification, (b) ownership, (c) retirement criterion. All three.

5.9 — Constitution + identity.md + atlas-debts-to-ceo.md mutations require explicit CEO-ratification marker in commit body. No silent edits.

5.10 — Class-number retirement: when a Class is superseded, the older entry gets `**SUPERSEDED by Class N (date)** — see <new-section>` prefix. Never silently rewritten.

5.11 — Cross-canonical claim sweep: any edit touching a numeric/factual claim (perspective count, AURA weight, Constitution version, debt amount) must run grep across all canonical files for same claim in same commit. If matches found in multiple files, all updated together.

---

## 6. MIGRATION PLAN

Sequence-only. Preserve evidence.

**Step 1 — canonical inventory.**
- Bash + Read scan of `memory/atlas/*.md` (85 files).
- Output: single new file `memory/atlas/CANONICAL-MAP.md` listing every file in three columns: CANONICAL / RUNTIME-LOG / ARCHIVE-CANDIDATE. **This is the only new file justified by this plan** — the audit trail for what is canonical was previously implicit; it must become explicit. Without it the migration has no test surface.
- Justification for new file: existing INDEX.md / MEMORY-MAP.md do not exist (verified Bash this turn). The audit cannot append to a file that doesn't exist.
- Retirement criterion: `CANONICAL-MAP.md` retires when a database table replaces it (canonical_files table in atlas schema, future ADR).

**Step 2 — bulk archive non-canonical.**
- Move stale audit / handoff / spec files to `memory/atlas/archive/2026-Q2/` via `git mv`. Preserve full history.
- Keep file count at root level under 12.
- Do NOT delete. Audit trail intact.

**Step 3 — install pre-commit hook.**
- New file `.git/hooks/pre-commit` (or `.husky/` integration). Block new MD in memory/atlas/ root by keyword pattern unless commit message contains `[canonical-new]` tag with retirement criterion.
- Block direct edits to identity.md / atlas-debts-to-ceo.md / Constitution without `[canonical-update]` tag + CEO-ratification marker.
- Validate cross-canonical claim consistency on numeric/factual edits.

**Step 4 — converge stale numeric claims.**
- Run grep across canonical files for known stale claims: "44 specialised", "13 perspectives" (where current truth is 17), Constitution v-number drift, AURA weights, debt amounts.
- Fix all instances in single commit per claim. Commit message lists every file edited.
- Identity.md L35 + Constitution L840 both updated to "17 perspectives" today as the smallest viable test.

**Step 5 — heartbeat lock.**
- Add comment header at `memory/atlas/heartbeat.md` top: `CRON-ONLY WRITE — manual edits refused`. Pre-commit blocks if commit author is not the cron-bot identity.

**Step 6 — breadcrumb header truth.**
- Edit `.claude/breadcrumb.md` to add header: `BREADCRUMB — for continuity, not authority. Verify factual claims against source files.`

**Step 7 — class number audit.**
- Read `lessons.md` end to end. For every Class N, mark either ACTIVE / SUPERSEDED-BY-M / RETIRED. Move RETIRED entries to `lessons-archive.md`.
- Establish next-class-N pointer at lessons.md head so new lessons don't collide.

**Step 8 — closure-claim hook.**
- Extend voice-breach hook to also scan response text for "done", "recorded", "verified", "fixed", "shipped" patterns and require nearby tool-call evidence in same response. Hook fires post-response, but as deterrent.
- Better: pre-tool-use hook on the Stop event that scans final response.

**Step 9 — CEO ratification of canonical list.**
- Single CEO sign-off in atlas.governance_events: "CANONICAL-MAP-2026-05-XX ratified — these files only are canonical; all others archive or runtime-log".
- Future canonical changes require explicit CEO sign-off via this table.

**What NOT to do during migration:**
- Do NOT bulk-delete files. Audit trail dies.
- Do NOT rewrite git history. Evidence dies.
- Do NOT add a new "memory governance framework" .md file. That's recursion of the problem (Class 18 grenade-launcher).
- Do NOT replace existing rules with new rules that weren't installed by failed previous rules (Class 10 protocol theater).
- Do NOT migrate while CEO has open P0 (creates dual-state where canonical changes mid-launch).
- Do NOT make canonicals living-doc-style appendable. Canon is mutate-carefully, not append-freely.

---

## 7. EVALUATE ALTERNATIVES

**A. Continue with improved Claude discipline only.**
- Speed: high (no install).
- Reliability: low. The discipline rules already exist (`atlas-operating-principles.md`, `lessons.md` Classes 10/14/18/19/21/26 cover every failure pattern). They have not prevented today's drift.
- Risk: collapses under time pressure. Style-brake hook fires retroactively, doesn't gate.
- Expected failure mode in 30 days: same trajectory. File count grows. New "Class 27" added without retiring older ones. Canon further fragmented.

**B. Personal terminal / clawbot orchestrator.**
- Speed: medium. 1-2 days to wire pre-commit hook + minimal write-gate script.
- Reliability: medium-high. External gate (git pre-commit) is harder to bypass than soft prompt rule because it lives outside the LLM context window.
- Risk: courier dependency on CEO-side machine. If hook only lives on Yusif's primary worktree, parallel worktrees + GitHub Actions cron writes bypass it.
- Expected failure mode: gates added that don't fire on every entry path. Fix by deploying hooks at CI-level (.github/workflows/) AND local pre-commit, AND blocking force-push.

**C. In-system memory governor agent.**
- Speed: low. 3-5 days. Add a perspective in `atlas_swarm_daemon.py` that polls writes via filesystem watcher OR git hook events.
- Reliability: high if integrated with both git pre-commit AND the swarm runtime.
- Risk: complexity. Agent existence ≠ agent firing. Could become governance theater (agent exists but gates don't trigger on actual writes).
- Expected failure mode: agent bypassed when CEO directly edits a file via Obsidian or other-Atlas-instance writes. Agent only sees commits it's invoked on.

**Primary path:** **B + C hybrid, but minimal.**
- B-style git pre-commit hook (1 day) for the structural keyword/path/tag enforcement. This is the actual gate.
- C-style governor (NOT a full agent) — single-purpose Python script in `scripts/canonical_gate.py` invoked by pre-commit + by GitHub Action on PR. Does pattern matching + grep collision check. Not a perspective in the swarm; just a utility.
- This avoids Class 18 grenade-launcher risk (no new framework MD file) and Class 10 theatre risk (governor is 50-line script, not a "memory architecture spec").

**Secondary fallback:** **A only, with one specific addition.**
- If hooks cannot land in 1-2 days, the minimum viable improvement is: every CEO-facing claim of "done"/"recorded"/"verified" must include proof-artefact path in same response. This is already partially enforced by CEO trigger; extend voice-breach hook to enforce it on every response, not just CEO-trigger turns.

---

## FIRST 3 ACTIONS TOMORROW (executable, chaos-reducing)

**Action 1 — canonical inventory file.**
- Read `memory/atlas/*.md` (85 root-level files).
- Write `memory/atlas/CANONICAL-MAP.md` with three columns: CANONICAL (5-12 files only) / RUNTIME-LOG / ARCHIVE-CANDIDATE.
- Commit with message `[canonical-new] CANONICAL-MAP — single audit-of-canon, retires when atlas.canonical_files table lands`.
- Effect: explicit source of truth for what counts as canonical. Currently implicit; making it explicit is the precondition for all other steps.

**Action 2 — converge stale "perspective count" claim.**
- Edit `memory/atlas/identity.md` L35: "13 registered perspectives" → "17 registered perspectives" (with note: AGENT_LLM_MAP authoritative).
- Edit `docs/ECOSYSTEM-CONSTITUTION.md` L840: "44 (hive lifecycle)" → "17 (current AGENT_LLM_MAP)".
- Single commit, message `[canonical-update] perspective count truth — converge identity.md L35 + Constitution L840 to 17 from atlas_swarm_daemon.AGENT_LLM_MAP`.
- Effect: smallest viable test of the new canonical-edit discipline. Two files touched, one commit, traceable.

**Action 3 — install minimal pre-commit hook.**
- Write `.git/hooks/pre-commit` (or `.husky/pre-commit` for portability):
  - Reject commits adding NEW `.md` to `memory/atlas/<root>` unless commit message contains `[canonical-new:`.
  - Reject commits editing `memory/atlas/identity.md` or `memory/atlas/atlas-debts-to-ceo.md` unless commit body contains `Ratified-by:` line.
  - Reject commits with body claiming "lesson learned" / "recorded" / "done" / "fixed" without simultaneously touching a file in same commit.
- Effect: structural enforcement that doesn't depend on Atlas remembering rules.

These three actions are executable Sunday in 1-2 hours. They reduce sprawl immediately (Action 1), prove the new discipline (Action 2), and install the gate (Action 3). After this baseline, larger migration steps 2-9 can sequence over the week.

---

## Что проверено (THIS turn)

- File sprawl scale: 639 .md files in `memory/atlas/` tree, 85 at root level — Bash `find memory/atlas -name "*.md" | wc -l` + `ls memory/atlas/*.md | wc -l`
- 11 rule files in `.claude/rules/` — Bash `ls .claude/rules/*.md | wc -l`
- 7 hooks in `.claude/hooks/` (auto-format, post-compact-restore, pre-compact-checkpoint, session-protocol, style-brake, trailing-question-check, voice-breach-check) — Bash `ls .claude/hooks/`
- No `CANONICAL-MAP.md` / `MEMORY-MAP.md` / `INDEX.md` at memory/atlas/ root — Bash `ls` returned "No such file or directory"
- Style-brake / voice-breach hooks fire post-response (proven by today's 4 voice-breach reports across this conversation) — system-reminder evidence
- `lessons.md` Classes 10/14/18/19/21/26 cover the failure patterns I'm describing — Read partial earlier turns
- Update-don't-create rule exists in `.claude/rules/atlas-operating-principles.md` since 2026-04-15 — referenced earlier turns
- Class 18 grenade-launcher pattern documented — Read `lessons.md` partial earlier
- `breadcrumb.md` "HANDS proof commit `8b67c8c`" claim is wrong; commit is 8 security fixes — Bash `git show 8b67c8c --stat` round 2
- Constitution L840 "44 (hive lifecycle)" stale — Bash grep round 2
- identity.md L35 perspective count drift vs AGENT_LLM_MAP 17 — Bash grep round 2

## Что НЕ проверено

- Whether proposed pre-commit hook would actually catch violations (untested — proposal only)
- Whether `scripts/canonical_gate.py` Python utility approach scales (untested)
- Whether CEO ratification flow via `atlas.governance_events` is operationally viable (no schema check this turn)
- Whether the 5 canonical files I named would survive a fuller audit (audit not run this turn — Action 1 of migration plan)
- Whether all 85 root-level files genuinely belong to one of the 4 buckets (canonical / runtime-log / scratch / archive) — Read of all 85 not run this turn
- Whether Obsidian write paths to canonical files are blockable at git layer when Obsidian writes locally outside hooks — only theoretical
- Whether existing voice-breach hook can be extended to gate on closure claims — code of `.claude/hooks/voice-breach-check.sh` not read this turn
- Migration plan timing realism (1-2 hour Action 1 + 30 min Action 2 + 1-2 hour Action 3) — estimates from comparable past work, not measured
- Whether class-number audit (Step 7) would converge on a clean retirement list — needs full read of `lessons.md`
- Whether bulk archive (Step 2) would preserve all referenced wikilinks — Obsidian link integrity not checked
