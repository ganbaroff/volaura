# First 10 Users Launch Plan
**Created:** 2026-04-13 | **By:** Cowork (Research Advisor) | **Status:** READY FOR CEO REVIEW

## Why 10 Before 5,000

WUF13 target is 5,000 users. But zero real users have completed the full journey end-to-end. Before scaling, we need 10 humans who:
1. Sign up independently (no hand-holding)
2. Complete assessment (at least 1 competency)
3. Receive AURA score (pipeline must work)
4. Share their profile link to at least 1 person
5. That person visits the public profile page

If this loop works for 10, it works for 5,000. If it breaks, we fix it before spending on acquisition.

---

## Current State (Production DB Audit, 2026-04-13)

| Metric | Count | Note |
|--------|-------|------|
| Profiles | 27 | mostly test accounts |
| Started assessment | 18 | |
| Completed | 13 | |
| Got AURA score | 8 | **5 lost (38% pipeline leak)** |
| Real users (not test) | ~3 | Yusif + 2 unknown |
| Share profile clicks | 0 | No analytics yet |

**Blockers Atlas is fixing now:**
- Pipeline leak (5 users lost their score)
- Single-competency scoring (only communication tested)
- Sentry dead (no error visibility)

---

## The 10-User Playbook

### Week 1: Fix & Verify (Atlas + Cowork)

**Atlas (backend):**
- Fix pipeline leak (Handoff 009 — P0)
- Verify Sentry gets events from Railway
- Clarify: single vs multi-competency per session

**Cowork (frontend + monitoring):**
- Public profile updated to new design (DONE)
- OG card updated to brand colors (DONE)
- Monitor DB for new completions + AURA scores

**CEO (manual test):**
- Walk through full flow yourself: logout, fresh signup, assessment, AURA page, share link
- Send share link to 2-3 trusted friends
- Report: what confused you, what broke, what felt wrong

### Week 2: Recruit 10 Beta Users

**Source:** Yusif's personal network — people who understand volunteering.
Not random. Not "anyone with a phone." People who will give honest feedback.

**Target profile:**
- Azerbaijani volunteers (WUF13, COP29, CIS Games alumni)
- Age 20-35, speak Azerbaijani or English
- Have used at least 1 professional platform (LinkedIn, Boss.az)

**Recruitment message (Telegram/WhatsApp, CEO sends personally):**

> Salam! Bir layihə üzərində işləyirəm — Volaura. Könüllülərin bacarıqlarını test edib, AURA skoru verir. Sənin fikrini bilmək istəyirəm.
> 5 dəqiqə vaxtın var? Link: volaura.app
> (Heç bir ödəniş yoxdur, sadəcə testi keç və nəticəni paylaş)

Translation: "Hi! I'm working on a project — Volaura. It tests volunteer skills and gives an AURA score. I want your opinion. Got 5 minutes? Link: volaura.app (No payment, just take the test and share the result)"

**Do NOT say:** "my startup", "we're launching", "invest in" — just "working on a project, want your opinion."

### Week 3: Measure & Learn

**Track (via Supabase SQL + PostHog if connected):**

| Metric | Target | How to measure |
|--------|--------|----------------|
| Signup rate | 8/10 invited | profiles table, created_at this week |
| Assessment start | 7/8 signups | assessment_sessions, status != null |
| Assessment complete | 5/7 starters | assessment_sessions, status = 'completed' |
| AURA score received | 5/5 completers | aura_scores, 0% leak |
| Profile shared | 3/5 scorers | UTM tracking on share links |
| Return visit (Day 7) | 2/5 | profiles last_login or analytics |

**Exit survey (Telegram DM, CEO asks personally):**
1. "Nə anladın?" (What did you understand?) — tests if value prop is clear
2. "Nə çətin idi?" (What was hard?) — finds UX friction
3. "Paylaşdın?" (Did you share?) — tests viral mechanic
4. "Nə əskik idi?" (What was missing?) — finds feature gaps

---

## Viral Loop Assessment

**Current state of the loop:**

```
User completes assessment
  → Gets AURA score + badge tier
    → Share buttons: Telegram, LinkedIn, WhatsApp, TikTok, native share
      → Shared link has OG card with score + competencies
        → Visitor sees public profile + "Get your AURA score" CTA
          → Visitor signs up → LOOP CLOSES
```

**What's working:**
- Share buttons exist (6 channels)
- OG card generates dynamically with score
- Public profile page has clear CTA to signup
- UTM tracking on share links

**What's missing:**
- No incentive to share (no "you get X for sharing")
- No notification when someone views your profile
- No "challenge a friend" mechanic active yet (component exists but untested)
- No email after assessment saying "share your result"
- PostHog not connected — can't measure share→signup conversion

**K-factor estimate:** Without incentives, expect K = 0.1-0.3 (1 in 3-10 users shares, 10-20% of recipients convert). Below viral threshold (K=1.0) but enough for initial validation.

---

## What Comes After 10

If the loop works (5+ out of 10 complete assessment AND receive score):

**Phase 1 Scale (Users 11-100):**
- CEO sends to broader network (50+ people)
- Add email lifecycle: welcome + assessment reminder + share nudge
- Connect PostHog for real funnel analytics
- Fix any UX issues found in Week 3 survey

**Phase 2 Scale (Users 100-1,000):**
- Partner with 1-2 volunteer organizations (not individuals)
- Organization creates account, assigns assessment to their volunteers
- This is where B2B revenue begins (Starter tier: 49 AZN/mo)

**Phase 3 Scale (Users 1,000-5,000):**
- WUF13 attendee funnel
- Press/content push (LinkedIn articles, Telegram channels)
- Referral incentive program (crystals for sharing)

---

## Decision Needed from CEO

**One question:** Should the first 10 users test with only communication competency (current state), or do we wait for Atlas to fix multi-competency scoring?

- **Ship now (1 competency):** Users get a partial AURA score. Faster feedback. But "Your AURA Score" showing only 1 of 8 competencies feels incomplete.
- **Wait (all 8):** Full product experience. But delays first users by however long the fix takes.

My recommendation: ship with 1 competency but change the UI copy. Instead of "Your AURA Score: 32.6" show "Communication: 32.6 — Take more assessments to build your full AURA profile." This sets expectation correctly and gives users a reason to come back.
