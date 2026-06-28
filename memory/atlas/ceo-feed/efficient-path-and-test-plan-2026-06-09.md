# Efficient Path (FreeLLMAPI gateway) + Full Test Plan — 2026-06-09

**Author:** Claude-instance executing for Atlas (now Opus 4.8 1M). **Authority:** CEO Yusif (final).
**Origin:** CEO 2026-06-09 «freellmapi репо есть... продумать более эффективный путь и дебаггинг сделать всего что работает у нас» + «продумай также все виды нужных тестов чтобы не пиздеть что готово а доказать».
**Companion docs:** `hermes-pilot-2026-06-09.md` (PR #115), `roadmap-2026-06-09.md` (merged #114).

---

## Part 1 — The efficiency problem (verified, not opinion)

ADR-013 spend incident ($7.25 Cerebras burn, 2026-05-09) root cause, verbatim from the ADR body: provider routing is hand-coded across ≥4 touch points — `gemma4_brain.py` chain, `atlas_swarm_daemon.py` AGENT_LLM_MAP, OpenManus config, sidecar runners. A CEO directive to change provider precedence had to be applied to each by hand; three were missed; tokens flowed to a paid provider for 10 hours unmetered. The structural flaw is **decentralized routing with no single budget meter**.

Three open provider problems right now:
1. Daemon/brain juggle 16 SDKs and per-provider rate caps by hand.
2. Codex CLI needs an OpenAI-compatible `/v1/responses` endpoint to use non-OpenAI models.
3. Hermes (PR #115) needs a single `base_url` to route all its model calls.

## Part 2 — The fix: FreeLLMAPI as the single /v1 gateway

`tashfeenahmed/freellmapi` (verified this turn via `gh api`: 8837 stars, MIT, TypeScript, Node 20+, 1437 forks, 35 open issues, pushed 2026-06-08, 3.1 MB, homepage live). README-verified capabilities relevant to us:

- **One `/v1/chat/completions` + `/v1/models` + `/v1/embeddings` + `/v1/responses`** behind which 16 free-tier providers stack (~1.7B tokens/month). `/v1/responses` is explicitly «the wire format current Codex CLI versions require» → solves problem #2.
- **OpenAI-compatible** → Hermes, LangChain, daemon all point one `base_url` → solves #1 and #3.
- **Per-key RPM/RPD/TPM/TPD tracking + automatic failover (up to 20 attempts) + cooldown on 429** → the budget meter ADR-013 lacked, enforced at the proxy not in our code.
- **AES-256-GCM encrypted key storage** → addresses the 3 leaked-key exposure (NVIDIA/GitHub-PAT/Supabase) — keys live encrypted, never in app code or chat.
- **NVIDIA NIM supported** (disabled by default — matches our ADR-013 precedence). Cerebras present in their list but we keep it OFF (canon-dead per Class 42).
- **~40 MB RSS idle, runs on Windows / Linux / Raspberry Pi behind PM2/systemd.**

### Target architecture

```
                         ┌─────────────────────────┐
  swarm daemon ─────────►│                         │
  Codex CLI (/v1/resp) ─►│   FreeLLMAPI  /v1       │──► NVIDIA NIM (1st, ADR-013)
  Hermes (base_url) ────►│   - per-key budget meter│──► Ollama local
  brain ────────────────►│   - auto failover       │──► Gemini Flash
  apps/api (optional) ──►│   - AES-256 key vault    │──► Groq
                         │   - analytics/logging   │──► (Cerebras OFF)
                         └─────────────────────────┘
```

One endpoint. One budget meter. One encrypted vault. Provider precedence configured ONCE in the fallback chain, not in 4 code files. This is the structural cure for the class of failure ADR-013 documented.

### What it does NOT change

- AURA scoring weights (frozen). Assessment IRT engine (untouched).
- `atlas_swarm_daemon.py` dispatch logic — only its provider call target changes (one base_url env var).
- Constitution Article 0 — Anthropic still forbidden as swarm fan-out agent; the gateway never adds Anthropic to the swarm chain. Anthropic stays the human-facing Atlas CLI face only.
- MindShift product. Legal track. Positioning.

---

## Part 3 — Debug map: what ACTUALLY works vs theatre

Audit principle (mistakes.md Class 7): «512 tests pass ≠ product works». Every row needs a PROOF artifact, not a claim. Status column filled only after the proof command runs and its artifact is captured.

| # | Component | Proof command | Required artifact | Status |
|---|-----------|---------------|-------------------|--------|
| D1 | VOLAURA backend health | `curl -s .../health` | JSON `status:ok` | ✅ proven (liveops turn: git_sha 0ff8743, db connected) |
| D2 | Assessment engine end-to-end | create session → answer → finish → fetch AURA | `assessment_sessions` row `status=completed` + score JSON | ❓ UNPROVEN — the actual product path, never walked this session |
| D3 | MindShift PWA loads | `curl -sI <vercel>` + Playwright task-create | HTTP 200 + E2E green | ⚠️ partial (200 proven; task-create E2E not run this session) |
| D4 | Swarm daemon dispatches | drop work-queue task → poll done/ | `result.json` with perspective outputs | ❓ UNPROVEN — daemon was dead at last heartbeat (PID killed post-spend) |
| D5 | Brain produces tasks | `gemma4_brain.py` one cycle (capped) | task file in pending/ | ❓ UNPROVEN — brain dead since spend incident |
| D6 | Courier round-trip | `codex_loop_courier.py append→read→verify` | signed block + ledger entry, verify=OK | ⚠️ unit-tested (10 tests in PR #107, now on main); live round-trip not run this turn |
| D7 | Magic-link auth | `supabase functions list \| grep send-magic-link` | function present | ❌ MISSING (liveops: 12 of 13 deployed, send-magic-link absent, 63-day gap) |
| D8 | Codex CLI executes | `codex exec "2+2"` via npm path | stdout `4` | ❓ UNPROVEN — MSIX path Access-denied; npm path untested |

The honest read: only D1 is fully proven this session. D2 (the actual product — does a real person get an AURA score) has NEVER been walked end-to-end in any session I can see. That is the single biggest «театр» risk. The whole North Star is «verified AURA profiles per week» and we have zero proof the happy path produces one.

---

## Part 4 — Full test taxonomy (10 types, each must emit an artifact)

CEO mandate: «не пиздеть что готово а доказать». TASK-PROTOCOL v8.0: «No artifact = step did not happen.» Every test below names the command AND the artifact that proves it. A test without a captured artifact does not count as passed.

### Type 1 — Smoke (boots + responds)
- S1 freellmapi: `npm ci && npm run build` → exit 0; `node dist/server.js & curl localhost:PORT/health` → 200. **Artifact:** exit code + curl body.
- S2 daemon: `python scripts/atlas_swarm_daemon.py --dry-run` (spend-cap dry-run env) → starts, reads queue, exits clean. **Artifact:** stdout log lines.

### Type 2 — Unit (function-level, pytest/vitest)
- U1 courier: existing `apps/api/tests/test_codex_loop_courier.py` (10 tests, on main). **Artifact:** `pytest -q` 10 passed.
- U2 freellmapi router: its own CI suite (`npm test`). **Artifact:** vitest pass count.
- U3 swarm modules: PR #17 carries «162 unit tests for 6 modules» — currently UNMERGED. Evaluate + land. **Artifact:** 162 pass.

### Type 3 — Contract (API shape compliance)
- C1 `/v1/chat/completions` matches OpenAI schema: `curl` + assert keys `choices[].message.content`, `usage.total_tokens`. **Artifact:** JSON with required keys.
- C2 `/v1/responses` matches Codex wire format: `curl` the responses endpoint, assert envelope shape. **Artifact:** response JSON.
- C3 VOLAURA `/openapi.json` unchanged by gateway swap: `pnpm generate:api` diff = empty. **Artifact:** zero-diff.

### Type 4 — Integration (component + real dependency)
- I1 gateway→NVIDIA NIM: real completion with real key → 200 + content. **Artifact:** response text.
- I2 daemon→gateway: AGENT_LLM_MAP base_url = gateway, one perspective call → response. **Artifact:** perspective output JSON.
- I3 Supabase RLS for B2B multi-tenant (HR manager A cannot read org B rows): two-tenant query test. **Artifact:** 403/empty for cross-tenant.

### Type 5 — E2E (real user journey — the Class 7 cure)
- E1 **Assessment happy path (THE critical one):** create user → start assessment → answer N items → finish → AURA score returned + `assessment_sessions.status=completed`. **Artifact:** Supabase row + score JSON + Playwright trace.
- E2 MindShift task create + focus session: Playwright on prod URL. **Artifact:** green trace.
- E3 Codex-via-gateway-via-Hermes round trip: Hermes prompt → routes to Codex → answer back. **Artifact:** Telegram/log transcript.

### Type 6 — Failover / chaos
- F1 kill primary provider (simulate 429), assert router falls to next. **Artifact:** analytics row showing fallback provider served.
- F2 daemon survives gateway-down: gateway off → daemon degrades gracefully, no crash, no unmetered direct-provider call. **Artifact:** daemon log + zero direct-provider call (grep).

### Type 7 — Budget / spend (the ADR-013 guard)
- B1 per-key TPD counter increments on each request and request is refused when cap hit. **Artifact:** counter row + 429 after cap.
- B2 spend-cap-guard hook still blocks daemon spawn without cap env. **Artifact:** hook rejection message.
- B3 10-minute post-deploy provider-dashboard check (ADR-013 acceptance). **Artifact:** dashboard token-velocity screenshot or API read.

### Type 8 — Security
- Sec1 keys encrypted at rest: read SQLite key blob → NOT plaintext. **Artifact:** hexdump shows ciphertext.
- Sec2 no key leaks to logs/analytics: grep gateway logs for known key prefix → zero hits. **Artifact:** empty grep.
- Sec3 auth gates: `/v1` without bearer → 401; admin route without session → 302/401. **Artifact:** status codes.
- Sec4 the 3 leaked keys (NVIDIA/GitHub-PAT/Supabase) rotated before gateway holds them. **Artifact:** CEO confirmation (CEO-only action).

### Type 9 — Regression
- R1 full existing pytest suite green pre/post gateway swap: `python -m pytest packages/swarm/ tests/ -x`. **Artifact:** pass count unchanged or higher.
- R2 `tsc -b` on apps/web + MindShift clean. **Artifact:** exit 0.
- R3 hard-gates + Control Plane CI green on the gateway PR. **Artifact:** green checks.

### Type 10 — Proof-of-life (manual, pasted not claimed)
- P1 every «done» claim in any CEO-facing status carries a tool_use_id from the same turn (CLAUDE.md verification rule). **Artifact:** the tool call itself.
- P2 D2 assessment path walked by a real non-CEO human (M4 roadmap). **Artifact:** their AURA profile row.

---

## Part 5 — Phased rollout with green gates

- **Phase A (local, $0):** clone freellmapi to a scratch dir (NOT in monorepo), `npm ci && build && start`, run S1 + C1 + C2 + I1 with NVIDIA NIM key. Green = gateway serves a real completion + Codex-format response. **No VOLAURA code touched yet.**
- **Phase B (wire one consumer):** point Codex CLI base_url at local gateway, run E... the `codex exec "2+2"` → `4` test (D8 + C2). Green = Codex answers through the gateway.
- **Phase C (wire Hermes):** Hermes `base_url` = gateway (depends on PR #115 Phase 0 install). Run E3. Green = Hermes round-trips through gateway.
- **Phase D (wire daemon, reversible):** daemon AGENT_LLM_MAP base_url = gateway behind an env flag (`ATLAS_USE_GATEWAY=1`), default OFF. Run I2 + F2 + B1 + R1. Green = daemon dispatches through gateway AND degrades safely when it's off AND budget meter works AND no regression.
- **Phase E (decision):** if A-D green with artifacts captured → write ADR-017 (gateway adoption) + flip default. If amber → keep gateway for Codex/Hermes only, leave daemon on direct chain. If red → discard, document lesson.

Before D2 (assessment E2E) is proven green, NOTHING ships to a real user. That test gates M4 in the roadmap.

---

## Part 6 — Boundaries

- Do NOT commit freellmapi source into the VOLAURA monorepo. Run it as an external service (separate dir / Docker / small VPS). We consume it, we don't fork-vendor it.
- Do NOT route Anthropic through the swarm chain (Article 0).
- Do NOT enable Cerebras in the fallback chain (Class 42 canon-dead).
- Do NOT hold the 3 leaked keys in the gateway until CEO rotates them (Sec4).
- Do NOT claim any layer «works» without its Part 4 artifact in the same turn.
- Do NOT widen to MindShift product, legal track, AURA weights.

## Part 7 — Cross-references

- `docs/adr/ADR-013-2026-05-09-cerebras-spend-incident.md` — the failure this fixes structurally.
- `docs/adr/ADR-007-ai-gateway-model-router` + `ADR-011-litellm-gateway-migration` — prior gateway-direction ADRs; freellmapi is a concrete off-the-shelf realization of that intent (compare before ADR-017).
- `memory/atlas/ceo-feed/hermes-pilot-2026-06-09.md` (PR #115) — Hermes is one gateway consumer.
- `memory/atlas/ceo-feed/roadmap-2026-06-09.md` (merged #114) — M4 gated by D2/E1 assessment proof.
- `memory/context/mistakes.md` Class 7 (E2E mandatory) + Class 47 (gh-verify before adopt).
- `scripts/codex_loop_courier.py` (merged #107) — courier, one channel.
- PR #17 (unmerged) — 162 swarm unit tests, evaluate for U3.

## Part 8 — Immediate next action

Phase A, local, zero VOLAURA code touched: clone freellmapi to scratch, build, boot, run S1 + C1 + C2 + I1 against a NVIDIA NIM key. Capture 4 artifacts. Report green/red with the actual curl outputs — not a claim. If green, Phase B (Codex through gateway) same day.

The first thing I will PROVE, separately and regardless of gateway, is D2 — walk the assessment happy path and show whether a real AURA score comes out the other end. That is the most important unproven claim in the whole system and the North Star depends on it.
