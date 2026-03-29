# MindShift ↔ VOLAURA Integration Spec

**Version:** 1.0 | **Sprint:** E1 | **Date:** 2026-03-29
**Status:** READY FOR E2 IMPLEMENTATION
**Owner:** CTO

> This document defines the exact API contract between MindShift and VOLAURA.
> MindShift team implements calls. VOLAURA team provides the endpoints.
> Both teams use this as the source of truth.

---

## Why This Integration Exists

MindShift knows behavioral signals that VOLAURA cannot capture through assessment alone:
- Real consistency (streak data — 30 days of actual follow-through)
- Daily energy patterns (when does this person peak?)
- Psychotype (achiever / planner / explorer / connector)
- Burnout proximity (4-signal formula)

VOLAURA knows verification that MindShift cannot provide:
- Formal skill assessment (ISO 10667-2 aligned methodology)
- AURA badge tier (Bronze / Silver / Gold / Platinum)
- Org discovery status (is this person in the talent pool?)

Together they form the complete picture. Neither alone is sufficient.

---

## Integration Architecture

```
MindShift (React 19 + Vite + Supabase)
    │
    │  [Sprint E2] Migrate to shared Supabase auth
    │  MindShift calls VOLAURA FastAPI directly
    │
    ▼
VOLAURA FastAPI (Railway) — apps/api/
    │
    ├── POST /api/character/events       ← MindShift writes here
    ├── GET  /api/character/state        ← MindShift reads AURA badge
    └── GET  /api/character/crystals     ← MindShift shows crystal balance
    │
    ▼
Supabase (shared project)
    ├── auth.users                       ← ONE user ID for both products
    ├── public.character_events          ← all events from all products
    ├── public.game_crystal_ledger       ← crystal transactions
    └── mindshift.*                      ← MindShift's own tables (migrated E2)
```

---

## Phase 1: Quick Wins (no auth migration needed)

These can be implemented WITHOUT the Supabase migration, using VOLAURA's user ID passed from MindShift's existing session.

### 1.1 AURA Badge Display in MindShift ProgressPage

**What:** Show user's VOLAURA AURA badge in MindShift ProgressPage alongside XP level.

**MindShift implementation:**
```typescript
// In MindShift ProgressPage — after user logs in
async function fetchAuraBadge(volauraToken: string) {
  const res = await fetch("https://api.volaura.app/api/character/state", {
    headers: { Authorization: `Bearer ${volauraToken}` }
  });
  if (!res.ok) return null;
  const data = await res.json();
  // data.data = { crystal_balance, xp_total, verified_skills, character_stats }
  return data.data;
}
```

**Response shape (GET /api/character/state):**
```json
{
  "data": {
    "user_id": "uuid",
    "crystal_balance": 150,
    "xp_total": 3200,
    "verified_skills": [
      {
        "skill_slug": "communication",
        "aura_score": 78.5,
        "badge_tier": "gold"
      }
    ],
    "character_stats": {
      "CHA": 45,
      "INT": 30,
      "END": 25
    },
    "login_streak": 7,
    "event_count": 12,
    "last_event_at": "2026-03-29T08:00:00Z",
    "computed_at": "2026-03-29T08:05:00Z"
  }
}
```

**UI suggestion:** In MindShift ProgressPage, below XP level:
```
[AURA Badge]  Communication: 🥇 Gold (78/100)
              Leadership: 🥈 Silver (64/100)
              [See full profile on VOLAURA →]
```

---

### 1.2 Crystal Balance Display

**What:** Show crystal balance in MindShift (earned from VOLAURA assessments).

**Endpoint:** `GET /api/character/crystals`

**Response:**
```json
{
  "data": {
    "balance": 150,
    "earned_lifetime": 350,
    "spent_lifetime": 200,
    "pending_rewards": []
  }
}
```

---

## Phase 2: Full Integration (requires Supabase auth migration — Sprint E2)

### 2.1 Supabase Auth Migration

**MindShift's current state:** Has its own Supabase project at `[redacted].supabase.co`

**Migration plan:**
1. Export MindShift's `auth.users` → seed into VOLAURA's Supabase (preserving emails)
2. Export MindShift's tables (tasks, focus_sessions, profiles, energy_logs, user_behavior) → add to VOLAURA Supabase as `mindshift.*` schema
3. Update MindShift's Supabase client URL to VOLAURA's project URL
4. Update RLS policies on MindShift tables: `auth.uid()` stays the same (same JWT pattern)
5. Test: login on MindShift → same user_id as VOLAURA

**Critical:** MindShift's `profiles.id` references `auth.users.id`. After migration, user IDs must match between products. If emails match → Supabase assigns same `auth.users` ID. This is safe.

---

### 2.2 Focus Session → character_event

**Trigger:** User completes a focus session in MindShift (PostSessionFlow component)

