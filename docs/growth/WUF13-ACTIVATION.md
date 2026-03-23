# WUF13 Activation Strategy

## Executive Summary

WUF13 (World Urban Forum 13) in Baku, May 2026, is Volaura's launch event and primary growth catalyst. The goal is NOT to make WUF13 the purpose of the platform, but to use it as a concentrated moment of acquisition and virality. Strategy: pre-event positioning → on-site engagement → live leaderboards and referrals → post-event follow-up.

**Targets:**
- **Sign-ups:** 500+ during the 3-day event
- **Assessments completed:** 300+ (60% of signups)
- **Social shares:** 200+ (badge/referral shares)
- **K-factor during event:** >2.0 (accelerated viral loop)
- **Organizations met:** 10+ for [[ORG-ACQUISITION]] pipeline

**Timeline:** 2 weeks pre-event, 3 days on-site, 1 month post-event follow-up

---

## Phase 1: Pre-Event Positioning (2 weeks before)

### 1.1 Landing Page with WUF13 Co-Branding

**Purpose:** Capture interest from attendees researching the event; build hype.

**URL:** `volaura.com/wuf13` or homepage takeover during May 1-13

**Design:**
```
Header:
- WUF13 logo (official Baku event branding)
- "Volaura: Get Verified at World Urban Forum 13"
- Countdown timer: "Baku event in {X} days"

Hero Section:
- Video or animation: "500+ volunteers getting verified in Baku"
- CTA: "Sign up now and get a free assessment at WUF13"

Value Props (3 columns):
1. "Take your 15-min assessment on-site"
   Icon: clock
   Copy: "Get your AURA score instantly at the Volaura booth"

2. "See the live leaderboard"
   Icon: chart
   Copy: "Watch real-time rankings of top volunteers updating live"

3. "Share your badge"
   Icon: share
   Copy: "Post your verified status on social, inspire your network"

Attendee Testimonials:
- 3 quotes from current 200-volunteer pipeline who've already scored
- "AURA helped me land a volunteer role at X org" — Ahmed M.
- Names + scores + event they attended

Event Logistics:
- Date: May 15-17, 2026
- Venue: Baku Congress Center (hyperlink to venue info)
- Booth Location: Hall B, Registration Area
- Hours: 9 AM - 6 PM daily
- What to Bring: Phone or tablet (we provide WiFi)

FAQ Section:
Q: Is it free? A: Yes, completely free
Q: How long does it take? A: 15 minutes
Q: Will my results be public? A: Only if you want them to be
Q: Can I share my score? A: Yes! Share on LinkedIn, Instagram, WhatsApp

CTA Button (prominent, sticky):
- "Sign Up for WUF13" (link to signup flow)
- Secondary: "Learn More" (scroll to details)

Footer:
- Partner logos (if applicable: sponsor orgs, government, NGOs)
- Social media links to Volaura + WUF13
- Link to full event agenda
```

**Implementation:**
- Next.js page: `app/[locale]/wuf13/page.tsx`
- Reusable hero component with countdown timer logic
- OG tags for social sharing: `og:title="Get Verified at WUF13"`, `og:image=[event-specific image]`

---

### 1.2 Social Media Campaign

**Platforms:** LinkedIn (primary), Instagram, Twitter/X, WhatsApp Business

**Timeline:** Start 2 weeks before, increase frequency as event approaches

#### LinkedIn Campaign
**Audience:** Professionals in Baku, NGO workers, event volunteers
**Cadence:** 3x per week (posts) + daily stories if company page allows

**Content Mix:**
1. **Announcement (Day 1):** "Volaura is coming to WUF13. Get verified in Baku."
   - Image: WUF13 logo + Volaura branding
   - Copy: "In 2 weeks, 500+ volunteers will get their AURA score at World Urban Forum 13. Meet us at the booth and discover your strengths."
   - CTA: "Learn more → link to wuf13 landing page"

2. **Founder Perspective (Day 4):** Personal video from founder
   - "Why Volaura is sponsoring WUF13"
   - Focus on impact: "200+ volunteers already verified, ready to transform their communities"
   - CTA: "Reserve your spot: sign up early"

