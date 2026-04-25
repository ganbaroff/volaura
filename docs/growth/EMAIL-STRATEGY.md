# Email Growth Strategy

## Executive Summary

Email is the primary lifecycle driver for Volaura. Unlike social virality which is passive, email actively nurtures users through critical journeys: signup → assessment → sharing → referral → retention. This strategy uses a combination of transactional emails (triggered by user actions) and lifecycle emails (time-based sequences) to maximize engagement, conversion, and word-of-mouth.

**Provider:** Resend (React Email for templates, best-in-class deliverability)
**Channels:** Transactional via FastAPI, Lifecycle via Supabase Edge Functions + scheduled cron jobs
**Language:** Bilingual (AZ primary, EN secondary) with i18n

---

## Email Infrastructure

### Provider: Resend
- **Why Resend:** Built for developers, React Email for template management, excellent deliverability
- **Authentication:** API key in FastAPI `.env` as `RESEND_API_KEY`
- **Rate Limits:** 100 emails/day free tier; upgrade to paid for >100/day

### Template Structure (React Email)
- **Location:** `apps/api/app/templates/emails/`
- **Pattern:** Each email type gets a component file
  ```
  apps/api/app/templates/emails/
  ├── WelcomeEmail.tsx
  ├── ScoreReadyEmail.tsx
  ├── MagicLinkEmail.tsx
  ├── BadgeChangeEmail.tsx
  ├── layout/
  │   ├── EmailLayout.tsx (header, footer, branding)
  │   └── styles.ts (shared CSS)
  ```
- **i18n:** Each template accepts `locale` prop, uses `t()` for translations
- **Rendering:** Server-side at send time via `render()`

### Delivery Triggers
- **Transactional (Real-Time):**
  - Endpoint: `POST /api/emails/send`
  - Triggered by: user actions (signup, score complete, attestation)
  - FastAPI service: `app.services.email.send_email(template, recipient, data)`
  - Latency: < 1 second

- **Lifecycle (Scheduled):**
  - Trigger: Supabase Cron Extension or pg_cron
  - Query: Find users matching condition (e.g., "signed up 1 day ago, haven't started assessment")
  - Batch send: Query returns users, loop sends via Resend API
  - Frequency: Daily at 2 AM UTC

---

## Transactional Emails

These are high-value, real-time emails triggered immediately by user actions. Open rates: 40%+.

### 1. Welcome Email
**Trigger:** User completes signup (email verified)
**Delay:** Immediate (< 5 seconds)
**Recipient:** New user's email

#### Content Structure
```
Subject (EN): "Welcome to Volaura — Your AURA journey starts now"
Subject (AZ): "Volaura-ya xoş gəldiniz — AURA səyahətiniz başlayır"

Body:
- Header image (Volaura logo + blue gradient)
- Greeting: "Hi {firstName}! 👋"
- Body copy (2-3 sentences):
  "You're now part of a community of verified profiles in Azerbaijan.
   In the next 15 minutes, take your AURA assessment to discover your
   skills. Organizations are looking for people like you."
- CTA button: "Start Your Assessment" (link to `/app/assessment`)
- Secondary: Referral link callout:
  "Know someone great? Share your link and get priority in the queue:
   {personalized_referral_link}"
- Footer: Social proof: "200+ volunteers already verified"
```

#### Template Component
```typescript
// apps/api/app/templates/emails/WelcomeEmail.tsx
import { initTranslations } from "@/app/i18n"; // Adapted for API context

export async function WelcomeEmail({
  firstName,
  email,
  referralLink,
  locale = "az"
}) {
  const { t } = await initTranslations(locale, ["email"]);

  return (
    <EmailLayout>
      <h1>{t("welcome.greeting", { name: firstName })}</h1>
      <p>{t("welcome.intro")}</p>
      <Button href={`${FRONTEND_URL}/app/assessment`}>
        {t("welcome.cta")}
      </Button>
      <hr />
      <p>{t("welcome.referral.label")}</p>
      <p><a href={referralLink}>{referralLink}</a></p>
      <p>{t("welcome.social_proof")}</p>
    </EmailLayout>
  );
}
```

#### Metrics
- **Open Rate Target:** 50-60% (transactional, warm)
- **Click-Through Rate:** 20-25% (assessment start)
- **Success Measure:** % of welcomes that lead to assessment start within 7 days

