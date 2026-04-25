# Viral Loop & Social Amplification

## Executive Summary

Volaura's core growth engine relies on a badge-sharing viral loop with a target K-factor of 1.2+. The mechanic is simple: volunteers earn AURA scores → share badges on social → friends see proof of achievement → friends sign up → cycle repeats. This document outlines share triggers, referral mechanics, and social proof amplifiers to achieve organic growth at scale.

**Target:** 25% conversion from shared badge → signup, with 5 invites per user = K of 1.25.

---

## Core Viral Mechanic

### The Loop
```
1. Volunteer completes assessment
2. Receives AURA score (0-100) + badge tier (Bronze/Silver/Gold/Platinum)
3. System shows "Share your achievement" with 1-click buttons
4. Volunteer shares on LinkedIn/Instagram/WhatsApp
5. Friend sees badge → "I want to know my score" → signs up
6. Friend takes assessment → gets score → shares → loop continues
```

### Why This Works
- **Real Achievement:** AURA score is earned, not given. Sharing is authentic.
- **Social Proof:** Seeing a peer's score normalizes taking the platform seriously.
- **Status Signal:** Badge tier signals competency level—people want to show they're worthy.
- **FOMO:** Leaderboard + referral rewards create incentive to participate.

---

## Share Triggers (High-Intent Moments)

These are the moments when users are most motivated to share. The system should detect each and surface the share UI aggressively.

### 1. Score Reveal (Highest Intent)
- **When:** Immediately after assessment completes, before showing anything else
- **What:** Full-screen modal showing:
  - Final AURA score (large, animated number)
  - Badge tier with animation (e.g., "Silver Badge" with shimmer effect)
  - Radar chart comparing to averages
  - Share buttons prominent (LinkedIn, Instagram, Twitter, WhatsApp, Copy Link)
- **Copy:** "You earned your AURA Score. Share it and inspire others."
- **Conversion:** Highest—user is in "achievement mode"
- **Implementation:** Frontend modal component triggered on assessment completion

### 2. Badge Upgrade
- **When:** AURA score improves enough to move to next tier
- **What:** Notification + in-app toast:
  - "🎉 Congratulations! You earned a Silver Badge"
  - Show old vs. new badge side-by-side
  - "Share your progress" button
- **Copy:** "You've leveled up. Show your network."
- **Conversion:** Medium-high—emotional high
- **Trigger Logic:** After assessment completion or org attestation, recalculate score; if tier changes, fire notification

### 3. Leaderboard Rank Change
- **When:** User enters top 10, top 50, or breaks into new rank tier
- **What:** In-app notification:
  - "You're now #8 in Baku AURA rankings"
  - Link to leaderboard showing their position
  - "Share your rank" CTA
