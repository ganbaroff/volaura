# ADR-003: Authentication & Verification System

**Status:** Accepted
**Date:** 2026-03-22
**Deciders:** Yusif (product owner), Claude (architecture)
**Related:** [[ADR-001-system-architecture]], [[ADR-002-database-schema]], [[ADR-005-aura-scoring]]
**Governed by:** [[../ECOSYSTEM-CONSTITUTION]]

---

## Context

Volaura is a verified professional talent platform where AURA scores must be trustworthy. Users need seamless passwordless authentication, and talent profiles need transparent credentialing at three levels: self-assessed (default), organization-attested (org vouches), and peer-verified (3+ Gold+ peers confirm). This ADR defines how authentication flows work, how JWT verification protects the API, how the 3-level verification system builds trust, and how role-based access controls (RLS + API roles) prevent unauthorized data access.

### Requirements

**Authentication:**
- Fast, passwordless onboarding (magic link primary, Google OAuth secondary)
- Works on unstable WiFi (major event venue with 5000 concurrent users)
- Mobile-first (PWA installable, works offline for assessments)
- No password resets, no forgot-password flows

**Verification (Trust Layers):**
- Level 1: Self-assessed (user completes assessment, gets AURA score, badge marked "Self-Assessed")
- Level 2: Org-attested (organization admin confirms competencies, raises trust multiplier to 1.15x)
- Level 3: Peer-verified (3+ Gold+ peers micro-assess competencies, multiplier 1.25x, creates network effect)

**Authorization:**
- Users: read own profile, take assessments, view events, see public profiles
- Org admins: manage organization, attest talent, search verified profile pool, create events
- Platform admins: full access, verify organizations, audit trails

**Security:**
- No plaintext credentials stored
- JWT signature verification for all API calls
- RLS policies protect all data in PostgreSQL
- Rate limiting on auth endpoints
- CSRF protection via SameSite cookies
- XSS prevention via CSP headers and HttpOnly cookies

---

## Decision

### 1. Authentication Strategy: Passwordless via Supabase Auth

#### 1.1 Primary Flow: Magic Link (Email)

**Why magic link first:**
- Zero password fatigue (common in Azerbaijan where password managers are less common)
- Works on any device (no app install required)
- Stateless for server (Supabase handles token generation, expiry, verification)
- Accessible (no CAPTCHA, easy for low-tech users)

**Flow:**

```
User                    Browser                  Supabase Auth
 │                         │                           │
 │  Submit email            │                           │
 │─────────────────────────>│                           │
 │                         │  POST /auth/v1/otp       │
 │                         │──────────────────────────>│
 │                         │  Generate OTP + email     │
 │                         │<──────────────────────────│
 │                         │  Send email w/ magic link │
 │                   (User clicks link in email)      │
 │                         │  Link: app.volaura.az/auth/confirm?token=xxxx
 │                         │                           │
 │                    POST /auth/callback             │
 │──────────────────────────────────────────────────>│
 │                         │  Verify token, create JWT│
 │<────────────────────────────────────────────────────│
 │  Set session cookie      │                           │
 │  Redirect to /dashboard  │                           │
```

**Implementation (Supabase config):**
```javascript
// apps/web/auth.config.ts
export const supabaseAuthConfig = {
  providers: {
    email: {
      enabled: true,
      otp_exp: 86400, // 24 hours
      otp_length: 6,
    },
  },
}
```

#### 1.2 Secondary Flow: Google OAuth (Fast-Track)

For users familiar with Google (tech-savvy, international):

```
User                    Browser                  Supabase Auth        Google
 │                         │                           │                 │
 │  Click "Sign in w/ Google"                         │                 │
 │─────────────────────────>│                          │                 │
 │                         │  Redirect to Google       │                 │
 │                         │──────────────────────────────────────────>│
 │                         │                          │                 │
 │                   (User grants permission)         │                 │
 │                         │<─────────────────────────────────────────│
 │                         │  OAuth callback (code)                    │
 │  Supabase exchanges code for token+user info       │
 │  Auto-creates profile if first time               │
 │                         │  Set session cookie      │
 │<────────────────────────────────────────────────────│
 │  Redirect to /dashboard  │                          │
```

**OAuth scopes** (minimal):
```javascript
// email, profile only — NO calendar, drive, etc.
scope: ["openid", "profile", "email"]
```

#### 1.3 Future Providers (Post-Launch)