3. **Countdown (Day 7, 3, 1):** "X days until WUF13"
   - Testimonial from existing volunteer: "Getting my AURA score changed how I volunteer"
   - Quick facts: "15 min assessment, instant results, 60,000+ people at WUF13"
   - CTA: Pre-register

4. **Day-of Posts (during event):** Live updates
   - "Live from WUF13: 150 volunteers assessed so far!"
   - Leaderboard screenshot
   - "Visit Booth B-12 to get verified"

#### Instagram Campaign
**Audience:** Younger volunteers, visual-first social
**Cadence:** 4-5 posts total, daily stories during event

**Content:**
1. **Carousel (Day 1):** What is AURA?
   - Slide 1: "Discover your volunteer strengths"
   - Slides 2-6: One competency per slide (Leadership, Communication, Reliability, etc.)
   - Slide 7: "Get verified at WUF13"

2. **Reel (Day 5):** 15-second video
   - Quick montage: assessment → score reveal → badge celebration
   - Music: upbeat, local
   - Text overlay: "Get verified. Share your AURA. 15 min."
   - CTA: Link in bio

3. **Story Series (during event):** Live booth content
   - Volunteers taking assessments on tablets
   - Badge reveals (emoji reactions)
   - Leaderboard updates
   - Poll: "What competency are you strongest at?"
   - Countdown stickers to hourly giveaways

#### WhatsApp Business
**Channel:** Volaura WhatsApp Business account (if available) or group
**Content:**
- Invite existing contacts: "See you at WUF13 booth!"
- Day-of updates: booth location, wait times, giveaway schedule

---

### 1.3 Email Outreach to 200+ Volunteer Pipeline

**Audience:** Current 200+ users already in system

**Subject:** "You're invited: Volaura booth at World Urban Forum 13"

**Email Content:**
```
Hi {FirstName},

You've already earned your AURA score. Now show everyone else.

In 2 weeks, World Urban Forum 13 comes to Baku—with 60,000+ attendees.
We're setting up a dedicated Volaura booth in Hall B, and we want you there.

Here's what happens:

1. Visit our booth (Registration Area, 9 AM - 6 PM daily)
2. See the LIVE AURA leaderboard (real-time rankings)
3. Meet other volunteers and the team
4. Get a printed badge sticker (top scorers only)
5. Refer your friends at the event and earn bonus AURA points

Your referral link for the event: {PersonalReferralLink}
Share it with colleagues, friends, anyone interested.

Reserve your time slot now:
[Button: "See WUF13 Schedule"]

See you in Baku!
The Volaura Team

P.S. Top 10 referrers during WUF13 get a special "WUF13 Ambassador" badge.
```

---

### 1.4 Printed Collateral

**Inventory:**
1. **QR Code Posters** (200 units)
   - Locations: Outside venue, session rooms, break areas
   - Design: Large QR code → `volaura.com/join/{qr_tracking_id}`
   - Text: "Get Verified at Volaura → Scan to join"
   - Volaura + WUF13 logos

2. **Mini Flyers** (5,000 units)
   - Size: A6 (4.1" x 5.8")
   - Design: One side = AURA score example, other side = QR code
   - Include: "15 min. Completely free. volaura.com/wuf13"

3. **Table Tents** (30 units, for booth)
   - Fold-out cardstock: "Sign up here" + QR code
   - Leaderboard display ads

4. **Badge Stickers** (Printed on-demand)
   - Design: Volaura badge tier (Bronze/Silver/Gold/Platinum)
   - Text: Name, AURA score, badge tier
   - For top scorers to wear at event

---

## Phase 2: On-Site Strategy (3 days)

Event: May 15-17, 2026 | Venue: Baku Congress Center

### 2.1 Booth Layout & Experience

**Location:** Hall B (Registration Area if possible, high foot traffic)

**Booth Size:** 20x10 ft (basic setup)

