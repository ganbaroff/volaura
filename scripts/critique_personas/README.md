# Independent Critique Personas

System prompts for `scripts/critique.py` — independent adversarial red-team voices via Anthropic API.

## Why this exists

Cowork-Atlas (sandbox-restricted to `api.anthropic.com`) cannot use Agent-tool subagents for critique because parent context bleeds into the subagent and triggers "Prompt is too long" on trivial requests. This wrapper bypasses Agent tool entirely — direct HTTP to Anthropic API, fresh context per persona, no parent-context inheritance.

## Usage

```bash
python scripts/critique.py \
  --target docs/research/az-capital-crisis-2026/01-macro-scenarios.md \
  --personas macro-economist,geopolitical-analyst,forecasting-methodologist,local-insider \
  --out docs/research/az-capital-crisis-2026/critiques \
  --model opus
```

Flags:
- `--target` — path to the .md document being critiqued
- `--personas` — comma-separated names matching files in this directory (without `.md`)
- `--out` — output directory; one `<persona>.md` per persona + `synthesis-input.json` aggregate
- `--model` — `opus` (claude-opus-4-6, $15/$75 per M tokens) or `sonnet` (claude-sonnet-4-6, $3/$15 per M)
- `--workers` — parallel API calls (default 4)
- `--dry-run` — estimate cost only, no API calls

## Cost model

Conservative estimate: ~5K input + 4K output per persona.
- Sonnet: ~$0.075 per persona × 7 = ~$0.53 per full critique batch
- Opus: ~$0.38 per persona × 7 = ~$2.63 per full critique batch

Hard ceiling: $3 per single batch (`COST_CEILING_USD` in `critique.py`). Above this the script aborts before any API call.

## Persona catalog

| Name | Discipline | When to use |
|---|---|---|
| `macro-economist` | EM crisis macro, IMF/WB perspective, historical analogues | Macro scenarios, currency regime |
| `geopolitical-analyst` | South Caucasus, Russia-Turkey-Iran-AZ dynamics, named decision-makers | Country-risk, regional escalation |
| `forecasting-methodologist` | Tetlock/superforecaster, base rates, falsifiability, calibration | Any document making probability claims |
| `local-insider` | Baku business reality, informal channels, family-ownership map | When Western-analyst lens may miss local truth |
| `quant` | Numbers, ∂/∂ sensitivity, fat-tail risk, SOFAZ accounting | Magnitude claims, financial flows |
| `legal` | Capital controls, sanctions, FATF/OFAC, Stripe/Mercury reality | Cross-border money mechanics |
| `devil` | Steelman opposition, hidden assumption attacks, base rate sceptic | Final challenge before decision |

## Adding a new persona

1. Create `scripts/critique_personas/<name>.md`
2. Write the system prompt: identity (background, credentials, language), discipline (what they catch, how they think), output style (tone, what they refuse to soften)
3. Reference: existing personas in this directory
4. No code change needed — the script auto-loads any file in this directory by name.

## Output structure

Each persona file ends with mandatory sections (see `_build_user_prompt` in `critique.py`):
- `## TOP_ATTACK` — single strongest reason document is wrong
- `## FINAL_A` — steelman FOR the document's thesis
- `## FINAL_B` — strongest argument AGAINST
- `## FINAL_C` — most likely scenario document fails to consider
- `## FINAL_D` — what evidence would change verdict

`synthesis-input.json` aggregates all `TOP_ATTACK` sections for convergence analysis (multiple personas converging on the same attack vector = strong signal).

## Failure modes

- Missing `ANTHROPIC_API_KEY` → exit 2 with clear error
- Missing target file → exit 2
- Missing persona file → exit 2 (validates BEFORE spending money)
- Cost estimate above `$3` ceiling → exit 3
- Per-persona API failure → writes `<persona>.err`, batch continues, exit 1 if any failure

Per `.claude/rules/atlas-operating-principles.md`: prefer assuming with `[ASSUMED]` over asking. Personas have `[ASSUMED]` tags built into their persona prompts where uncertainty exists.