- **Apple Sign-In** (for iPad users at events)
- **Telegram Login Widget** (pre-registered volunteers can auth via Telegram)

---

### 2. JWT Flow: Browser → Supabase Auth → FastAPI

All API calls pass Supabase JWT, verified by FastAPI before processing.

#### 2.1 Token Lifecycle

```
Supabase Auth                       Browser                      FastAPI API
     │                                  │                              │
     │  POST /auth/callback            │                              │
     │<─────────────────────────────────│                              │
     │  Generate JWT:                   │                              │
     │  • access_token (15 min)         │                              │
     │  • refresh_token (30 days)       │                              │
     │  Set HttpOnly cookie with token  │                              │
     │────────────────────────────────>│                              │
     │                                  │                              │
     │                                  │  GET /api/profile           │
     │                                  │  Header: Authorization: Bearer <access_token>
     │                                  │────────────────────────────>│
     │                                  │                     Verify JWT signature
     │                                  │                     Extract sub (user_id)
     │                                  │<────────────────────────────│
     │                                  │  200 OK {profile_data}      │
     │                                  │<────────────────────────────│
```

#### 2.2 Token Refresh (Automatic, No User Interaction)

When access_token expires (15 min):

```
Browser                        Supabase Auth
     │                                │
     │ GET /api/profile              │
     │ (with expired access_token)   │
     │─────────────────────────────>│ FastAPI detects 401 (invalid_token)
     │                              │
     │ FastAPI returns 401           │
     │<─────────────────────────────│
     │                              │
     │ JavaScript catches 401        │
     │ POST /auth/v1/token          │ (with refresh_token from cookie)
     │──────────────────────────────>│
     │                              │ Generate new access_token
     │ Set cookie + return new token│
     │<──────────────────────────────│
     │ Retry GET /api/profile       │
     │ (with new access_token)       │
     │──────────────────────────────>│ Success (200)
```

Supabase SDK handles this automatically via `onAuthStateChange()`.

#### 2.3 FastAPI JWT Verification Dependency

```python
# apps/api/app/deps.py
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.config import settings

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """
    Verify Supabase JWT and return user UUID.
    Raises 401 if invalid or expired.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,  # SUPABASE_JWT_SECRET env var
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Token missing user ID"}
            )
        return user_id
    except JWTError as e:
        logger.error("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token verification failed"}
        )

class CurrentUserId(str):
    """Alias for user UUID from JWT"""
    pass

CurrentUserId = Annotated[str, Depends(get_current_user)]

# Usage in endpoints:
@router.get("/profile")
async def get_profile(user_id: CurrentUserId, db: SupabaseUser) -> ProfileOut:
    """Get current user's profile"""
    result = await db.table("profiles").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
    return ProfileOut(**result.data[0])
```

---

### 3. Three-Level Verification System

The core innovation: users can see at a glance how trustworthy a volunteer's AURA score is.

#### 3.1 Level 1: Self-Assessed (Default)

After completing the 8-competency assessment:
- User gets AURA score and competency breakdown
- All competencies tagged as `verification_level: 'self_assessed'`
- Badge badge displays: **Gold (Self-Assessed)** or **Silver (Self-Assessed)**
- Trust multiplier: 1.0x (baseline)

**User sees on profile:**
```
🏅 Self-Assessed Gold  |  AURA: 82/100
━━━━━━━━━━━━━━━━━━━━━━
📊 Communication: 85 (Self-Assessed)
📊 Leadership: 78 (Self-Assessed)
...
```

#### 3.2 Level 2: Organization-Attested

An organization (with `verified_org: true`) admin can attest specific competencies for a volunteer. This happens post-assessment, when the org wants to formally confirm the volunteer worked for them.

**Preconditions:**
- Volunteer must exist in system (has profile + AURA score)
- Organization must be registered and verified (manual process by platform admin)
- Org admin initiates attestation in org dashboard
- Volunteer can accept/reject attestation

**Flow:**

