# ADR-006: Ecosystem Integration Architecture

**Date:** 2026-03-29
**Status:** ACCEPTED
**Sprint:** E1
**Deciders:** CTO (Claude), CEO (Yusif)
**Related:** [[ADR-001-system-architecture]], [[ADR-002-database-schema]], [[ADR-005-aura-scoring]]
**Governed by:** [[../ECOSYSTEM-CONSTITUTION]] | **Products:** [[../MINDSHIFT-INTEGRATION-SPEC]] | [[../LIFE-SIMULATOR-INTEGRATION-SPEC]] | [[../AI-TWIN-CONCEPT]] | [[../ECOSYSTEM-MAP]]

> 2026-04-21 runtime note: this ADR contains historical target decisions. For current implemented state and active gaps, use `docs/CURRENT-VS-TARGET-ARCHITECTURE-2026-04-21.md` as canonical.

---

## Context

VOLAURA is one product in a 5-product ecosystem. The other products (MindShift, Life Simulator, BrandedBy, ZEUS) currently have zero integration with each other. Users must manage separate accounts, separate auth, and derive no benefit from using multiple products.

The goal of this ADR is to lock the foundational architecture decisions that enable cross-product integration — specifically: how do products share identity, how do they communicate, and how does the Life Simulator become a game that reflects real achievements from VOLAURA and MindShift?

---

## Decisions

### Decision 1: Shared Supabase Project

**Chosen:** One Supabase project, per-product schemas (`public`, `mindshift`, `lifesim`, `brandedby`). Shared `auth.users`.

**Alternatives considered:**
- **Separate Supabase per product** — rejected because: no SSO without custom JWT bridge, 4x management overhead, cross-product queries require HTTP calls.
- **Separate auth + JWT federation** — rejected because: 2-3 weeks of implementation for zero user benefit.

**Consequences:**
- Free SSO: one email+password logs into all products
- JWT `user_metadata.products[]` claims — each product checks its own claim
- RLS policies per schema prevent cross-product data leakage
- MindShift migration required (currently on its own Supabase project) — Sprint E2

---

### Decision 2: Shared FastAPI Monolith

**Chosen:** Extend `apps/api/` with routers per product. Single Railway deploy.

**Alternatives considered:**
- **Microservices** — rejected: solo founder, $50/mo budget, separate deploys = 4x failure surfaces
- **Supabase Edge Functions for everything** — rejected: cold starts, no Python, can't use google-genai SDK, no Pydantic v2

**Consequences:**
- Character API lives in `apps/api/app/routers/character.py`
- All products call `https://api.volaura.app/api/character/...`
- Life Simulator (Godot) makes HTTP calls to this URL

---

### Decision 3: Event-Sourced character_state

**Chosen:** `character_events` table (append-only log) + `character_state` materialized view. No mutable JSON blob.

**Alternatives considered:**
- **Single mutable JSON blob** (`character_states` table with one row per user) — rejected: race conditions when two products write simultaneously, no audit trail, 1MB Supabase column limit hit at ~2K events
- **PostgreSQL LISTEN/NOTIFY** — rejected: doesn't work with Supabase client connections

**Schema:**
```sql
CREATE TABLE public.character_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    event_type TEXT NOT NULL,
    -- event_type ENUM: crystal_earned | skill_verified | xp_earned |
    --                   stat_changed | buff_applied | vital_logged
    payload JSONB NOT NULL DEFAULT '{}',
    -- payload always includes: _schema_version (INT), for forward compat
    source_product TEXT NOT NULL,
    -- source_product ENUM: volaura | mindshift | lifesim | brandedby | zeus
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX idx_char_events_user_time
    ON public.character_events(user_id, created_at DESC);
```

**Materialized view:** `character_state` computes current stats by folding events. Refreshed on read (lazy) or by pg_cron every 5 minutes. GET /character/state returns computed view, not raw events.

**Archival:** Events older than 90 days → `public.character_events_archive`. pg_cron job. Keeps active table fast.

---

### Decision 4: Crystal Economy — Idempotent Rewards

**Chosen:** `game_character_rewards` table with `PRIMARY KEY (user_id, skill_slug)` guarantees idempotency. Cannot claim same assessment reward twice, regardless of API retries.

