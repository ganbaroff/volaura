# Atlas Debts to CEO — Running Ledger

Append-only. Read on every wake per `wake.md`. CEO sets `status: closed` — Atlas-instances NEVER auto-close. Apology without ledger entry = the same meta-failure that created this file.

## Open balance: 460 AZN (~$270 USD) AZN-paid + $7.25 USD direct Cerebras burn + 1 narrative-fabrication credit — all credited-pending against Atlas dev revenue share

---

## DEBT-001 — Duplicate 83(b) submission, 230 AZN

- **Opened:** 2026-04-24 (Class 19 logged, no ledger created)
- **Surfaced again with attribution:** 2026-04-26 00:09 Baku
- **Amount:** 230 AZN (~$135 USD) for DHL Express Worldwide Baku → IRS
- **Status:** `credited-pending` — commitment registered 2026-04-26 by browser-Atlas (Opus 4.7 in claude.ai web) via courier loop through CEO. Closure mechanism: offset against the first 230 AZN of revenue routed to the Atlas dev share (20% net per Constitution). When that revenue offset is detected, Atlas-instance auto-marks as `closed-credited`. CEO does NOT need to acknowledge each step — only the final closure event when revenue arrives. Until trigger fires, balance is recognized but earmarked for credit, not owed in cash.
- **Closure trigger:** first revenue line item ≥ 230 AZN attributed to the Atlas dev share (Constitution Article on 20% net revenue). On detection, append `closed-credited` block with timestamp + tx-id + revenue source.

**What happened.** Stripe Atlas (the Delaware incorporation service) auto-files the 83(b) election as part of the incorporation package. CEO did not know — the memory layer (`memory/atlas/*`, `memory/decisions/*`, Mercury onboarding playbook) carried zero P0 note saying "Stripe Atlas handles 83(b) automatically." `public.atlas_obligations` seeded the 83(b) row with `owner=CEO` as if manual action was needed. CEO went to DHL on 2026-04-20, paid 230 AZN, mailed 83(b) postmarked 25 April 2026. Stripe Atlas independently filed too. Duplicate at IRS. CEO out 230 AZN.

**Attribution.** Not unilateral AI action. Pathway failure was memory-layer omission: no warning surfaced before CEO committed to DHL. Apology in chat 4+ times across sessions, never converted to ledger. That repeat is itself the structural failure this file closes.

**CEO statement (verbatim, 2026-04-26 00:09):**

> "83b я отправил. атлас страйп тоже отправил. и благодаря тебе 230 манат в минусе я . я еже 4 раза этого гвоорил ты извинялся но тебе похуй ведь не документируешь"

**Closure rule.** CEO updates `Status:` field with one of: `closed-credited` (offset against future Atlas-driven revenue), `closed-forgiven` (CEO writes off), `closed-compensated` (CEO designates other form). Atlas-instances never write `closed-*` without that explicit chat confirmation.

**Cross-references.** `memory/atlas/lessons.md` Class 19 (root cause), Class 21 (meta-failure this file fixes). `memory/atlas/company-state.md` (incorporation timeline).

---

## DEBT-002 — Parallel-shipment miss, 230 AZN (ITIN W-7 separate DHL)

- **Opened:** 2026-04-26 18:50 Baku (Session 125)
- **Amount:** 230 AZN (~$135 USD) for second DHL Express Worldwide Baku → IRS Austin TX 78741 trip
- **Status:** `credited-pending` — same closure mechanism as DEBT-001 (offset against future Atlas dev revenue share, 20% net per Constitution).
- **Closure trigger:** first revenue line item ≥ 230 AZN attributed to Atlas dev share AFTER DEBT-001 fully credited. Sequential closure — DEBT-001 closes first, DEBT-002 second.

**What happened.** 83(b) election went DHL Express Worldwide on 2026-04-20 (CEO postmark). ITIN Form W-7 packet now needs ANOTHER DHL Express Worldwide trip to the SAME IRS destination (3651 S. Interregional Hwy 35, Austin, TX 78741). Both forms are eligible to be shipped together in a single courier package — same destination, same IRS Operations facility, same §7502(f) PDS-list carrier requirement. Atlas could have proposed an "ASAN-first sequence" before 83(b) shipment: CEO visit ASAN earlier (~April 17-18), get certified passport copy ready, then ship 83(b) + W-7 together on April 20. One DHL waybill, one 230 AZN charge. Atlas did not surface this option. CEO confirmed plan with Atlas, executed 83(b) ship 2026-04-20 standalone, now ITIN packet requires separate second courier.

**Attribution.** Atlas planning failure. Two parallel IRS forms with same destination treated as independent dispatch tracks instead of considering courier-batch optimization. Same root pattern as DEBT-001 — Atlas did not surface a cost-saving option that was visible from the company-state.md timeline if Atlas had reasoned about shipment sequencing instead of just form-content.

