## Acceptance Criteria — Path B: LiteLLM gateway (Phase 1)

- [ ] `packages/swarm/providers/litellm_adapter.py` exists with `LiteLLMProvider` implementing `LLMProvider` ABC
- [ ] `SWARM_USE_LITELLM=0` (default): `ProviderRegistry.discover()` returns legacy providers, no behavioral change
- [ ] `SWARM_USE_LITELLM=1`: `ProviderRegistry.discover()` returns single `LiteLLMProvider` instance
- [ ] All existing provider files (`gemini.py`, `groq_*.py`, etc.) untouched
- [ ] `litellm>=1.50.0` in `apps/api/requirements.txt`
- [ ] ADR-011 filed in `docs/adr/`
- [ ] Python syntax valid on both modified files