```sql
CREATE TABLE public.game_character_rewards (
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    skill_slug TEXT NOT NULL,
    crystals INT NOT NULL DEFAULT 50,
    claimed BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, skill_slug)
);
```

**Crystal economy rules:**
- VOLAURA assessment: 50 crystals per competency, once per user per competency (max 400)
- MindShift focus: floor(xp_earned / 100) crystals, daily cap 15
- Anti-farming: 7-day cooldown enforced in `game_crystal_ledger`
- EU compliance: every paid crystal sink has a free alternative path

---

### Decision 5: Life Simulator Integration via HTTP

**Chosen:** Life Simulator (Godot) calls `POST /api/character/events` via Godot's `HTTPRequest` node. Auth via Supabase JWT stored in `cloud_save_manager.gd`.

**Consequences:**
- CloudSaveManager must store JWT from auth flow
- `CLOUD_ENABLED = true` in `cloud_save_manager.gd`
- Character stats boosted by verified skills on game load:
  - `communication` score → `social` stat (Life Sim actual field name)
  - `reliability` score → `energy` stat
  - `tech_literacy` → `intelligence` stat
  - `leadership` → `social` + `happiness` stats
  Note: Life Sim character.gd uses: health, money, happiness, energy, intelligence, social
  (not STR/INT/WIS/CHA — those were design names, not code names)
- Crystal balance displayed from `GET /api/character/crystals`

---

## VOLAURA → Crystal Bridge (Sprint E1 implementation)

When a VOLAURA assessment session completes with a score:

1. `POST /api/assessment/submit_answer` processes last answer
2. Session marked `completed`
3. Internal claim triggered server-side inside the submit_answer handler —
   see `apps/api/app/services/assessment/rewards.py::claim_reward` (no
   separate public HTTP endpoint). Called with `{ user_id, skill_slug, session_id }`.
4. If not yet claimed → insert `game_character_rewards` row + insert `character_events` row (`crystal_earned`, 50 crystals) + insert `game_crystal_ledger` row
5. If already claimed → silent no-op (unique constraint on `game_character_rewards`), idempotent, no double reward

**Implementation note (2026-04-14):** earlier drafts of this ADR showed step 3
as a standalone `POST /api/character/rewards/claim` HTTP endpoint. The shipped
implementation folds the claim into the assessment submit handler — there is
no public rewards/claim endpoint. LifeSim and MindShift never need to call it;
VOLAURA emits the rewards internally when an assessment completes.

---

## MindShift Integration Contract (Sprint E2)

MindShift will call these endpoints after Sprint E2 migration:

```
POST /api/character/events
Authorization: Bearer <supabase_jwt>
{
  "event_type": "xp_earned",
  "payload": {
    "_schema_version": 1,
    "xp": 150,
    "focus_minutes": 30,
    "phase": "flow",
    "energy_before": 3,
    "energy_after": 4,
    "psychotype": "achiever"
  },
  "source_product": "mindshift"
}
```

```
POST /api/character/events
{
  "event_type": "vital_logged",
  "payload": {
    "_schema_version": 1,
    "burnout_score": 45,
    "streak": 12,
    "energy_level": 4
  },
  "source_product": "mindshift"
}
```

MindShift receives in return:
- `GET /api/character/state` — AURA badge tier + score (display in ProgressPage)
- `GET /api/character/crystals` — crystal balance (display in MindShift)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| MindShift migration loses user data | Export + import + verify before cutover. Rollback = re-point to old Supabase URL |
| Life Sim JWT expiry in-game | Refresh token flow in CloudSaveManager before expiry |
| character_state stale during active session | Accept eventual consistency (max 5 min lag). Flag in GET response: `freshness: "cached" | "live"` |
| Crystal double-claim on network retry | Idempotency key in `game_character_rewards` PRIMARY KEY |
| Rate limit on `/api/character/events` | 100 req/min per user. MindShift batches events per focus session |

---

## Supersedes

No previous ADR. This is the first cross-product architecture decision.

## Next Review

Sprint E2 — after MindShift integration is implemented. Adjust if MindShift migration reveals blockers.
