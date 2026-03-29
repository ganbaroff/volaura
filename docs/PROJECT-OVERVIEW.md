# VOLAURA ECOSYSTEM — Full Project Overview

**Version:** 1.0 | **Written:** 2026-03-29 Sprint E1 | **Owner:** CTO

> This is the living description of what we are building and why.
> Update after every sprint that changes direction. Never let it go stale.

---

## What Is This?

**VOLAURA** is a Verified Professional Talent Platform — the rational assessment layer in a 5-product ecosystem designed to make skills legible, life playable, and talent findable.

**The one-sentence pitch:**
"Prove your skills. Earn your AURA. Get found by top organizations — and watch your real-life achievements shape a game character."

---

## The Five Products

| Product | What It Does | Stack | Completion |
|---------|-------------|-------|-----------|
| **VOLAURA** | Verified skills, AURA score, org search | Next.js 14 + FastAPI + Supabase | ~85% |
| **MindShift** | ADHD-first productivity, focus timer, Mochi AI | React 19 + Vite + Supabase | ~92% PWA |
| **Life Simulator** | RPG game — your real achievements = character progression | Godot 4.4 + GDScript | ~65% game / 0% API |
| **BrandedBy** | AI video twin — your face, your verified story | React 19 + Cloudflare Workers | ~15% |
| **ZEUS** | Autonomous agent framework (local desktop control) | Python + CrewAI + ChromaDB | ~70% desktop |

**Shared infrastructure:**
- One Supabase project (schemas: `public`, `mindshift`, `lifesim`, `brandedby`)
- One FastAPI monolith on Railway (`apps/api/`)
- One auth system (`auth.users`) — login once, access everything
- One `character_events` table — all products write here, Life Simulator reads here

---

## The Ecosystem Logic (Brain Architecture)

Each product maps to a function in the human brain — Ramachandran's neuroscience framework:

```
VOLAURA (cortex)          → rational assessment, verification, judgment
MindShift (basal ganglia) → habits, streaks, dopamine loops
Life Simulator (limbic)   → emotions, play, identity narrative
BrandedBy (mirror neurons)→ social signaling, professional presence
ZEUS (cerebellum)         → autonomous execution, pattern completion

character_state (thalamus)→ central router — filters and distributes signals
                            from all products to all products
```

The `character_state` is NOT just storage. It routes. It filters.
A burnout signal from MindShift should NOT directly reduce Life Simulator health —
it should be interpreted, weighted, and expressed appropriately per product context.

---

## VOLAURA: What It Is Now

