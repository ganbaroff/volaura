# ADR-011: LiteLLM gateway migration for Python swarm

**Date:** 2026-04-19
**Status:** PROPOSED (Phase 1 shipped behind feature flag)
**Deciders:** Atlas CTO

## Context

The swarm provider layer (`packages/swarm/providers/`) contained 7 bespoke files implementing individual LLM provider integrations (Gemini, Groq x3, DeepSeek, OpenAI, dynamic discovery). Each maintained its own HTTP plumbing, retry logic, and error handling. Two call sites consumed the interface: `engine.py` and `pm.py`.

The existing fallback chain (defined in CLAUDE.md): Cerebras Qwen3-235B → Ollama local → NVIDIA NIM → Anthropic Haiku (last resort, never primary agent).

## Decision

Replace bespoke provider files with a single `LiteLLMProvider` that routes through `litellm.Router`. The migration is **behind a feature flag** (`SWARM_USE_LITELLM=1`) to allow zero-risk phased rollout.

### What changed

- `packages/swarm/providers/litellm_adapter.py` — new file, ~130 lines, implements `LLMProvider` ABC
- `packages/swarm/providers/__init__.py` — `ProviderRegistry.discover()` checks `SWARM_USE_LITELLM` env var first
- `apps/api/requirements.txt` — added `litellm>=1.50.0`
- No changes to `engine.py`, `pm.py`, or any consumer code

### Fallback chain in LiteLLM Router

```
primary:   cerebras/qwen-3-235b-a22b-instruct  (CEREBRAS_API_KEY)
fallback1: ollama/qwen2.5:32b                  (localhost:11434, always registered)
fallback2: nvidia_nim/meta/llama-3.3-70b-instruct (NVIDIA_API_KEY)
fallback3: anthropic/claude-haiku-4-5-20251001 (ANTHROPIC_API_KEY, last resort)
```

## Phased rollout plan

| Phase | When | Action |
|-------|------|--------|
| 1 (shipped) | 2026-04-19 | Adapter live, `SWARM_USE_LITELLM=0` default — no production impact |
| 2 | After 48h observation | Enable flag in one CI job. Compare swarm output schema. |
| 3 | After Phase 2 clean | Flip default to ON. Keep flag for emergency rollback. |
| 4 | 2 weeks after Phase 3 | Delete legacy provider files after confirmed stability. |

## Consequences

**Benefits:**
- Single interface across 100+ providers — adding new models requires zero code
- Built-in retry + fallback + cost tracking via LiteLLM's `success_callback`
- Removes ~200 lines of bespoke HTTP/retry glue
- Router handles TOCTOU race conditions in fallback selection

**Risks:**
- LiteLLM error semantics differ from `base.py` — mitigated by feature flag + parity tests before Phase 3
- `response_format: json_object` not universally supported — mitigated by JSON extraction fallback in adapter
- Ollama local is always registered but may be offline — Router will skip it silently via fallback

## Rejected alternatives

- **Keep bespoke providers** — each new provider requires a new file + HTTP client. Not scalable past 5 providers.
- **OpenRouter as gateway** — adds external dependency and latency vs direct provider calls. LiteLLM routes direct.
- **Full rewrite now** — risk of breaking the 13 registered perspectives. Phased flag approach is safer.

## Call sites at migration time

4 import lines, 2 files:
- `engine.py:47-49` — imports `ProviderRegistry`, `LLMProvider`, `load_discovered_providers`
- `pm.py:37-38` — imports `ProviderRegistry`, `LLMProvider`

No changes to either file required — adapter is drop-in.
