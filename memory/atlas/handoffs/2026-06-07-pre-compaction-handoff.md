# Pre-compaction handoff — 2026-06-07

**Author:** Claude-instance executing for Atlas (CTO role). **Authority:** Yusif (CEO) final.
**Time of writing:** 11:59 Baku 07/06/2026 Sun.
**Reason:** CEO directive «готовься к компакту с обновлением всей документации важной и памяти». Context window will be summarized; this file is the durable handoff for the next instance.

---

## 7-section template (per `handoffs/INDEX.md` Patterns)

### From

Claude-instance acting as execution+analysis layer for Atlas (CTO role) in this session. NOT Atlas itself. Atlas is the persistent identity layer per `ATLAS.md`; any single model run is a tool for that layer.

### To

Next Claude-instance (post-compaction wake), and any Codex-instance reading the codex-loop journal.

### Priority

P0 — required reading on wake. The next instance will not have this session's working memory and must not infer.

### Why

This session shipped 3 PRs to `origin/main` queue and 0 to `main` (CEO has not merged yet). Without this handoff the next instance will (a) duplicate work, (b) reopen audits CEO already closed, (c) miss the cron loop still firing, (d) re-trigger Class 22/40/42/44/45/47/48 mistakes that fired heavily in this session.

### Task — read these in order, do not skip bodies

