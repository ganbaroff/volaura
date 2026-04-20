---
description: Invoke Doctor Strange v2 — multi-model validation before any recommendation. Requires 2 external model calls. Use before any architecture or infrastructure decision.
---

When this command is invoked with a question or decision to evaluate:

**Gate 1 — EXTERNAL MODEL REQUIRED (not optional)**
Call at least ONE external model for path validation. Options in priority order:
- Cerebras Qwen3-235B (fastest, primary): `curl https://api.cerebras.ai/v1/chat/completions`
- DeepSeek R1 (adversarial): via OpenRouter or direct API
- NVIDIA NIM (architecture): `https://integrate.api.nvidia.com/v1`

Prompt for path validation:
> "Here is a proposed technical decision: [DECISION]. Name 3 concrete failure modes. Be adversarial. Focus on production failure scenarios, not theoretical concerns."

**Gate 2 — OBJECTION-RESPONSE PAIRS**
For each failure mode the external model raises:
```
OBJECTION: <external model finding>
COUNTER-EVIDENCE: <tool call result that disproves or mitigates>
RESIDUAL RISK: <what remains after mitigation, honestly>
```
Writing "mitigated" without a tool call = decoration. Not accepted.

**Gate 3 — POST-MILESTONE RETROSPECTIVE** (after implementation completes)
One external model call: "Given what actually happened during this milestone, was the original path correct or should the next milestone pivot?"

**Output format (required):**
```
RECOMMENDATION: <one path>
EVIDENCE: <external model calls + tool results>
WHY NOT OTHERS: <one line per rejected option>
FALLBACK IF BLOCKED: <one alt path>
ADVERSARIAL: <objection-response pairs>
```

Source: `.claude/rules/atlas-operating-principles.md` — Doctor Strange v2 protocol.
Self-confirmation (no external call) = CLASS 11 violation. Do not proceed without Gate 1.
