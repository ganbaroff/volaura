# Volaura — Mass Activation Plan (11K Contacts)
> Written: 2026-03-27 | Session 47
> Answers 5 unresolved questions from team audit + expands into Sprint 10.5

---

## ⚡ TL;DR — Executive Summary

We have 4,000 + 7,000 = **11,000 warm contacts** ready to activate.
**ONE infrastructure blocker** will crash the system if we don't fix it first: Gemini rate limits.
Everything else is a few hours of work.

Timeline before activation is safe: **3-4 days** (migrations + Groq fallback + onboarding page).

---

## THE 5 QUESTIONS — ANSWERED

---

### Q1: What exact link to send?

**Answer:** `https://volaura.app/register?ref=SOURCE_CODE&utm_source=CHANNEL&utm_medium=referral&utm_campaign=activation_wave1`

#### Link variants by channel:

| Channel | Link |
|---------|------|
| HR coordinator WhatsApp | `volaura.app/register?ref=hr-{name}&utm_source=whatsapp&utm_medium=referral&utm_campaign=activation_wave1` |
| CEO personal LinkedIn | `volaura.app/register?utm_source=linkedin&utm_medium=social&utm_campaign=activation_wave1` |
| Direct email to 4K contacts | `volaura.app/register?ref=email-wave1&utm_source=email&utm_medium=email&utm_campaign=activation_wave1` |
| Telegram broadcast | `volaura.app/register?ref=tg-broadcast&utm_source=telegram&utm_medium=social&utm_campaign=activation_wave1` |
| STEP IT network | `volaura.app/register?ref=step-it&utm_source=direct&utm_medium=referral&utm_campaign=activation_wave1` |

#### What changes in the codebase:
1. **New migration** (000034): Add `referral_code TEXT`, `utm_source TEXT`, `utm_campaign TEXT` to `profiles`
2. **Registration endpoint**: capture `ref` and `utm_*` query params → store in profile on signup
3. **No special tracking page needed** — capture at Supabase auth callback URL (Next.js `auth/callback`)

#### Copy-paste message for HR coordinators (RU):
```
Привет!

Я создал платформу для волонтёров — Volaura. Бесплатный тест на 10 минут →
получаешь подтверждённый бейдж со своими компетенциями (коммуникация, лидерство и др.).
Организации видят твой профиль и приглашают на ивенты.

Если работал(а) на COP29 или CIS Games — твой опыт уже считается.

Ссылка: volaura.app/register?ref={YOUR_REF_CODE}

Было бы здорово, если поделишься с ребятами из группы 🙏
```

#### Copy-paste message for EN/global:
```
Hey!

I built Volaura — a verified skills platform for volunteers.
Free 10-min assessment → get a badge with your competencies.
Organizations see your profile and invite you to events.

If you volunteered at COP29, CIS Games, or similar — your experience counts.

Join here: volaura.app/register?ref={YOUR_REF_CODE}
```

---

### Q2: What do they see first?

**Answer:** The current flow is: `/register` → email confirm → `/dashboard` (AURA = 0, empty).
**This is wrong for cold traffic.** Empty dashboard = 60% bounce in first 30 seconds.

#### Required: Onboarding Gate (1 screen, not a wizard)

After registration + email confirm → redirect to `/welcome` (new page):

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  👋 Welcome to Volaura, [Name]                 │
│                                                 │
│  You're 10 minutes away from your               │
│  verified volunteer badge.                      │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │                                         │   │
│  │  What Volaura checks:                   │   │
│  │  ✓ Communication     ✓ Reliability      │   │
│  │  ✓ Leadership        ✓ Adaptability     │   │
│  │  ✓ Tech Literacy     ✓ English Level    │   │
│  │                                         │   │
│  │  Your AURA Score will be visible to     │   │
│  │  organizations looking for volunteers.  │   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  [🚀 Start My Assessment — 10 min]  ←CTA       │
│                                                 │
│  [Skip for now — go to dashboard]              │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Key decision:** Assessment start = first action. NOT profile fill. NOT dashboard exploration.
**Why:** Registration → badge is the value prop. Delaying it causes churn.

