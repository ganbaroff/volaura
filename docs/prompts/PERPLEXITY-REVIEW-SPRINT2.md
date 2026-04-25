# Perplexity Prompt — Sprint 2 Code Review

**Paste into Perplexity (Pro, with web search ON)**

---

I'm building Volaura, a verified talent platform with Next.js 14 App Router and Supabase.

Please review these implementation decisions and flag any issues or better approaches based on current best practices (2025-2026):

## 1. Supabase Auth Middleware Chain

```typescript
// middleware.ts
export async function middleware(request: NextRequest) {
  const i18nResponse = i18nRouter(request, i18nConfig);
  if (i18nResponse.status === 301 || i18nResponse.status === 302) {
    return i18nResponse;
  }
  return await updateSession(request, i18nResponse);
}

// supabase/middleware.ts
const { data: { user } } = await supabase.auth.getUser();
// redirect if !user and protected route
```

Questions:
- Is `supabase.auth.getUser()` in middleware the correct pattern for Next.js 14 + @supabase/ssr ^0.6.0?
- Should I use `getSession()` or `getUser()`? Which is more secure?
- Any known performance issues with running auth check on every request?

## 2. i18n Configuration

```typescript
const i18nConfig = {
  locales: ["az", "en"] as const,
  defaultLocale: "az" as const,
  prefixDefault: true,
}
```

Using `next-i18n-router` ^5.5.0 + `react-i18next` ^15.4.0.

Questions:
- Is `next-i18n-router` still the recommended approach for Next.js 14 App Router i18n in 2026?
- Are there better alternatives? (next-intl, paraglide, etc.)
- Any issues with `prefixDefault: true` and SEO?

## 3. PWA with @ducanh2912/next-pwa ^10.2.0

```javascript
const config = withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
})(nextConfig);
```

Questions:
- Is @ducanh2912/next-pwa compatible with Next.js 14.2.x?
- Any known issues with App Router + service worker?
- Should we use the official next-pwa or this fork?

## 4. Tailwind CSS 4 Config

```css
@import "tailwindcss";
@theme {
  --color-brand: #6366f1;
  /* shadcn/ui CSS variables */
}
```

Questions:
- Is this the correct CSS-first approach for Tailwind v4 + shadcn/ui?
- Any breaking changes in Tailwind v4 that affect shadcn components?

Please search for recent issues, GitHub discussions, and official docs. Flag anything that could break in production.