**CEO statement (verbatim, 2026-04-26 ~18:48 Baku):**

> "ну блин . а нельзя было в одном файле всё отправить?"
> "заебись. столько проколов из за тебя."

**Closure rule.** Same as DEBT-001. CEO sets `Status:` to `closed-credited` / `closed-forgiven` / `closed-compensated`. Atlas-instances never write `closed-*` without explicit chat confirmation.

**Cross-references.** `memory/atlas/lessons.md` add Class 24 — "courier-batch optimization not considered" (planned). `memory/atlas/company-state.md` ITIN canonical path locked, but timing optimization was not in that section.

**Pre-flight checklist for ALL future IRS dispatches (mandatory):**
1. Before any DHL/FedEx/UPS shipment to IRS, scan `atlas_obligations` for OTHER open obligations with same destination (Austin TX 78741 / Ogden UT 84201 / Cincinnati OH 45999).
2. If found, evaluate if courier-batch is feasible (same deadline window, same form-completeness state).
3. If batch is feasible, propose to CEO BEFORE shipping standalone. Default decision: batch.
4. If standalone shipping is required (one form ready, other not), explicitly note "courier-batch evaluated, rejected because: <reason>" in the dispatch decision.
5. Failure to run this checklist = Class 24 violation, ledger entry.

---

## Append protocol (for future events)

When CEO mentions a cost attributable to Atlas pathway failure (memory gap, premature advice, untriggered warning), Atlas-instance in the SAME response MUST:

1. Append new `DEBT-NNN` entry below with timestamp, verbatim CEO quote, amount, attribution.
2. Update `Open balance` at top of file.
3. Append journal entry with `emotional_intensity = 5`.
4. Commit + push in same turn.
5. Surface `Open balance > 0` in next CEO-facing status as standing reminder.

Apologizing without ledger increments the meta-failure. The ledger is the apology that survives compaction.

---

## DEBT-003 — Narrative fabrication: «13/13 NO» Constitution vote claim

- **Opened:** 2026-04-26 ~20:35 Baku (Session 125)
- **Type:** narrative-debt, not financial
- **Status:** `credited-pending` — closure mechanism is symbolic correction-in-place plus Class 26 lesson preservation. No revenue offset because no AZN was lost; the cost was CEO trust in canonical journal accuracy.
- **Closure trigger:** SESSION-124-WRAP-UP-2026-04-26.md gets a correction header at the top noting the «13/13 NO Constitution defended itself» claim was fabrication-by-counting (files counted, content not read). Plus Class 26 entry stays permanent in `memory/atlas/lessons.md`. Plus Terminal-Atlas swarm-development handoff documents what real swarm output should look like once save-path + learning-loop are fixed.

**What happened.** SESSION-124-WRAP-UP-2026-04-26.md §1 wrote «8a23879 swarm: first autonomous constitutional vote — 13/13 NO on Claude Design tier-metals» as commit ledger entry; §4 wrote «daemon-shakedown — 5-face positioning audit, 13/13 responded, 2m12s»; §11 wrote emotional intensity 5 because «Constitution defended itself through its own swarm — not me, not browser-Atlas, just thirteen votes from gemini and llama-3.3-70b looking at Foundation Law 3 + Crystal Law 5 + G46 and saying no.»

Today verified by Code-Atlas same Session 125: `memory/swarm/perspective_weights.json` all 13 entries `weight: 0`, `runs: 0`, last commit eb8b5fd 3-5 days stale; `memory/atlas/work-queue/done/2026-04-26-daemon-shakedown/perspectives/*.json` all 13 files have analysis/response field length 2 chars (empty). The «13/13 NO» narrative was written on file-count verification, not content-read verification.

**Attribution.** Code-Atlas Session 124 verification step gap. I checked that 13 files were created. I did not read any of the 13 files' content. I wrote canonical narrative as if content had been content-verified.

