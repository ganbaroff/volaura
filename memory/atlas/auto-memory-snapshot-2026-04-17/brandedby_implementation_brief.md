---
name: BrandedBy Implementation Brief
description: Complete context for a Claude Code agent to build BrandedBy AI Celebrity Video Platform
type: handoff
created: 2026-03-27
author: Claude (CTO) for Yusif Ganbarov (CEO)
---

# BrandedBy AI Celebrity Video Platform — Implementation Brief

> This document is a self-contained handoff. The implementing agent should NOT need to ask clarifying questions for Week 1 deliverables. Read fully before writing any code.

---

## 1. CONTEXT — What Exists Today

### Current State
- **Live product:** Built on Mocha (no-code platform), hosted on a .xyz domain. CSR-only, zero SEO, zero enterprise credibility.
- **Delivery:** 24-48 hour manual pipeline. A human receives a request, manually creates a video, and emails it back. Zero automation.
- **Web presence:** Google returns nothing for "BrandedBy Azerbaijan". No social proof, no case studies, no testimonials.
- **Celebrity contracts:** Warm connections exist to 7 influencers (see Section 3). Formal contracts are NOT yet signed.

### Existing Codebase
- **GitHub:** https://github.com/ganbaroff/brandedby-ai-platform
- **Tech:** Hono framework + Cloudflare Workers + D1 (SQLite) + R2 storage
- **Size:** ~18,857 lines of code, estimated ~15% feature-complete
- **CRITICAL BUG (P0):** `admin:admin123` hardcoded credentials in `secure-auth.ts`. This must be killed immediately — do NOT carry this into the new stack.
- **AI video generation:** 0% implemented. "FaceMorphingDemo" is a CSS slideshow. "AI Assistant" is random string selection.
- **Stripe:** Card is never tokenized (no Stripe Elements). No webhook handler. Payment is non-functional.
- **Data:** Celebrity data has Cyrillic encoding corruption (names show as `?????`).

### Decision: ABANDON the Cloudflare/D1 codebase
Do NOT migrate or refactor the existing repo. The codebase is 15% complete with fundamental issues. Start fresh on the shared stack. The only things worth extracting from the old repo are: celebrity names/bios (after fixing encoding) and any image assets in R2.

---

## 2. ECOSYSTEM POSITION — BrandedBy is NOT Standalone

BrandedBy is one of 4 interconnected platforms built by a solo founder (Yusif) + AI:

| Platform | Brain Analogy | Function |
|---|---|---|
| **Volaura** | Cortex (rational assessment) | Skill verification, AURA scores |
| **Life Simulator** | Limbic system (emotions) | Emotional engagement game (Godot) |
| **MindFocus** | Basal ganglia (habits) | Habit tracking, focus sessions |
| **BrandedBy** | Mirror neurons (social/celebrity) | Celebrity content layer |

### How BrandedBy Connects
1. BrandedBy celebrities become **premium NPCs** in Life Simulator
2. Brands pay BrandedBy for **NPC integration** = B2B revenue without direct video sales
3. `character_state` JSON is the **integration hub** across all products
4. Shared Supabase Auth = one login across all products
5. Crystal economy: users earn crystals in Volaura/MindFocus, spend them on celebrity NPC interactions in Life Simulator

