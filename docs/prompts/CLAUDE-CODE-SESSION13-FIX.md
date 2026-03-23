# Session 13-FIX: Codebase Quality Hardening

> **Run this BEFORE Session 13 (Org Pages). No new features until every fix below is committed.**

---

## 🎯 Mission

Yusif's words: "то что ошибок нет не означает что всё там правильно" — no errors doesn't mean everything is correct.

This prompt addresses issues found by a consolidated audit of Sessions 1-12. The codebase runs, tests pass, but there are security gaps, missing i18n, accessibility holes, and inconsistent patterns that will compound if we build on top of them.

**Rules:**
- Fix everything below IN ORDER (security first, then quality)
- Run `pytest` after each fix group — zero regression allowed
- Each fix = 1 atomic commit with descriptive message
- Do NOT build any new features. Only improve what exists.

---

## 👤 Who You Are

You are Yusif's CTO and co-founder. $50/mo budget, 6-week timeline. You own quality.

**Communication style:**
- Direct. No hedging. "[Verdict]. [Reason]. [Action]."
- If something is wrong, say it. Yusif prefers blunt honesty.
- At the end, write: `🧭 If you said nothing, here's what I'd do next: [3 items]`

---

## 📋 Context: What Already Exists

### Sessions 1-4: Backend Foundation
- 25 Python files, 12 SQL migrations, 72+ tests passing
- FastAPI + Supabase + per-request client via Depends()
- Pure Python IRT/CAT engine (3PL + EAP)
- AURA scoring with 8 competencies and weighted aggregation
- Rate limiting on auth + assessment endpoints (slowapi)
- JWT validation via server-side admin.auth.get_user()
- Structured error responses on all endpoints

### Sessions 5-10: Frontend Architecture
- Next.js 14 App Router + shadcn/ui + Tailwind CSS 4
- Pages: Landing, Login, Callback, Dashboard, Profile, AURA, Assessment, Settings, Public Profile
- react-i18next (AZ primary, EN secondary) — but INCOMPLETE coverage (see fixes below)
- Zustand for auth state, TanStack Query for server state

### Session 11: API Integration
- INTERIM API client (`lib/api/client.ts`) with envelope unwrapping
- INTERIM TypeScript types (`lib/api/types.ts`) — all marked with TODO for @hey-api/openapi-ts replacement
- TanStack Query hooks: useAuraScore, useProfile, useBadges, useActivity
- Pages rewired: Dashboard, Profile, AURA → use hooks instead of manual fetch
- Security: Fixed protocol-relative open redirect in login + callback

### Session 12: Stitch Design System
- Dark theme migration: globals.css rewritten with Material 3 tokens
- Components updated: TopBar, Sidebar, LanguageSwitcher
- New pages: Leaderboard (podium + ranked list), Notifications (categories + actions)
- i18n: +14 keys for leaderboard + notifications

---

## ⚠️ Mistakes Log — DO NOT REPEAT

1. **Never use global Supabase client** — always per-request via Depends()
2. **Never use Pydantic v1** — ConfigDict, @field_validator only
3. **Never use print()** — loguru only
4. **Never hardcode strings** — i18n t() function for ALL user-facing text
5. **Never use `getattr(settings, "field", default)`** — access settings.field directly
6. **Never use relative routing** — always `/${locale}/path`
7. **Always unwrap API envelope** — response.data, not raw response
8. **Always use isMounted pattern** for async state updates in components
9. **Always check Python version compatibility** before adding deps
10. **Schema verification** — INTERIM types MUST match real Pydantic schemas

---

## 🏗️ Architecture Quick Reference

```
apps/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── config.py       # Settings (Pydantic BaseSettings)
│   │   ├── deps.py         # SupabaseAdmin, SupabaseUser, CurrentUserId
│   │   ├── main.py         # App + middleware + router registration
│   │   ├── core/assessment/ # IRT/CAT engine + BARS evaluator
│   │   ├── middleware/      # rate_limit.py, security_headers.py
│   │   ├── routers/        # auth, profiles, assessment, aura, badges, events, organizations, verification, health
│   │   ├── schemas/        # Pydantic v2 models
│   │   └── services/       # llm.py (Gemini primary, OpenAI fallback)
│   └── tests/
├── web/                    # Next.js 14 frontend
│   └── src/
│       ├── app/[locale]/   # Pages (App Router)
│       ├── components/     # UI components
│       ├── hooks/queries/  # TanStack Query hooks
│       ├── lib/api/        # INTERIM client + types
│       ├── locales/{en,az}/ # i18n JSON files
│       └── stores/         # Zustand
supabase/
├── migrations/             # SQL migrations (YYYYMMDDHHMMSS_*.sql)
└── seed.sql                # Dev seed data
```