```
Org Admin                   Browser                    FastAPI              Supabase DB
    │                          │                           │                    │
    │ Search: "Ahmed"         │                           │                    │
    │  (from volunteer pool)  │                           │                    │
    │─────────────────────────>│                          │                    │
    │                         │ GET /api/volunteers/search?q=Ahmed
    │                         │──────────────────────────>│                    │
    │                         │                    Query profiles (RLS ok)
    │                         │<──────────────────────────│                    │
    │                         │ Return [Ahmed's profile]  │                    │
    │                         │<──────────────────────────│                    │
    │ Click "Attest Communication"                        │                    │
    │──────────────────────────>│                          │                    │
    │                         │ POST /api/verifications   │                    │
    │                         │   {                       │                    │
    │                         │     competency: "communication",
    │                         │     volunteer_id: "ahmed_uuid",
    │                         │     org_id: "current_org"
    │                         │   }                       │                    │
    │                         │──────────────────────────>│                    │
    │                         │              Insert verifications row          │
    │                         │──────────────────────────────────────────────>│
    │                         │         verification_level = 'org_attested'   │
    │                         │         attested_by_org = org.id              │
    │                         │         attested_by_user = admin.id           │
    │                         │         attested_at = now()                   │
    │                         │                     Success (201)             │
    │                         │<──────────────────────────────────────────────│
    │                         │<──────────────────────────┤                    │
    │ Attestation sent        │                           │                    │
    │ (Ahmed gets notified)   │                           │                    │
    │                                                     │                    │
    │                                    Ahmed accepts   │                    │
    │                                    (webhook event) │                    │
    │                                                     │                    │
    │                                    verification_level updated to
    │                                    'org_attested'
```

**Data model (verifications table):**

```sql
CREATE TABLE public.verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  competency TEXT NOT NULL, -- e.g., 'communication', 'leadership'
  verification_level verification_level NOT NULL DEFAULT 'self_assessed',

  -- For org attestation (Level 2)
  attested_by_org UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
  attested_by_user UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  attested_at TIMESTAMPTZ,

  -- For peer verification (Level 3)
  peer_verifications JSONB DEFAULT '[]', -- [{verifier_id, micro_assessment_score, verified_at}, ...]
  peer_count INT DEFAULT 0,

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  UNIQUE(volunteer_id, competency),
  CONSTRAINT valid_competency CHECK (competency IN (
    'communication', 'reliability', 'english_proficiency',
    'leadership', 'event_performance', 'tech_literacy',
    'adaptability', 'empathy_safeguarding'
  ))
);
```

**Effect on AURA Score:**
- Attested competencies have trust multiplier 1.15x
- If communication raw = 85, after attestation = 85 * 1.15 = 97.75
- Overall composite score recalculated and cached
- Capped at 100 (no boosting above hard limit)

**User sees on profile after attestation:**
```
🏅 Gold (Organization-Verified)  |  AURA: 88/100
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Communication: 97 ✅ (Attested by Mercy Corps)
📊 Leadership: 78 (Self-Assessed)
...
```

#### 3.3 Level 3: Peer-Verified (Network Effect)

The highest trust level. 3+ volunteers with Gold+ badge can collectively micro-assess and verify a competency.

**Preconditions:**
- Verifier must have Gold+ badge (AURA >= 75)
- Volunteer must have completed at least one assessment
- Verifier must have verified at least one other volunteer (preventing sybil attacks)
- Each peer verifier sees a micro-assessment (3-5 short questions in a live session)

**Flow (simplified):**

```
Verifier (Gold+)           Browser              FastAPI              Supabase
     │                        │                     │                   │
     │ Click "Verify Ahmed"   │                     │                   │
     │───────────────────────>│                     │                   │
     │                        │ GET /api/micro-assessment/ahmed
     │                        │────────────────────>│                   │
     │                        │    Load 3 questions │                   │
     │                        │    about Ahmed      │                   │
     │<───────────────────────│<────────────────────│                   │
     │ Complete 3 micro-Qs    │                     │                   │
     │───────────────────────>│                     │                   │
     │                        │ POST /api/peer-verification
     │                        │  {                  │                   │
     │                        │    volunteer_id: ahmed_id,
     │                        │    competency: "leadership",
     │                        │    score: 82        │                   │
     │                        │  }                  │                   │
     │                        │────────────────────>│                   │
     │                        │         Append to verifications.peer_verifications
     │                        │────────────────────────────────────────>│
     │                        │         {           │                   │
     │                        │           verifier_id: "verifier_uuid", │
     │                        │           score: 82,                    │
     │                        │           verified_at: now()            │
     │                        │         }                               │
     │                        │         peer_count += 1                 │
     │                        │<────────────────────────────────────────│
     │ ✅ Peer verification   │                     │                   │
     │    recorded            │                     │                   │
     │                        │                     │                   │
     │  [2nd verifier also    │                     │                   │
     │   completes micro-Qs]  │                     │                   │
     │                        │                     │                   │
     │  [3rd verifier also    │                     │                   │
     │   completes micro-Qs]  │                     │                   │
     │                        │                     │                   │
     │  When peer_count >= 3: │                     │                   │
     │  Trigger verification_level update to        │                   │
     │  'peer_verified' if avg score > min threshold│                   │
```

