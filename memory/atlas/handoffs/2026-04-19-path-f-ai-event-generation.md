# Path F — AI-Generated Life-Sim Events (ADR-012)

**Source:** Cowork-Atlas, Session 121 continuation
**Target:** Terminal-Atlas (Claude Code CLI on CEO's Windows box)
**CEO directive (verbatim):** "событийная очередь 45 карточек?) заебись. а не много? давай меньше. п.с сарказм там ии должен был генерировать всю историю. а не пре дейайнд пре дефайд как фолбек"
**Status at handoff:** Terminal said "Запускаю ADR" — context compaction hit before ADR-012 was written. Resume from scratch with this self-contained spec.

---

## Scope in one line
AI generates each Life-Sim event from current character state; JSON pool of ~8 archetype skeletons is OFFLINE FALLBACK ONLY.

## Why this path (CEO call, not yours to revisit)
45 pre-defined JSON cards = the exact "pre-defined as fallback" anti-pattern CEO flagged. The entire pitch of Life Simulator inside VOLAURA is "твой симулятор жизни пишет AI который помнит всё что ты сделал в VOLAURA/MindShift" — a 45-card JSON library is the opposite of that pitch. We keep a few archetype skeletons strictly as the "no network / LLM down" escape hatch.

## Three phases (ship them in this order, not all at once)

**Phase 1 — endpoint behind feature-flag (this PR).**
- `POST /api/character/generate-event` implemented in FastAPI.
- LiteLLM router (SWARM_USE_LITELLM flag from Path B commit 1a9c910) used with chain: Cerebras Qwen3-235B → Ollama → NVIDIA NIM → Haiku.
- Godot adapter: `api_client.generate_event(state)` with 2s timeout; on timeout or non-2xx → read from JSON pool (unchanged behavior, old code path intact).
- Default config: `LIFESIM_EVENTS_AI=0` (JSON still primary). Ship the endpoint dark.

**Phase 2 — enable flag (next PR, after Phase 1 parity test).**
- Flip `LIFESIM_EVENTS_AI=1` in Railway env.
- AI becomes primary; JSON fires only on timeout/error.
- Observe 48h in prod, watch p50/p95 latency on the endpoint, error rate, fallback rate.

**Phase 3 — prune (third PR, only after Phase 2 is stable).**
- Delete 37 of 45 JSON cards.
- Keep 8 archetype skeletons: `crisis`, `opportunity`, `social`, `health`, `career`, `milestone`, `random_small`, `random_big`.
- These 8 are the fallback library, not the content library.

Do not compress these phases into one PR. Each phase has its own revert button.

---

## Files to create/modify (Phase 1 only)

### 1. `docs/adr/ADR-012-ai-generated-events.md` (new)

Use the same section shape as ADR-010 and ADR-011. Minimum sections:

- **Context:** 45-card JSON pool was shipped as primary generator; CEO called out the pre-defined-as-fallback inversion; Life Sim pitch is AI-driven narrative memory across VOLAURA + MindShift.
- **Decision:** `POST /api/character/generate-event` is the primary event source. JSON pool of 8 archetype skeletons is the offline fallback only. LiteLLM router with Cerebras primary, 2s timeout budget.
- **API contract:** (exact JSON schema below)
- **Fallback policy:** timeout OR 5xx OR invalid schema → Godot picks random archetype from 8-skeleton pool; no retry at the Godot layer; API may retry internally across router chain.
- **Content guardrails:** NEVER RED (Foundation Law #1) — emotional_tone token set excludes "anger", "rage", "despair", "panic"; uses "tense", "anxious", "melancholy", "bittersweet", "hopeful", "triumphant", "playful", "heavy", "light" only. No gratuitous violence, no romantic content for characters <18, no medication brand names.
- **Memory contract:** prompt assembles `{age, 8 stats, career, last 5-10 character_events, relationships}` — `character_events` is the cross-product memory bus (VOLAURA + MindShift + Life Sim all write here), so "AI remembers" is literally reading this table.
- **Phases:** the three phases above, with explicit rollback for each.
- **Revisit triggers:** p95 endpoint latency > 3s OR fallback rate > 15% OR any CEO complaint about card feeling generic.

### 2. `apps/api/app/api/character.py` — new endpoint

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from loguru import logger

from app.deps import SupabaseUser, CurrentUserId
from app.services.litellm_router import generate_json  # from Path B adapter

router = APIRouter(prefix="/api/character", tags=["character"])


class Stat(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Literal["health","mood","energy","intellect","charisma","discipline","creativity","resilience"]
    value: int = Field(ge=0, le=100)


class RecentEvent(BaseModel):
    event_type: str
    payload: dict
    created_at: str  # ISO


class GenerateEventRequest(BaseModel):
    age: int = Field(ge=0, le=120)
    stats: list[Stat]
    career: str | None = None
    relationships: list[dict] = Field(default_factory=list)
    recent_events: list[RecentEvent] = Field(default_factory=list, max_length=10)


class EventChoice(BaseModel):
    label: str = Field(max_length=80)
    stat_deltas: dict[str, int]  # {"mood": -5, "discipline": +3}


class GeneratedEvent(BaseModel):
    archetype: Literal["crisis","opportunity","social","health","career","milestone","random_small","random_big"]
    title: str = Field(max_length=80)
    description: str = Field(max_length=400)
    choices: list[EventChoice] = Field(min_length=2, max_length=4)
    emotional_tone: Literal["tense","anxious","melancholy","bittersweet","hopeful","triumphant","playful","heavy","light"]


SYSTEM_PROMPT = """You are the narrator of a life simulator. Given a character's
current state and recent history, generate ONE event card that feels personally
relevant to what just happened. Respect these rules:

- Never reference medication brand names, never sexualize minors, never depict
  gratuitous violence.
- Emotional tone MUST be one of: tense, anxious, melancholy, bittersweet,
  hopeful, triumphant, playful, heavy, light. Never anger/rage/despair/panic.
- 2 to 4 choices per card; each choice has stat_deltas in -15..+15 range.
- Title: ≤80 chars, description: ≤400 chars.
- Output strict JSON matching the schema.
"""


@router.post("/generate-event", response_model=GeneratedEvent)
async def generate_event(
    req: GenerateEventRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
) -> GeneratedEvent:
    # Budget: 2s total. LiteLLM router handles internal fallback chain.
    try:
        result = await generate_json(
            system=SYSTEM_PROMPT,
            user_payload=req.model_dump(),
            schema=GeneratedEvent.model_json_schema(),
            timeout_s=2.0,
        )
    except TimeoutError:
        logger.warning("generate_event timeout", user_id=user_id)
        raise HTTPException(
            status_code=504,
            detail={"code": "LIFESIM_EVENT_TIMEOUT", "message": "Event generation timed out"},
        )
    except Exception as e:
        logger.error("generate_event failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=502,
            detail={"code": "LIFESIM_EVENT_FAILED", "message": "Event generation failed"},
        )

    try:
        return GeneratedEvent.model_validate(result)
    except Exception as e:
        logger.error("generate_event schema mismatch", user_id=user_id, error=str(e), raw=result)
        raise HTTPException(
            status_code=502,
            detail={"code": "LIFESIM_EVENT_SCHEMA", "message": "AI returned invalid schema"},
        )
```

Route registration: add `router` to the FastAPI app include_router list next to the other character routes. If `character.py` already exists with existing routes, append this endpoint to the same module (don't create a sibling file — per update-don't-create rule).

### 3. `apps/api/app/services/litellm_router.py` — `generate_json` helper

If Path B commit 1a9c910 didn't expose `generate_json`, add it there. Shape:

```python
async def generate_json(
    system: str,
    user_payload: dict,
    schema: dict,
    timeout_s: float = 2.0,
) -> dict:
    """Call the LiteLLM chain with JSON response format + schema.
    
    Chain order (from ADR-011): Cerebras qwen3-235b → Ollama local →
    NVIDIA NIM → Anthropic Haiku. Internal per-call timeout proportional
    to timeout_s / len(chain). Returns parsed dict. Raises TimeoutError
    if whole chain exhausts budget.
    """
    ...
```

If the adapter is sync-only today, wrap it in `asyncio.to_thread` with `asyncio.wait_for`. Do NOT block the event loop on a sync HTTP call.

### 4. Godot side — `scripts/controllers/event_queue_controller.gd` (or equivalent)

Current code reads JSON. New code path:

```gdscript
# Roughly — adapt to actual file structure
func next_event() -> Dictionary:
    if AppController.lifesim_events_ai_enabled:  # reads LIFESIM_EVENTS_AI flag from remote config or hardcoded false for Phase 1
        var state := _build_character_state()
        var ai_event = await volaura_api.generate_event(state, 2.0)  # 2s timeout
        if ai_event != null and _validate_event_schema(ai_event):
            return ai_event
        push_warning("AI event fell back to archetype pool")
    return _pick_archetype_from_pool()


func _pick_archetype_from_pool() -> Dictionary:
    # Pool reduced to 8 archetype skeletons in Phase 3.
    # Phase 1: keep the existing 45-card pool untouched as transitional fallback.
    var idx := randi() % event_pool.size()
    return event_pool[idx]
```

### 5. `scripts/managers/api_client.gd` — add `generate_event`

```gdscript
func generate_event(state: Dictionary, timeout_s: float = 2.0) -> Variant:
    if not is_authenticated():
        return null
    var http := HTTPRequest.new()
    add_child(http)
    http.timeout = timeout_s
    var body_str := JSON.stringify(state)
    var headers := PackedStringArray([
        "Content-Type: application/json",
        "Authorization: Bearer %s" % _jwt
    ])
    var err := http.request(base_url + "/api/character/generate-event", headers, HTTPClient.METHOD_POST, body_str)
    if err != OK:
        http.queue_free()
        return null
    var result = await http.request_completed
    http.queue_free()
    var response_code: int = result[1]
    var body: PackedByteArray = result[3]
    if response_code < 200 or response_code >= 300:
        return null
    var parsed = JSON.parse_string(body.get_string_from_utf8())
    if typeof(parsed) != TYPE_DICTIONARY:
        return null
    return parsed
```

Pair this with the `_api_post` helper from commit dc423bd — they share the HTTPRequest pattern; extract a private helper if the duplication bothers you, but don't let refactor scope-creep past Phase 1.

---

## Acceptance criteria (Phase 1 — DONE when all true)

1. `docs/adr/ADR-012-ai-generated-events.md` exists with all required sections.
2. `POST /api/character/generate-event` responds 200 with valid JSON matching `GeneratedEvent` schema for a sample state (age=25, mid stats, empty recent_events).
3. Endpoint respects 2s timeout budget; timeout returns 504 with structured error body.
4. Unit test `apps/api/tests/test_generate_event.py` covers: valid response, timeout path, schema-mismatch path. At least one test hits the real router with LiteLLM stub (mock the upstream HTTP, don't mock the router itself).
5. `SWARM_USE_LITELLM=1` set in Railway env for the API service (coordinate with CEO; he has Railway access).
6. Godot `api_client.generate_event` compiles under Godot 4.6.1 (no parse errors via `godot --headless --check-only`).
7. `LIFESIM_EVENTS_AI` flag defaults to false — existing JSON pool flow is the default for this PR.
8. Foundation Law #1 scan: grep for "red", "anger", "rage" in new files → zero hits.
9. Commit message body contains `Verified-against-library-source: apps/api/app/services/litellm_router.py:<line>` if you touch auth-related bits (not relevant here, but if the pattern surfaces, honor the frontend.md gate).
10. Separate PR, not mixed with PR #13.

---

## What NOT to do (learned from this session)

- Don't bundle Phase 2 + Phase 3 into Phase 1. CEO gave a clear directive on order.
- Don't delete the 45-card JSON pool yet. Phase 3 only.
- Don't add retry logic at the Godot layer. The router chain retries internally; Godot either gets an event or falls back. One shot.
- Don't wire `generate_event` into actively running sessions as a blocking call — the 2s timeout is a ceiling, not a SLA. Godot event loop must not freeze.
- Don't add analytics/PostHog calls here. Path D owns that. Keep scopes clean.
- Don't mix this with LiteLLM parity tests (T4). That's its own PR.

---

## Rollback (per phase)

- **Phase 1:** set `LIFESIM_EVENTS_AI=0` (already the default). Endpoint stays dark, no user impact.
- **Phase 2:** flip flag back to 0. JSON becomes primary again. No data migration needed.
- **Phase 3:** git revert the 37-card deletion commit. JSON pool restored.

---

## Report back

When Phase 1 ships, Terminal writes one line to `memory/atlas/journal.md` (timestamp + commit sha + PR link) and updates the dashboard `docs/dashboards/atlas-status-2026-04-19.html` Path F row to `Done · <sha>`.

That's it. Ship Phase 1, report, wait for CEO to approve Phase 2 flag flip.
