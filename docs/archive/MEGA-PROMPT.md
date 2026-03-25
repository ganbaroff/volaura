# VOLAURA — Full Stack Generation Prompt

> Один промпт. Внутри — 8 модулей. Отправляй целиком или по модулям.
> Основан на 32 документах базы знаний проекта.

---

## SYSTEM CONTEXT

You are building **Volaura** — a verified competency platform and community for the best volunteers. This is NOT "another volunteer platform" — it's a platform where skills are verified through AI-powered assessment, organizations CHOOSE proven talent, and volunteers ASPIRE to be listed.

**Core concept:**
- Volunteers take an adaptive assessment across 8 competencies → get AURA composite score (0-100) → badge tier (Platinum/Gold/Silver/Bronze)
- Organizations search verified volunteers, post events, attest volunteer skills post-event
- Every event (COP29, CIS Games, conferences, etc.) is dynamic data with live volunteer counters
- AI coaching, smart matching, live social proof — the platform feels alive, not static
- Azerbaijan first, CIS/MENA expansion later

**CRITICAL: Events are dynamic data. NEVER hardcode specific event names, dates, or branding. Any organization can create any event.**

### Tech Stack (MANDATORY — do not substitute)

**Frontend (apps/web/):**
- Next.js 14 App Router (ONLY — never Pages Router)
- TypeScript 5 strict mode (no `any`)
- Tailwind CSS 4 (CSS-first: `@import "tailwindcss"`, `@theme {}` block, NO tailwind.config.js)
- shadcn/ui (base components, customized via cn())
- Framer Motion (all animations)
- Recharts (radar chart, line chart)
- react-i18next (AZ primary, EN secondary)
- Zustand (client state)
- TanStack Query v5 (server state)
- React Hook Form + Zod (forms)
- @ducanh2912/next-pwa (PWA)

**Backend (apps/api/):**
- Python 3.11+ with FastAPI (async)
- Supabase async SDK — per-request client via `Depends()`, NEVER global
- Pydantic v2 (ConfigDict, @field_validator — NEVER v1 syntax)
- google-genai SDK (Gemini 2.5 Flash — primary LLM)
- loguru (logging — NEVER print())
- Resend (email)

**Database:**
- Supabase PostgreSQL + RLS on ALL tables
- pgvector with vector(768) — Gemini embeddings (NOT 1536/OpenAI)
- All vector ops via RPC functions only

**Monorepo:**
- Turborepo + pnpm workspaces
- `apps/web/` (Next.js), `apps/api/` (FastAPI), `supabase/` (migrations), `packages/` (shared configs)

### File Naming Rules
- TypeScript: kebab-case files, PascalCase components
- Python: snake_case everywhere
- SQL: snake_case tables and columns
- Import alias: `@/` → `apps/web/src/`

---

## DESIGN SYSTEM

### Colors (oklch — use EXACTLY these values)

In Tailwind CSS 4, custom colors use `--color-*` prefix inside `@theme {}`:

```css
/* globals.css — inside @theme {} — Tailwind CSS 4 format */
--color-background: oklch(0.985 0.002 260);
--color-foreground: oklch(0.15 0.03 260);
--color-card: oklch(1 0 0);
--color-primary: oklch(0.55 0.24 264);       /* Indigo — main CTA */
--color-primary-hover: oklch(0.48 0.24 264);
--color-secondary: oklch(0.97 0.005 260);
--color-muted: oklch(0.55 0.03 260);
--color-accent: oklch(0.65 0.20 264);
--color-destructive: oklch(0.58 0.24 27);
--color-border: oklch(0.93 0.005 260);
--color-success: oklch(0.70 0.17 165);
--color-warning: oklch(0.75 0.18 80);

/* Badge tier colors */
--color-platinum: oklch(0.85 0.05 270);
--color-gold: oklch(0.80 0.18 85);
--color-silver: oklch(0.75 0.03 260);
--color-bronze: oklch(0.65 0.12 55);

/* Usage in Tailwind: bg-primary, text-foreground, border-border, etc. */
/* Dark mode: override in .dark {} class — see globals.css below */
```

### Typography
- Body: `Inter` (Google Fonts)
- Scores/Numbers: `JetBrains Mono` (monospace)
- Scale: 12/14/16/18/20/24/30/36/48/60px

### Animation Springs (Framer Motion)
```ts
const springs = {
  default: { stiffness: 260, damping: 20 },
  gentle:  { stiffness: 120, damping: 14 },
  bouncy:  { stiffness: 400, damping: 10 },
  stiff:   { stiffness: 500, damping: 30 },
};
```
All animations MUST respect `prefers-reduced-motion`.

### Spacing: 4px base unit. Border radius: 12px default, 16px cards, 999px pills.
### Breakpoints: 640 / 768 / 1024 / 1280 / 1536px.
### Touch targets: minimum 44×44px.

---

## DATABASE SCHEMA

### Enums
```sql
CREATE TYPE badge_tier AS ENUM ('none', 'bronze', 'silver', 'gold', 'platinum');
CREATE TYPE competency_type AS ENUM (
  'communication', 'reliability', 'english_proficiency', 'leadership',
  'event_performance', 'tech_literacy', 'adaptability', 'empathy_safeguarding'
);
CREATE TYPE question_type AS ENUM ('bars', 'mcq', 'open_text');
CREATE TYPE verification_level AS ENUM ('self_assessed', 'org_attested', 'peer_verified');
CREATE TYPE user_role AS ENUM ('volunteer', 'org_admin', 'platform_admin');
CREATE TYPE assessment_status AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE event_status AS ENUM ('draft', 'upcoming', 'open', 'full', 'in_progress', 'completed', 'cancelled');
CREATE TYPE registration_status AS ENUM ('registered', 'attended', 'no_show', 'cancelled');
```

### Core Tables (all have RLS enabled)

**profiles** — extends Supabase auth.users
```sql
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  avatar_url TEXT,
  bio TEXT,
  city TEXT,
  country TEXT DEFAULT 'AZ',
  expertise TEXT[] DEFAULT '{}',
  languages TEXT[] DEFAULT '{az}',
  role user_role DEFAULT 'volunteer',
  verification_level verification_level DEFAULT 'self_assessed',
  locale TEXT DEFAULT 'az' CHECK (locale IN ('az', 'en')),
  referral_code TEXT UNIQUE,
  referred_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  is_public BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public profiles are viewable by everyone" ON profiles FOR SELECT USING (is_public = true);
CREATE POLICY "Users can read own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
```

**aura_scores**
```sql
CREATE TABLE public.aura_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  composite_score SMALLINT NOT NULL CHECK (composite_score BETWEEN 0 AND 100),
  tier badge_tier NOT NULL,
  reliability_factor FLOAT CHECK (reliability_factor BETWEEN 0.85 AND 1.0),
  is_current BOOLEAN DEFAULT true,
  percentile FLOAT,
  events_attended INT DEFAULT 0,
  calculated_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX idx_aura_scores_current ON aura_scores (user_id) WHERE is_current = true;

ALTER TABLE public.aura_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own scores" ON aura_scores FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Public scores viewable" ON aura_scores FOR SELECT
  USING (EXISTS (SELECT 1 FROM profiles WHERE profiles.id = aura_scores.user_id AND profiles.is_public = true));
```