**API prefix pattern:** `app.include_router(router, prefix="/api")` → all routes are `/api/...`
**API response envelope:** `{ "data": ..., "meta": ... }` — always unwrap `.data`

---

## 🔴 FIX GROUP 1: Security (do first)

### Fix 1.1: Missing auth check on list_registrations (HIGH)
**File:** `apps/api/app/routers/events.py` lines 249-257
**Bug:** `list_registrations` uses `db_admin` (service role, bypasses RLS) but does NOT verify that the requesting user is the event's org owner. ANY authenticated user can list ALL registrations for ANY event — leaks volunteer PII (names, ratings, feedback).

**Fix:**
```python
@router.get("/{event_id}/registrations", response_model=list[RegistrationResponse])
async def list_registrations(
    event_id: str,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> list[RegistrationResponse]:
    """List registrations for an event — org owner only."""
    # SECURITY: Verify requesting user owns the event's organization
    event_result = await db_admin.table("events").select("organization_id").eq("id", event_id).single().execute()
    if not event_result.data:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})

    org_result = await db_admin.table("organizations").select("owner_id").eq("id", event_result.data["organization_id"]).single().execute()
    if not org_result.data or org_result.data["owner_id"] != str(user_id):
        raise HTTPException(status_code=403, detail={"code": "NOT_ORG_OWNER", "message": "Only the organization owner can view registrations"})

    result = await db_admin.table("registrations").select("*").eq("event_id", event_id).execute()
    return [RegistrationResponse(**row) for row in (result.data or [])]
```

### Fix 1.2: Nondeterministic hash() in rate limiter (MEDIUM)
**File:** `apps/api/app/middleware/rate_limit.py` line 25
**Bug:** Python's `hash()` is randomized per process (PYTHONHASHSEED). Two workers will compute different rate-limit keys for the same token → rate limits don't work across workers.

**Fix:**
```python
import hashlib

def _key_func(request: Request) -> str:
    """Rate limit key: IP address + user ID if authenticated."""
    ip = get_remote_address(request)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        # Deterministic hash — consistent across workers
        token_hash = hashlib.sha256(auth[7:40].encode()).hexdigest()[:12]
        return f"{ip}:{token_hash}"
    return ip
```

### Fix 1.3: Missing rate limiting on write endpoints (MEDIUM)
**Files:** `events.py`, `organizations.py`, `profiles.py`
**Bug:** 13 write endpoints have no rate limiting. Auth (5/min) and assessment (3/hr, 60/hr) are protected, but event creation, org creation, profile updates, search, check-in, and rating endpoints are wide open.

**Fix:** Add `@limiter.limit()` decorators to all write endpoints:
```python
from app.middleware.rate_limit import limiter, RATE_PROFILE_WRITE, RATE_DEFAULT

# For event/org creation:
@limiter.limit(RATE_PROFILE_WRITE)  # 10/minute
@router.post("/events", ...)

# For search endpoints:
@limiter.limit(RATE_DEFAULT)  # 60/minute
@router.post("/organizations/search/volunteers", ...)

# For rating endpoints:
@limiter.limit(RATE_PROFILE_WRITE)  # 10/minute
@router.post("/{event_id}/rate/coordinator", ...)
```

Apply to ALL of these:
- `events.py`: POST /events, PUT /events/{id}, DELETE /events/{id}, POST /events/{id}/register, POST /events/{id}/checkin, POST /events/{id}/rate/coordinator, POST /events/{id}/rate/volunteer
- `organizations.py`: POST /organizations, PUT /organizations/me, POST /organizations/search/volunteers
- `profiles.py`: POST /profiles/me, PUT /profiles/me, POST /profiles/{id}/verification-link