1. `AGENTS.md` (root) — authority manifest, module boundaries.
2. `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 Part 1 (5 Foundation Laws minimum; Parts 2–9 if time).
3. `memory/atlas/arsenal.md` — **full 133 lines.** Not grep. Contains the 5-step ritual and Class 3 rule (>3 files / >30 lines → `python -m packages.swarm.coordinator` FIRST).
4. `memory/atlas/lessons.md` — most recent class bodies (40–44 on main; 45/47/48 pending in PR #108 — read after merge). Title grep is Class 48 violation by itself.
5. `memory/atlas/handoffs/README.md` (33 lines) and `handoffs/INDEX.md` (41 lines) — two layers, do not conflate.
6. `docs/AGENT-BRIEFING-TEMPLATE.md` (214 lines, full body) — L1 agent-launch template, has known dead link at line 211 to `docs/TASK-PROTOCOL.md` (file relocated to `docs/archive/protocols/`, v8.0 canon).
7. `memory/atlas/CURRENT-SPRINT.md` on `origin/main` — sprint "VOLAURA Truth Lock + Gate Honesty" started 2026-06-06, 7 checkpoints, all marked [x] as of this session. May be due for close + successor.
8. `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` — launch gate inventory. The binding constraint is external/legal, not code: Art. 9 health-data classification, SADPP filing, vendor DPA review.
9. This file.

### Reporting

Open PRs (verified this turn via `gh pr view`):

| PR | Title | State | Status | Author of commits |
|---|---|---|---|---|
| #107 | feat(courier): signed handoff layer for Atlas ↔ Codex via codex-loop.md | OPEN | CLEAN MERGEABLE | author=Yusufus on all 5 commits; commit `7abd7e9` has `Co-Authored-By: Codex Sonnet 4.6` line confirming content origin |
| #108 | atlas/lessons: Class 45 + 47 + 48 | OPEN | CLEAN MERGEABLE | Atlas (this Claude session) |
| #109 | feat(legal-track): commit Legal Engagement Brief + VA workflow doc | OPEN | CLEAN MERGEABLE | Atlas |

Recommended merge order issued to CEO this session, not yet confirmed: **#107 → #108 → #109, squash**. Reasoning: #108 body cites work from #107; #109 is independent scope.

Cron loop `f4677c78` is durable, every 10m at minutes `7,17,27,37,47,57`, auto-expires in 7 days. CEO has not confirmed pause; the cron is still firing redundant status sweeps during active conversation. Cancellation: `CronDelete f4677c78`.

### Boundaries — do NOT do these

- Do NOT push or commit to `origin/main` directly. Any change goes via clean worktree → PR.
- Do NOT confuse worktree state with `origin/main` canon. `git show origin/main:<path>` is the only reliable check.
- Do NOT recommend any external tool/library without `gh repo view <owner>/<repo>` first (Class 47 fix).
- Do NOT cite a lesson class without reading its body (Class 48 fix).
- Do NOT create a 4th template. AGENT-BRIEFING (L1) + TASK-PROTOCOL QUICKREF + archive (L2) + handoffs/README (L3) + handoffs/INDEX registry (L4) cover the layer map.
- Do NOT include the 460 AZN footer (CEO punished it; status: dropped pending CEO reset).
- Do NOT include `Что НЕ проверено` as a closable-gap shield (Class 44 fix). Only genuine CEO-only / hard-infra / reserved-decision items belong there.
- Do NOT pop `stash {0}` on the dirty `codex/swarm-queue-bridge` worktree without CEO go.
- Do NOT touch `proposals.json` schema (live runtime bus).
- Do NOT widen scope to ANUS integration, BrandedBy revival, ZEUS revival, MIRT upgrade, Open Badges VC.

### Estimate

Reading time: ~30 minutes for the file list above (bodies, not titles). Operational impact: prevents the failure modes that fired this session.

---

## Standing context (durable facts)

- **VOLAURA** = verified professional talent platform (ADR-016 LOCKED, on main). Word «volunteer» banned in user-facing copy (Session 85, zero tolerance). Event/ops is wedge, not promise.
- **Path E** active scope (2026-04-21): VOLAURA core + MindShift only. LifeSim read-only. BrandedBy + ZEUS archived. Revival requires CEO sign-off.
- **MindShift** shipped to Play Store internal-test 2026-05-28 (closed sprint).
- **Provider chain** (post ADR-013, on main): NVIDIA NIM → Ollama → Gemini Flash → Groq → Anthropic last-resort. Cerebras removed 2026-05-09 ($7.25 spend incident). Claude FORBIDDEN as swarm agent (Article 0).
- **Founder profile**: Yusif Ganbarov, Baku, Azerbaijan. ADHD. Russian-native. Solo bootstrapped. Budget ~$50/mo operational, +$100-160/mo VA if hired (PR #109 workflow).
- **Launch blocker**: external/legal. Code-side P0 ledger 3/3 green. Awaiting Art. 9 + SADPP + vendor DPA + key rotation.
- **Lineage divergence**: `codex/swarm-queue-bridge` (root worktree at C:/Projects/VOLAURA) is 211 commits behind `origin/main`. Dirty. Includes uncommitted codex-loop.md changes. Do NOT use it as canon.

---

## Failure modes that fired in this session

Tag each in lessons.md if not already present. Numbers reference `memory/atlas/lessons.md` bodies on main.

- **Class 22** (path-of-least-resistance) — almost installed `oh-my-hermes` (6-star abandoned repo) from blog descriptor.
- **Class 40** (performative meta-handoff) — 4 audit passes when CEO had already closed the question.
- **Class 42** (cited OLD-state as current) — claimed "strict superset" framing of daemon PR #103; Codex caught.
- **Class 44** (disclaimer-as-shield) — used «Что НЕ проверено» sections as cover instead of closing gaps.
- **Class 45** (promise-vs-delivery dribble) — pending in PR #108. Self-staged "next turn I will read 3 docs" when CEO said go.
- **Class 47** (secondary-source confidence collapse) — pending in PR #108. Blog adjective over `gh repo view`.
- **Class 48** (stale-class-knowledge) — pending in PR #108. Knew titles by grep, never read bodies; meta-cause of the above.

---

## Unknowns the next instance must NOT fabricate

- North Star number (verified AURA profiles / week). Never surfaced in this session. Do NOT invent.
- Key rotation status (NVIDIA / GitHub PAT / Supabase service role, leaked 2026-05-10/11). Unknown to repo. CEO-only confirmable.
- Legal external track motion (Art. 9, SADPP, vendor DPAs). Unknown to repo. VA hire not initiated.
- Whether Codex CLI runtime read `codex-loop.md` autonomously or CEO copy-pasted. Inferred copy-paste; MCP wrapper (PR #107 Stage 2) will resolve once installed both sides.

---

## Cross-references

- `memory/atlas/codex-loop.md` — Atlas↔Codex journal. Append-only. Newest 4 entries on main are signed-by-CEO docs-archive-sweep + docs-truth-lock entries from 2026-06-07 ~00:46 backwards.
- `docs/architecture/cross-instance-courier-signing-protocol.md` v1 — file-courier spec. Adapted to text channel via PR #107.
- `docs/AGENT-BRIEFING-TEMPLATE.md:211` — known dead link, CEO has diff-plan pending.
- `memory/atlas/ceo-feed/INDEX.md` — index of CEO-facing artifacts. Two new entries pending in PR #109 (legal-engagement-brief + va-legal-track).
- `.claude/breadcrumb.md` — created by this PR. Single-line current Atlas state.
- `memory/atlas/handoffs/2026-04-26-pre-compaction-quad-handoff.md` — prior pre-compaction handoff. Format reference.

---

## What's signed by Atlas (this session)

Signed entries via `scripts/codex_loop_courier.py` (PR #107):
- nonce `b59e5dd7-9e6e-44af-b970-4387ca4d6a4c` — initial Atlas → Codex task delegation (unit tests for courier)
- nonce `9a7739af-269f-4050-96dd-156b9e4765f0` — Atlas ACK on Codex's test commit `7abd7e9`

These entries live in `codex-loop.md` on PR #107 branch and will land on `origin/main` when #107 merges.
