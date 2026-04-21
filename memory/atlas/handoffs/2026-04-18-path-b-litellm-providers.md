# Handoff — Path B: LiteLLM gateway migration for Python swarm

## STATUS
**READY 2026-04-18 Baku.** Path C closed (commit 1c46e5f). Path A closed (commit f19fc1e — LifeSim Godot 4.6.1 parse-order fixed, root cause: `_get()` shadowed `Object._get(StringName)` virtual). Path B can start.

## TARGET TOOL
Claude Code CLI (Terminal-Atlas) inside `C:/Projects/VOLAURA/` or wherever the working copy is. Same filesystem as Cowork.

## GOAL
Replace the bespoke LLM-hierarchy routing in `packages/swarm/providers/` with LiteLLM's unified interface. Preserve the existing fallback chain semantics (Cerebras → Ollama → NVIDIA NIM → Anthropic Haiku last-resort) via LiteLLM's `Router` with custom routing strategy.

## CONTEXT (verified 2026-04-18 by Cowork-Atlas)

### Current layout
```
packages/swarm/providers/
  __init__.py          (7018 B)
  base.py              (4017 B)
  deepseek.py          (1369 B)
  dynamic.py           (7238 B)
  gemini.py            (1337 B)
  groq_gemma.py        (1218 B)
  [additional providers — list via `ls packages/swarm/providers/`]
```

### What consumes this
`agent_hive.py` (40 KB), `engine.py` (22 KB), `pm.py` (40 KB), `autonomous_run.py` (79 KB), `coordinator.py` (16 KB), `reflexion.py`, `perspective_registry.py`, `skills_loader.py` — all call into `packages/swarm/providers/`.

### Grep confirmed (session 120)
`grep -rn "from.*utils\|import.*utils" packages/swarm/*.py` returns **zero matches**. There is no `packages/swarm/utils/` directory. The migration target is `providers/`, not a phantom `utils/`.

### LiteLLM adoption rationale
- Single interface across 100+ LLM providers (OpenAI, Anthropic, Groq, Cerebras, DeepSeek, Gemini, NVIDIA, Ollama, OpenRouter).
- Built-in retry + fallback + load balancing via `Router`.
- Unified cost tracking via `success_callback`.
- Removes ~200 lines of bespoke provider glue.

### Risks (adversarial from DeepSeek, session 120)
- "Gateway collapse if packages/swarm/utils/ doesn't exist" — **refuted** (no such path exists and nothing imports from it).
- Real risk: behavior drift in reflexion/pm/coordinator if LiteLLM's error semantics differ from current base.py. Must shim.

## TASKS

### T1. Inventory current provider call sites
```bash
grep -rn "from packages.swarm.providers\|from .providers\|from packages.swarm import providers" packages/swarm/ | tee /tmp/provider-callsites.txt
wc -l /tmp/provider-callsites.txt
```
Attach list to commit message. We need to know every call site before refactoring.

### T2. Install LiteLLM behind a feature flag
- Add `litellm>=1.50` to `packages/swarm/pyproject.toml` (or root `pyproject.toml` — verify which is authoritative).
- Create `packages/swarm/providers/litellm_adapter.py` — new file, implements `base.py`'s abstract interface using `litellm.completion` and `litellm.Router`.
- Do NOT delete any existing provider file yet.
- Feature flag: env var `SWARM_USE_LITELLM=1` — when unset, use legacy providers. When set, use litellm_adapter.

### T3. Wire fallback chain
Router config (Python):
```python
# Mirrors current fallback semantics: Cerebras → Ollama → NVIDIA NIM → Haiku
model_list = [
    {"model_name": "primary",   "litellm_params": {"model": "cerebras/qwen-3-235b-a22b-instruct-2507", "api_key": os.environ["CEREBRAS_API_KEY"]}},
    {"model_name": "ollama-fb", "litellm_params": {"model": "ollama/qwen2.5:32b", "api_base": "http://localhost:11434"}},
    {"model_name": "nvidia-fb", "litellm_params": {"model": "nvidia/...", "api_key": os.environ["NVIDIA_API_KEY"]}},
    {"model_name": "haiku-lr",  "litellm_params": {"model": "anthropic/claude-haiku-4-5-20251001", "api_key": os.environ["ANTHROPIC_API_KEY"]}},
]
router = litellm.Router(model_list=model_list, fallbacks=[{"primary": ["ollama-fb", "nvidia-fb", "haiku-lr"]}])
```
Exact model IDs must be verified against the LiteLLM model-list catalog before shipping.

### T4. Parity tests — MUST PASS before flipping flag
- Pick 5 representative prompts from `packages/swarm/autonomous_run.py` CTO/researcher/builder modes.
- Run each twice: once with `SWARM_USE_LITELLM=0` (legacy), once with `SWARM_USE_LITELLM=1` (new).
- Diff the outputs. If structural format is identical (JSON schema, field order), PASS. If prose differs but schema matches, PASS. If schema differs, FAIL — fix the adapter.
- Save diffs to `docs/research/swarm/litellm-parity-2026-04-18.md`.

### T5. Phased rollout plan (document, don't execute)
Document in `docs/adr/` a phased rollout:
1. Adapter live but flag OFF (default) — ship.
2. Enable flag in one CI job — observe for 48h.
3. Flip default to ON — retain flag for rollback.
4. Remove legacy provider files after 2 weeks of ON-default.

## NON-GOALS
- Do NOT delete any existing provider file in this PR.
- Do NOT change the 13 registered perspectives in `autonomous_run.PERSPECTIVES`.
- Do NOT modify agent skills files (51 files in `packages/swarm/` skill loaders).
- Do NOT swap Anthropic Haiku as last-resort — CEO directive, stays last-resort.

## ACCEPTANCE
1. `packages/swarm/providers/litellm_adapter.py` exists with type-hinted public API matching `base.py` interface.
2. `pyproject.toml` has `litellm` as a new dep.
3. Feature flag `SWARM_USE_LITELLM` toggles routing cleanly (unit test proves both paths work).
4. Parity test document shows schema-identical outputs on 5 prompts.
5. ADR filed under `docs/adr/NNNN-litellm-gateway-migration.md`.
6. No changes to consumer code (`agent_hive.py` etc.) — adapter is drop-in.
7. Commit: `feat(swarm): litellm adapter behind feature flag (Path B phase 1)`.

## RETURN CONTRACT
```
CALL SITES FOUND: <count>
LITELLM VERSION: <x.y.z>
ADAPTER FILE: packages/swarm/providers/litellm_adapter.py (<line count>)
FEATURE FLAG: SWARM_USE_LITELLM (default: 0)
PARITY TESTS: <passed/total>
ADR NUMBER: <NNNN>
COMMIT: <sha>
BLOCKERS: <list, or "none">
```