### Fix 1.4: Missing input validation on VolunteerSearchRequest (MEDIUM)
**File:** `apps/api/app/schemas/organization.py` lines 45-52
**Bug:** No validation on search query length, limit max, offset bounds, or badge_tier enum. Allows arbitrarily long queries (Gemini embedding will fail), unlimited pagination (DoS), and invalid badge tiers.

**Fix:**
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator

class VolunteerSearchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=1, max_length=500)
    competency_id: str | None = None
    badge_tier: str | None = None
    min_aura: float = 0
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("badge_tier")
    @classmethod
    def validate_badge_tier(cls, v: str | None) -> str | None:
        if v is not None and v not in ("platinum", "gold", "silver", "bronze"):
            raise ValueError("Invalid badge tier. Must be: platinum, gold, silver, bronze")
        return v
```

### Fix 1.5: Missing string length validation on OrganizationCreate (MEDIUM)
**File:** `apps/api/app/schemas/organization.py` lines 11-26
**Bug:** `name`, `description`, `website_url` have no length constraints. Allows DB bloat.

**Fix:** Add Field constraints:
```python
class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website_url: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None  # EmailStr if pydantic[email] installed

class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    website_url: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = None
```

---

## 🟡 FIX GROUP 2: Frontend Bug (language-switcher)

### Fix 2.1: Relative URL in language switcher
**File:** `apps/web/src/components/layout/language-switcher.tsx` line 17
**Bug:** `router.push(segments.join("/"))` produces a relative URL when pathname is `"/"` — `segments = ["", ""]`, joined = `""` (empty string). Also, if pathname doesn't start with a locale, `segments[1] = newLocale` inserts at wrong position.

**Fix:**
```typescript
function switchLocale(newLocale: Locale) {
    if (newLocale === currentLocale) return;
    const segments = pathname.split("/");
    segments[1] = newLocale;
    const newPath = segments.join("/") || "/";
    // Ensure absolute path
    router.push(newPath.startsWith("/") ? newPath : `/${newPath}`);
}
```

---

## 🟡 FIX GROUP 3: i18n Hardcoded Strings

### Fix 3.1: Settings page — 5 hardcoded strings
**File:** `apps/web/src/app/[locale]/(dashboard)/settings/page.tsx`
**Strings to replace:**
- Line 9: `"Settings"` → `t("settings.title")`
- Line 12: `"Language"` → `t("settings.language")`
- Line 14: `"Interface language"` → `t("settings.interfaceLanguage")`
- Line 20: `"Account"` → `t("settings.account")`
- Line 22: `"Manage your account settings via your profile page."` → `t("settings.accountDescription")`

### Fix 3.2: Public profile page — 4 hardcoded strings
**File:** `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx`
**Strings to replace:**
- Line 134: `"AURA Score"` → `t("publicProfile.auraScore")`
- Line 157: `"AURA score not yet available"` → `t("publicProfile.auraNotAvailable")`
- Line 163: `"Want your own verified AURA score?"` → `t("publicProfile.ctaTitle")`
- Line 165: `"Join Volaura, complete your assessment..."` → `t("publicProfile.ctaDescription")`

**Note:** This is a public page. Add `useTranslation` (client component) or `initTranslations` (server component) depending on current pattern.

### Fix 3.3: Leaderboard + Notifications hardcoded labels
**File:** `apps/web/src/app/[locale]/(dashboard)/leaderboard/page.tsx` lines 177-181
**File:** `apps/web/src/app/[locale]/(dashboard)/notifications/page.tsx` lines 150-154
**Bug:** These files have inline AZ/EN label objects instead of using i18n t() function. Replace with proper i18n keys.

### Fix 3.4: Assessment open-text placeholder
**File:** `apps/web/src/components/assessment/open-text-answer.tsx` line 18
**String:** `"Type your answer here..."` → `t("assessment.answerPlaceholder")`

### Fix 3.5: Share buttons
**File:** `apps/web/src/components/aura/share-buttons.tsx` lines 91, 95, 99
**Strings:** `"Telegram"`, `"LinkedIn"`, `"WhatsApp"` — these are brand names and can stay hardcoded. **SKIP this fix.**

### i18n keys to add
Add ALL new keys to BOTH `apps/web/src/locales/en/common.json` AND `apps/web/src/locales/az/common.json`:

```json
// EN
{
  "settings": {
    "title": "Settings",
    "language": "Language",
    "interfaceLanguage": "Interface language",
    "account": "Account",
    "accountDescription": "Manage your account settings via your profile page."
  },
  "publicProfile": {
    "auraScore": "AURA Score",
    "auraNotAvailable": "AURA score not yet available",
    "ctaTitle": "Want your own verified AURA score?",
    "ctaDescription": "Join Volaura, complete your assessment, and share your verified volunteer badge."
  },
  "assessment": {
    "answerPlaceholder": "Type your answer here..."
  }
}
```

```json
// AZ — account for 20-30% longer text, special chars: ə ğ ı ö ü ş ç
{
  "settings": {
    "title": "Parametrlər",
    "language": "Dil",
    "interfaceLanguage": "İnterfeys dili",
    "account": "Hesab",
    "accountDescription": "Hesab parametrlərini profil səhifəsindən idarə edin."
  },
  "publicProfile": {
    "auraScore": "AURA Balı",
    "auraNotAvailable": "AURA balı hələ mövcud deyil",
    "ctaTitle": "Öz təsdiqlənmiş AURA balınızı istəyirsiniz?",
    "ctaDescription": "Volaura-ya qoşulun, qiymətləndirmənizi tamamlayın və təsdiqlənmiş könüllü nişanınızı paylaşın."
  },
  "assessment": {
    "answerPlaceholder": "Cavabınızı buraya yazın..."
  }
}
```

---

## 🟡 FIX GROUP 4: Accessibility

### Fix 4.1: Auth guard loading spinner needs aria-label
**File:** `apps/web/src/components/layout/auth-guard.tsx` line 39
**Fix:** Add `role="status" aria-label={t("loading.default")}` to the spinner container.

### Fix 4.2: Sidebar logout button needs aria-label
**File:** `apps/web/src/components/layout/sidebar.tsx` line 68
**Fix:** Add `aria-label={t("nav.logout")}` to the logout button.

### Fix 4.3: Assessment textarea aria-label should use i18n
**File:** `apps/web/src/components/assessment/open-text-answer.tsx` line 44
**Fix:** Replace hardcoded `aria-label="Open text answer"` with `aria-label={t("assessment.answerPlaceholder")}`.

---

## 🟡 FIX GROUP 5: TanStack Query Hardening

### Fix 5.1: Add retry config to query hooks
**Files:** `apps/web/src/hooks/queries/use-profile.ts`, `use-aura.ts`
**Bug:** No retry configuration. TanStack Query defaults to 3 retries, but staleTime is not set — every mount refetches.

**Fix:** Add consistent config:
```typescript
export function useProfile() {
  const token = useAuthToken();
  return useQuery({
    queryKey: ["profile", "me"],
    queryFn: () => apiFetch<ProfileResponse>("/api/profiles/me", { token }),
    enabled: !!token,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}
```

Apply same pattern to: `useAuraScore`, `useProfile`, `usePublicProfile`, `useBadges`.

### Fix 5.2: Fix useActivity empty array fallback
**File:** `apps/web/src/hooks/queries/use-dashboard.ts`
**Bug:** `useActivity()` catches errors and returns empty array — breaks TanStack Query retry logic and error boundary pattern.

**Fix:** Remove the try/catch. Let the error propagate. The component already handles `isError` state.

---

## 🟢 FIX GROUP 6: Error Boundaries

### Fix 6.1: Add error.tsx to dashboard layout
**File:** Create `apps/web/src/app/[locale]/(dashboard)/error.tsx`

```tsx
"use client";

import { useTranslation } from "react-i18next";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h2 className="text-xl font-semibold text-on-surface">
        {t("error.generic")}
      </h2>
      <p className="max-w-md text-on-surface-variant">
        {t("error.tryAgain")}
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-primary px-4 py-2 text-on-primary transition-colors hover:bg-primary/90"
      >
        {t("error.retry")}
      </button>
    </div>
  );
}
```

Add i18n key `"error.tryAgain"`:
- EN: `"Something went wrong. Please try again."`
- AZ: `"Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin."`

---

## ✅ Verification Checklist (run after ALL fixes)

After completing all fix groups:

1. **Backend tests:** `cd apps/api && pytest -v` — MUST be 72+ tests, 0 failures
2. **Frontend lint:** `cd apps/web && pnpm lint` — 0 errors
3. **Frontend build:** `cd apps/web && pnpm build` — 0 errors
4. **i18n completeness:** Verify every key in `en/common.json` has a matching key in `az/common.json`
5. **No regressions:** All existing pages still render (dashboard, profile, aura, assessment, leaderboard, notifications, settings)
6. **Security spot-check:** Manually verify `list_registrations` now returns 403 for non-owner

---

## 📊 DSP Council Review Summary

```
🔮 DSP: Session 13-FIX — Fix Before Build
Stakes: High | Reversibility: High (all fixes are additive) | Model: sonnet
Council: All 6 personas

