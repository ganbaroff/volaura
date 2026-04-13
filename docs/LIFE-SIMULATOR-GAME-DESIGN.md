# Life Simulator — Game Design Document

**Status:** 85% architecture complete, 3 P0 bugs block gameplay
**Engine:** Godot 4.4
**Location:** `C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026`
**Integration:** VOLAURA API (`/api/character/state`, `/api/character/events`, `/api/character/crystals`)

**Cross-references:** [[LIFE-SIMULATOR-INTEGRATION-SPEC]] | [[ECOSYSTEM-CONSTITUTION]] | [[MINDSHIFT-INTEGRATION-SPEC]] | [[VISION-FULL]] | [[ECOSYSTEM-MAP]] | [[MONETIZATION-ROADMAP]] | [[adr/ADR-006-ecosystem-architecture]] | [[research/ecosystem-design-research]] | [[research/ECOSYSTEM-REDESIGN-BRIEF-2026-04-14]] | [[adr/ADR-005-aura-scoring]]

---

## Core Game Loop

```
Character Creation → Year Cycle → Events → Choices → Consequences → Stat Changes → Age → Repeat
                                                                         ↓
                                                              VOLAURA competencies boost stats
                                                              Crystals add to money
                                                              MindShift streaks slow aging
```

### Year Cycle (1 year = ~30 seconds real time)
1. Time advances 1 year
2. Random events generated from pool (filtered by age, stats, career)
3. Player makes choices (2-4 options per event)
4. Consequences applied to stats
5. Milestone check (age 18: college, 25: career, 30: marriage, etc.)
6. VOLAURA sync: pull latest competency scores + crystals
7. Stats decay/grow based on activity

### Character Stats (0-100)
| Stat | Affects | VOLAURA Boost |
|------|---------|---------------|
| Health | Lifespan, energy | — |
| Happiness | Event availability, relationships | empathy(0.05) + event_perf(0.05) + leadership(0.03) |
| Energy | Actions per year, work quality | reliability(0.05) + adaptability(0.05) |
| Intelligence | Career options, education | tech_literacy(0.10) + english(0.05) |
| Social | Relationships, networking | communication(0.10) + leadership(0.05) |
| Money | Purchases, lifestyle | crystals from VOLAURA (capped 9999) |

### Death Conditions
- Health reaches 0
- Age reaches 100 (natural death)
- Specific event chains (risky choices)

---

## P0 Bugs (FIXED — 2026-04-13)

### P0-1: check_requirements() doesn't exist ✅
**Fixed in:** Session 95 audit — already corrected to `can_trigger(character)`

### P0-2: EventModal auto-selects choice 0 ✅
**Fixed:** Removed `_make_choice(0)` from `process_next_event()`. Added `resolve_current_event()` public method. Connected `event_started` signal to `gameplay_controller._on_event_started()` which shows EventModal. Milestone events converted from raw dicts to EventChoice objects.

### P0-3: GameOver scene empty ✅
**Fixed:** Full game_over.gd script + rebuilt game_over.tscn with stats grid (age, money, health, happiness, intelligence, social), death reason text, restart + menu buttons. Stats passed via `Globals.game_over_data`.

---

## Event System

### Event Types
| Type | Trigger | Example |
|------|---------|---------|
| Random | Each year, probability-weighted | "Car breaks down", "Friend invites to party" |
| Milestone | At specific ages | "Graduate college", "First job", "Marriage proposal" |
| Career | Based on job + stats | "Promotion offered", "Fired for low performance" |
| VOLAURA | Based on AURA scores | "Org recruits you as Gold-level specialist" |
| Crystal | Based on balance | "Unlock premium training course" |

### Event JSON Format (in `data/`)
```json
{
  "id": "career_promotion_01",
  "title": "Promotion Opportunity",
  "description": "Your manager notices your consistent performance...",
  "min_age": 25,
  "max_age": 55,
  "requirements": {"intelligence": 40, "social": 30},
  "choices": [
    {
      "text": "Accept the promotion",
      "consequences": {"money": 20, "energy": -10, "happiness": 15}
    },
    {
      "text": "Decline — focus on personal life",
      "consequences": {"happiness": 10, "social": 5, "money": -5}
    }
  ]
}
```

---

## VOLAURA Integration Points

### On Game Start
```
1. Check JWT token (from login or stored)
2. GET /api/character/state → {crystal_balance, verified_skills, character_stats}
3. Apply competency boosts to character stats
4. Add crystal_balance to character.money (capped 9999)
```

### During Gameplay (every 5 game-years) ✅ Implemented
```
1. POST /api/character/events → log game milestones
2. GET /api/character/crystals → refresh crystal balance
TimeController._advance_year() triggers api_client.load_crystals() every 5 years.
```

### On Game Over
```
1. POST /api/character/events → final stats, death reason, total years
2. Show "Play again" + "Take VOLAURA assessment to boost next life"
```

---

## Crystal Economy in Life Sim (governed by [[ECOSYSTEM-CONSTITUTION]] Crystal Laws 1-8)

### Earn (from VOLAURA/[[MINDSHIFT-INTEGRATION-SPEC|MindShift]])
- Assessment completion: +50-200 crystals
- Focus session: +10-30 crystals
- Badge earned: +100 crystals

### Spend (in Life Sim)
- Premium training course: 50 crystals (intelligence +10)
- Social event ticket: 30 crystals (social +5, happiness +5)
- Health insurance: 100 crystals (health decay halved for 10 years)
- Career coach: 75 crystals (next promotion guaranteed)

---

## Rooms ($10,000 Entry — Future)

Premium multiplayer rooms where verified professionals gather:
- Entry requires: Platinum badge OR 10,000 crystals
- Features: live chat, shared events, collaborative challenges
- Revenue: subscription per room access
- Implementation: Phase 3+ (after single-player is solid)

---

## Implementation Priority

1. ~~Fix 3 P0 bugs~~ ✅ (all 3 fixed 2026-04-15)
2. ~~Add 20 event JSONs~~ ✅ (53 events: 47 base + 6 VOLAURA integration)
3. ~~VOLAURA API integration~~ ✅ (VolauraAPIClient + Character.apply_volaura_boosts)
4. ~~Add crystal spend options in-game~~ ✅ (6 VOLAURA events with crystal spend)
5. ~~GameOver → "Take assessment" CTA~~ ✅ (VOLAURA button + AURA level display + deep link)
6. Rooms feature (Phase 3)