**Minimum threshold:** Average of 3 peer micro-assessments must be >= 60 to activate peer verification.

**Effect on AURA:**
- Peer-verified competencies: 1.25x trust multiplier
- If communication raw = 85, after peer verify = 85 * 1.25 = 106.25 (capped at 100)
- Creates network effect: users need other verified peers to reach the highest trust state

**User sees:**
```
🏅 Platinum (Peer-Verified)  |  AURA: 95/100
━━━━━━━━━━━━━━━━━━━━━━━━
📊 Communication: 100 ✅✅ (Verified by Leyla, Rauf, Tina)
📊 Leadership: 97 ✅ (Attested by UN Development Programme)
...
```

---

### 4. Authorization & Role-Based Access Control

#### 4.1 Roles & Permissions Matrix

| Action | Volunteer | Org Admin | Platform Admin |
|--------|-----------|----------|-----------------|
| View own profile | ✅ | ✅ | ✅ |
| View own AURA | ✅ | ✅ | ✅ |
| View public profiles | ✅ | ✅ | ✅ |
| Search volunteers | ❌ | ✅ | ✅ |
| Take assessment | ✅ | ✅ | ✅ |
| View competency scores | ✅ (own) | ✅ (own) | ✅ (all) |
| Attest competencies | ❌ | ✅ (own org) | ❌ |
| Peer-verify | ✅ (if Gold+) | ✅ (if Gold+) | ✅ |
| Create events | ❌ | ✅ (own org) | ✅ |
| Verify organization | ❌ | ❌ | ✅ |
| View audit log | ❌ | ❌ | ✅ |
| Manage admins | ❌ | ❌ | ✅ |

#### 4.2 Role Storage & RLS Enforcement

Roles stored in `profiles.role` column (PostgreSQL ENUM):

```sql
CREATE TYPE user_role AS ENUM ('volunteer', 'org_admin', 'platform_admin');

ALTER TABLE public.profiles ADD COLUMN role user_role DEFAULT 'volunteer';
```

**RLS Policies enforcing authorization:**

```sql
-- ========== VOLUNTEERS CAN ONLY READ OWN PROFILE ==========
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
ON public.profiles FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Anyone can read public profiles (non-sensitive columns)"
ON public.profiles FOR SELECT
USING (visibility = 'public')
WITH CHECK (visibility = 'public');

-- ========== VOLUNTEERS CAN UPDATE OWN PROFILE ONLY ==========
CREATE POLICY "Users can update own profile"
ON public.profiles FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- ========== COMPETENCY SCORES: VOLUNTEER READS OWN, ORG READS ORG'S, ADMIN READS ALL ==========
ALTER TABLE public.competency_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Volunteers read own competency scores"
ON public.competency_scores FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "Org admins read their org's volunteers' scores"
ON public.competency_scores FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM org_members
    WHERE org_members.user_id = auth.uid()
      AND org_members.role IN ('owner', 'admin')
      AND org_members.org_id IN (
        SELECT org_id FROM org_attestations
        WHERE volunteer_id = competency_scores.user_id
      )
  )
);

CREATE POLICY "Platform admins read all competency scores"
ON public.competency_scores FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
      AND profiles.role = 'platform_admin'
  )
);

-- ========== VERIFICATIONS: ATTESTATION ONLY BY ORG ADMINS ==========
ALTER TABLE public.verifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Org admins can attest within their org"
ON public.verifications FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM org_members om
    WHERE om.user_id = auth.uid()
      AND om.org_id = attested_by_org
      AND om.role IN ('owner', 'admin')
  )
);

CREATE POLICY "Users can see verifications for their own profile"
ON public.verifications FOR SELECT
USING (volunteer_id = auth.uid() OR auth.uid() IS NULL); -- NULL for public view

CREATE POLICY "Platform admin sees all verifications"
ON public.verifications FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
      AND profiles.role = 'platform_admin'
  )
);
```

#### 4.3 FastAPI Permission Checks

For actions not enforced by RLS, FastAPI validates roles:

```python
# apps/api/app/deps.py

async def require_org_admin(user_id: CurrentUserId, db: SupabaseUser) -> str:
    """
    Check if user is org admin of the org in the request.
    """
    result = await db.table("profiles").select("id").eq("id", user_id).execute()
    profile = result.data[0] if result.data else None

    if not profile or profile["role"] != "org_admin":
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Only org admins can perform this action"}
        )
    return user_id

async def require_platform_admin(user_id: CurrentUserId, db: SupabaseUser) -> str:
    """
    Check if user is platform admin.
    """
    result = await db.table("profiles").select("id").eq("id", user_id).execute()
    profile = result.data[0] if result.data else None

    if not profile or profile["role"] != "platform_admin":
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Only platform admins can perform this action"}
        )
    return user_id

# Usage in endpoint:
@router.post("/verifications")
async def create_attestation(
    payload: AttestationRequest,
    user_id: require_org_admin,  # This endpoint is org_admin only
    db: SupabaseUser
):
    """Org admin attests a volunteer's competency"""
    # Verify org membership
    org_result = await db.table("org_members").select("*").eq("user_id", user_id).eq("org_id", payload.org_id).execute()
    if not org_result.data:
        raise HTTPException(status_code=403, detail={"code": "NOT_ORG_MEMBER"})

    # Insert attestation
    attestation = {
        "volunteer_id": payload.volunteer_id,
        "competency": payload.competency,
        "verification_level": "org_attested",
        "attested_by_org": payload.org_id,
        "attested_by_user": user_id,
        "attested_at": datetime.utcnow().isoformat(),
    }
    result = await db.table("verifications").insert(attestation).execute()
    return result.data[0]
```

---

### 5. Session Management & Token Handling in Next.js

#### 5.1 Middleware: Auth & i18n Routing

```typescript
// apps/web/middleware.ts
import { type NextRequest, NextResponse } from "next/server"
import { createServerClient } from "@/lib/supabase/server"

const PUBLIC_ROUTES = ["/", "/auth", "/volunteers", "/events", "/about"]
const LOCALE_REGEX = /^\/([a-z]{2})/

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // ========== i18n ROUTING ==========
  // Detect locale from cookie, accept-language, or default to 'az'
  let locale = request.cookies.get("locale")?.value || "az"

  if (!pathname.match(LOCALE_REGEX)) {
    // No locale prefix: redirect to /az/... or /en/...
    const response = NextResponse.redirect(
      new URL(`/${locale}${pathname}`, request.url)
    )
    return response
  }

  // ========== AUTH CHECK ==========
  const supabase = await createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  // Protected routes require auth
  const isProtectedRoute = pathname.startsWith("/dashboard") ||
                           pathname.startsWith("/assessment") ||
                           pathname.startsWith("/org")

  if (isProtectedRoute && !session) {
    // Redirect to login
    return NextResponse.redirect(
      new URL(`/${locale}/auth/login?redirect=${encodeURIComponent(pathname)}`, request.url)
    )
  }

  // Allow through
  return NextResponse.next()
}

export const config = {
  matcher: [
    // Match all routes except static files
    "/((?!_next/static|_next/image|favicon.ico|public).*)",
  ],
}
```

#### 5.2 Client-Side Auth State Management

```typescript
// apps/web/lib/auth/auth-store.ts
import { create } from "zustand"
import { createClient } from "@/lib/supabase/client"

interface AuthStore {
  user: User | null
  session: Session | null
  isLoading: boolean
  signInWithMagicLink: (email: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthStore>((set) => {
  const supabase = createClient()

  return {
    user: null,
    session: null,
    isLoading: true,

    initialize: async () => {
      const { data: { session } } = await supabase.auth.getSession()
      set({ session: session, user: session?.user || null, isLoading: false })

      // Listen for auth changes
      supabase.auth.onAuthStateChange((event, session) => {
        set({ session, user: session?.user || null })

        if (event === "SIGNED_OUT") {
          // Invalidate all cached API data
          window.location.href = "/auth/login"
        }
      })
    },

    signInWithMagicLink: async (email: string) => {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    },

    signInWithGoogle: async () => {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
          scopes: "openid profile email",
        },
      })
      if (error) throw error
    },

    signOut: async () => {
      await supabase.auth.signOut()
      set({ user: null, session: null })
    },
  }
})
```

#### 5.3 Protected Component Pattern

