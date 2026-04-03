# Customer Journey Map -- Volaura Platform

**Last Updated:** 2026-04-03
**Source of Truth:** Actual routes from `apps/web/src/app/[locale]/`, persona definitions from `ux-research-agent.md`, AURA weights and badge tiers from `CLAUDE.md`.

---

## How to Read This Document

Each journey maps a persona through every screen they touch. Columns:

| Column | Meaning |
|--------|---------|
| **Step** | Sequential number in the journey |
| **Action** | What the user does |
| **Route / Screen** | Actual app route or external surface |
| **Emotion** | What the user feels (Excited / Curious / Neutral / Confused / Anxious / Frustrated / Bored) |
| **Drop-off Risk** | None / Low / Medium / HIGH / CRITICAL |
| **Drop-off Reason** | Why they might leave at this step |
| **What's Missing** | Feature or UX element that would keep them going |
| **Code Status** | Built / Partial / Stub / Not Built |

---

## Journey 1: LEYLA -- Young Professional, Mobile, Baku

**Persona:** Leyla, 22yo, Baku. Mobile-first (Android). AZ native speaker. Wants to be found by organizations without relying on nepotism. Low trust of unfamiliar platforms. High social-proof sensitivity.

**JTBD:** "Help me get a job at a good company in Baku without nepotism."

**Entry point:** LinkedIn post or Telegram group share from a friend.