---

### 2. Magic Link Email
**Trigger:** User requests passwordless login
**Delay:** Immediate (< 2 seconds)
**Recipient:** User's email

#### Content Structure
```
Subject (EN): "Your Volaura login link"
Subject (AZ): "Volaura giriş bağlantınız"

Body:
- Simple, minimal design
- "Click the link below to log in to your Volaura account"
- Big blue button: "Log In" (with token in href)
- Expiry note: "This link expires in 10 minutes"
- Footer: "Didn't request this? You can safely ignore it."
```

#### Implementation
- Generate token: `secrets.token_urlsafe(32)` in Python
- Store in Supabase: `INSERT INTO magic_links (token, user_id, expires_at) VALUES (...)`
- Email link: `{FRONTEND_URL}/auth/magic-link?token={token}`
- Cleanup: Cron job deletes expired tokens daily

#### Metrics
- **Open Rate:** 70%+ (urgent)
- **Click Rate:** 80%+ (high intent)

---

### 3. Score Ready Email
**Trigger:** Assessment evaluation complete (LLM scores submitted)
**Delay:** Immediate (< 5 seconds)
**Recipient:** User who completed assessment

#### Content Structure
```
Subject (EN): "Your AURA Score is ready! 🎯"
Subject (AZ): "Sizin AURA Skozu hazırdır! 🎯"

Body:
- Large, prominent score display: "{Score}/100"
- Badge tier name with icon: "Silver Badge"
- Breakdown: Radar chart or competency bar chart
- Key stats: "Leadership: 85 | Communication: 78 | Reliability: 82"
- Main CTA: "View Your Full Profile" (link to `/app/profile`)
- Share section with icons:
  "Share your achievement and inspire your network:"
  [LinkedIn button] [Instagram button] [WhatsApp button] [Copy Link button]
- Secondary: "Next steps: Complete one event to boost your score"
- Footer: Organization call-in
  "Organizations are looking for volunteers like you.
   Browse jobs → Organizations will be notified you're available"
```

#### Design Notes
- This email has highest visual impact—use branded badge images
- Include static image of badge/radar chart (PNG) so non-image email clients still see value
- Share buttons use deep links (e.g., `whatsapp://send?text=Check+my+AURA+Score...`)

#### Metrics
- **Open Rate Target:** 75%+ (peak interest moment)
- **Click Rate:** 30-40% (to profile or share)
- **Share Rate:** 25-30% of opens (critical for viral loop)

---

### 4. Badge Change Email (Upgrade)
**Trigger:** User's AURA score crosses tier threshold (Bronze→Silver, etc.)
**Delay:** Immediate
**Recipient:** User

#### Content Structure
```
Subject (EN): "Congratulations! You earned a Silver Badge 🏆"
Subject (AZ): "Təbriklər! Gümüş Nişanı qazandınız 🏆"

Body:
- Celebration emoji and headline
- Show old badge vs. new badge side-by-side
- Stat: "You went from Bronze (40) to Silver (75) AURA"
- Explanation: "Your reliability and leadership have improved.
   Organizations now see you as a trusted volunteer."
- Main CTA: "Share Your Progress" (pre-filled share modal)
- Secondary: "See updated profile"
- Peer pressure: "Only 15% of volunteers have reached Silver tier"
```

#### Trigger Logic
```python
# In assessment submission service
async def evaluate_assessment(user_id, answers):
    # ... LLM evaluation ...
    old_score = await get_user_aura_score(user_id)
    new_score = calculate_aura(evaluation)
    old_tier = get_tier(old_score)
    new_tier = get_tier(new_score)

    if new_tier > old_tier:
        await send_badge_upgrade_email(user_id, old_tier, new_tier)
```

#### Metrics
- **Open Rate:** 60%+ (personal achievement)
- **Share Rate:** 35%+ (ego-driven sharing)

---