**competency_scores**
```sql
CREATE TABLE public.competency_scores (
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  competency competency_type,
  score SMALLINT CHECK (score BETWEEN 0 AND 100),
  weight FLOAT NOT NULL,
  verification_level verification_level DEFAULT 'self_assessed',
  questions_count INT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, competency)
);

ALTER TABLE public.competency_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own competency scores" ON competency_scores FOR SELECT USING (auth.uid() = user_id);
```

**questions**
```sql
CREATE TABLE public.questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competency competency_type NOT NULL,
  type question_type NOT NULL,
  difficulty_level SMALLINT CHECK (difficulty_level BETWEEN 1 AND 3),
  text_az TEXT NOT NULL,
  text_en TEXT NOT NULL,
  options_az JSONB,        -- MCQ: [{"label":"...", "value":"a", "score_weight":0.8}]
  options_en JSONB,
  bars_anchors_az JSONB,   -- BARS: [{"level":1, "description":"..."}, ... {"level":7, "description":"..."}]
  bars_anchors_en JSONB,
  rubric_az TEXT,           -- open_text: LLM evaluation rubric
  rubric_en TEXT,
  max_words INT,            -- open_text word limit
  irt_a FLOAT DEFAULT 1.0,  -- discrimination
  irt_b FLOAT DEFAULT 0.0,  -- difficulty
  irt_c FLOAT DEFAULT 0.25, -- guessing
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Questions readable by authenticated" ON questions FOR SELECT TO authenticated USING (is_active = true);
```

**assessments**
```sql
CREATE TABLE public.assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  competency competency_type NOT NULL,
  status assessment_status DEFAULT 'in_progress',
  current_difficulty SMALLINT DEFAULT 1,
  questions_answered INT DEFAULT 0,
  final_score SMALLINT,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own assessments" ON assessments FOR ALL USING (auth.uid() = user_id);
```

**assessment_responses**
```sql
CREATE TABLE public.assessment_responses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES questions(id),
  response_value JSONB NOT NULL,
  score FLOAT,
  llm_score FLOAT,
  llm_feedback JSONB,
  time_spent_seconds INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.assessment_responses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own responses" ON assessment_responses FOR ALL
  USING (EXISTS (SELECT 1 FROM assessments WHERE assessments.id = assessment_responses.assessment_id AND assessments.user_id = auth.uid()));
```

**organizations**
```sql
CREATE TYPE org_plan AS ENUM ('starter', 'growth', 'enterprise');

CREATE TABLE public.organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT,
  logo_url TEXT,
  website TEXT,
  contact_email TEXT,
  is_verified BOOLEAN DEFAULT false,
  plan org_plan DEFAULT 'starter',
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Orgs viewable by everyone" ON organizations FOR SELECT USING (true);
```

**org_members** — links users to organizations
```sql
CREATE TABLE public.org_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  joined_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(org_id, user_id)
);

ALTER TABLE public.org_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Members can read own org" ON org_members FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Org admins can manage members" ON org_members FOR ALL
  USING (EXISTS (SELECT 1 FROM org_members om WHERE om.org_id = org_members.org_id AND om.user_id = auth.uid() AND om.role IN ('owner', 'admin')));
```

**events**
```sql
CREATE TABLE public.events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title_en TEXT NOT NULL,
  title_az TEXT NOT NULL,
  description_en TEXT,
  description_az TEXT,
  date_start TIMESTAMPTZ NOT NULL,
  date_end TIMESTAMPTZ,
  location TEXT,
  location_lat FLOAT,
  location_lng FLOAT,
  min_aura_score SMALLINT DEFAULT 0,
  required_competencies competency_type[],
  capacity INT,
  registered_count INT DEFAULT 0,
  status event_status DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Published events viewable" ON events FOR SELECT USING (status != 'draft');
CREATE POLICY "Org admins can manage events" ON events FOR ALL
  USING (EXISTS (SELECT 1 FROM org_members WHERE org_members.org_id = events.org_id AND org_members.user_id = auth.uid() AND org_members.role IN ('owner', 'admin')));
```

**event_registrations**
```sql
CREATE TABLE public.event_registrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  status registration_status DEFAULT 'registered',
  org_rating SMALLINT CHECK (org_rating BETWEEN 1 AND 5),
  org_feedback TEXT,
  registered_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(event_id, user_id)
);

ALTER TABLE public.event_registrations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own registrations" ON event_registrations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can register" ON event_registrations FOR INSERT WITH CHECK (auth.uid() = user_id);
```

**notifications**
```sql
CREATE TABLE public.notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  title_az TEXT NOT NULL,
  title_en TEXT NOT NULL,
  body_az TEXT,
  body_en TEXT,
  action_url TEXT,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own notifications" ON notifications FOR ALL USING (auth.uid() = user_id);
```

**volunteer_embeddings**
```sql
CREATE TABLE public.volunteer_embeddings (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  embedding VECTOR(768) NOT NULL,
  metadata JSONB DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_embeddings_ivfflat ON volunteer_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

ALTER TABLE public.volunteer_embeddings ENABLE ROW LEVEL SECURITY;
-- Direct access blocked: match_volunteers() uses SECURITY DEFINER to bypass RLS
CREATE POLICY "Users can read own embedding" ON volunteer_embeddings FOR SELECT USING (auth.uid() = user_id);
-- Org search goes through match_volunteers() RPC which has SECURITY DEFINER
```

**referrals**
```sql
CREATE TABLE public.referrals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  referee_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  referral_code TEXT NOT NULL,
  converted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own referrals" ON referrals FOR SELECT USING (auth.uid() = referrer_id);
```

**badge_history**
```sql
CREATE TABLE public.badge_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  old_tier badge_tier,
  new_tier badge_tier NOT NULL,
  old_score SMALLINT,
  new_score SMALLINT NOT NULL,
  trigger TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.badge_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own badge history" ON badge_history FOR SELECT USING (auth.uid() = user_id);
```

