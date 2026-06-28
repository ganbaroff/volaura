# AGENTS.md — packages/swarm

**Parent manifest:** [../../AGENTS.md](../../AGENTS.md)

## Scope

Multi-provider LLM swarm: `autonomous_run`, perspectives, proposals, LiteLLM adapter. Internal control plane — not user-facing product.

## May depend on

- `packages/swarm/tools/*`, Supabase service-role where documented
- LiteLLM router (ADR-011/013)

## May NOT depend on

- `apps/api/app/*` internals, `apps/web/*`

## LLM policy (ADR-013)

NVIDIA NIM → Ollama → Gemini → Groq. **No Cerebras.** No Claude as swarm agent (Article 0).

## Tests

- `packages/swarm/tests/` when present
- Repo-root control-plane tests: `tests/test_litellm_adapter.py`, daemon suite in CI