```typescript
// apps/web/components/dashboard.tsx
"use client"
import { useAuthStore } from "@/lib/auth/auth-store"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

export function Dashboard() {
  const router = useRouter()
  const { user, isLoading } = useAuthStore()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/auth/login")
    }
  }, [user, isLoading])

  if (isLoading) return <div>Loading...</div>
  if (!user) return null

  return (
    <div>
      <h1>Welcome, {user.email}</h1>
      {/* Dashboard content */}
    </div>
  )
}
```

---

### 6. Security Considerations

#### 6.1 Rate Limiting

**Supabase Auth (built-in):**
- Magic link: 5 requests per email per hour
- OTP verification: 5 attempts per token

**FastAPI custom middleware** (apps/api/app/middleware/rate_limit.py):

```python
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app
        self.requests = defaultdict(list)  # {ip: [timestamps]}

    async def __call__(self, request: Request, call_next):
        ip = request.client.host
        now = datetime.utcnow()

        # Clean old requests (> 1 minute ago)
        self.requests[ip] = [
            ts for ts in self.requests[ip]
            if now - ts < timedelta(minutes=1)
        ]

        # Auth endpoints: 10 req/min per IP
        if request.url.path.startswith("/auth"):
            if len(self.requests[ip]) >= 10:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"code": "RATE_LIMITED", "message": "Too many requests"}
                )

        # Other API: 100 req/min per IP
        elif len(self.requests[ip]) >= 100:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED"}
            )

        self.requests[ip].append(now)
        return await call_next(request)
```

**Applied to FastAPI:**
```python
# apps/api/main.py
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI()
app.add_middleware(RateLimitMiddleware)
```

#### 6.2 CSRF Protection (SameSite Cookies)

Supabase Auth automatically sets:
```
Set-Cookie: sb-auth-token=...; SameSite=Lax; Secure; HttpOnly
```

- `SameSite=Lax`: Cookies sent on top-level navigation from external sites, but not for cross-site form submissions
- `Secure`: HTTPS only
- `HttpOnly`: Not accessible to JavaScript (prevents XSS exfiltration)

#### 6.3 XSS Prevention

**Content Security Policy (CSP)** in Next.js middleware:

```typescript
// apps/web/middleware.ts
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-inline' *.google.com *.supabase.co;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' *.supabase.co *.vercel.app;
`