### Sample Seed Data (2-3 questions per type for testing)
```sql
INSERT INTO questions (competency, type, difficulty_level, text_az, text_en, bars_anchors_az, bars_anchors_en) VALUES
('communication', 'bars', 1,
 'Komanda üzvləri ilə ünsiyyətinizi necə qiymətləndirirsiniz?',
 'How would you rate your communication with team members?',
 '[{"level":1,"description":"Heç vaxt ünsiyyət qurmuram"},{"level":4,"description":"Lazım olanda ünsiyyət qururam"},{"level":7,"description":"Aktiv və effektiv ünsiyyət qururam"}]',
 '[{"level":1,"description":"Never communicate"},{"level":4,"description":"Communicate when needed"},{"level":7,"description":"Proactively and effectively communicate"}]'
);

INSERT INTO questions (competency, type, difficulty_level, text_az, text_en, options_az, options_en) VALUES
('english_proficiency', 'mcq', 2,
 'Aşağıdakı cümlədə boşluğu doldurun: "The volunteers ___ already arrived."',
 'Fill in the blank: "The volunteers ___ already arrived."',
 '[{"label":"has","value":"a","score_weight":0.0},{"label":"have","value":"b","score_weight":1.0},{"label":"is","value":"c","score_weight":0.0},{"label":"are","value":"d","score_weight":0.1}]',
 '[{"label":"has","value":"a","score_weight":0.0},{"label":"have","value":"b","score_weight":1.0},{"label":"is","value":"c","score_weight":0.0},{"label":"are","value":"d","score_weight":0.1}]'
);

INSERT INTO questions (competency, type, difficulty_level, text_az, text_en, rubric_az, rubric_en, max_words) VALUES
('leadership', 'open_text', 2,
 'Çətin vəziyyətdə komandanızı necə motivasiya edərdiniz? Konkret bir nümunə təsvir edin.',
 'How would you motivate your team in a difficult situation? Describe a specific example.',
 'Qiymətləndirmə: 1) Konkret nümunə varmı? 2) Liderlik davranışı göstərilib? 3) Nəticə təsvir edilib?',
 'Evaluate: 1) Is there a specific example? 2) Does it show leadership behavior? 3) Is the outcome described?',
 200
);
```

### Performance Indexes
```sql
CREATE INDEX idx_assessments_user_status ON assessments(user_id, status);
CREATE INDEX idx_assessments_user_competency ON assessments(user_id, competency);
CREATE INDEX idx_event_registrations_event ON event_registrations(event_id, status);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_badge_history_user ON badge_history(user_id, created_at DESC);
CREATE INDEX idx_competency_scores_user ON competency_scores(user_id);
```

### Key RPC Functions
```sql
CREATE OR REPLACE FUNCTION match_volunteers(
  query_embedding VECTOR(768),
  match_count INT,
  min_aura FLOAT DEFAULT 0
) RETURNS TABLE(volunteer_id UUID, similarity FLOAT)
LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  RETURN QUERY
  SELECT ve.user_id,
         1 - (ve.embedding <=> query_embedding) AS similarity
  FROM volunteer_embeddings ve
  JOIN aura_scores a ON ve.user_id = a.user_id AND a.is_current = true
  WHERE a.composite_score >= min_aura
  ORDER BY ve.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION get_leaderboard(
  p_limit INT DEFAULT 50,
  p_offset INT DEFAULT 0
) RETURNS TABLE(user_id UUID, username TEXT, full_name TEXT, avatar_url TEXT, composite_score SMALLINT, tier badge_tier, rank BIGINT)
LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  RETURN QUERY
  SELECT p.id, p.username, p.full_name, p.avatar_url, a.composite_score, a.tier,
         ROW_NUMBER() OVER (ORDER BY a.composite_score DESC) AS rank
  FROM profiles p
  JOIN aura_scores a ON p.id = a.user_id AND a.is_current = true
  WHERE p.is_public = true AND p.role = 'volunteer'
  ORDER BY a.composite_score DESC
  LIMIT p_limit OFFSET p_offset;
END;
$$;
```

---

## MODULE 1: Project Setup & Layout Shell

### File Structure
```
apps/
  web/
    src/
      app/
        middleware.ts          # Auth check + i18n locale redirect
        [locale]/
          layout.tsx          # Root layout with i18n provider
          page.tsx            # Landing page
          error.tsx           # Global error boundary
          not-found.tsx       # 404 page
          loading.tsx         # Global loading skeleton
          (auth)/
            login/page.tsx
            callback/page.tsx
          (app)/
            layout.tsx        # App shell (sidebar + bottom nav)
            dashboard/page.tsx
            assessment/
              page.tsx        # Assessment hub
              [id]/page.tsx   # Active assessment
            profile/
              page.tsx        # Own profile
            leaderboard/page.tsx
            events/
              page.tsx
              [id]/page.tsx
            settings/page.tsx
            notifications/page.tsx
          (public)/
            u/[username]/page.tsx  # Public profile
        i18n.ts
        globals.css
      components/
        ui/                   # shadcn/ui base
        features/             # Feature components
          navigation/
            app-sidebar.tsx
            bottom-nav.tsx
            top-bar.tsx
          assessment/
            question-card.tsx
            bars-scale.tsx
            mcq-options.tsx
            open-text-input.tsx
            assessment-progress.tsx
          score/
            aura-display.tsx
            radar-chart.tsx
            badge-chip.tsx
            score-counter.tsx
          profile/
            profile-header.tsx
            competency-breakdown.tsx
            share-buttons.tsx
            verification-badges.tsx
          events/
            event-card.tsx
            event-list.tsx
          common/
            language-switcher.tsx
            theme-toggle.tsx
            empty-state.tsx
            loading-skeleton.tsx
            confetti.tsx
      lib/
        supabase/
          client.ts           # Browser client
          server.ts           # Server component client
          middleware.ts
        api/
          generated/          # @hey-api/openapi-ts output
        utils/
          cn.ts
          format.ts
      stores/
        auth-store.ts
        assessment-store.ts
        ui-store.ts
      locales/
        az/
          common.json
          auth.json
          assessment.json
          results.json
          profile.json
          events.json
          errors.json
        en/
          (same files)
      types/
        index.ts
    public/
      icons/
      manifest.json
    next.config.ts
    postcss.config.ts         # @tailwindcss/postcss
    tsconfig.json
  api/
    app/
      __init__.py
      main.py                 # FastAPI app
      config.py               # Settings (pydantic-settings)
      deps.py                 # Depends(): SupabaseUser, SupabaseAdmin, CurrentUserId
      routers/
        __init__.py
        auth.py
        profiles.py
        assessments.py
        scores.py
        events.py
        organizations.py
        verifications.py
        notifications.py
        share.py
        admin.py
      services/
        __init__.py
        assessment_engine.py  # Question selection, scoring
        aura_calculator.py    # AURA composite score
        llm.py                # Gemini evaluation
        email.py              # Resend integration
        embedding.py          # Vector embedding generation
      models/
        __init__.py
        schemas.py            # All Pydantic models
    requirements.txt
    Dockerfile
supabase/
  migrations/
    00001_extensions.sql
    00002_enums.sql
    00003_profiles.sql
    00004_questions.sql
    00005_assessments.sql
    00006_aura_scores.sql
    00007_events.sql
    00008_organizations.sql
    00009_notifications_referrals.sql
    00010_embeddings.sql
  seed.sql
packages/
  eslint-config/
  typescript-config/
turbo.json
pnpm-workspace.yaml
```

### Layout Implementation

