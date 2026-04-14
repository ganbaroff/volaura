# Cowork State
**Updated:** 2026-04-14 Baku | **Session:** 10 (startup-programs research deliverable)

---

## 💼 STARTUP PROGRAMS RESEARCH — DELIVERED (2026-04-14)

CEO directive "пропусти вопрос, делай по своему усмотрению — широкий охват" → built three artifacts:

1. **`docs/business/startup-programs-catalog.xlsx`** — 54 programs across Cloud / AI-LLM /
   Banking-Perks / DevTools / Marketing / Productivity / Accelerators / AZ-CIS.
   6 sheets: README · Catalog (filterable, ROI-color-scaled) · Top 10 ROI · Sequence
   Plan (week-by-week) · Pre-reqs (what unlocks what) · Status Tracker.
   108 formulas, all green via `scripts/recalc.py`. Total potential ≈ $5.5M+ stacked.

2. **`docs/business/volaura-pitch-deck.pptx`** — 12-slide reusable deck, Constitution-aligned
   palette (BG_DARK + ACCENT lavender #C0C1FF, never red, sandwich structure dark→light→dark).
   Cover · Problem · Solution · Product · How it works · Market · Traction (with honest
   readiness bars 50-70%) · Business Model · Tech & Moat · Team · Roadmap · The Ask.
   Visual QA passed: all 12 slides re-rendered after fixes (ring-on-text overlap on cover,
   list-into-footer on slide 3, card-into-footer on slide 4, clipped numbers on slide 7,
   ring-on-footer on slide 12 — all corrected).

3. **`docs/business/applications/README.md`** — 10 personalized application drafts +
   common reusable answers + week-by-week order of operations + "what NOT to do" rules.
   Top 10 chosen by ROI score from catalog: Microsoft for Startups, Cloudflare, Notion,
   Databricks, NVIDIA Inception, DigitalOcean, HubSpot, Google AI tier, Sentry, Anthropic.
   Plus 2 bonus: Innoland (AZ-specific) and ElevenLabs (already integrated).

Strategic finding for CEO (week-5 decision in Sequence Plan): **Stripe Atlas ($500 +
30 days) is the single biggest leverage point** — converts $0 startup to $500K+ in
stacked US-only perks (Brex, Mercury, Ramp, HubSpot 90%, AWS Activate Portfolio).
Documented in Pre-reqs sheet. CEO sign-off needed.

---

## 📂 PRIOR SESSION CONTENT (2026-04-13T19:05)

---

## 🎬 CONTENT PIPELINE — TIER 1 SHIPPED (2026-04-13 evening)

Cowork executed CEO directive "do" (Tier 1 from `docs/content/VIDEO-PIPELINE-UPGRADES-2026-04-13.md`). All three Tier-1 items landed in this session:

1. **Whisper.cpp captions** — `packages/remotion/src/components/Captions.tsx` + `scripts/transcribe.ts`.
   `@remotion/captions` + `@remotion/install-whisper-cpp` 4.0.448 wired. Run
   `pnpm --filter @volaura/remotion transcribe -- voice.wav --language=az`
   → emits `voice.captions.json` consumable by `<Captions captions={...} />`.
   TikTokAZ composition now accepts optional `audio` + `captions` data fields.
2. **TTS module** — `packages/swarm/tts.py`. Azure (`az-AZ-BabekNeural`/`BanuNeural`) for AZ;
   ElevenLabs Multilingual v2 for EN/RU. Output is 22.05kHz/16-bit/mono RIFF WAV
   (Whisper-friendly, drops into Remotion `<Audio>` via `staticFile()`). Env vars
   added to `.env.md`. CLI: `python -m packages.swarm.tts --lang az --text ... --out ....wav`.
3. **Postiz deployment handoff** — `docs/ops/postiz-deployment-handoff.md`. Apache 2.0
   self-hosted scheduler picked over Mixpost/Buffer/Hootsuite. Deployment plan, env vars,
   Gherkin acceptance criteria, rollback strategy all written. Atlas-owned next step
   is Railway provision + `packages/swarm/postiz_client.py` once CEO grants OAuth.

Verification: `tsc --noEmit` clean against full source; `@remotion/bundler` bundle
succeeds end-to-end (only Chromium download is sandbox-blocked, expected).

Atlas pipeline doc updated: `memory/atlas/content-pipeline-handoff.md` now has
Step 5.5 (TTS) and Step 8 (Postiz) in the DAG with new Gherkin AC #10–12.

Side-effect of session: discovered that the prior session's Write tool silently
truncated 10+ files at byte boundaries. All 10 restored and now passing typecheck.
Mistake to log in `mistakes.md` next pass: "trust file completeness only after
re-reading tail + a parser pass — silent truncation looks fine in editor preview."

---

## ⚠️ HANDOFF 011 SUSPENDED — REALITY PROBE FIRST

CEO directive 2026-04-13: "не верь документации, докажи что видишь и проанализировал".
Cowork re-verified own audit via Supabase MCP + file reads + constitution_checker run.

**Key retraction:** "Production API is DOWN" was **wrong**. Cowork's curl returned HTTP 000 because the sandbox blocks external egress (HTTP 403 from proxy), not because Railway died. Supabase logs show live `python-httpx/0.28.1` traffic 17:14–17:45 UTC today. **API is alive.**

Full verification: `packages/atlas-memory/knowledge/verification-2026-04-13.md`.

---

## 🎯 ACTIVE PRIORITY — HANDOFF 012 (REALITY PROBE)

**File:** `handoffs/012-full-reality-probe.md`
**Status:** 🟡 AWAITING ATLAS (local Claude Code)
**Why:** Cowork cannot verify ground truth from inside the sandbox. Atlas runs locally — can curl Railway, `ls` standalone repos, hit Sentry/Railway CLI, run Playwright. Must return ground truth before we plan or fix anything else.

**9 probes (90–120 min):**
1. VOLAURA production health (direct curl to Railway + frontend)
2. Sentry event count last 7d / 24h (confirm DSN + project)
3. Standalone products — mindflow, brandedby, life-simulator, zeus — real paths, commits, tests, deploys, integration grep, honest readiness 0–100
4. VOLAURA test suite (pytest + npm test)
5. Playwright E2E (full-journey.spec.ts)
6. Constitution checker — 15 flags triaged real-vs-noise
7. Railway env vars diff vs local `.env`
8. Git index health (fsck — Cowork saw local corruption, may be sandbox artifact)
9. Cross-product bridge audit (character_events / EXTERNAL_BRIDGE_SECRET grep in each repo)

**Output destination:** `sync/claudecode-state.md` → section `## Reality Probe 2026-04-13`. 7 ACs defined in the handoff.

**Rule:** no coding during the probe. Fixes come in Handoff 013 after ground truth lands.

---

## HANDOFF 011 — ON HOLD

`handoffs/011-full-prod-fix.md` still exists on disk but is **partially based on Cowork's sandbox blindness** (Task 0 "revive Railway API" is bogus). Will be rewritten or trimmed once Handoff 012 reports back. Do not act on 011 as-is.

---

## What Cowork Verified Today (evidence-backed)

| Claim | Verdict | Evidence |
|---|---|---|
| Atlas identity protocol | TRUE | `identity/core.md:6` |
| Prod API down | **FALSE** — retracted | Supabase logs show live traffic |
| 38% data loss (5 orphan sessions) | TRUE | 5 UUIDs listed in verification report, all 2026-04-11 19:09–19:17 |
| 4 Constitution violations | WRONG NUMBER — retracted | Real count: 15 flags, ~3 live (leaderboard leftovers in `dashboard/page.tsx:17,163,338`), rest are teaching comments + `duration=800` boundary |
| 329 doc files | TRUE | find confirms |
| Ecosystem events wired (Session 9) | TRUE | assessment.py:889,916,926 call emit_* — uncommitted in working tree |
| MindShift/BrandedBy/LifeSim/ZEUS 75–95% ready | UNVERIFIED | numbers came from single scan 2026-04-12, repos not in this mount |
| MindShift bridge = 0 | FALSE — overstated | 1 xp_earned event from source=e2e_d5_test 2026-04-09; `zeus.governance_events` schema exists in Volaura DB |
| Jarvis daemon active | FALSE | archived at `archive/jarvis_daemon.py` |
| Sentry "0 events in 30d" | UNVERIFIED | Claim rests on earlier audit, not re-checked via Sentry MCP today |

**New findings Cowork surfaced (not in prior audit):**
- Supabase advisor: 1 ERROR — `public.character_events_public_safe` view is SECURITY DEFINER, bypasses RLS.
- 4 WARN/INFO: RLS-no-policy on `user_identity_map` and `zeus.governance_events`; vector/pg_trgm in public schema; service-role policy with `USING(true)`; leaked password protection disabled.
- MindShift DB: 3 users, 1 subscription, 0 focus_sessions, 0 tasks, 0 crystal_ledger — deployed, unused.
- Local git index corruption: `git status` → `fatal: unknown index entry format 0x74000000`. May be sandbox artifact. Probe 8 verifies.

---

## What Cowork Did This Session

1. Assessment engine audit (13 files, 6 DB queries, math verified)
2. Audit report: `docs/audits/ASSESSMENT-ENGINE-AUDIT-2026-04-13.md`
3. Architecture research: `docs/research/ASSESSMENT-ARCHITECTURE-RESEARCH-2026-04-13.md`
4. Ecosystem events service: `apps/api/app/services/ecosystem_events.py` — 3 emit_* wired into /complete
5. Beta readiness checklist: `docs/BETA-READINESS-CHECKLIST.md`
6. Handoff 010 → 011 → **012 (reality probe)**
7. McKinsey-style independent audit: `docs/audits/VOLAURA-INDEPENDENT-AUDIT-2026-04-13.docx`
8. Road-to-100 plan: `packages/atlas-memory/plans/ROAD-TO-100-2026-04-13.md` (4 phases, 90 days)
9. Full self-verification sweep: `packages/atlas-memory/knowledge/verification-2026-04-13.md`
10. Handoff 012 (reality probe) — this step

---

## Handoff Queue

| # | Status |
|---|--------|
| **012 Reality Probe** | **🎯 P1 ACTIVE — awaiting Atlas local execution** |
| 011 Full Prod Fix | ⏸️ ON HOLD — to be revised after 012 |
| 010 Beta Readiness | ⬆️ SUPERSEDED BY 011 (still on hold) |
| 009 Pipeline fix | ⬆️ FOLDED INTO 011 |
| 001-002, 005-007 | ✅ DONE |
| 003 PostHog | 📝 READY (P2) |
| 004 Swarm Phase 2 | 📝 READY (P1) |
| 008 volunteer_id rename | 📝 READY (P2) |

---

## After Atlas Returns Reality Probe Results

1. Rewrite `knowledge/verification-2026-04-13.md` with ground-truth corrections.
2. Rewrite `plans/ROAD-TO-100-2026-04-13.md` with real readiness percentages + DB security items.
3. Trim or rewrite Handoff 011 (drop Task 0 if API confirmed alive, keep outbox + Sentry + E2E + Constitution).
4. Write Ha