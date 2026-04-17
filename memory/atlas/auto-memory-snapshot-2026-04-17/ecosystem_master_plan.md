---
name: Ecosystem Master Plan — March 27, 2026
description: Complete integration plan for Volaura + MindShift + Life Simulator + BrandedBy + ZEUS
type: project
last_updated: 2026-03-27
---

# MASTER INTEGRATION PLAN v2.0 (Updated with Session Insights)

## NEW INSIGHTS (2026-03-27 evening session)

### 1. SIMA Verification = Deep Moat (BrandedBy)
Celebrities verify identity via Azerbaijan's state SIMA system.
Platform becomes legal consent infrastructure. No global competitor can replicate.
SIMA access CONFIRMED available.

### 2. Influencer Network = Chicken-and-Egg Solved
CEO has warm connections: Tunzale Aghayeva, Azer Aydemir Kim, Farid Pasdashunas,
Vusal Yusifli, Yuspace, Tedroid, infonews. Not cold outreach.

### 3. Brain Architecture Mapping (from Ramachandran neuroscience analysis)
| Brain Function | Ecosystem Component |
|---|---|
| Thalamus (central hub) | character_state JSON |
| Cortex (rational assessment) | Volaura AURA |
| Limbic system (emotions) | Life Simulator |
| Basal ganglia (habits) | MindFocus streaks |
| Dopamine system (reward) | Crystals |
| Mirror neurons (social) | Hiring Layer |
| Synesthesia (cross-modal) | Integration layer |
| Peak shift (signal amplification) | Gamification of real achievements |
| Conscious→Unconscious | Learning through play |

### 4. ADHD-First Design Principle (NON-NEGOTIABLE)
CEO has ADHD. Platform must use POSITIVE reinforcement only.
NO pay-to-avoid-harm mechanics. NO anxiety loops. NO punishment for absence.
Crystals = "make life richer", NOT "avoid death".
Free survival path ALWAYS exists.

### 5. Hiring Layer = LinkedIn Killer (Stealth)
After game play, users hire each other based on:
- Known behavior (observed in game)
- Verified skills (Volaura AURA)
- Organic connections (built through play)
NEVER say "LinkedIn competitor". Say "RPG where real skills matter."

### 6. Local Storage First (BrandedBy)
Phase 1: Files on user PC (zero cost). Phase 2: Sell subscriptions to fund servers.

## 5 Architecture Decisions

1. **Shared Supabase** — one project, schemas per product: `public` (Volaura), `mindshift`, `lifesim`, `brandedby`. Shared `auth.users` = SSO for free.
2. **Shared FastAPI monolith** — extend `apps/api/` with routers per product. Single Railway deploy. Solo founder can't maintain 4 backends.
3. **Event-sourced character_state** — `character_events` table + materialized view. Multi-platform writes without race conditions. 90-day archival solves 1MB limit.
4. **Shared Supabase Auth** — JWT `user_metadata.products[]` claims. Each product checks own claim. One login = all products.
5. **Migrate BrandedBy to FastAPI** — kill Cloudflare Workers + D1. BrandedBy is 15% complete, migration costs 2 days vs permanent separate stack.

## Complete Bug/Fix List (verified from code)

### Life Simulator (P0 = crash)
1. P0: `event_queue_controller.gd:202` — `check_requirements` → should be `can_trigger`
2. P0: `event_queue_controller.gd:128` — auto-selects choice 0, player never sees EventModal
3. P0: `game_over.tscn` — empty file, death leads nowhere
4. P0: `game_loop_controller.gd:91` — `character.full_name` doesn't exist
5. P1: `event_queue_controller.gd:54` — EventLoader child never freed (memory leak)
6. P1: `event.gd:83` — non-repeatable events can NEVER fire (should check trigger_count > 0)
7. P1: `time_controller.gd:13` — 1 sec = 1 year = death in 2 min. Should be 30 sec = 1 year
8. P1: `idle_controller.gd:200` — upgrade multiplier linear instead of compound
9. P1: `main_game_ui.gd:69-82` — no null checks on UI nodes
10. P2: `cloud_save_manager.gd:14` — CLOUD_ENABLED is const, can't toggle

### MindShift
11. P1: No API layer — all client-side Supabase calls, zero REST endpoints
12. P1: No shared auth — siloed Supabase Auth
13. P1: Burnout score client-only — not persisted to DB
14. P2: 30-day task purge loses verification data
15. P2: XP variable-ratio scheduling needs normalization for crystal conversion
16. P2: Psychotype cold-start (needs 10+ sessions)

