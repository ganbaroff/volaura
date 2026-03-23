# Event Activation Strategy

## Executive Summary

A major event (e.g., international conference, summit, forum) presents Volaura's opportunity to acquire volunteers at scale and create viral growth. The goal is NOT to make any single event the platform's entire purpose, but to use it as a concentrated moment of acquisition and virality. Strategy: pre-event positioning → on-site engagement → live leaderboards and referrals → post-event follow-up.

**Example Targets (adjust by event size):**
- **Sign-ups:** 500+ during the multi-day event
- **Assessments completed:** 300+ (60% of signups)
- **Social shares:** 200+ (badge/referral shares)
- **K-factor during event:** >2.0 (accelerated viral loop)
- **Organizations met:** 10+ for [[ORG-ACQUISITION]] pipeline

**Timeline:** 2 weeks pre-event, 3-5 days on-site, 1 month post-event follow-up

---

## Phase 1: Pre-Event Positioning (2 weeks before)

### 1.1 Landing Page with Event Co-Branding

**Purpose:** Capture interest from attendees researching the event; build hype.

**URL:** `volaura.com/{event-slug}` or homepage takeover during final 2 weeks

**Design:**
```
Header:
- Event logo (official co-branding)
- "Volaura: Get Verified at [EVENT_NAME]"
- Countdown timer: "[EVENT_NAME] in {X} days"

Hero Section:
- Video or animation: "500+ volunteers getting verified at [EVENT_NAME]"
- CTA: "Sign up now and get a free assessment at [EVENT_NAME]"

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
- 3 quotes from current volunteer pipeline who've already scored
- Include names, scores, and context
- Build social proof: "AURA helped me land a volunteer role at X org"

Event Logistics:
- Date: [EVENT_DATES]
- Venue: [VENUE_NAME] (hyperlink to venue info)
- Booth Location: [BOOTH_LOCATION]
- Hours: [BOOTH_HOURS]
- What to Bring: Phone or tablet (we provide WiFi)

FAQ Section:
Q: Is it free? A: Yes, completely free
Q: How long does it take? A: 15 minutes
Q: Will my results be public? A: Only if you want them to be
Q: Can I share my score? A: Yes! Share on LinkedIn, Instagram, WhatsApp

CTA Button (prominent, sticky):
- "Sign Up for [EVENT_NAME]" (link to signup flow)
- Secondary: "Learn More" (scroll to details)

Footer:
- Partner logos (if applicable: sponsor orgs, government, NGOs)
- Social media links to Volaura + event
- Link to full event agenda
```

**Implementation:**
- Next.js page: `app/[locale]/events/{event-slug}/page.tsx` (parameterized)
- Reusable hero component with countdown timer logic
- OG tags for social sharing: `og:title="Get Verified at [EVENT_NAME]"`, `og:image=[event-specific image]`

---

### 1.2 Social Media Campaign

**Platforms:** LinkedIn (primary), Instagram, Twitter/X, WhatsApp Business

**Timeline:** Start 2 weeks before, increase frequency as event approaches

#### LinkedIn Campaign
**Audience:** Professionals in event city/region, NGO workers, event volunteers
**Cadence:** 3x per week (posts) + daily stories if company page allows

**Content Mix:**
1. **Announcement (Day 1):** "Volaura is coming to [EVENT_NAME]. Get verified."
   - Image: Event logo + Volaura branding
   - Copy: "In 2 weeks, 500+ volunteers will get their AURA score at [EVENT_NAME]. Meet us at the booth and discover your strengths."
   - CTA: "Learn more → link to event landing page"

2. **Founder Perspective (Day 4):** Personal video from founder
   - "Why Volaura is at [EVENT_NAME]"
   - Focus on impact: "200+ volunteers already verified, ready to transform their communities"
   - CTA: "Reserve your spot: sign up early"

3. **Countdown (Day 7, 3, 1):** "X days until [EVENT_NAME]"
   - Testimonial from existing volunteer: "Getting my AURA score changed how I volunteer"
   - Quick facts: "15 min assessment, instant results, [ATTENDEE_COUNT]+ attendees"
   - CTA: Pre-register

