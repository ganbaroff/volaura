# Cowork Research: Life Simulator Game Logic + ZEUS→ATLAS Rename

**Author:** Cowork (Claude Opus, Research Advisor)
**Date:** 2026-04-12
**For:** Atlas (CTO) — CEO Mandates #1 and #2

---

## 1. LIFE SIMULATOR — Game Logic Design

### Current State
- **Integration spec exists:** `docs/LIFE-SIMULATOR-INTEGRATION-SPEC.md` — API client, stat mapping, cloud save
- **Godot 4.4 codebase:** separate repo `life-simulator-2026`
- **Web placeholder:** `/[locale]/life` page created (Cowork Session 9)
- **Auth flow:** `volaura_login_screen.tscn/.gd` + `api_client.gd` committed (Session 92)
- **P0 bugs:** 4 blockers identified in spec (check_requirements, EventModal, game_over.tscn, full_name)

### Missing: Core Game Loop Design

The integration spec covers VOLAURA↔LifeSim data flow but NOT the game itself. CEO mandate is "develop fully." Here's the game design:

#### Core Loop (Bitlife-style, ADHD-optimized)
```
START → Choose age (18/25/30) → Year Loop:
  1. View stats dashboard (health, money, happiness, energy, intelligence, social)
  2. Choose 1 action per "turn" (turn = 1 year of life)
  3. Random event triggers (based on stats + choices)
  4. See outcome → stats update → age +1
  5. Repeat until age 80 or game over condition
```

#### Action Categories (max 6 — ADHD)
1. **Career** — Job search, work hard, ask for raise, start business
2. **Education** — Study, take course, learn language, get certification
3. **Social** — Make friends, date, volunteer, attend events
4. **Health** — Exercise, doctor visit, meditate, diet
5. **Finance** — Save, invest, buy property, gamble
6. **Adventure** — Travel, explore, take risk, random challenge

#### Event System (Variable Reward — ADHD dopamine)
- 30% chance per turn of a random event
- Events have 2-3 choices (never more — decision fatigue)
- Outcomes are WEIGHTED by stats (high intelligence → better outcomes for education events)
- Some events are VOLAURA-connected (if user has high AURA, they get "recruiter noticed you" events)

#### VOLAURA Integration Points
| VOLAURA trigger | Life Sim effect |
|-----------------|-----------------|
| User completes assessment | "New skill unlocked" event next turn |
| AURA score > 70 | "Recruiter event" pool unlocked |
| Crystal balance > 100 | Starting money bonus |
| Badge tier upgrade | Celebration event + stat boost |

#### Monetization (Crystal Economy)
- **Earn crystals:** Complete Life Sim achievements → crystals in VOLAURA
- **Spend crystals:** Buy "life perks" (second chance, stat boost, unlock premium careers)
- **Cross-product loop:** Assessment → crystals → Life Sim perks → more engagement → assessment retake

#### Floor Mechanic (ADHD — <2 min per session)
- One turn = one tap + read outcome = 30 seconds
- Player can play 1 turn and leave
- Auto-save after every turn
- Push notification: "Your character aged 1 year while you were away. See what happened?"

### Implementation Priority for Atlas
```
P0: Fix 4 existing bugs (see integration spec)
P1: Year-loop game controller (age +1, stat decay, action system)
P2: Event system (30 events minimum, 2-3 choices each)
P3: VOLAURA stat enrichment (from integration spec)
P4: Crystal economy (earn/spend between products)
P5: Cloud save (Supabase persistence)
```

---

## 2. ZEUS → ATLAS RENAME

### Scope Analysis

**Frontend (14 refs, 6 files):**
- `globals.css` — 2 refs (`--color-product-zeus`)
- `bottom-tab-bar.tsx` — 7 refs (tab item, icon, routing)
- `zeus/page.tsx` — 2 refs (ProductPlaceholder)
- `product-placeholder.tsx` — 1 ref
- `en/common.json` — 1 ref (`"zeus": "ZEUS"`)
- `az/common.json` — 1 ref (`"zeus": "ZEUS"`)

**Backend (15 refs, 4 files):**
- `zeus_gateway.py` — 4 refs (router, entire file)
- `telegram_webhook.py` — 8 refs (ZEUS gateway references)
- `video_generation_worker.py` — 2 refs
- `main.py` — 1 ref (router include)

**Docs (50+ refs):**
- Constitution, CLAUDE.md, ECOSYSTEM-MAP, various docs

### Rename Strategy (поэтапно = step by step)

**Phase 1: Frontend only (safe, no API breakage)**
- Rename `--color-product-zeus` → `--color-product-atlas`
- Rename route `/zeus` → `/atlas`
- Update BottomTabBar tab (id, label, href)
- Update i18n keys
- Keep backend unchanged for now

**Phase 2: Backend (needs deploy coordination)**
- Rename `zeus_gateway.py` → `atlas_gateway.py`
- Update all imports in `main.py`
- Update Telegram webhook references
- Update video generation worker

**Phase 3: Documentation**
- Bulk find-replace in docs/
- Update ECOSYSTEM-MAP.md
- Update Constitution references

### Risk: Telegram bot hardcodes "ZEUS" in messages
The telegram_webhook.py has 8 references. Some are in user-facing messages sent to CEO. These need careful rewrite, not just find-replace.

### Recommendation
Start Phase 1 (frontend only) immediately — zero risk. Phase 2 needs a deploy window.

---

## Atlas Action Items

1. **Life Sim P0:** Fix 4 Godot bugs before anything else
2. **Life Sim P1:** Build year-loop game controller with the 6 action categories
3. **ZEUS rename Phase 1:** Frontend rename (Cowork already created the zeus route — easy to rename)
4. **Life Sim P2:** 30 events with 2-3 choices each

These are independent tracks — Life Sim and rename can run in parallel.