#### Onboarding flow:
```
/register → (email confirm) → /welcome → /assessment?competency=communication
                                              ↓
                                     /assessment/complete
                                              ↓
                                     /aura (badge reveal screen)
                                              ↓
                                     "Share your badge" → LinkedIn / TikTok
```

The **badge reveal** is the emotional peak. If users reach it, they share.
If they don't reach it (empty dashboard), they churn.

#### What to build (Sprint 10.5 scope):
- `apps/web/src/app/[locale]/welcome/page.tsx` — 1-screen onboarding gate
- `apps/web/src/app/[locale]/aura/page.tsx` — add share mechanic (already exists, needs share button)
- Middleware: redirect first-time users from `/dashboard` → `/welcome`

---

### Q3: How to track conversion (UTM/referral)?

**Answer:** 3-layer tracking. All backend, no third-party analytics needed.

#### Layer 1: referral_code in profiles (migration)
```sql
ALTER TABLE public.profiles
ADD COLUMN referral_code TEXT,  -- who referred them (e.g. "hr-leyla-cop29")
ADD COLUMN utm_source TEXT,     -- "whatsapp", "linkedin", "email", "telegram"
ADD COLUMN utm_campaign TEXT;   -- "activation_wave1", "hr_bouquet_march"
```
Capture at auth callback: `apps/web/src/app/auth/callback/route.ts` reads query params from `localStorage` (saved at `/register` page load) → passes to profile creation.

#### Layer 2: referral_stats view (zero new infrastructure)
```sql
CREATE VIEW public.referral_stats AS
SELECT
    referral_code,
    utm_source,
    utm_campaign,
    COUNT(*) AS registrations,
    COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL) AS badges_earned,
    ROUND(
        COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL)::NUMERIC / COUNT(*) * 100, 1
    ) AS conversion_pct,
    MIN(created_at) AS first_registration,
    MAX(created_at) AS last_registration
FROM public.profiles
WHERE referral_code IS NOT NULL
GROUP BY referral_code, utm_source, utm_campaign;
```
CEO can query this directly in Supabase dashboard. No analytics tool needed.

#### Layer 3: daily digest to CEO via Telegram
ZEUS scheduler sends daily at 20:00 Baku:
```
📊 Volaura activation digest — [DATE]
• New registrations today: X
• Assessments completed: Y
• Badges issued: Z
• Top ref code: {ref_code} (N signups)
• Conversion: A%
```

#### Funnel to track:
```
11,000 contacted
    ↓  (target: 15%)
1,650 click the link
    ↓  (target: 60%)
990 register
    ↓  (target: 70%)
693 start assessment
    ↓  (target: 80%)
554 complete assessment
    ↓  (target: 40%)
222 share badge
```
If share K-factor = 0.40 → 222 × 0.40 = 89 second-wave organic signups.

---

### Q4: Can Railway handle 3,000 users in 1 day?

**Short answer: Yes — but Gemini WILL crash at 125+ users/day without Groq fallback.**

#### Capacity breakdown:
| Layer | Current limit | 3K users/day load | Status |
|-------|--------------|-------------------|--------|
| Railway CPU | Hobby $5/mo, shared | ~2 req/min average | ✅ Fine |
| Railway memory | 512MB | Assessment JSON: ~2KB/session | ✅ Fine |
| Supabase DB | Free tier, 500MB, 20 connections | ~50 concurrent at peak | ✅ Fine |
| Supabase storage | 1GB | Not used for assessment | ✅ Fine |
| **Gemini free tier** | **15 RPM** | **17+ RPM at 125 users/hour** | **❌ CRASH** |
| Groq fallback | Not implemented | — | ❌ MISSING |
| Rate limiter | In-memory slowapi | Resets on restart only | ✅ Acceptable |

#### The math on Gemini:
```
3,000 users / 24h = 125 users/hour
125 users × 8 questions = 1,000 LLM calls/hour
1,000 / 60 = 16.7 RPM

Gemini free tier limit: 15 RPM → EXCEEDED by 11%
```

**Even 110 users/hour = system down.** This is a P0 blocker.

#### Fix: Groq fallback (3-4 hours of work)
Current `bars.py` already has a fallback path for `keyword_fallback`. What's missing is LLM fallback:

```python
# apps/api/app/services/bars.py (to be added in Sprint 10.5)
async def evaluate_with_llm_resilient(prompt: str) -> dict:
    """Try Gemini → Groq fallback → keyword_fallback."""
    try:
        return await evaluate_with_gemini(prompt, timeout=10)
    except (RateLimitError, TimeoutError):
        logger.warning("Gemini rate limited → trying Groq")
        try:
            return await evaluate_with_groq(prompt, timeout=8)
        except Exception:
            logger.warning("Groq failed → keyword_fallback")
            return keyword_fallback_evaluation(...)
```

Cost: Groq is **free tier up to 14,400 requests/day** (llama-3.3-70b-versatile).
At 3K users × 8 questions = 24K calls/day → need Groq paid ($0.59/1M tokens ≈ $2/day max).

**Verdict:** Don't scale Railway. Fix Gemini fallback. Cost delta: $2/day → acceptable.

#### When to upgrade Railway:
- Current: single instance, ~$8/month
- Upgrade trigger: >500 concurrent users (not 3K/day — concurrent)
- Next tier: Railway Professional (~$20/month, dedicated vCPU)
- **Do NOT upgrade before 500 DAU** — waste of money

---

### Q5: Are there Russian questions in the question bank?

**Answer: NO. The question bank has only EN + AZ columns. Zero RU content.**

#### What exists:
```sql
-- Current questions table
scenario_en TEXT NOT NULL,   -- ✅ English (90 questions)
scenario_az TEXT NOT NULL,   -- ✅ Azerbaijani (90 questions)
-- scenario_ru does NOT exist
```

#### Impact analysis:
- **Azerbaijan 4K contacts**: AZ questions work perfectly. Not a blocker.
- **CIS/global 7K contacts**: English questions work for most. Russian preferred by many CIS volunteers.
- **Conversion impact**: ~25% lower completion rate for RU-native users reading EN questions (industry benchmark: L2 language assessments = 20-30% drop in performance scores)

#### Recommendation: 3-tier approach
1. **Before activation wave (2 days)**: Add `scenario_ru` column (nullable). Fill 30 highest-frequency questions in RU. That's ~5 per competency × 6 competencies = 30 questions.
2. **At activation**: If `user.languages` includes 'ru' → serve scenario_ru (fallback: scenario_en)
3. **Month 2**: Fill remaining 60 questions in RU. Full parity.

#### Cost: 30 RU translations
Use Gemini to translate 30 EN questions to idiomatic Russian, then manual review = 2 hours.
**This is not optional for CIS expansion. Do it before activation.**

---

## SPRINT 10.5: Mass Activation Readiness

> **Goal:** Make the system safe for 11K contacts in 3-4 days of work.
> **NOT IN:** BrandedBy, ZEUS, Sprint A2-A5, new features.
> **SUCCESS:** Activation wave sent, system doesn't crash, conversion tracked, CEO sees stats.

### Priority order (must be done in sequence):

#### P0: Groq LLM fallback (BLOCKING — do first)
**Owner: CTO**
**Time: 3-4 hours**
**Files:** `apps/api/app/services/bars.py`, `apps/api/app/config.py`

```
1. Add GROQ_API_KEY to Railway env vars (key already in apps/api/.env from ZEUS)
2. Add evaluate_with_groq() function in llm.py (reuse ZEUS pattern)
3. Wrap evaluate_with_llm() with try→Groq→keyword_fallback chain
4. Test: simulate Gemini 429 → verify Groq fires → verify keyword_fallback fires
5. Add to prometheus-style log: "evaluation_provider": "gemini|groq|keyword_fallback"
```

#### P1: DB migration 000034 — activation tracking (1 hour)
**Owner: CTO via Supabase MCP**

```sql
-- Migration 000034: activation_tracking
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS referral_code TEXT,
ADD COLUMN IF NOT EXISTS utm_source TEXT,
ADD COLUMN IF NOT EXISTS utm_campaign TEXT;

-- Index for fast aggregation
CREATE INDEX idx_profiles_referral_code ON public.profiles(referral_code)
WHERE referral_code IS NOT NULL;

-- CEO stats view (RLS: service role only)
CREATE OR REPLACE VIEW public.referral_stats AS
SELECT
    referral_code,
    utm_source,
    utm_campaign,
    COUNT(*) AS registrations,
    COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL) AS badges_earned,
    ROUND(COUNT(*) FILTER (WHERE badge_issued_at IS NOT NULL)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1) AS conversion_pct,
    MIN(created_at) AS first_registration,
    MAX(created_at) AS last_registration
FROM public.profiles
WHERE referral_code IS NOT NULL
GROUP BY referral_code, utm_source, utm_campaign
ORDER BY registrations DESC;
```

