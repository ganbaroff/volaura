# КОМПЛЕКСНЫЙ АНАЛИЗ PROMPT ДЛЯ VOLAURA

## РОЛЬ И КОНТЕКСТ

Ты — Senior Product Architect, Tech Lead и Business Strategist с 15+ летним опытом в:
- SaaS платформах (B2B и B2C)
- HR Tech и Talent Management системах
- Gamification и Behavioral Psychology в продуктах
- AI/ML системах (assessment, matching, personalization)
- CIS/MENA региональном рынке
- Startup scaling от 0 до Series A

## СТРАТЕГИЧЕСКИЕ ОСНОВЫ PROJEСTA

### 1. КОНЦЕПЦИЯ И ВИДЕНИЕ

**VOLAURA — Elite Volunteer Talent Platform**

Это НЕ очередная база данных волонтёров. Это:

- **Elite Club** для proven talent (бейджи заслуживаются, не покупаются)
- **Talent Verification System** с объективными метриками компетенций
- **Viral Growth Engine** где каждый assessment создаёт органический маркетинг
- **Premium Talent Pool** для event organizers и corporations

**Ключевое отличие от конкурентов:** Ни одна платформа не объединяет assessment + badge + portable profile + event history + coordinator ratings В ОДНОМ месте для волонтёров.

### 2. РЕГИОН: АЗЕРБАЙДЖАН

**Почему Азербайджан:**

- WUF13 Baku, май 2026 (16,000 заявок, 2,500 позиций)
- COP29 legacy и международные события
- Молодое население Баку (средний возраст ~30 лет)
- Активная digital transformation государства
- ASAN Service экосистема (36,000+ волонтёров)
- AIESEC, YARAT, ADA University programs
- Corporate CSR growth (SOCAR, Kapital Bank, BP Azerbaijan)

**Market Specifics:**
- Telegram-dominant market (не email, не Slack)
- Mobile-first пользователи (80%+ на телефонах)
- AZ + EN + RU multilingual environment
- Trust-based business culture (relationships > cold outreach)
- Government-supported civic initiatives

### 3. CORE MECHANICS

#### AURA Score System

**8 Competencies с финальными весами:**

```
1. Communication (0.20) — навыки коммуникации
2. Reliability (0.15) — надёжность и пунктуальность
3. English (0.15) — уровень английского CEFR A2-C1
4. Leadership (0.15) — лидерские качества
5. Event Performance (0.10) — опыт ивентов
6. Tech Literacy (0.10) — техническая грамотность
7. Adaptability (0.10) — адаптивность
8. Empathy & Safeguarding (0.05) — эмпатия и безопасность
```

**Badge Tiers:**

```
None (<40)     — ещё не оценён
Bronze (40-59) — начальный уровень
Silver (60-74) — подтверждённые компетенции
Gold (75-89)   — высокий уровень
Platinum (90+) — elite performer
```

**Elite Status:** AURA ≥75 AND 2+ competencies ≥75

#### Reliability Scoring v2

**No-show penalties:**

```
-15 → ghost (не пришёл, не предупредил)
-10 → same day cancellation
-5  → 24h cancellation
-2  → 48h cancellation
 0  → 72h+ cancellation (норма)
```

**Decay (восстановление):**

```
+5 за каждое успешное attendance
+5 First Event Bonus (однократно)
```

**UI States:**

```
0 events  → "Reliability Pending [?]"
3 events  → "Reliability Verified ✓"
5+ events → "Reliability Proven 🛡"
```

**Alerts:** Warning координатору если 2+ SJT red flags

#### Adaptive Assessment System

**Технологии:**

- IRT/CAT через `adaptivetesting` PyPI (Bayesian, 1PL/2PL/3PL/4PL)
- Discrimination index (recalculate после каждой сессии)
- Anti-gaming: response time check, lie detector, consistency score
- Evaluation caching при submit_answer (экономит 50% LLM calls)

**BARS (Behaviorally Anchored Rating Scales):**

- 4-point scale для каждого вопроса
- Anchors = конкретные поведенческие описания
- Каждый балл привязан к observable behavior

#### VIRAL GROWTH ENGINE — Sharable AURA Card

**ЭТО MVP-0. Без неё нет органического роста.**

**Viral Loop:**

```
Assessment завершён
    ↓
Красивая AURA Card генерируется автоматически
    ↓
"Поделиться" → Instagram / LinkedIn / Telegram / WhatsApp
    ↓
Контакты видят: "Айсель прошла Volaura — Gold 🏅"
    ↓
Переходят → регистрируются
    ↓
Проходят assessment → делятся → цикл повторяется
```

**Технические детали:**

```
AURA Card = OG Image (Open Graph)
Генерация: Vercel OG (satori library) или Canvas API
Размеры:
  - 1080×1080 (Instagram Square)
  - 1080×1920 (Instagram Story)
  - 1200×630 (LinkedIn/Twitter)

URL структура:
  volaura.app/u/{username} → public profile
  volaura.app/u/{username}/card → OG image endpoint

Контент карточки:
  - Имя + фото (опционально)
  - AURA Score (большой, центр)
  - Badge tier (Bronze/Silver/Gold/Platinum)
  - Radar chart (6 осей, мини версия)
  - "Verified by Volaura" + QR код на профиль
  - Брендинг Volaura внизу

Open Badges:
  - Экспорт в LinkedIn Certifications одной кнопкой
  - JSON формат Open Badges 3.0 стандарт
```

**Психология Gen Z — почему работает:**

```
1. Social proof — "мой друг прошёл, я тоже хочу"
2. Achievement signaling — Gold badge = статус
3. FOMO — видишь чужой badge, хочешь свой
4. LinkedIn credibility — реальный карьерный актив
5. Конкуренция — "у меня Silver, у неё Gold, хочу лучше"

Это Duolingo streak mechanics применённый к волонтёрству.
```

**Metrics:** K-factor > 1.0, 30% sharing target

---

## SECTION 1: COMPLETE ARCHITECTURE

### 1.1 SYSTEM OVERVIEW