| Step | Action | Route / Screen | Emotion | Drop-off Risk | Drop-off Reason | What's Missing | Code Status |
|------|--------|---------------|---------|---------------|-----------------|----------------|-------------|
| 1 | Sees shared link on Telegram/LinkedIn | External (social media) | Curious | Medium | Link looks unfamiliar; no brand recognition in AZ yet | Social proof in link preview (user count, badge image). OG image shows generic text, not a real badge. | Partial -- OG metadata exists but no dynamic card image with score |
| 2 | Lands on invite page | `/{locale}/invite?code=BETA_01` | Curious | Low | Page auto-redirects in 3s; might feel rushed | Countdown text is in English by default; AZ users see i18n key if translation is missing | Built |
| 3 | Lands on landing page (if no invite code) | `/{locale}` (landing) | Neutral | HIGH | No proof this platform is real. No testimonials. No org logos. No user count. Landing shows HeroSection, ImpactTicker, FeaturesGrid, HowItWorks, OrgCta. | Real testimonials from AZ users. Logo strip of organizations that use Volaura. "X users already verified" counter with real data. | Built but lacks social proof |
| 4 | Taps "Get Started" / "Sign Up" | `/{locale}/signup` | Motivated | Medium | Form has 6+ fields visible at once on mobile. Privacy checkbox text is long in AZ. Username pattern allows AZ chars but no real-time uniqueness check. | Real-time username availability check. Reduce visible fields (progressive disclosure). Password strength meter (not just hint text). | Built |
| 5 | Sees celebration screen (#0042) | Signup success state | Excited | None | Celebration is brief (2.2s timeout) -- might miss it on slow connection | Allow user to tap to continue instead of auto-redirect | Built |
| 6 | Onboarding Step 1: Name + Username | `/{locale}/onboarding` (step 1) | Neutral | Low | Username already entered at signup -- feels redundant | Pre-fill from signup (partially done via user_metadata) | Built -- pre-fill works |
| 7 | Onboarding Step 2: Location + Languages | `/{locale}/onboarding` (step 2) | Neutral | Low | Location is free text, not a dropdown. User types "Baki" vs "Baku" -- no normalization. | Location autocomplete (at minimum, AZ city dropdown). Language pre-select based on locale. | Built but no autocomplete |
| 8 | Onboarding Step 3: Pick first competency | `/{locale}/onboarding` (step 3) | Anxious | Medium | 8 competencies shown as a grid. Decision paralysis. "Communication" is pre-selected but user does not know why. No explanation of what each competency measures. | Competency descriptions (1-line each). "Most popular" badge on Communication. Link to info page per competency. | Built but lacks descriptions in grid |
| 9 | Redirected to Assessment page | `/{locale}/assessment?competency=communication` | Motivated | Low | Pre-selected competency carried over. Clear "~5 min" time estimate shown. | None -- this step works well | Built |
| 10 | Starts assessment (taps "Start") | `/{locale}/assessment/{sessionId}` | Focused | Medium | Questions are LLM-evaluated open-text. On mobile, keyboard covers question text. No progress indicator per-question (only total). | Sticky question text above keyboard. Per-question progress bar (e.g., "Question 3 of 8"). Ability to save and resume mid-assessment. | Built but mobile UX needs polish |
| 11 | Completes assessment | `/{locale}/assessment/{sessionId}/complete` | Proud | Low | Score is shown with coaching tips and gaming flag warnings. Crystal earning animation plays. | Immediate share CTA on completion screen (currently only on AURA page). "You beat X% of users" social comparison. | Built |
| 12 | Views AURA score | `/{locale}/aura` | Excited | None | Reveal curtain animation (first time). Animated counter. Badge display with spring animation. Haptic feedback. This is the peak emotional moment. | None -- this is the best screen in the app | Built |
| 13 | Sees share prompt modal | `/{locale}/aura` (modal after 5s) | Motivated | LOW | Share options: Copy Link, Telegram, LinkedIn, TikTok (bio link). But: no image/card to share -- just a URL. | Downloadable badge image (PNG/SVG) for Instagram Stories. Pre-written share text in AZ. WhatsApp share button (major in AZ). | Partial -- buttons exist but no visual asset to share |
| 14 | Shares on LinkedIn | External (LinkedIn) | Proud | Medium | LinkedIn preview shows OG image from `/u/{username}`. But no dynamic score image -- just text metadata. | Dynamic OG image with badge, score, and radar chart. LinkedIn "Add to Profile" deep link for AURA badge. | Not Built -- no dynamic OG image |
| 15 | Public profile is viewed by an org | `/{locale}/u/{username}` | Hopeful | N/A (passive) | Profile shows: name, score, radar chart, badge, languages, location. IntroRequestButton visible to org accounts. ChallengeButton for peer challenges. | Portfolio/project links. "Available for opportunities" status toggle. Notification when profile is viewed. | Built but lacks portfolio section |
| 16 | Org sends intro request | IntroRequestButton on public profile | Excited | LOW | Leyla receives... nothing? No notification system for intro requests is visible in the codebase. | Email/Telegram notification when org requests intro. In-app notification on `/{locale}/notifications`. Response flow (accept/decline). | Stub -- button exists, notification delivery unclear |
| 17 | Returns to improve score | `/{locale}/assessment` | Determined | Medium | Cooldown timer (429 rate limit). Must wait ~30 min between attempts. No guidance on which competency to try next. | "Your weakest competency" recommendation. Cooldown countdown timer (not just error message). Practice mode without score impact. | Partial |

**Critical Drop-off Points:**
1. **Step 3 (Landing page)** -- No social proof kills trust for AZ users. This is the #1 conversion killer.
2. **Step 14 (LinkedIn share)** -- Without a visual badge image, the share has low engagement. Text-only links get 80% less engagement than image posts.
3. **Step 16 (Intro request)** -- If Leyla never gets notified that an org is interested, the entire platform promise breaks.

---

## Journey 2: NIGAR -- HR Manager, Desktop, Organization Account

**Persona:** Nigar, 38yo, HR manager at a 50+ employee corporate in Baku. Desktop user. Searches for verified talent to reduce bad-hire risk. Needs to justify platform adoption to her manager.

**JTBD:** "Help me find candidates who can actually do the job, not just talk well."

**Entry point:** Direct outreach from Volaura team, or sees org CTA on landing page.

| Step | Action | Route / Screen | Emotion | Drop-off Risk | Drop-off Reason | What's Missing | Code Status |
|------|--------|---------------|---------|---------------|-----------------|----------------|-------------|
| 1 | Sees "Find Talent" CTA on landing page | `/{locale}` (OrgCta section) | Curious | Medium | OrgCta section exists but no case studies, no ROI data, no testimonials from other HR managers. | "Companies using Volaura" logo strip. "Reduce bad hires by X%" stat. Demo video or screenshot of search flow. | Built but lacks persuasion content |
| 2 | Clicks "Find Talent" -- goes to signup with org type | `/{locale}/signup?type=organization` | Neutral | HIGH | Signup form is the same as volunteer form. Org type dropdown (NGO/Corporate/Gov/Startup/Academic/Other) but no explanation of what org features include. | Separate org landing page with feature comparison. "What you get" checklist (search, dashboard, saved searches, intro requests). Pricing transparency (free tier vs paid). | Built -- same form, no dedicated org page |
| 3 | Selects org type, fills form | `/{locale}/signup` | Neutral | Medium | No company email validation. Anyone can create an org account with a gmail address. No domain verification. | Company email domain validation (optional). Organization verification badge (later phase). | Built but no org verification |
| 4 | Onboarding (2 steps for orgs -- no competency selection) | `/{locale}/onboarding` (steps 1-2) | Neutral | Low | Org name auto-fills from display_name. Organization row auto-created on finish. | Industry selector. Team size input. "What roles are you hiring for?" to personalize search. | Built |
| 5 | Redirected to My Organization page | `/{locale}/my-organization` | Neutral | HIGH | This page exists but its contents are unclear from the route alone. If it is an empty dashboard with no volunteers, Nigar sees zero value immediately. | Pre-populated "quick start" guide. Sample search results (demo mode). "Invite your first candidate" CTA. | Built but empty-state UX unknown |
| 6 | Navigates to Discover page | `/{locale}/discover` | Hopeful | CRITICAL | Two modes: Browse (all visible volunteers) and Smart Search (semantic/vector search). If talent pool is small (<20 users), browse returns a sparse list. Smart Search requires org account -- returns 403 for volunteers. | Empty-state messaging when pool is small: "X volunteers and growing. Invite candidates to grow the pool." Result count and quality indicators. Filter by competency (not just AURA score and badge tier). | Built |
| 7 | Uses Smart Search with filters | `/{locale}/discover` (search mode) | Focused | HIGH | Semantic search uses pgvector embeddings. Quality depends on volunteer profile completeness (bio, skills). Min-AURA and badge-tier filters exist. But: no competency-specific filter. Cannot search "leadership > 80". | Competency-level filter (e.g., "leadership >= 75"). Sort by specific competency score. Industry/role tags on volunteers. | Built but lacks competency-level filters |
| 8 | Clicks on a volunteer | `/{locale}/u/{username}` | Evaluating | Medium | Public profile shows: AURA score, radar chart, badge, languages, location. But: no work history, no portfolio, no endorsements, no assessment details. | Assessment completion dates. Competency score trend over time. Peer endorsements. "About" section with professional summary. | Built but profile is thin |
| 9 | Clicks "Request Introduction" | IntroRequestButton on profile | Decisive | LOW | Button exists and sends request. But: no confirmation of what happens next. No expected response time. No cost indicator. | Confirmation modal: "We'll notify {name} and connect you within 24h." Email notification to both parties. Request status tracking in org dashboard. | Partial -- button built, follow-through unclear |
| 10 | Goes to Org Volunteers dashboard | `/{locale}/org-volunteers` | Evaluating | Medium | Shows: total assigned, completed, avg AURA, badge distribution, top volunteers, filterable list with search. Saved searches with notification toggle. | Comparison view (side-by-side volunteer profiles). Export to CSV/PDF. Team shortlist feature. Integration with ATS (Applicative Tracking System) via API. | Built |
| 11 | Saves a search with notification | `/{locale}/org-volunteers` (save modal) | Satisfied | Low | Save search modal works. Notification toggle exists. But: notification delivery mechanism unclear -- where do notifications go? | Email digest of new matches. In-app notification center. Webhook/API for ATS integration. | Partial -- save works, delivery unclear |
| 12 | Returns weekly to check new talent | `/{locale}/org-volunteers` or `/{locale}/discover` | Routine | Medium | No re-engagement mechanism. No "new since last visit" indicator. No email summary. | Weekly email: "3 new Gold+ volunteers matched your saved search." Push notification for high-match candidates. | Not Built |

**Critical Drop-off Points:**
1. **Step 2 (Signup)** -- No dedicated org landing page. Nigar sees the same signup form as a 22-year-old volunteer. Zero enterprise credibility signals.
2. **Step 6 (Discover)** -- If the talent pool is small, Nigar sees 5 volunteers and concludes the platform is not ready. She never comes back.
3. **Step 12 (Retention)** -- No re-engagement. Without automated notifications of new matches, Nigar forgets the platform exists after 1 week.

---

## Journey 3: KAMAL -- Senior Professional, Full Profile Builder

**Persona:** Kamal, 34yo, experienced professional in Baku. Wants to be found by companies through verified skills, not just a CV. Will complete all 8 competency assessments to build a comprehensive profile.

**JTBD:** "Show my network that I've been validated by a credible platform."

**Entry point:** Organic search or direct signup.

| Step | Action | Route / Screen | Emotion | Drop-off Risk | Drop-off Reason | What's Missing | Code Status |
|------|--------|---------------|---------|---------------|-----------------|----------------|-------------|
| 1 | Signs up and completes onboarding | `/{locale}/signup` then `/{locale}/onboarding` | Motivated | Low | Same as Leyla journey steps 4-8 | Same issues as Leyla journey | Built |
| 2 | Completes first assessment (communication) | `/{locale}/assessment` then `/{locale}/assessment/{id}` | Focused | Low | ~5 min assessment. LLM-evaluated open-text answers. | None -- first assessment experience is solid | Built |
| 3 | Sees first AURA score | `/{locale}/aura` | Excited | None | Reveal animation, radar chart shows only 1 competency filled. | Radar chart should show "locked" state for uncompleted competencies (currently shows 0). | Built but radar shows 0 instead of "not yet assessed" |
| 4 | Returns for second assessment (reliability) | `/{locale}/assessment` | Determined | Medium | Must manually select next competency. No guidance on optimal order. Cooldown timer if too soon. No "continue your profile" prompt. | Recommended next competency based on AURA weight ("Reliability contributes 15% -- assess next for biggest score boost"). Progress tracker: "2/8 competencies complete." | Built but no guided progression |
| 5 | Completes assessments 3-5 | `/{locale}/assessment` (repeat) | Routine/Bored | HIGH | Assessments 3-5 feel repetitive. Same UI, same flow. No variety. No reward between assessments. Crystal earning is the only feedback. | Milestone celebration at 4/8 ("Halfway there!"). Variety in question format (scenario-based, ranking, etc.). "Streak" for completing assessments on consecutive days. | Partial -- crystals exist but no milestone celebrations |
| 6 | Hits assessment 6 -- fatigue sets in | `/{locale}/assessment` | Bored | HIGH | By assessment 6, Kamal has spent 25-30 minutes on assessments. The interface is identical each time. No new value unlocked between assessments. | Unlock new profile features at milestones (e.g., at 5/8: "Expert Verification" section unlocks). Show profile completeness % on dashboard. Send push notification: "Only 2 more to complete your profile." | Not Built |
| 7 | Completes all 8 assessments | `/{locale}/aura` | Proud | LOW | Full radar chart. All 8 competencies scored. But: no celebration for completing all 8. No special badge or status. | "Full Profile" badge or "8/8 Verified" indicator. Celebration animation. Elevated visibility in search results for orgs. | Not Built |
| 8 | Views complete profile | `/{locale}/profile` | Satisfied | Low | Profile shows: header, impact metrics (events, hours, verified skills), skill chips, expert verifications (empty array), activity timeline (empty array). | ExpertVerifications and ActivityTimeline are rendering empty arrays -- need real data sources. Bio editing. Avatar upload. | Partial -- sections exist but empty |
| 9 | Views public profile | `/{locale}/u/{username}` | Evaluating | Medium | Public profile shows score, radar, badge, languages, location, registration number. But: no way to know if orgs are viewing it. | Profile view counter visible to owner. "Your profile was viewed X times this week." Analytics on which competencies orgs search for most. | Partial -- ProfileViewTracker exists but no owner-facing analytics |
| 10 | Waits to be found by organizations | Dashboard / Notifications | Anxious | CRITICAL | No feedback loop. Kamal completed all 8 assessments and now... nothing happens. No org has contacted him. No indication anyone has seen his profile. Dashboard shows the same cards as day 1. | "Your profile was viewed by 3 organizations this week." Intro request notifications. "Recommended jobs/opportunities" feed. Periodic "Your score improved" or "You moved up in leaderboard" notifications. | Not Built -- no passive feedback loop |
| 11 | Checks leaderboard for validation | `/{locale}/leaderboard` | Competitive | Low | Leaderboard shows weekly/monthly/all-time rankings. Kamal can see his rank. But: leaderboard only shows overall score, not per-competency. | Per-competency leaderboards. "You ranked up" notification. "Challenge a peer" from leaderboard (ChallengeButton exists but only on public profile). | Built |
| 12 | Considers leaving the platform | Mental state | Frustrated | CRITICAL | Without any org contact or visibility proof, Kamal concludes the platform does not deliver on its promise. | Weekly engagement email: "X orgs searched for your skill set. Y profiles were viewed. Keep your score fresh." | Not Built |

**Critical Drop-off Points:**
1. **Steps 5-6 (Assessment fatigue)** -- The core loop (assess, score, repeat) has no variation or milestone rewards. 8 consecutive assessments with identical UX is a retention killer.
2. **Step 10 (Waiting)** -- The platform's core promise is "get found by orgs." Without any signal that orgs are looking, Kamal's trust erodes to zero. This is the existential risk for the product.
3. **Step 12 (Churn)** -- No re-engagement mechanism. No proof of value. Kamal leaves and tells friends the platform does not work.

---

## Journey 4: RAUF -- Brand Builder, Referral Champion

**Persona:** Rauf, 28yo, ambitious mid-career professional in Baku. Building a professional brand. Shares achievements publicly. Motivated by social status and crystal economy. Will refer friends.

**JTBD:** "Show my network that I've been validated by a credible platform. Earn rewards for growing the community."

**Entry point:** Sees a friend's shared AURA badge on LinkedIn or Telegram.

| Step | Action | Route / Screen | Emotion | Drop-off Risk | Drop-off Reason | What's Missing | Code Status |
|------|--------|---------------|---------|---------------|-----------------|----------------|-------------|
| 1 | Sees friend's AURA badge shared on LinkedIn | External (LinkedIn/Telegram) | Curious + Competitive | Medium | Shared link goes to friend's public profile `/u/{username}`. But: no visual badge in share -- just a link with OG text. | Dynamic share image showing badge, score, and radar chart. "I scored 82/100 on Volaura" visual card. | Not Built |
| 2 | Visits friend's public profile | `/{locale}/u/{username}` | Impressed | LOW | Profile shows score, radar, badge tier. CTA at bottom: "Get your AURA score" links to signup. ChallengeButton lets Rauf challenge the friend. | "Beat {friend}'s score" gamification CTA. "X people have scored higher -- can you?" | Built |
| 3 | Taps "Get your AURA score" CTA | `/{locale}/signup` | Motivated | Medium | Standard signup form. No reference to the friend or challenge context. Friend's influence is lost at this point. | Pre-fill referral: "Invited by @{friend}". Referral bonus preview: "You and {friend} earn 50 crystals." | Built but no referral tracking |
| 4 | Completes signup + onboarding + first assessment | Steps 4-11 from Leyla journey | Focused | Medium | Same as Leyla journey | Same issues as Leyla journey | Built |
| 5 | Sees AURA score, wants to share | `/{locale}/aura` | Proud | LOW | Share prompt modal appears after 5s. ShareButtons: Copy Link, Telegram, LinkedIn, TikTok. | WhatsApp button (dominant in AZ). Downloadable badge image. "Share to Instagram Stories" format. Pre-written AZ share text. | Partial |
| 6 | Shares badge on LinkedIn | External (LinkedIn) | Proud | Medium | Shares URL `volaura.app/u/{username}`. LinkedIn renders OG preview. But: generic text, no visual card, low engagement. | Dynamic OG image: badge + score + radar chart rendered as PNG. LinkedIn "Add certification" integration. | Not Built |
| 7 | Shares in Telegram group | External (Telegram) | Social | LOW | Telegram share URL is built: `tg://share?url=...`. Works on mobile. | Telegram bot integration: "@volaura_bot share" command. Inline badge card in Telegram. | Partial -- URL share works, no bot integration for sharing |
| 8 | Wants to refer friends for crystal rewards | Dashboard | Motivated | CRITICAL | No referral system exists. No referral link. No crystal reward for referrals. Dashboard has crystal balance widget but no "Invite friends" CTA. | Referral link generation: `volaura.app/invite?ref={username}`. Crystal reward: 50 crystals per referred user who completes assessment. Referral leaderboard. Progress tracker: "3/5 friends invited -- earn bonus at 5." | Not Built |
| 9 | Checks crystal balance | Dashboard (CrystalBalanceWidget) | Curious | Low | Crystal balance shows total. Earned from assessments. But: no crystal spending mechanism. No crystal store. No crystal transfer. | Crystal store: spend on premium features (detailed analytics, profile boost, additional assessments). Crystal history/log. Crystal earning breakdown. | Partial -- balance shows, no spend mechanism |
| 10 | Explores Tribe feature | Dashboard (TribeCard) | Curious | Medium | TribeCard exists on dashboard. Tribe matching pool and streak tracking exist in backend (`tribe_matching.py`, `tribe_streak_tracker.py`). But: frontend implementation status unclear. | Tribe join flow. Tribe chat or activity feed. Tribe-level challenges. "Your tribe completed X assessments this week" notification. | Partial -- backend exists, frontend is a card stub |
| 11 | Tries to earn more crystals | `/{locale}/assessment` | Motivated | HIGH | Only way to earn crystals is completing assessments. After all 8 are done, no more earning. Cooldown between retakes limits grinding. | Daily challenges: "Answer 3 questions, earn 10 crystals." Referral crystals. Streak bonuses (consecutive-day login). Community challenges: "Your tribe earned 500 crystals this week." | Not Built |
| 12 | Returns weekly to check rank and activity | `/{locale}/dashboard` + `/{locale}/leaderboard` | Routine | HIGH | Dashboard shows same content. Leaderboard position might not change. No new content or challenges. Feed curator skill generates recommendations but they link to existing features. | Weekly challenges. New assessment questions (question bank rotation). "Your friend {name} just scored higher than you" competitive notification. Seasonal competitions. | Partial |

**Critical Drop-off Points:**
1. **Step 8 (Referral)** -- Rauf is the ideal viral growth engine, but there is zero referral infrastructure. No invite link, no reward, no tracking. This is the single biggest growth opportunity left on the table.
2. **Step 11 (Crystal ceiling)** -- Once Rauf completes all assessments, crystal earning stops. The economy has no ongoing source of engagement. Referral rewards and daily challenges are needed.
3. **Step 1 (Share visual)** -- Without a shareable badge image, Rauf's shares generate minimal engagement. Text-only LinkedIn posts get ~80% less reach than image posts.

---

## Cross-Journey Gap Analysis

### Highest-Priority Gaps (affects all personas)

| Gap | Affected Journeys | Impact | Effort Estimate |
|-----|-------------------|--------|-----------------|
| **No dynamic OG image for profile shares** | Leyla (14), Rauf (1, 6) | Kills viral loop. Shares with images get 2-5x more engagement. | Medium -- server-side image generation via `@vercel/og` or Satori |
| **No notification system for intro requests** | Leyla (16), Nigar (9), Kamal (10) | Platform promise ("get found") is broken if users never know an org is interested | Medium -- email + in-app notification |
| **No referral system** | Rauf (8) | Primary viral growth mechanism is entirely missing | Medium -- referral link, tracking, crystal reward |
| **No re-engagement emails** | Nigar (12), Kamal (12), Rauf (12) | Users forget the platform after first session. No reason to return. | Low -- email service + cron job |
| **No profile view analytics for owners** | Kamal (9-10), Leyla (15) | Users cannot prove the platform delivers value. Trust erosion. | Low -- ProfileViewTracker exists, just needs owner-facing UI |

### Medium-Priority Gaps

| Gap | Affected Journeys | Impact |
|-----|-------------------|--------|
| Assessment fatigue (no milestones between assessments) | Kamal (5-6) | 60%+ drop-off predicted between assessment 3 and 8 |
| No competency-level search filters for orgs | Nigar (7) | Orgs cannot find "leadership > 80" -- the core search use case |
| Empty ExpertVerifications and ActivityTimeline on profile | Kamal (8) | Profile looks incomplete even after all 8 assessments |
| No dedicated org landing page | Nigar (2) | Enterprise buyers see consumer signup -- no credibility |
| Radar chart shows 0 for unassessed competencies | Kamal (3) | Misleading -- suggests user scored 0, not "not yet assessed" |

### Lower-Priority Gaps (post-launch)

| Gap | Affected Journeys | Impact |
|-----|-------------------|--------|
| No WhatsApp share button | Leyla (13), Rauf (5) | WhatsApp is dominant messaging app in AZ |
| Location autocomplete | Leyla (7) | Minor UX friction during onboarding |
| Crystal spending mechanism | Rauf (9) | Crystal economy is earn-only -- no utility yet |
| Per-competency leaderboards | Kamal (11) | Nice-to-have competitive feature |
| Tribe frontend implementation | Rauf (10) | Backend ready, frontend is a card component |

---

## Metrics to Track Per Journey

| Metric | Leyla | Nigar | Kamal | Rauf |
|--------|-------|-------|-------|------|
| Signup-to-first-assessment completion | Target: 70% | N/A | Target: 80% | Target: 75% |
| Assessment abandonment rate | Target: <20% | N/A | Target: <15% | Target: <20% |
| Share rate after first AURA reveal | Target: 30% | N/A | Target: 20% | Target: 50% |
| Assessments completed (of 8) | Target: 2+ | N/A | Target: 8 | Target: 3+ |
| D7 retention (return within 7 days) | Target: 40% | Target: 50% | Target: 60% | Target: 50% |
| Intro requests received (30 days) | Target: 1+ | N/A | Target: 2+ | Target: 1+ |
| Searches per session | N/A | Target: 5+ | N/A | N/A |
| Referrals sent | Target: 1 | Target: 0 | Target: 1 | Target: 5+ |
| Org signup conversion from landing | N/A | Target: 15% | N/A | N/A |

---

## Next Actions (Prioritized)

1. **P0: Dynamic OG share image** -- Implement `@vercel/og` for `/u/{username}/card` endpoint. Shows badge, score, radar chart as PNG. Unlocks viral loop for Leyla + Rauf.
2. **P0: Intro request notifications** -- Email + in-app notification when an org requests intro. Without this, the "get found" promise is broken.
3. **P0: Profile view analytics** -- Show profile owners how many views they received this week. Uses existing ProfileViewTracker data.
4. **P1: Referral system** -- Generate referral links, track conversions, reward crystals. Rauf's entire journey depends on this.
5. **P1: Re-engagement emails** -- Weekly digest: "X profile views, Y new org searches matched your skills, Z new volunteers in your tribe."
6. **P1: Assessment milestone celebrations** -- "4/8 done! Halfway to full profile." Reduces Kamal's fatigue drop-off.
7. **P2: Dedicated org landing page** -- Separate from consumer signup. Case studies, ROI data, feature comparison.
8. **P2: Competency-level search filters** -- Let Nigar search "leadership >= 75 AND communication >= 70".
9. **P2: WhatsApp share button** -- Add to ShareButtons component. Dominant in AZ market.
10. **P3: Crystal spending mechanism** -- Profile boost, premium analytics, additional assessment slots.