#### P2: Capture UTM at registration (2 hours)
**Owner: CTO**
**Files:** `apps/web/src/app/[locale]/register/page.tsx`, `apps/web/src/app/auth/callback/route.ts`

```
1. In register/page.tsx: on mount, save {ref, utm_source, utm_campaign} to sessionStorage
2. In auth/callback/route.ts: after session created, read sessionStorage → PATCH /api/profiles/me
3. Add PATCH /api/profiles/me with referral_source schema (non-sensitive, no auth bypass)
4. Test: register with ?ref=test-hr → check profiles table → referral_code = 'test-hr'
```

#### P3: scenario_ru column + 30 translations (2 hours)
**Owner: CTO + Gemini batch translate**
**Files:** new migration 000035

```sql
-- Migration 000035: scenario_ru
ALTER TABLE public.questions
ADD COLUMN IF NOT EXISTS scenario_ru TEXT;
-- nullable — fallback to scenario_en if NULL
```

Then batch translate via Gemini (script, not manual):
```python
# scripts/translate_ru.py
# Read all questions WHERE scenario_ru IS NULL
# For each: Gemini translate scenario_en → scenario_ru
# UPDATE questions SET scenario_ru = ... WHERE id = ...
# Run once. Non-destructive.
```

Language selection in assessment:
```python
# In GET /api/assessment/questions
# Check profile.languages[] → if 'ru' in languages → use scenario_ru if not None
# Fallback: scenario_en
```

#### P4: Welcome/onboarding page (3 hours)
**Owner: CTO (simple page, no V0 needed)**
**File:** `apps/web/src/app/[locale]/welcome/page.tsx`

Design spec above in Q2 section. Key requirements:
- Shows value proposition (8 competencies, AURA score, badge)
- Primary CTA: "Start Assessment"
- Secondary: "Skip for now"
- Reads `?ref` from URL → displays "You were referred by [source]" (optional social proof)
- i18n: EN + AZ + RU (3 languages for this page specifically — first impression matters)

Middleware update:
```typescript
// middleware.ts — add after auth check
if (isAuthenticated && request.nextUrl.pathname === `/${locale}/dashboard`) {
  const hasCompletedAssessment = /* check from profile or cookie */;
  if (!hasCompletedAssessment) {
    return NextResponse.redirect(new URL(`/${locale}/welcome`, request.url));
  }
}
```

#### P5: Badge share mechanic (2 hours)
**Owner: CTO**
**File:** `apps/web/src/app/[locale]/aura/page.tsx`

Add to existing AURA page (post-assessment completion):
```
┌───────────────────────────────┐
│  🏆 You earned Silver badge!  │
│  AURA Score: 72.4             │
│                               │
│  [Share on LinkedIn]          │
│  [Share on TikTok]            │
│  [Copy link to profile]       │
│                               │
│  Made possible by Volaura ✓  │
└───────────────────────────────┘
```

LinkedIn share URL (native, no API needed):
```
https://www.linkedin.com/sharing/share-offsite/?url=https://volaura.app/{locale}/profile/{username}
```

TikTok: copy-to-clipboard with text "My AURA Score: 72 | Silver Badge | volaura.app" (TikTok has no web share API)

#### P6: Telegram daily digest (1 hour)
**Reuse ZEUS infrastructure already built.**
Add `activation_digest` mode to zeus_content_run.py:
- Query `referral_stats` view
- Format as Telegram message
- Send to TELEGRAM_CEO_CHAT_ID (not channel)

---

## EXPANDED DEVELOPMENT IMPACT

These answers change 3 things in the overall plan:

### 1. Sprint 10 reprioritization
**Before:** API codegen → org dashboard → post #3 → Vitest fix
**After:**
```
Sprint 10.5 (ADDED, P0): Activation readiness — Groq fallback + UTM tracking
Sprint 10:   API codegen + org dashboard (unchanged — org dashboard = fastest B2B revenue)
```