**High-level Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
│  │ Web App │  │ Mobile  │  │ Telegram│  │ Admin Panel │ │
│  │ (Next.js)│  │ (PWA)  │  │   Bot   │  │  (Dashboard)│ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Next.js API Routes /api/*               │  │
│  │         + FastAPI Backend Microservices              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Supabase   │  │  FastAPI    │  │  External  │
│  (Database, │  │  (Python    │  │  Services  │
│   Auth,     │  │  AI/ML,    │  │  (Stripe,  │
│   Storage)  │  │  Business  │  │  LinkedIn, │
│             │  │  Logic)    │  │  Telegram) │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 1.2 FRONTEND ARCHITECTURE

**Tech Stack:**

```
Framework: Next.js 14+ (App Router)
Language: TypeScript 5+
Styling: Tailwind CSS 4+ + CSS Modules
Animation: Framer Motion
Charts: Recharts (radar chart)
Forms: React Hook Form + Zod validation
State: Zustand (lightweight) / TanStack Query
i18n: react-i18next (AZ primary, EN secondary)
PWA: next-pwa for offline support
Testing: Vitest + React Testing Library + Playwright
```

**Folder Structure:**

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth group
│   │   ├── login/
│   │   ├── register/
│   │   └── onboarding/
│   ├── (dashboard)/              # Protected routes
│   │   ├── profile/
│   │   ├── assessment/
│   │   ├── events/
│   │   ├── matches/
│   │   └── settings/
│   ├── (public)/                 # Public routes
│   │   ├── [username]/           # Public profiles
│   │   └── card/[username]/      # OG images
│   ├── (b2b)/                    # B2B dashboard
│   │   ├── search/
│   │   ├── event/create/
│   │   └── analytics/
│   └── api/                      # API routes
│       ├── auth/
│       ├── assessment/
│       └── webhooks/
├── components/
│   ├── ui/                       # Base UI components
│   ├── features/                 # Feature-specific
│   │   ├── assessment/
│   │   ├── radar-chart/
│   │   ├── aura-card/
│   │   └── ...
│   └── layouts/
├── lib/
│   ├── supabase/
│   ├── api/
│   └── utils/
├── hooks/                        # Custom hooks
├── stores/                       # Zustand stores
├── types/                        # TypeScript types
├── i18n/
│   ├── locales/
│   │   ├── az/
│   │   └── en/
│   └── config.ts
└── public/
    └── og/                       # OG image templates
```

**Key Pages and Features:**

```
1. Landing Page (/):
   - Hero с viral CTA
   - AURA Card preview
   - Social proof (stats, testimonials)
   - Feature highlights
   - Pricing (B2B)
   - Footer с links

2. Auth Flow (/login, /register):
   - Supabase Auth (email, Google, Apple)
   - AZ/EN/RU language toggle
   - Clean onboarding experience

3. Volunteer Dashboard (/dashboard):
   - Profile completion progress
   - AURA Score visualization (radar chart)
   - Upcoming events
   - Messages/notifications
   - Quick actions

4. Assessment Flow (/assessment):
   - Competency selection
   - Adaptive question engine
   - Real-time progress
   - BARS rating interface
   - Results + AURA Card generation

5. Public Profile (/u/[username]):
   - AURA Score badge
   - Radar chart
   - Event history
   - Skills verification
   - Contact CTA
   - Share buttons

6. AURA Card (/u/[username]/card):
   - OG image generation
   - 3 format exports
   - QR code to profile
   - Social share buttons

7. Events (/events):
   - Browse events
   - Filter by competency match
   - Event details
   - Registration flow
   - QR check-in

8. B2B Dashboard (/b2b):
   - Volunteer search
   - Advanced filters (AURA, skills, availability)
   - Saved candidates
   - Event management
   - Analytics
   - CSV export
```

### 1.3 BACKEND ARCHITECTURE

**Tech Stack:**

```
Framework: FastAPI (Python 3.11+)
Database: Supabase (PostgreSQL + RLS)
ORM: SQLAlchemy 2.0 + asyncpg
Auth: Supabase Auth + JWT
AI: Gemini 2.5 Flash (primary), OpenAI (fallback)
Vector DB: pgvector (semantic matching)
Background: Celery + Redis (optional, can use Supabase Edge Functions)
Testing: pytest + pytest-asyncio
Documentation: OpenAPI/Swagger auto-generated
```

**Microservices Structure:**

```
backend/
├── apps/
│   ├── api/                     # FastAPI main app
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── deps.py              # Dependencies
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── assessment.py
│   │       ├── events.py
│   │       ├── profiles.py
│   │       ├── matching.py
│   │       └── webhooks.py
│   │
│   ├── core/                    # Core business logic
│   │   ├── assessment/
│   │   │   ├── engine.py       # IRT/CAT engine
│   │   │   ├── bars.py         # BARS evaluation
│   │   │   ├── aura.py         # AURA calculation
│   │   │   └── anti_gaming.py  # Fraud detection
│   │   ├── matching/
│   │   │   ├── vector.py       # pgvector operations
│   │   │   ├── rules.py        # Rule-based matching
│   │   │   └── ml.py           # ML predictions
│   │   └── reliability/
│   │       ├── scoring.py       # Reliability calculation
│   │       └── predictions.py   # No-show prediction
│   │
│   ├── services/                # External integrations
│   │   ├── llm.py              # Gemini/OpenAI wrapper
│   │   ├── stripe.py           # Payments
│   │   ├── linkedin.py         # Open Badges
│   │   └── notifications.py    # Email/Telegram
│   │
│   └── models/                 # Pydantic + SQLAlchemy
│       ├── user.py
│       ├── assessment.py
│       ├── event.py
│       └── organization.py
│
├── migrations/                  # Alembic migrations
├── tests/
├── scripts/
├── pyproject.toml
└── Dockerfile
```

**API Endpoints Design:**

```
# Auth
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me

# Profile
GET    /api/profiles/{username}
PUT    /api/profiles/me
GET    /api/profiles/me/public
POST   /api/profiles/me/avatar
GET    /api/profiles/{username}/card  # OG image

# Assessment
POST   /api/assessment/start
GET    /api/assessment/questions/{session_id}
POST   /api/assessment/answer
POST   /api/assessment/complete
GET    /api/assessment/results/{session_id}
GET    /api/assessment/history
POST   /api/assessment/reassess

# Events
GET    /api/events
POST   /api/events
GET    /api/events/{id}
PUT    /api/events/{id}
DELETE /api/events/{id}
POST   /api/events/{id}/register
POST   /api/events/{id}/checkin
POST   /api/events/{id}/rate

# Matching (B2B)
GET    /api/matching/volunteers
POST   /api/matching/search
GET    /api/matching/recommended
POST   /api/matching/save
GET    /api/matching/saved

# Organizations (B2B)
POST   /api/orgs
GET    /api/orgs/me
PUT    /api/orgs/me
GET    /api/orgs/{id}
GET    /api/orgs/{id}/volunteers
POST   /api/orgs/{id}/invite

# Payments
POST   /api/payments/create-checkout
POST   /api/payments/webhook
GET    /api/payments/subscription
POST   /api/payments/cancel

# Admin (protected)
GET    /api/admin/questions
POST   /api/admin/questions
PUT    /api/admin/questions/{id}
DELETE /api/admin/questions/{id}
GET    /api/admin/analytics
GET    /api/admin/users
```

### 1.4 DATABASE ARCHITECTURE

**Supabase Schema Design:**

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE SCHEMA                          │
└─────────────────────────────────────────────────────────────┘

-- 1. USERS & AUTH
auth.users (managed by Supabase Auth)
    └── id (UUID, PK)
    └── email
    └── created_at
    └── user_metadata (name, avatar_url, phone)

-- 2. PROFILES
public.profiles
    ├── id (UUID, PK, FK → auth.users)
    ├── username (UNIQUE)
    ├── display_name
    ├── avatar_url
    ├── bio (text)
    ├── location
    ├── languages (text[])
    ├── social_links (JSONB)
    ├── created_at
    └── updated_at

-- 3. COMPETENCIES (Reference)
public.competencies
    ├── id (UUID, PK)
    ├── slug (UNIQUE)
    ├── name_en
    ├── name_az
    ├── description_en
    ├── description_az
    └── weight (float)  -- AURA weight

-- 4. QUESTIONS BANK
public.questions
    ├── id (UUID, PK)
    ├── competency_id (FK → competencies)
    ├── difficulty (enum: easy, medium, hard)
    ├── type (enum: multiple_choice, open_ended)
    ├── scenario_en (text)
    ├── scenario_az (text)
    ├── options (JSONB)  -- [{key, text_en, text_az}]
    ├── correct_answer (char)
    ├── explanation_en (text)
    ├── explanation_az (text)
    ├── expected_concepts (JSONB)  -- For open-ended
    ├── cefr_level (char)  -- For English only
    ├── discrimination_index (float)
    ├── times_shown (int)
    ├── times_correct (int)
    └── is_active (boolean)

-- 5. ASSESSMENT SESSIONS
public.assessment_sessions
    ├── id (UUID, PK)
    ├── volunteer_id (FK → profiles)
    ├── status (enum: in_progress, completed, abandoned)
    ├── started_at (timestamptz)
    ├── completed_at (timestamptz)
    ├── duration_ms (int)
    ├── language (char)  -- en/az
    └── answers (JSONB)  -- [{question_id, answer, time_ms, evaluation}]

-- 6. AURA SCORES (Materialized)
public.aura_scores
    ├── id (UUID, PK)
    ├── volunteer_id (FK → profiles, UNIQUE)
    ├── total_score (float)
    ├── badge_tier (enum)
    ├── elite_status (boolean)
    ├── competency_scores (JSONB)  -- {competency_slug: score}
    ├── reliability_score (float)
    ├── reliability_status (text)
    ├── events_attended (int)
    ├── events_no_show (int)
    ├── last_updated (timestamptz)
    └── aura_history (JSONB)  -- Timeline

-- 7. BADGES
public.badges
    ├── id (UUID, PK)
    ├── slug (UNIQUE)
    ├── name_en
    ├── name_az
    ├── description_en
    ├── description_az
    ├── icon_url
    └── requirements (JSONB)

public.volunteer_badges
    ├── id (UUID, PK)
    ├── volunteer_id (FK → profiles)
    ├── badge_id (FK → badges)
    ├── earned_at (timestamptz)
    ├── open_badges_url (text)  -- LinkedIn export
    └── metadata (JSONB)

-- 8. EVENTS
public.events
    ├── id (UUID, PK)
    ├── organization_id (FK → organizations)
    ├── title_en
    ├── title_az
    ├── description_en
    ├── description_az
    ├── event_type (text)
    ├── location
    ├── start_date (timestamptz)
    ├── end_date (timestamptz)
    ├── capacity (int)
    ├── required_competencies (UUID[])
    ├── required_min_aura (float)
    ├── status (enum: draft, open, closed, cancelled)
    └── metadata (JSONB)

-- 9. REGISTRATIONS
public.registrations
    ├── id (UUID, PK)
    ├── event_id (FK → events)
    ├── volunteer_id (FK → profiles)
    ├── status (enum: pending, approved, rejected, waitlisted)
    ├── registered_at (timestamptz)
    ├── checked_in_at (timestamptz)
    ├── coordinator_rating (int)  -- 1-5
    ├── coordinator_feedback (text)
    ├── volunteer_rating (int)  -- 1-5
    └── volunteer_feedback (text)

-- 10. ORGANIZATIONS (B2B)
public.organizations
    ├── id (UUID, PK)
    ├── owner_id (FK → auth.users)
    ├── name
    ├── type (enum: company, ngo, government, individual)
    ├── logo_url
    ├── website
    ├── description
    ├── subscription_tier (enum: free, starter, growth, enterprise)
    ├── subscription_expires_at (timestamptz)
    ├── trust_score (float)
    ├── created_at
    └── verified_at (timestamptz)

-- 11. RLS POLICIES
-- Profiles: Anyone can read, only owner can update
-- AURA Scores: Public read
-- Events: Public read, org can write own
-- Registrations: Volunteer + org involved can read/write
-- Organizations: Public read, owner can write

-- 12. VECTOR SEARCH (pgvector)
public.volunteer_embeddings (for semantic matching)
    ├── volunteer_id (FK → profiles, PK)
    ├── embedding (vector(1536))  -- Gemini embeddings
    └── updated_at (timestamptz)

-- Functions for vector similarity:
CREATE FUNCTION match_volunteers(query_embedding vector(1536), match_count int)
RETURNS TABLE(volunteer_id uuid, similarity float)
AS $$
BEGIN
  RETURN QUERY
  SELECT ve.volunteer_id,
         1 - (ve.embedding <=> query_embedding) as similarity
  FROM volunteer_embeddings ve
  ORDER BY ve.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

### 1.5 REAL-TIME & COMMUNICATIONS

**Telegram Bot:**

```
Bot Features:
├── Notifications
│   ├── Event reminders (24h, 2h before)
│   ├── Registration status updates
│   └── AURA score changes
├── Check-in
│   ├── /checkin {event_id} → QR scan
│   └── Attendance confirmation
├── Commands
│   ├── /profile → Link to profile
│   ├── /aura → Current score summary
│   ├── /events → Upcoming events
│   └── /help → Bot commands
└── Admin
    ├── Broadcast to volunteers
    └── Event coordination
```

**Real-time (Supabase Realtime):**

```
Subscriptions:
├── New events (for volunteers)
├── Registration status changes
├── AURA score updates
├── Messages (internal chat)
└── Presence (online status)
```

### 1.6 AI/ML INTEGRATION

**LLM Integration (Gemini/OpenAI):**

```
1. Open-ended Answer Evaluation
   - Prompt engineering for BARS scoring
   - Response caching
   - Fallback chain (Gemini → OpenAI → Rule-based)

2. Semantic Matching
   - Volunteer profiles → embeddings
   - Event requirements → embeddings
   - Cosine similarity matching
   - Re-ranking with rules

3. Adaptive Question Selection
   - IRT parameters per question
   - Theta estimation per volunteer
   - Next best question algorithm
   - Stopping criteria (SE ≤ 0.3)

4. No-show Prediction
   - 6-signal behavioral model
   - Historical patterns
   - Risk scoring
```

---

## SECTION 2: COMPETITOR ANALYSIS

### 2.1 GLOBAL COMPETITORS

**VolunteerMatch + Idealist (merged 2025)**

```
STRENGTHS:
✅ 14M+ volunteer profiles
✅ 100k+ opportunities
✅ 30 years of trust
✅ Strong brand recognition

WEAKNESSES:
❌ No competency assessment
❌ No radar charts/visual profiles
❌ No gamification
❌ No B2B dashboard
❌ Legacy UI/UX
❌ No AI matching

STEAL:
→ Platform scale and trust model
→ Event categorization taxonomy
→ Search and filter UX patterns
```

**Galaxy Digital (Get Connected)**

```
STRENGTHS:
✅ Volunteer app with check-in
✅ Skills qualification tracking
✅ Hour tracking
✅ Basic matching

WEAKNESSES:
❌ No public visual profiles
❌ No gamification or badges
❌ No Discord-like community
❌ Weak analytics
❌ Poor mobile UX

STEAL:
→ Hour tracking mechanics
→ Skills qualification system
→ Basic matching algorithm
→ Shift management UX
```

**Better Impact**

```
STRENGTHS:
✅ Robust scheduling
✅ LMS integration
✅ ISO27001 security
✅ Healthcare/education focus

WEAKNESSES:
❌ Complex, enterprise-only
❌ Expensive ($400+/mo)
❌ Steep learning curve
❌ No modern UX
❌ No gamification

STEAL:
→ LMS integration patterns
→ Compliance workflows
→ Background check integration
→ Structured onboarding
```

**Benevity**

```
STRENGTHS:
✅ Enterprise CSR focus
✅ Deep integrations (Workday, SAP)
✅ Global corporate clients
✅ High revenue ($30-150k/year)

WEAKNESSES:
❌ Only enterprise/corporate
❌ Not for public volunteers
❌ Very expensive
❌ Complex implementation

STEAL:
→ Corporate CSR program structure
→ Employee volunteering mechanics
→ Donation matching integration
→ Enterprise reporting
```

**POINT App**

```
STRENGTHS:
✅ Mobile-first design
✅ Beautiful UI
✅ Free tier for nonprofits
✅ Dynamic records (reliability tracking)
✅ TikTok-style feed

WEAKNESSES:
❌ No competency assessment
❌ No B2B premium dashboard
❌ Limited gamification
❌ No Open Badges

STEAL:
✅ Dynamic Records — автоматический расчёт reliability
✅ TikTok feed UX — лента возможностей
✅ Free → Paid conversion model
✅ Mobile-first approach
✅ Simple flat pricing
```

**Catchafire**

```
STRENGTHS:
✅ Skills-based matching
✅ Professional volunteers (pro-bono)
✅ Outcome valuation
✅ NGO focus

WEAKNESSES:
❌ Only professional consulting
❌ No event management
❌ Limited to pro-bono
❌ Complex onboarding

STEAL:
✅ Outcome valuation ("ты создал ценность на $340")
✅ Skills-based matching algorithm
✅ Professional profile structure
✅ Impact measurement
```

**Deed**

```
STRENGTHS:
✅ Modern UX
✅ Gamification elements
✅ Corporate CSR
✅ AI matching

WEAKNESSES:
❌ No competency testing
❌ No visual profiles
❌ Expensive tier

STEAL:
✅ Modern component library
✅ Badge and achievement system
✅ Team challenges
✅ AI matching UI
```

### 2.2 REGIONAL COMPETITORS (CIS/MENA)

**NOT FOUND:**
- Ни одна платформа не фокусируется на CIS/MENA
- Возможность быть первым

### 2.3 FEATURES TO STEAL

```
┌─────────────────────────────────────────────────────────────┐
│                    FEATURE STEALING MATRIX                  │
├──────────────────────┬──────────────┬──────────────────────┤
│ FEATURE              │ FROM        │ HOW TO IMPLEMENT     │
├──────────────────────┼──────────────┼──────────────────────┤
│ Dynamic Records       │ POINT App   │ reliability_score     │
│                      │             │ calculation in SQL    │
├──────────────────────┼──────────────┼──────────────────────┤
│ Outcome Valuation    │ Catchafire  │ Impact calculation   │
│                      │             │ module               │
├──────────────────────┼──────────────┼──────────────────────┤
│ Skills Matching      │ Eightfold   │ pgvector semantic     │
│                      │             │ search               │
├──────────────────────┼──────────────┼──────────────────────┤
│ Gamification         │ Benevity    │ Points → Badge →      │
│                      │ Deed        │ Leaderboard system   │
├──────────────────────┼──────────────┼──────────────────────┤
│ Mobile-first         │ POINT App   │ PWA + responsive      │
│                      │             │ design               │
├──────────────────────┼──────────────┼──────────────────────┤
│ Open Badges          │ LinkedIn    │ Open Badges 3.0      │
│                      │             │ + LinkedIn API        │
├──────────────────────┼──────────────┼──────────────────────┤
│ Corporate CSR        │ Benevity    │ B2B dashboard with   │
│                      │             │ CSR features         │
├──────────────────────┼──────────────┼──────────────────────┤
│ Impact Dashboard     │ Galaxy      │ Analytics module      │
│                      │             │ + visualizations     │
└──────────────────────┴──────────────┴──────────────────────┘
```

### 2.4 WHAT NO ONE HAS (OUR MOAT)

```
UNIQUE COMBINATION:
1. Adaptive competency assessment (IRT-based)
2. Visual radar chart profiles
3. Sharable AURA Card (viral)
4. Behavioral reliability tracking
5. Elite badge system (earned, not bought)
6. B2B premium access to verified talent
7. Open Badges → LinkedIn integration
8. Gen Z gamification mechanics
9. Telegram-native experience
10. CIS/MENA regional focus
```

---

## SECTION 3: RISK ANALYSIS

### 3.1 STRATEGIC RISKS

```
┌─────────────────────────────────────────────────────────────┐
│                   STRATEGIC RISK MATRIX                      │
├─────────────────────┬─────────┬───────────────────────────┤
│ RISK                │ IMPACT  │ MITIGATION               │
├─────────────────────┼─────────┼───────────────────────────┤
│ Cold Start          │ CRITICAL│ WUF13 seeding + viral     │
│ (no volunteers)     │         │ loop + ASAN partnership     │
├─────────────────────┼─────────┼───────────────────────────┤
│ Cold Start          │ CRITICAL│ Free tier + pilot with     │
│ (no B2B clients)   │         │ trusted partners first     │
├─────────────────────┼─────────┼───────────────────────────┤
│ Founder Burnout     │ HIGH    │ Clear MVP scope +          │
│ (solo developer)    │         │ automation tools           │
├─────────────────────┼─────────┼───────────────────────────┤
│ WUF13 Cancellation  │ HIGH    │ Multiple event pipeline +  │
│                     │         │ alternative launches      │
├─────────────────────┼─────────┼───────────────────────────┤
│ AURA Score Backlash │ MEDIUM  │ Transparency +             │
│ (perceived as bias) │         │ "Reliability Pending"     │
├─────────────────────┼─────────┼───────────────────────────┤
│ Competitor Copy     │ MEDIUM  │ First mover + community +  │
│                     │         │ relationships             │
├─────────────────────┼─────────┼───────────────────────────┤
│ Market Timing       │ MEDIUM  │ Digital AZ government     │
│ (too early/late)   │         │ support + events calendar │
├─────────────────────┼─────────┼───────────────────────────┤
│ Regulatory Changes  │ LOW     │ Legal entity + compliance │
│                     │         │ monitoring               │
└─────────────────────┴─────────┴───────────────────────────┘
```

### 3.2 TECHNICAL RISKS

```
┌─────────────────────────────────────────────────────────────┐
│                  TECHNICAL RISK MATRIX                      │
├─────────────────────┬─────────┬───────────────────────────┤
│ RISK                │ IMPACT  │ MITIGATION               │
├─────────────────────┼─────────┼───────────────────────────┤
│ LLM Cost Explosion │ HIGH    │ Caching + Gemini free     │
│                     │         │ tier + budget alerts     │
├─────────────────────┼─────────┼───────────────────────────┤
│ IRT Calibration    │ HIGH    │ Start with seeded params  │
│ (wrong scoring)    │         │ + expert review           │
├─────────────────────┼─────────┼───────────────────────────┤
│ Supabase Outage    │ MEDIUM  │ Multi-region + backup    │
│                     │         │ + status page            │
├─────────────────────┼─────────┼───────────────────────────┤
│ Security Breach    │ CRITICAL│ RLS + row-level security  │
│ (user data leak)   │         │ + audits + encryption     │
├─────────────────────┼─────────┼───────────────────────────┤
│ Scale Limits       │ MEDIUM  │ Supabase Pro tier +      │
│ (free tier cap)    │         │ planning upgrade path     │
├─────────────────────┼─────────┼───────────────────────────┤
│ AI Hallucination   │ MEDIUM  │ Human review + rule-based│
│ (wrong evaluation) │         │ fallback + appeals        │
├─────────────────────┼─────────┼───────────────────────────┤
│ Mobile Performance │ LOW     │ PWA + optimization +     │
│                     │         │ lazy loading            │
├─────────────────────┼─────────┼───────────────────────────┤
│ Browser Compat.     │ LOW     │ Testing matrix +         │
│                     │         │ polyfills               │
└─────────────────────┴─────────┴───────────────────────────┘
```

### 3.3 MARKET RISKS

```
┌─────────────────────────────────────────────────────────────┐
│                   MARKET RISK MATRIX                         │
├─────────────────────┬─────────┬───────────────────────────┤
│ RISK                │ IMPACT  │ MITIGATION               │
├─────────────────────┼─────────┼───────────────────────────┤
│ Low Volunteer       │ HIGH    │ Viral loop + ASAN +       │
│ Adoption Rate       │         │ Gen Z targeting           │
├─────────────────────┼─────────┼───────────────────────────┤
│ B2B Willingness    │ HIGH    │ Free tier + clear ROI +   │
│ to Pay             │         │ pilot pricing             │
├─────────────────────┼─────────┼───────────────────────────┤
│ Trust Issues       │ MEDIUM  │ Transparency + verified   │
│ (new platform)     │         │ badges + testimonials     │
├─────────────────────┼─────────┼───────────────────────────┤
│ Telegram Dominance │ MEDIUM  │ Telegram-first + native  │
│ (users won't       │         │ bot experience            │
│ download app)      │         │                         │
├─────────────────────┼─────────┼───────────────────────────┤
│ Economic Downturn   │ MEDIUM  │ Government/nonprofit      │
│ (reduced CSR)      │         │ focus + resilience       │
├─────────────────────┼─────────┼───────────────────────────┤
│ Currency Risk       │ LOW     │ USD pricing + Stripe     │
│ (AZN volatility)   │         │ adaptive pricing         │
├─────────────────────┼─────────┼───────────────────────────┤
│ Political Changes  │ LOW     │ Regional diversification │
│                     │         │ in future               │
├─────────────────────┼─────────┼───────────────────────────┤
│ Language Barriers  │ LOW     │ Quality translation +     │
│ (content quality) │         │ native speakers review   │
└─────────────────────┴─────────┴───────────────────────────┘
```

### 3.4 OPERATIONAL RISKS

```
┌─────────────────────────────────────────────────────────────┐
│                  OPERATIONAL RISK MATRIX                     │
├─────────────────────┬─────────┬───────────────────────────┤
│ RISK                │ IMPACT  │ MITIGATION               │
├─────────────────────┼─────────┼───────────────────────────┤
│ Question Bank       │ HIGH    │ Kimi generator +          │
│ Bottleneck         │         │ content pipeline          │
├─────────────────────┼─────────┼───────────────────────────┤
│ Assessment Fraud   │ HIGH    │ Anti-gaming + behavioral  │
│                     │         │ signals + spot checks    │
├─────────────────────┼─────────┼───────────────────────────┤
│ No-show Prediction │ MEDIUM  │ Conservative matching +   │
│ Inaccuracy         │         │ coordinator alerts       │
├─────────────────────┼─────────┼───────────────────────────┤
│ Event Organizer    │ MEDIUM  │ Training + documentation │
│ Onboarding         │         │ + support channels       │
├─────────────────────┼─────────┼───────────────────────────┤
│ Content Moderation │ MEDIUM  │ Auto-moderation +        │
│                     │         │ community flags          │
├─────────────────────┼─────────┼───────────────────────────┤
│ Support Overload   │ MEDIUM  │ Self-service + FAQ +      │
│                     │         │ chatbot                  │
├─────────────────────┼─────────┼───────────────────────────┤
│ System Errors      │ LOW     │ Monitoring + alerts +     │
│ (wrong AURA calc) │         │ rollback procedures       │
├─────────────────────┼─────────┼───────────────────────────┤
│ Data Loss          │ CRITICAL│ Automated backups +       │
│                     │         │ export functionality     │
└─────────────────────┴─────────┴───────────────────────────┘
```

---

## SECTION 4: AZERBAIJAN MARKET ANALYSIS

### 4.1 MARKET SIZE & OPPORTUNITY

**TAM Calculation:**

```
Azerbaijan Demographics:
├── Total Population: 10.1M
├── Baku Population: 2.3M (23%)
├── Youth (18-35): ~2.5M
├── Urban Youth: ~1.5M
├── Potential Volunteers (5-8%): 75,000-120,000
└── Elite Tier (10-15%): 7,500-18,000

Event Market (Baku):
├── Annual Events: 500+ (conferences, sports, cultural)
├── Major Events: 10-15 (mega events with 1000+ volunteers)
├── Event Agencies: 50+
├── Corporations with CSR: 100+
└── NGOs: 200+

B2B Market (TAM):
├── NPOs/NGOs: 200 × $79/mo = $15,800/mo
├── Event Agencies: 50 × $199/mo = $9,950/mo
├── Corporate CSR: 30 × $499/mo = $14,970/mo
└── Total TAM: ~$40,720/mo = $488,640/yr

SAM (Azerbaijan only): $40,720/mo
SOM (realistic Year 1): $5,000-10,000/mo
```

### 4.2 TARGET SEGMENTS

**Volunteer Segments:**

```
1. University Students (18-22)
   ├── Motivation: CV building, networking, skills
   ├── Channels: University groups, ASAN
   ├── Preferred: Quick wins, badges, social sharing
   └── Pain: No way to prove experience

2. Young Professionals (23-28)
   ├── Motivation: Career advancement, networking
   ├── Channels: LinkedIn, Telegram, referrals
   ├── Preferred: Quality events, prestigious orgs
   └── Pain: Wasting time on disorganized events

3. Experienced Volunteers (29-40)
   ├── Motivation: Giving back, leadership
   ├── Channels: NGO networks, word of mouth
   ├── Preferred: Leadership roles, meaningful work
   └── Pain: Lack of recognition for experience

4. Corporate Employees (CSR programs)
   ├── Motivation: Team building, CSR requirements
   ├── Channels: HR departments, corporate portals
   ├── Preferred: Easy administration, reporting
   └── Pain: Manual volunteer coordination
```

**B2B Segments:**

```
1. Event Agencies (Primary)
   ├── Size: 10-50 employees
   ├── Pain: Volunteer coordination chaos
   ├── WTP: $99-199/mo
   └── Key Features: Search, filters, CSV export

2. International Organizations
   ├── Size: Enterprise
   ├── Pain: Compliance and verification
   ├── WTP: $299-499/mo
   └── Key Features: Background checks, API

3. NGOs/Nonprofits
   ├── Size: 5-20 staff
   ├── Pain: Limited budget, no tools
   ├── WTP: $0-79/mo (free tier acceptable)
   └── Key Features: Basic management, messaging

4. Corporate CSR
   ├── Size: HR team
   ├── Pain: Employee engagement tracking
   ├── WTP: $199-499/mo
   └── Key Features: Analytics, matching, reporting
```

### 4.3 AZERBAIJAN-SPECIFIC REQUIREMENTS

**Cultural Considerations:**

```
✅ Respect hierarchy and seniority
✅ Face-to-face relationship building before deals
✅ Government support for civic initiatives
✅ ASAN Service model (one-stop government)
✅ Telegram as primary communication
✅ Mobile-first everything
✅ Trust badges and verification
✅ Community/peer recommendations

⚠️ Avoid:
- Cold outreach (relationship-first)
- Complex onboarding (ASAN simplicity)
- English-only (AZ primary)
- Expensive pricing (value-first)
```

**Language Requirements:**

```
Content Language Distribution:
├── Azerbaijani (AZ): 70% — PRIMARY
├── English (EN): 20% — SECONDARY
├── Russian (RU): 10% — OPTIONAL (legacy speakers)
└── Turkish: Helpful for localization

Technical:
- RTL: NO (AZ is LTR)
- Character encoding: UTF-8 everywhere
- Date format: DD.MM.YYYY (European)
- Currency: AZN display, USD pricing
```

**Payment Infrastructure:**

```
Available:
✅ Bank cards (Kapitalbank, Pasha Bank, AccessBank)
✅ E-GOV portal integration (future)
✅ Stripe (international cards)
✅ Local payment gateways (Milli, eManat)

Challenges:
⚠️ Low credit card penetration (30-40%)
⚠️ Cash preference in some segments
⚠️ Currency: 1.7 AZN = 1 USD (pegged)
```

### 4.4 AZERBAIJAN EVENT LANDSCAPE

**Major Annual Events:**

```
Q1 (January-March):
├── Davos-ish Global Economic Forum
├── Baku International Film Festival
└── Caspian Energy Forum

Q2 (April-June):
├── Formula 1 Azerbaijan Grand Prix
├── Baku International Marathon
├── World Urban Forum (WUF13) - MAY 2026
└── Eurovision Song Contest (if hosted)

Q3 (July-September):
├── Baku Sea Festival
├── Caspian Games
└── International Jazz Festival

Q4 (October-December):
├── Baku International Education Fair
├── Caspian Renewable Energy Week
└── Corporate year-end events

Ongoing:
├── UN/Sport events (40+ annually)
├── Diplomatic receptions (100+ annually)
├── Corporate summits (200+ annually)
└── Cultural festivals (50+ annually)
```

**Key Event Organizers:**

```
International in Baku:
├── UN Azerbaijan
├── British Embassy / FCDO
├── US Embassy / USAID
├── EU Delegation
├── World Bank / IMF
├── SOCAR
├── BP Azerbaijan
├── OPEC
└── Caspian European Club

Local Event Agencies:
├── Caspian Events Group
├── Baku Congress Service
├── Premium Events
├── Azerbaijan Tourism Board
├── ADA University Events
└── ASAN Service Events
```

### 4.5 AZERBAIJAN SKILLS REQUIREMENTS

**Most In-Demand Volunteer Skills:**

```
Hard Skills (by demand):
1. English (B1-B2) — 85% of events
2. First Aid/CPR — 70%
3. IT/Technical Support — 60%
4. Photography/Video — 55%
5. Foreign Languages (RU, TR, FR, DE) — 50%
6. Driver's License — 45%
7. Social Media — 40%
8. Catering/ Hospitality — 35%
9. Security Protocols — 30%
10. Data Entry — 25%

Soft Skills (by demand):
1. Communication — 90%
2. Teamwork — 85%
3. Punctuality — 80%
4. Adaptability — 75%
5. Problem Solving — 70%
6. Leadership — 60%
7. Customer Service — 55%
8. Conflict Resolution — 45%
9. Cultural Awareness — 40%
10. Stress Management — 35%
```

---

## SECTION 5: SKILLS & COMPETENCIES TO LOAD

### 5.1 TECHNICAL SKILLS (Frontend)

```
REQUIRED:
├── Next.js 14+ (App Router)
├── TypeScript 5+
├── React 18+
├── Tailwind CSS 4+
├── Zustand or TanStack Query
├── React Hook Form + Zod
├── Recharts or Chart.js
├── react-i18next
└── Git/GitHub workflows

RECOMMENDED:
├── Framer Motion (animations)
├── Playwright (E2E testing)
├── Vitest (unit testing)
├── PWA (next-pwa)
├── Turborepo (monorepo)
└── Storybook (component library)

NICE TO HAVE:
├── Three.js (3D elements)
├── D3.js (advanced charts)
├── Radix UI (accessibility)
└── tRPC (type-safe APIs)
```

### 5.2 TECHNICAL SKILLS (Backend)

```
REQUIRED:
├── Python 3.11+
├── FastAPI
├── SQLAlchemy 2.0+
├── PostgreSQL
├── Supabase SDK
├── asyncpg
├── Pydantic 2.0+
├── JWT/Auth
└── Git/GitHub

RECOMMENDED:
├── Celery + Redis (background jobs)
├── Alembic (migrations)
├── pytest + pytest-asyncio
├── OpenTelemetry (observability)
├── Redis (caching)
└── Docker + Docker Compose

AI/ML:
├── Gemini SDK
├── OpenAI SDK
├── pgvector
├── NumPy + Pandas
└── Scikit-learn (basic ML)
```

### 5.3 PRODUCT SKILLS

```
REQUIRED:
├── User research (surveys, interviews)
├── UX writing (microcopy)
├── A/B testing design
├── Analytics setup (Supabase Analytics)
├── Feature prioritization (RICE, MoSCoW)
└── Roadmap planning

RECOMMENDED:
├── Figma (design collaboration)
├── Notion/Obsidian (documentation)
├── Linear/Jira (project management)
├── Mixpanel/Amplitude (product analytics)
└── Hotjar (user behavior)
```

### 5.4 GROWTH & MARKETING SKILLS

```
REQUIRED:
├── Telegram community building
├── Viral loop design
├── Referral program mechanics
├── Content marketing (AZ market)
└── Social media (Instagram, LinkedIn)

RECOMMENDED:
├── SEO (local AZ)
├── Paid acquisition (Meta, Google)
├── Influencer partnerships
├── PR/media relations
└── Event marketing

COPYWRITING:
├── Landing page copy
├── Email sequences
├── Push notifications (Gen Z tone)
├── Social media posts
└── B2B sales collateral
```

### 5.5 BUSINESS & SALES SKILLS

```
REQUIRED:
├── B2B sales (relationship-based)
├── Cold outreach (AZ style)
├── Pricing strategy
├── Contract negotiation
└── Financial modeling

RECOMMENDED:
├── Grant writing (EU, USAID, UNDP)
├── Partnership development
├── Legal entity setup (AZ)
├── Tax optimization (SMBDA)
└── Investor pitch preparation
```

---

## SECTION 6: OPEN-SOURCE SOLUTIONS TO LEVERAGE

### 6.1 ASSESSMENT & EDUCATION

```
adaptivetesting (PyPI)
├── Purpose: IRT/CAT implementation
├── Features: Bayesian estimation, multiple IRT models
├── Status: Production ready
└── Use: Core assessment engine

EduCAT (GitHub - bigdata-ustc)
├── Purpose: Educational assessment system
├── Features: Question bank, adaptive testing
├── Status: Academic, needs adaptation
└── Use: Reference architecture

Open edX (GitHub)
├── Purpose: LMS platform
├── Features: Courses, assessments, certificates
├── Status: Production
└── Use: Volaura Academy (future)

xAPI (Rust)
├── Purpose: Learning analytics
├── Features: Track any learning experience
├── Status: Stable
└── Use: Competency tracking
```

### 6.2 GAMIFICATION & BADGES

```
Open Badges (IMS Global)
├── Purpose: Portable digital badges
├── Features: Badge definitions, issuance, verification
├── Standard: Open Badges 3.0
└── Use: AURA Badge export to LinkedIn

BadgeKit (GitHub - MozFest)
├── Purpose: Badge creation and issuing
├── Features: Badge design, criteria, evidence
├── Status: Archived but reference
└── Use: Badge system patterns

GamifyYourCourse (GitHub)
├── Purpose: Gamification for learning
├── Features: Points, badges, leaderboards
├── Status: Reference
└── Use: Gamification mechanics

Badgr (GitHub - eALot)
├── Purpose: Open Badge issuer
├── Features: Issue, earn, display badges
├── Status: Production
└── Use: Badge management infrastructure
```

### 6.3 MATCHING & AI

```
pgvector (PostgreSQL extension)
├── Purpose: Vector similarity search
├── Features: Cosine distance, ANN indexing
├── Status: Supabase built-in
└── Use: Semantic volunteer matching

LangChain
├── Purpose: LLM application framework
├── Features: Chains, agents, memory
├── Status: Production
└── Use: LLM wrapper for evaluation

sentence-transformers
├── Purpose: Text embeddings
├── Features: 100+ languages, fast inference
├── Status: Production
└── Use: Profile/job embedding generation

RecBole (GitHub - RUC)
├── Purpose: Recommender systems
├── Features: 70+ algorithms, evaluation
├── Status: Research
└── Use: Advanced matching algorithms
```

### 6.4 BACKEND & INFRASTRUCTURE

```
FastAPI
├── Purpose: Python web framework
├── Features: Async, Pydantic, OpenAPI
├── Status: Production
└── Use: API layer

Supabase
├── Purpose: Firebase alternative
├── Features: Auth, DB, Storage, Realtime, Edge Functions
├── Status: Production
└── Use: Database, auth, backend

Railway
├── Purpose: Cloud hosting
├── Features: Deploy from Git, pay-per-use
├── Status: Production
└── Use: FastAPI deployment

Vercel
├── Purpose: Next.js hosting
├── Features: Edge network, auto-deploy, OG images
├── Status: Production
└── Use: Frontend deployment, OG generation

Stripe
├── Purpose: Payments
├── Features: Subscriptions, invoicing, local payment methods
├── Status: Production
└── Use: B2B billing
```

### 6.5 COMMUNITY & MESSAGING

```
python-telegram-bot
├── Purpose: Telegram Bot API
├── Features: Polling, webhooks, inline keyboards
├── Status: Production
└── Use: Telegram notifications, check-in

Stream Chat
├── Purpose: Chat/messaging API
├── Features: Channels, reactions, moderation
├── Status: Production (paid)
└── Use: In-app chat (future)

Discord.js
├── Purpose: Discord bot/API
├── Features: Slash commands, embeds, webhooks
├── Status: Production
└── Use: Community management reference

Rocket.Chat
├── Purpose: Open source Slack alternative
├── Features: Channels, DMs, video calls
├── Status: Production
└── Use: Self-hosted chat option
```

---

## SECTION 7: WHAT'S MISSING & GAPS

### 7.1 PRODUCT GAPS

```
NOT YET DEFINED:

1. CV Parser Module
   - Should we auto-parse LinkedIn/resume?
   - Integration with which services?
   - Fallback to manual entry?

2. Question Bank Management UI
   - Admin interface for adding questions?
   - Approval workflow?
   - Version control?

3. Appeals Process
   - What if volunteer disagrees with AURA?
   - Re-assessment policy?
   - Human review?

4. Organization Verification
   - How do we verify orgs?
   - What badges for orgs?
   - Trust score mechanics?

5. Pricing for Volunteers
   - $4.99 badge only?
   - Premium features?
   - What about employer-pays model?

6. International Expansion
   - Language additions (TR, RU native)?
   - Country-specific adaptations?
   - Data residency?
```

### 7.2 TECHNICAL GAPS

```
NOT YET DEFINED:

1. Notification Preferences
   - Granular notification settings?
   - Quiet hours?
   - Channel preferences (email/SMS/TG)?

2. Offline Mode
   - Can volunteers use app offline?
   - Sync when back online?
   - What features offline?

3. Data Export
   - Can volunteers export their data?
   - GDPR-like rights?
   - Export formats?

4. Performance at Scale
   - Load testing results?
   - Caching strategy?
   - CDN configuration?

5. Monitoring & Alerting
   - What metrics to track?
   - Alert thresholds?
   - On-call rotation?

6. Disaster Recovery
   - RTO/RPO targets?
   - Backup frequency?
   - Recovery procedures?
```

### 7.3 BUSINESS GAPS

```
NOT YET DEFINED:

1. Legal Entity
   - IP LLC or local AZ entity?
   - Tax residency?
   - Bank account?

2. Contracts & Terms
   - Volunteer terms of service?
   - B2B SLA?
   - Liability insurance?

3. Revenue Operations
   - Who does B2B sales?
   - Customer support model?
   - Billing operations?

4. Partnerships
   - Formal partnership agreements?
   - Revenue sharing?
   - Co-marketing?

5. Metrics & OKRs
   - What to measure?
   - North Star metric?
   - Quarterly goals?

6. Investor Strategy
   - Bootstrap to profitability?
   - Seek seed funding?
   - Apply for grants only?
```

---

## SECTION 8: FINAL QUESTIONS FOR ANALYSIS

### 8.1 ARCHITECTURE QUESTIONS

1. Is the microservices approach (separate FastAPI) correct for solo dev, or should everything be Next.js API routes?

2. Should we use tRPC for type-safe APIs between frontend and backend?

3. What's the optimal caching strategy for LLM evaluations?

4. How to handle multi-tenancy for B2B organizations?

5. Should we use Edge Functions or serverless for specific features?

### 8.2 COMPETITOR QUESTIONS

6. What specific UI patterns from POINT App should we copy?

7. How did Catchafire implement outcome valuation?

8. What's Benevity's gamification system structure?

9. How does Galaxy Digital calculate reliability scores?

10. What makes VolunteerMatch's search so effective?

### 8.3 RISK QUESTIONS

11. What's the biggest risk of the elite club positioning?

12. How to mitigate cold start without cheap/free tactics?

13. What's the risk of WUF13 cancellation? Alternative plans?

14. How to handle AURA score disputes?

15. What security certifications should we pursue?

### 8.4 MARKET QUESTIONS

16. What's the real B2B willingness to pay in Azerbaijan?

17. How to approach SOCAR/Kapital Bank CSR departments?

18. What's the best channel for ASAN partnership?

19. How to handle Russian-speaking population?

20. What local payment methods are essential?

### 8.5 SKILLS QUESTIONS

21. Should we hire or outsource specific skills?

22. What's the realistic timeline with solo dev?

23. Which skills can AI/Claude Code replace?

24. What community skills are most important?

25. How to build the first B2B sales relationship?

---

## DELIVERABLE FORMAT

Analyze the above context and provide:

### 1. EXECUTIVE SUMMARY
(3-4 sentences on overall assessment)

### 2. ARCHITECTURE RECOMMENDATIONS
- Module breakdown
- Technology decisions
- Integration points
- Gaps to fill

### 3. COMPETITOR ANALYSIS
- Features to steal (specific)
- Implementation approach
- Differentiation strategy

### 4. RISK MITIGATION PLAN
- Top 5 risks with mitigation
- Contingency plans
- Early warning indicators

### 5. AZERBAIJAN MARKET ENTRY
- Pricing validation
- Partnership priorities
- Go-to-market tactics
- Local adaptation needs

### 6. SKILLS LOADING PLAN
- Immediate priorities
- AI augmentation strategy
- Hiring/f outsourcing decisions
- Timeline for skill acquisition

### 7. MISSING PIECES
- What's not defined
- What's critical to define
- Recommendations for each gap

### 8. ACTION PLAN
- Next 30 days
- Next 90 days
- WUF13 launch checklist
- Post-launch priorities

---

## CONTEXT FILES AVAILABLE

If available, analyze these files from the conversation:
1. Previous architecture documents
2. Code review from Kimi
3. Financial model
4. Survey drafts
5. Research outputs from Gemini

---

## IMPORTANT REMINDERS

- Write in Russian (user's language)
- Be specific and actionable
- Use data from conversation when available
- Mark "не определено" for unknown information
- Focus on what makes Volaura unique
- Consider solo developer constraints
- Prioritize viral growth from day 1
- Remember: Elite Club, not volunteer database