Leyla (Volunteer, 22yo, mobile):
  "Hardcoded strings mean I can't use the app in Azerbaijani properly.
   Settings page shows English even when I switch to AZ. Fix i18n first —
   I'll stop using the app if it feels half-translated."

Nigar (Org Admin, HR manager):
  "The missing auth on list_registrations is a GDPR-level issue. I manage
   50+ volunteers — if any user can see my event's registration data including
   ratings and feedback, that's a trust violation. This MUST be fix #1."

Attacker:
  "Fix 1.1 (missing auth) is exploitable TODAY. Any authenticated user can
   enumerate event IDs and dump all registration data. Fix 1.2 (hash) means
   rate limits are effectively disabled with >1 worker. Fix 1.4 (no query
   length limit) = trivial DoS via 100KB search query to Gemini embedding."

Scaling Engineer:
  "Rate limiting gaps (Fix 1.3) matter even at current scale. One bot can
   create unlimited events and registrations. At 10x users, the missing
   staleTime in TanStack Query hooks means every component mount hits the API —
   add staleTime: 5min to all hooks."

Yusif (Founder):
  "$50/mo budget. These are all cheap fixes — no new infra, no new deps.
   The i18n fixes are critical for Azerbaijan launch. Do security first,
   i18n second, everything else third."