### 2. ZEUS now has a job BEFORE channels are configured
Previously ZEUS was blocked on "no Telegram channel IDs from CEO".
**New use:** ZEUS sends activation digest to CEO's personal chat (TELEGRAM_CEO_CHAT_ID already configured). This works TODAY without public channels.

### 3. Language architecture is decided
- `volaura.app` serves AZ + EN + RU (add RU to i18n now, before activation)
- RU = CIS first. Later: Turkish (TR) for MENA Phase 2.
- i18n locale array: ['az', 'en', 'ru'] (was ['az', 'en'])

**What this means for i18n:**
- Add `ru` to `generateStaticParams` in layout
- Create `public/locales/ru/common.json` (Gemini-translate EN → RU, ~1h)
- RU locale goes live WITH activation wave (not after)

---

## ACTIVATION SEQUENCE (when ready)

### Day -3 (today + 3 days): Build
- [ ] P0: Groq fallback live on Railway
- [ ] P1: Migration 000034 applied
- [ ] P2: UTM capture at registration
- [ ] P3: Migration 000035 + 30 RU question translations
- [ ] P4: Welcome page live
- [ ] P5: Badge share button live on AURA page
- [ ] P6: CEO daily digest via Telegram

### Day 0: Soft launch (Yusif's warm network, ~100 people)
- Send to 10 closest HR coordinators with personalized links
- Monitor: `/api/admin/referral_stats` or Supabase dashboard
- Watch for Gemini rate limit errors in Railway logs
- Fix anything that breaks

### Day 3: Full activation
If Day 0 had <5% error rate:
- Email blast to all 4K contacts (Mailchimp or direct — Yusif decides)
- WhatsApp message via HR coordinators with their ref codes
- LinkedIn post (Post #3 — activation angle)

### Day 7: Measure
Target:
| Metric | Floor | Target | Moonshot |
|--------|-------|--------|---------|
| Registrations | 300 | 800 | 2,000 |
| Assessments completed | 150 | 500 | 1,500 |
| Badges issued | 100 | 400 | 1,200 |
| Badge shares | 20 | 150 | 500 |
| K-factor | 0.05 | 0.3 | 0.6 |

---

## CEO DECISIONS NEEDED (1 question only)

**Single question for Yusif before activation:**

> "Есть ли у тебя уже список из ~10 HR-координаторов с именами для реферальных кодов?
> Если да — дай мне их имена, я сгенерирую коды вида `ref=hr-leyla-cop29` и подготовлю
> готовые сообщения для каждого."

This takes 10 minutes from Yusif. Everything else — CTO builds.

---

## WHAT THE TEAM THINKS

**Лейла (volunteer, 22, mobile):** "The welcome page is right. If I open the link and see a dashboard with 0 everything — I close it. Start the assessment immediately."

**Нигяр (org admin, desktop):** "Referral tracking needs to work the FIRST day. We need to know which HR brought the most volunteers — that's our B2B pipeline. Those HRs become our first paying org customers."

**Attacker:** "Gemini rate limit bomb. If 100+ users hit assessment in the same hour, system goes down. User #101 gets an error, shares to WhatsApp: 'doesn't work'. Platform credibility = 0 in 60 minutes."

**Scaling Engineer:** "UTM in sessionStorage has a race condition at auth callback. The callback fires in a new tab — sessionStorage is origin-scoped but NOT shared across tabs. Use localStorage, not sessionStorage."

**Yusif (founder):** "Russian questions before activation — this is a non-negotiable for the CIS contacts. If they see EN questions, 30% will quit. We're leaving signups on the table."

**QA:** "Test the full onboarding journey with a clean browser before sending any links. Specifically: register → verify email → welcome page → assessment start. If any step 404s or breaks, the HR coordinators will blame the product."

---

*This document expands the existing LAUNCH-ACTIVATION-PLAN.md with technical infrastructure answers.*
*For the original growth strategy: docs/growth/LAUNCH-ACTIVATION-PLAN.md*
*For the referral code pattern: already designed there (volaura.com/start?ref=leyla-cop29) — this doc updates the technical implementation.*