### BrandedBy
17. P0: AI video generation = 0%
18. P0: Stripe card never tokenized (no Stripe Elements)
19. P0: No Stripe webhook handler (security hole)
20. P1: Celebrity data corrupted (Cyrillic → ?????)
21. P1: "FaceMorphingDemo" is CSS slideshow
22. P1: "AI Assistant" is random string selection
23. P2: D1 lock-in (needs Supabase migration)

### ZEUS
24. P1: localhost-only (no cloud access)
25. P1: No API key auth on OpenAI-compat endpoint
26. P1: No Godot bridge (ZeusBridge is desktop controller only)
27. P2: Hardcoded local paths
28. P2: Supabase integration basic (no RLS, no auth tokens)

### Integration Layer
29. P0: character_state API doesn't exist
30. P0: No shared auth across products
31. P0: No crystal economy implementation
32. P1: No event-sourcing for cross-product writes
33. P1: No history archival strategy
34. P2: No SSO UI flow

## Data Mapping: MindShift → character_state

| MindShift | character_state | Life Sim Stat | Conversion |
|---|---|---|---|
| psychotype | personality.archetype | Growth curves | achiever=STR, explorer=INT, connector=CHA, planner=WIS |
| energyLevel (1-5) | vitals.energy | Stamina 0-100 | (energy/5)*100 |
| xpTotal | economy.crystals | Crystals | floor(xp/100) |
| streak | buffs.consistency | Age slowdown | ≥7d=0.9x, ≥30d=0.75x |
| burnoutScore (0-100) | vitals.health | Health (inv) | 100-burnout |
| focusMinutesTotal | stats.focus | INT XP | focus*2 |
| tasksCompletedTotal | stats.productivity | STR XP | tasks*5 |

## Crystal Economy

**Sources:** Stripe purchase ($0.99=100, $4.99=600, $9.99=1400), Volaura assessment (50 flat, each competency once, max 400), Daily login (5/day, 15 on day 7), Milestones (10-25).
**Sinks:** Life extension at 90+ (200=+5yrs), Premium NPC (150), Cosmetics (50-300), 2x income boost 24h (100).
**Anti-farming:** Each Volaura competency rewards once only. 7-day cooldown. Daily cap 15. No transfers. Completion-based NOT score-based.
**EU compliance:** Every paid item has free alternative. Free survival path always exists.

## Supabase Tables (new)