### Integration Architecture (decided, not yet built)
- **Database:** Shared Supabase project, `brandedby` schema for BrandedBy-specific tables
- **Backend:** Shared FastAPI monolith at `apps/api/` (extends Volaura's existing Railway deployment)
- **Auth:** Shared Supabase Auth with `user_metadata.products[]` JWT claims
- **Why shared:** Solo founder cannot maintain 4 separate backends. One Railway deploy, one Supabase project.

### BrandedBy Supabase Tables (planned)
```sql
CREATE TABLE brandedby.celebrities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    bio TEXT,
    category TEXT,
    image_url TEXT,
    game_available BOOLEAN DEFAULT FALSE,  -- flag for Life Simulator NPC
    sprite_data JSONB,                      -- NPC appearance in game
    sima_verified BOOLEAN DEFAULT FALSE,    -- SIMA identity verification status
    sima_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE brandedby.video_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    celebrity_id UUID REFERENCES brandedby.celebrities(id),
    script TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    video_url TEXT,
    stripe_payment_id TEXT,
    tier TEXT NOT NULL,  -- 'spotlight', 'ambassador', 'enterprise'
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE brandedby.influencer_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    social_links JSONB,
    follower_count INT,
    category TEXT,
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. MOAT — Why Competitors Cannot Replicate This

### Moat 1: SIMA State Identity Verification
- **SIMA** = Azerbaijan's state identity verification system (like eID/Aadhaar but Azerbaijani)
- Celebrities create official AI avatars verified through SIMA
- The platform becomes **legal consent infrastructure** — not just a video tool
- SIMA access has been **CONFIRMED available** by the CEO
- No global competitor (Synthesia, HeyGen, D-ID, Tavus, Captions.ai) has SIMA access
- This turns the compliance problem (deepfake consent) into a product feature

### Moat 2: Licensed Local Celebrity IP
- Azerbaijan-specific celebrity likenesses that global platforms cannot offer
- Local celebrities are the ones that local brands want in their ads

### Moat 3: Influencer Network (Chicken-and-Egg Solved)
CEO has **warm direct connections** (not cold outreach) to:

| Name | Type | Notes |
|---|---|---|
| Tunzale Aghayeva | Actress/public figure | High-profile |
| Azer Aydemir Kim | Actor | Entertainment |
| Farid Pasdashunas | Influencer | Social media |
| Vusal Yusifli | Influencer | Social media |
| Yuspace | YouTube channel | Media/content |
| Tedroid | Media outlet | Tech/media |
| infonews | Media outlet | News |

This means: we do NOT need to solve cold celebrity acquisition. The first 3-5 celebrities can be onboarded through warm introductions.

---

## 4. WEEK 1 DELIVERABLE — Scope Lock

**IN:** Landing page + SIMA verification hero + influencer onboarding form
**NOT IN:** Stripe, video generation, AI pipeline, admin dashboard, mobile app
**SUCCESS:** brandedby.com is live, loads fast, looks enterprise-grade, has working influencer form
**TIME:** ~8-12 hours of implementation work

### Specific Deliverables

1. **Register brandedby.com** (CEO handles domain purchase, agent handles DNS/Vercel config)

2. **Next.js 14 landing page on Vercel**
   - App Router (NOT Pages Router)
   - TypeScript strict mode
   - Tailwind CSS 4
   - Sections: Hero, How It Works, Celebrity Showcase (with placeholder portraits), SIMA Verification explainer, Pricing preview (no buy buttons yet), Influencer CTA
   - Mobile-first responsive
   - AZ primary language, EN secondary (i18n from day 1)
   - Performance: Lighthouse 90+ on all metrics

3. **SIMA Verification as hero feature**
   - This is the headline differentiator, not "AI video"
   - Messaging: "The only platform where celebrity consent is state-verified"
   - Visual: shield/verification badge iconography
   - Do NOT implement actual SIMA API integration yet — just the messaging and UX

4. **Influencer onboarding form**
   - Option A: Supabase table (`brandedby.influencer_applications`) if shared Supabase is ready
   - Option B: Airtable form embed if Supabase setup would delay launch
   - Fields: name, email, social links (Instagram, TikTok, YouTube), follower count, category, message
   - Confirmation page after submission

5. **No Stripe yet** — pricing section shows tiers but buttons say "Coming Soon" or "Contact Us"

---

## 5. TECH STACK

### Target Stack (Week 1)
| Layer | Technology | Hosting | Cost |
|---|---|---|---|
| Frontend | Next.js 14 (App Router) | Vercel (free tier) | $0 |
| Styling | Tailwind CSS 4 | -- | -- |
| Language | TypeScript 5 strict | -- | -- |
| Form backend | Supabase or Airtable | Supabase (free) or Airtable (free) | $0 |
| Domain | brandedby.com | Namecheap/Vercel | ~$12/year |

### Target Stack (Week 2+, when backend needed)
| Layer | Technology | Hosting | Cost |
|---|---|---|---|
| Backend | FastAPI (shared with Volaura) | Railway | ~$8/mo (shared) |
| Database | Supabase PostgreSQL | Supabase | Free tier |
| Storage | Cloudflare R2 or Supabase Storage | -- | Pay-as-you-go |
| Payments | Stripe (Checkout Sessions + Billing) | -- | 2.9% + $0.30 |
| Video AI | HeyGen API or similar (TBD Sprint 9) | -- | Per-video cost |
| Voice AI | ElevenLabs API (TBD) | -- | Per-minute cost |

### Why NOT Keep Cloudflare/D1
- Solo founder cannot maintain separate Cloudflare Workers + D1 stack alongside Volaura's FastAPI + Supabase
- BrandedBy is only 15% complete — migration cost is ~2 days, permanent maintenance cost of separate stack is unbounded
- Shared auth, shared database, shared deployment = one system to monitor

### Repo Structure (NEW)
```
brandedby/
  apps/
    web/                    # Next.js 14 (deployed to Vercel)
      src/
        app/
          [locale]/         # i18n routing
            page.tsx        # Landing page
            layout.tsx
          api/              # Next.js API routes (form submission if no FastAPI yet)
        components/
          ui/               # shadcn/ui
          features/
            hero/
            pricing/
            celebrity-showcase/
            sima-verification/
            influencer-form/
        lib/
          i18n/
          utils/
        locales/
          az/
          en/
      public/
        images/
          celebrities/      # Placeholder portraits
```

If the decision is made to keep BrandedBy in its own repo (separate from Volaura monorepo), use this structure. If merging into the Volaura monorepo, add it as `apps/brandedby-web/`.

---

## 6. PRICING

| Tier | Price | Billing | Stripe Product |
|---|---|---|---|
| **Spotlight** | $199/video | One-time | Stripe Checkout Sessions |
| **Ambassador** | $799/month | Subscription | Stripe Billing |
| **Enterprise** | $2,500+/month | Custom invoice | Manual / Stripe custom |

### Unit Economics
- Celebrity licensing: $500-$5,000/year for Tier 3 (local influencer)
- Video COGS: ~$20-50/video (API costs)
- Gross margin: ~75-90% per Spotlight video
- Do NOT pursue Tier 1 celebrities ($50K-$150K/year licensing) pre-revenue

### ICP (Ideal Customer Profile)
CMO or Head of Marketing at an Azerbaijani brand with >= $500K/year ad budget.
**First-call list:** Azercell, Kapital Bank, Bakcell, PASHA Bank, ABB, Silk Way Airlines.

---

## 7. DESIGN PRINCIPLES (Non-Negotiable)

1. **ADHD-first design:** CEO has ADHD. The platform must use positive reinforcement ONLY.
   - No anxiety loops, no punishment for inaction, no "you're falling behind" messaging
   - Progress = celebration. Absence = neutral (not negative).

2. **No pay-to-avoid-harm mechanics:**
   - Every paid feature must have a free alternative path
   - Monetization = "make life richer", NOT "avoid pain"
   - This applies to the crystal economy and all future gamification

3. **Mandatory AI disclosure:**
   - All AI-generated content must be visibly labeled as AI-generated
   - Never say "deepfakes" — always say "licensed AI celebrity content"
   - This is both ethical and legal positioning

4. **Content moderation:**
   - All scripts must be checked for inappropriate content before video generation
   - Celebrity likenesses must never be used in political, sexual, or defamatory content
   - Moderation is a feature, not a restriction (brands want brand-safe content)

5. **Enterprise-grade trust signals:**
   - SIMA verification badge prominently displayed
   - Professional design (no "startup-y" casualness)
   - .com domain (NOT .xyz, NOT .ai)
   - AZ/EN language support from day 1

---

## 8. LEGAL FRAMEWORK

- **Azerbaijan:** No specific AI likeness law. SIMA-verified consent is the gold standard.
- **Approach:** BrandedBy becomes the legal infrastructure layer — the platform where consent is formally recorded and verified.
- **Every video:** Must carry AI disclosure watermark/label.
- **Celebrity contracts:** Must include: likeness rights, usage scope, revenue share terms, termination clause, content approval rights.
- **Content policy:** No political content, no sexual content, no defamation, no impersonation outside platform.

---

## 9. FIRST QUESTIONS for the Implementation Session

Before writing any code, the implementing agent should confirm with CEO:

1. **Which influencers have you contacted?** Which ones said yes? This determines whose placeholder portraits go on the landing page.
2. **How many hours/week for BrandedBy vs Volaura?** This determines sprint velocity and whether to do weekly or biweekly releases.
3. **Is brandedby.com registered?** If not, register it. If CEO prefers a different domain, confirm first.
4. **Separate repo or Volaura monorepo?** Recommendation: separate repo for now (`ganbaroff/brandedby`), merge into monorepo when backend integration happens.
5. **Supabase: shared project or separate?** Recommendation: shared Supabase project with `brandedby` schema (per architecture decision). But confirm the Volaura Supabase project ID.

---

## 10. MISTAKES TO NOT REPEAT

These are documented mistakes from the BrandedBy and Volaura projects. The implementing agent MUST internalize these:

| # | Mistake | Prevention |
|---|---|---|
| 1 | Building strategy around problems CEO already solved | ASK what assets/connections exist BEFORE planning acquisition strategies |
| 2 | Throwing crypto/token ideas without legal framework | No blockchain, no tokens. Crystals are in-app currency only. |
| 3 | Estimating timelines for a 5-person team when it is 1 founder + AI | All estimates assume 1 human (CEO, part-time) + AI agents |
| 4 | Not asking what assets/connections already exist | CEO has warm influencer connections — do not plan cold outreach |
| 5 | Hardcoding credentials (admin:admin123) | Use environment variables + Supabase Auth. Zero hardcoded secrets. |
| 6 | Building on no-code platforms for enterprise products | Next.js + Vercel. No Mocha, no Bubble, no Webflow for core product. |
| 7 | Ignoring encoding (Cyrillic corruption) | UTF-8 everywhere. Explicit `encoding='utf-8'` on all file operations. Test with Azerbaijani characters: a, g, i, o, u, s, c |
| 8 | "Comprehensive" plans that ignore resource constraints | Week 1 = landing page ONLY. No video pipeline, no AI, no Stripe. |
| 9 | Fake features (CSS slideshow labeled "FaceMorphing") | If a feature is not real, do not put it on the site. Placeholder = honest "Coming Soon". |
| 10 | Separate infrastructure per product | Shared Supabase + shared FastAPI. One system to maintain. |

---

## 11. ANTI-PATTERNS (NEVER DO)

- **Never build on Mocha again.** The existing Mocha site is being replaced, not upgraded.
- **Never hardcode credentials.** Use environment variables and proper auth.
- **Never build without demo content first.** The landing page needs real-looking celebrity placeholders and copy before going live.
- **Never announce expansion before 3+ enterprise logos.** Azerbaijan first. Georgia/Kazakhstan later. No "Coming to 10 countries" messaging.
- **Never use global Supabase client.** Per-request via dependency injection (FastAPI `Depends()`).
- **Never use Pydantic v1 syntax.** `ConfigDict`, `@field_validator`, not `class Config` or `@validator`.
- **Never use `print()`.** Use `loguru` for all logging.
- **Never use Redux.** Zustand for client state.
- **Never use Pages Router.** App Router only.
- **Never say "deepfakes."** Say "licensed AI celebrity content."
- **Never skip i18n.** AZ primary, EN secondary, from the first commit.
- **Never build AI video pipeline in Week 1.** That is Sprint 9 (Week 9) in the master plan.

---

## 12. STORAGE STRATEGY (Bootstrap Phase)

BrandedBy is pre-revenue. Storage costs must be zero or near-zero:

- **Phase 1 (now):** No video storage needed. Landing page only.
- **Phase 2 (when video pipeline exists):** Videos stored in Supabase Storage or R2. Small scale, free tier.
- **Phase 3 (at scale):** Sell 1,000 subscriptions first, then fund proper CDN/storage infrastructure.
- **Principle:** Do not over-engineer storage before there is revenue to pay for it.

---

## 13. EXPANSION SEQUENCE

| Phase | Market | Timeline | Trigger |
|---|---|---|---|
| 1 | Azerbaijan | Months 1-18 | Now |
| 2 | Georgia | Months 12-24 | 3+ enterprise clients in AZ |
| 3 | Kazakhstan | Months 24-36 | Proven unit economics |

Do NOT build multi-region infrastructure now. Do NOT add Georgian/Kazakh celebrities. Do NOT translate to Georgian/Kazakh. Azerbaijan only until proven.

---

## 14. IMPLEMENTATION TIMELINE (12-Sprint Master Plan)

BrandedBy-specific sprints from the ecosystem master plan:

| Sprint | Week | Deliverable |
|---|---|---|
| **Week 1** (standalone) | 1 | Landing page + SIMA hero + influencer form |
| **Week 2-3** (standalone) | 2-3 | Onboard 3-5 influencers, create 5 demo videos (manual) |
| **Week 4** (standalone) | 4 | Stripe $199 Spotlight, first paying customers |
| **Sprint 5** (ecosystem) | 5 | Kill Cloudflare/D1, migrate to shared FastAPI + Supabase |
| **Sprint 7** (ecosystem) | 7 | Cross-product SSO (shared auth) |
| **Sprint 9** (ecosystem) | 9 | AI video pipeline MVP (HeyGen/Runway/Kling/D-ID evaluation) |
| **Sprint 10** (ecosystem) | 10 | Celebrity NPC bridge to Life Simulator |

---

## 15. SUCCESS METRICS

### Week 1
- [ ] brandedby.com resolves and loads in < 3 seconds
- [ ] Lighthouse score 90+ on all 4 metrics
- [ ] Landing page renders correctly on mobile (375px) and desktop (1280px)
- [ ] Influencer form submits successfully and data persists
- [ ] AZ and EN language toggle works
- [ ] Zero hardcoded credentials in codebase
- [ ] SIMA verification messaging is prominent and clear

### Month 1
- [ ] 3-5 influencers onboarded (applications received, not necessarily contracts signed)
- [ ] 5 demo videos created (even if manually)
- [ ] Stripe Spotlight ($199) checkout functional
- [ ] 1 paying customer

### Month 3
- [ ] 3+ enterprise clients (Azercell, Kapital Bank, etc.)
- [ ] Automated video pipeline (< 5 min from order to delivery)
- [ ] Shared auth with Volaura working

---

## 16. ENVIRONMENT VARIABLES NEEDED

```env
# Week 1 (landing page only)
NEXT_PUBLIC_SITE_URL=https://brandedby.com
NEXT_PUBLIC_DEFAULT_LOCALE=az

# Week 2+ (when Supabase integration happens)
NEXT_PUBLIC_SUPABASE_URL=<shared with Volaura>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<shared with Volaura>

# Week 4+ (when Stripe integration happens)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Sprint 9+ (when AI video pipeline happens)
HEYGEN_API_KEY=<TBD>
ELEVENLABS_API_KEY=<TBD>
```

Do NOT set up Stripe or AI API keys in Week 1. They are not needed.

---

## 17. COPY DIRECTION (Landing Page)

### Hero Section
- Headline (AZ): "SIMA ilə təsdiqlənmiş məşhur AI videoları" (SIMA-verified celebrity AI videos)
- Headline (EN): "State-Verified Celebrity AI Videos"
- Subhead: The only platform where celebrity consent is verified through Azerbaijan's state identity system.
- CTA: "Become a Verified Creator" (for influencers) / "Request Demo" (for brands)

### Tone
- Professional, not startup-casual
- Trustworthy, not hype-driven
- Enterprise-grade, not consumer-playful
- "Licensed AI content" never "deepfakes" or "synthetic media"

### Key Messages
1. SIMA-verified consent = legal certainty for brands
2. Licensed local celebrities that global platforms cannot offer
3. From $199/video — accessible pricing for the Azerbaijani market
4. AI-generated content, honestly labeled, brand-safe

---

## 18. OPEN DECISIONS (for CEO to resolve)

These are decisions the implementing agent cannot make alone:

1. **Separate repo vs Volaura monorepo?** Recommendation: separate repo now, merge later.
2. **Which Supabase project?** Need the project ID for the shared instance.
3. **Celebrity placeholder images:** Does CEO have photos with usage rights, or should we use generic silhouettes?
4. **Contact form destination:** CEO's email for "Request Demo" inquiries?
5. **Analytics:** Vercel Analytics (free) or something else?
6. **Which influencers to feature by name on the landing page?** Only feature those with explicit permission.

---

*End of brief. The implementing agent should read this document in full, confirm the open decisions with CEO, then execute Week 1 deliverables.*