4. **Day-of Posts (during event):** Live updates
   - "Live from [EVENT_NAME]: 150 volunteers assessed so far!"
   - Leaderboard screenshot
   - "Visit [BOOTH_LOCATION] to get verified"

#### Instagram Campaign
**Audience:** Younger volunteers, visual-first social
**Cadence:** 4-5 posts total, daily stories during event

**Content:**
1. **Carousel (Day 1):** What is AURA?
   - Slide 1: "Discover your volunteer strengths"
   - Slides 2-6: One competency per slide (Leadership, Communication, Reliability, etc.)
   - Slide 7: "Get verified at [EVENT_NAME]"

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
- Invite existing contacts: "See you at [EVENT_NAME] booth!"
- Day-of updates: booth location, wait times, giveaway schedule

---

### 1.3 Email Outreach to Volunteer Pipeline

**Audience:** Current users already in system

**Subject:** "You're invited: Volaura booth at [EVENT_NAME]"

**Email Content:**
```
Hi {FirstName},

You've already earned your AURA score. Now show everyone else.

In 2 weeks, [EVENT_NAME] comes to [CITY]—with [EXPECTED_ATTENDEES]+ attendees.
We're setting up a dedicated Volaura booth in [BOOTH_LOCATION], and we want you there.

Here's what happens:

1. Visit our booth ([BOOTH_LOCATION], [BOOTH_HOURS])
2. See the LIVE AURA leaderboard (real-time rankings)
3. Meet other volunteers and the team
4. Get a printed badge sticker (top scorers only)
5. Refer your friends at the event and earn bonus AURA points

Your referral link for the event: {PersonalReferralLink}
Share it with colleagues, friends, anyone interested.

Reserve your time slot now:
[Button: "See [EVENT_NAME] Schedule"]

See you in [CITY]!
The Volaura Team

P.S. Top 10 referrers during [EVENT_NAME] get a special "[EVENT_NAME] Ambassador" badge.
```

---

### 1.4 Printed Collateral

**Inventory:**

1. **QR Code Posters** (200 units)
   - Locations: Outside venue, session rooms, break areas
   - Design: Large QR code → `volaura.com/join/{qr_tracking_id}`
   - Text: "Get Verified at Volaura → Scan to join"
   - Volaura + event logos

2. **Mini Flyers** (5,000 units)
   - Size: A6 (4.1" x 5.8")
   - Design: One side = AURA score example, other side = QR code
   - Include: "15 min. Completely free. volaura.com/{event-slug}"

3. **Table Tents** (30 units, for booth)
   - Fold-out cardstock: "Sign up here" + QR code
   - Leaderboard display ads

4. **Badge Stickers** (Printed on-demand)
   - Design: Volaura badge tier (Bronze/Silver/Gold/Platinum)
   - Text: Name, AURA score, badge tier
   - For top scorers to wear at event

---

## Phase 2: On-Site Strategy (multi-day event)

Event: [EVENT_DATES] | Venue: [VENUE_NAME]

### 2.1 Booth Layout & Experience

**Location:** [BOOTH_LOCATION] (high foot traffic area if possible)

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
- Bilingual support (local language + English minimum)

**Design Aesthetic:**
- Volaura brand colors (blue, white, light gray)
- Event co-branding (official logo displayed)
- Modern, tech-forward (not cluttered)
- Inviting (comfortable seating for waiting)

---

### 2.2 Assessment Optimization for High-Volume Events

**Challenge:** 500+ people, potential 5,000+ foot traffic, unreliable connectivity

**Solution: Quick Mode Assessment**

Standard assessment: 40 questions (20 min)
Event Quick Mode: 20 questions (10 min)
- Reduce questions per competency from 5 to 2-3
- Fewer options for some questions (faster responses)
- Same scoring logic (no compression of results)

**Offline-First Strategy**