**Positioning (locked Sprint E1, 2026-03-29):**
- NOT a volunteer platform (removed from all copy)
- NOT a LinkedIn competitor (don't frame it that way)
- YES a "verified talent platform" / "RPG where real skills matter"

**For users:** Take adaptive assessments → earn AURA score (0-100) → get Bronze/Silver/Gold/Platinum badge → be discovered by orgs searching by competency.

**For organizations:** Search talent by verified skill and score, not unverified CVs. Send intro requests. Rate event participation. Build a verified talent pool.

**AURA Score weights (FINAL — do not change):**

| Competency | Weight |
|-----------|--------|
| Communication | 20% |
| Reliability | 15% |
| English Proficiency | 15% |
| Leadership | 15% |
| Event Performance | 10% |
| Tech Literacy | 10% |
| Adaptability | 10% |
| Empathy & Safeguarding | 5% |

**Badge tiers:** Platinum ≥90 | Gold ≥75 | Silver ≥60 | Bronze ≥40 | None <40

---

## MindShift: What It Brings

**The ADHD-first productivity PWA.** 22,795 lines, deployed and live.

**Why it matters for the ecosystem:**
MindShift knows things VOLAURA doesn't:
- When your energy peaks (daily rhythm from `energy_logs`)
- Whether you actually follow through (streak + show-up rate)
- What kind of thinker you are (psychotype: achiever/planner/explorer/connector)
- How close you are to burnout (Burnout Radar: 4-signal formula)

These are AURA inputs that no assessment can capture — they come from 30+ days of behavior.

**Integration contract (Sprint E2):**

| MindShift sends | VOLAURA receives | character_state event |
|----------------|-----------------|----------------------|
| `focus_session` completed | `reliability` signal | `xp_earned` + stat `focus` |
| `streak >= 7` | `reliability` boost | `buff_applied: consistency` |
| `psychotype` derived | persona enrichment | `profile_updated` |
| `burnout_score > 70` | adaptation hint | `state_changed: health` |
| `energy_level` on session | timing signal | `vital_logged: energy` |

**ADHD rules (non-negotiable, carry forward to VOLAURA UX):**
- No red color anywhere (RSD trigger)
- No punishment for absence — warm re-entry always
- Positive crystal sinks only — "get more" not "avoid losing"
- Max 3 decisions at once (cognitive load limit)
- Variable ratio XP for dopamine bridge

---

## Life Simulator: The Game Layer

**Godot 4.4 RPG — your real skills become game stats.**

**Current state:** 65-70% complete game logic. 4 P0 bugs (unplayable without fix). 0% API integration.

**Character model (8 stats):**
Strength (STR), Intelligence (INT), Wisdom (WIS), Charisma (CHA), Endurance (END), Agility (AGI), Luck (LCK), Creativity (CRE)

**How VOLAURA connects:**
```
VOLAURA assessment completed → POST /api/character/events
  {
    event_type: "skill_verified",
    payload: { competency_slug: "communication", score: 78, badge: "gold" },
    source_product: "volaura"
  }

→ character_state materializes:
  communication score → CHA stat boost
  reliability score   → END stat boost
  tech_literacy       → INT stat boost
  leadership          → STR stat boost
```

**Crystal economy:**
- VOLAURA: complete each competency assessment = 50 crystals (idempotent, max 400 total)
- MindShift: focus sessions = XP → crystals (floor(xp/100))
- Life Simulator: spend crystals on premium events, cosmetics, NPC quests
- NEVER pay-to-avoid-harm. Always a free path. ADHD-first.

**Crystal sinks (positive only):**
- Premium life events (150) — special storylines, travel, education
- Celebrity NPC quests (150) — mentorship, unique rewards
- Cosmetics (50-300) — appearance, home decoration
- Time capsule (100) — save your character at peak moment
- Gift to friend (50-200) — social bonding

**P0 bugs to fix before Sprint E3 (Godot):**
1. `event.check_requirements()` → should be `can_trigger()` → CRASH
2. EventModal never shows — auto-selects choice 0 → player never interacts
3. `game_over.tscn` is empty file → death leads nowhere
4. `character.full_name` doesn't exist → has `first_name + last_name`

---

## The character_state API

**The central nervous system of the ecosystem.**

**Tables (in VOLAURA's Supabase `public` schema):**

```sql
character_events        — event log (all products write here)
  id, user_id, event_type, payload JSONB, source_product, created_at

game_crystal_ledger     — crystal transaction log
  id, user_id, amount, source, reference_id, created_at

game_character_rewards  — idempotent reward tracking (one per competency)
  user_id, skill_slug, crystals, claimed, PRIMARY KEY (user_id, skill_slug)
```

**API endpoints (Sprint E1):**
```
POST /api/character/events          — write an event (any product)
GET  /api/character/state           — computed character state (materialized)
GET  /api/character/crystals        — crystal balance
POST /api/character/rewards/claim   — claim assessment reward (idempotent)
```

**Event types:**
- `crystal_earned` — crystals from assessment, focus, or purchase
- `skill_verified` — VOLAURA competency completed with score
- `xp_earned` — MindShift focus session XP
- `stat_changed` — any stat modification with source
- `buff_applied` — temporary buff (streak, flow state)
- `vital_logged` — energy, health, burnout data point

---

## Integration Architecture (Decided Sprint E1)

**Decision:** Shared Supabase project, per-product schemas. Single auth.

| Decision | Chosen | Alternative rejected | Why |
|----------|--------|---------------------|-----|
| Auth | Shared `auth.users` | Separate Supabase per product | Free SSO, no JWT translation |
| Database | Shared project, schemas per product | Separate DBs | Single connection string, RLS per schema |
| Backend | Shared FastAPI monolith on Railway | Microservices | Solo founder can't maintain 4 backends |
| character_state | Event-sourced (`character_events` log + materialized view) | Single mutable JSON | No race conditions, full audit trail, archivable |
| Life Sim cloud save | Supabase `lifesim.save_games` | Local file | Cloud save = progression persistence |

**Migration path for MindShift (Sprint E2):**
1. Add `mindshift` schema to VOLAURA's Supabase
2. Export MindShift's current Supabase tables to migration SQL
3. Add `user_id` foreign key to `auth.users`
4. MindShift auth → redirect to shared Supabase auth endpoint
5. MindShift calls `POST /api/character/events` on focus completion

---

## The User Journey (End-to-End)

**From signup to game character fully reflecting your real skills:**

```
1. Register on VOLAURA (or MindShift — shared auth)
2. Onboarding → pick first competency
3. Take adaptive assessment (10-15 questions, AI-evaluated)
4. Earn AURA score + badge
5. POST /api/character/events: { event_type: "skill_verified", ... }
   → POST /api/character/rewards/claim: 50 crystals awarded
6. Open Life Simulator → game logs in via same Supabase JWT
7. GET /api/character/state → character's CHA stat boosted from communication score
8. Crystal balance shows in game UI
9. Spend crystals on premium life events
10. Focus 30 min on MindShift → XP earned → POST /api/character/events: xp_earned
11. Character INT stat grows from focus minutes
12. Organization finds user on VOLAURA, sends intro request
13. User's verified skills, AURA badge, and psychotype inform the match
```

This is the loop. Real life → platform verification → game world → back to real life.

---

## What We Are NOT Building

- A jobs board (VOLAURA connects talent and orgs at skill level, not job-application level)
- A LinkedIn clone (we verify skills, we don't just list them)
- A gamification layer on top of CVs (the game IS the engagement mechanic, not a reward for using a boring app)
- A pay-to-win game (crystals are earned through real skill, free path always exists)
- A standalone game (Life Simulator needs VOLAURA data to have meaning)

---

## Open Risks

| Risk | Severity | Owner | Status |
|------|---------|-------|--------|
| MindShift auth migration breaks existing users | HIGH | CTO | Not started — Sprint E2 |
| Life Sim P0 bugs make Sprint E3 take 2x expected | HIGH | CTO | Documented, awaiting sprint |
| character_state API latency at scale (10K events/user) | MEDIUM | CTO | Archival strategy designed, not built |
| BrandedBy still 15% — SIMA + video pipeline unstarted | HIGH | CEO | Parallel track B |
| Crystal economy EU compliance (free path validation) | MEDIUM | CTO | Designed in master plan |

---

## Sprint Roadmap

| Sprint | Focus | Key deliverable |
|--------|-------|----------------|
| E1 (now) | Ecosystem Identity | Rebrand done, character_state API, assessment→crystal bridge |
| E2 | MindShift Integration | Shared auth, focus→character events, MindShift calls API |
| E3 | Life Sim Playable | Fix 4 P0 bugs, wire CloudSaveManager to API |
| E4 | Life Sim Cloud | Full crystal economy visible in game, verified skills as abilities |
| E5 | SSO + Cross-product UX | One login, all products, smooth handoffs |
| A2+ | VOLAURA features | Notifications, event management, org rating |

---

*Last updated: Sprint E1, 2026-03-29*
*Next review: Sprint E2 start*
