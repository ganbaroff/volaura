---
description: Next.js 14 App Router + Tailwind 4 + i18n rules — AZ primary locale, TanStack Query, shadcn
globs:
  - "apps/web/**"
---

# Frontend Rules (Next.js 14 + shadcn + i18n)

## App Router Only
- All pages in `app/[locale]/` directory
- Use `generateStaticParams` for locale segments
- Server Components by default, `"use client"` only when needed
- Use `params: Promise<{}>` pattern (Next.js 14.2+)

## i18n
```tsx
// Server Component
import initTranslations from "@/app/i18n";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);
  return <h1>{t("landing.title")}</h1>;
}

// Client Component
"use client";
import { useTranslation } from "react-i18next";

export function MyComponent() {
  const { t } = useTranslation();
  return <p>{t("common.loading")}</p>;
}
```

## Component Patterns
- Use shadcn/ui for base components
- Compose features in `components/features/`
- Use `cn()` from `@/lib/utils/cn` for conditional classes
- Props interfaces above component definition

## State Management
- Server state: TanStack Query (fetching, caching, mutations)
- Client state: Zustand stores in `stores/`
- Form state: React Hook Form + Zod

## Supabase (Browser)
```typescript
import { createClient } from "@/lib/supabase/client";
const supabase = createClient();
```

## Supabase (Server Component)
```typescript
import { createClient } from "@/lib/supabase/server";
const supabase = await createClient();
```

## Supabase — library-source verification gate (INC-018, 2026-04-17)

Before pinning ANY `@supabase/ssr` or `@supabase/supabase-js` auth option as a "fix" (`flowType`, `detectSessionInUrl`, `autoRefreshToken`, `persistSession`, `storage`, `storageKey`):

1. Run `npm pack @supabase/ssr@<installed-version>` (or the relevant package) to `/tmp`.
2. Read the corresponding factory source (`createBrowserClient.js` / `createServerClient.js`).
3. Verify the option is actually honored — not hardcoded after the user-options spread.
4. If hardcoded: the userland "fix" is a no-op. Move the fix to the consumer (the code that calls exchange / getSession / etc.), not the client factory.

INC-018 REV1 (Session 117) shipped `auth: { detectSessionInUrl: false }` in `apps/web/src/lib/supabase/client.ts` and declared the OAuth PKCE race resolved. It was a no-op: `@supabase/ssr` 0.6.0 hardcodes `detectSessionInUrl: isBrowser()` AFTER `...options?.auth`, silently overwriting the userland value. Discovery cost 60 seconds (one `npm pack` + one file read). Skipping this step cost CEO's trust and one full diagnostic cycle. REV2 fix lives in `apps/web/src/app/[locale]/callback/page.tsx` (getSession-first-then-fallback, no client-factory changes).

Rule: no commit touches `apps/web/src/lib/supabase/client.ts` or `apps/web/src/lib/supabase/server.ts` `auth` options without a `Verified-against-library-source: <file>:<line>` line in the commit body.

## OAuth callback pattern (INC-017 + INC-018, 2026-04-17)

The OAuth callback page handles TWO entry paths and must stay correct for both:

- **Path A — external OAuth redirect** (fresh page load from Google / GitHub / etc.): `createBrowserClient` singleton is built fresh on /callback. Its `_initialize()` sees `?code=` in the URL and auto-exchanges it, consuming the PKCE `code_verifier` cookie. Any SECOND call to `exchangeCodeForSession(code)` in the same load cycle throws "PKCE code verifier not found in storage" and bounces the user to /login.

- **Path B — SPA soft navigation** (user clicked an in-app link that carried `?code=`): singleton was built on a previous page with no `?code=` in URL. `_initialize()` already ran and did NOT auto-exchange. You MUST call `exchangeCodeForSession(code)` explicitly or the session never lands.

Canonical callback pattern (single code path, handles both):
```ts
void (async () => {
  const supabase = createClient();
  const { data: initial } = await supabase.auth.getSession(); // awaits _initializePromise
  let session = initial.session;
  if (!session) {
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);
    if (error || !data.session) { router.replace(`/${locale}/login?message=oauth-error`); return; }
    session = data.session;
  }
  setSession(session);
  // ... attribution PUT, onboarding-vs-dashboard routing
})();
```

Do NOT call `exchangeCodeForSession(code)` unconditionally — that's INC-018 REV1's mistake.
Do NOT rely on auto-exchange alone — that's INC-017's original mistake (SPA path loses session).
Do NOT try to disable `detectSessionInUrl` — that's REV1's no-op; library hardcodes it.

## API Calls
Use generated types from @hey-api/openapi-ts:
```typescript
import { getHealth } from "@/lib/api/generated";
```

## Tailwind CSS 4
- Use `@import "tailwindcss"` in globals.css
- Theme via `@theme {}` block
- No tailwind.config.js needed