### 5. Event Reminder Email
**Trigger:** 24 hours before registered event
**Delay:** Scheduled (4 PM user's local time, day before)
**Recipient:** Registered volunteer

#### Content Structure
```
Subject (EN): "Reminder: {Event Name} is tomorrow"
Subject (AZ): "{Event Name} yarın keçiriləcək"

Body:
- Event name and time
- Location (with map link)
- "What to bring" checklist (if provided by org)
- Volunteer's role summary
- CTA: "See Event Details" (link to event page)
- Secondary: "Can't make it? Let the organizer know ASAP"
```

#### Implementation
- Cron job daily at 12 AM UTC
- Query: `SELECT user_id, event_id FROM registrations WHERE event_date = NOW() + INTERVAL 1 DAY`
- Send email per user
- Store in `event_reminders` table to avoid duplicates

#### Metrics
- **Open Rate:** 50-60% (reminder context)
- **Click Rate:** 15-20%
- **Success:** Reduced no-show rate by 10%

---

### 6. Organization Attestation Email
**Trigger:** Organization completes attestation for volunteer
**Delay:** Immediate (< 5 seconds)
**Recipient:** Volunteer

#### Content Structure
```
Subject (EN): "{Org Name} verified your {Competency}!"
Subject (AZ): "{Org Name} sizin {Competency} bacarığını təsdiq etdi!"

Body:
- Organization logo
- "Great news! {Org Name} verified your skills in:"
- List verified competencies (badges)
- "This improves your AURA score. See how:"
- AURA impact: "Your score increased from 78 to 82"
- CTA: "View Your Profile" (with org badge highlighted)
- Secondary: "Thanks to {Org Name} for recognizing your work"
```

#### Metrics
- **Open Rate:** 85%+ (external validation, highest emotional impact)
- **Click Rate:** 40%+ (users want to see new badge)

---

### 7. Peer Verification Request Email
**Trigger:** Another volunteer requests peer verification
**Delay:** Immediate (< 5 seconds)
**Recipient:** Volunteer being asked to verify

#### Content Structure
```
Subject (EN): "{Name} asked you to verify their skills"
Subject (AZ): "{Name} sizə onların bacarıqlarını təsdiq etməyi xahiş edir"

Body:
- "{Name} would like you to verify they have strong {Competency}."
- "You've worked together before. Your opinion counts."
- CTA button: "Review & Verify" (or "Not Yet")
- What happens: "Your verification will be added to their profile
   and help them gain recognition."
- Footer: Privacy note: "Your review is visible to {Name} only."
```

#### Implementation
- Trigger: `POST /api/verifications/request-peer-verification`
- Store in `peer_verifications` table with status `pending`
- Email link goes to: `/app/verify/{verification_id}`
- CTA options: "Yes, verify" (+1 to their competency), "Not yet", "Report"

#### Metrics
- **Open Rate:** 55-65% (personal request)
- **Response Rate:** 40-50% (action required)

---

## Lifecycle Emails

These are time-based emails sent at key points in the user journey. They nurture engagement and prevent churn.

### Timeline Overview
```
Day 0  → Welcome + Start Assessment
Day 1  → (if no assessment) Nudge: "Your AURA score is waiting"
Day 3  → (if started, not done) "You're almost done"
Day 7  → (if assessed) "Share your badge and get noticed"
Day 14 → "Events near you match your competencies"
Day 30 → Monthly update: leaderboard position, events attended
Day 60 → Re-engagement: "We miss you"
Day 90 → "Time to retake your assessment—show how you've grown"
```

### Day 0: Welcome Email
See [[#1. Welcome Email]]

---

### Day 1: Assessment Nudge (If No Assessment)
**Trigger:** Cron job at 2 AM UTC, query users with `created_at = NOW() - INTERVAL 1 DAY` and no `assessment_sessions`
**Recipient:** Users who signed up yesterday but haven't started assessment
**Open Rate Target:** 35-45%

#### Content
```
Subject (EN): "Your AURA score is waiting—takes just 15 minutes ⏱️"
Subject (AZ): "Sizin AURA Skozu gözləyir—cəmi 15 dəqiqə çəkir ⏱️"

Body:
- Brief reminder: "You signed up for Volaura yesterday.
   Now let's find out what you're great at."
- Teaser: "1,234 volunteers have already completed it.
   See where you rank."
- CTA: "Start Assessment"
- FAQ section:
  Q: How long does it take? A: 15-20 minutes
  Q: What questions will I be asked? A: On leadership, communication, reliability, etc.
  Q: Is it graded? A: No, it's a discovery tool for you
```

---

### Day 3: Almost Done (If Started But Not Completed)
**Trigger:** Cron job, query users with `assessment_sessions` where `status = 'in_progress'` and `created_at < NOW() - INTERVAL 3 DAYS`
**Recipient:** Users who started but abandoned
**Open Rate Target:** 40-50%

#### Content
```
Subject (EN): "You're {X} questions away from your AURA Score"
Subject (AZ): "Siz {X} suala qalan olmusunuz"

Body:
- Encouragement: "You've already answered {25/40} questions.
   Don't lose your progress!"
- Show score preview: "Based on what we know so far,
   you're on track for a {estimated_score}"
- Time estimate: "{remaining} questions, about {time} minutes left"
- CTA: "Finish Now" (resume assessment)
- Reassurance: "No pressure. You can save and come back anytime."
```

---

### Day 7: Share & Inspire (If Assessed)
**Trigger:** Cron job, query users with completed assessment and `created_at = NOW() - INTERVAL 7 DAYS`
**Recipient:** Users who assessed but haven't shared
**Open Rate Target:** 35-45%

#### Content
```
Subject (EN): "Your AURA badge is turning heads. Time to share."
Subject (AZ): "Sizin AURA nişanı diqqət çəkir. Indi bölüşün."

Body:
- FOMO: "125 people in Baku just shared their AURA.
   Be part of the movement."
- Why share: "Help friends discover their strengths.
   Recommend Volaura to your network."
- Referral angle: "When you share, friends who sign up
   get priority in the assessment queue."
- CTA: "Share Your Badge Now"
- Alternative: "Or explore events where your skills matter"
```

---

### Day 14: Local Events
**Trigger:** Cron job, query users with completed assessment
**Recipient:** All assessed users
**Open Rate Target:** 25-35%

#### Content
```
Subject (EN): "3 volunteer events near you match your skills"
Subject (AZ): "Sizin bacarıqlarınıza uyğun 3 könüllülük tədbirləri"

Body:
- Personalized: "Based on your {Leadership, Communication} scores,
   these organizations need you:"
- Event cards (3 events):
  1. Major Event — "Seeking session facilitators" — May 15
  2. Baku NGO Forum — "Event coordination help" — April 20
  3. Community Cleanup — "Leadership positions" — Ongoing
- CTA per event: "View & Register"
- Secondary: "See all events in your area"
```

---

### Day 30: Monthly AURA Update
**Trigger:** Cron job, query users active in the last 30 days
**Recipient:** Active users
**Open Rate Target:** 30-40%

#### Content
```
Subject (EN): "Your March AURA Update: You ranked #47 in Baku 📊"
Subject (AZ): "Sizin Mart AURA Yeniləmesi: Bakıda #47 sırada 📊"

Body:
- Leaderboard position: "You've moved up 12 spots this month!"
- Events attended: "You volunteered at 2 events (5 AURA points)"
- Competency growth: Bar chart showing improvements
- Peer comparison: "75% of volunteers in your tier have attended fewer events"
- Featured achievers: "Meet this month's AURA Stars"
- CTA: "View Your Full Stats" (link to dashboard)
```

---

### Day 60: Re-Engagement (If No Action)
**Trigger:** Cron job, query users where `last_action_date < NOW() - INTERVAL 60 DAYS`
**Recipient:** Inactive users
**Open Rate Target:** 15-25% (lower—re-engagement is harder)

#### Content
```
Subject (EN): "We miss you, {firstName}. What's new on Volaura?"
Subject (AZ): "{firstName}, biz səni əskik edirik. Volaura-da yeniliklər nədir?"

Body:
- Personal touch: "It's been 2 months since your last login.
   A lot has changed."
- What's new:
  • 500+ new verified profiles joined
  • Streak system launched (earn badges for consistency)
  • Organizations now verifying skills (get verified by pros)
- Social proof: "Your friends Sarah and Ahmed have been active"
- CTA: "See What You've Missed" (login link)
- Exit: "Prefer not to hear from us? Unsubscribe below."
```

---

### Day 90: Reassessment Prompt
**Trigger:** Cron job, query users where `last_assessment_date = NOW() - INTERVAL 90 DAYS`
**Recipient:** Users who assessed 3 months ago
**Open Rate Target:** 25-35%

#### Content
```
Subject (EN): "You've grown. Time to retake your AURA assessment."
Subject (AZ): "Siz böyümüsünüz. AURA qiymətləndirməsini yenidən keçirin."

Body:
- Growth narrative: "3 months ago, you scored 72. You've volunteered
   at 3 events, learned new skills. Your AURA might have improved."
- Incentive: "Retake the assessment in 10 minutes.
   See if you've earned a higher tier."
- What changes: "Your Leadership score jumped from 75 to 82
   (based on event feedback)."
- CTA: "Retake Assessment"
- Secondary: "See your peer's growth" (link to leaderboard)
```

---

## Email Copy Guidelines

### Tone & Voice
- **English:** Friendly, encouraging, action-oriented
- **Azerbaijani:** Same, but culturally aware (use informal second person in appropriate contexts)
- **Avoid:** Corporate jargon, unclear acronyms, overly long sentences
- **Do:** Use names, include specific numbers, celebrate progress

### CTA Button Best Practices
- **One primary CTA per email** (most emails have 1 button)
- **Button text:** Action-oriented verb (Start, View, Share, Register, Verify)
- **Size:** Large, mobile-friendly (minimum 44x44 px)
- **Color:** Volaura brand color (blue)
- **Link tracking:** All links include UTM parameters:
  ```
  ?utm_source=email&utm_medium=lifecycle&utm_campaign=day1_nudge
  ```

### Personalization
- Always use first name: "Hi {firstName}!"
- Reference their score/tier: "You earned Silver"
- Location: "Events near you in {city}"
- Competencies: "Your Leadership skills" (not generic)
- Social proof: "125 volunteers in Baku"

### Accessibility
- Alt text on all images
- Sufficient color contrast (WCAG AA)
- Clear hierarchy with headings
- Short paragraphs (2-3 sentences max)
- Mobile-responsive (Resend handles this)

---

## List Management & Compliance

### Opt-In & Consent
- **Signup:** Explicit checkbox "Receive AURA updates and event notifications"
- **Magic link login:** Implicit consent (already subscribed)
- **Quarterly re-confirm:** Send "We still have your email, do you want updates?" (GDPR/local law compliance)

### Unsubscribe
- **All emails:** Footer link to unsubscribe preferences
- **Granular Control:** Users can unsubscribe from:
  - Lifecycle emails only (keep transactional)
  - Event reminders only
  - Weekly summaries only
  - All non-essential
- **Transactional emails** (score ready, attestation, magic link) cannot be unsubscribed from

### Handling Invalid Emails
- **Bounce Handling:** Resend API returns bounce status
- **Hard bounce** (invalid email): Mark `profiles.email_bounced = true`, set email verification to false
- **Soft bounce** (temporary): Retry 3 times over 7 days, then mark bounced
- **Complaint** (spam report): Unsubscribe user entirely

---

## Analytics & Optimization

### Key Metrics by Email Type

| Email | Send Volume | Open Rate Target | CTR Target | Conversion Target |
|-------|------------|-----------------|------------|------------------|
| Welcome | 100% of signups | 50% | 20% | 40% start assessment in 7d |
| Magic Link | On demand | 70% | 80% | 90% login |
| Score Ready | 100% of assessments | 75% | 35% | 25% share |
| Badge Upgrade | 20-30% of assessments | 60% | 40% | 30% share |
| Event Reminder | 100% of registrants | 50% | 15% | 10% show up |
| Attestation | 100% events | 85% | 40% | 50% view profile |
| Day 1 Nudge | 100% who don't assess | 40% | 18% | 25% start assessment |
| Day 7 Share | 80% of assessed | 40% | 25% | 20% share |
| Day 30 Update | 100% active | 35% | 20% | 15% open dashboard |

### Dashboard Metrics
- **Segment Performance:** Breakdown by cohort (signup date, event attendance, score tier)
- **Funnel Analysis:** Email sent → opened → clicked → action taken (signup/assessment/share)
- **A/B Tests:** Subject line variants, CTA button copy, sending time
- **Deliverability:** Bounce rate, complaint rate, inbox placement

### Testing Plan

**Phase 1 (Weeks 1-2):**
- A/B test Welcome subject lines (3 variants)
- A/B test Score Ready CTA button copy ("Share Now" vs. "Show Your Score")

**Phase 2 (Weeks 3-4):**
- A/B test Day 7 sending time (3 PM vs. 6 PM user local time)
- Test email design (minimalist vs. image-heavy)

**Phase 3 (Month 2+):**
- Personalization tests (first name vs. anonymous)
- Referral incentive messaging tests

---

## Implementation Roadmap

### Phase 1 (Weeks 1-2, Pre-Launch Event)
- [ ] Set up Resend account + FastAPI integration
- [ ] Build email templates: Welcome, Magic Link, Score Ready
- [ ] Implement transactional sending service: `app.services.email`
- [ ] Test deliverability in staging
- [ ] Deploy to production

### Phase 2 (Weeks 3-4, Pre-Launch Event)
- [ ] Add lifecycle email cron jobs (Day 1, Day 7, Day 30)
- [ ] Build badge upgrade notification email
- [ ] Implement list management (unsubscribe, preferences)
- [ ] Set up analytics dashboard (Resend API)
- [ ] A/B test first variants

### Phase 3 (Week 5, at Launch Event)
- [ ] Event reminder emails + registration
- [ ] Peer verification request emails
- [ ] Launch event attendee post-event emails
- [ ] Deploy event-specific subject lines

### Phase 4 (Weeks 6+, Post-Launch Event)
- [ ] Day 60 re-engagement email
- [ ] Day 90 reassessment prompt
- [ ] Attestation email
- [ ] Quarterly preference re-confirm (compliance)

---

## Technical Reference

### Resend Integration (FastAPI)
```python
# app/services/email.py
from resend import Resend
from app.templates.emails import WelcomeEmail, ScoreReadyEmail

class EmailService:
    def __init__(self, api_key: str):
        self.client = Resend(api_key=api_key)

    async def send_welcome(self, user: User, locale: str = "az"):
        html = await render(
            WelcomeEmail(
                firstName=user.first_name,
                referralLink=f"volaura.com/join/{user.referral_code}",
                locale=locale
            )
        )

        response = self.client.emails.send({
            "from": "Volaura <hello@volaura.com>",
            "to": user.email,
            "subject": t("email.welcome.subject", locale),
            "html": html,
        })

        # Log in database
        await db.table("email_logs").insert({
            "user_id": user.id,
            "email_type": "welcome",
            "resend_id": response.id,
            "sent_at": datetime.now(timezone.utc),
        })

        return response

# Usage in route
@router.post("/auth/signup")
async def signup(user_data: SignupRequest, email_service: EmailService = Depends()):
    user = await create_user(user_data)
    await email_service.send_welcome(user, locale="az")
    return {"user_id": user.id}
```

### Cron Job (Supabase Edge Function)
```python
# Supabase Edge Function: send_day1_nudge
import asyncio
from supabase_async import acreate_client
from app.services.email import EmailService

async def send_day1_nudge():
    supabase = await acreate_client(URL, KEY)

    # Find users who signed up yesterday, no assessment
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    users = await supabase.table("profiles") \
        .select("id, email, first_name, locale") \
        .eq("created_at::date", yesterday) \
        .execute()

    # Filter: no assessment_sessions
    for user in users.data:
        sessions = await supabase.table("assessment_sessions") \
            .select("*") \
            .eq("volunteer_id", user.id) \
            .execute()

        if len(sessions.data) == 0:
            email_service = EmailService(api_key=settings.resend_api_key)
            await email_service.send_nudge(user, locale=user.locale or "az")

# Deploy: `supabase functions deploy send_day1_nudge`
# Schedule: `supabase cron deploy send_day1_nudge --cron="0 2 * * *"`
```

---

## Success Metrics & Targets

**By Month 2 Post-Launch:**
- 95%+ email deliverability rate
- 45%+ open rate on transactional emails
- 25%+ conversion from share email → actual shares
- 20%+ new signups from email campaigns
- <1% unsubscribe rate on lifecycle emails
- 40% of assessed users have shared at least once (via email prompt)

**By Month 6:**
- K-factor contribution from email: 0.3+ (30% of viral growth from email nurture)
- Referral-driven signups: 25%+
- Email-driven event attendance: 40%+

---

## Cross-References

- [[VIRAL-LOOP]] — Email triggers sharing; sharing drives viral loop
- Launch event strategy — Event-specific email campaigns
- [[ORG-ACQUISITION]] — Organization outreach emails (separate cadence)
- [[CLAUDE.md]] — Tech stack: FastAPI, Resend, i18n integration