export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  response.headers.set("Content-Security-Policy", cspHeader)
  return response
}
```

**Frontend best practices:**
- All user inputs via React (automatic HTML escaping)
- Never use `dangerouslySetInnerHTML` unless sanitized with DOMPurify
- Supabase SDK prevents injection (parameterized queries)

#### 6.4 Passwordless Security

Since no passwords:
- **No brute-force attacks** on passwords
- **Email compromise still critical**: Requires org email domain (e.g., `volunteer@mercycorps.org`)
- **Magic link expires in 24 hours**: Single-use token revoked after first click
- **Refresh token rotation**: Supabase rotates refresh token on each use

#### 6.5 API Key Security (Org Integrations)

For organizations accessing volunteer data via API (v1):

```python
# Create org API key
@router.post("/orgs/{org_id}/api-keys")
async def create_api_key(
    org_id: UUID,
    user_id: require_org_admin,
    db: SupabaseUser
) -> APIKeyResponse:
    """Generate API key for org (shown once)"""
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    await db.table("org_api_keys").insert({
        "org_id": org_id,
        "key_hash": key_hash,
        "created_by": user_id,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return APIKeyResponse(api_key=api_key, warning="Save this key — it won't be shown again")

# Verify API key in FastAPI
async def verify_api_key(key: str = Header(...), db: SupabaseAdmin) -> UUID:
    """Verify org API key and return org_id"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    result = await db.table("org_api_keys").select("org_id").eq("key_hash", key_hash).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail={"code": "INVALID_API_KEY"})
    return result.data[0]["org_id"]
```

---

### 7. Token Expiry & Refresh

| Token Type | Expiry | Refresh | Storage |
|-----------|--------|---------|---------|
| access_token | 15 min | Via refresh_token | HttpOnly cookie |
| refresh_token | 30 days | Rotates on each use | HttpOnly cookie |
| Magic link | 24 hours | N/A (single-use) | Email link |

**Refresh flow (automatic in Supabase SDK):**
1. Access token expires (15 min)
2. Browser detects 401 on API call
3. SDK calls `POST /auth/v1/token` with refresh_token
4. Supabase issues new access_token (rotate refresh_token too)
5. Retry original request

---

### 8. Org Attestation Workflow (End-to-End)

#### 8.1 Pre-Attestation: Volunteer Completes Assessment

```
1. Ahmed takes 8-competency assessment
2. Receives AURA: 82/100 (all self-assessed)
3. Notification: "Tell orgs where you volunteered"
```

#### 8.2 Org Finds & Attests

```
Mercy Corps admin:
1. Logs into Mercy Corps dashboard
2. Searches: "Ahmed"
   - Finds: Ahmed's profile, AURA 82 (self-assessed)
   - Sees: Communication 85, Leadership 78, etc.
3. Clicks: "This person volunteered for us"
4. Selects: ["Communication", "Leadership"] (not all 8)
5. Leaves note: "Led community mobilization in Ganja, June-Aug 2025"
6. Clicks "Send Attestation"
   → Attestation created in DB with org_attested status
   → Ahmed gets notification: "Mercy Corps confirmed your Leadership & Communication"
7. Ahmed reviews attestation, clicks "Accept"
   → verification_level changes to 'org_attested'
   → AURA recalculated (boosted by 1.15x for those competencies)
   → New score: ~86/100

Ahmed's profile now shows:
  Communication: 97 ✅ (Attested by Mercy Corps)
  Leadership: 89 ✅ (Attested by Mercy Corps)
  Other competencies: Still self-assessed
```

---

### 9. Peer Verification Workflow (End-to-End)

#### 9.1 Setup: Create Micro-Assessment Questions

```sql
-- Questions for peer verification (separate from main assessment)
INSERT INTO questions (competency, question_type, text, options)
VALUES
  ('communication', 'open_text', 'Tell about Ahmed''s communication skills', NULL),
  ('communication', 'bars', 'How clear is Ahmed''s written English?', '[0..10]'),
  ('communication', 'mcq', 'Ahmed explained a complex concept to you. How?',
   '[A: Very clearly, B: Somewhat, C: Poorly]');
```

#### 9.2 Verifier Completes Micro-Assessment

```
Leyla (Gold volunteer):
1. Browses: "Volunteers Needing Peer Verification"
   → See Ahmed: AURA 86 (2 orgs attested, 6 self-assessed)
2. Clicks: "Verify Ahmed"
3. Completes micro-assessment:
   - "Tell about Ahmed's communication skills" → Types positive feedback
   - "How clear is Ahmed's English?" → Rates 8/10
   - "Ahmed explained X to you. How?" → Selects A (Very clearly)
4. Submits
   → System scores micro-assessment responses (LLM eval for open_text)
   → Peer verification record created
   → Leyla's verification recorded (score: 82)

Rauf & Tina (also Gold) do the same.

System detects: 3 peer verifications for Ahmed's communication
  Average score: (82 + 79 + 85) / 3 = 82 > 60 threshold ✅
  → verification_level = 'peer_verified' for communication
  → AURA boosted by 1.25x for that competency
  → New communication score: 97 * 1.25 = 100 (capped)

Ahmed's profile now shows:
  Communication: 100 ✅✅ (Verified by Leyla, Rauf, Tina)
  Leadership: 89 ✅ (Attested by Mercy Corps)
```

---

## Options Considered

### Option A: OAuth Only (No Magic Link)

**Pros:**
- Simpler (only one auth flow)
- Industry-standard

**Cons:**
- Many users in Azerbaijan don't have Google accounts
- Requires internet (Google redirects)
- Less accessible for low-tech volunteers
- **Rejected**

### Option B: Email + Password

**Pros:**
- Traditional, familiar

**Cons:**
- Password reset flows add complexity
- Users write passwords on sticky notes (common in Azerbaijan)
- No security benefit over passwordless
- **Rejected**

### Option C: Phone-Based OTP

**Pros:**
- Very accessible in Azerbaijan (high mobile penetration)
- Works on any phone

**Cons:**
- SMS cost (~$0.01 per message, scales poorly)
- Requires verified phone numbers (adds friction)
- SIM-swapping attacks possible
- **Considered, deferred to post-launch**

### Option D: Two-Level Verification (No Peer)

**Pros:**
- Simpler to implement
- Faster to launch

**Cons:**
- No network effect for scaling trust
- Volunteers plateau at "org-attested" (less motivation)
- Organizations become gatekeepers (less decentralized)
- **Rejected in favor of 3-level**

---

## Consequences

### Positive

1. **Seamless UX**: No password resets, magic link is fastest auth flow
2. **Trustworthy scores**: Three-level verification makes AURA scores meaningful
3. **Decentralized credentialing**: Peer verification creates network effects (volunteers help each other)
4. **Scalable**: Supabase Auth scales to 10,000+ users with minimal cost
5. **Audit trail**: All attestations & verifications logged with org/user metadata
6. **Safe for orgs**: RLS prevents volunteers from seeing other org's volunteers
7. **GDPR-adjacent**: No password storage, easy to delete user data (Supabase handles via cascades)

### Negative

1. **Email dependency**: If user loses email access, can't log in (mitigated by Google OAuth backup)
2. **Org attestation requires manual effort**: Not automated (by design — orgs should review)
3. **Micro-assessment creates extra friction**: Peer verifiers must spend 5 min per verification
4. **Trust multiplier math is opaque**: Users may not understand why AURA jumped from 86 to 95

### Mitigation

1. Offer account recovery via Google (link Google account to existing email)
2. Orgs can bulk-attest via CSV import (future feature)
3. Offer incentives for peer verification (badges, leaderboard rank)
4. Publish AURA calculation formula on help page

---

## Action Items

### Before Launch (Critical)

- [ ] Implement FastAPI JWT verification dependency (get_current_user)
- [ ] Create verifications table migration + RLS policies
- [ ] Build org attestation endpoint + UI in org dashboard
- [ ] Build peer verification micro-assessment UI + scoring
- [ ] Set up email templates (magic link, attestation notification, peer request)
- [ ] Test Supabase Auth with magic link (offline scenarios)
- [ ] Test token refresh on real unstable WiFi (simulate in QA)
- [ ] Add CSP headers to Next.js middleware
- [ ] Rate limiting middleware for FastAPI
- [ ] Platform admin panel: verify organizations

### Post-Launch (Quick Wins)

- [ ] Bulk attestation import (CSV for orgs)
- [ ] Phone-based OTP as backup auth method
- [ ] AURA calculation formula docs (help center article)
- [ ] Org API v1: search volunteers by competency + AURA
- [ ] Peer verification leaderboard (top verifiers)
- [ ] Email: "You can now be peer-verified!" when user hits Silver

### Future (6+ months)

- [ ] Apple Sign-In for iOS app
- [ ] Telegram Login Widget (pre-register via Telegram)
- [ ] Delegation: Org owner delegates attestation to team members
- [ ] Revocation: Org can revoke attestation if volunteer left
- [ ] Peer verification: Verifier can retract their verification (if score was wrong)
- [ ] Anonymous peer verification (remove verifier name from volunteer's view)
- [ ] Custom competency frameworks for large orgs

---

## Security Checklist

- [x] Supabase JWT verified by FastAPI
- [x] RLS policies on all tables with personal data
- [x] Rate limiting on auth endpoints
- [x] CSRF protection via SameSite=Lax cookies
- [x] XSS prevention via CSP + HttpOnly cookies
- [x] No plaintext passwords (passwordless)
- [x] Refresh token rotation (handled by Supabase)
- [x] Per-request Supabase client (no global state)
- [x] API keys hashed before storage (org integrations)
- [x] Attestation audit trail (org_id, user_id, timestamp)

---

## Glossary

- **access_token**: Short-lived JWT (15 min), sent in Authorization header for API calls
- **refresh_token**: Long-lived token (30 days), used to get new access_token
- **RLS**: Row-Level Security, PostgreSQL feature that filters rows based on user role
- **Peer verification**: 3+ Gold+ volunteers confirm a competency via micro-assessment
- **Org attestation**: Organization formally confirms volunteer's competency
- **Trust multiplier**: Factor applied to raw competency score based on verification level (1.0x, 1.15x, 1.25x)
- **Micro-assessment**: Short quiz (3-5 Qs) verifiers answer about a volunteer
- **Verification level**: One of {self_assessed, org_attested, peer_verified}

---

## Related Documents

- [[ADR-001-system-architecture]]: System design (Supabase, FastAPI, Vercel)
- [[ADR-002-database-schema]]: Profile, competency, assessment schema
- [[ADR-004-api-security]]: API rate limiting, API key management, audit logs
- [[ADR-005-aura-scoring]]: AURA composite score calculation with multipliers