**Root Layout** (`app/[locale]/layout.tsx`):
```tsx
import { Inter, JetBrains_Mono } from "next/font/google";
import TranslationsProvider from "@/components/providers/translations-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import initTranslations from "@/app/i18n";
import "@/app/globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

const i18nNamespaces = ["common", "auth", "assessment", "results", "profile", "events", "errors"];

export function generateStaticParams() {
  return [{ locale: "az" }, { locale: "en" }];
}

export default async function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const { resources } = await initTranslations(locale, i18nNamespaces);

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrains.variable} font-sans antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          <TranslationsProvider locale={locale} namespaces={i18nNamespaces} resources={resources}>
            {children}
          </TranslationsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**App Shell** (`app/[locale]/(app)/layout.tsx`):
```tsx
"use client";
import { AppSidebar } from "@/components/features/navigation/app-sidebar";
import { BottomNav } from "@/components/features/navigation/bottom-nav";
import { TopBar } from "@/components/features/navigation/top-bar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <AppSidebar className="hidden lg:flex" />
      <div className="flex flex-1 flex-col">
        <TopBar />
        <main className="flex-1 px-4 py-6 lg:px-8">{children}</main>
        <BottomNav className="lg:hidden" />
      </div>
    </div>
  );
}
```

### globals.css (Tailwind CSS 4)
```css
@import "tailwindcss";

@theme {
  --color-background: oklch(0.985 0.002 260);
  --color-foreground: oklch(0.15 0.03 260);
  --color-card: oklch(1 0 0);
  --color-primary: oklch(0.55 0.24 264);
  --color-primary-hover: oklch(0.48 0.24 264);
  --color-secondary: oklch(0.97 0.005 260);
  --color-muted: oklch(0.55 0.03 260);
  --color-accent: oklch(0.65 0.20 264);
  --color-destructive: oklch(0.58 0.24 27);
  --color-border: oklch(0.93 0.005 260);
  --color-success: oklch(0.70 0.17 165);
  --color-warning: oklch(0.75 0.18 80);
  --color-platinum: oklch(0.85 0.05 270);
  --color-gold: oklch(0.80 0.18 85);
  --color-silver: oklch(0.75 0.03 260);
  --color-bronze: oklch(0.65 0.12 55);
  --font-sans: var(--font-inter);
  --font-mono: var(--font-mono);
  --radius-default: 12px;
  --radius-card: 16px;
  --radius-pill: 999px;
}

@layer base {
  body {
    @apply bg-background text-foreground;
  }
}

.dark {
  --color-background: oklch(0.13 0.03 260);
  --color-foreground: oklch(0.93 0.01 260);
  --color-card: oklch(0.18 0.02 260);
  --color-border: oklch(0.25 0.02 260);
  --color-secondary: oklch(0.20 0.02 260);
}
```

---

## MODULE 2: Authentication Flow

### Pages
1. **Login** (`/[locale]/login`) — magic link input + Google OAuth button
2. **Auth Callback** (`/[locale]/callback`) — handles magic link & OAuth redirect

### Supabase Auth Config
- Magic link (email OTP, 24h expiry, 6-digit code)
- Google OAuth (redirect flow)
- JWT in cookies via `@supabase/ssr`

### Frontend Auth Pattern
```tsx
// lib/supabase/client.ts
import { createBrowserClient } from "@supabase/ssr";
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

// lib/supabase/server.ts
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll(), setAll: (c) => c.forEach(({ name, value, options }) => cookieStore.set(name, value, options)) } }
  );
}
```

### Backend Auth Pattern
```python
# app/deps.py
from typing import Annotated
from supabase import acreate_client, AsyncClient
from fastapi import Depends, HTTPException, Request
from app.config import settings

async def get_supabase_user(request: Request) -> AsyncClient:
    """Per-request client with user JWT for RLS enforcement."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, detail={"code": "UNAUTHORIZED", "message": "Missing token"})
    client = await acreate_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options={"headers": {"Authorization": f"Bearer {token}"}}
    )
    return client

async def get_supabase_admin() -> AsyncClient:
    """Admin client — bypasses RLS. Use only in services, never in user-facing routes."""
    return await acreate_client(settings.supabase_url, settings.supabase_service_role_key)

async def get_current_user_id(request: Request) -> str:
    """Verify JWT and extract user ID."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, detail={"code": "UNAUTHORIZED", "message": "Missing token"})
    admin = await acreate_client(settings.supabase_url, settings.supabase_service_role_key)
    resp = await admin.auth.get_user(token)
    if not resp or not resp.user:
        raise HTTPException(401, detail={"code": "UNAUTHORIZED", "message": "Invalid token"})
    return str(resp.user.id)

