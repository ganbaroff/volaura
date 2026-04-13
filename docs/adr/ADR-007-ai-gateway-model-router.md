# ADR-007: AI Gateway — Role-Based Model Router

**Date:** 2026-04-11 (built), 2026-04-12 (documented)
**Status:** ACCEPTED
**Sprint:** Session 93
**Deciders:** CTO-Hands (Atlas, Claude Opus 4.6), CEO (Yusif Ganbarov)
**Related:** [[ADR-008-zeus-governance-layer]] | [[ADR-009-crewai-adoption]] | [[../CONSTITUTION_AI_SWARM]] | [[../ECOSYSTEM-CONSTITUTION]] | [[../research/NEUROCOGNITIVE-ARCHITECTURE-2026]]

---

## Context

The swarm and ad-hoc LLM calls across the codebase each picked providers their own way. `app/services/llm.py`, `packages/swarm/engine.py`, `app/services/reeval_worker.py`, and various inline calls scattered across routers all made independent provider choices. This meant:

1. No single place to audit when a call went to the wrong model.
2. No enforcement of Article 0 hierarchy (Cerebras → Ollama → NVIDIA → Haiku last resort).
3. Risk of Claude models being used as swarm agents — explicitly forbidden by Article 0.
4. No instrumentation point for tracking degraded fallback events.
5. Perplexity (CTO-Brain) proposed adding "Gemini 2.5 Pro as judge" and "DeepSeek V3 as worker" without a file to add them to.

The AI council brief (Grok's block on provider strategy) recommended: a sane strategy for which providers to use for what, clear fallback patterns, and a single abstraction over multiple providers.

---

## Decision

**Chosen:** A single `apps/api/app/services/model_router.py` module with four roles and ordered fallback chains per role. Haiku is physically unreachable from the JUDGE, WORKER, and FAST chains — it is only in the SAFE_USER_FACING chain as the last fallback, enforcing Article 0 at the code level rather than in comments.

### Roles

| Role | Purpose | Chain (in order) |
|---|---|---|
| `JUDGE` | Heavy evaluation, strategic reasoning, large-context tasks | Cerebras Qwen3-235B → Ollama local → NVIDIA Nemotron Ultra 253B → NVIDIA Llama 3.3 70B |
| `WORKER` | Bulk operations, code generation, straightforward agent work | Cerebras → Ollama → NVIDIA Llama 3.3 70B → Groq Llama 70B |
| `FAST` | Low-latency user-path operations, quick classification | Groq Llama 8B instant → Ollama → NVIDIA Llama 3.3 70B |
| `SAFE_USER_FACING` | User-visible AI responses where safety/polish matter | Gemini 2.5 Pro → NVIDIA Llama 3.3 70B → **Anthropic Haiku** (last resort only) |

### Code-level enforcement

`_CHAINS` dict maps each role to an ordered list of factory functions. `select_provider(role)` iterates the chain, annotates `is_fallback=True` if index > 0, and calls `emit_fallback_event(admin, role, spec)` as fire-and-forget logging to `zeus.governance_events`. Attempting to use Claude as a JUDGE/WORKER/FAST provider is not blocked by a runtime check — it is impossible because the factory for Claude does not exist in those chains.

### Alternatives considered

- **Keep the status quo (scattered provider choices)** — rejected because Article 0 enforcement was impossible and audit was manual.
- **Use `swarm-models` library from The Swarm Corporation** — rejected for now because our needs are specific (Article 0 compliance, `zeus.governance_events` integration) and the library adds a dependency without covering those needs. Reconsider in Q3 2026 if we need richer multi-provider failover semantics.
- **Use LangChain's LLM abstraction** — rejected because LangChain is a heavy dependency for what is ~300 lines of focused code. Atlas favours bespoke primitives over framework adoption for core infrastructure.
- **Accept Perplexity's proposal of "Claude as safe/user-facing"** — rejected and challenged formally. Article 0 says Haiku is last resort only, not first-line. Documented in `docs/PERPLEXITY-RECONCILIATION-2026-04-11.md`.

---

## Consequences

**Positive:**
- Single point of audit for every LLM call routing decision.
- Article 0 enforcement is now structural, not advisory.
- Fallback events land in `zeus.governance_events` as `provider_fallback` entries with severity `low` — operators can see when production is running on a degraded provider.
- Future additions (Cerebras when key arrives, new Gemini models) are one-factory-function-and-one-chain-update away.

**Negative:**
- The router is synchronous `select_provider()` returning a spec; actual LLM invocation still happens in the calling code. A v2 could wrap invocation itself.
- No automatic rate-limit awareness — if NVIDIA starts 429ing we do not gracefully shift traffic. Q3 2026 work.
- `is_fallback` semantic is naive — it reports `True` for any non-primary choice even if the primary is deliberately disabled. Medium-priority cleanup, noted by security audit agent Session 93.

**Neutral:**
- OpenAI and DeepSeek are referenced in the config file but have no factory functions in `_CHAINS`. They are dead fields. Either wire them into a role or delete the config fields. Deferred pending CEO decision on whether DeepSeek becomes a swarm worker.

---

## Verification

- `python -c "from app.services.model_router import select_provider, ProviderRole; ..."` with loaded env returns:
  - JUDGE → `nvidia/nvidia/llama-3.1-nemotron-ultra-253b-v1` (fallback=True because Cerebras/Ollama unavailable)
  - WORKER → `nvidia/meta/llama-3.3-70b-instruct` (fallback=True)
  - FAST → `groq/llama-3.1-8b-instant` (fallback=False)
  - SAFE_USER_FACING → `gemini/gemini-2.5-pro` (fallback=False)
- Without env loaded: JUDGE/WORKER/FAST return `NONE AVAILABLE`, SAFE_USER_FACING returns `anthropic/claude-haiku` (last resort confirmed).
- No code path exists for Claude in JUDGE/WORKER/FAST chains — grep `claude` in `_CHAINS` returns zero matches for those three roles.

---

## Follow-ups

1. **Cerebras API key acquisition** (CEO action) — once available, Cerebras becomes primary for JUDGE and WORKER, dropping latency significantly.
2. **Ollama model selection** — decide between `qwen2.5:32b` and `llama3.3:70b` for local fallback based on Yusif's hardware. Deferred to post-decision on home server.
3. **Rate-limit awareness** — Q3 2026 work, currently the router is latency-blind.
4. **Dead fields cleanup** — delete `openai_api_key` and `deepseek_api_key` from `config.py` if they remain unused by Q2 close.
