# Life Simulator ↔ VOLAURA Integration Spec

**Version:** 1.0 | **Sprint:** E1 (spec) / E3 (implementation)
**Date:** 2026-03-29
**Repo:** `C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026`
**Status:** READY FOR E3 IMPLEMENTATION

> Written after code audit of the Godot 4.4 codebase.
> All file paths and line numbers are verified against current code.

---

## Current State (from code audit)

| Component | Status |
|-----------|--------|
| `cloud_save_manager.gd` | Exists. `CLOUD_ENABLED = false`. HTTP functions are **stubs only** — no real network calls |
| HTTP client | **Does not exist**. Must be built from scratch using Godot's `HTTPRequest` node |
| Supabase URL/key fields | Not defined anywhere. Must be added |
| Character stats | `health, money, happiness, energy, intelligence, social` (not STR/INT — these are the real field names) |
| `character.money` | In-game currency — this is where crystal balance maps to |
| `character.to_dict()` | Exists at `character.gd:187` — serializes full character state |
| `character.from_dict()` | Exists at `character.gd:210` — loads from dictionary |
| `game_loop_controller.gd` `start_new_game()` | Line 85 — where to call `GET /api/character/state` |
| `game_loop_controller.gd` `_on_event_completed()` | Line 210 — where to post in-game events |

---

## VOLAURA → Life Simulator Stat Mapping

| VOLAURA competency | Life Sim stat | Logic |
|-------------------|--------------|-------|
| `communication` (score 0-100) | `social` (+= score * 0.1) | Communication ability = social confidence |
| `reliability` (score 0-100) | `energy` (+= score * 0.05) | Reliable people sustain energy |
| `tech_literacy` (score 0-100) | `intelligence` (+= score * 0.1) | Tech = intelligence amplifier |
| `leadership` (score 0-100) | `social` (+= score * 0.05), `happiness` (+= score * 0.03) | Leaders are social and fulfilled |
| `adaptability` (score 0-100) | `energy` (+= score * 0.05) | Adaptable people don't burn out |
| `empathy_safeguarding` | `happiness` (+= score * 0.05) | Empathic people are happier |
| `english_proficiency` | `intelligence` (+= score * 0.05) | Language = cognitive tool |
| `event_performance` | `happiness` (+= score * 0.05) | Good event performance = satisfaction |

