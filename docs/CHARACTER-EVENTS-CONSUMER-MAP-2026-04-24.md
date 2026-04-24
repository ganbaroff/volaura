# Character Events Consumer Map

Date: 2026-04-24
Author: Atlas (CTO forensic pass — code-backed, no narrative)
Status: Living document — update when consumers gain proven code receipts

---

## What this file is

For each ecosystem event type: producer, declared consumers, actual proven code consumers,
idempotency state, replay path, and current proof status.

Proof levels used:
  proven     = server-side code that reads this event type and reacts
  partial    = code exists but reaction is indirect (snapshot read, not event-driven)
  declared   = comment in code says "consumed by X" — no matching read code found
  missing    = not even declared

---

## Events emitted by VOLAURA

### assessment_completed

Producer: apps/api/app/services/ecosystem_events.py::emit_assessment_completed
Trigger: POST /api/assessment/complete/{session_id} — line 1286 in assessment.py
Schema version: 1
Payload: competency_slug, competency_score, items_answered, energy_level, stop_reason, gaming_flags
Idempotency: fire-and-forget, no deduplication key in character_events
Replay path: side_effects["ecosystem_events"] tracked in assessment_completion_jobs — if missed,
  reconciler retry will re-emit on next /complete call

Consumer map:
  MindShift     declared   comment in ecosystem_events.py: "adapts coaching path based on competency + score"
                           actual mechanism: MindShift CAN poll GET /api/character/events to catch up
                           no server-side code in this repo that pushes assessment_completed to MindShift directly
                           cross_product_bridge.py pushes crystal_earned + skill_verified, NOT assessment_completed
  Life Simulator declared   comment: "triggers character stat update"
                           lifesim.py comment (line 148): "Future iteration: aggregate from character_events"
                           meaning: LifeSim does NOT yet consume this event server-side
  Atlas          declared   comment: "updates agent context for next user interaction"
                           no code receipt for this
  BrandedBy      missing    not declared as consumer of assessment_completed anywhere

Honest proof status: DECLARED ONLY — no downstream code reacts to this event type server-side

---

### aura_updated

Producer: apps/api/app/services/ecosystem_events.py::emit_aura_updated
Trigger: POST /api/assessment/complete — line 1343 in assessment.py, only when aura_updated=True and slug set
Schema version: 1
Payload: total_score, badge_tier, competency_scores, elite_status, percentile_rank
Idempotency: fire-and-forget, no deduplication key
Replay path: side_effects["aura_events"] tracked in assessment_completion_jobs

Consumer map:
  send-notification edge function    partial   handles type="aura_updated" in NotificationPayload
                                               but this is invoked explicitly by assessment router via email path
                                               NOT a polling consumer of character_events table
  Life Simulator                     declared  comment: "updates character base stats from competency_scores"
                                               actual stat mapping exists in lifesim.py (apply_stat_boosts_from_verified_skills)
                                               but it's a pure function called on demand, not triggered by event
  BrandedBy                          partial   refresh_personality calls get_character_state RPC which reads AURA
                                               this is a snapshot read, not a reaction to aura_updated event
  Atlas                              declared  comment: "refreshes agent's knowledge of user capability profile"
                                               no code receipt

Honest proof status: PARTIALLY DECLARED — notification side exists but via explicit call, not event polling.
No server-side code loops on aura_updated from character_events.

---

### badge_tier_changed

Producer: apps/api/app/services/ecosystem_events.py::emit_badge_tier_changed
Trigger: POST /api/assessment/complete — line 1353 in assessment.py, only when old_tier != new_tier
Schema version: 1
Payload: old_tier, new_tier, total_score
Idempotency: skips if old_tier == new_tier — safe but no deduplication key in character_events
Replay path: side_effects["aura_events"] same block as aura_updated

Consumer map:
  BrandedBy       declared  comment: "unlocks 'Verified Professional' content templates at Silver+"
                            no code receipt that reads badge_tier_changed from character_events
  Life Simulator  declared  comment: "triggers character visual upgrade animation"
                            no code receipt
  Atlas           declared  comment: "agent congratulates user on next interaction"
                            no code receipt

Honest proof status: DECLARED ONLY — nothing in this codebase reacts to badge_tier_changed server-side

---

## Events emitted by Life Simulator

### lifesim_choice

Producer: apps/api/app/services/lifesim.py / routers/lifesim.py
Consumers: None declared. Event is written for ecosystem audit trail. Not consumed by other products.
Proof status: WRITE-ONLY

### lifesim_crystal_spent

Producer: apps/api/app/routers/lifesim.py
Consumers: game_crystal_ledger RPC handles the actual deduction. character_events is audit trail only.
Proof status: WRITE-ONLY (audit)

---

## Events emitted by BrandedBy

### brandedby_crystal_spent

Producer: apps/api/app/routers/brandedby.py — line 379 (queue skip audit)
Consumers: None — audit trail only
Proof status: WRITE-ONLY (audit)

---

## The polling contract (the real consumer pattern today)

The actual cross-product consumption pattern is NOT event-driven reactions.
It is snapshot reads and polling:

  GET /api/character/events (apps/api/app/routers/character.py line 317)
    Reads character_events for a user, ordered by created_at desc
    MindShift can call this to catch up missed events
    This is the MindShift fallback path documented in cross_product_bridge.py comment

  RPC get_character_state
    BrandedBy refresh_personality calls this (brandedby.py line 201)
    LifeSim stat functions use verified_skills list derived from this
    This is a snapshot, not event-driven

So the organism's actual consumption pattern is:
  VOLAURA writes events → bus accumulates → downstream polls snapshot OR polls event list
  No downstream product has a server-side loop that fires on specific event types

---

## What is missing for a real organism

1. A server-side listener per event type per downstream product, OR
   a scheduled reconciler that processes unhandled character_events per product

2. A "processed" marker or cursor per (product, event_id) so events are not double-applied

3. Tests of the form: emit event → verify downstream state changed → verify idempotent on replay

---

## Gap summary

Event                 | Producer | MindShift | LifeSim | BrandedBy | Atlas
assessment_completed  | proven   | declared  | declared | missing   | declared
aura_updated          | proven   | partial   | declared | partial   | declared
badge_tier_changed    | proven   | missing   | declared | declared  | declared

Producer side is proven. Consumer side is mostly declared intent.
The bus is real. The metabolism is not yet fully real.