```sql
-- Shared character state (event-sourced)
CREATE TABLE public.character_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    event_type TEXT NOT NULL, -- 'crystal_earned','skill_verified','xp_earned','stat_changed'
    payload JSONB NOT NULL DEFAULT '{}', -- includes _schema_version
    source_product TEXT NOT NULL, -- 'volaura','mindshift','lifesim','brandedby'
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_char_events_user ON public.character_events(user_id, created_at DESC);

-- Crystal ledger
CREATE TABLE public.game_crystal_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    amount INT NOT NULL,
    source TEXT NOT NULL,
    reference_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Volaura rewards (idempotent)
CREATE TABLE public.game_character_rewards (
    user_id UUID REFERENCES auth.users(id),
    skill_slug TEXT NOT NULL,
    crystals INT DEFAULT 50,
    claimed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (user_id, skill_slug)
);

-- Life Simulator cloud saves
CREATE TABLE lifesim.save_games (
    user_id UUID REFERENCES auth.users(id),
    slot INT NOT NULL DEFAULT 0,
    character_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, slot)
);

-- BrandedBy (migrated from D1)
CREATE TABLE brandedby.celebrities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    bio TEXT,
    category TEXT,
    image_url TEXT,
    game_available BOOLEAN DEFAULT FALSE,
    sprite_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## SELF-CRITIQUE v2.0 → v3.0 (10 issues found and fixed)
1. SIMA missing from sprints → Added Sprint 0B
2. BrandedBy too late (Week 5) → Moved to parallel Track B starting Week 1
3. "Life extension" violates ADHD → Replaced with positive crystal sinks
4. Sprint 1/2 dependency → Resequenced
5. Hiring Layer missing → Added Sprint 11
6. ZEUS premature → Moved to Sprint 10 (after cloud API exists)
7. Brain mapping decorative → character_state redesigned as thalamus
8. No mobile strategy → Added Sprint 8 mobile unification
9. No parallelism → 3 tracks now
10. No demo content → Sprint 0B includes demo video creation

## Crystal Economy v3 (ADHD-safe + Queue Gamification)
**Sinks (POSITIVE only — no pay-to-avoid-harm):**
- Premium experiences (150 crystals): unlock special life events, travel, education
- Celebrity NPC quests (150): unique storylines, mentorship
- Cosmetics (50-300): character appearance, home decoration
- Time capsule (100): save a memory of your character at peak moment
- Gift to friend (50-200): social bonding mechanic
- ~~Life extension at 90+~~ REMOVED — violates ADHD-first principle

**Queue Skip mechanic (v3 addition — Yusif's design, 2026-03-27):**
All compute-heavy features use a priority queue. Free = wait. Crystals = skip.
This is the PRIMARY crystal sink — concrete, immediate, universally understood.
| Feature | Free wait | Crystal skip | Pro |
|---------|-----------|-------------|-----|
| Voice avatar (Kokoro/Bark) | 48h | 10 crystals → 1h | immediate |
| Video avatar (SadTalker) | 72h | 25 crystals → 2h | immediate |
| AI portrait animation | 24h | 5 crystals → now | immediate |
| Detailed AI report | 12h | 8 crystals → now | immediate |
UX: "Your voice is queued — ready in 48h. Skip for 10 crystals?"
Re-engagement: notification when ready = 80%+ open rate.
Психология: не "заплати чтобы не страдать" — а "заплати чтобы получить быстрее". ADHD-safe.

**TTS Stack (updated after research — 2026-03-27):**
- Phase 1: Kokoro TTS (82M params, CPU, Apache 2.0, deploy on Railway) → $0
  OR Google Cloud TTS free tier (4M chars/month = 8K responses free)
- Phase 2: Bark (Suno) via Replicate → $0.01/response, supports [laughs][coughs][sighs]
- Phase 3: Parler-TTS on Modal.com → $0.003/response, voice described in natural language
- ElevenLabs: NOT in plan (7 responses/day on $22/month — 70x less than alternatives)

## 12-Sprint Plan v3.0 (28% → 85%) — 3 PARALLEL TRACKS

### TRACK A: Core Integration (CTO leads)

**Sprint A0 (Week 1): character_state as Thalamus**
- Design character_state with routing/filtering (not just storage)
- Migrations: character_events, crystal_ledger, game_character_rewards
- FastAPI: POST/GET /api/character/events, /api/character/state
- character_state materialized view with priority-based refresh
- Acceptance: POST event → GET state returns computed view <50ms

**Sprint A1 (Week 2): Volaura → Crystal Bridge**
- Assessment completion → crystal_earned event (50 per competency, max 400)
- Anti-farming: idempotent rewards table, one claim per competency
- Acceptance: Complete assessment → crystals visible in GET /state

**Sprint A2 (Week 3): MindShift → Shared Auth + character_state**
- MindShift schema in Supabase with RLS
- Replace localStorage with Supabase (tasks, sessions, streaks)
- Focus completion → character event (XP + stat change)
- Shared Supabase Auth (login on Volaura domain)
- Acceptance: MindShift login = Volaura login, focus session → character event

**Sprint A3 (Week 4): Life Simulator Bug Fixes**
- Fix all 10 P0-P2 bugs (file:line references in bug list above)
- Aging speed: 30 sec = 1 game year
- Wire EventModal to EventQueue properly
- Build GameOver → Life History screen
- Acceptance: Birth-to-death playthrough without crashes

**Sprint A4 (Week 5): Life Simulator → Cloud**
- GDScript HTTP client for character_state API
- cloud_save_manager: CLOUD_ENABLED=true
- Crystal balance display from character_state
- Load Volaura verified skills as character abilities
- Acceptance: Save/load cloud, crystals from Volaura visible in game

**Sprint A5 (Week 6): Cross-product SSO**
- JWT user_metadata.products[] claims
- Shared /auth/login UI on volaura.app
- MindShift + BrandedBy redirect to shared login
- Acceptance: One login → all 4 products accessible

### TRACK B: BrandedBy (Parallel Chat — starts Week 1)

**Sprint B0 (Week 1): Landing + SIMA MVP**
- Register brandedby.com (or .ai)
- Next.js 14 landing page on Vercel
- SIMA verification hero section (explain the moat)
- Influencer onboarding form (email, social, interest)
- Contact 3-5 influencers from warm list
- Acceptance: Landing live, 3+ influencer responses

**Sprint B1 (Week 2): Demo Content + Celebrity Onboarding**
- Sign 2-3 Tier 3 influencers (near-zero cost)
- Create 5 demo videos (HeyGen API manual pipeline)
- Demo reel on landing page
- Acceptance: 5 demo videos embedded on site

**Sprint B2 (Week 3): Stripe + Self-Serve**
- Migrate API to shared FastAPI + Supabase (kill D1/Cloudflare)
- Fix celebrity data (Cyrillic corruption)
- Stripe Checkout Sessions for $199 Spotlight
- Stripe webhook with idempotency
- Acceptance: User can pay $199, order recorded, webhook fires

**Sprint B3 (Week 4): Video Pipeline Automation**
- Research: HeyGen API vs Kling vs Runway
- Pipeline: script → prompt enhance (Claude) → video (HeyGen) → branding (FFmpeg) → delivery
- Content moderation on script input
- Mandatory AI disclosure watermark
- Acceptance: Order → video URL in <10 min

**Sprint B4 (Week 5): Celebrity NPC Bridge**
- Flag celebrities as game_available in Supabase
- Life Simulator: load celebrity data as NPC
- NPC gives quest → rewards crystals
- Acceptance: 1 celebrity NPC in game, quest → crystals

### TRACK C: Game Economy + Polish (starts Week 6)

**Sprint C0 (Week 6): PERMA Crystal Economy**
- Map each Volaura competency to PERMA dimension
- Crystal shop in Life Simulator (ALL positive sinks)
- Free alternative for every paid item
- Daily login streak (5/day, 15 on day 7)
- Acceptance: Crystal economy functional, EU compliant

**Sprint C1 (Week 7): Mobile Unification**
- Life Simulator: Godot HTML5 export for web
- MindShift PWA: ensure works on same devices
- Consistent auth flow across mobile/web
- Deep links: game → Volaura assessment → back to game
- Acceptance: Full flow works on Android Chrome

**Sprint C2 (Week 8): ZEUS Cloud API**
- ZEUS: replace localhost with cloud-accessible FastAPI endpoint
- API key auth on OpenAI-compat endpoint
- Godot bridge via cloud API (not localhost WebSocket)
- Acceptance: ZEUS controls game state via cloud API <200ms

**Sprint C3 (Week 9): Hiring Layer MVP**
- Profile page showing: verified skills (Volaura) + game stats + connections
- "I'd work with this person" button (simple endorsement)
- Discovery: browse users by verified skill
- Acceptance: User can find and endorse another user based on verified skills

**Sprint C4 (Week 10): History Archival + Performance**
- pg_cron: archive character_events >90 days to cold storage
- Materialized view refresh optimization
- Load test: 10K events per user, GET /state <100ms
- Acceptance: Performance verified at scale

**Sprint C5 (Week 11): E2E Integration Demo**
- Full journey: register → assess → earn crystals → play game → focus → XP → meet user → endorse
- Fix all cross-product bugs
- 2-min demo video for investors
- Acceptance: Complete journey recorded, demo ready

## Progress Forecast v3.0 (3 parallel tracks)
| Week | Track A | Track B | Track C | Ecosystem % |
|---|---|---|---|---|
| 1 | A0: character_state | B0: Landing + SIMA | — | 32% |
| 2 | A1: Volaura bridge | B1: Demo content | — | 38% |
| 3 | A2: MindShift sync | B2: Stripe | — | 45% |
| 4 | A3: Life Sim bugs | B3: Video pipeline | — | 52% |
| 5 | A4: Life Sim cloud | B4: Celebrity NPC | — | 60% |
| 6 | A5: SSO | — | C0: Crystal economy | 66% |
| 7 | — | — | C1: Mobile unification | 70% |
| 8 | — | — | C2: ZEUS cloud | 74% |
| 9 | — | — | C3: Hiring Layer MVP | 78% |
| 10 | — | — | C4: Performance | 82% |
| 11 | — | — | C5: E2E demo | 85% |

## Neuroscience-Informed Design Principles (from Ramachandran analysis)
1. **Thalamus pattern**: character_state filters and routes — not all events matter to all products
2. **Peak shift**: gamification amplifies real achievements (badge → visual effect → crystals → NPC reaction)
3. **Conscious→Unconscious**: first assessments are deliberate, after 2 weeks they feel automatic
4. **Synesthesia**: one action triggers responses in ALL connected products simultaneously
5. **Savant discovery**: AURA can reveal skills the user didn't know they had
6. **No Capgras**: emotional layer (Life Sim) must ALWAYS be connected to rational layer (Volaura) — never let them diverge