- **Copy:** "You're in the top 10. Your network should know."
- **Conversion:** Medium—appeals to competitive users
- **Leaderboard:** [[#Social Proof Amplifiers]]

### 4. Organization Attestation
- **When:** An organization verifies one or more competencies
- **What:** Email + in-app notification:
  - "Acme NGO verified your {Leadership, Communication} skills"
  - New "Verified by Acme" badge on profile
  - "Share your verified skills" CTA
- **Copy:** "Organizations trust your expertise. Share it."
- **Conversion:** Medium—social proof angle
- **Implementation:** Trigger via `attestations` table insert

### 5. Event Completion
- **When:** User checks in to event and organizer marks completion
- **What:** Post-event email + in-app notification:
  - "You volunteered at the major event! Added to your profile."
  - Event badge or streak counter
  - "Share what you did" CTA
- **Copy:** "You made an impact. Let others know."
- **Conversion:** Low-medium—depends on event prominence
- **Integration:** Event activation strategy

---

## Share Formats

All share formats should include OG (Open Graph) tags so shared links display rich cards on social platforms.

### 1. LinkedIn Post Card
- **Dimensions:** 1200x627px
- **Content:**
  - AURA score (large, bold text)
  - Badge tier name + icon
  - Radar chart (6 competencies)
  - Volunteer's name (optional—default to anonymous)
  - CTA: "Get your AURA Score" linking to signup/login
- **Style:** Professional, clean, Volaura brand colors
- **Implementation:** Generate server-side via Next.js API route or Vercel function, store as shareable image
- **Share Button:** Integrates with LinkedIn share API

### 2. Instagram Story Template
- **Dimensions:** 1080x1920px vertical
- **Content:**
  - Name at top ("Sarah's AURA Score")
  - Large score number (center)
  - Badge tier below
  - Vibrant gradient background (changes by tier: Bronze=copper, Silver=gray, Gold=gold, Platinum=diamond gradient)
  - Bottom CTA: "Get Yours @volaura.com"
  - WhatsApp/Instagram Story sticker-friendly design
- **Style:** Modern, colorful, Instagram-native feel
- **Implementation:** React component rendered to PNG server-side
- **Share Method:** Download image → upload to Instagram Story or use direct Instagram share API

### 3. Square Card (General Social)
- **Dimensions:** 1080x1080px
- **Content:**
  - Smaller version of score + badge
  - Competency icons (6 small circular icons)
  - Short tagline: "I'm verified. Are you?"
  - URL: `volaura.com/u/{username}`
- **Style:** Works on Twitter, Facebook, Pinterest
- **Use Case:** Evergreen profile sharing, not just score reveal

### 4. Shareable Public Profile Link
- **URL:** `volaura.com/u/{username}` or `volaura.com/u/{uuid}`
- **Page Includes:**
  - AURA score + badge
  - Radar chart
  - Competencies breakdown
  - Organizations that verified
  - Events attended
  - OG tags for rich preview:
    - `og:title`: "{Name}'s AURA Score: {Score}"
    - `og:image`: Dynamic image of badge + score
    - `og:description`: "Verified profile on Volaura"
- **Privacy:** Public by default; users can opt to anonymous after signup
- **Implementation:** Dynamic route in Next.js App Router with generateStaticParams

### 5. QR Code
- **Use Case:** Physical events, printed materials
- **Target:** `volaura.com/join/{qr_code_id}`
- **Design:**
  - Square, 200x200px minimum
  - Volaura logo in center (white background)
  - Text below: "Get verified at Volaura"
- **Print Strategy:** Pre-event materials should include QR codes (2 weeks before launch event)
- **Tracking:** Each QR code has unique ID to track which source referred user

### 6. WhatsApp Share
- **Format:** Text message + link
- **Content:** "Check out my AURA Score! [link to profile]"
- **Button:** One-click share to WhatsApp (uses WhatsApp Web API)
- **Important:** WhatsApp doesn't preview links richly like other platforms, so include name + score in text

---

## Referral System

The referral mechanic creates a second viral loop: users actively inviting peers, not just passively sharing.

### Unique Referral Link
- **Format:** `volaura.com/join/{referral_code}`
- **Code:** 8-character unique slug (e.g., `x4k9pLm2`)
- **Generation:** When user account created, generate code; store in `profiles.referral_code`
- **Tracking:** When new user signs up via referral link, store referrer ID in `profiles.referred_by`

### Referrer Rewards
- **Reward Type:** Small AURA boost (NOT enough to game the system)
- **Amount:** +2 AURA points per successful referral (max 20 points from referrals per month)
- **Why Small:** Prevents people from farming referrals; keeps focus on genuine achievement
- **Notification:** "You earned +2 AURA for referring {Name}"
- **Cap:** After 10 successful referrals in a month, reward drops to +1

### Referee Rewards
- **Reward:** Priority in next assessment queue (see faster results)
- **Benefit:** When queued assessments are evaluated by LLM, referred users get processed first
- **Notification:** "Jump the line! You were referred by {Name}—assessment starts now"
- **Implementation:** Add `priority_score` column to `assessment_sessions` table

### Leaderboard for Top Referrers
- **Display:** In-app tab showing top 20 users by referrals
- **Metrics:**
  - `referral_code`
  - `referrals_this_month`
  - `referral_conversion_rate` (% who completed assessment)
- **Incentive:** Top 3 get featured in monthly email, special "Advocate" badge
- **Reset:** Monthly leaderboard resets on 1st of each month

### Conversion Tracking
- **Tables:**
  - `profiles.referral_code` (generated at signup)
  - `profiles.referred_by` (foreign key to referrer's user_id)
  - `referral_conversions` table:
    - `referrer_id`, `referee_id`, `created_at`, `status` (invited/signup/assessed/converted)
- **Queries:**
  - "How many people has {user_id} referred?"
  - "What's the conversion rate from my referrals?"
- **Dashboard:** Users see their referral stats in profile settings

### Target Metrics
- **Average referrals per user:** 5 (mix of active sharers and passive)
- **Conversion rate:** 25% of referred invitees complete signup
- **K-factor contribution:** 5 × 0.25 = 1.25

---

## Viral Coefficient (K-Factor)

The K-factor measures viral growth sustainability.

```
K = invites_per_user × conversion_rate
```

### Target: K > 1.2

**Breakdown:**
- **Invites per user:** 5
  - 2 via direct share buttons (score reveal, badge upgrade)
  - 2 via referral link sharing
  - 1 via email/messaging to close network
- **Conversion rate:** 25%
  - LinkedIn share: 15-20% (professional audience, high intent)
  - Instagram share: 20-25% (younger audience, social proof)
  - Referral link: 30% (already warm, peer endorsement)
  - Weighted average: 25%
- **K = 5 × 0.25 = 1.25** ✓

### Monitoring K-Factor
- **Metrics to Track:**
  - `invites_sent_per_user` (sum of share button clicks per user)
  - `conversion_from_shared_link` (% of clicks that result in signup)
  - `time_to_conversion` (days from share to signup)
- **Dashboards:**
  - Internal analytics dashboard (Supabase + Recharts)
  - Weekly K-factor report to team
  - Alerts if K drops below 1.1

### Levers to Optimize K
- **Increase invites:** Better share triggers, referral UX
- **Increase conversion:** Improve landing page, simplify signup, social proof on signup page
- **Reduce friction:** One-click share, pre-filled referral messages, mobile optimization

---

## Social Proof Amplifiers

These mechanisms create visibility and FOMO that drives signups.

### 1. Real-Time Leaderboard

**Mechanics:**
- **Frequency:** Updated every 10 minutes via Supabase Realtime
- **Scope:** Global, by city, by competency
- **Visibility:**
  - Leaderboard page: `volaura.com/leaderboard`
  - In-app dashboard
  - Shareable: `volaura.com/leaderboard?city=baku`
- **Data:**
  - User rank, name (anonymized by default), AURA score, badge tier
  - Trend indicator (↑/→/↓ if rank changed)
  - Verified badge count
- **Implementation:**
  - View in Supabase: `SELECT rank() OVER (ORDER BY total_score DESC) as rank, * FROM aura_scores ORDER BY total_score DESC LIMIT 100`
  - Realtime subscription on frontend: `supabase.from('aura_scores').on('*', callback).subscribe()`

### 2. Geographic Segmentation
- **Message:** "X people in your city have AURA scores"
- **Mechanics:**
  - User's profile includes `city` (derived from location on signup or filled manually)
  - Notification: "250 volunteers in Baku now verified"
  - Local leaderboard: see who in your city ranks highest
  - Event discovery: "Events in Baku for your competencies"
- **Psychological Hook:** Local peer pressure (FOMO to join local community)

### 3. Organization Logo Wall
- **Visual:** On public profiles and leaderboard, show logos of orgs that verified the volunteer
- **Mechanics:**
  - When org attests a competency, org logo added to volunteer's profile
  - Displays up to 5 logos (most recent or highest-profile first)
  - Hover shows: "{Org} verified {Competency} on {Date}"
- **Social Proof:** "These professional organizations trust this person"

### 4. Launch Event Branding & Limited-Time Badge
- **During Event:** All profiles show "Launch Event Attendee" badge if they assessed during launch event window (May 2026)
- **Mechanics:**
  - `profiles.launch_event_attendee = true` if signup_date in launch event window
  - Special leaderboard: "Top Launch Event Scorers"
  - Email campaigns highlight "500+ volunteers verified at launch event"
- **Scarcity:** Time-limited, creates urgency to attend

### 5. "Featured This Week" Spotlight
- **Selection:** Highest improvement in AURA score, most referrals, or interesting profile
- **Display:** Featured in weekly email to all users, in-app spotlight section
- **Benefit to Featured:** Small badge, highlight on profile, PR in social channels
- **Mechanics:**
  - Admin or algorithm selects 3-5 users weekly
  - Email highlight with their profile photo, score, story (optional quote)
  - Drive traffic to their public profile

---

## Gamification Elements

Beyond badges, these mechanics keep users engaged and sharing.

### 1. Badge Progression Visualization
- **Current:** User sees current tier (Bronze/Silver/Gold/Platinum)
- **New:** Show progress bar to next tier with clear score gap
- **Example:** "Silver (75 AURA) — You're 8 points away from Gold. Share your profile to learn more."
- **Update Frequency:** After every assessment completion or attestation

### 2. Streak System
- **Mechanic:** Consecutive months attending at least one event
- **Display:** "✓ 3-month Volunteer Streak"
- **Incentive:** Users don't want to break the streak
- **Leaderboard:** "Longest Active Streaks"
- **Reset:** If user doesn't attend event in a month, streak resets to 0
- **Notification:** "Your streak is active! One more event this month keeps it going."

### 3. "AURA Rising" Notification
- **Trigger:** After user completes an assessment and AURA score improves
- **Message:** "Your AURA is rising—now 82 (up from 78). Silver badge earned!"
- **Mechanic:** Encourages retaking assessments to see improvement
- **Frequency:** Only show when genuine improvement happens

### 4. Monthly "AURA Stars" Recognition
- **Selection Criteria:**
  - Top 3 overall scorers in the month
  - Most improved score
  - Most events attended
  - Most referrals
- **Recognition:**
  - Monthly email: "Meet this month's AURA Stars"
  - In-app badge: "AURA Star — March 2026"
  - Feature on social media (@volaura Instagram)
  - Announce in volunteer community Slack/Discord (if exists)
- **Psychological:** Aspirational goal; users compete to be featured

### 5. Competency Specialization Path
- **Mechanic:** Users can focus on specific competencies; earn "Specialist" badge
- **Display:** "Leadership Specialist" badge if score >85 in one competency
- **Incentive:** Specialized volunteers more valuable to orgs, can market themselves
- **Leaderboard:** "Top Leadership Specialists" (competency-specific rankings)

---

## Implementation Timeline

### Phase 1 (Weeks 1-2, Pre-Launch Event)
- [ ] Score reveal modal with share buttons (LinkedIn, Instagram, WhatsApp, Copy)
- [ ] Referral link generation + tracking
- [ ] Public profile page with OG tags
- [ ] Real-time leaderboard (global + city)
- [ ] Badge tier logic in assessment completion flow

### Phase 2 (Week 3-4, Pre-Launch Event)
- [ ] Badge upgrade notifications
- [ ] Leaderboard rank notifications
- [ ] Organization attestation sharing flow
- [ ] Referral rewards (AURA boost + priority queue)
- [ ] Top referrers leaderboard

### Phase 3 (Week 5, at Launch Event)
- [ ] Launch event attendee badge
- [ ] Limited-time leaderboard display
- [ ] QR code generation + tracking
- [ ] Offline-first share capability (cache badge images)

### Phase 4 (Weeks 6+, Post-Launch Event)
- [ ] Streak system
- [ ] Monthly AURA Stars recognition
- [ ] Email features of top referrers
- [ ] Competency specialization badges
- [ ] A/B testing on share triggers

---

## Technical Implementation Notes

### Frontend (Next.js)
- **Share Modal Component:** `components/features/ShareModal.tsx`
  - Detects platform (mobile iOS → Instagram, Android → WhatsApp, desktop → LinkedIn)
  - Uses native share APIs where available, fallbacks to copy/link
  - Tracks share via `useAnalytics()` hook (event: `"share_score"`, properties: `{platform, badge_tier}`)

- **Leaderboard Page:** `app/[locale]/leaderboard/page.tsx`
  - Server-side query to get top 100 users
  - Realtime subscription for live updates
  - Filters: city, competency
  - Client-side scroll loads more via TanStack Query

- **Public Profile:** `app/[locale]/u/[username]/page.tsx`
  - generateStaticParams for SEO
  - OG image generation via Vercel OG Image Generator (dynamic text)

### Backend (FastAPI)
- **OG Image Generation Endpoint:** `POST /api/og-image`
  - Input: `user_id`, `score`, `badge_tier`
  - Output: PNG image (cached in S3 or Vercel Blob)
  - Library: `PIL` or `Pillow`, or use Vercel SDK

- **Referral Code Generation:** `POST /api/referrals/generate`
  - Generate unique 8-char code
  - Store in `profiles.referral_code`

- **Referral Tracking:** Middleware or hook when user signs up
  - Check query param `?ref={code}`
  - Lookup referrer via `profiles.referral_code = code`
  - Set `profiles.referred_by = referrer_id`
  - Log in `referral_conversions` table

- **Leaderboard Query:** RPC function in Supabase
  ```sql
  CREATE OR REPLACE FUNCTION get_leaderboard(
      p_limit INT DEFAULT 100,
      p_city TEXT DEFAULT NULL,
      p_competency TEXT DEFAULT NULL
  ) RETURNS TABLE(rank INT, user_id UUID, name TEXT, score FLOAT, badge_tier TEXT) AS $$
  BEGIN
      RETURN QUERY
      SELECT ROW_NUMBER() OVER (ORDER BY a.total_score DESC),
             a.volunteer_id, p.display_name, a.total_score, p.badge_tier
      FROM aura_scores a
      JOIN profiles p ON a.volunteer_id = p.id
      WHERE (p_city IS NULL OR p.city = p_city)
      ORDER BY a.total_score DESC
      LIMIT p_limit;
  END;
  $$ LANGUAGE plpgsql;
  ```

### Analytics
- **Events to Track:**
  - `share_button_clicked` (platform: linkedin/instagram/whatsapp/copy)
  - `badge_earned` (badge_tier)
  - `rank_changed` (new_rank, direction: up/down)
  - `referral_link_clicked` (referrer_id)
  - `signup_from_referral` (referrer_id)
  - `signup_from_shared_profile` (source_user_id)

- **Dashboard:** Supabase + Recharts showing K-factor, conversion rates, top referrers

---

## Metrics & Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Viral Coefficient (K)** | > 1.2 | (invites/user) × (conversion rate) |
| **Share Conversion Rate** | > 25% | signup / shared_link_clicks |
| **Referral Conversion** | > 30% | referee_signup / referral_invites |
| **Monthly Active Sharers** | > 40% of assessed users | users_clicked_share / total_assessed |
| **Leaderboard Views** | > 500/week | page views to leaderboard |
| **Referral-Driven Signups** | > 20% of new signups | signup_with_referred_by / total_signups |

---

## Cross-References

- Event activation strategy — Using viral loop at the launch event
- [[EMAIL-STRATEGY]] — Transactional emails trigger sharing
- [[ORG-ACQUISITION]] — Organizations drive more events, enabling streaks
- [[CLAUDE.md]] — Tech stack (Zustand for share modal state, TanStack Query for leaderboard)