**Equipment:**
- 2-3 tablets (iPad with assessment app)
- 1 laptop (for org reps to verify volunteers)
- 1 large display screen (43"+ TV or projector)
- WiFi router (backup if venue WiFi fails)
- Portable chargers
- Signage (3-4 banners)

**Staffing:**
- 1 person full-time (deployment manager or volunteer lead)
- 2 people per 8-hour shift (rotation)
- Volunteer assessment guides (if available)
- Bilingual support (AZ/EN at minimum)

**Design Aesthetic:**
- Volaura brand colors (blue, white, light gray)
- WUF13 co-branding (official logo displayed)
- Modern, tech-forward (not cluttered)
- Inviting (comfortable seating for waiting)

---

### 2.2 Assessment Optimization for WUF13

**Challenge:** 500+ people, potential 5,000+ foot traffic, unreliable WiFi

**Solution: Quick Mode Assessment**

Standard assessment: 40 questions (20 min)
WUF13 Quick Mode: 20 questions (10 min)
- Reduce questions per competency from 5 to 2-3
- Fewer options for some questions (faster responses)
- Same scoring logic (no compression of results)

**Offline-First Strategy**

1. **Pre-download questions:** At startup, cache all 20 WUF13 Quick questions + media locally
2. **Answer locally:** All user interactions happen in-browser (no network calls)
3. **Batch sync:** After completion, sync responses to backend when WiFi returns
4. **Fallback:** If offline assessment can't sync within 1 hour, queue for later eval

**Queue Management (If Overwhelmed)**

If booth gets >20 people waiting:
1. Display: "Your turn in ~{X} min"
2. Collect email/phone for later reminder
3. Send SMS/email: "Come back at {time}, we'll have your results ready"
4. Assessments evaluated in batches (150 users → eval in 30 min blocks)

**Technical Implementation:**
```typescript
// Quick Mode assessment in Next.js
export const QUICK_MODE_CONFIG = {
  num_questions: 20,
  questions_per_competency: 3,
  timeout_per_question: 30, // seconds
  estimated_duration_minutes: 10,
};

// Offline service worker
// Cache all questions at app startup
// Use IndexedDB for local answer storage
// Sync on page visibility change or manual upload
```

---

### 2.3 Live Leaderboard Display

**Purpose:** Create FOMO and competitive energy

**Technical Setup:**
1. Large display shows top 50 global AURA scorers (updated every 10 minutes)
2. Filter toggles (Baku only, today only, WUF13 attendees)
3. Real-time animation (scores update with Supabase Realtime)
4. Scroll through names, scores, badges

**Design:**
```
┌─────────────────────────────────────────┐
│  🏆 AURA Leaderboard - WUF13 2026 🏆   │
├─────────────────────────────────────────┤
│ #1  Fatima M.     95 AURA [PLATINUM]    │
│ #2  Ahmed K.      91 AURA [PLATINUM]    │
│ #3  Leila H.      88 AURA [GOLD]        │
│ ...                                     │
│ #47 Sarah T.      72 AURA [SILVER]      │
├─────────────────────────────────────────┤
│ Filters: [Global] [Baku] [Today]        │
│ Last updated: 2 minutes ago              │
└─────────────────────────────────────────┘
```

**Implementation:**
- Supabase Realtime subscription to `aura_scores` table
- Recharts line chart for real-time updates
- Next.js component: `components/features/LiveLeaderboard.tsx`

---

### 2.4 Photo Booth Integration

**Purpose:** Gamify the experience, drive Instagram shares

**Setup:**
- iPad/tablet with photo capture + badge overlay
- Printed props (AURA badges, WUF13 signage)
- Backdrop with WUF13 + Volaura branding

**Mechanics:**
1. Volunteer poses with badge/prop
2. Photo taken with iPad
3. Real-time badge overlay added (badge icon + score)
4. Instagram share prompt: "Share your AURA moment"
5. Link includes referral code: `instagram.com/share?url=volaura.com/u/{username}?ref={code}`

**Implementation:**
- Web app using Canvas or FFmpeg to overlay badge
- One-tap Instagram share (via Web Intent API)
- Store photos in Supabase Storage if permission granted

---

### 2.5 Physical Badges (Top Scorers)

**Purpose:** Tangible reward, drives competition

**When:** End of each day, print badges for top 10 daily scorers

**Design:**
- Small sticker badge (2" x 2")
- Format: "[#{Rank}] {Name} | {Score} AURA | {Tier}"
- Example: "#3 Leila | 88 AURA | GOLD"
- Volaura logo + WUF13 logo

**Technology:**
- Query top 10 by `assessment_sessions.completed_at` DESC for the day
- Render PNG via Next.js API route (same tech as share badges)
- Print on thermal printer (ZeBra or similar)
- Deliver end of day (5 PM ceremony)

**Announcement:**
- "Daily recognition! Top 10 scorers from today, come get your printed badge!"
- Photos of badge winners for social media

---

### 2.6 Organization Engagement

**Goal:** Identify volunteer orgs for [[ORG-ACQUISITION]] pipeline

**Setup:**
1. Booth area for org reps to sign up
2. Demo Volaura org dashboard (verification workflow)
3. "Organizations: Free access for your first event" CTA

**Process:**
- Org rep fills short form: org name, sector, contact
- Demo: "See the verified volunteers matching your needs"
- Follow-up: Email within 48 hours with onboarding link

**Targets:**
- Meet: 10+ org reps
- Convert to trial: 5+
- Qualified leads for growth: All 10+

---

### 2.7 Activation Day-by-Day Schedule

#### Day 1 (May 15): Soft Launch, Awareness Building
- **Booth Setup:** 8 AM - 9 AM
- **Hours:** 9 AM - 6 PM
- **Focus:** Foot traffic, signups, word-of-mouth
- **Staffing:** 2 people
- **Goal:** 150 signups, 80 assessments
- **Daily Email:** "WUF13 opened! See live leaderboard."

#### Day 2 (May 16): Peak Engagement, Competitive Energy
- **Hours:** 9 AM - 6 PM
- **Focus:** Leaderboard updates, referrals, org meetings
- **Staffing:** 2-3 people (busiest day)
- **Goal:** 200 signups, 120 assessments
- **Hourly Update:** Announce top 10 daily scorers on loudspeaker/display
- **Giveaway:** Every 2 hours, raffle 1 free Volaura premium feature (future value)
- **Livestream:** 30-min Instagram/YouTube live tour of booth

#### Day 3 (May 17): Finale, Celebration, Post-Event Push
- **Hours:** 9 AM - 4 PM (shorter, event closing early)
- **Focus:** Last-minute signups, ceremony for top performers
- **Staffing:** 2 people
- **Goal:** 150 signups, 100 assessments
- **Closing Ceremony (3 PM):** Announce WUF13 top 20, give printed badges
- **Post-Event Email Send:** Immediate (within 2 hours) to all WUF13 participants

---

## Phase 3: Post-Event Follow-Up (1 month)

### 3.1 Immediate Email Blitz (Days 1-3)

**To all WUF13 participants who signed up:**

**Day 0 (same day):** "Thank you for WUF13"
```
Subject: "You were amazing at WUF13. Here's what's next."

Body:
- Thank you for attending
- Recap: {X} volunteers verified, {Y} new friends made
- Your score: {Score} | {Tier}
- CTA: "View your profile"
- Social: "Share what you accomplished"
```

**Day 1:** "Your AURA journey doesn't end here"
```
Subject: "Keep the momentum. Volunteer now."

Body:
- Highlight: "250 assessments completed at WUF13"
- Next step: Events matching your competencies
- Featured: "3 events this month where your skills matter"
- CTA: "See events near you"
```

**Day 3:** Peer re-engagement
```
Subject: "Your friends from WUF13 are already active"

Body:
- Social proof: "15 volunteers from the forum have already shared"
- Leaderboard update: "You rank #{rank} on the WUF13 leaderboard"
- CTA: "View leaderboard" + "Invite your WUF13 friends"
```

---

### 3.2 Referral Push (Week 1-2)

**Incentive:** "Refer WUF13 friends and both get bonus AURA"

**Email (Week 1):**
```
Subject: "Bring your WUF13 friends to Volaura and earn rewards"

Copy:
- "Remember {Friend}'s name from the booth? Invite them."
- Referral link: {PersonalReferralLink}
- Bonus: "+2 AURA for each friend who assesses"
- Leaderboard: "Top referrers this month get featured"
- CTA: "Invite friends"
```

**In-App Notification:**
- "You can earn +20 AURA by referring your WUF13 network"
- Share button pre-filled with referral link

---

### 3.3 Highlight Top Performers (Week 2-3)

**Email: "Meet WUF13's AURA Stars"**

**Content:**
- Top 5 scorers: photos + profiles
- Most improved: story of growth
- Most referrals: community builder highlight
- Featured on: Volaura blog, social media, in-app

**Distribution:**
- Email to all WUF13 participants
- LinkedIn post from company account
- Instagram post + stories
- Blog post: "Lessons from 500 WUF13 Volunteers"

---

### 3.4 Event Tracking for [[ORG-ACQUISITION]]

**Immediate (Day 1):**
- Follow up with all org reps who visited booth
- Email: "Thanks for exploring Volaura at WUF13"
- Offer: "Free tier access for your next event"
- Calendar invite: 15-min onboarding call

**Week 2:**
- Send case study: "How WUF13 used Volaura to verify volunteers"
- Data: {X} volunteers, {Y} events, {Z} hours saved on vetting

**Month 1:**
- Check-in: "Ready to launch your first event on Volaura?"

---

### 3.5 Badge & Leaderboard Persistence

**WUF13 Attendee Badge:** Permanent on profiles
- All users who assessed during May 15-17 get special badge: "✓ WUF13 Verified"
- Shows on leaderboard for 3 months post-event
- Builds credibility: "Trusted by 500+ WUF13 volunteers"

**WUF13 Leaderboard:** Archived
- Freeze leaderboard at end of event
- Make public: `volaura.com/leaderboard/wuf13`
- Display: "WUF13 Top 50" for historical reference
- Link from blog post

---

## Contingency Plans

### Poor WiFi Connectivity
- **Backup:** Bring portable hotspot (Mifi device, 4G router)
- **Offline mode:** Quick assessment pre-cached locally, sync later
- **Communication:** "WiFi slow? We'll email your results within 1 hour"

### Higher Than Expected Foot Traffic
- **Queue system:** Email reminder with time slot
- **Batch evaluation:** Run LLM evals in scheduled batches (3 per hour)
- **Extend hours:** Stay open until 7 PM if needed

### Equipment Failure
- **Backup tablet:** Bring 1 extra iPad
- **Display failure:** Use laptop connected to TV (via HDMI)
- **Printer failure:** Use on-demand badge printing service (e.g., Printful API)

### Low Sign-Up Rate
- **Price incentive:** Offer "Free premium month for WUF13 attendees"
- **Social proof:** Display leaderboard more prominently
- **Booth visibility:** Move location if traffic is low

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Total booth visits | 1,000+ | |
| Sign-ups | 500+ | |
| Assessment completions | 300+ | |
| Conversion (signup → assessment) | 60%+ | |
| Social shares | 200+ | |
| Referrals generated at booth | 150+ | |
| Org leads captured | 10+ | |
| Post-event survey response | 40%+ | |
| Event NPS | 50+ | |

---

## Post-Event Retrospective (Week 4)

**Team Debrief:** What worked, what didn't
**Metrics Analysis:** Compare targets vs. actual
**Key Questions:**
- What was most effective signup trigger?
- Best referral source?
- Organization insights (which sectors interested)?
- Assessment completion rate (was offline helpful)?
- Leaderboard impact (did it drive competition)?

**Document findings:** Add to [[DECISIONS.md]] for future events

---

## Cross-References

- [[VIRAL-LOOP]] — Referrals accelerate during event
- [[EMAIL-STRATEGY]] — Pre, during, post-event emails
- [[ORG-ACQUISITION]] — Organization meetings at booth
- [[CLAUDE.md]] — Tech stack for offline assessment, live leaderboard