1. **Pre-download questions:** At startup, cache all 20 Quick Mode questions + media locally
2. **Answer locally:** All user interactions happen in-browser (no network calls)
3. **Batch sync:** After completion, sync responses to backend when connectivity returns
4. **Fallback:** If offline assessment can't sync within 1 hour, queue for later evaluation

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
2. Filter toggles (local city only, current day only, event attendees)
3. Real-time animation (scores update with Supabase Realtime)
4. Scroll through names, scores, badges

**Design:**
```
┌─────────────────────────────────────────┐
│  🏆 AURA Leaderboard - [EVENT_NAME] 🏆 │
├─────────────────────────────────────────┤
│ #1  Fatima M.     95 AURA [PLATINUM]    │
│ #2  Ahmed K.      91 AURA [PLATINUM]    │
│ #3  Leila H.      88 AURA [GOLD]        │
│ ...                                     │
│ #47 Sarah T.      72 AURA [SILVER]      │
├─────────────────────────────────────────┤
│ Filters: [Global] [Local] [Today]       │
│ Last updated: 2 minutes ago              │
└─────────────────────────────────────────┘
```

**Implementation:**
- Supabase Realtime subscription to `aura_scores` table
- Recharts line chart for real-time updates
- Next.js component: `components/features/LiveLeaderboard.tsx`

---

### 2.4 Photo Booth Integration

**Purpose:** Gamify the experience, drive social shares

**Setup:**
- iPad/tablet with photo capture + badge overlay
- Printed props (AURA badges, event signage)
- Backdrop with event + Volaura branding

**Mechanics:**
1. Volunteer poses with badge/prop
2. Photo taken with iPad
3. Real-time badge overlay added (badge icon + score)
4. Social share prompt: "Share your AURA moment"
5. Link includes referral code: `instagram.com/share?url=volaura.com/u/{username}?ref={code}`

**Implementation:**
- Web app using Canvas or FFmpeg to overlay badge
- One-tap social share (via Web Intent API)
- Store photos in Supabase Storage if permission granted

---

### 2.5 Physical Badges (Top Scorers)

**Purpose:** Tangible reward, drives competition

**When:** End of each day, print badges for top 10 daily scorers

**Design:**
- Small sticker badge (2" x 2")
- Format: "[#{Rank}] {Name} | {Score} AURA | {Tier}"
- Example: "#3 Leila | 88 AURA | GOLD"
- Volaura logo + event logo

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

**Goal:** Identify volunteer organizations for [[ORG-ACQUISITION]] pipeline

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

**Adjust these guidelines by event length and expected traffic:**

#### Opening Day: Soft Launch, Awareness Building
- **Setup:** 1 hour before official opening
- **Hours:** Full venue hours
- **Focus:** Foot traffic, signups, word-of-mouth
- **Staffing:** 2 people
- **Goal:** 150 signups, 80 assessments
- **Daily Email:** "[EVENT_NAME] opened! See live leaderboard."

#### Mid-Event Days: Peak Engagement, Competitive Energy
- **Hours:** Full venue hours
- **Focus:** Leaderboard updates, referrals, org meetings
- **Staffing:** 2-3 people (busiest day expected here)
- **Goal:** 200 signups, 120 assessments
- **Hourly Update:** Announce top 10 daily scorers on loudspeaker/display
- **Giveaway:** Every 2 hours, raffle 1 free Volaura premium feature (future value)
- **Livestream:** 30-min social media live tour of booth

#### Final Day: Finale, Celebration, Post-Event Push
- **Hours:** Venue closing hours
- **Focus:** Last-minute signups, ceremony for top performers
- **Staffing:** 2 people
- **Goal:** 150 signups, 100 assessments
- **Closing Ceremony:** Announce event top performers, give printed badges
- **Post-Event Email Send:** Immediate (within 2 hours) to all event participants

---

## Phase 3: Post-Event Follow-Up (1 month)

### 3.1 Immediate Email Blitz (Days 1-3)

**To all event participants who signed up:**