**MindShift calls:**
```typescript
// In MindShift's PostSessionFlow.tsx or useFocusSession hook
// After session saved to Supabase:
await fetch("https://api.volaura.app/api/character/events", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${supabaseSession.access_token}`, // shared JWT
  },
  body: JSON.stringify({
    event_type: "xp_earned",
    payload: {
      _schema_version: 1,
      xp: Math.floor(session.duration_minutes * 5), // 5 XP per minute
      focus_minutes: session.duration_minutes,
      phase: session.final_phase, // "struggle" | "release" | "flow"
      energy_before: session.energy_before,
      energy_after: session.energy_after,
      psychotype: userBehavior.psychotype,
    },
    source_product: "mindshift",
  }),
});
```

**Crystal conversion:** `floor(xp_earned / 100)` crystals awarded per session. Daily cap: 15 crystals from MindShift source.

**Life Simulator effect:**
- Focus minutes → INT stat boost (`focus_minutes * 2` = INT XP)
- Tasks completed → STR stat boost
- Psychotype maps: achiever→STR, explorer→INT, connector→CHA, planner→WIS

---

### 2.3 Streak → Reliability Signal

**Trigger:** Daily login in MindShift, after streak update

**MindShift calls:**
```typescript
// Only when streak changes (once per day max)
await fetch("https://api.volaura.app/api/character/events", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    event_type: "buff_applied",
    payload: {
      _schema_version: 1,
      buff_type: "consistency",
      streak_days: currentStreak,
      // 7+ days = 0.9x age progression rate in Life Sim
      // 30+ days = 0.75x age progression rate
    },
    source_product: "mindshift",
  }),
});
```

---

### 2.4 Vital Signs → character_state

**Trigger:** Energy level logged in MindShift (EnergyPicker component)

**MindShift calls:**
```typescript
await fetch("https://api.volaura.app/api/character/events", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    event_type: "vital_logged",
    payload: {
      _schema_version: 1,
      energy_level: energyValue, // 1-5
      burnout_score: burnoutScore, // 0-100
    },
    source_product: "mindshift",
  }),
});
```

---

### 2.5 Psychotype → AURA Profile Enrichment

**Trigger:** Once psychotype is derived in MindShift (after 10+ sessions)

**MindShift calls:**
```typescript
// One-time after psychotype first derived, and on each psychotype change
await fetch("https://api.volaura.app/api/character/events", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    event_type: "stat_changed",
    payload: {
      _schema_version: 1,
      stat: "psychotype",
      value: psychotype, // "achiever" | "planner" | "explorer" | "connector"
      source: "mindshift_derivation",
    },
    source_product: "mindshift",
  }),
});
```

**Life Simulator character stat mapping:**
```
achiever  → STR stat as primary growth axis
planner   → WIS stat as primary growth axis
explorer  → INT stat as primary growth axis
connector → CHA stat as primary growth axis
```

---

## Rate Limits

All MindShift calls to VOLAURA API:
- POST /api/character/events: **30 req/minute** per user
- GET /api/character/state: **60 req/minute** per user
- Recommendation: batch focus events per session (one call at end, not per minute)
- Recommendation: cache GET /state for 5 minutes in MindShift

---

## Error Handling

| HTTP Code | Code | MindShift action |
|-----------|------|-----------------|
| 401 | UNAUTHORIZED | User not logged in or token expired — skip silently |
| 409 | REWARD_ALREADY_CLAIMED | Normal — idempotent, ignore |
| 422 | DAILY_CRYSTAL_CAP_REACHED | Normal — skip, try tomorrow |
| 422 | INVALID_CRYSTAL_AMOUNT | Bug in MindShift — log error |
| 500 | EVENT_STORE_FAILED | Retry once after 3s, then log |

All calls should be **best-effort**: never block MindShift UX for VOLAURA API failures.

---

## What MindShift Receives Back

From VOLAURA API, MindShift displays in ProgressPage:

1. **AURA Badge tier** — "You've earned Gold in Communication on VOLAURA"
2. **Crystal balance** — "You have 150 crystals — use them in Life Simulator"
3. **Deep link** — "See your full AURA profile →" (opens VOLAURA profile page)
4. **Find focus partners** — `GET /api/discovery/volunteers?match_by=aura_skills` — find users with complementary skills for Focus Rooms

---

## ADHD-Safe Integration Rules

These rules from MindShift's guardrails apply to ALL integration touchpoints:

1. **No red** — crystal balance shows in teal/gold, never red
2. **No punishment framing** — "Earn more crystals" not "You lost crystals"
3. **No mandatory** — VOLAURA API failure silently skipped, never blocks MindShift session
4. **Positive reinforcement only** — badge display = reward moment, not comparison
5. **No streak pressure** — "You've maintained a 7-day streak 🎉" not "Don't break your streak!"

---

## Sprint E2 Implementation Checklist

**VOLAURA side:**
- [ ] Add `mindshift` schema to Supabase migration
- [ ] Add `GET /api/character/crystals` endpoint (if not already exists)
- [ ] Add CORS origin for MindShift's Vercel URL
- [ ] Add `mindshift` to accepted `source_product` enum in schemas
- [ ] Rate limit for MindShift source: 30 events/minute

**MindShift side:**
- [ ] Add env var: `VITE_VOLAURA_API_URL=https://api.volaura.app`
- [ ] Create `src/shared/lib/volaura-bridge.ts` — typed API client
- [ ] Migrate Supabase project URL to shared project
- [ ] PostSessionFlow: call bridge after session saved
- [ ] ProgressPage: fetch and display AURA badge
- [ ] Daily login: emit streak event if streak changed
- [ ] EnergyPicker: emit vital_logged on energy selection

---

*Last updated: Sprint E1, 2026-03-29*
*Contact: CTO (Claude) — update this doc when API changes*
