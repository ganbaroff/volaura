# Breadcrumb — last declared Atlas action

**Updated:** 2026-06-10 ~16:00 Baku by Claude-instance (Opus 4.8) executing for Atlas.
**Supersedes:** the 2026-06-10 ~01:25 mega-sprint breadcrumb (main has advanced far past it).

## READ THIS FIRST on wake → then the handoffs
Session arc + 15-min reading list: **`memory/atlas/SESSION-HANDOFF-2026-06-09.md`**. Then this breadcrumb for everything since. Fable 5 instances: also `memory/atlas/FABLE-5-PROMPTING.md` AND note — **our domain (assessment integrity, RLS, keys, credits, LLM-routing) trips Fable 5's cyber/bio safety filter constantly → do security/infra/credits work on Opus 4.8, not Fable** (`memory/atlas/master-prompt.md`).

## One-paragraph state (origin/main advancing past `9d3bdb9`)
Big session. Merged this session: #122 (D-1/D-3/D-5 assessment defects, prod-proven), #123 codex-loop, #124 master-prompt, #125 ecosystem-pillars+mega-sprint+Fable-ban, #126 wake-chain repair, #127 CI test-gate (the never-run swarm/atlas-core/brain/openmanus suites now run), #128 clone-rescue report, #129 cleanup (vendored claude-flow agents removed), #130 morning-report, **#131 brain-chain fix (Cerebras REMOVED from `gemma4_brain.py`, NVIDIA-first, Codex-reviewed, MERGED)**, #132 BrandedBy ledger correction, #133 deferred-key-rotation debt, #134+#135 credits ledger (console-verified). **Fossils resolved:** #93 brand-identity banner LANDED (rebased); #17 + #13 CLOSED (superseded — verified). The freellmapi $0 gateway is LIVE (`http://34.60.182.57:8799`, `/ping` 200).

## OPEN THREADS (what's actually in flight)
1. **Pitch deck v3** — v2 (`C:/Users/user/Downloads/volaura-deck-v2.{html,pdf}`) is generic + had [CEO-fill] holes; CEO rejected it ("не цепляет, словно отчёт средней компании"). Build v3 from **`memory/atlas/PITCH-DECK-SOURCE-2026-06-10.md`** (real cited numbers + LOCKED ADR-016 positioning). BLOCKED on 2 CEO confirms: (a) ask-framing (no current raise exists — accelerator/pilot/grant/future-SeriesA), (b) founder bio (COP29/CIS-Games vs civil-society). Use a DESIGN TOOL (Canva MCP / pptx skill / Figma) + real visuals + **screenshot-and-Read every slide before "done"** (v2 failed by verifying text, not pixels).
2. **Credits** — `memory/atlas/CREDITS-AND-RESOURCES.md` (console-verified). CEO actions: spend $247 GCP Free before **Jul 8 2026**; click NVIDIA "Authenticate Email" to finish the INC form; Azure $5k redemption → sub `8f69cd30-…`; log into AWS to read Activate amount.
3. **Deferred key rotation** — 5 keys exposed 2026-06-10, CEO deferred (`atlas-debts-to-ceo.md`). To add a key to .env safely: clipboard → append, value NEVER through chat.
4. **Cerebras sweep** — #131 fixed `gemma4_brain.py` only; Cerebras still referenced in live-code (`packages/swarm/tools/llm_router.py`, `apps/api/app/services/model_router.py`, `packages/swarm/providers/dynamic.py`). Spend-sensitive → via Codex, not solo.
5. **Provider liveness (Atlas probe 2026-06-10):** Groq WORKS, Gemini alive(quota 429), Cerebras key-alive-but-removed-by-policy, **NVIDIA key DEAD (401)**, Azure unverified.
6. D-4 (`selected_answer` capture) awaiting Codex · Hermes blocked on 2 CEO gates (e2-small +$24/mo, valid Telegram token).

## Do NOT
fabricate a fundraise $ number (none exists — runway is a non-issue) · claim real users (pre-beta, 0 paying, legal-gated) · use "volunteer platform" / "LinkedIn competitor" framing (ADR-016 banned) · push origin/main direct · resize VM without CEO · use the dead Telegram token · touch scoring/LLM-routing code solo (Class 3 — Codex) · revive Cerebras · Anthropic in swarm (Article 0) · auto-close debts · do security/credits work on Fable 5 (use Opus).

— deck source: `memory/atlas/PITCH-DECK-SOURCE-2026-06-10.md` · credits: `memory/atlas/CREDITS-AND-RESOURCES.md` · full arc: `memory/atlas/SESSION-HANDOFF-2026-06-09.md`