**Day 0 (same day):** "Thank you for [EVENT_NAME]"
```
Subject: "You were amazing at [EVENT_NAME]. Here's what's next."

Body:
- Thank you for attending
- Recap: {X} volunteers verified, {Y} new connections made
- Your score: {Score} | {Tier}
- CTA: "View your profile"
- Social: "Share what you accomplished"
```

**Day 1:** "Your AURA journey doesn't end here"
```
Subject: "Keep the momentum. Volunteer now."

Body:
- Highlight: "250 assessments completed at [EVENT_NAME]"
- Next step: Volunteer opportunities matching your competencies
- Featured: "3 volunteer openings this month where your skills matter"
- CTA: "See opportunities near you"
```

**Day 3:** Peer re-engagement
```
Subject: "Your friends from [EVENT_NAME] are already active"

Body:
- Social proof: "15 volunteers from the event have already shared"
- Leaderboard update: "You rank #{rank} on the [EVENT_NAME] leaderboard"
- CTA: "View leaderboard" + "Invite your event friends"
```

---

### 3.2 Referral Push (Week 1-2)

**Incentive:** "Refer [EVENT_NAME] friends and both get bonus AURA"

**Email (Week 1):**
```
Subject: "Bring your [EVENT_NAME] friends to Volaura and earn rewards"

Copy:
- "Remember {Friend}'s name from the booth? Invite them."
- Referral link: {PersonalReferralLink}
- Bonus: "+2 AURA for each friend who assesses"
- Leaderboard: "Top referrers this month get featured"
- CTA: "Invite friends"
```

**In-App Notification:**
- "You can earn +20 AURA by referring your [EVENT_NAME] network"
- Share button pre-filled with referral link

---

### 3.3 Highlight Top Performers (Week 2-3)

**Email: "Meet [EVENT_NAME]'s AURA Stars"**

**Content:**
- Top 5 scorers: photos + profiles
- Most improved: story of growth
- Most referrals: community builder highlight
- Featured on: Volaura blog, social media, in-app

**Distribution:**
- Email to all event participants
- LinkedIn post from company account
- Instagram post + stories
- Blog post: "Lessons from 500 [EVENT_NAME] Volunteers"

---

### 3.4 Event Tracking for [[ORG-ACQUISITION]]

**Immediate (Day 1):**
- Follow up with all org reps who visited booth
- Email: "Thanks for exploring Volaura at [EVENT_NAME]"
- Offer: "Free tier access for your next event"
- Calendar invite: 15-min onboarding call

**Week 2:**
- Send case study: "How [EVENT_NAME] used Volaura to verify volunteers"
- Data: {X} volunteers, {Y} opportunities, {Z} hours saved on vetting

**Month 1:**
- Check-in: "Ready to launch your first event on Volaura?"

---

### 3.5 Badge & Leaderboard Persistence

**Event Attendee Badge:** Permanent on profiles
- All users who assessed during event get special badge: "✓ [EVENT_NAME] Verified"
- Shows on leaderboard for 3 months post-event
- Builds credibility: "Trusted by 500+ [EVENT_NAME] volunteers"

**Event Leaderboard:** Archived
- Freeze leaderboard at end of event
- Make public: `volaura.com/leaderboard/{event-slug}`
- Display: "[EVENT_NAME] Top 50" for historical reference
- Link from blog post

---

## Contingency Plans

### Poor Connectivity
- **Backup:** Bring portable hotspot (Mifi device, 4G router)
- **Offline mode:** Quick assessment pre-cached locally, sync later
- **Communication:** "Connectivity slow? We'll email your results within 1 hour"

### Higher Than Expected Foot Traffic
- **Queue system:** Email reminder with time slot
- **Batch evaluation:** Run LLM evals in scheduled batches (3 per hour)
- **Extend hours:** Stay open until later if needed

### Equipment Failure
- **Backup tablet:** Bring 1 extra iPad
- **Display failure:** Use laptop connected to TV (via HDMI)
- **Printer failure:** Use on-demand badge printing service (e.g., Printful API)

### Low Sign-Up Rate
- **Incentive boost:** Offer "Free premium month for event attendees"
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