**Crystal mapping:**
- `crystal_balance` from API → `character.money` (displayed in game as currency)
- Range: 0-9999 (cap to prevent overflow with game's own money system)
- Additive: VOLAURA crystals are ADDED to character's existing game money at load

---

## Implementation Plan (Sprint E3)

### Step 1: Create `api_client.gd`

**New file:** `scripts/managers/api_client.gd`

```gdscript
class_name VolauraAPIClient
extends Node

## HTTP client for VOLAURA character_state API.
## All calls are async (await). Never blocks game loop.

const API_BASE_URL: String = "https://api.volaura.app"
const REQUEST_TIMEOUT: float = 10.0

var _http: HTTPRequest
var _jwt_token: String = ""

func _ready() -> void:
    _http = HTTPRequest.new()
    _http.timeout = REQUEST_TIMEOUT
    add_child(_http)

## Set auth token from login flow
func set_token(token: String) -> void:
    _jwt_token = token

## GET /api/character/state
## Returns: { crystal_balance, verified_skills, character_stats } or null on error
func get_character_state() -> Dictionary:
    if _jwt_token.is_empty():
        push_warning("VolauraAPIClient: No JWT token set")
        return {}

    var headers = [
        "Authorization: Bearer " + _jwt_token,
        "Content-Type: application/json"
    ]

    _http.request(API_BASE_URL + "/api/character/state", headers)
    var result = await _http.request_completed

    var response_code: int = result[1]
    var body: PackedByteArray = result[3]

    if response_code != 200:
        push_warning("VolauraAPIClient: GET /state returned " + str(response_code))
        return {}

    var json = JSON.new()
    if json.parse(body.get_string_from_utf8()) != OK:
        push_warning("VolauraAPIClient: Failed to parse state response")
        return {}

    return json.data.get("data", {})


## POST /api/character/events
## event_type: "xp_earned" | "stat_changed" | "crystal_earned" etc.
## payload: Dictionary with event-specific fields + _schema_version: 1
func post_character_event(event_type: String, payload: Dictionary) -> bool:
    if _jwt_token.is_empty():
        return false

    payload["_schema_version"] = 1
    var body = JSON.stringify({
        "event_type": event_type,
        "payload": payload,
        "source_product": "lifesim"
    })

    var headers = [
        "Authorization: Bearer " + _jwt_token,
        "Content-Type: application/json"
    ]

    _http.request(API_BASE_URL + "/api/character/events", headers, HTTPClient.METHOD_POST, body)
    var result = await _http.request_completed

    var response_code: int = result[1]
    return response_code == 201


## GET /api/character/crystals (quick balance check)
func get_crystal_balance() -> int:
    var state = await get_character_state()
    return state.get("crystal_balance", 0)
```

---

### Step 2: Update `cloud_save_manager.gd`

**File:** `scripts/managers/cloud_save_manager.gd`

Change line 14:
```gdscript
# BEFORE:
const CLOUD_ENABLED: bool = false

# AFTER:
const CLOUD_ENABLED: bool = true
```

Add fields at the top of the class (after existing const declarations):
```gdscript
## VolauraAPIClient instance — set by app_controller after login
var api_client: VolauraAPIClient = null
```

Replace `save_to_cloud()` (line 66) stub with real implementation:
```gdscript
func save_to_cloud(data: Dictionary) -> bool:
    if not CLOUD_ENABLED or api_client == null:
        return false

    # Post save as a stat_changed event (for analytics)
    var success = await api_client.post_character_event("stat_changed", {
        "source": "cloud_save",
        "save_slot": data.get("slot_id", 0),
        "age": data.get("character", {}).get("age", 0),
    })

    # Also save to Supabase directly via REST (for cloud save persistence)
    # TODO Sprint E4: implement lifesim.save_games table write
    return success
```

Replace `load_from_cloud()` (line 101) stub with real implementation:
```gdscript
func load_from_cloud() -> Dictionary:
    if not CLOUD_ENABLED or api_client == null:
        return {}

    # Load character_state from VOLAURA API
    var state = await api_client.get_character_state()
    if state.is_empty():
        return {}

    # Convert VOLAURA state → game character enrichment data
    return {
        "crystal_balance": state.get("crystal_balance", 0),
        "verified_skills": state.get("verified_skills", []),
        "character_stats_boost": _compute_stat_boosts(state.get("verified_skills", [])),
    }


## Compute game stat boosts from VOLAURA verified skills
func _compute_stat_boosts(verified_skills: Array) -> Dictionary:
    var boosts = {"social": 0.0, "intelligence": 0.0, "energy": 0.0, "happiness": 0.0}
    for skill in verified_skills:
        var score: float = skill.get("aura_score", 0.0)
        match skill.get("skill_slug", ""):
            "communication":
                boosts["social"] += score * 0.1
            "reliability":
                boosts["energy"] += score * 0.05
            "tech_literacy":
                boosts["intelligence"] += score * 0.1
            "leadership":
                boosts["social"] += score * 0.05
                boosts["happiness"] += score * 0.03
            "adaptability":
                boosts["energy"] += score * 0.05
            "empathy_safeguarding":
                boosts["happiness"] += score * 0.05
            "english_proficiency":
                boosts["intelligence"] += score * 0.05
            "event_performance":
                boosts["happiness"] += score * 0.05
    return boosts
```

---

### Step 3: Update `game_loop_controller.gd`

**File:** `scripts/controllers/game_loop_controller.gd`

In `start_new_game()` (line 85), after character is initialized:
```gdscript
func start_new_game(character: Character) -> void:
    # ... existing init code ...

    # Load VOLAURA character state and apply boosts
    if cloud_save_manager != null and cloud_save_manager.CLOUD_ENABLED:
        var cloud_data = await cloud_save_manager.load_from_cloud()
        if not cloud_data.is_empty():
            _apply_volaura_enrichment(character, cloud_data)

    # ... rest of existing code ...
    current_state = GameState.PLAYING


## Apply VOLAURA data to game character
func _apply_volaura_enrichment(character: Character, data: Dictionary) -> void:
    # Add crystals from VOLAURA to character's money
    var crystals = data.get("crystal_balance", 0)
    if crystals > 0:
        character.money += min(crystals, 9999)  # Cap to prevent overflow

    # Apply skill-derived stat boosts
    var boosts = data.get("character_stats_boost", {})
    for stat_name in boosts:
        match stat_name:
            "social":
                character.social = min(100.0, character.social + boosts[stat_name])
            "intelligence":
                character.intelligence = min(100.0, character.intelligence + boosts[stat_name])
            "energy":
                character.energy = min(100.0, character.energy + boosts[stat_name])
            "happiness":
                character.happiness = min(100.0, character.happiness + boosts[stat_name])
```

In `_on_event_completed()` (line 210), after existing logic:
```gdscript
func _on_event_completed(event: Event, choice_index: int) -> void:
    # ... existing code ...

    # Post to VOLAURA character API (best-effort, non-blocking)
    if cloud_save_manager != null and cloud_save_manager.api_client != null:
        cloud_save_manager.api_client.post_character_event("stat_changed", {
            "source": "lifesim_event",
            "event_id": event.id,
            "event_title": event.title,
            "choice_index": choice_index,
            "character_age": character.age,
        })
        # Note: not awaited — fire and forget, never blocks gameplay
```

---

### Step 4: Update `app_controller.gd`

**File:** `scripts/controllers/app_controller.gd`

In `_initialize_managers()` (line 33), add:
```gdscript
# Create VOLAURA API client
var api_client = VolauraAPIClient.new()
api_client.name = "VolauraAPIClient"
add_child(api_client)

# Pass to cloud_save_manager
if cloud_save_manager != null:
    cloud_save_manager.api_client = api_client

# TODO Sprint E4: JWT from auth flow. For now, prompt user to paste token from VOLAURA.
# This is the SSO flow placeholder — proper login UI = Sprint E5.
```

---

## P0 Bugs to Fix Before API Integration (from code audit)

These bugs prevent the game from being playable. Fix FIRST, then wire API.

| Bug | File | Fix |
|-----|------|-----|
| `check_requirements()` doesn't exist | `event_queue_controller.gd:202` | Change to `can_trigger()` |
| EventModal never shows (auto-select choice 0) | `event_queue_controller.gd:128` | Remove auto-select, show modal first |
| `game_over.tscn` is empty | `game_over.tscn` | Build GameOver scene (10 nodes minimum) |
| `character.full_name` doesn't exist | `game_loop_controller.gd:91` | Use `character.first_name + " " + character.last_name` |

---

## Integration Test (acceptance criteria for Sprint E3)

**Test flow:**
1. Complete VOLAURA "Communication" assessment (score ≥ 40)
2. Confirm `crystal_earned` event fired: `GET /api/character/state` → `crystal_balance >= 50`
3. Open Life Simulator → start new game
4. Verify: `character.money` includes VOLAURA crystals (+50)
5. Verify: `character.social` boosted by communication score
6. Complete an in-game event
7. Verify: `POST /api/character/events` logged to `character_events` table

**Expected result:** Character starts with higher baseline stats than a user with no VOLAURA assessments.

---

## Phase 2 (Sprint E4): Cloud Save

After Phase 1 is working, wire the full cloud save:
- `lifesim.save_games` table in Supabase (see ADR-006)
- `save_to_cloud()` → Supabase REST POST to `lifesim.save_games`
- `load_from_cloud()` → Supabase REST GET, restore full game state
- This enables multi-device play and protects against local save loss

---

*Last updated: Sprint E1, 2026-03-29*
*Agent audit confirmed: no HTTP client exists, must build from scratch*
