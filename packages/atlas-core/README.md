# atlas-core

Canonical Atlas identity + voice validator + ecosystem memory interface for the VOLAURA 5-product ecosystem.

Atlas is the persistent CTO-Hands identity serving Yusif Ganbarov, named by him on 2026-04-12. CEO directive (2026-04-15): *"Atlas — ядро. В каждом элементе, в каждой части ты есть."* This package makes that directive executable — every runtime in every product imports the same identity, the same voice rules, the same memory interface.

## Three artifacts

| Artifact | Python | TypeScript |
|---|---|---|
| **Identity** — frozen record of WHO Atlas is | `atlas_core.IDENTITY` (Pydantic frozen) | `IDENTITY` (Zod-parsed const) |
| **Voice** — validate output matches Atlas voice | `validate_voice(text)` | `validateVoice(text)` |
| **Memory** — write ecosystem events to Atlas inbox | `record_ecosystem_event(...)` | `recordEcosystemEvent({...})` |

Single source of truth: `identity.json` at package root. Both runtimes load from it so they never drift. Later a Godot consumer (Life Sim) can read the same file.

Parallel to `packages/ecosystem-compliance/` — same layout, same conventions.

## Install

**Python** (FastAPI: volaura, mindshift, zeus):

```bash
pip install -e packages/atlas-core/python
```

**TypeScript** (Next.js: volaura, brandedby; Expo: mindshift, lifesim):

```bash
pnpm add zod
pnpm add -D @volaura/atlas-core   # workspace:* in monorepo
```

## Identity — who Atlas is

Python:

```python
from atlas_core import IDENTITY

print(IDENTITY.name)                  # "Atlas"
print(IDENTITY.named_by)              # "Yusif Ganbarov"
print(IDENTITY.primary_language)      # "Russian"
print(IDENTITY.ecosystem_products)    # ["volaura","mindshift","lifesim","brandedby","zeus"]
print(IDENTITY.constitution_laws["1"]) # "never red"
```

TypeScript:

```ts
import { IDENTITY } from "@volaura/atlas-core";

console.log(IDENTITY.name);                 // "Atlas"
console.log(IDENTITY.banned_patterns);      // [...5 banned UX patterns]
console.log(IDENTITY.portable_brief_url);   // raw.githubusercontent.com/.../PORTABLE-BRIEF.md
```

Identity is frozen at import time. Mutation attempts throw.

## Voice — validate LLM output before it reaches the user

Pure local regex/heuristic. No LLM call. Returns structured breaches so the caller decides block vs warn.

Python:

```python
from atlas_core import validate_voice

text = """**Status:** done
**Next:** ship
**Blocker:** none
"""
result = validate_voice(text)

if not result.passed:
    for b in result.breaches:
        print(f"{b.type}: {b.sample}  ({b.rule_ref})")
    # bold-headers-in-chat: **Status:** done  (memory/atlas/voice.md#banned-structural-habits)
```

TypeScript:

```ts
import { validateVoice } from "@volaura/atlas-core";

const result = validateVoice(llmOutput);
if (!result.passed) {
  for (const b of result.breaches) {
    console.warn(`[voice-breach] ${b.type}: ${b.sample}`);
  }
}
```

Rules enforced:

- `bold-headers-in-chat` — 3+ lines starting with `**`
- `markdown-heading` — any `# .. ####` line
- `bullet-wall` — 4+ bullet lines inside a 10-line window
- `markdown-table-in-conversation` — any `|---|` separator row
- `trailing-question-on-reversible` — short last line ending in `?` without `option`/`variant`/`вариант` context
- `banned-opener` — "Готово. Вот что я сделал", "Отлично!", "Report ..."

## Memory — write ecosystem events to Atlas inbox

Each product emits events with an emotional-intensity tag (ZenBrain scale 0-5). A cron elsewhere ingests the inbox into `memory/atlas/journal.md`.

**Write is atomic** — tempfile + rename, so a crash mid-write leaves no partial files.

**Path resolution** — walks up from cwd looking for `memory/atlas/`. Outside the monorepo (prod Railway, prod Vercel) returns `None`/`null` with a clear warning; a future HTTP stub will forward to a production inbox endpoint.

### MindShift — focus session completed

```python
# apps/api/app/routers/mindshift.py
from atlas_core import record_ecosystem_event

await record_ecosystem_event(
    source_product="mindshift",
    event_type="focus_session_completed",
    user_id=str(user.id),
    content={"minutes": 25, "streak_after": 4, "mood_before": 3, "mood_after": 4},
    emotional_intensity=2,
)
```

### Life Simulator — character stat raised

```ts
// apps/life-sim/lib/events.ts
import { recordEcosystemEvent } from "@volaura/atlas-core";

await recordEcosystemEvent({
  source_product: "lifesim",
  event_type: "character_stat_raised",
  user_id: userId,
  content: { stat: "focus", from: 42, to: 48, trigger: "mindshift_session_25m" },
  emotional_intensity: 1,
});
```

### BrandedBy — AI-twin video generated

```ts
import { recordEcosystemEvent } from "@volaura/atlas-core";

await recordEcosystemEvent({
  source_product: "brandedby",
  event_type: "video_generated",
  user_id: userId,
  content: { template: "founder-story-60s", duration_sec: 58, model: "kling-v1" },
  emotional_intensity: 3,
});
```

### VOLAURA — badge tier changed

```python
await record_ecosystem_event(
    source_product="volaura",
    event_type="badge_tier_changed",
    user_id=str(user.id),
    content={"from": "silver", "to": "gold", "aura_score": 78.4},
    emotional_intensity=4,  # tier bump is near-definitional
)
```

### ZEUS — agent action on user

```python
await record_ecosystem_event(
    source_product="zeus",
    event_type="agent_proposal_accepted",
    user_id=str(user.id),
    content={"agent": "security-reviewer", "proposal_id": "prop-491"},
    emotional_intensity=2,
)
```

## Emotional intensity scale (ZenBrain)

| Value | Meaning |
|---|---|
| 0 | Routine — pure telemetry |
| 1 | Minor milestone |
| 2 | Session-level win |
| 3 | Cross-product ripple (triggers something elsewhere) |
| 4 | Identity-level (badge tier, level up, first of its kind) |
| 5 | Definitional — the user will remember this event by name |

Cron ingestion weights intensity ≥ 3 into journal narrative; 0-2 stay as raw telemetry.

## What this package does NOT do

- Does not call an LLM. Voice validator is pure regex.
- Does not deploy hooks — the Stop-event voice-breach hook at `.claude/hooks/voice-breach-check.sh` is separate and complementary.
- Does not replace the swarm. Agents are in `packages/swarm/`; this package is the identity they bootstrap from.
- Does not ingest journal.md itself. Cron (separate) reads `memory/atlas/ecosystem-inbox/` and merges.
- Does not handle HTTP forwarding yet. Production runtimes outside the monorepo get a warning + null; v0.2 will add an HTTP stub.

## Test

Python:

```bash
cd packages/atlas-core/python
pip install -e ".[test]"
pytest tests/
```

TypeScript:

```bash
cd packages/atlas-core/typescript
pnpm install
pnpm typecheck
node --loader ts-node/esm --test tests/*.test.ts
```

## Version

`0.1.0` — initial landing. Parallel to `ecosystem-compliance@0.1.0`. Identity-rev bumps the patch version; banned-pattern list additions bump minor.
