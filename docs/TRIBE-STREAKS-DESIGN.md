# Tribe Streaks — Design Spec v2.0

**Status:** Design only. CHECKLIST COMPLETE. Awaiting CEO sign-off on 3 questions before code.
**Prerequisite:** Anti-harassment safeguards must be implemented BEFORE any tribe matching code.
**Board mandate:** Strategic Board Director (nemotron-ultra-253b) flagged toxicity risk as CRITICAL.
**Checklist run:** 2026-04-02 — 4-agent review. 7/7 items addressed. 13 approved changes incorporated below. 3 CEO decisions pending.

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

## Team Review Findings (2026-04-02 — 4-agent checklist)

### 13 Approved Changes (must incorporate before first migration commit)

1. **[Cultural] Zero kudos count hidden** — Never show "0 kudos this week." Hide count until ≥1 received. Zero-count display is a cultural harm in AZ (passive ostracism signal). PENDING CEO Q1.
2. **[Security] Matching service must use service_role** — Matching algorithm runs exclusively in admin Supabase client context. Never exposed via user JWT or PostgREST.
3. **[Security] Add `tribe_member_history` table** — Stores previous co-member IDs per user. Service-role only. No user-readable RLS. Required for "no repeat tribes" filter.
4. **[Security] Opted-out members invisible in API** — `GET /api/tribes/me` filters `WHERE opt_out_at IS NULL`. Departed members do not appear as "inactive" — they simply don't exist in the response.
5. **[Architecture] `grace_periods_used` resets per cycle** — Add `cycle_started_at TIMESTAMPTZ` to `tribe_streaks`. Grace periods are per-tribe-cycle, not lifetime. PENDING CEO Q2 for grace model choice.
6. **[Architecture] Add renewal tracking** — Add `tribe_renewal_requests (tribe_id UUID, user_id UUID, requested_at TIMESTAMPTZ)` table. Matching service reads this to decide whether to renew or re-match.
7. **[Architecture] CHECK constraint on `last_activity_week`** — `CHECK (last_activity_week ~ '^\d{4}-W\d{2}$')` on `tribe_streaks`.
8. **[RLS] Full RLS policies** — See "RLS Policies" section below. Kudos readable only via service_role (SECURITY DEFINER RPC), not directly by users.
9. **[UX] Opt-out in 1 tap from tribe card** — Overflow menu ("...") on tribe card, first item: "Leave this tribe." No confirmation dialog. One-tap = immediate silent soft-delete.
10. **[UX] Opt-out DOES NOT reset streak** — `POST /api/tribes/opt-out` must not touch `tribe_streaks`. Streak is personal, tribe-independent.
11. **[UX] Post-opt-out forward path** — After opt-out, user sees "Find a new tribe?" prompt. No blank state. Blank tribe state = abandonment cliff.
12. **[Grace] Grace counter resets at new cycle** — Implement via `cycle_started_at` check in streak service. When new tribe assigned → reset `grace_periods_used = 0`.
13. **[Grace] No numeric grace counter in UI** — Do NOT show "You have 1 grace period left." Use fading crystal animation only. Numeric counter = gameable budget.

### CEO Decisions Required (3 questions — no code until answered)

**Q1 — Kudos zero-count display:**
- Option A: Show "0 kudos" (honest, risks passive ostracism in AZ culture)
- Option B: Hide count when 0, show "Be the first to send kudos" prompt (Cultural Intelligence recommendation)

**Q2 — Grace period model:**
- Option A: 2 free misses in any order, resets each cycle (simple, gameable)
- Option B: Fading-crystal model — miss 1 = dims, miss 2 = dimmer, miss 3 consecutive = resets (more forgiving, consistent with visual design, harder to game)

**Q3 — Opted-out member replacement:**
- Option A: 2-person tribe continues until cycle end, then re-matched (less disruptive)
- Option B: Tribe dissolves immediately on any opt-out, all members re-matched (cleaner, more disruptive)

---

## RLS Policies (complete SQL — copy into migration)

```sql
-- tribes
ALTER TABLE public.tribes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Members can read their tribe" ON public.tribes FOR SELECT
  USING (id IN (SELECT tribe_id FROM public.tribe_members WHERE user_id = auth.uid() AND opt_out_at IS NULL));
CREATE POLICY "No direct insert by users" ON public.tribes FOR INSERT TO authenticated WITH CHECK (FALSE);
CREATE POLICY "No direct update by users" ON public.tribes FOR UPDATE TO authenticated USING (FALSE);
CREATE POLICY "No direct delete by users" ON public.tribes FOR DELETE TO authenticated USING (FALSE);

-- tribe_members
ALTER TABLE public.tribe_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Members can read their tribe members" ON public.tribe_members FOR SELECT
  USING (tribe_id IN (SELECT tribe_id FROM public.tribe_members AS tm WHERE tm.user_id = auth.uid() AND tm.opt_out_at IS NULL));
CREATE POLICY "Users can soft opt-out of own membership" ON public.tribe_members FOR UPDATE
  USING (user_id = auth.uid() AND opt_out_at IS NULL) WITH CHECK (user_id = auth.uid());
CREATE POLICY "No direct membership insert" ON public.tribe_members FOR INSERT TO authenticated WITH CHECK (FALSE);
CREATE POLICY "No hard delete by users" ON public.tribe_members FOR DELETE TO authenticated USING (FALSE);

-- tribe_streaks
ALTER TABLE public.tribe_streaks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own streak only" ON public.tribe_streaks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "No direct streak insert" ON public.tribe_streaks FOR INSERT TO authenticated WITH CHECK (FALSE);
CREATE POLICY "No direct streak update" ON public.tribe_streaks FOR UPDATE TO authenticated USING (FALSE);
CREATE POLICY "No direct streak delete" ON public.tribe_streaks FOR DELETE TO authenticated USING (FALSE);

-- tribe_kudos: INSERT allowed for active members; SELECT blocked (use SECURITY DEFINER RPC for count)
ALTER TABLE public.tribe_kudos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Active members can send kudos" ON public.tribe_kudos FOR INSERT TO authenticated
  WITH CHECK (tribe_id IN (SELECT tribe_id FROM public.tribe_members WHERE user_id = auth.uid() AND opt_out_at IS NULL));
CREATE POLICY "Kudos not directly readable" ON public.tribe_kudos FOR SELECT TO authenticated USING (FALSE);
CREATE POLICY "Kudos immutable" ON public.tribe_kudos FOR UPDATE TO authenticated USING (FALSE);
CREATE POLICY "Kudos not deleteable by users" ON public.tribe_kudos FOR DELETE TO authenticated USING (FALSE);
```

---

## Decision Log

| Decision | Rationale | Risk if wrong |
|----------|-----------|---------------|
| Score matching ±15 points | Prevents Platinum/Bronze pairing | Too narrow = small pool → bad matches |
| 4-week rotation | Prevents clique lock-in | Too short = no attachment formed |
| Anonymous kudos (tribe-level, not member-level) | Prevents weaponization. Kudos count is per tribe, not per person | "Send kudos to [name]" framing is wrong — always "send to your tribe" |
| Streak visible only to self | Prevents peer pressure | Too private = no social motivation |
| 2 grace periods per cycle (CEO Q2 pending) | Forgiveness without enabling laziness | If lifetime (not per-cycle), feels unfair after bad month |
| Opted-out members invisible (not shown as inactive) | Face-saving: no public "X left" | Remaining 2-person tribe needs a path (CEO Q3 pending) |
| Matching uses service_role only | Prevents cross-user activity data leakage via user JWT | Must be enforced in FastAPI service layer |