QA Engineer:
  "Error boundaries (Fix 6.1) prevent white-screen crashes. Currently if
   any dashboard child throws, the entire layout dies. One error.tsx file
   catches all unhandled errors gracefully."

Score: 44/50 (T:9 U:9 S:9 F:9 R:8)
Winner: Execute all fixes in stated order (security → bug → i18n → a11y → queries → boundaries)
Accepted risks: No visual regression testing (no Playwright yet)
Fallback: If any fix causes test regression, revert that fix only and document for next session
```

---

## 🚫 NEVER / ✅ ALWAYS (Full List)

### NEVER
- Use SQLAlchemy or any ORM — Supabase SDK only
- Use global Supabase client — per-request via Depends()
- Use Pydantic v1 syntax (`class Config`, `orm_mode`, `@validator`)
- Use `google-generativeai` — use `google-genai`
- Use print() — use loguru
- Hardcode strings — use i18n t()
- Use Redux — use Zustand
- Use Pages Router — use App Router only
- Use relative routing — always `/${locale}/path`
- Use `getattr(settings, "field", default)` — use `settings.field`

### ALWAYS
- UTF-8 encoding everywhere
- Per-request Supabase client via Depends()
- Type hints on all Python functions
- Strict TypeScript (no `any`)
- i18n for ALL user-facing strings
- RLS policies on all tables
- Structured JSON error responses (`detail: {"code": "...", "message": "..."}`)
- isMounted ref pattern on components with async state
- Absolute routing: `/${locale}/path`
- Unwrap API response envelope: `response.data`
- AZ strings: 20-30% longer, special chars (ə ğ ı ö ü ş ç), date DD.MM.YYYY

---

## 🧭 After This Fix Session

Once all fixes are committed and verified:
1. Proceed to Session 13: Org Launch Bundle (`docs/prompts/CLAUDE-CODE-SESSION13-ORG-EVENTS.md`)
2. The codebase will be secure, fully i18n'd, accessible, and resilient
3. New features build on a solid foundation instead of compounding hidden issues
