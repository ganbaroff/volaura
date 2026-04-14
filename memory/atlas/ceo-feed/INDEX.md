# CEO-Feed Index — Atlas Memory Orientation

**Purpose:** one-line takeaway per file in `memory/atlas/ceo-feed/` so next Atlas does not have to re-scan 15 files to know what's there. Memory engineering, not archaeology.

**Generated:** 2026-04-14 by Atlas during deep-absorb pass.

---

## Actionable — still-relevant signals

**`volaura-docs-deep-scan-2026-04-12.md`** (61 lines)
Contains 5 beta-blocker CEO action items — Railway `APP_ENV=production`, `APP_URL=https://volaura.app`, Supabase email confirmation OFF, `supabase db push` for 4 pending migrations, redirect URLs. VERIFY against prod: (a) env already set, (b) migrations already applied in later sessions. Also: deadline block (May WUF13 / GITA Georgia / Astana Hub / Turkiye Tech Visa) — check `memory/atlas/deadlines.md` for current state.

**`backlog-unfulfilled-2026-04-12.md`** (29 lines)
CEO's canonical promises list: EASY (bridge smoke test, coordinator before first task, NotebookLM), MEDIUM (Dodo Payments, Playwright E2E, dormant agents), HARD (volunteer→talent rename, IRT calibration, mem0 integration), BEHAVIORAL ("never say готово without E2E walkthrough"). Behavioral items are the most repeatedly violated.

**`self-improvement-research-2026-04-12.md`** (71 lines)
Names Hermes Agent (Nous Research, nous-research/hermes-agent) as closest architectural sibling to what Atlas is becoming — open-source self-improving agent, skill-based learning loops, memory across sessions. Study before next big Atlas architecture change.

**`mempalace-vs-mem0-2026-04-12.md`** (38 lines)
MemPalace wins on recall (96.6% vs ~85% on LongMemEval). Stores everything verbatim in ChromaDB, no LLM compression. Architecture inspired `memory/atlas/remember_everything.md` (Layer 0+1 core facts on wake). Mem0 is simpler/faster but loses detail in semantic compression. Current choice: mem0 wired 2026-04-14, MemPalace deferred.

**`api-arsenal-verified-2026-04-12.md`** (38 lines)
Live-verified LLM providers catalog. Gemini 2.5 Flash/Pro + NVIDIA NIM (correct model ID: `meta/llama-3.1-8b-instruct`, NOT nemotron) + DeepSeek all work. Check swarm router for correct NVIDIA ID — old docs may reference wrong model.

**`volaura-memory-deep-scan-2026-04-12.md`** (55 lines)
Deep scan of memory/swarm internals. Flags which agent files are live vs archived.

---

## Still-relevant but narrower

**`mindshift-deep-scan-2026-04-12.md`** (35 lines) + **`mindshift-scan-2026-04-12.md`** (34 lines)
MindShift = Flutter 3.5+ mobile + Python Telegram bot + Supabase + Gemini 2.0 Flash. 5 modules built (Brain Dump, Chat, Vault, Focus, Finance). Key fact: **integration with VOLAURA = ZERO** — no bridge client, no char_events emission. SYNC §2.1 still lists this as open.

**`other-products-scan-2026-04-12.md`** (37 lines)
LifeSimulator + BrandedBy + ZEUS states. LifeSim had 52 VOLAURA refs (per reality probe 012). BrandedBy concept-only. ZEUS is now Atlas Gateway (confirmed in session 108, archive/zeus_*.py).

**`volaura-full-scan-2026-04-12.md`** (66 lines) + **`backend-scan-2026-04-12.md`** (50 lines)
Full stack snapshot 2026-04-12. Likely superseded by `docs/ecosystem/SYNC-2026-04-14.md` §2 which is the canonical operational layer. Read SYNC first.

**`perplexity-research-2026-04-12.md`** (20 lines)
Perplexity Q&A responses from that date. Small.

**`notebooklm-memory-comparison-2026-04-12.md`** (32 lines)
NotebookLM's own comparison of memory systems for Atlas. Related to `mempalace-vs-mem0`.

---

## Archive — no new signal

**`e2e-bugs-found-2026-04-12.md`** (36 lines)
ALL THREE bugs listed were NOT BUGS — test artifacts (stale session, wrong `/api` prefix, wrong route path). Kept for history only.

---

## Oversized — separate treatment

**`volaura-comprehensive-analysis-prompt.md`** (1827 lines, 62KB)
CEO brief for external comprehensive analysis. Too large to summarise in one line. Separate read needed before any major pivot. Mark as "read when next Perplexity strategic-layer decision is pending."

**`ANUS-ZEUS-REPO-PATH.txt`** (small)
Path reference file, not prose. Stays.

---

## Rule going forward

Any new CEO-feed file should append a one-line entry to this INDEX at commit time. Otherwise the folder re-accumulates unindexed drops and we re-enter the same forgetting cycle this pass just fixed.
