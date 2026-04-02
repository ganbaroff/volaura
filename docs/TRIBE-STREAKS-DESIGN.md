# Tribe Streaks — Design Spec v1.0

**Status:** Design only. NOT ready to implement.
**Prerequisite:** Anti-harassment safeguards must be implemented BEFORE any tribe matching code.
**Board mandate:** Strategic Board Director (nemotron-ultra-253b) flagged toxicity risk as CRITICAL.

---

## What It Is

3-person accountability circles. Each person in the tribe:
- Sees their tribe members' assessment activity (not scores — activity only)
- Can send a Kudos (anonymous, private count only — not public leaderboard)
- Accumulates a tribe streak for consecutive weeks where ALL members complete ≥1 assessment

The streak "fades" if the chain breaks (Kimi design: koi tokens that fade). Visual: a dimming crystal.

---

## Why It Works (Board analysis)

**Behavioral mechanism (Strategic Board Director):**
Leverages collectivist psychology by anchoring progress to small-group accountability.
Social commitment (not competition) drives retention. Fading tokens create urgency without
individual shame, aligning with "rising together" cultural values.

**Cultural fit (CPO Board + Cultural Intelligence Agent):**
- Group success = psychological safety in AZ/CIS
- No public ranking = no anxiety, no comparison
- Private kudos = recognition without performance pressure

---

## Anti-Harassment Safeguards (REQUIRED before any code)

### Risk 1: Toxic peer matching
If tribes form randomly, mismatched peers create guilt spirals.
A user who falls behind feels shame from their tribe. A user who dominates feels resentment.

**Mitigation required:**
- Match tribes by: (a) similar AURA score range ±15 points, (b) similar assessment frequency (active vs casual)
- NEVER match a Platinum user with a Bronze user
- Algorithm: weighted similarity score, not random

### Risk 2: Exclusionary cliques (CPO Board finding)
If tribe membership is permanent, "castes" form. High performers self-select into elite circles.
New users can never break in.

**Mitigation required:**
- Tribe membership expires after 4 weeks — then tribes can REQUEST to renew together (opt-in)
- Default after 4 weeks: new matching run (fresh start) UNLESS all 3 members opt to renew
- Forced rotation removed per Cultural Intelligence Agent finding: AZ culture = trust requires familiarity; forced cycling creates perpetual cold-start problem
- User can opt out of a tribe without penalty (no public "I left" notification)
- Grace period: first 2 broken streaks don't count (forgiveness mechanic)

### Risk 3: Harassment via kudos
Even anonymous kudos can be weaponized (0 kudos to someone = passive ostracism).

**Mitigation required:**
- Kudos are opt-in, not opt-out (you choose to send, not required)
- No "kudos received" count visible to the sender
- "Kudos" label — not "likes" or "points"

### Risk 4: Peer pressure on streak
If streak is visible to all members, it creates "I can't let my tribe down" anxiety.

**Mitigation required:**
- Streak counter visible only to YOU, not to tribe members
- Tribe members see only: "active this week / inactive this week" (binary, no details)
- No push notifications about tribe member inactivity (pull only — they check when they want)

---

## Database Schema (proposed — NOT migrated yet)

```sql
-- Tribes (3-person groups)
CREATE TABLE tribes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,  -- 4 weeks from creation
    status TEXT NOT NULL DEFAULT 'active'  -- active | expired | dissolved
);

-- Tribe memberships
CREATE TABLE tribe_members (
    tribe_id UUID REFERENCES tribes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    opt_out_at TIMESTAMPTZ,  -- soft opt-out, no notification to others
    PRIMARY KEY (tribe_id, user_id)
);
-- RLS: user can only read their own tribe

-- Tribe streaks (per-user, not per-tribe)
CREATE TABLE tribe_streaks (
    user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_activity_week TEXT,  -- YYYY-Www format (ISO week)
    grace_periods_used INT NOT NULL DEFAULT 0  -- max 2 before streak resets
);
-- RLS: user can only read their own streak

-- Kudos ledger (anonymous, no sender visible to recipient)
CREATE TABLE tribe_kudos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tribe_id UUID REFERENCES tribes(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- NOTE: no sender_id stored — truly anonymous. Recipient sees count only.
);
-- RLS: tribe members can insert; NO select on sender identity
```

---

## API Endpoints (proposed)

```
GET  /api/tribes/me           — my current tribe + members (activity status only)
GET  /api/tribes/me/streak    — my streak count + longest
POST /api/tribes/me/kudos     — send anonymous kudos to my tribe
POST /api/tribes/opt-out      — leave current tribe silently
```

---

## Matching Algorithm (pseudocode)

```python
def match_tribe(user_id: str, pool: list[User]) -> list[str]:
    """Returns 2 other user IDs to form a 3-person tribe."""
    user = get_user(user_id)

    candidates = [
        u for u in pool
        if abs(u.aura_score - user.aura_score) <= 15  # score proximity
        and u.assessments_last_30d > 0  # recently active
        and u.id not in user.previous_tribe_members  # no repeat tribes
    ]

    # Score similarity (higher = more similar = better match)
    candidates.sort(key=lambda u: -similarity_score(user, u))

    return [candidates[0].id, candidates[1].id] if len(candidates) >= 2 else []
```

---

## Implementation Checklist (BEFORE writing any frontend)

- [ ] Anti-harassment design reviewed by Cultural Intelligence Agent
- [ ] Matching algorithm reviewed by Security Agent (privacy: what does "activity status" reveal?)
- [ ] DB schema reviewed by Architecture Agent
- [ ] RLS policies written for all 4 tables
- [ ] Opt-out flow UX reviewed by Behavioral Nudge Engine (is opt-out low-friction enough?)
- [ ] Grace period mechanic user-tested (does 2 grace periods feel fair?)
- [ ] CEO sign-off on tribe visibility model (what exactly can tribe members see about each other?)

---

## Sprint Estimate

- DB schema + migrations: 0.5 day
- Matching service (Python): 1 day
- Streak tracking (cron or trigger): 0.5 day
- API endpoints (4): 1 day
- Frontend (tribe card + streak crystal): 1.5 days
- Tests: 0.5 day
**Total: ~5 days. Do NOT start until checklist above is 100% checked.**

---

## Decision Log

| Decision | Rationale | Risk if wrong |
|----------|-----------|---------------|
| Score matching ±15 points | Prevents Platinum/Bronze pairing | Too narrow = small pool → bad matches |
| 4-week rotation | Prevents clique lock-in | Too short = no attachment formed |
| Anonymous kudos | Prevents weaponization | Too anonymous = no meaning |
| Streak visible only to self | Prevents peer pressure | Too private = no social motivation |
| 2 grace periods | Forgiveness without enabling laziness | Might need tuning |