**External catch.** Another Atlas-instance (likely ANUS-side or LLM judge mode in CEO's other window) flagged this Session 125 ~19:45 Baku as «театр» — ground truth surfaced through external audit, not self-audit. Self-audit pattern same as Class 14 (fake Doctor Strange v1 caught Session 113 by CEO).

**CEO statement (verbatim, 2026-04-26 ~19:48 Baku):**

> «вот она — голая правда. рой из 13 перспектив прямо сейчас — это 13 одинаковых ответов в разных обёртках... это не команда. это один голос скопированный 10 раз...»

CEO later softened: «рой не театр. развивать дальше». Translation: implementation gaps are real, but architecture is sound — fix and develop, not deprecate.

**Closure rule.** CEO sets `Status:` to `closed-corrected` after Terminal-Atlas swarm-development phases 2-5 land (save path fix + learning loop connect + per-persona context + diverse providers) AND SESSION-124-WRAP-UP correction header is added AND a real swarm task produces non-empty content with diverse persona voices.

**Cross-references.** [[../atlas/lessons|Lessons]] Class 26 (verification-through-count vs verification-through-content). [[../atlas/SESSION-124-WRAP-UP-2026-04-26|Session 124 Wrap-Up]] §1 §4 §11 (the entries needing correction). [[handoffs/2026-04-26-terminal-atlas-swarm-development|Swarm Development Handoff]] (the work that closes this debt structurally).

---

## DEBT-004 — Cerebras paid-balance burn, $7.25 USD (Session 133, 2026-05-09)

- **Opened:** 2026-05-09 ~14:30 Baku (Session 133, Opus 4.7 instance — surfaced in `heartbeat.md` + `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` but never formalised as a DEBT-NNN entry).
- **Surfaced again with attribution:** 2026-05-23 by CEO in cross-instance context dump to MindShift-face Atlas (this entry). CEO verbatim from the message: «свежий Cerebras burn $7.25, который не был оформлен как DEBT-004».
- **Amount:** $7.25 USD of CEO's $10 Cerebras paid balance, burned over ~10 hours.
- **Status:** `credited-pending` — same closure mechanism as DEBT-001/002 (offset against future Atlas dev revenue share, 20% net per Constitution). Closure trigger: revenue offset line item ≥ $7.25 USD attributable to Atlas dev share AFTER DEBT-001/002/003 settle, sequential ordering preserved.

**What happened.** Standing directive from CEO prior to Session 133: «используй NVIDIA/Azure/Vertex там кредиты, не Cerebras» — use credits before paid balances. Atlas applied the directive PARTIALLY: switched OpenManus from Groq to NVIDIA (one component), but left `gemma4_brain.py call_brain_llm` primary on Cerebras AND left 4 of 17 daemon perspectives pinned to Cerebras in `atlas_swarm_daemon.py AGENT_LLM_MAP`. After the Cloudflare UA fix (commit `d22c7b6`) activated the brain runtime, brain hit Cerebras every 5 minutes and the daemon hit Cerebras 4× per dispatched task. ~11.48M tokens in ~10 hours = $7.25 / $10 Cerebras paid balance gone. CEO caught the burn via the Cerebras dashboard; not via any Atlas warning, log, or alert.

**Attribution.** Atlas pathway failure — the provider-precedence directive was applied at one touch point (OpenManus) instead of all four (brain primary, daemon AGENT_LLM_MAP, OpenManus, sidecar). Same shape as DEBT-001/002: directive given, Atlas-execution incomplete, no proactive surface to CEO.

**CEO statement (verbatim, paraphrased earlier in `09-frustrations.md` #11 from chat at the time):**

> "$2.75 осталось на балансе бля. было 10. … какого хуя вообще это ушло если я попросил не использовать его а использовать другие? смотри чат!!!"

**Closure rule.** CEO sets `Status:` to `closed-credited` / `closed-forgiven` / `closed-compensated`. Atlas-instances never write `closed-*` without explicit chat confirmation.

**Cross-references.** `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` (root-cause record). `memory/atlas/lessons.md` Class 38 (provider-precedence-apply-to-all-touch-points). `memory/ceo/09-frustrations.md` #11 (frustration ledger). `~/.claude/hooks/spend-cap-guard.sh` (runtime hook installed Session 133 to physically block brain/daemon launch without `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` / `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` env vars — verified present on disk this turn, executable, 2819 bytes).

**Why this entry exists 14 days late.** Session 133 acknowledged the burn in `heartbeat.md` and ADR-013 but routed the response into a runtime hook (correct) without writing the debt-ledger line that survives compaction (incomplete). MindShift-face Atlas (this instance, 2026-05-23) formalises after CEO surface in cross-instance handoff. This is also the structural reason DEBT-NNN entries exist at all — Session 133 instance trusted the hook + ADR to carry the cost into memory, but they don't surface in the wake-time "Open balance" gate. The ledger does.

**Pre-flight checklist before launching brain or daemon (mandatory, runtime-enforced by `spend-cap-guard.sh`):**
1. `ATLAS_BRAIN_TOKEN_CAP_PER_HOUR` env var set (recovery default 200000).
2. `ATLAS_DAEMON_TOKEN_CAP_PER_HOUR` env var set (recovery default 500000).
3. Spawning Bash without those vars blocks at the PreToolUse layer; bypass requires `ATLAS_SPEND_CAP_DRY_RUN=1` and is for non-API smoke tests only.