SupabaseUser = Annotated[AsyncClient, Depends(get_supabase_user)]
SupabaseAdmin = Annotated[AsyncClient, Depends(get_supabase_admin)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
```

### Login Page UI
- Clean centered card
- Email input with "Send Magic Link" primary button
- Divider "or"
- "Continue with Google" secondary button
- Language switcher in top-right
- Animated floating orbs background (Framer Motion, gentle spring)
- i18n: all text from `auth.json` namespace

### UX Copy
```json
// locales/az/auth.json
{
  "login": {
    "title": "Volaura-ya daxil olun",
    "subtitle": "Könüllülük bacarıqlarınızı kəşf edin",
    "email_placeholder": "E-poçt ünvanınız",
    "magic_link_button": "Giriş linki göndər",
    "or_divider": "və ya",
    "google_button": "Google ilə davam et",
    "magic_link_sent": "Giriş linki göndərildi! E-poçtunuzu yoxlayın.",
    "magic_link_error": "Link göndərilə bilmədi. Yenidən cəhd edin."
  }
}
// locales/en/auth.json
{
  "login": {
    "title": "Sign in to Volaura",
    "subtitle": "Discover your volunteer potential",
    "email_placeholder": "Your email address",
    "magic_link_button": "Send magic link",
    "or_divider": "or",
    "google_button": "Continue with Google",
    "magic_link_sent": "Magic link sent! Check your email.",
    "magic_link_error": "Couldn't send the link. Please try again."
  }
}
```

---

## MODULE 3: Assessment Engine

### Flow
1. User opens Assessment Hub → sees 8 competency cards with status (not started / in progress / completed)
2. Taps competency → starts assessment for that competency
3. Questions appear one at a time (3 types: BARS, MCQ, Open Text)
4. Progress bar shows position
5. After all questions → competency score calculated
6. After ALL 8 competencies → full AURA score calculated
7. Results screen with confetti + radar chart + badge reveal

### Question Types

**BARS (Behaviorally Anchored Rating Scale):**
- 7-point horizontal scale
- Each point has a behavioral anchor text
- User taps a point on the scale
- Score: `((selected - 1) / 6) × 100`

**MCQ (Multiple Choice Question):**
- 4 options, single select
- Each option has a hidden `score_weight` (0.0 to 1.0)
- Score: `score_weight × 100`

**Open Text:**
- Text area with word limit
- Submitted to Gemini 2.5 Flash for LLM evaluation
- Returns score (0-100) + structured feedback
- Evaluation prompt uses rubric from `questions.rubric_az/en`

### Questions Per Competency
```
- Base: 3 questions per competency (1 BARS + 1 MCQ + 1 Open Text)
- If score variance > 20 between questions: add 1-2 more at adjusted difficulty
- Maximum: 5 per competency
- Total assessment: 24-40 questions across all 8 competencies
- Estimated time: 15-25 minutes
- Users CAN resume abandoned assessments (status='in_progress' saved per competency)
- Only ONE assessment per competency can be in_progress at a time
```

### Pseudo-Adaptive Question Selection
```python
# Per competency:
# Start at difficulty 1 (easy)
# If score > 70 on current question → next difficulty +1
# If score < 40 → next difficulty -1
# Stay within 1-3 range
# Select random unused question at current difficulty for this competency
```

### LLM Evaluation (Open Text) — ASYNC Pattern
```python
# Open text answers are evaluated ASYNCHRONOUSLY:
# 1. User submits answer → store with llm_score=NULL, status='pending_evaluation'
# 2. Return 202: { "evaluation_status": "pending", "next_question": {...} }
# 3. Background task (FastAPI BackgroundTasks) sends to Gemini
# 4. Frontend polls GET /assessments/{id}/responses/{resp_id}/status
#    OR subscribes to Supabase Realtime on assessment_responses table
# 5. When evaluation complete → score stored, frontend updates

# Input sanitization (prevent prompt injection):
def sanitize_user_input(text: str, max_chars: int = 1400) -> str:
    forbidden = ["SYSTEM:", "ASSISTANT:", "ignore previous", "forget instructions"]
    cleaned = text
    for pattern in forbidden:
        cleaned = cleaned.replace(pattern, "[FILTERED]")
    return cleaned[:max_chars]

# Structured prompt (NEVER string concatenation with user input):
evaluation_prompt = {
    "system": "You evaluate volunteer assessment answers. Score 0-100 based ONLY on the rubric below. Output JSON: {score: int, feedback: string}",
    "rubric": rubric_from_db,  # NEVER from user input
    "answer": sanitize_user_input(user_answer),
}

# Fallback if Gemini fails:
# 1. Apply heuristic: score = min(80, max(20, word_count / max_words * 60))
# 2. Flag response with status='fallback_scored'
# 3. Queue for retry via pg_cron (max 3 retries, 15min interval)
# 4. Log error to Sentry
```

### AURA Score Calculation
```python
WEIGHTS = {
    "communication": 0.20, "reliability": 0.15, "english_proficiency": 0.15,
    "leadership": 0.15, "event_performance": 0.10, "tech_literacy": 0.10,
    "adaptability": 0.10, "empathy_safeguarding": 0.05,
}

VERIFICATION_MULTIPLIERS = {"self_assessed": 1.00, "org_attested": 1.15, "peer_verified": 1.25}

BADGE_TIERS = [(90, "platinum"), (75, "gold"), (60, "silver"), (40, "bronze")]
# < 40 = "none"

# Per competency:
#   raw = weighted_avg(question_scores, weights: hard=1.5x, medium=1.0x, easy=0.7x)
#   adjusted = raw × type_modifier (BARS=1.0, MCQ=0.9, Open Text=1.1)
#   final = clamp(adjusted, 0, 100)
#
# Total AURA:
#   sum(competency_score × weight × verification_multiplier) × reliability_factor
#   reliability_factor = 1.0 - (0.15 × normalized_std_dev), clamped [0.85, 1.0]
#   final = clamp(total, 0, 100)
```

### Assessment UI Components

**QuestionCard:** Card wrapper with question text, type indicator, timer (optional)
**BARSScale:** 7 tappable circles in a row, each with anchor text below. Selected = filled primary color. Animation: scale bounce on tap.
**MCQOptions:** 4 option cards in vertical stack. Selected = primary border + checkmark. Animation: gentle spring on select.
**OpenTextInput:** Textarea with word counter. Character limit visual. "AI will evaluate" badge.
**AssessmentProgress:** Top bar showing `{current}/{total}` with progress bar. Competency name + icon.

### Assessment Results Screen
- Confetti animation (canvas-confetti or custom Framer Motion)
- AURA score counter animating from 0 to final score (JetBrains Mono, 72px)
- Badge reveal with spring animation
- Radar chart (8 axes, filled polygon)
- Competency breakdown list
- "Share Your Score" CTA with share buttons (LinkedIn, Instagram Story, Copy Link)
- "View Full Profile" secondary CTA

---

## MODULE 4: Dashboard & AURA Score

### Dashboard Page
- Greeting: "Salam, {name}!" / "Hello, {name}!"
- AURA Score card (large): score number + badge + trend arrow
- Radar chart (compact version, 8 axes)
- Quick actions: "Take Assessment", "Find Events", "Share Profile"
- Upcoming events (horizontal scroll cards)
- Recent notifications (3 most recent)
- Leaderboard snippet (your rank + 2 above + 2 below)

### AURA Score Page (dedicated)
- Large animated score counter (JetBrains Mono)
- Badge with tier name and color
- Full radar chart (interactive — tap axis for detail)
- Competency breakdown: 8 rows, each with name + score bar + verification icon
- Verification levels per competency (shield icons: gray/blue/gold)
- Score history timeline (line chart, Recharts)
- "Improve Your Score" section → links to reassessment
- Share section: 3 format previews (LinkedIn, Story, Square) + Copy Link + QR

### Badge Tier Display
```tsx
// badge-chip.tsx
const tierConfig = {
  platinum: { color: "bg-platinum", icon: "Crown", label: { az: "Platinum", en: "Platinum" } },
  gold:     { color: "bg-gold", icon: "Award", label: { az: "Qızıl", en: "Gold" } },
  silver:   { color: "bg-silver", icon: "Medal", label: { az: "Gümüş", en: "Silver" } },
  bronze:   { color: "bg-bronze", icon: "Shield", label: { az: "Bürünc", en: "Bronze" } },
  none:     { color: "bg-muted", icon: "Circle", label: { az: "Başlanğıc", en: "Starter" } },
};
```

---

## MODULE 5: Profile & Public Sharing

### Profile Page (authenticated) — THIS IS A LIVING PORTFOLIO, NOT A STATIC PAGE
- Avatar (uploadable, 128px circle)
- Name, username, city, bio
- AURA badge (prominent) with animated counter
- Competency radar chart (interactive — tap axis for detail)
- Skills/expertise tags
- Languages spoken
- Verification status indicators (3 levels: self/org/peer)
- **Impact metrics**: "120 volunteer hours · 8 events · 3 organizations"
- **Event timeline**: Visual timeline of every event with org logos, dates, volunteer count
  - Each event card shows: org logo + event name + date + "Verified ✓" if org-attested
  - Live counter: "42 volunteers confirmed" — taps to expand avatars/badges
- **AURA growth graph**: Line chart showing score trajectory over time
- **Organization endorsements**: Logos of orgs that attested this volunteer + competencies verified
- "Edit Profile" button
- "Share Profile" button

### Public Profile (`/u/[username]`)
- Server-rendered (SSR for SEO)
- OG image auto-generated: name + AURA score + badge + radar chart
- Same layout as profile but read-only
- "Join Volaura" CTA for non-users
- QR code for printing on physical badges

### Share Formats
- LinkedIn: 1200×627px card
- Instagram Story: 1080×1920px
- Square: 1080×1080px
All generated via `@vercel/og` (Satori) at edge

### OG Image Route
```tsx
// app/api/og/[username]/route.tsx
import { ImageResponse } from "@vercel/og";
// Generate dynamic image with user's AURA score, badge, radar chart preview
```

---

## MODULE 6: Events & Organizations

### Events are DYNAMIC DATA — not hardcoded content
Any organization can create events. Past events (COP29, CIS Games) show as history with live counters. Upcoming events show as opportunities. The platform gets richer with every event.

### Events List Page
- Filter bar: date, location, min AURA requirement, competency, status (upcoming/past)
- Event cards: **org logo** + title + date + location + **live volunteer counter** + min AURA badge
- Sort: date (default), popularity, volunteer count
- "My Events" tab (registered + attended)
- **Past events section**: Shows completed events with confirmed volunteer counts
  - Each card: org logo + "42 volunteers · avg AURA 71" + expandable volunteer list

### Event Detail Page
- Hero: title, **org logo (uploaded by org)**, date, location map
- Description (bilingual AZ/EN)
- Requirements: min AURA score, required competencies (with badge icons)
- **Live capacity bar**: "32/50 registered" — animated, updates in real-time via Supabase Realtime
- "Register" primary CTA (disabled if AURA too low, with clear explanation)
- **Registered volunteers**: Scrollable avatars + badge chips + AURA scores
  - Tap avatar → mini profile popup (name, badge, top competency)
- **For past events**: "I participated" self-attestation button
  - Volunteer claims participation → pending org confirmation
  - Org confirms → volunteer count increases, attestation applied

### Event Card Component (reusable — appears on profiles, dashboard, events page)
```tsx
// Event card shows:
// - Org logo (from org profile, NOT hardcoded)
// - Event title (from DB)
// - Date range
// - Location
// - Live volunteer counter: "👥 42 confirmed" — updates via Realtime
// - Average AURA of participants
// - Required competencies as small icons
// - Status badge: "Upcoming" | "In Progress" | "Completed"
// When tapped/clicked: shows expandable list of volunteer avatars + badges
```

### Organization Portal (separate layout)
- Org dashboard: events overview, volunteer pool stats, **attestation queue**
- Create/edit events (with logo upload, description in AZ/EN, competency requirements)
- **Volunteer search**: filter by AURA score, competency, location, availability
- **Semantic search**: describe ideal volunteer in natural language → pgvector matching
  - Shows matching score: "87% match" for each volunteer
- **Post-event attestation workflow**:
  1. Event ends → org sees list of registered volunteers
  2. For each: rate (1-5 stars) + checkbox per competency verified + optional comment
  3. Submit → volunteer's AURA recalculated with 1.15x multiplier for attested competencies
  4. Volunteer gets notification: "Organization X verified your Leadership and Communication!"
- **Request volunteers**: AI-matched invitations to top candidates
- **Self-attestation review**: Queue of volunteers claiming "I participated" — org confirms/denies

### DB: Add to events table
```sql
-- Events already have: org logo from organizations.logo_url
-- Add: confirmed_volunteer_count as materialized view or trigger
CREATE OR REPLACE FUNCTION update_event_volunteer_count()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE events SET registered_count = (
    SELECT COUNT(*) FROM event_registrations
    WHERE event_id = NEW.event_id AND status IN ('registered', 'attended')
  ) WHERE id = NEW.event_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_event_count
AFTER INSERT OR UPDATE OR DELETE ON event_registrations
FOR EACH ROW EXECUTE FUNCTION update_event_volunteer_count();
```

---

## MODULE 7: Backend API

### All Endpoints (FastAPI)

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI(title="Volaura API", version="1.0.0")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# CORS — restricted to frontend origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],  # e.g. "https://volaura.com"
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles_router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(assessments_router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(scores_router, prefix="/api/v1/scores", tags=["scores"])
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(org_router, prefix="/api/v1/org", tags=["organizations"])
app.include_router(verifications_router, prefix="/api/v1/verifications", tags=["verifications"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(share_router, prefix="/api/v1/share", tags=["share"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
```

### Key Endpoint Specs

**POST /api/v1/assessments/start** — Start assessment for a competency
```python
Request: { "competency": "communication" }
Response: { "data": { "assessment_id": "uuid", "first_question": {...} } }
```

**POST /api/v1/assessments/{id}/answers** — Submit answer, get next question
```python
Request: { "question_id": "uuid", "response": { "selected": 5 }, "time_spent_seconds": 45 }
# For BARS/MCQ (instant scoring):
Response: { "data": { "score": 71.4, "next_question": {...} | null, "is_complete": false } }
# For open_text (async LLM evaluation):
Response (202): { "data": { "evaluation_status": "pending", "response_id": "uuid", "next_question": {...} } }
# Frontend polls: GET /api/v1/assessments/{id}/responses/{response_id}/status
# Returns: { "data": { "status": "completed", "score": 78.5, "feedback": "..." } }
```

**POST /api/v1/assessments/{id}/complete** — Finalize assessment, trigger AURA recalc
```python
Response: { "data": { "competency_score": 78, "aura_score": 72, "badge_tier": "silver", "badge_changed": true } }
```

**GET /api/v1/scores/me** — Get current AURA score
```python
Response: {
  "data": {
    "composite_score": 72,
    "tier": "silver",
    "percentile": 68.5,
    "reliability_factor": 0.95,
    "competencies": [
      { "competency": "communication", "score": 85, "weight": 0.20, "verification_level": "self_assessed" },
      ...
    ],
    "events_attended": 3,
    "last_assessed": "2026-03-20T..."
  }
}
```

**GET /api/v1/scores/leaderboard** — Leaderboard
```python
Query: ?limit=50&offset=0&competency=communication (optional)
Response: { "data": [{ "rank": 1, "username": "...", "avatar_url": "...", "score": 95, "tier": "platinum" }], "meta": { "total": 200 } }
```

**POST /api/v1/org/volunteers/search** — Semantic search
```python
Request: { "query": "Reliable English-speaking event coordinator", "min_aura": 60, "limit": 20 }
# Backend: generates embedding via Gemini → calls match_volunteers RPC
Response: { "data": [{ "user_id": "...", "username": "...", "score": 78, "similarity": 0.89, "competencies": [...] }] }
```

### Response Envelope (ALL endpoints)
```python
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-22T...",
    "request_id": "uuid",
    "version": "1.0.0",
    "pagination": { "page": 1, "per_page": 50, "total": 200 }  # optional
  }
}
```

### Error Format (ALL errors)
```python
{
  "detail": {
    "code": "ASSESSMENT_NOT_FOUND",
    "message": "Assessment not found or does not belong to user"
  }
}
```

---

## I18N — CRITICAL RULES

1. **ZERO hardcoded strings.** Every user-facing string uses `t()` from react-i18next.
2. **Azerbaijani is primary.** Write AZ first, then EN.
3. **Azerbaijani characters:** ə, ğ, ı, ö, ü, ş, ç — test that they render correctly.
4. **Text expansion:** AZ text is ~20-30% longer than EN. Design for the longer string.
5. **Date format:** AZ = DD.MM.YYYY, EN = MMM DD, YYYY
6. **Number format:** AZ = 1.234,56 — EN = 1,234.56
7. **Currency:** AZN (₼)

### Namespace Structure
```
locales/{az,en}/common.json    — nav, buttons, generic
locales/{az,en}/auth.json      — login, signup, verification
locales/{az,en}/assessment.json — questions UI, progress, instructions
locales/{az,en}/results.json   — score reveal, badges, sharing
locales/{az,en}/profile.json   — profile page, edit, public
locales/{az,en}/events.json    — event listing, detail, registration
locales/{az,en}/errors.json    — all error messages
```

---

## CRITICAL CONSTRAINTS — READ CAREFULLY

1. **NEVER use Pages Router** — App Router only, all routes under `app/[locale]/`
2. **NEVER use Redux** — Zustand for client state, TanStack Query for server state
3. **NEVER use SQLAlchemy or any ORM** — Supabase SDK only
4. **NEVER use global Supabase client** — per-request via Depends()
5. **NEVER use Pydantic v1 syntax** — no `class Config`, no `@validator`, no `orm_mode`
6. **NEVER use `google-generativeai`** — use `google-genai` SDK
7. **NEVER use print()** in Python — use `loguru.logger`
8. **NEVER hardcode strings** — use `t()` function from react-i18next
9. **NEVER use tailwind.config.js** — Tailwind CSS 4 uses `@theme {}` in globals.css
10. **NEVER use vector(1536)** — Gemini embeddings are 768-dimensional
11. **ALL tables MUST have RLS enabled** with appropriate policies
12. **ALL API responses** use the standard envelope: `{ data, meta }`
13. **ALL errors** return structured format: `{ detail: { code, message } }`
14. **UTF-8 everywhere** — explicit `encoding='utf-8'` in Python file operations
15. **Type hints on ALL Python functions** — no untyped code
16. **Strict TypeScript** — no `any` type allowed
17. **Rate limiting on ALL endpoints** — use `slowapi`:
    - Auth: 5/minute per IP
    - Assessment start: 5/hour per user
    - Assessment answers: 60/hour per user
    - LLM evaluation: 30/hour per user
    - Semantic search: 30/minute per org
    - Leaderboard: 60/minute (cacheable)
18. **LLM input sanitization** — NEVER send raw user text to Gemini. Use structured prompts with sanitized input.
19. **Async LLM evaluation** — Open text scoring is async (BackgroundTasks), returns 202, frontend polls for result.
20. **LLM fallback** — If Gemini fails: heuristic score, flag for retry, log to Sentry.

---

## ERROR CODES (use in ALL HTTPException.detail)

```python
# Every error response: { "detail": { "code": "<CODE>", "message": "<human-readable>" } }
ERROR_CODES = {
    "UNAUTHORIZED": (401, "Authentication required"),
    "FORBIDDEN": (403, "Access denied"),
    "PROFILE_NOT_FOUND": (404, "Profile not found"),
    "ASSESSMENT_NOT_FOUND": (404, "Assessment not found"),
    "EVENT_NOT_FOUND": (404, "Event not found"),
    "EVENT_FULL": (409, "Event is at full capacity"),
    "ALREADY_REGISTERED": (409, "Already registered for this event"),
    "INSUFFICIENT_AURA": (403, "AURA score too low for this event"),
    "ASSESSMENT_ALREADY_COMPLETE": (409, "This competency assessment is already completed"),
    "COMPETENCY_IN_PROGRESS": (409, "Assessment for this competency is already in progress"),
    "INVALID_ANSWER_FORMAT": (422, "Invalid answer format for this question type"),
    "RATE_LIMIT_EXCEEDED": (429, "Too many requests, try again later"),
    "LLM_EVALUATION_FAILED": (503, "AI evaluation temporarily unavailable"),
    "EVALUATION_PENDING": (202, "Answer saved, AI evaluation in progress"),
    "UPGRADE_REQUIRED": (402, "This feature requires a paid plan"),
}
```

### Error i18n Keys (errors.json)
```json
{
  "UNAUTHORIZED": { "az": "Autentifikasiya tələb olunur", "en": "Authentication required" },
  "FORBIDDEN": { "az": "Giriş qadağandır", "en": "Access denied" },
  "PROFILE_NOT_FOUND": { "az": "Profil tapılmadı", "en": "Profile not found" },
  "ASSESSMENT_NOT_FOUND": { "az": "Qiymətləndirmə tapılmadı", "en": "Assessment not found" },
  "EVENT_NOT_FOUND": { "az": "Tədbir tapılmadı", "en": "Event not found" },
  "EVENT_FULL": { "az": "Tədbir dolub", "en": "Event is at full capacity" },
  "ALREADY_REGISTERED": { "az": "Artıq qeydiyyatdan keçmisiniz", "en": "Already registered" },
  "INSUFFICIENT_AURA": { "az": "AURA balınız bu tədbir üçün kifayət deyil", "en": "AURA score too low" },
  "ASSESSMENT_ALREADY_COMPLETE": { "az": "Bu bacarıq artıq qiymətləndirilib", "en": "Already completed" },
  "RATE_LIMIT_EXCEEDED": { "az": "Çox sorğu. Bir az gözləyin", "en": "Too many requests" },
  "LLM_EVALUATION_FAILED": { "az": "AI qiymətləndirmə müvəqqəti əlçatmazdır", "en": "AI evaluation unavailable" },
  "NETWORK_ERROR": { "az": "Şəbəkə xətası. Yenidən cəhd edin", "en": "Network error. Please retry" },
  "GENERIC_ERROR": { "az": "Xəta baş verdi", "en": "Something went wrong" }
}
```

---

## MODULE 8: Growth & Analytics

### 8.1 Referral System
```python
# POST /api/v1/referrals/invite — Send referral invite
Request: { "email": "friend@example.com" }
Response: { "data": { "referral_id": "uuid", "invite_link": "https://volaura.com/join?ref=CODE" } }
# Rate limit: 20 invites/day per user
# Abuse prevention: one invite per email, verified email required

# GET /api/v1/referrals/me — Get user's referral stats
Response: { "data": { "referral_code": "ABC123", "total_invited": 5, "total_converted": 2, "bonus_earned": 20 } }

# Reward mechanics:
# - Referrer: +5 bonus to lowest competency score (max 5 referrals = +25 max)
# - Referee: +3 bonus on first assessment completion
# - Rewards applied AFTER base AURA calculation, before clamping to 100
```

### 8.2 Email Lifecycle (Resend Integration)
```python
# Trigger → Template → Timing:
# 1. user_signup → welcome_email → immediate (1 min after signup)
#    Content: "Salam! AURA balınızı kəşf edin" / "Welcome! Discover your AURA score"
#    CTA: "Start Assessment"
#
# 2. assessment_completed → results_email → 5 min after completion
#    Content: Score + badge + share link + "Invite friends"
#    CTA: "Share Your Badge"
#
# 3. no_login_7_days → nudge_email → Day 7
#    Content: "X volunteers joined since you left" + social proof
#    CTA: "Continue Assessment"
#
# 4. no_login_30_days → winback_email → Day 30
#    Content: New features + "Your AURA score is waiting"
#    CTA: "Come Back"
#
# 5. referral_converted → thank_you_email → immediate
#    Content: "Your friend {name} joined! +5 bonus applied"
#
# ALL emails: bilingual (AZ primary with EN fallback), Resend API, mobile-responsive
```

### 8.3 Analytics Events
```typescript
// Core events to track (use GA4 or Mixpanel):
type AnalyticsEvent =
  | { name: "user_signup"; props: { source: "organic" | "referral" | "wuf13" | "google"; locale: string } }
  | { name: "assessment_started"; props: { competency: string } }
  | { name: "assessment_completed"; props: { competency: string; score: number; time_seconds: number } }
  | { name: "aura_calculated"; props: { score: number; tier: string } }
  | { name: "score_shared"; props: { platform: "linkedin" | "instagram" | "copy" | "qr" } }
  | { name: "profile_viewed"; props: { is_own: boolean; from_referral: boolean } }
  | { name: "event_registered"; props: { event_id: string; org_id: string } }
  | { name: "referral_sent"; props: { method: "email" | "link" } }
  | { name: "referral_converted"; props: { referrer_id: string } };

// UTM on all share links:
// https://volaura.com/u/{username}?utm_source=linkedin&utm_medium=social&utm_campaign=aura_badge
// https://volaura.com/join?ref={code}&utm_source=referral&utm_medium=email&utm_campaign=invite_v1
```

### 8.4 OG Tags (Share Preview)
```tsx
// Dynamic per-user OG tags on /u/[username]:
<meta property="og:title" content="{name} — {tier} Volunteer (AURA {score})" />
<meta property="og:description" content="Verified volunteer on Volaura. {top_competency} specialist." />
<meta property="og:image" content="https://volaura.com/api/og/{username}" />
<meta property="og:url" content="https://volaura.com/u/{username}" />
<meta name="twitter:card" content="summary_large_image" />

// JSON-LD structured data:
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "{full_name}",
  "description": "{bio}",
  "image": "{avatar_url}",
  "url": "https://volaura.com/u/{username}"
}
```

---

## MODULE 9: Gamification, AI Coaching & Liveness

### 9.1 Duolingo-Inspired Engagement System

**Streaks (Monthly Volunteer Streak):**
- Count consecutive months with at least 1 event attended
- Display: "🔥 3-month streak" on profile and dashboard
- Notification at day 25: "Your streak is active! Attend an event to keep it going"
- If missed: "Your 5-month streak ended. Start a new one!"
- DB: Add `current_streak INT DEFAULT 0, longest_streak INT DEFAULT 0` to profiles

**Leagues (Monthly, City-Scoped):**
- Groups of ~30 users in same city, ranked by monthly AURA activity
- Top 5 promote to next league, bottom 5 demote
- League tiers: Rookie → Contender → Challenger → Elite → Champion
- League resets monthly
- DB: `volunteer_leagues` table (user_id, league_tier, city, month, rank, xp_earned)

**Competency Specialization:**
- If any single competency score ≥ 85: earns "Specialist" badge for that competency
- "Leadership Specialist 🎯" shown on profile
- Visible in search: orgs can filter by specialists

### 9.2 AURA Coach — Personalized AI Assistant

**Powered by Gemini 2.5 Flash. Appears as a chat bubble in bottom-right.**

**Capabilities:**
```typescript
type AuraCoachMessage =
  | { type: "skill_gap"; text: "Your Communication is 62. To reach Gold, improve it to 70+. Try the advanced assessment." }
  | { type: "event_match"; text: "3 events this week match your profile at 80%+. Register now!" }
  | { type: "growth_path"; text: "You're 8 points from Gold. Focus on English (+5) and Reliability (+3)." }
  | { type: "nudge"; text: "You haven't volunteered in 30 days. 12 new events posted near you." }
  | { type: "celebration"; text: "Organization X rated you 5/5! Want to request a Leadership attestation?" }
  | { type: "weekly_digest"; text: "This week: +3 AURA, 2 profile views from organizations, 1 new event match." }
```

**API Endpoint:**
```python
# POST /api/v1/coach/message — Get AI coaching insight
Request: { "context": "dashboard" }  # or "profile", "assessment_result", "event_browse"
Response: {
  "data": {
    "messages": [
      { "type": "growth_path", "text_az": "...", "text_en": "...", "action_url": "/assessment" },
      { "type": "event_match", "text_az": "...", "text_en": "...", "action_url": "/events/uuid" }
    ]
  }
}
# Rate limit: 10/hour per user. Cache for 1 hour.
# Backend: Generates via Gemini using volunteer profile + event data + score history as context
```

**UI Component: `aura-coach.tsx`**
- Floating action button (bottom-right, above BottomNav on mobile)
- Tap → expandable card with 1-3 contextual tips
- Each tip has: icon + text + action button
- Dismiss individual tips or collapse all
- Pulse animation when new insight available

### 9.3 Live Social Proof (Platform Feels Alive)

**Global Stats Widget (Landing page + Dashboard):**
```tsx
// live-stats.tsx — updates via Supabase Realtime or polling every 60s
<div className="flex gap-6">
  <StatCounter value={847} label={t("stats.verified_volunteers")} />
  <StatCounter value={23} label={t("stats.new_today")} prefix="+" />
  <StatCounter value={15} label={t("stats.organizations")} />
  <StatCounter value={42} label={t("stats.events_completed")} />
</div>
// Counter animates when value changes (Framer Motion spring)
```

**Activity Feed (Dashboard sidebar):**
```tsx
// activity-feed.tsx — real-time via Supabase Realtime subscription
<ActivityFeed>
  <ActivityItem icon="🏆" text="Leyla M. just earned Platinum!" time="2 min ago" />
  <ActivityItem icon="✅" text="COP29 — 1 new volunteer confirmed" time="5 min ago" />
  <ActivityItem icon="📊" text="+3 volunteers assessed today in Baku" time="12 min ago" />
  <ActivityItem icon="🎯" text="Rashad K. became a Leadership Specialist" time="1h ago" />
</ActivityFeed>
```

**DB: Activity log table for real-time feed:**
```sql
CREATE TABLE public.activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL CHECK (type IN ('badge_earned', 'assessment_completed', 'event_confirmed', 'attestation_received', 'specialist_earned', 'streak_milestone')),
  actor_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  metadata JSONB DEFAULT '{}',  -- { "badge": "platinum", "event_name": "COP29", "score": 92 }
  is_public BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_activity_log_recent ON activity_log(created_at DESC) WHERE is_public = true;

ALTER TABLE public.activity_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public activities viewable" ON activity_log FOR SELECT USING (is_public = true);
```

### 9.4 Impact Metrics (on Profile)
```sql
-- Materialized view or computed on read:
-- total_volunteer_hours: SUM of event durations where status='attended'
-- events_attended: COUNT of event_registrations where status='attended'
-- organizations_worked_with: COUNT DISTINCT org_id from attended events
-- total_attestations: COUNT of org attestations received
-- people_helped: optional manual input or org-provided metric
```

```tsx
// impact-metrics.tsx
<div className="grid grid-cols-3 gap-4 text-center">
  <ImpactStat value={120} label={t("profile.hours")} icon="Clock" />
  <ImpactStat value={8} label={t("profile.events")} icon="Calendar" />
  <ImpactStat value={3} label={t("profile.organizations")} icon="Building" />
</div>
```
