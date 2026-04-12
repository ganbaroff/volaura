# Life Simulator — Game Design Document

**Status:** 85% architecture complete, 3 P0 bugs block gameplay
**Engine:** Godot 4.4
**Location:** `C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026`
**Integration:** VOLAURA API (`/api/character/state`, `/api/character/events`, `/api/character/crystals`)

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

## P0 Bugs (block ALL gameplay)

### P0-1: check_requirements() doesn't exist
**File:** `scripts/controllers/event_queue_controller.gd:202`
**Fix:** Change `event.check_requirements(character)` → `event.can_trigger(character)`
**Impact:** Events don't generate, game hangs

### P0-2: EventModal auto-selects choice 0
**File:** `scripts/controllers/event_queue_controller.gd:128`
**Fix:** Remove auto `_make_choice(0)`, connect modal to wait for user input
**Impact:** Player can't make choices

### P0-3: GameOver scene empty
**File:** `scenes/ui/game_over.tscn`
**Fix:** Add stats display (age, money, social, intelligence, happiness), death reason, restart/menu buttons
**Impact:** Game ends with blank screen

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

### During Gameplay (every 5 game-years)
```
1. POST /api/character/events → log game milestones
2. GET /api/character/crystals → refresh crystal balance
```

### On Game Over
```
1. POST /api/character/events → final stats, death reason, total years
2. Show "Play again" + "Take VOLAURA assessment to boost next life"
```

---

## Crystal Economy in Life Sim

### Earn (from VOLAURA/MindShift)
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

1. Fix 3 P0 bugs (50 minutes total)
2. Add 20 event JSONs (diverse life events)
3. Verify VOLAURA API integration (crystal sync)
4. Add crystal spend options in-game
5. GameOver → "Take assessment" CTA
6. Rooms feature (Phase 3)
