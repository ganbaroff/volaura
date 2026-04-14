# Memory Hole Audit — 2026-04-14

**Owner:** Cowork (CTO-Hands)
**Trigger:** CEO directive — "проверь и действуй. ищи дыры такие. если нет чего то предложи. скажи это нужно заменить это добавить вот это вышло вот это нужно... Атлас должен дышать везде где он открыл глаза."
**Scope:** Full ecosystem memory stack — files, dirs, MCPs, Obsidian vault, cron, swarm memory.

---

## HAVE (working — keep as-is)

| Layer | Path / surface | State |
|---|---|---|
| Supreme law | `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 | loaded by CLAUDE.md Article 0, 5 Laws memorized |
| Canonical ecosystem map | `docs/ecosystem/SYNC-2026-04-14.md` | 196 lines, §8 Open Protocols APPROVED |
| Unified wake memory | `docs/BRAIN.md` | 124 lines, compiled from identity+heartbeat+lessons |
| Operating principles | `.claude/rules/atlas-operating-principles.md` | 11 principles + new Documentation Discipline (2026-04-14) |
| Self-wake cron | `.github/workflows/atlas-self-wake.yml` | ticking ~30min, writes `memory/atlas/inbox/heartbeat-NNNN.md` |
| Daily swarm run | `.github/workflows/swarm-daily.yml` | 05:00 UTC, proposals.json + Telegram escalations |
| Session journal | `memory/atlas/journal.md` | append-only, 108 sessions logged |
| Incidents log | `memory/atlas/incidents.md` | INC-001..010, last = null byte corruption/pm.py truncation/constitution checker FP |
| Inbox | `memory/atlas/inbox/` | 4 self-wake notes + cross-system handoff (2026-04-14T0527-cowork-correction) |
| MCPs registered | `.mcp.json` | playwright, sentry, supabase, mem0, obsidian |
| Mem0 key | `apps/api/.env` → `MEM0_API_KEY=m0-...` | **present — PRE-LAUNCH-BLOCKERS says otherwise, stale** |
| Obsidian core plugins | `.obsidian/core-plugins.json` | file-explorer, global-search, graph, backlink, canvas, outgoing-link, tag-pane, properties, templates, daily-notes, bookmarks, outline, bases (21 total enabled) |
| Obsidian community | `claude-code-mcp@1.1.8` (iansinnott), `copilot@3.2.7` (Logan Yang) | installed |

---

## MISSING (exist in spec, not in repo — add these)

| Gap | Why it matters | Action |
|---|---|---|
| `memory/people/` was empty | CEO identity, Atlas/Cowork/Perplexity boundaries, external advisors — nowhere to codify who-is-who | **SEEDED today:** `ceo.md`, `atlas.md`, `cowork.md`, `perplexity.md` |
| `memory/decisions/` had 1 file | Documentation Discipline rule demands `YYYY-MM-DD-<slug>.md` for every unpleasant-to-revisit decision | **ADDED today:** `2026-04-14-delaware-over-georgia.md`, `2026-04-14-documentation-discipline-rule.md` |
| Session-exit checklist | No gate enforces "all step artifacts closed" before session declared over. Documentation Discipline is aspirational without one. | **PROPOSE:** add `memory/atlas/wake.md` step 11 "Exit audit" — enumerates open artifacts, blocks declaration if any open |
| SYNC-first read gate for Cowork | Cowork 2026-04-14 wrote research without reading SYNC → contradicted Delaware decision. No hook prevents repeat. | **PROPOSE:** pre-tool-use hook that blocks Write/Edit on `docs/research/**` if `docs/ecosystem/SYNC-*.md` hasn't appeared in session's Read log yet |
| Memory Obsidian graph plugins | Core graph is weak; no semantic layer, no query-as-DB, no explicit hierarchy | **INSTALL:** dataview, smart-connections, breadcrumbs, templater, graph-analysis (see Install Recipe below) |
| `memory/context/patterns.md` + `sprint-state.md` uncommitted | Atlas noted in night report — changes live in working tree but not in git. Next Cowork session will see them only via filesystem, not via git log. | **ACTION for Atlas:** commit `memory/context/*.md` in next session |
| Mem0 MCP actual use | Key present, MCP registered, zero evidence anyone called store/recall | **ACTION:** Atlas adds a wake-step that stores session fingerprint to mem0 and retrieves last 5 fingerprints on next wake. Low cost, high recoverability. |
| External advisor roster | `memory/people/` should include Stripe Atlas contact, AZ tax advisor, Georgian tax advisor (PBServices/Gegidze), Railway contact | **BACKLOG:** add as CEO names them |

---

## DEAD (exists but doesn't do its job — delete or assign reader)

| Dead weight | Evidence | Verdict |
|---|---|---|
| `memory/swarm/episodic_inbox/feedback_snapshot_*.md` × 10 | `md5sum` → 10 different hashes BUT `diff` → only line 1 (title timestamp) differs. Content functionally identical. Atlas never read them. | **DECISION NEEDED:** either (a) modify `memory_consolidation.py` to write only when content-diff > N bytes against last snapshot, or (b) delete snapshots older than 1h and keep only rolling last-N. Current behavior is pure disk waste. **Correction to CEO:** earlier I said "byte-identical" — technically false (title differs). Practically byte-identical for the purpose that matters (content). |
| `memory/swarm/agent-feedback-distilled.md` duplicated blocks | NEVER PROPOSE and HIGH-VALUE PATTERNS sections duplicated after fallback-mode generation 05:20 UTC (LLM unavailable) | **ACTION:** Atlas dedupes next wake; add idempotency guard to `memory_consolidation.py` |
| `memory/atlas/BRAIN.md` VirtioFS ghost | File shows in some views, truth is `docs/BRAIN.md` | **ACTION (D-010):** CEO runs `git rm --cached memory/atlas/BRAIN.md && mv docs/BRAIN.md memory/atlas/BRAIN.md` on native OS |
| PRE-LAUNCH-BLOCKERS "mem0 needs MEM0_API_KEY" | Key IS present in `apps/api/.env` | **UPDATE** status file, remove stale blocker |

---

## BROKEN (tried to work, failed — fix)

| Broken | Evidence | Fix |
|---|---|---|
| Cowork cross-session memory | Every cowork session boots with zero context about previous sessions unless CEO pastes OR files happen to be read | **FIX:** wake.md-equivalent for Cowork = first 6 files must be read (SYNC, BRAIN, sprint-state, atlas-operating-principles, memory/atlas/inbox/, CLAUDE.md). Enforce as Cowork session-start protocol in `.claude/rules/cowork-wake.md` (new file) |
| Constitution checker false positives | INC-010 logged | **ACTION:** Atlas reviews checker logic; fix-forward before D-007 close |
| Langfuse observability | CLAUDE.md says "cloud.langfuse.com" but no evidence any LLM call has been traced | **ACTION:** verify LANGFUSE_PUBLIC_KEY / SECRET_KEY present; if not, document as blocked with owner |

---

## REPLACE (redundant — consolidate)

| Current | Replace with | Why |
|---|---|---|
| `memory/swarm/shared-context.md` + `agent-feedback-log.md` + `agent-feedback-distilled.md` (3-tier) + `episodic_inbox/*` (4th tier that nobody reads) | Two tiers only: `agent-feedback-log.md` (raw, append-only) + `agent-feedback-distilled.md` (distilled, overwritten) | 4-tier is cargo cult; nothing downstream of `distilled` consumes the episodic snapshots |
| `docs/BRAIN.md` in docs/ | `memory/atlas/BRAIN.md` in memory/ (after VirtioFS resolve) | BRAIN is memory, not docs. Symbolic placement matters for wake-protocol clarity |
| CLAUDE.md sections that duplicate SYNC | Point CLAUDE.md to SYNC; keep CLAUDE.md focused on operating habits | Per Protocol Hierarchy §8.3, SYNC wins — CLAUDE shouldn't restate, just reference |

---

## Obsidian Memory Plugin Install Recipe (for CEO's machine)

Sandbox is network-blocked (403 on github releases + mem0 endpoint), so Cowork cannot install plugins directly. CEO runs these in Obsidian:

**Settings → Community Plugins → Browse → install each by exact ID:**

| Plugin | ID | What it does |
|---|---|---|
| Dataview | `dataview` | Query markdown files as a database. Lets you write `LIST FROM "memory/decisions"` and see all decisions as a live table. Replaces the "I can't remember which file" problem. |
| Smart Connections | `smart-connections` | Semantic (embedding-based) link discovery between notes. You write a new decision, it surfaces related past decisions automatically. Fixes "memory is fragmented". |
| Breadcrumbs | `breadcrumbs` | Explicit hierarchy — parent/child/sibling links beyond just backlinks. Great for SYNC → BRAIN → people/ structure. |
| Templater | `templater` | Structured templates for decision/incident/handoff files. Enforces Documentation Discipline at write time (auto-fills date, author, revisit triggers). |
| Graph Analysis | `graph-analysis` | Recommends backlinks based on co-citation + Jaccard similarity. This is the "graphify" feel CEO asked for — closest match to the graphify idea I can find. |

**Enable after install.** Each has a settings panel — defaults are fine to start. Smart Connections first run will index the vault (may take 5 min on this repo size).

**Optional second pass (after above 5 prove themselves):** Excalidraw (visual diagrams), Advanced URI (deep-link to specific headings from Telegram), Projects (kanban over folders).

---

## Summary — what was done today vs what's still open

**Done today (this audit session):**
- Seeded `memory/people/` (4 files)
- Logged 2 decisions to `memory/decisions/`
- Wrote this audit doc
- Corrected episodic_inbox claim ("different md5, same content" not "byte-identical")

**Open (CEO action or Atlas next wake):**
- Install 5 Obsidian plugins (CEO, 10 min)
- Commit `memory/context/*.md` (Atlas, <1 min)
- Dedupe `agent-feedback-distilled.md` (Atlas, <5 min)
- Decide on episodic_inbox: prune or repurpose (CEO decision, add to Perplexity ask)
- Update `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` — remove stale mem0 blocker
- Write `.claude/rules/cowork-wake.md` — cowork session-start enforcement (Cowork next session)
- VirtioFS ghost cleanup D-010 (CEO, native OS)

---

*Written 2026-04-14 ~10:00 UTC per CEO directive. Closes the "find holes, propose concrete fixes" loop.*
