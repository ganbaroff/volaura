# Integration Contract Lock (Bridge/Event Payloads)

**Date:** 2026-04-21  
**Purpose:** pin current runtime contracts to reduce doc/code drift until full generated-client rollout.

## Character Events Contract (Current Runtime)

- Endpoint: `POST /api/character/events`
- Schema owner: `apps/api/app/schemas/character.py::CharacterEventCreate`
- Allowed `source_product`:
  - `volaura`
  - `mindshift`
  - `lifesim`
  - `brandedby`
  - `eventshift`
- Allowed `event_type`:
  - `crystal_earned`, `crystal_spent`, `skill_verified`, `skill_unverified`
  - `xp_earned`, `stat_changed`, `login_streak`, `milestone_reached`
  - `buff_applied`, `vital_logged`
- Runtime limit: `30/minute` (`apps/api/app/routers/character.py`)

## Character State Read Contracts

- `GET /api/character/state`
  - response owner: `CharacterStateOut`
  - runtime limit: `60/minute`
- `GET /api/character/crystals`
  - response owner: `CrystalBalanceOut`
  - runtime limit: `60/minute`

## Compliance Contracts

- Art.20 portability:
  - `GET /api/auth/export`
  - owner: `apps/api/app/routers/auth.py`
- Art.22 formal review:
  - `GET /api/aura/human-review/decisions`
  - `POST /api/aura/human-review`
  - `GET /api/aura/human-review`
  - owner: `apps/api/app/routers/grievance.py`

## Rule

Any spec/example that diverges from these contracts is non-canonical until updated with code + tests.

